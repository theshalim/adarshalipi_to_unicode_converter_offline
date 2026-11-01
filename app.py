"""AdarshaLipi / Bijoy ⇆ Unicode Converter — offline Windows app."""
import ctypes
import os
import queue
import sys
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox

from converter import ansi_to_unicode, unicode_to_ansi
import docx_convert

APP_TITLE = "Bangla Converter"
MAX_TXT = 20 * 1024 * 1024
MIN_BUSY_SECONDS = 1.6          # keep the progress card up long enough to be seen
ANSI_FONTS = {"AdarshaLipi": ["AdarshaLipiExp", "AdarshaLipiCon"],
              "Bijoy": ["SutonnyMJ", "SutonnyOMJ", "BijoyMJ"]}

# palette
BG = "#F5F6F8"
SURFACE = "#FFFFFF"
BORDER = "#E4E7EB"
TEXT = "#111827"
MUTED = "#6B7280"
ACCENT = "#15803D"
ACCENT_DARK = "#166534"
ACCENT_SOFT = "#ECFDF3"
PILL = "#EEF0F3"
HOVER = "#F1F3F5"
UI = "Segoe UI"


def guess_encoding(text):
    """Return the encoding the ANSI text was clearly typed in, or None."""
    alipi = sum(text.count(c) for c in "\xa1\xa2\xad\xae")   # া ি ে in AdarshaLipi
    bijoy = sum(text.count(c) for c in "‡†")       # ে in Bijoy
    if bijoy >= 2 and bijoy > 3 * alipi:
        return "Bijoy"
    if alipi >= 2 and alipi > 3 * bijoy:
        return "AdarshaLipi"
    return None


