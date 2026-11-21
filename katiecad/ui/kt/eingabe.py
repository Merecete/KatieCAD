# -*- coding: utf-8 -*-
"""
katiecad/ui/kt/eingabe.py - text input widgets of the Kivy layer: Entry, Text, Listbox
(BSD-3-Clause).

The editing (cursor, selection, clipboard, keys) is done here in Python, the keys reach
the widget through the class bindings in klassen.py like under Tk.
"""

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

from katiecad.ui.kt import fontmod, events as EV
from katiecad.ui.kt import tkmod as T


# ------------------------------------------------------------ cursor blinking
class _Blinker:
    an = True
    widget = None
    _kt_ev = None

    @classmethod
    def start(cls, w):
        cls.widget = w
        cls.an = True
        if cls._kt_ev is None:
            cls._kt_ev = Clock.schedule_interval(cls._kt_tick, 0.53)

    @classmethod
    def stop(cls, w):
        if cls.widget is w:
            cls.widget = None

    @classmethod
    def _kt_tick(cls, _dt):
        w = cls.widget
        if w is None or w._kt_zerstoert:
            return
        cls.an = not cls.an
        w._kt_neu_zeichnen()

    @classmethod
    def zuruecksetzen(cls):
        cls.an = True


# ============================================================
# Single-line editing (Entry, ttk.Entry, Combobox, Spinbox)
# ============================================================
class EditMixin:
    """Needs: self._kt_o (textvariable, show, state, font, justify), self._kt_innen_text()."""

    def _kt_edit_init(self):
        self._kt_text = ""
        self._kt_cur = 0
        self._kt_sel = None             # (a, b) or None
        self._anker = 0
        self._kt_xscroll = 0
        var = self._kt_o.get("textvariable")
        if isinstance(var, T.Variable):
            self._kt_text = str(var._kt_roh())

    # -- value
    def _kt_wert(self):
        var = self._kt_o.get("textvariable")
        if isinstance(var, T.Variable):
            return str(var._kt_roh())
        return self._kt_text

    def _kt_wert_setzen(self, s):
        var = self._kt_o.get("textvariable")
        self._kt_text = s
        if isinstance(var, T.Variable):
            self._kt_intern = True
            try:
                var.set(s)
            finally:
                self._kt_intern = False
        self._kt_cur = max(0, min(self._kt_cur, len(s)))
        self._kt_neu_zeichnen()

    def _kt_variable_geaendert(self, var):
        if getattr(self, "_kt_intern", False):
            return
        self._kt_text = str(var._kt_roh())
        self._kt_cur = len(self._kt_text)
        self._kt_sel = None
        self._kt_xscroll = 0
        self._kt_neu_zeichnen()

    def _kt_bearbeitbar(self):
        st = str(self._kt_o.get("state", "normal"))
        return st not in ("disabled", "readonly") and "disabled" not in self._kt_zustand \
            and "readonly" not in self._kt_zustand

    # -- Tk API
    def _kt_index(self, i):
        """Entry index ("end", "insert", "anchor", "sel.first", "sel.last", "@x" or a number) ->
        character position, as Tk's entry index command.
        """
        t = self._kt_wert()
        if i in (T.END, "end"):
            return len(t)
        if i in (T.INSERT, "insert"):
            return self._kt_cur
        if i == "anchor":
            return self._anker
        if i in ("sel.first", T.SEL_FIRST):
            if not self._kt_sel:
                raise T.TclError("selection isn't in widget")
            return self._kt_sel[0]
        if i in ("sel.last", T.SEL_LAST):
            if not self._kt_sel:
                raise T.TclError("selection isn't in widget")
            return self._kt_sel[1]
        if isinstance(i, str) and i.startswith("@"):
            return self._kt_pos_bei(int(float(i[1:])))
        return max(0, min(len(t), int(i)))

    def get(self):
        return self._kt_wert()

    def insert(self, index, string):
        t = self._kt_wert()
        i = self._kt_index(index)
        s = str(string)
        if i <= self._kt_cur:
            self._kt_cur += len(s)
        self._kt_wert_setzen(t[:i] + s + t[i:])

    def delete(self, first, last=None):
        t = self._kt_wert()
        a = self._kt_index(first)
        b = self._kt_index(last) if last is not None else a + 1
        if b < a:
            a, b = b, a
        if self._kt_cur > a:
            self._kt_cur = max(a, self._kt_cur - (b - a))
        self._kt_sel = None
        self._kt_wert_setzen(t[:a] + t[b:])

    def icursor(self, index):
        self._kt_cur = self._kt_index(index)
        self._kt_neu_zeichnen()

    def index(self, index):
        return self._kt_index(index)

    def select_range(self, start, end):
        a, b = self._kt_index(start), self._kt_index(end)
        self._kt_sel = (min(a, b), max(a, b)) if a != b else None
        self._anker = a
        self._kt_neu_zeichnen()

    selection_range = select_range

    def select_clear(self):
        self._kt_sel = None
        self._kt_neu_zeichnen()

    selection_clear = select_clear

    def select_present(self):
        return bool(self._kt_sel)

    selection_present = select_present

    def select_from(self, index):
        self._anker = self._kt_index(index)

    selection_from = select_from

    def select_to(self, index):
        self.select_range(self._anker, index)

    selection_to = select_to

    def select_adjust(self, index):
        self.select_to(index)

    def xview(self, *args):
        return (0.0, 1.0)

    def xview_moveto(self, f):
        pass

    def xview_scroll(self, n, what):
        pass

    def validate(self):
        return True

    # -- display helpers
    def _kt_anzeige(self):
        t = self._kt_wert()
        show = self._kt_o.get("show")
        return show[0] * len(t) if show else t

    def _kt_pos_bei(self, x):
        """Widget x -> character index."""
        t = self._kt_anzeige()
        font = self._kt_o.get("font")
        l = self._kt_text_x0()
        rel = x - l + self._kt_xscroll
        if rel <= 0:
            return 0
        vor = 0
        for i in range(1, len(t) + 1):
            w = fontmod.text_breite(t[:i], font)
            if w >= rel:
                return i if (w - rel) < (rel - vor) else i - 1
            vor = w
        return len(t)

    def _kt_text_x0(self):
        return self._kt_innen_text()[0]

    def _kt_text_malen(self, g, kx, ky, fg, sel_bg, sel_fg, aktiv):
        """Draws the text of a one-line field: selection background, text (shown in the colours
        of the selection where selected) and the blinking cursor when the field has the
        focus. The text is shifted sideways so the cursor stays visible in a narrow field.
        """
        l, t, r, b = self._kt_innen_text()
        bw = self._kt_w - l - r
        bh = self._kt_h - t - b
        font = self._kt_o.get("font")
        text = self._kt_anzeige()
        lh = fontmod.zeilen_hoehe(font)
        cur_x = fontmod.text_breite(text[:self._kt_cur], font)
        gesamt = fontmod.text_breite(text, font)
        just = self._kt_o.get("justify", "left")
        # keep the cursor visible
        if aktiv:
            if cur_x - self._kt_xscroll > bw - 2:
                self._kt_xscroll = cur_x - bw + 2
            if cur_x - self._kt_xscroll < 0:
                self._kt_xscroll = max(0, cur_x - 10)
        if gesamt <= bw:
            self._kt_xscroll = 0
        versatz = 0
        if gesamt < bw and just == "center":
            versatz = (bw - gesamt) // 2
        elif gesamt < bw and just == "right":
            versatz = bw - gesamt
        y0 = t + (bh - lh) // 2
        ky_text = ky + self._kt_h - y0 - lh
        if self._kt_sel and aktiv is not None:
            a, e = self._kt_sel
            xa = fontmod.text_breite(text[:a], font) - self._kt_xscroll + versatz
            xe = fontmod.text_breite(text[:e], font) - self._kt_xscroll + versatz
            xa, xe = max(0, xa), min(bw, xe)
            if xe > xa:
                g.add(Color(*sel_bg))
                g.add(Rectangle(pos=(kx + l + xa, ky_text), size=(xe - xa, lh)))
        tex = fontmod.text_textur(text, font)
        if tex is not None:
            tw, th = tex.size
            sx = self._kt_xscroll
            breite = max(0, min(tw - sx, bw - versatz))
            if breite > 0:
                region = tex.get_region(sx, 0, breite, th)
                fontmod.text_zeichnen(g, region, fg, (kx + l + versatz, ky_text), (breite, th))
        if aktiv and _Blinker.an and self._kt_bearbeitbar():
            cx = cur_x - self._kt_xscroll + versatz
            if 0 <= cx <= bw:
                farbe = T._rgba(self._kt_o.get("insertbackground"), fg) or fg
                g.add(Color(*farbe))
                g.add(Rectangle(pos=(kx + l + cx, ky_text), size=(1, lh)))

    # -- editing (called by the class bindings)
    def _kt_text_eingabe(self, s):
        """Typed text: replaces the selection or is inserted at the cursor (line breaks
        removed), unless the field is readonly / disabled or validatecommand rejects the new
        value.
        """
        if not self._kt_bearbeitbar() or not s:
            return
        s = s.replace("\r", "").replace("\n", "")
        if not s:
            return
        t = self._kt_wert()
        if self._kt_sel:
            a, b = self._kt_sel
            t = t[:a] + t[b:]
            self._kt_cur = a
            self._kt_sel = None
        neu = t[:self._kt_cur] + s + t[self._kt_cur:]
        if not self._kt_pruefen(neu, s, self._kt_cur, "1"):
            return
        self._kt_cur += len(s)
        _Blinker.zuruecksetzen()
        self._kt_wert_setzen(neu)

    def _kt_pruefen(self, neu, s, idx, aktion):
        """Runs validatecommand like Tk for the change `aktion` (insert / delete): the Tk
        substitutions (%P new value, %S inserted text, %i index, %d action ...) are passed in
        the order registered. True if the change may happen.
        """
        vc = self._kt_o.get("validatecommand")
        modus = self._kt_o.get("validate", "none")
        if not vc or modus in ("none", None, ""):
            return True
        if isinstance(vc, (tuple, list)):
            f = vc[0]
            if isinstance(f, str):
                f = self._kt_root_._kt_befehle.get(f)
            ersatz = {"%P": neu, "%S": s, "%s": self._kt_wert(), "%d": aktion, "%i": str(idx),
                      "%V": "key", "%v": modus, "%W": str(self)}
            args = [ersatz.get(a, a) for a in vc[1:]]
            try:
                return bool(f(*args)) if f else True
            except Exception:
                return True
        f = self._kt_root_._kt_befehle.get(vc) if isinstance(vc, str) else vc
        try:
            return bool(f()) if callable(f) else True
        except Exception:
            return True

    def _kt_taste(self, ev):
        """Key in a one-line field: cursor movement (with Shift: selection, with Ctrl: word by
        word), Home / End, delete keys, Ctrl+A / C / X / V. Other keys are left to the text
        input (_kt_text_eingabe).
        """
        ks = ev.keysym
        t = self._kt_wert()
        shift = bool(ev.state & EV.SHIFT)
        ctrl = bool(ev.state & EV.CONTROL)
        _Blinker.zuruecksetzen()
        if ctrl and ks.lower() == "a":
            self.select_range(0, T.END)
            self._kt_cur = len(t)
            return
        if ctrl and ks.lower() == "c":
            self._kt_kopieren()
            return
        if ctrl and ks.lower() == "x":
            if self._kt_bearbeitbar() and self._kt_sel:
                self._kt_kopieren()
                self._kt_auswahl_loeschen()
            return
        if ctrl and ks.lower() == "v":
            if self._kt_bearbeitbar():
                try:
                    s = self.clipboard_get()
                except T.TclError:
                    s = ""
                self._kt_text_eingabe(s.split("\n")[0])
            return
        if ks == "BackSpace":
            if not self._kt_bearbeitbar():
                return
            if self._kt_sel:
                self._kt_auswahl_loeschen()
            elif self._kt_cur > 0:
                neu = t[:self._kt_cur - 1] + t[self._kt_cur:]
                if self._kt_pruefen(neu, t[self._kt_cur - 1], self._kt_cur - 1, "0"):
                    self._kt_cur -= 1
                    self._kt_wert_setzen(neu)
            return
        if ks == "Delete":
            if not self._kt_bearbeitbar():
                return
            if self._kt_sel:
                self._kt_auswahl_loeschen()
            elif self._kt_cur < len(t):
                neu = t[:self._kt_cur] + t[self._kt_cur + 1:]
                if self._kt_pruefen(neu, t[self._kt_cur], self._kt_cur, "0"):
                    self._kt_wert_setzen(neu)
            return
        bewegung = {"Left": self._kt_cur - 1, "Right": self._kt_cur + 1, "Home": 0, "End": len(t)}
        if ks in bewegung:
            neu = max(0, min(len(t), bewegung[ks]))
            if ctrl and ks in ("Left", "Right"):
                neu = self._kt_wortgrenze(t, self._kt_cur, -1 if ks == "Left" else 1)
            if shift:
                if not self._kt_sel:
                    self._anker = self._kt_cur
                a, b = self._anker, neu
                self._kt_sel = (min(a, b), max(a, b)) if a != b else None
            else:
                if self._kt_sel and ks in ("Left", "Right"):
                    neu = self._kt_sel[0] if ks == "Left" else self._kt_sel[1]
                self._kt_sel = None
            self._kt_cur = neu
            self._kt_neu_zeichnen()

    @staticmethod
    def _kt_wortgrenze(t, i, r):
        """Position of the next word boundary from `i` in direction `r` (-1 left, +1 right) -
        for Ctrl+arrow and double click.
        """
        if r < 0:
            i -= 1
            while i > 0 and not t[i - 1].isalnum():
                i -= 1
            while i > 0 and t[i - 1].isalnum():
                i -= 1
            return max(0, i)
        n = len(t)
        while i < n and t[i].isalnum():
            i += 1
        while i < n and not t[i].isalnum():
            i += 1
        return i

    def _kt_kopieren(self):
        if self._kt_sel and not self._kt_o.get("show"):
            a, b = self._kt_sel
            self.clipboard_clear()
            self.clipboard_append(self._kt_wert()[a:b])

    def _kt_auswahl_loeschen(self):
        a, b = self._kt_sel
        t = self._kt_wert()
        self._kt_sel = None
        self._kt_cur = a
        self._kt_wert_setzen(t[:a] + t[b:])

    def _kt_maus_runter(self, ev):
        """Mouse press in a one-line field: places the cursor; a double click selects the word,
        a triple click everything.
        """
        self.focus_set()
        i = self._kt_pos_bei(ev.x)
        if ev._kt_klicks >= 3:
            self.select_range(0, T.END)
            return
        if ev._kt_klicks == 2:
            t = self._kt_wert()
            a = self._kt_wortgrenze(t, i + 1 if i < len(t) else i, -1) if t else 0
            b = i
            while b < len(t) and t[b].isalnum():
                b += 1
            self._kt_sel = (a, b) if b > a else None
            self._kt_cur = b
            self._kt_neu_zeichnen()
            return
        if ev.state & EV.SHIFT:
            a = self._anker
            self._kt_sel = (min(a, i), max(a, i)) if a != i else None
        else:
            self._anker = i
            self._kt_sel = None
        self._kt_cur = i
        _Blinker.zuruecksetzen()
        self._kt_neu_zeichnen()

    def _kt_maus_ziehen(self, ev):
        i = self._kt_pos_bei(ev.x)
        a = self._anker
        self._kt_sel = (min(a, i), max(a, i)) if a != i else None
        self._kt_cur = i
        self._kt_neu_zeichnen()

    def _kt_fokus_aenderung(self):
        if "focus" in self._kt_zustand:
            _Blinker.start(self)
        else:
            _Blinker.stop(self)
            self._kt_sel = None if not getattr(self, "_sel_behalten", False) else self._kt_sel
        self._kt_neu_zeichnen()

    def _kt_nimmt_fokus(self):
        return "disabled" not in self._kt_zustand and self._kt_o.get("takefocus", 1) not in (0, "0")


