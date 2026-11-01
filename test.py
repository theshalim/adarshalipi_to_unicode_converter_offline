"""Round-trip tests: Unicode -> ANSI -> Unicode must give back the same text."""
import sys

from converter import ansi_to_unicode as a2u, unicode_to_ansi as u2a, _compose

sys.stdout.reconfigure(encoding="utf-8")
words = [w for line in open("test_words.txt", encoding="utf-8") for w in line.split()]
failed = 0
for enc in ("AdarshaLipi", "Bijoy"):
    bad = 0
    for w in words:
        an = u2a(w, enc)
        back = a2u(an, enc)
        if back != _compose(w):
            bad += 1
            print(enc, "MISMATCH", w, "->", ascii(an), "->", back)
    print(enc, "mismatches:", bad, "of", len(words))
    failed += bad

# a whole document must survive ANSI -> Unicode -> ANSI -> Unicode unchanged
text = open("sample_unicode.txt", encoding="utf-8").read().strip()
for enc in ("AdarshaLipi", "Bijoy"):
    u = a2u(u2a(text, enc), enc)
    again = a2u(u2a(u, enc), enc)
    ok = u == _compose(text) and again == u
    print(enc, "paragraph round trip:", "ok" if ok else "FAILED")
    failed += not ok

sys.exit(1 if failed else 0)
