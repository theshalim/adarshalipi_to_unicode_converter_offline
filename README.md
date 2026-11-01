# Bangla Converter — AdarshaLipi / Bijoy ⇆ Unicode (offline)

A small Windows app that converts Bangla text between the old ANSI fonts
(**AdarshaLipi** and **Bijoy / SutonnyMJ**) and **Unicode**. It runs fully
offline: no internet connection, no installation, no data leaves the PC.

আদর্শলিপি / বিজয় ⇆ ইউনিকোড কনভার্টার — ইন্টারনেট ছাড়াই চলে।

## Features

- **Text:** paste into a box and press a button (F5 → Unicode, F6 → old font).
- **Word files (.docx):** converts the whole document and saves a new copy.
  Tables, headers, footers, text boxes, bold/italic, sizes and English text are
  kept as they are. The original file is never changed.
- **Auto-detect:** notices whether pasted text or a Word file is AdarshaLipi or
  Bijoy and switches automatically.
- Both directions: old font → Unicode and Unicode → old font.

## Download and run

Build the `.exe` (below) or take it from the Releases page, then double-click
`AdarshaLipi-Unicode-Converter.exe`. Requires Windows 10/11, 64-bit.

Windows may show "Windows protected your PC" because the file is not
digitally signed: choose **More info → Run anyway**.

**Fonts are not included.** AdarshaLipi and SutonnyMJ are not free to
redistribute, so install them from your own AdarshaLipi/Bijoy software.
Conversion works without them; only the left box will show Latin letters
instead of Bangla.

## Build from source

```bat
build.bat
```

This installs the requirements, runs the tests and creates
`dist\AdarshaLipi-Unicode-Converter.exe`. To bundle a Unicode display font,
put `Nikosh.ttf` next to `build.bat` first.

Run the tests on their own with `python test.py`.

## Project layout

| File | What it does |
|---|---|
| `converter.py` | The conversion tables and engine for AdarshaLipi and Bijoy |
| `docx_convert.py` | Converts the text inside Word files while keeping the layout |
| `app.py` | The window (Tkinter) |
| `test.py`, `test_words.txt`, `sample_unicode.txt` | Round-trip tests |
| `make_test_docx.py` | Builds a sample Word file for manual testing (needs `python-docx`) |

## How the tables were made

No public AdarshaLipi mapping was found, so every glyph of the AdarshaLipiExp
font was rendered and matched against Unicode Bangla by eye. The Bijoy table
was checked the same way against SutonnyMJ. Round-trip tests pass for both,
but the AdarshaLipi table has not yet been checked against real documents
typed in the original AdarshaLipi software. Reports of wrong letters are welcome.

## Security

- No network access, logging or telemetry.
- Word files are read with a hardened XML parser (no DTDs or external
  entities) and are rejected if they look like zip bombs.