# ============================================================
# tk.Entry
# ============================================================
class Entry(EditMixin, T.BaseWidget):
    _kt_klasse = "Entry"
    _kt_standard = {"background": "#ffffff", "foreground": "#000000", "font": "TkTextFont",
                 "borderwidth": 1, "relief": T.SUNKEN, "highlightthickness": 1,
                 "highlightbackground": "#f0f0f0", "highlightcolor": "#000000", "width": 20,
                 "textvariable": None, "show": "", "state": "normal", "justify": "left",
                 "insertbackground": "#000000", "selectbackground": "#0078d7",
                 "selectforeground": "#ffffff", "disabledbackground": "#f0f0f0",
                 "disabledforeground": "#6d6d6d", "readonlybackground": "#f0f0f0",
                 "cursor": "xterm", "validate": "none", "validatecommand": None,
                 "exportselection": 1, "takefocus": 1, "insertwidth": 2}

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__(master, cnf, **kw)
        self._kt_edit_init()

    def _kt_innen_text(self):
        b = T._int(self._kt_o.get("borderwidth", 1)) + T._int(self._kt_o.get("highlightthickness", 1))
        return b + 1, b, b + 1, b

    def _kt_natuerlich(self):
        font = self._kt_o.get("font")
        l, t, r, b = self._kt_innen_text()
        return (T._int(self._kt_o.get("width", 20)) * fontmod.text_breite("0", font) + l + r,
                fontmod.zeilen_hoehe(font) + t + b + 2)

    def _kt_malen(self, kx, ky):
        st = self._kt_o.get("state")
        bg = self._kt_farbe_opt("disabledbackground" if st == "disabled" else
                             ("readonlybackground" if st == "readonly" else "background"))
        self._kt_hintergrund(kx, ky, bg)
        fg = self._kt_farbe_opt("disabledforeground" if st == "disabled" else "foreground", (0, 0, 0, 1))
        self._kt_text_malen(self._kt_g_inhalt, kx, ky, fg, self._kt_farbe_opt("selectbackground", (0, 0.47, 0.84, 1)),
                         self._kt_farbe_opt("selectforeground", (1, 1, 1, 1)), "focus" in self._kt_zustand)


