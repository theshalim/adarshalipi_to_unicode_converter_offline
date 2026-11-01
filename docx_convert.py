"""Convert the Bangla text inside a Word .docx file, keeping its layout.

Only runs typed in an AdarshaLipi or Bijoy font are converted to Unicode (or,
the other way, only runs holding Unicode Bangla). Tables, headers, footers,
footnotes and text boxes are all paragraphs in the XML, so they are covered
the same way, and everything else in the file is copied unchanged.
"""
import re
import zipfile

from lxml import etree

from converter import ansi_to_unicode, unicode_to_ansi

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
UNICODE_FONT = "Nikosh"
ANSI_FONT = {"AdarshaLipi": "AdarshaLipiExp", "Bijoy": "SutonnyMJ"}
PARTS = re.compile(r"word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$")
BANGLA = re.compile("[ঀ-৿]")

# Untrusted files: never load DTDs, external entities or network resources
SAFE_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False,
                              dtd_validation=False, huge_tree=False)
MAX_PART = 100 * 1024 * 1024    # one XML part, uncompressed
MAX_TOTAL = 500 * 1024 * 1024   # whole file, uncompressed
MAX_RATIO = 200                 # uncompressed / compressed, catches zip bombs


class UnsafeDocx(ValueError):
    pass


def _parse(xml):
    if b"<!DOCTYPE" in xml[:4096].upper() or b"<!ENTITY" in xml.upper():
        raise UnsafeDocx("The file contains a DOCTYPE/ENTITY declaration, which real Word files never have.")
    return etree.fromstring(xml, SAFE_PARSER)


def _check_zip(z):
    total = 0
    for i in z.infolist():
        total += i.file_size
        if i.file_size > MAX_PART or total > MAX_TOTAL:
            raise UnsafeDocx("The file is too large to convert safely.")
        if i.file_size > 1024 * 1024 and i.file_size > MAX_RATIO * max(i.compress_size, 1):
            raise UnsafeDocx("The file looks like a zip bomb (it expands to a huge size).")


def q(tag):
    return f"{{{W}}}{tag}"


def font_encoding(name):
    """Which ANSI encoding a font name belongs to, if any."""
    if not name:
        return None
    n = name.lower().replace(" ", "")
    if n.startswith("adarshalipi"):
        return "AdarshaLipi"
    if n.endswith("mj") and not n.endswith("omj"):  # SutonnyMJ, BijoyMJ, ...; SutonnyOMJ is Unicode
        return "Bijoy"
    return None


class Styles:
    """Resolves the font a run really uses (direct, run style, paragraph style, defaults)."""

    def __init__(self, xml):
        self.fonts, self.based, self.default_font, self.default_para = {}, {}, None, None
        if xml is None:
            return
        root = _parse(xml)
        rf = root.find("w:docDefaults/w:rPrDefault/w:rPr/w:rFonts", NS)
        self.default_font = self._ascii(rf)
        for st in root.findall("w:style", NS):
            sid = st.get(q("styleId"))
            self.fonts[sid] = self._ascii(st.find("w:rPr/w:rFonts", NS))
            b = st.find("w:basedOn", NS)
            self.based[sid] = b.get(q("val")) if b is not None else None
            if st.get(q("type")) == "paragraph" and st.get(q("default")) == "1":
                self.default_para = sid

    @staticmethod
    def _ascii(rf):
        if rf is None:
            return None
        return rf.get(q("ascii")) or rf.get(q("hAnsi"))

    def style_font(self, sid):
        seen = set()
        while sid and sid not in seen:
            seen.add(sid)
            if self.fonts.get(sid):
                return self.fonts[sid]
            sid = self.based.get(sid)
        return None

    def run_font(self, run, para):
        rf = run.find("w:rPr/w:rFonts", NS)
        f = self._ascii(rf)
        if f:
            return f
        rs = run.find("w:rPr/w:rStyle", NS)
        if rs is not None and self.style_font(rs.get(q("val"))):
            return self.style_font(rs.get(q("val")))
        ps = para.find("w:pPr/w:pStyle", NS)
        sid = ps.get(q("val")) if ps is not None else self.default_para
        return self.style_font(sid) or self.default_font


def _rpr_key(run):
    rpr = run.find("w:rPr", NS)
    return etree.tostring(rpr) if rpr is not None else b""


def _set_font(run, font, to_unicode):
    rpr = run.find("w:rPr", NS)
    if rpr is None:
        rpr = etree.SubElement(run, q("rPr"))
        run.remove(rpr)
        run.insert(0, rpr)
    rf = rpr.find("w:rFonts", NS)
    if rf is None:
        rf = etree.Element(q("rFonts"))
        rpr.insert(0 if rpr.find("w:rStyle", NS) is None else 1, rf)
    for a in list(rf.attrib):
        if a.endswith("Theme"):
            del rf.attrib[a]
    for a in ("ascii", "hAnsi", "cs", "eastAsia"):
        rf.set(q(a), font)
    if to_unicode:
        # Word draws Bangla with the complex-script size/bold/italic: copy them over
        for plain, cs in (("sz", "szCs"), ("b", "bCs"), ("i", "iCs")):
            src = rpr.find(f"w:{plain}", NS)
            if src is not None and rpr.find(f"w:{cs}", NS) is None:
                el = etree.Element(q(cs))
                if src.get(q("val")) is not None:
                    el.set(q("val"), src.get(q("val")))
                src.addnext(el)


