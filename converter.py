"""AdarshaLipi / Bijoy (ANSI) <-> Unicode Bangla converter.

The ANSI side is text typed with the AdarshaLipiExp / AdarshaLipiCon fonts or
the Bijoy (SutonnyMJ) fonts. Each key in a table is the character Windows stores for that glyph
(Windows-1252 code points as Unicode), and the value is the Unicode Bangla
it represents. Both tables were checked by rendering every glyph of ALIPI_EX.TTF
and SutonnyMJ.ttf next to the Unicode it is mapped to.
"""
import re

# Placeholders used while reordering
REPH = ""          # র্ written after the consonant in ANSI
PRE_I = ""         # ি  written before the consonant
PRE_E = ""         # ে  written before the consonant
PRE_OI = ""        # ৈ  written before the consonant

ALIPI_MAP = {
    # punctuation / symbols that differ from plain ASCII
    "\x22": "‘", "\x27": "’", "\x24": "৳", "\x40": "ঽ",
    "\x5f": "—", "\x60": "÷", "\x7a": "।", "\x7c": ".",
    # conjuncts on the smart-quote codes (checked in ALIPI_CO.TTF; damaged in some ALIPI_EX.TTF copies)
    "‘": "জ্ঞ", "’": "ঞ্চ", "“": "ঞ্ছ", "”": "ঞ্জ", "•": "ঞ্ঝ",
    # digits
    "0": "০", "1": "১", "2": "২", "3": "৩", "4": "৪",
    "5": "৫", "6": "৬", "7": "৭", "8": "৮", "9": "৯",
    # vowels
    "A": "অ", "B": "আ", "C": "ই", "D": "ঈ", "E": "উ", "F": "ঊ", "G": "ঋ",
    "H": "এ", "I": "ঐ", "J": "ও", "K": "ঔ",
    # consonants
    "L": "ক", "M": "খ", "N": "গ", "O": "ঘ", "P": "ঙ", "Q": "চ", "R": "ছ",
    "S": "জ", "T": "ঝ", "U": "ঞ", "V": "ট", "W": "ঠ", "X": "ড", "Y": "ঢ",
    "Z": "ণ", "a": "ত", "b": "থ", "c": "দ", "d": "ধ", "e": "ন", "f": "প",
    "g": "ফ", "h": "ব", "i": "ভ", "j": "ম", "k": "য", "l": "র", "m": "ল",
    "n": "শ", "o": "ষ", "p": "স", "q": "হ", "r": "ক্ষ", "s": "ড়", "t": "ঢ়",
    "u": "য়", "v": "ৎ", "w": "ং", "x": "ঃ", "y": "ঁ",
    # vowel signs (several glyph variants each)
    "\xa1": "া", "\xa2": PRE_I, "\xa3": "ী", "\xb1": "ী",
    "\xa4": "ু", "\xa5": "ু", "\xa6": "ু",  # \xa6 is the ু shaped for র (রু)
    "\xa7": "ূ", "\xa8": "ূ", "\xa9": "ূ",  # \xa9 is the ূ shaped for র (রূ)
    "\xaa": "ৃ", "\xab": "ৃ",
    "\xad": PRE_E, "\xae": PRE_E, "\xaf": PRE_OI, "\xb0": PRE_OI,
    "\x7e": "ৗ",
    # half forms (first part of a conjunct, written before the consonant)
    "\xb2": "ঙ্", "\xb4": "ঙ্", "\xb3": "ণ্", "\xb5": "চ্", "\xb6": "জ্",
    "\xb7": "ঞ্", "∙": "ঞ্", "\xb8": "ন্", "\xbe": "ন্", "\xbf": "ন্",
    "\xc3": "প্", "\xc7": "ম্", "\xd2": "ল্", "\xd5": "শ্",
    "\xd6": "ষ্", "\xd7": "ষ্", "\xd8": "স্", "\xd9": "স্",
    # below-base forms (second part of a conjunct, written after the consonant)
    "\xb9": "্ত", "\xba": "্ত", "\xbb": "্ত্র",
    "\xbc": "্দ", "\xbd": "্ধ", "\xc0": "্ন", "\xc1": "্ন", "\xc8": "্ম",
    "\xc4": "্ব", "\xc5": "্ব", "\xc6": "্ব", "\xc9": "্য",
    "\xca": "্র", "\xcb": "্র", "\xcc": "্র", "\xd0": "্র", "\xd3": "্ল", "\xd4": "্ল",
    "\xdb": "্ষ", "\xda": "্", "\xd1": REPH,
    # complete conjuncts
    "\xdc": "দ্ধ", "\xde": "দ্ধ্ব", "\xe0": "দ্ব", "\xe1": "দ্ভ", "\xe2": "দ্র",
    "\xe3": "ষ্ঠ", "\xe4": "ন্ড", "\xe5": "ন্ধ", "\xe6": "ন্ন", "\xe7": "প্ত",
    "\xe8": "প্প", "\xe9": "ফ্র", "\xea": "ব্জ", "\xeb": "ব্দ", "\xec": "ব্ধ",
    "\xee": "ব্ব", "\xef": "ভ্র", "\xf0": "ম্ব", "\xf1": "ম্ভ", "\xf2": "ম্ভ্র",
    "\xf3": "ল্ক", "\xf4": "ল্ড", "\xf5": "ল্ল", "\xf6": "শু", "\xf7": "শু",
    "\xf8": "ষ্ট", "\xf9": "ষ্ঠ", "\xfa": "স্ক", "\xfb": "স্ক্র", "\xfc": "স্ব",
    "\xfd": "হু", "\xfe": "ক্ষ্ম", "Œ": "জ্ঝ", "œ": "ত্র", "Š": "শ্রু",
    "š": "ত্ত", "Ÿ": "দ্দ", "ƒ": "ক্ট", "ˆ": "ঙ্ক", "˜": "ষ্ঠ",
    "–": "ট্ট", "—": "ড্ড", "‚": "ক্ক", "„": "ক্স", "†": "গ্ন",
    "‡": "গ্ধ", "…": "গু", "‰": "ঙ্গ", "‹": "জ্জ", "›": "ত্থ",
    "™": "ণ্ড",
}