# ============================================================
# tk.Text (multi-line, plain text; tags only for colours)
# ============================================================
class Text(T.BaseWidget):
    _kt_klasse = "Text"
    _kt_standard = {"background": "#ffffff", "foreground": "#000000", "font": "TkFixedFont",
                 "borderwidth": 1, "relief": T.SUNKEN, "highlightthickness": 1,
                 "highlightbackground": "#f0f0f0", "highlightcolor": "#000000", "width": 80,
                 "height": 24, "wrap": "char", "state": "normal", "padx": 1, "pady": 1,
                 "insertbackground": "#000000", "selectbackground": "#0078d7",
                 "selectforeground": "#ffffff", "cursor": "xterm", "yscrollcommand": None,
                 "xscrollcommand": None, "takefocus": 1, "undo": False, "spacing1": 0,
                 "spacing3": 0, "relief_": None}

    def __init__(self, master=None, cnf=None, **kw):
        self._kt_inhalt = ""
        self._kt_cur = 0
        self._kt_sel = None
        self._anker = 0
        self._kt_oben = 0                 # first visible display line
        self._tags = {}
        super().__init__(master, cnf, **kw)

    # -- indices "line.char", "end", "insert", modifiers "+Nc", "-1c", "lineend"
    def _kt_idx(self, index):
        """Text index ("line.char", "end", "insert", "sel.first", "1.0 lineend", "insert+3c"
        ...) -> position in the content string. Only the forms KatieCAD uses are supported;
        offsets in lines are ignored.
        """
        s = self._kt_inhalt
        if isinstance(index, (int, float)) and not isinstance(index, bool):
            index = str(index)
        index = str(index).strip()
        # split "base +/- modifiers": "insert+3c" -> "insert", "+3c"; "1.0 lineend" -> "1.0", " lineend"
        basis = index
        rest = ""
        for i, ch in enumerate(index):
            if ch in "+-" and i > 0:
                basis, rest = index[:i], index[i:]
                break
            if ch == " " and i > 0:
                basis, rest = index[:i], index[i:]
                break
        basis = basis.strip()
        if basis in ("end", T.END):
            pos = len(s) + 1           # Tk: "end" is after the implicit final newline
        elif basis in ("insert", T.INSERT):
            pos = self._kt_cur
        elif basis in ("sel.first",):
            if not self._kt_sel:
                raise T.TclError("text doesn't contain any characters tagged with \"sel\"")
            pos = self._kt_sel[0]
        elif basis in ("sel.last",):
            if not self._kt_sel:
                raise T.TclError("text doesn't contain any characters tagged with \"sel\"")
            pos = self._kt_sel[1]
        elif basis.startswith("@"):
            pos = len(s)
        elif "." in basis:
            z, c = basis.split(".", 1)
            zeilen = s.split("\n")
            zi = max(1, int(z)) - 1
            if zi >= len(zeilen):
                pos = len(s)
            else:
                pos = sum(len(x) + 1 for x in zeilen[:zi])
                if c == "end":
                    pos += len(zeilen[zi])
                else:
                    pos += min(int(c), len(zeilen[zi]))
        else:
            try:
                pos = int(basis)
            except ValueError:
                pos = len(s)
        for teil in rest.replace("+", " +").replace("-", " -").split():
            t = teil.strip()
            if not t:
                continue
            if t in ("lineend",):
                e = s.find("\n", pos)
                pos = len(s) if e < 0 else e
            elif t in ("linestart",):
                pos = s.rfind("\n", 0, pos) + 1
            else:
                try:
                    zahl = int("".join(ch for ch in t if ch in "+-0123456789"))
                except ValueError:
                    continue
                if t.endswith(("c", "chars")) or t[-1].isdigit():
                    pos += zahl
                # offsets in lines ("+1l", "+2 lines") are not used by KatieCAD: ignored
        return max(0, min(len(s) + 1, pos))

    def _kt_pos_text(self, pos):
        s = self._kt_inhalt[:pos]
        z = s.count("\n") + 1
        c = len(s) - (s.rfind("\n") + 1)
        return f"{z}.{c}"

    def index(self, index):
        return self._kt_pos_text(min(self._kt_idx(index), len(self._kt_inhalt)))

    def get(self, index1="1.0", index2=None):
        a = self._kt_idx(index1)
        b = self._kt_idx(index2) if index2 is not None else a + 1
        s = self._kt_inhalt + "\n"
        return s[a:b]

    def insert(self, index, chars, *tags):
        i = min(self._kt_idx(index), len(self._kt_inhalt))
        s = str(chars)
        self._kt_inhalt = self._kt_inhalt[:i] + s + self._kt_inhalt[i:]
        if self._kt_cur >= i:
            self._kt_cur += len(s)
        self._kt_geaendert()

    def delete(self, index1, index2=None):
        a = min(self._kt_idx(index1), len(self._kt_inhalt))
        b = min(self._kt_idx(index2), len(self._kt_inhalt)) if index2 is not None else a + 1
        if b < a:
            a, b = b, a
        self._kt_inhalt = self._kt_inhalt[:a] + self._kt_inhalt[b:]
        if self._kt_cur > a:
            self._kt_cur = max(a, self._kt_cur - (b - a))
        self._kt_sel = None
        self._kt_geaendert()

    def replace(self, index1, index2, chars, *args):
        self.delete(index1, index2)
        self.insert(index1, chars)

    def _kt_geaendert(self):
        self._kt_neu_zeichnen()
        self._kt_scroll_melden()
        try:
            self._kt_ereignis("Virtual", _kt_virtuell="<<Modified>>")
        except Exception:
            pass

    def see(self, index):
        """see(index): scrolls so the line of `index` is visible."""
        pos = min(self._kt_idx(index), len(self._kt_inhalt))
        zeilen = self._kt_anzeige_zeilen()
        n = 0
        for k, (a, b, _z) in enumerate(zeilen):
            if a <= pos <= b:
                n = k
                break
        sicht = self._kt_sicht_zeilen()
        if n < self._kt_oben:
            self._kt_oben = n
        elif n >= self._kt_oben + sicht:
            self._kt_oben = n - sicht + 1
        self._kt_neu_zeichnen()
        self._kt_scroll_melden()

    def mark_set(self, name, index):
        if name == "insert":
            self._kt_cur = min(self._kt_idx(index), len(self._kt_inhalt))
            self._kt_neu_zeichnen()

    def mark_unset(self, *names):
        pass

    def tag_configure(self, tagName, cnf=None, **kw):
        self._tags.setdefault(tagName, {}).update(kw)

    tag_config = tag_configure

    def tag_add(self, tagName, index1, *args):
        if tagName == "sel":
            a = self._kt_idx(index1)
            b = self._kt_idx(args[0]) if args else a + 1
            self._kt_sel = (min(a, b), max(a, b))
            self._kt_neu_zeichnen()

    def tag_remove(self, tagName, index1, index2=None):
        if tagName == "sel":
            self._kt_sel = None
            self._kt_neu_zeichnen()

    def tag_delete(self, *names):
        pass

    def tag_ranges(self, tagName):
        if tagName == "sel" and self._kt_sel:
            return (self._kt_pos_text(self._kt_sel[0]), self._kt_pos_text(self._kt_sel[1]))
        return ()

    def edit_modified(self, arg=None):
        return False

    def edit_reset(self):
        pass

    def edit_separator(self):
        pass

    def window_create(self, index, **kw):
        pass

    def image_create(self, index, **kw):
        pass

    def search(self, pattern, index, stopindex=None, **kw):
        i = self._kt_inhalt.find(pattern, self._kt_idx(index))
        return self._kt_pos_text(i) if i >= 0 else ""

    # -- layout
    def _kt_innen_text(self):
        b = T._int(self._kt_o.get("borderwidth", 1)) + T._int(self._kt_o.get("highlightthickness", 1))
        px, py = T._int(self._kt_o.get("padx", 1)), T._int(self._kt_o.get("pady", 1))
        return b + px, b + py, b + px, b + py

    def _kt_natuerlich(self):
        font = self._kt_o.get("font")
        l, t, r, b = self._kt_innen_text()
        return (T._int(self._kt_o.get("width", 80)) * fontmod.text_breite("0", font) + l + r,
                T._int(self._kt_o.get("height", 24)) * fontmod.zeilen_hoehe(font) + t + b)

    def _kt_anzeige_zeilen(self):
        """-> [(start, end, text)] display lines after wrapping."""
        font = self._kt_o.get("font")
        l, t, r, b = self._kt_innen_text()
        breite = self._kt_w - l - r - 2
        wrap = self._kt_o.get("wrap", "char")
        erg = []
        pos = 0
        for zeile in self._kt_inhalt.split("\n"):
            if wrap == "none" or breite <= 10 or fontmod.text_breite(zeile, font) <= breite:
                erg.append((pos, pos + len(zeile), zeile))
            else:
                teile = fontmod.umbrechen(zeile, font, breite) if wrap == "word" else \
                    _zeichen_umbruch(zeile, font, breite)
                p = pos
                for k, teil in enumerate(teile):
                    start = zeile.find(teil, p - pos) + pos if teil else p
                    erg.append((start, start + len(teil), teil))
                    p = start + len(teil)
            pos += len(zeile) + 1
        return erg

    def _kt_sicht_zeilen(self):
        l, t, r, b = self._kt_innen_text()
        return max(1, (self._kt_h - t - b) // max(1, fontmod.zeilen_hoehe(self._kt_o.get("font"))))

    def _kt_scroll_melden(self):
        cmd = self._kt_o.get("yscrollcommand")
        if cmd:
            n = max(1, len(self._kt_anzeige_zeilen()))
            s = self._kt_sicht_zeilen()
            try:
                cmd(self._kt_oben / n, min(1.0, (self._kt_oben + s) / n))
            except Exception:
                pass

    def yview(self, *args):
        """yview(): visible part as fractions; "moveto" a fraction or "scroll" n units / pages
        (one unit = one line).
        """
        n = max(1, len(self._kt_anzeige_zeilen()))
        s = self._kt_sicht_zeilen()
        if not args:
            return (self._kt_oben / n, min(1.0, (self._kt_oben + s) / n))
        if args[0] == "moveto":
            self._kt_oben = int(float(args[1]) * n)
        elif args[0] == "scroll":
            k = int(float(args[1]))
            self._kt_oben += k * (s if str(args[2]).startswith("page") else 1)
        self._kt_oben = max(0, min(self._kt_oben, max(0, n - s)))
        self._kt_neu_zeichnen()
        self._kt_scroll_melden()

    def yview_moveto(self, f):
        self.yview("moveto", f)

    def yview_scroll(self, n, what):
        self.yview("scroll", n, what)

    def xview(self, *args):
        return (0.0, 1.0)

    def _kt_setzen(self, x, y, w, h, sichtbar=True):
        super()._kt_setzen(x, y, w, h, sichtbar)
        self._kt_scroll_melden()

    def _kt_malen(self, kx, ky):
        """Draws the multi-line text: visible lines from the first shown one (_kt_oben),
        selection background, the text and the cursor when focused.
        """
        disabled = self._kt_o.get("state") == "disabled"
        self._kt_hintergrund(kx, ky)
        g = self._kt_g_inhalt
        font = self._kt_o.get("font")
        fg = self._kt_farbe_opt("foreground", (0, 0, 0, 1))
        sel_bg = self._kt_farbe_opt("selectbackground", (0, 0.47, 0.84, 1))
        l, t, r, b = self._kt_innen_text()
        lh = fontmod.zeilen_hoehe(font)
        zeilen = self._kt_anzeige_zeilen()
        s = self._kt_sicht_zeilen()
        aktiv = "focus" in self._kt_zustand
        for k in range(self._kt_oben, min(len(zeilen), self._kt_oben + s)):
            a, e, text = zeilen[k]
            y = t + (k - self._kt_oben) * lh
            ky_z = ky + self._kt_h - y - lh
            if self._kt_sel:
                sa, se = max(a, self._kt_sel[0]), min(e, self._kt_sel[1])
                if se > sa:
                    xa = fontmod.text_breite(text[:sa - a], font)
                    xe = fontmod.text_breite(text[:se - a], font)
                    g.add(Color(*sel_bg))
                    g.add(Rectangle(pos=(kx + l + xa, ky_z), size=(xe - xa, lh)))
            tex = fontmod.text_textur(text, font)
            if tex is not None:
                tw = min(tex.size[0], self._kt_w - l - r)
                fontmod.text_zeichnen(g, tex.get_region(0, 0, tw, tex.size[1]), fg, (kx + l, ky_z),
                                      (tw, tex.size[1]))
            if aktiv and not disabled and _Blinker.an and a <= self._kt_cur <= e:
                naechste = zeilen[k + 1][0] if k + 1 < len(zeilen) else None
                if self._kt_cur < e or naechste is None or naechste > e:
                    cx = fontmod.text_breite(text[:self._kt_cur - a], font)
                    g.add(Color(*(self._kt_farbe_opt("insertbackground", fg) or fg)))
                    g.add(Rectangle(pos=(kx + l + cx, ky_z), size=(1, lh)))

    def _kt_pos_bei(self, x, y):
        """Position in the content for the point (x, y) inside the widget - where a click places
        the cursor.
        """
        font = self._kt_o.get("font")
        l, t, r, b = self._kt_innen_text()
        lh = max(1, fontmod.zeilen_hoehe(font))
        zeilen = self._kt_anzeige_zeilen()
        k = min(len(zeilen) - 1, max(0, self._kt_oben + (y - t) // lh))
        a, e, text = zeilen[k]
        rel = x - l
        for i in range(len(text) + 1):
            if fontmod.text_breite(text[:i], font) >= rel:
                return a + max(0, i - (1 if i and fontmod.text_breite(text[:i], font) - rel >
                                       rel - fontmod.text_breite(text[:i - 1], font) else 0))
        return e

    # -- editing
    def _kt_bearbeitbar(self):
        return self._kt_o.get("state") != "disabled"

    def _kt_text_eingabe(self, s):
        """Typed text in the multi-line field: replaces the selection or is inserted at the
        cursor.
        """
        if not self._kt_bearbeitbar() or not s:
            return
        if self._kt_sel:
            a, b = self._kt_sel
            self._kt_inhalt = self._kt_inhalt[:a] + self._kt_inhalt[b:]
            self._kt_cur = a
            self._kt_sel = None
        self._kt_inhalt = self._kt_inhalt[:self._kt_cur] + s + self._kt_inhalt[self._kt_cur:]
        self._kt_cur += len(s)
        _Blinker.zuruecksetzen()
        self.see("insert")
        self._kt_geaendert()

    def _kt_taste(self, ev):
        """Key in the multi-line field: cursor movement over lines and characters (with Shift:
        selection), Home / End, Return (new line), Tab, delete keys, Ctrl+A / C / X / V.
        """
        ks = ev.keysym
        s = self._kt_inhalt
        ctrl = bool(ev.state & EV.CONTROL)
        shift = bool(ev.state & EV.SHIFT)
        _Blinker.zuruecksetzen()
        if ctrl and ks.lower() == "a":
            self._kt_sel = (0, len(s))
            self._kt_neu_zeichnen()
            return
        if ctrl and ks.lower() == "c":
            if self._kt_sel:
                self.clipboard_clear()
                self.clipboard_append(s[self._kt_sel[0]:self._kt_sel[1]])
            return
        if ctrl and ks.lower() == "x":
            if self._kt_sel and self._kt_bearbeitbar():
                self.clipboard_clear()
                self.clipboard_append(s[self._kt_sel[0]:self._kt_sel[1]])
                self._kt_text_eingabe("") if False else self._kt_loeschen_sel()
            return
        if ctrl and ks.lower() == "v":
            try:
                self._kt_text_eingabe(self.clipboard_get())
            except T.TclError:
                pass
            return
        if not self._kt_bearbeitbar() and ks not in ("Left", "Right", "Up", "Down", "Home", "End"):
            return
        if ks in ("Return", "KP_Enter"):
            self._kt_text_eingabe("\n")
        elif ks == "Tab":
            pass
        elif ks == "BackSpace":
            if self._kt_sel:
                self._kt_loeschen_sel()
            elif self._kt_cur > 0:
                self._kt_inhalt = s[:self._kt_cur - 1] + s[self._kt_cur:]
                self._kt_cur -= 1
                self._kt_geaendert()
        elif ks == "Delete":
            if self._kt_sel:
                self._kt_loeschen_sel()
            elif self._kt_cur < len(s):
                self._kt_inhalt = s[:self._kt_cur] + s[self._kt_cur + 1:]
                self._kt_geaendert()
        elif ks in ("Left", "Right", "Home", "End", "Up", "Down"):
            neu = self._kt_cur
            if ks == "Left":
                neu -= 1
            elif ks == "Right":
                neu += 1
            elif ks == "Home":
                neu = s.rfind("\n", 0, self._kt_cur) + 1
            elif ks == "End":
                e = s.find("\n", self._kt_cur)
                neu = len(s) if e < 0 else e
            else:
                zs = s.rfind("\n", 0, self._kt_cur) + 1
                spalte = self._kt_cur - zs
                if ks == "Up" and zs > 0:
                    vz = s.rfind("\n", 0, zs - 1) + 1
                    neu = min(vz + spalte, zs - 1)
                elif ks == "Down":
                    e = s.find("\n", self._kt_cur)
                    if e >= 0:
                        ne = s.find("\n", e + 1)
                        neu = min(e + 1 + spalte, len(s) if ne < 0 else ne)
            neu = max(0, min(len(s), neu))
            if shift:
                if not self._kt_sel:
                    self._anker = self._kt_cur
                self._kt_sel = (min(self._anker, neu), max(self._anker, neu)) if self._anker != neu else None
            else:
                self._kt_sel = None
            self._kt_cur = neu
            self.see("insert")

    def _kt_loeschen_sel(self):
        a, b = self._kt_sel
        self._kt_inhalt = self._kt_inhalt[:a] + self._kt_inhalt[b:]
        self._kt_cur = a
        self._kt_sel = None
        self._kt_geaendert()

    def _kt_maus_runter(self, ev):
        """Mouse press in the multi-line field: places the cursor; a double click selects the
        word.
        """
        self.focus_set()
        i = self._kt_pos_bei(ev.x, ev.y)
        self._kt_cur = i
        self._anker = i
        self._kt_sel = None
        if ev._kt_klicks == 2:
            s = self._kt_inhalt
            a = i
            while a > 0 and s[a - 1].isalnum():
                a -= 1
            b = i
            while b < len(s) and s[b].isalnum():
                b += 1
            self._kt_sel = (a, b) if b > a else None
        self._kt_neu_zeichnen()

    def _kt_maus_ziehen(self, ev):
        i = self._kt_pos_bei(ev.x, ev.y)
        self._kt_sel = (min(self._anker, i), max(self._anker, i)) if self._anker != i else None
        self._kt_cur = i
        self._kt_neu_zeichnen()

    def _kt_fokus_aenderung(self):
        if "focus" in self._kt_zustand:
            _Blinker.start(self)
        else:
            _Blinker.stop(self)
        self._kt_neu_zeichnen()

    def _kt_nimmt_fokus(self):
        return self._kt_o.get("state") != "disabled"


def _zeichen_umbruch(zeile, font, breite):
    teile, aktuell = [], ""
    for ch in zeile:
        if fontmod.text_breite(aktuell + ch, font) > breite and aktuell:
            teile.append(aktuell)
            aktuell = ch
        else:
            aktuell += ch
    teile.append(aktuell)
    return teile


# ============================================================
# tk.Listbox
# ============================================================
class Listbox(T.BaseWidget):
    _kt_klasse = "Listbox"
    _kt_standard = {"background": "#ffffff", "foreground": "#000000", "font": "TkDefaultFont",
                 "borderwidth": 1, "relief": T.SUNKEN, "highlightthickness": 1,
                 "highlightbackground": "#f0f0f0", "highlightcolor": "#000000", "width": 20,
                 "height": 10, "selectmode": "browse", "selectbackground": "#0078d7",
                 "selectforeground": "#ffffff", "activestyle": "dotbox", "exportselection": 1,
                 "yscrollcommand": None, "xscrollcommand": None, "listvariable": None,
                 "state": "normal", "cursor": "", "takefocus": 1, "selectborderwidth": 0}

    def __init__(self, master=None, cnf=None, **kw):
        self._kt_eintraege = []
        self._kt_farben = {}
        self._kt_gewaehlt = set()
        self._kt_aktiv = 0
        self._kt_oben = 0
        self._anker = 0
        super().__init__(master, cnf, **kw)

    def _kt_idx(self, i):
        if i in (T.END, "end"):
            return len(self._kt_eintraege)
        if i in ("active",):
            return self._kt_aktiv
        if i == "anchor":
            return self._anker
        if isinstance(i, str) and i.startswith("@"):
            y = int(i.split(",")[1]) if "," in i else 0
            return self.nearest(y)
        return int(i)

    def insert(self, index, *elements):
        i = min(self._kt_idx(index), len(self._kt_eintraege))
        for k, e in enumerate(elements):
            self._kt_eintraege.insert(i + k, str(e))
        self._kt_geaendert()

    def delete(self, first, last=None):
        a = self._kt_idx(first)
        b = self._kt_idx(last) if last is not None else a
        if last in (T.END, "end"):
            b = len(self._kt_eintraege) - 1
        del self._kt_eintraege[a:b + 1]
        self._kt_gewaehlt = {i for i in self._kt_gewaehlt if i < a} | \
            {i - (b - a + 1) for i in self._kt_gewaehlt if i > b}
        self._kt_geaendert()

    def get(self, first, last=None):
        if last is None:
            i = self._kt_idx(first)
            return self._kt_eintraege[i] if 0 <= i < len(self._kt_eintraege) else ""
        a, b = self._kt_idx(first), self._kt_idx(last)
        if last in (T.END, "end"):
            b = len(self._kt_eintraege) - 1
        return tuple(self._kt_eintraege[a:b + 1])

    def size(self):
        return len(self._kt_eintraege)

    def curselection(self):
        return tuple(sorted(self._kt_gewaehlt))

    def selection_set(self, first, last=None):
        a = self._kt_idx(first)
        b = self._kt_idx(last) if last is not None else a
        if last in (T.END, "end"):
            b = len(self._kt_eintraege) - 1
        if self._kt_o.get("selectmode") in ("browse", "single"):
            self._kt_gewaehlt = {a} if 0 <= a < len(self._kt_eintraege) else set()
        else:
            self._kt_gewaehlt |= {i for i in range(a, b + 1) if 0 <= i < len(self._kt_eintraege)}
        self._kt_neu_zeichnen()

    select_set = selection_set

    def selection_clear(self, first, last=None):
        a = self._kt_idx(first)
        b = self._kt_idx(last) if last is not None else a
        if last in (T.END, "end"):
            b = len(self._kt_eintraege) - 1
        self._kt_gewaehlt -= set(range(a, b + 1))
        self._kt_neu_zeichnen()

    select_clear = selection_clear

    def selection_includes(self, index):
        return self._kt_idx(index) in self._kt_gewaehlt

    select_includes = selection_includes

    def selection_anchor(self, index):
        self._anker = self._kt_idx(index)

    def activate(self, index):
        self._kt_aktiv = max(0, min(len(self._kt_eintraege) - 1, self._kt_idx(index)))
        self._kt_neu_zeichnen()

    def index(self, i):
        return self._kt_idx(i)

    def see(self, index):
        i = self._kt_idx(index)
        s = self._kt_sicht()
        if i < self._kt_oben:
            self._kt_oben = i
        elif i >= self._kt_oben + s:
            self._kt_oben = i - s + 1
        self._kt_geaendert()

    def nearest(self, y):
        lh = self._kt_zeile_h()
        t = self._kt_innen()[1]
        return max(0, min(len(self._kt_eintraege) - 1, self._kt_oben + int((y - t) // lh)))

    def itemconfigure(self, index, cnf=None, **kw):
        if cnf:
            kw = {**cnf, **kw}
        self._kt_farben.setdefault(self._kt_idx(index), {}).update(kw)
        self._kt_neu_zeichnen()

    itemconfig = itemconfigure

    def itemcget(self, index, option):
        return self._kt_farben.get(self._kt_idx(index), {}).get(option, "")

    def _kt_zeile_h(self):
        return fontmod.zeilen_hoehe(self._kt_o.get("font")) + 2

    def _kt_sicht(self):
        if not self._kt_sichtbar:           # not laid out yet: the requested number of rows
            return max(1, T._int(self._kt_o.get("height", 10)))
        l, t, r, b = self._kt_innen()
        return max(1, (self._kt_h - t - b) // self._kt_zeile_h())

    def _kt_geaendert(self):
        self._kt_neu_zeichnen()
        self._kt_scroll_melden()

    def _kt_scroll_melden(self):
        cmd = self._kt_o.get("yscrollcommand")
        if cmd:
            n = max(1, len(self._kt_eintraege))
            try:
                cmd(self._kt_oben / n, min(1.0, (self._kt_oben + self._kt_sicht()) / n))
            except Exception:
                pass

    def yview(self, *args):
        n = max(1, len(self._kt_eintraege))
        s = self._kt_sicht()
        if not args:
            return (self._kt_oben / n, min(1.0, (self._kt_oben + s) / n))
        if args[0] == "moveto":
            self._kt_oben = int(round(float(args[1]) * n))
        elif args[0] == "scroll":
            k = int(float(args[1]))
            self._kt_oben += k * (s if str(args[2]).startswith("page") else 1)
        self._kt_oben = max(0, min(self._kt_oben, max(0, n - s)))
        self._kt_geaendert()

    def yview_moveto(self, f):
        self.yview("moveto", f)

    def yview_scroll(self, n, what):
        self.yview("scroll", n, what)

    def xview(self, *args):
        return (0.0, 1.0)

    def _kt_natuerlich(self):
        font = self._kt_o.get("font")
        l, t, r, b = self._kt_innen()
        return (T._int(self._kt_o.get("width", 20)) * fontmod.text_breite("0", font) + l + r + 4,
                T._int(self._kt_o.get("height", 10)) * self._kt_zeile_h() + t + b)

    def _kt_setzen(self, x, y, w, h, sichtbar=True):
        super()._kt_setzen(x, y, w, h, sichtbar)
        self._kt_scroll_melden()

    def _kt_malen(self, kx, ky):
        """Draws the list: the visible entries from the top one, selected entries with the
        selection colours.
        """
        self._kt_hintergrund(kx, ky)
        g = self._kt_g_inhalt
        font = self._kt_o.get("font")
        l, t, r, b = self._kt_innen()
        lh = self._kt_zeile_h()
        fg = self._kt_farbe_opt("foreground", (0, 0, 0, 1))
        sbg = self._kt_farbe_opt("selectbackground", (0, 0.47, 0.84, 1))
        sfg = self._kt_farbe_opt("selectforeground", (1, 1, 1, 1))
        bw = self._kt_w - l - r
        for k in range(self._kt_oben, min(len(self._kt_eintraege), self._kt_oben + self._kt_sicht())):
            y = t + (k - self._kt_oben) * lh
            kyz = ky + self._kt_h - y - lh
            f = self._kt_farben.get(k, {})
            gewaehlt = k in self._kt_gewaehlt
            bg = T._rgba(f.get("selectbackground" if gewaehlt else "background")) or \
                (sbg if gewaehlt else None)
            if bg is not None:
                g.add(Color(*bg))
                g.add(Rectangle(pos=(kx + l, kyz), size=(bw, lh)))
            farbe = T._rgba(f.get("selectforeground" if gewaehlt else "foreground")) or \
                (sfg if gewaehlt else fg)
            tex = fontmod.text_textur(self._kt_eintraege[k], font)
            if tex is not None:
                tw = min(tex.size[0], bw - 2)
                fontmod.text_zeichnen(g, tex.get_region(0, 0, tw, tex.size[1]), farbe,
                                      (kx + l + 2, kyz + 1), (tw, tex.size[1]))

    def _kt_klick(self, ev):
        """Click in the list: selects the entry under the mouse according to selectmode (browse
        / single: only it, multiple: toggles, extended: with Ctrl toggles, with Shift a
        range) and sends <<ListboxSelect>>.
        """
        if not self._kt_eintraege:
            return
        self.focus_set()
        i = self.nearest(ev.y)
        modus = self._kt_o.get("selectmode", "browse")
        if modus == "multiple":
            self._kt_gewaehlt ^= {i}
        elif modus == "extended" and ev.state & EV.CONTROL:
            self._kt_gewaehlt ^= {i}
            self._anker = i
        elif modus == "extended" and ev.state & EV.SHIFT:
            a, b = sorted((self._anker, i))
            self._kt_gewaehlt = set(range(a, b + 1))
        else:
            self._kt_gewaehlt = {i}
            self._anker = i
        self._kt_aktiv = i
        self._kt_neu_zeichnen()
        self._kt_ereignis("Virtual", _kt_virtuell="<<ListboxSelect>>")

    def _kt_taste(self, ev):
        if ev.keysym in ("Up", "Down") and self._kt_eintraege:
            i = max(0, min(len(self._kt_eintraege) - 1, self._kt_aktiv + (1 if ev.keysym == "Down" else -1)))
            self._kt_aktiv = i
            if self._kt_o.get("selectmode") in ("browse", "single", "extended"):
                self._kt_gewaehlt = {i}
                self._kt_ereignis("Virtual", _kt_virtuell="<<ListboxSelect>>")
            self.see(i)

    def _kt_nimmt_fokus(self):
        return True


# ============================================================
# Spinbox (tk) / Scale - only used through ttk; kept minimal
# ============================================================
class Spinbox(Entry):
    _kt_klasse = "Spinbox"


class Scale(T.BaseWidget):
    _kt_klasse = "Scale"
    _kt_standard = {"from_": 0, "to": 100, "orient": T.VERTICAL, "variable": None, "command": None,
                 "background": "#f0f0f0", "length": 100, "width": 15, "resolution": 1}

    def get(self):
        v = self._kt_o.get("variable")
        return v.get() if isinstance(v, T.Variable) else self._kt_o.get("from_", 0)

    def set(self, value):
        v = self._kt_o.get("variable")
        if isinstance(v, T.Variable):
            v.set(value)
