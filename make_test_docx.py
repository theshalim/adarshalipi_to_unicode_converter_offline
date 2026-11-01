import sys; sys.stdout.reconfigure(encoding="utf-8")
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from converter import unicode_to_ansi as u2a

def run(p, text, font, size=14, bold=False):
    r = p.add_run(text); r.font.name = font; r.font.size = Pt(size); r.bold = bold
    r._element.rPr.rFonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hAnsi", font)
    return r

A = lambda s: u2a(s, "AdarshaLipi")
B = lambda s: u2a(s, "Bijoy")
d = Document()
hp = d.sections[0].header.paragraphs[0]; run(hp, A("গণপ্রজাতন্ত্রী বাংলাদেশ সরকার"), "AdarshaLipiExp", 12)
p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, A("কর্মচারীদের মাসিক বেতন বিবরণী"), "AdarshaLipiExp", 20, True)
p = d.add_paragraph()
run(p, A("অফিস: "), "AdarshaLipiExp", 14, True); run(p, A("জেলা প্রশাসকের কার্যালয়, ঢাকা"), "AdarshaLipiExp")
run(p, "  (Ref: HR-2026/11)", "Times New Roman", 12)
t = d.add_table(rows=4, cols=4); t.style = "Table Grid"
rows = [["ক্রমিক", "নাম", "পদবী", "বেতন (টাকা)"],
        ["১", "মোঃ রফিকুল ইসলাম", "সহকারী পরিচালক", "৪৫,০০০"],
        ["২", "শ্রীমতী সুস্মিতা চক্রবর্তী", "হিসাবরক্ষক", "৩২,৫০০"],
        ["৩", "মোছাঃ জান্নাতুল ফেরদৌস", "অফিস সহায়ক", "১৮,২০০"]]
for i, row in enumerate(rows):
    for j, val in enumerate(row):
        c = t.cell(i, j).paragraphs[0]
        if i == 3:   # last row typed in Bijoy
            run(c, B(val), "SutonnyMJ", 13, i == 0)
        else:
            run(c, A(val), "AdarshaLipiExp", 13, i == 0)
p = d.add_paragraph()
run(p, B("বিঃ দ্রঃ সকল তথ্য সঠিক বলে প্রত্যয়ন করা হলো।"), "SutonnyMJ", 14)
p = d.add_paragraph(); run(p, "English line stays the same: Total 95,700 Taka.", "Calibri", 12)
d.save("testdocs/sample_ansi.docx"); print("saved")