# Empty / unused slots in the AdarshaLipi font: dropped during conversion
ALIPI_DROP = set("^¬ÂÝßíÿ")

BIJOY_MAP = {
    # digits, punctuation
    "0": "০", "1": "১", "2": "২", "3": "৩", "4": "৪",
    "5": "৫", "6": "৬", "7": "৭", "8": "৮", "9": "৯",
    "$": "৳", "|": "।", "&": "্",
    "Ñ": "–", "Ò": "“", "Ó": "”", "Ô": "‘", "Õ": "’",
    # vowels (আ is typed A + v)
    "A": "অ", "B": "ই", "C": "ঈ", "D": "উ", "E": "ঊ", "F": "ঋ",
    "G": "এ", "H": "ঐ", "I": "ও", "J": "ঔ",
    # consonants
    "K": "ক", "L": "খ", "M": "গ", "N": "ঘ", "O": "ঙ", "P": "চ", "Q": "ছ",
    "R": "জ", "S": "ঝ", "T": "ঞ", "U": "ট", "V": "ঠ", "W": "ড", "X": "ঢ",
    "Y": "ণ", "Z": "ত", "_": "থ", "`": "দ", "a": "ধ", "b": "ন", "c": "প",
    "d": "ফ", "e": "ব", "f": "ভ", "g": "ম", "h": "য", "i": "র", "j": "ল",
    "k": "শ", "l": "ষ", "m": "স", "n": "হ", "o": "ড়", "p": "ঢ়", "q": "য়",
    "r": "ৎ", "s": "ং", "t": "ঃ", "u": "ঁ",
    # vowel signs
    "v": "া", "w": PRE_I, "x": "ী", "y": "ু", "z": "ু", "“": "ু", "æ": "ু",
    "~": "ূ", "ƒ": "ূ", "‚": "ূ", "„": "ৃ", "…": "ৃ",
    "‡": PRE_E, "†": PRE_E, "ˆ": PRE_OI, "‰": PRE_OI, "Š": "ৗ",
    # half forms
    "•": "ঙ্", "”": "চ্", "˜": "দ্", "™": "দ্", "š": "ন্", "›": "ন্",
    "¤": "ম্", "®": "ষ্", "¯": "স্",
    # below-base forms
    "¨": "্য", "ª": "্র", "«": "্র", "Ö": "্র", "¬": "্ল", "ø": "্ল",
    "¡": "্ব", "^": "্ব", "Ÿ": "্ব", "¦": "্ব", "¢": "্ভ", "£": "্ভ্র",
    "¥": "্ম", "§": "্ম", "œ": "্ন", "Í": "্ত", "—": "ত", "‹": "্ক",
    "Œ": "্ক্র", "ú": "্প", "è": "্ণ", "‘": "্তু", "’": "্থ", "¿": "্ত্র",
    "©": REPH,
    # complete conjuncts
    "°": "ক্ক", "±": "ক্ট", "²": "ক্ষ্ম", "³": "ক্ত", "´": "ক্ম", "µ": "ক্র",
    "¶": "ক্ষ", "·": "ক্স", "¸": "গু", "¹": "গ্ন", "º": "গ্দ", "»": "গ্ধ",
    "¼": "ঙ্ক", "½": "ঙ্গ", "¾": "জ্জ", "À": "জ্ঝ", "Á": "জ্ঞ", "Â": "ঞ্চ",
    "Ã": "ঞ্ছ", "Ä": "ঞ্জ", "Å": "ঞ্ঝ", "Æ": "ট্ট", "Ç": "ড্ড", "È": "ণ্ট",
    "É": "ণ্ঠ", "Ë": "ত্ত", "Ì": "ত্থ", "Î": "ত্র", "Ï": "দ্দ",
    "×": "দ্ধ", "Ø": "দ্ব", "Ù": "দ্ম", "Ú": "ন্ঠ", "Û": "ন্ড", "Ü": "ন্ধ",
    "Ý": "ন্স", "Þ": "প্ট", "ß": "প্ত", "à": "প্প", "á": "প্স", "â": "ব্জ",
    "ã": "ব্দ", "ä": "ব্ধ", "å": "ভ্র", "ç": "ম্ফ", "é": "ল্ক", "ê": "ল্গ",
    "ë": "ল্ট", "ì": "ল্ড", "í": "ল্প", "î": "ল্ফ", "ï": "শু", "ð": "শ্চ",
    "ñ": "শ্ছ", "ò": "ষ্ণ", "ó": "ষ্ট", "ô": "ষ্ঠ", "õ": "ষ্ফ", "ö": "স্খ",
    "÷": "স্ট", "ù": "স্ফ", "û": "হু", "ü": "হৃ", "ý": "হ্ন", "þ": "হ্ম",
}