def _text_only(run):
    """True when a run holds nothing but formatting and text."""
    return all(ch.tag in (q("rPr"), q("t")) for ch in run)


def _groups(para, wanted):
    """Consecutive runs with the same formatting that need converting, as lists."""
    group, key = [], None
    for el in para:
        if el.tag in (q("proofErr"), q("bookmarkStart"), q("bookmarkEnd")):
            continue
        if el.tag == q("r") and wanted(el) is not None:
            k = (_rpr_key(el), wanted(el))
            if group and k == key and _text_only(el) and _text_only(group[-1]):
                group.append(el)
                continue
            if group:
                yield group
            group, key = [el], k
        else:
            if group:
                yield group
            group, key = [], None
    if group:
        yield group


def _split_to_ansi(group, enc):
    """Replace runs with pieces: Bangla parts converted in the ANSI font,
    English/other parts left in the original font, so they don't turn into Bangla."""
    src = "".join(t.text or "" for r in group for t in r.iter(q("t")))
    first = group[0]
    parent, pos = first.getparent(), first.getparent().index(first)
    template = etree.tostring(first)
    for r in group:
        parent.remove(r)
    for piece in re.split("([ঀ-৿‌‍]+(?:[ ।]+[ঀ-৿‌‍]+)*)", src):
        if not piece:
            continue
        run = etree.fromstring(template, SAFE_PARSER)
        for t in run.findall("w:t", NS):
            run.remove(t)
        t = etree.SubElement(run, q("t"))
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        if BANGLA.search(piece):
            t.text = unicode_to_ansi(piece, enc)
            _set_font(run, ANSI_FONT[enc], False)
        else:
            t.text = piece
        parent.insert(pos, run)
        pos += 1


def _convert_part(xml, styles, direction, target):
    root = _parse(xml)
    changed = 0
    for para in root.iter(q("p")):
        if direction == "to_unicode":
            def wanted(r, p=para):
                return font_encoding(styles.run_font(r, p))
        else:
            def wanted(r):
                text = "".join(t.text or "" for t in r.iter(q("t")))
                return target if BANGLA.search(text) else None
        for group in _groups(para, wanted):
            enc = wanted(group[0])
            texts = [t for r in group for t in r.iter(q("t"))]
            if not texts:
                continue
            if direction == "to_ansi" and all(_text_only(r) for r in group):
                _split_to_ansi(group, enc)
                changed += len(texts)
                continue
            if all(_text_only(r) for r in group):
                src = "".join(t.text or "" for t in texts)
                out = ansi_to_unicode(src, enc) if direction == "to_unicode" else unicode_to_ansi(src, enc)
                texts[0].text = out
                texts[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                for t in texts[1:]:
                    t.getparent().remove(t)
                for r in group[1:]:
                    r.getparent().remove(r)
            else:  # run with tabs/breaks: convert each text piece on its own
                for t in texts:
                    t.text = (ansi_to_unicode(t.text or "", enc) if direction == "to_unicode"
                              else unicode_to_ansi(t.text or "", enc))
            font = UNICODE_FONT if direction == "to_unicode" else ANSI_FONT[enc]
            _set_font(group[0], font, direction == "to_unicode")
            changed += len(texts)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), changed


def inspect(path):
    """Count runs per kind so the app can pick a direction: {'AdarshaLipi': n, 'Bijoy': n, 'Unicode': n}."""
    counts = {"AdarshaLipi": 0, "Bijoy": 0, "Unicode": 0}
    with zipfile.ZipFile(path) as z:
        _check_zip(z)
        styles = Styles(z.read("word/styles.xml") if "word/styles.xml" in z.namelist() else None)
        for name in z.namelist():
            if not PARTS.search(name):
                continue
            root = _parse(z.read(name))
            for para in root.iter(q("p")):
                for r in para.iter(q("r")):
                    text = "".join(t.text or "" for t in r.iter(q("t")))
                    if not text.strip():
                        continue
                    enc = font_encoding(styles.run_font(r, para))
                    if enc:
                        counts[enc] += 1
                    elif BANGLA.search(text):
                        counts["Unicode"] += 1
    return counts


def convert_docx(src, dst, direction, target="AdarshaLipi", progress=None):
    """direction: 'to_unicode' or 'to_ansi' (then target is 'AdarshaLipi' or 'Bijoy').
    progress(done, total), if given, is called after each part of the file.
    Returns how many text pieces were converted."""
    total = 0
    with zipfile.ZipFile(src) as zin:
        _check_zip(zin)
        styles = Styles(zin.read("word/styles.xml") if "word/styles.xml" in zin.namelist() else None)
        items = zin.infolist()
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for i, item in enumerate(items, 1):
                data = zin.read(item.filename)
                if PARTS.search(item.filename):
                    data, n = _convert_part(data, styles, direction, target)
                    total += n
                zout.writestr(item, data)
                if progress:
                    progress(i, len(items))
    return total