def resource(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def load_private_font(path):
    """Make a bundled font usable by this app even if it is not installed."""
    if os.path.exists(path):
        ctypes.windll.gdi32.AddFontResourceExW(path, 0x10, 0)  # FR_PRIVATE


def pick_font(root, wanted):
    have = set(tkfont.families(root))
    for name in wanted:
        if name in have:
            return name
    return "Segoe UI"


def rounded(canvas, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


class Button(tk.Canvas):
    """Flat rounded button. kind: primary, outline, ghost."""
    STYLES = {
        "primary": (ACCENT, ACCENT_DARK, "#FFFFFF", ACCENT, ACCENT_DARK),
        "outline": (SURFACE, ACCENT_SOFT, ACCENT, ACCENT, ACCENT),
        "ghost": (SURFACE, HOVER, TEXT, BORDER, BORDER),
    }

    def __init__(self, parent, text, command, kind="ghost", size=10, bold=False,
                 pad=(16, 8), expand=False, s=1.0):
        self.fill, self.hover, self.fg, self.line, self.line_hover = self.STYLES[kind]
        self.font = (UI, size, "bold" if bold or kind != "ghost" else "normal")
        self.command, self.text, self.s, self.expand = command, text, s, expand
        f = tkfont.Font(font=self.font)
        self.pad = (int(pad[0] * s), int(pad[1] * s))
        w = f.measure(text) + 2 * self.pad[0]
        h = f.metrics("linespace") + 2 * self.pad[1]
        super().__init__(parent, width=w, height=h, bg=parent.cget("bg"),
                         highlightthickness=0, cursor="hand2")
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<Enter>", lambda e: self.draw(True))
        self.bind("<Leave>", lambda e: self.draw(False))
        self.bind("<Button-1>", lambda e: self.command())
        self.hot = False
        self.draw()

    def set_text(self, text):
        self.text = text
        if not self.expand:
            f = tkfont.Font(font=self.font)
            self.configure(width=f.measure(text) + 2 * self.pad[0])
        self.draw()

    def draw(self, hot=None):
        if hot is not None:
            self.hot = hot
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            w, h = int(self.cget("width")), int(self.cget("height"))
        rounded(self, 1, 1, w - 1, h - 1, int(9 * self.s),
                fill=self.hover if self.hot else self.fill,
                outline=self.line_hover if self.hot else self.line)
        self.create_text(w / 2, h / 2, text=self.text, fill=self.fg, font=self.font)


class Segmented(tk.Canvas):
    """Pill-shaped two-option switch."""

    def __init__(self, parent, options, variable, command, s=1.0):
        self.options, self.var, self.command, self.s = options, variable, command, s
        self.font = (UI, 10, "bold")
        f = tkfont.Font(font=self.font)
        self.seg_w = max(f.measure(o) for o in options) + int(36 * s)
        self.h = f.metrics("linespace") + int(18 * s)
        super().__init__(parent, width=self.seg_w * len(options) + int(8 * s), height=self.h,
                         bg=parent.cget("bg"), highlightthickness=0, cursor="hand2")
        self.bind("<Button-1>", self.click)
        self.draw()

    def click(self, e):
        i = min(len(self.options) - 1, max(0, int((e.x - 4 * self.s) // self.seg_w)))
        if self.options[i] != self.var.get():
            self.var.set(self.options[i])
            self.command()

    def draw(self):
        self.delete("all")
        s, w, h = self.s, int(self.cget("width")), self.h
        rounded(self, 0, 0, w, h, h // 2, fill=PILL, outline=PILL)
        for i, o in enumerate(self.options):
            x1 = int(4 * s) + i * self.seg_w
            on = o == self.var.get()
            if on:
                rounded(self, x1, int(4 * s), x1 + self.seg_w, h - int(4 * s), (h - 8 * s) // 2,
                        fill=SURFACE, outline=BORDER)
            self.create_text(x1 + self.seg_w / 2, h / 2, text=o, font=self.font,
                             fill=ACCENT if on else MUTED)


class BusyCard(tk.Toplevel):
    """Modal progress card: spinner, steps, progress bar, then a finished state."""

    def __init__(self, app, title, subtitle):
        super().__init__(app.root)
        self.withdraw()  # build hidden, then show centred over the main window
        self.app, self.s = app, app.s
        s = self.s
        self.overrideredirect(True)
        self.configure(bg=BORDER)
        self.transient(app.root)
        body = tk.Frame(self, bg=SURFACE, padx=int(28 * s), pady=int(24 * s))
        body.pack(padx=1, pady=1)
        self.icon = tk.Canvas(body, width=int(56 * s), height=int(56 * s), bg=SURFACE,
                              highlightthickness=0)
        self.icon.pack()
        self.title = tk.Label(body, text=title, font=(UI, 13, "bold"), bg=SURFACE, fg=TEXT)
        self.title.pack(pady=(int(12 * s), 2))
        self.sub = tk.Label(body, text=subtitle, font=(UI, 9), bg=SURFACE, fg=MUTED,
                            wraplength=int(340 * s))
        self.sub.pack()
        self.bar = tk.Canvas(body, width=int(340 * s), height=int(8 * s), bg=SURFACE,
                             highlightthickness=0)
        self.bar.pack(pady=(int(18 * s), int(8 * s)))
        self.step = tk.Label(body, text="", font=(UI, 9), bg=SURFACE, fg=MUTED)
        self.step.pack()
        self.actions = tk.Frame(body, bg=SURFACE)
        self.actions.pack(pady=(int(16 * s), 0))
        self.angle, self.shown, self.target, self.done = 0, 0.0, 0.0, False
        self.place_centered()
        self.deiconify()
        self.attributes("-topmost", True)  # never hide behind the main window
        self.lift()
        self.grab_set()
        self.animate()

    def place_centered(self):
        self.update_idletasks()
        r = self.app.root
        x = r.winfo_rootx() + (r.winfo_width() - self.winfo_reqwidth()) // 2
        y = r.winfo_rooty() + (r.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f"{self.winfo_reqwidth()}x{self.winfo_reqheight()}+{x}+{y}")

    def animate(self):
        if not self.winfo_exists():
            return
        s, c = self.s, self.icon
        c.delete("all")
        m, d = int(6 * s), int(56 * s)
        if self.done:
            c.create_oval(m, m, d - m, d - m, fill=ACCENT_SOFT, outline=ACCENT_SOFT)
            c.create_line(d * .32, d * .52, d * .45, d * .65, d * .70, d * .38,
                          fill=ACCENT, width=int(4 * s), capstyle="round", joinstyle="round")
        else:
            c.create_oval(m, m, d - m, d - m, outline=PILL, width=int(5 * s))
            c.create_arc(m, m, d - m, d - m, start=self.angle, extent=100,
                         style="arc", outline=ACCENT, width=int(5 * s))
            self.angle = (self.angle - 9) % 360
        # ease the bar toward the real progress
        self.shown += (self.target - self.shown) * 0.18
        w, h = int(self.bar.cget("width")), int(self.bar.cget("height"))
        self.bar.delete("all")
        rounded(self.bar, 0, 0, w, h, h // 2, fill=PILL, outline=PILL)
        if self.shown > 0.01:
            rounded(self.bar, 0, 0, max(h, int(w * self.shown)), h, h // 2,
                    fill=ACCENT, outline=ACCENT)
        self.after(16, self.animate)

    def set_progress(self, fraction, step):
        self.target = max(self.target, min(1.0, fraction))
        self.step.configure(text=step)

    def finish(self, title, subtitle, buttons):
        self.done, self.target = True, 1.0
        self.title.configure(text=title)
        self.sub.configure(text=subtitle)
        self.step.configure(text="")
        self.step.pack_forget()
        for label, cmd, kind in buttons:
            Button(self.actions, label, cmd, kind=kind, s=self.s).pack(side="left", padx=4)
        self.place_centered()  # grow to fit the buttons

    def close(self):
        self.grab_release()
        self.destroy()


class App:
    def __init__(self, root):
        self.root = root
        self.s = root.winfo_fpixels("1i") / 96.0
        s = self.s
        root.title(APP_TITLE)
        root.geometry(f"{int(1180 * s)}x{int(740 * s)}")
        root.minsize(int(860 * s), int(520 * s))
        root.configure(bg=BG)
        try:
            root.iconbitmap(resource("icon.ico"))
        except tk.TclError:
            pass

        self.fonts = {k: pick_font(root, v) for k, v in ANSI_FONTS.items()}
        self.uni_family = pick_font(root, ["Nikosh", "SolaimanLipi", "Kalpurush", "Nirmala UI"])
        self.encoding = tk.StringVar(value="AdarshaLipi")
        self.size = 18

        # header
        header = tk.Frame(root, bg=SURFACE, padx=int(24 * s), pady=int(14 * s))
        header.pack(fill="x")
        tk.Frame(root, bg=BORDER, height=1).pack(fill="x")
        brand = tk.Frame(header, bg=SURFACE)
        brand.pack(side="left")
        try:
            self.logo = tk.PhotoImage(file=resource("icon.png"))
            factor = max(1, round(self.logo.width() / (36 * s)))
            self.logo = self.logo.subsample(factor)
            tk.Label(brand, image=self.logo, bg=SURFACE).pack(side="left", padx=(0, int(12 * s)))
        except tk.TclError:
            pass
        names = tk.Frame(brand, bg=SURFACE)
        names.pack(side="left")
        tk.Label(names, text=APP_TITLE, font=(UI, 15, "bold"), bg=SURFACE, fg=TEXT).pack(anchor="w")
        tk.Label(names, text="AdarshaLipi  ·  Bijoy   ↔   Unicode        ●  Works offline",
                 font=(UI, 9), bg=SURFACE, fg=MUTED).pack(anchor="w")
        self.seg = Segmented(header, list(ANSI_FONTS), self.encoding, self.apply_encoding, s=s)
        self.seg.pack(side="right")
        tk.Label(header, text="Old font", font=(UI, 9), bg=SURFACE, fg=MUTED).pack(side="right", padx=(0, 10))

        # action row
        actions = tk.Frame(root, bg=BG, padx=int(24 * s), pady=int(14 * s))
        actions.pack(fill="x")
        Button(actions, "Convert Word file", self.convert_word, kind="primary", s=s).pack(side="left")
        Button(actions, "Open text file", self.open_file, s=s).pack(side="left", padx=int(8 * s))
        Button(actions, "Clear", self.clear, s=s).pack(side="left")
        zoom = tk.Frame(actions, bg=BG)
        zoom.pack(side="right")
        tk.Label(zoom, text="Text size", font=(UI, 9), bg=BG, fg=MUTED).pack(side="left", padx=(0, 8))
        Button(zoom, "–", lambda: self.zoom(-2), s=s, pad=(12, 6)).pack(side="left")
        self.size_label = tk.Label(zoom, text=str(self.size), width=3, font=(UI, 10, "bold"),
                                   bg=BG, fg=TEXT)
        self.size_label.pack(side="left")
        Button(zoom, "+", lambda: self.zoom(2), s=s, pad=(12, 6)).pack(side="left")

        # bottom: status + convert buttons (packed before the cards so they stay visible)
        foot = tk.Frame(root, bg=BG, padx=int(24 * s))
        foot.pack(side="bottom", fill="x", pady=(0, int(12 * s)))
        self.status = tk.Label(foot, text="", font=(UI, 9), bg=BG, fg=MUTED, anchor="w")
        self.status.pack(fill="x")
        convert = tk.Frame(root, bg=BG, padx=int(24 * s))
        convert.pack(side="bottom", fill="x", pady=(int(4 * s), int(8 * s)))
        convert.columnconfigure(0, weight=1)
        convert.columnconfigure(1, weight=1)
        self.btn_uni = Button(convert, "", self.to_unicode, kind="primary", size=11, pad=(16, 11),
                              expand=True, s=s)
        self.btn_uni.grid(row=0, column=0, sticky="ew", padx=(0, int(6 * s)))
        self.btn_ansi = Button(convert, "", self.to_ansi, kind="outline", size=11, pad=(16, 11),
                               expand=True, s=s)
        self.btn_ansi.grid(row=0, column=1, sticky="ew", padx=(int(6 * s), 0))

        # text cards
        cards = tk.Frame(root, bg=BG, padx=int(24 * s))
        cards.pack(fill="both", expand=True)
        cards.columnconfigure(0, weight=1, uniform="c")
        cards.columnconfigure(1, weight=1, uniform="c")
        cards.rowconfigure(0, weight=1)
        self.ansi = self._card(cards, 0, self.fonts["AdarshaLipi"], "ansi")
        self.uni = self._card(cards, 1, self.uni_family, "uni")
        self.uni.label.configure(text="Unicode")
        self.uni.hint.configure(text="Works everywhere: Facebook, Google, email")

        root.bind("<F5>", lambda e: self.to_unicode())
        root.bind("<F6>", lambda e: self.to_ansi())
        self.apply_encoding()
        self.set_status("Paste text in a box and press a button below.     "
                        "Shortcuts: F5 → Unicode,  F6 → old font")

    def _card(self, parent, col, family, key):
        s = self.s
        card = tk.Frame(parent, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0, int(6 * s)) if col == 0 else (int(6 * s), 0))
        head = tk.Frame(card, bg=SURFACE, padx=int(16 * s), pady=int(12 * s))
        head.pack(fill="x")
        titles = tk.Frame(head, bg=SURFACE)
        titles.pack(side="left")
        label = tk.Label(titles, text="", font=(UI, 11, "bold"), bg=SURFACE, fg=TEXT)
        label.pack(anchor="w")
        hint = tk.Label(titles, text="", font=(UI, 8), bg=SURFACE, fg=MUTED)
        hint.pack(anchor="w")
        for text, cmd in (("Save", lambda: self.save_file(key)), ("Copy", lambda: self.copy(key)),
                          ("Paste", lambda: self.paste(key))):
            Button(head, text, cmd, s=s, size=9, pad=(12, 5)).pack(side="right", padx=(int(6 * s), 0))
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x")
        box = tk.Frame(card, bg=SURFACE)
        box.pack(fill="both", expand=True)
        txt = tk.Text(box, wrap="word", undo=True, height=6, width=20, font=(family, self.size),
                      relief="flat", bd=0, padx=int(16 * s), pady=int(12 * s), bg=SURFACE, fg=TEXT,
                      insertbackground=ACCENT, selectbackground="#BBF7D0", selectforeground=TEXT,
                      highlightthickness=0, spacing1=2, spacing3=2)
        sb = tk.Scrollbar(box, command=txt.yview, relief="flat", width=int(12 * s))
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        txt.family, txt.label, txt.hint = family, label, hint
        return txt

    # ------------------------------------------------------------- helpers
    def text(self, key):
        return self.ansi if key == "ansi" else self.uni

    def set_status(self, msg):
        self.status.configure(text=msg)

    def zoom(self, step):
        self.size = max(10, min(48, self.size + step))
        self.size_label.configure(text=str(self.size))
        for t in (self.ansi, self.uni):
            t.configure(font=(t.family, self.size))

    def apply_encoding(self):
        enc = self.encoding.get()
        self.seg.draw()
        self.ansi.family = self.fonts[enc]
        self.ansi.configure(font=(self.ansi.family, self.size))
        self.ansi.label.configure(text=enc)
        if self.fonts[enc] == "Segoe UI":
            self.ansi.hint.configure(text=f"{enc} font is not installed: letters show in English",
                                     fg="#B45309")
        else:
            self.ansi.hint.configure(text=f"Old {enc} font text", fg=MUTED)
        self.btn_uni.set_text(f"{enc}   →   Unicode")
        self.btn_ansi.set_text(f"Unicode   →   {enc}")

    # ------------------------------------------------------------- text actions
    def to_unicode(self):
        src = self.ansi.get("1.0", "end-1c")
        if not src.strip():
            self.set_status(f"The {self.encoding.get()} box is empty. Paste some text first.")
            return
        note = ""
        guess = guess_encoding(src)
        if guess and guess != self.encoding.get():
            self.encoding.set(guess)
            self.apply_encoding()
            note = f"  (detected {guess} automatically)"
        enc = self.encoding.get()
        self.uni.delete("1.0", "end")
        self.uni.insert("1.0", ansi_to_unicode(src, enc))
        self.set_status(f"✓  {enc} → Unicode done{note}")

    def to_ansi(self):
        enc = self.encoding.get()
        src = self.uni.get("1.0", "end-1c")
        if not src.strip():
            self.set_status("The Unicode box is empty. Paste some text first.")
            return
        self.ansi.delete("1.0", "end")
        self.ansi.insert("1.0", unicode_to_ansi(src, enc))
        self.set_status(f"✓  Unicode → {enc} done")

    def copy(self, key):
        data = self.text(key).get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(data)
        self.set_status("✓  Copied")

    def paste(self, key):
        try:
            data = self.root.clipboard_get()
        except tk.TclError:
            return
        t = self.text(key)
        t.delete("1.0", "end")
        t.insert("1.0", data)

    def clear(self):
        self.ansi.delete("1.0", "end")
        self.uni.delete("1.0", "end")
        self.set_status("")

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        if os.path.getsize(path) > MAX_TXT:
            messagebox.showerror(APP_TITLE, "This file is too large (limit 20 MB).")
            return
        with open(path, "rb") as f:
            raw = f.read()
        try:
            data = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            data = raw.decode("cp1252", errors="replace")
        # Bangla Unicode letters mean it is a Unicode file, otherwise ANSI
        key = "uni" if any("ঀ" <= c <= "৿" for c in data) else "ansi"
        t = self.text(key)
        t.delete("1.0", "end")
        t.insert("1.0", data)
        if key == "ansi" and guess_encoding(data):
            self.encoding.set(guess_encoding(data))
            self.apply_encoding()
        box = "Unicode" if key == "uni" else self.encoding.get()
        self.set_status(f"Opened {os.path.basename(path)} in the {box} box")

    def save_file(self, key):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text files", "*.txt")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.text(key).get("1.0", "end-1c"))
        self.set_status(f"✓  Saved {os.path.basename(path)}")

    # ------------------------------------------------------------- Word files
    def convert_word(self):
        path = filedialog.askopenfilename(
            title="Choose a Word file",
            filetypes=[("Word files", "*.docx *.doc"), ("All files", "*.*")])
        if not path:
            return
        if path.lower().endswith(".doc"):
            messagebox.showinfo(APP_TITLE, "This is an old Word file (.doc).\n\n"
                                "Open it in Word, choose File → Save As → Word Document (*.docx), "
                                "then convert the new .docx file.")
            return
        try:
            counts = docx_convert.inspect(path)
        except Exception as e:  # unsafe, damaged or not a real .docx
            messagebox.showerror(APP_TITLE, f"Could not read this Word file.\n\n{e}")
            return
        ansi = counts["AdarshaLipi"] + counts["Bijoy"]
        if ansi == 0 and counts["Unicode"] == 0:
            messagebox.showinfo(APP_TITLE, "No AdarshaLipi, Bijoy or Unicode Bangla text found in this file.")
            return
        if ansi:
            direction, target, label = "to_unicode", "AdarshaLipi", "Unicode"
            found = " + ".join(k for k in ("AdarshaLipi", "Bijoy") if counts[k])
        else:
            target = self.encoding.get()
            direction, label, found = "to_ansi", target, "Unicode"
        base = os.path.splitext(os.path.basename(path))[0]
        dst = filedialog.asksaveasfilename(
            title=f"Save the {label} copy as  (your original file is not changed)",
            defaultextension=".docx", initialfile=f"{base} ({label}).docx",
            initialdir=os.path.dirname(path), filetypes=[("Word files", "*.docx")])
        if not dst:
            return
        if not dst.lower().endswith(".docx"):  # never save or open anything but a Word file
            dst += ".docx"
        if os.path.normcase(os.path.abspath(dst)) == os.path.normcase(os.path.abspath(path)):
            messagebox.showerror(APP_TITLE, "Please save with a different name so the original stays safe.")
            return
        self.run_word_job(path, dst, direction, target, f"{found}  →  {label}")

    def run_word_job(self, src, dst, direction, target, route):
        card = BusyCard(self, "Converting Word file", f"{os.path.basename(src)}\n{route}")
        card.set_progress(0.05, "Reading the file…")
        events = queue.Queue()

        def work():
            try:
                n = docx_convert.convert_docx(
                    src, dst, direction, target,
                    progress=lambda i, total: events.put(("progress", i / total)))
                events.put(("done", n))
            except PermissionError:
                events.put(("error", "Could not save. If that file is open in Word, close it and try again."))
            except Exception as e:  # unsafe or damaged file
                events.put(("error", f"Could not convert this Word file.\n\n{e}"))

        started = time.monotonic()
        threading.Thread(target=work, daemon=True).start()
        result = {}
        steps = ["Reading the file…", "Converting text, tables and headers…", "Saving the new file…"]

        def poll():
            while not events.empty():
                kind, value = events.get()
                result[kind] = value
            # reveal the real progress over at least MIN_BUSY_SECONDS so it can be followed
            elapsed = time.monotonic() - started
            paced = min(result.get("progress", 0), elapsed / MIN_BUSY_SECONDS)
            card.set_progress(0.05 + 0.95 * paced, steps[min(2, int(paced * 3))])
            if "error" in result:
                card.close()
                messagebox.showerror(APP_TITLE, result["error"])
            elif "done" in result and elapsed >= MIN_BUSY_SECONDS:
                self.set_status(f"✓  Word file saved: {os.path.basename(dst)}")
                card.finish("Conversion complete",
                            f"{result['done']} pieces of text converted.\nSaved as {os.path.basename(dst)}",
                            [("Open file", lambda: (card.close(), os.startfile(dst)), "primary"),
                             ("Show folder", lambda: (card.close(), os.startfile(os.path.dirname(dst))),
                              "ghost"),
                             ("Close", card.close, "ghost")])
            else:
                self.root.after(50, poll)

        poll()


def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    for f in ("Nikosh.ttf",):  # AdarshaLipi/SutonnyMJ are not ours to redistribute; use installed copies
        load_private_font(resource(f))
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