# ড় ঢ় য় as single code points (normalizers split them into letter + nukta)
NUKTA = {chr(0x9A1) + chr(0x9BC): chr(0x9DC), chr(0x9A2) + chr(0x9BC): chr(0x9DD),
         chr(0x9AF) + chr(0x9BC): chr(0x9DF)}


def _compose(t: str) -> str:
    for k, v in NUKTA.items():
        t = t.replace(k, v)
    return t


HASANTA = chr(0x9CD)
C = "[ক-হড়ঢ়য়]"          # one consonant
CLUSTER = f"{C}(?:{HASANTA}{C})*"                 # consonant cluster
VSIGNS = "[া-ৄেৈোৌৗঁ-ঃ]"
PHALA = {"য", "র", "ব", "ম", "ন", "ল"}
YA_PHALA_ON_RA = ""   # marks র‍্য (র + ZWJ + ্য) while converting


class Encoding:
    def __init__(self, name, table, drop, pre, sign, hasanta, reph, special,
                 extra_full=None, letters=None, au_prefix=""):
        self.name = name
        self.table = table
        self.drop = set(drop)
        self.pre = pre              # ি ে ৈ -> glyph written before the consonant
        self.sign = sign            # other vowel signs and marks
        self.hasanta = hasanta      # visible hasanta glyph
        self.reph = reph            # র্ glyph written after the consonant
        self.special = special      # consonant+vowel glyphs (শু, হু, ...)
        self.au_prefix = au_prefix  # glyph drawn before ৗ (AdarshaLipi: া)

        # preferred glyph for each Unicode string (first variant in the table wins)
        rev = {}
        for k, v in table.items():
            v = _compose(v)
            if v not in (PRE_I, PRE_E, PRE_OI, REPH) and v not in rev:
                rev[v] = k
        rev.update(extra_full or {})
        rev.update(letters or {})
        self.rev = rev
        self.full = sorted((u for u in rev if len(u) > 1 and HASANTA in u
                            and not u.startswith(HASANTA) and not u.endswith(HASANTA)),
                           key=len, reverse=True)
        self.half = {u[0]: rev[u] for u in rev if len(u) == 2 and u.endswith(HASANTA)}
        self.below = {u: rev[u] for u in rev if u.startswith(HASANTA) and len(u) > 1}

    # ------------------------------------------------------------ ANSI -> Unicode
    def to_unicode(self, text: str) -> str:
        s = "".join(self.table.get(ch, ch) for ch in text if ch not in self.drop)
        s = _compose(s).replace(HASANTA + HASANTA, HASANTA)
        s = s.replace("অা", "আ")  # Bijoy types আ as অ + া
        # pre-base vowel sign: move after the cluster that follows it
        s = re.sub(f"([{PRE_I}{PRE_E}{PRE_OI}])({CLUSTER})", r"\2\1", s)
        # reph: written after the cluster (and its vowel signs), belongs before it
        s = re.sub(f"({CLUSTER})((?:{VSIGNS}|[{PRE_I}{PRE_E}{PRE_OI}])*){REPH}", r"র্\1\2", s)
        # ো and ৌ
        s = re.sub(f"{PRE_E}া?ৗ", "ৌ", s)
        s = s.replace(PRE_E + "া", "ো").replace("াৗ", "ৌ")
        return s.replace(PRE_I, "ি").replace(PRE_E, "ে").replace(PRE_OI, "ৈ").replace(REPH, "র্")

    # ------------------------------------------------------------ Unicode -> ANSI
    def _cluster(self, cl: str) -> str:
        rev, parts = self.rev, cl.split(HASANTA)
        out, i = [], 0
        while i < len(parts):
            hit = next((f for f in self.full
                        if parts[i:i + f.count(HASANTA) + 1] == f.split(HASANTA)), None)
            if hit:
                out.append(rev[hit])
                i += hit.count(HASANTA) + 1
                if i < len(parts):  # more of the cluster follows the conjunct
                    if HASANTA + parts[i] in self.below:
                        out.append(self.below[HASANTA + parts[i]])
                        i += 1
                    else:
                        out.append(self.hasanta)
                continue
            c = parts[i]
            nxt = parts[i + 1] if i + 1 < len(parts) else None
            if nxt is None:
                out.append(rev.get(c, c))
                i += 1
            elif nxt in PHALA and HASANTA + nxt in self.below:
                out += [rev.get(c, c), self.below[HASANTA + nxt]]
                i += 2
            elif c in self.half:
                out.append(self.half[c])
                i += 1
            elif HASANTA + nxt in self.below:
                out += [rev.get(c, c), self.below[HASANTA + nxt]]
                i += 2
            else:
                out += [rev.get(c, c), self.hasanta]  # next consonant follows
                i += 1
        return "".join(out)

    def _syllable(self, m: re.Match) -> str:
        reph, cl, signs = m.group(1), m.group(2), m.group(3)
        signs = signs.replace("ো", "ো").replace("ৌ", "ৌ")
        pre = "".join(self.pre[s] for s in signs if s in self.pre)
        post_signs = "".join(s for s in signs if s not in self.pre)
        body = None
        for sp, g in self.special.items():
            base, sign = sp[:-1], sp[-1]
            if cl.endswith(base) and post_signs.startswith(sign) and (
                    len(cl) == len(base) or cl[-len(base) - 1] == HASANTA):
                head = cl[:-len(base)].rstrip(HASANTA)
                body = (self._cluster(head) if head else "") + g
                post_signs = post_signs[1:]
                break
        if body is None:
            body = self._cluster(cl)
        if pre and self.hasanta in body:
            # a visible hasanta splits the cluster, so ি/ে/ৈ belong before its last letter
            cut = body.rfind(self.hasanta) + 1
            body, pre = body[:cut] + pre + body[cut:], ""
        post = "".join((self.au_prefix if s == "ৗ" else "") + self.sign.get(s, s)
                       for s in post_signs)
        return pre + body + (self.reph if reph else "") + post

    def from_unicode(self, text: str) -> str:
        s = _compose(text).replace("র‍" + HASANTA + "য", "র" + YA_PHALA_ON_RA)
        # one pass, so glyphs already written are never converted a second time
        tok = re.compile(f"(র{HASANTA}(?={C}))?({CLUSTER})({VSIGNS}*)|(.)", re.S)

        def piece(m):
            if m.group(2):
                return self._syllable(m)
            ch = m.group(4)
            if ch == YA_PHALA_ON_RA:
                return self.below[HASANTA + "য"]
            if ch in "‌‍":
                return ""
            if "।" <= ch <= "৿" or ch in "‘’“”–—÷•":
                return self.rev.get(ch, self.sign.get(ch, self.pre.get(ch, ch)))
            return ch
        return tok.sub(piece, s)


ADARSHALIPI = Encoding(
    "AdarshaLipi", ALIPI_MAP, ALIPI_DROP,
    pre={"ি": "\xa2", "ে": "\xae", "ৈ": "\xaf"},  # \xad is a soft hyphen that Word hides
    sign={"া": "\xa1", "ী": "\xa3", "ু": "\xa4", "ূ": "\xa7", "ৃ": "\xaa", "ৗ": "\x7e",
          "ং": "w", "ঃ": "x", "ঁ": "y"},
    hasanta="\xda", reph="\xd1",
    special={"শ্রু": "Š", "শু": "\xf6", "হু": "\xfd", "গু": "…", "রু": "l\xa6", "রূ": "l\xa9"},
    # ন্ত/স্ত join properly with the below-base ত (\xba, \xbb for ত্র); the \xbe ন্ and
    # \xb4 ঙ্ half forms connect better than the first variants in the table. The
    # below-base ত collides with ক's bowl at text sizes, so ক্ত is written with a hasanta.
    extra_full={"ন্ত": "e\xba", "স্ত": "p\xba", "ন্ত্র": "e\xbb", "স্ত্র": "p\xbb",
                "ক্ত": "L\xdaa", "ঙ্ক্ষ": "\xb4r", "ন্": "\xbe", "ঙ্": "\xb4",
                # no স্থ glyph: স্ half + থ reads as "সিথ" next to ি, a hasanta reads right
                "স্থ": "p\xdab"},
    # the font has no double quote or bullet: those codes are conjuncts
    letters={"“": "\x22\x22", "”": "\x27\x27", "•": "*"},
    au_prefix="\xa1",  # ৗ is drawn as া plus a top curl
)

BIJOY = Encoding(
    "Bijoy", BIJOY_MAP, (),
    pre={"ি": "w", "ে": "‡", "ৈ": "ˆ"},
    sign={"া": "v", "ী": "x", "ু": "y", "ূ": "~", "ৃ": "…", "ৗ": "Š",
          "ং": "s", "ঃ": "t", "ঁ": "u"},
    hasanta="&", reph="\xa9",
    special={"ন্তু": "š‘", "স্তু": "\xaf‘", "গু": "\xb8", "শু": "\xef",
             "হু": "\xfb", "হৃ": "\xfc", "রু": "i\xe6", "রূ": "iƒ"},
    extra_full={"ন্ত": "š\xcd", "স্ত": "\xaf\xcd", "ন্ত্র": "š\xbf",
                "স্ত্র": "\xaf\xbf", "ন্থ": "š’", "স্থ": "\xaf’",
                "ম্প": "\xa4\xfa", "স্প": "\xaf\xfa", "ষ্প": "\xae\xfa",
                "স্ক": "\xaf‹", "ষ্ক": "\xae‹", "স্ক্র": "\xafŒ",
                "ষ্ক্র": "\xaeŒ", "ম্ব": "\xa4^", "স্ব": "\xaf^", "ম্ভ": "\xa4\xa2",
                "ম্ভ্র": "\xa4\xa3", "ম্ম": "\xa4\xa7", "স্ম": "\xaf\xa7", "ষ্ম": "\xae\xa7",
                "দ্ভ": "™\xa2", "ক্ব": "K\xa1"},
    letters={"আ": "Av", "‘": "\xd4", "’": "\xd5", "“": "\xd2", "”": "\xd3", "–": "\xd1"},
)

ENCODINGS = {"AdarshaLipi": ADARSHALIPI, "Bijoy": BIJOY}


def ansi_to_unicode(text: str, encoding: str = "AdarshaLipi") -> str:
    return ENCODINGS[encoding].to_unicode(text)


def unicode_to_ansi(text: str, encoding: str = "AdarshaLipi") -> str:
    return ENCODINGS[encoding].from_unicode(text)
