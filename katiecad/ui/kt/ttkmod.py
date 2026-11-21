# -*- coding: utf-8 -*-
"""
katiecad/ui/kt/ttkmod.py - tkinter.ttk on Kivy, drawn like Tk's "clam" theme (BSD-3-Clause).

ttk.Style keeps configure/map per style name with the usual fallback
("Title.TLabel" -> "TLabel" -> "."); the widgets look their colours up for their
current state (active, pressed, focus, selected, disabled, readonly ...).
"""

from kivy.graphics import Color, Rectangle, Line, Mesh

from katiecad.ui.kt import _base, fontmod, events as EV
from katiecad.ui.kt import tkmod as T
from katiecad.ui.kt.eingabe import EditMixin, _Blinker

__all__ = ["Style", "Widget", "Frame", "Label", "Button", "Checkbutton", "Radiobutton", "Entry",
           "Combobox", "Spinbox", "Separator", "Scrollbar", "Treeview", "Notebook", "Labelframe",
           "LabelFrame", "Progressbar", "Scale", "Sizegrip", "Menubutton", "OptionMenu",
           "PanedWindow", "Panedwindow", "LabeledScale"]

# ============================================================
# Style database (Tk 8.6 clam theme as start)
# ============================================================
_KONF = {}      # style -> {option: value}
_MAP = {}       # style -> {option: [(states, value)]}


def _clam():
    """Default settings and state maps of Tk's "clam" theme (colours, borders, paddings per
    style), the look the program's ttk styles build on. Called at start and by
    theme_use("clam").
    """
    _KONF.clear()
    _MAP.clear()
    d, dr, ds, li, fr = "#cfcdc8", "#bab5ab", "#9e9a91", "#eeebe7", "#dcdad5"
    _KONF["."] = {"background": fr, "foreground": "black", "bordercolor": ds, "darkcolor": d,
                  "lightcolor": li, "troughcolor": dr, "selectbackground": "#4a6984",
                  "selectforeground": "#ffffff", "font": "TkDefaultFont",
                  "fieldbackground": "#ffffff", "insertcolor": "black", "arrowcolor": "black"}
    _MAP["."] = {"background": [(("disabled",), fr), (("active",), li)],
                 "foreground": [(("disabled",), "#999999")],
                 "selectbackground": [(("!focus",), ds)],
                 "selectforeground": [(("!focus",), "white")]}
    _KONF["TButton"] = {"anchor": "center", "width": -11, "padding": 5, "relief": "raised"}
    _MAP["TButton"] = {"background": [(("disabled",), fr), (("pressed",), dr), (("active",), li)],
                       "lightcolor": [(("pressed",), dr)], "darkcolor": [(("pressed",), dr)],
                       "bordercolor": [(("alternate",), "#000000")]}
    _KONF["Toolbutton"] = {"anchor": "center", "padding": 2, "relief": "flat"}
    _MAP["Toolbutton"] = {"relief": [(("disabled",), "flat"), (("selected",), "sunken"),
                                     (("pressed",), "sunken"), (("active",), "raised")],
                          "background": [(("disabled",), fr), (("pressed",), dr), (("active",), li)],
                          "lightcolor": [(("pressed",), dr)], "darkcolor": [(("pressed",), dr)]}
    for s in ("TCheckbutton", "TRadiobutton"):
        _KONF[s] = {"indicatorbackground": "#ffffff", "indicatormargin": (1, 1, 4, 1), "padding": 2,
                    "indicatorforeground": "black"}
        _MAP[s] = {"indicatorbackground": [(("pressed",), fr), (("!disabled", "alternate"), "#5895bc"),
                                           (("disabled", "alternate"), "#a0a0a0"), (("disabled",), fr)]}
    _KONF["TEntry"] = {"padding": 1, "insertwidth": 1}
    _MAP["TEntry"] = {"background": [(("readonly",), fr)], "bordercolor": [(("focus",), "#4a6984")],
                      "lightcolor": [(("focus",), "#6f9dc6")]}
    _KONF["TCombobox"] = {"padding": 1, "insertwidth": 1, "arrowsize": 15}
    _MAP["TCombobox"] = {"background": [(("active",), li), (("pressed",), li)],
                         "fieldbackground": [(("readonly", "focus"), "#4a6984"), (("readonly",), fr)],
                         "foreground": [(("readonly", "focus"), "#ffffff")],
                         "arrowcolor": [(("disabled",), "#999999")],
                         "bordercolor": [(("focus",), "#4a6984")]}
    _KONF["TSpinbox"] = {"arrowsize": 10, "padding": (2, 0, 10, 0)}
    _MAP["TSpinbox"] = {"background": [(("readonly",), fr)], "arrowcolor": [(("disabled",), "#999999")],
                        "bordercolor": [(("focus",), "#4a6984")]}
    _KONF["TNotebook.Tab"] = {"padding": (6, 2, 6, 2)}
    _MAP["TNotebook.Tab"] = {"padding": [(("selected",), (6, 4, 6, 2))],
                             "background": [(("selected",), fr), ((), dr)],
                             "lightcolor": [(("selected",), li), ((), d)]}
    _KONF["Heading"] = {"font": "TkHeadingFont", "relief": "raised", "padding": 3}
    _KONF["Treeview"] = {"background": "#ffffff", "rowheight": 20}
    _MAP["Treeview"] = {"background": [(("disabled",), fr), (("selected",), "#4a6984")],
                        "foreground": [(("disabled",), "#999999"), (("selected",), "#ffffff")],
                        "bordercolor": [(("focus",), "#4a6984")]}
    _KONF["TLabelframe"] = {"borderwidth": 2, "relief": "raised"}
    _KONF["TProgressbar"] = {"background": fr}
    _KONF["TSeparator"] = {}
    _KONF["TScrollbar"] = {"arrowsize": 14}


_clam()


def _eltern(style):
    """"Icon.Toolbutton" -> "Toolbutton" -> "."."""
    if style == ".":
        return None
    if "." in style:
        return style.split(".", 1)[1]
    return "."


def _passt(states, zustand):
    for s in states:
        for teil in str(s).split():
            if teil.startswith("!"):
                if teil[1:] in zustand:
                    return False
            elif teil not in zustand:
                return False
    return True


def nachschlagen(style, option, zustand=frozenset(), standard=None):
    """Like Tk: the state map of the first style in the chain that maps this option (no
    further maps if none of its states match), then the settings of the chain."""
    s = style
    while s is not None:
        m = _MAP.get(s, {}).get(option)
        if m:
            for states, wert in m:
                if _passt(states, zustand):
                    return wert
            break
        s = _eltern(s)
    s = style
    while s is not None:
        k = _KONF.get(s, {})
        if option in k:
            return k[option]
        s = _eltern(s)
    return standard


def _map_liste(spec):
    """[("active", "#fff"), ("pressed", "!disabled", "#000")] -> [((states), value)]."""
    erg = []
    for e in spec:
        e = tuple(e)
        if len(e) < 2:
            continue
        states = []
        for s in e[:-1]:
            if isinstance(s, (tuple, list)):
                states.extend(s)
            else:
                states.extend(str(s).split())
        erg.append((tuple(states), e[-1]))
    return erg


class Style:
    def __init__(self, master=None):
        self.master = master

    def configure(self, style, query_opt=None, **kw):
        if query_opt is not None:
            return _KONF.get(style, {}).get(query_opt)
        if not kw:
            return dict(_KONF.get(style, {}))
        _KONF.setdefault(style, {}).update(kw)
        _base.alles_neu()

    def map(self, style, query_opt=None, **kw):
        if query_opt is not None:
            return [tuple(s) + (v,) for s, v in _MAP.get(style, {}).get(query_opt, [])]
        if not kw:
            return {k: [tuple(s) + (v,) for s, v in l] for k, l in _MAP.get(style, {}).items()}
        d = _MAP.setdefault(style, {})
        for k, v in kw.items():
            d[k] = _map_liste(v)
        _base.alles_neu()

    def lookup(self, style, option, state=None, default=None):
        z = frozenset(state or ())
        return nachschlagen(style, option.lstrip("-"), z, default)

    def layout(self, style, layoutspec=None):
        return []

    def element_create(self, elementname, etype, *args, **kw):
        pass

    def element_names(self):
        return ()

    def element_options(self, elementname):
        return ()

    def theme_create(self, themename, parent=None, settings=None):
        pass

    def theme_settings(self, themename, settings):
        pass

    def theme_names(self):
        return ("clam", "alt", "default", "classic", "winnative", "vista", "xpnative")

    def theme_use(self, themename=None):
        if themename is None:
            return "clam"
        _clam()
        _base.alles_neu()


# ============================================================
# Drawing helpers (clam elements)
# ============================================================
def _f(v, standard=None):
    return T._rgba(v, standard)


def _rect(g, farbe, x, y, w, h):
    if farbe is None or w <= 0 or h <= 0:
        return
    g.add(Color(*farbe))
    g.add(Rectangle(pos=(x, y), size=(w, h)))


def _rahmen1(g, farbe, x, y, w, h):
    if farbe is None:
        return
    _rect(g, farbe, x, y, w, 1)
    _rect(g, farbe, x, y + h - 1, w, 1)
    _rect(g, farbe, x, y, 1, h)
    _rect(g, farbe, x + w - 1, y, 1, h)


def _clam_rand(g, x, y, w, h, rand, hell, dunkel, relief="raised"):
    """Clam border: outer line in bordercolor, inner bevel light/dark (Kivy coordinates)."""
    if relief == "flat":
        return
    _rahmen1(g, rand, x, y, w, h)
    if relief == "solid" or w < 4 or h < 4:
        return
    oben, unten = (hell, dunkel) if relief in ("raised", "groove") else (dunkel, hell)
    # top / left
    _rect(g, oben, x + 1, y + h - 2, w - 2, 1)
    _rect(g, oben, x + 1, y + 1, 1, h - 2)
    # bottom / right
    _rect(g, unten, x + 1, y + 1, w - 2, 1)
    _rect(g, unten, x + w - 2, y + 1, 1, h - 2)


def _pfeil(g, farbe, cx, cy, groesse, richtung="down"):
    """Filled triangle centred at (cx, cy) (Kivy coordinates)."""
    if farbe is None:
        return
    h = groesse / 2.0
    if richtung == "down":
        pts = [cx - h, cy + h / 2, cx + h, cy + h / 2, cx, cy - h / 2]
    elif richtung == "up":
        pts = [cx - h, cy - h / 2, cx + h, cy - h / 2, cx, cy + h / 2]
    elif richtung == "left":
        pts = [cx + h / 2, cy - h, cx + h / 2, cy + h, cx - h / 2, cy]
    else:
        pts = [cx - h / 2, cy - h, cx - h / 2, cy + h, cx + h / 2, cy]
    g.add(Color(*farbe))
    g.add(Mesh(vertices=[pts[0], pts[1], 0, 0, pts[2], pts[3], 0, 0, pts[4], pts[5], 0, 0],
               indices=[0, 1, 2], mode="triangles"))


# ============================================================
# ttk widget base
# ============================================================
class Widget(T.BaseWidget):
    _kt_klasse = "TFrame"
    _kt_stil_basis = "."
    _kt_standard = {"style": "", "takefocus": "", "cursor": "", "class_": ""}

    def __init__(self, master=None, widgetname=None, cnf=None, **kw):
        if isinstance(widgetname, dict) and cnf is None:
            cnf = widgetname
        kw.pop("class_", None)
        super().__init__(master, cnf, **kw)

    # -- style lookup
    def _kt_stil(self):
        return self._kt_o.get("style") or self._kt_stil_basis

    def _kt_s(self, option, standard=None):
        return nachschlagen(self._kt_stil(), option, self._kt_zustand, standard)

    def _kt_sf(self, option, standard=None):
        return _f(self._kt_s(option), standard)

    # -- ttk state API
    def state(self, statespec=None):
        """state(): without argument the current states (as Tk returns them); with a state spec
        like ("disabled",) or ("!disabled",) sets / clears them and returns the previous ones
        so they can be restored. The widget is redrawn with the colours of the new state.
        """
        if statespec is None:
            return tuple(sorted(self._kt_zustand - {"hover"}))
        alt = []
        for s in (statespec if isinstance(statespec, (list, tuple)) else str(statespec).split()):
            if s.startswith("!"):
                if s[1:] in self._kt_zustand:
                    alt.append(s[1:])
                self._kt_zustand.discard(s[1:])
            else:
                if s not in self._kt_zustand:
                    alt.append("!" + s)
                self._kt_zustand.add(s)
        self._kt_layout_planen()
        self._kt_neu_zeichnen()
        return tuple(alt)

    def instate(self, statespec, callback=None, *args, **kw):
        ok = _passt(statespec if isinstance(statespec, (list, tuple)) else str(statespec).split(),
                    self._kt_zustand)
        if ok and callback:
            return callback(*args, **kw)
        return ok

    def _kt_state_option(self, v):
        for s in ("disabled", "readonly"):
            self._kt_zustand.discard(s)
        if v in ("disabled",):
            self._kt_zustand.add("disabled")
        elif v == "readonly":
            self._kt_zustand.add("readonly")

    def _kt_innen(self):
        pad = self._kt_o.get("padding")
        if pad in (None, ""):
            pad = self._kt_s("padding", 0)
        l, t, r, b = T._padding(pad or 0)
        bw = T._int(self._kt_o.get("borderwidth", self._kt_s("borderwidth", 0)) or 0)
        return l + bw, t + bw, r + bw, b + bw

    def _kt_hover_aenderung(self):
        self._kt_neu_zeichnen()

    def _kt_fokus_aenderung(self):
        self._kt_neu_zeichnen()

    def _kt_font(self):
        return self._kt_o.get("font") or self._kt_s("font", "TkDefaultFont")


# ============================================================
# Frame / Label / Separator / Labelframe
# ============================================================
class Frame(Widget):
    _kt_klasse = "TFrame"
    _kt_stil_basis = "TFrame"
    _kt_standard = dict(Widget._kt_standard, padding="", width=0, height=0, relief="", borderwidth="")

    def _kt_malen(self, kx, ky):
        bg = self._kt_sf("background")
        _rect(self._kt_g_hinten, bg, kx, ky, self._kt_w, self._kt_h)
        relief = self._kt_o.get("relief") or self._kt_s("relief", "flat")
        bw = T._int(self._kt_o.get("borderwidth") or self._kt_s("borderwidth", 0) or 0)
        if bw and relief != "flat":
            _clam_rand(self._kt_g_hinten, kx, ky, self._kt_w, self._kt_h, self._kt_sf("bordercolor"),
                       self._kt_sf("lightcolor"), self._kt_sf("darkcolor"), relief)


class Labelframe(Frame):
    _kt_klasse = "TLabelframe"
    _kt_stil_basis = "TLabelframe"
    _kt_standard = dict(Frame._kt_standard, text="", labelanchor="nw", labelwidget=None)

    def _kt_innen(self):
        l, t, r, b = Frame._kt_innen(self)
        bw = T._int(self._kt_s("borderwidth", 2) or 2)
        th = fontmod.zeilen_hoehe(self._kt_s("font", "TkDefaultFont")) if self._kt_o.get("text") else 0
        return l + bw, t + max(bw, th + 2), r + bw, b + bw

    def _kt_malen(self, kx, ky):
        """Draws a labelframe: border line with a gap for the label text at the top left."""
        bg = self._kt_sf("background")
        _rect(self._kt_g_hinten, bg, kx, ky, self._kt_w, self._kt_h)
        font = self._kt_s("font", "TkDefaultFont")
        th = fontmod.zeilen_hoehe(font) if self._kt_o.get("text") else 0
        rand = self._kt_sf("bordercolor")
        y_top = th // 2
        _rahmen1(self._kt_g_hinten, rand, kx, ky, self._kt_w, self._kt_h - y_top)
        if self._kt_o.get("text"):
            tw = fontmod.text_breite(self._kt_o["text"], font)
            _rect(self._kt_g_hinten, bg, kx + 6, ky + self._kt_h - th, tw + 6, th)
            self._kt_text_zeichnen(self._kt_g_inhalt, str(self._kt_o["text"]), font,
                                self._kt_sf("foreground", (0, 0, 0, 1)), 9, 0, "nw", kx, ky)


LabelFrame = Labelframe


class Label(T._TextBild, Widget):
    _kt_klasse = "TLabel"
    _kt_stil_basis = "TLabel"
    _kt_standard = dict(Widget._kt_standard, text="", textvariable=None, image="", compound="none",
                     font="", foreground="", background="", anchor="", justify="left",
                     wraplength=0, width="", padding="", relief="", borderwidth="", state="normal")

    def _kt_innen(self):
        pad = self._kt_o.get("padding")
        if pad in (None, ""):
            pad = self._kt_s("padding", 0)
        l, t, r, b = T._padding(pad or 0)
        bw = T._int(self._kt_o.get("borderwidth") or self._kt_s("borderwidth", 0) or 0)
        return l + bw, t + bw, r + bw, b + bw

    def _kt_textopt(self):
        # T._TextBild reads font/anchor from self._kt_o; fill in the style values
        o = self._kt_o
        return o

    def _kt_inhalt_groesse(self):
        alt_f = self._kt_o.get("font")
        self._kt_o["font"] = self._kt_font()
        try:
            return T._TextBild._kt_inhalt_groesse(self)
        finally:
            self._kt_o["font"] = alt_f

    def _kt_natuerlich(self):
        cw, ch, mit_bild, _mt = self._kt_inhalt_groesse()
        w = self._kt_o.get("width")
        if w not in (None, "", 0):
            n = T._int(w)
            zb = fontmod.text_breite("0", self._kt_font())
            cw = max(cw, -n * zb) if n < 0 else n * zb
        l, t, r, b = self._kt_innen()
        return cw + l + r, ch + t + b

    def _kt_malen(self, kx, ky):
        """Draws a ttk label: background, then text and / or image (via _kt_zeichne_inhalt) with
        the font and anchor of the widget or its style; colours from the widget options or
        the style for the current state.
        """
        bg = _f(self._kt_o.get("background")) or self._kt_sf("background")
        _rect(self._kt_g_hinten, bg, kx, ky, self._kt_w, self._kt_h)
        fg = (None if "disabled" in self._kt_zustand else _f(self._kt_o.get("foreground"))) or \
            self._kt_sf("foreground", (0, 0, 0, 1))
        l, t, r, b = self._kt_innen()
        alt = {k: self._kt_o.get(k) for k in ("font", "anchor")}
        self._kt_o["font"] = self._kt_font()
        self._kt_o["anchor"] = self._kt_o.get("anchor") or self._kt_s("anchor", "w")
        try:
            self._kt_zeichne_inhalt(self._kt_g_inhalt, kx, ky, fg, l, t, self._kt_w - l - r, self._kt_h - t - b)
        finally:
            self._kt_o.update(alt)

    def _kt_hover_aenderung(self):
        pass

    def _kt_nimmt_fokus(self):
        return False


class Separator(Widget):
    _kt_klasse = "TSeparator"
    _kt_stil_basis = "TSeparator"
    _kt_standard = dict(Widget._kt_standard, orient=T.HORIZONTAL)

    def _kt_natuerlich(self):
        return (2, 2)

    def _kt_malen(self, kx, ky):
        f = self._kt_sf("background")
        if "background" not in _KONF.get(self._kt_stil(), {}) and "background" not in _KONF.get("TSeparator", {}):
            f = self._kt_sf("darkcolor")
        _rect(self._kt_g_hinten, f, kx, ky, self._kt_w, self._kt_h)

    def _kt_hover_aenderung(self):
        pass


class Sizegrip(Widget):
    _kt_klasse = "TSizegrip"

    def _kt_natuerlich(self):
        return (16, 16)


# ============================================================
# Buttons
# ============================================================
class Button(T._TextBild, Widget):
    _kt_hover_aktiv = True
    _kt_klasse = "TButton"
    _kt_stil_basis = "TButton"
    _kt_standard = dict(Widget._kt_standard, text="", textvariable=None, image="", compound="none",
                     command=None, width="", padding="", default="normal", state="normal",
                     underline=-1)

    def _kt_toolbutton(self):
        return self._kt_stil().endswith("Toolbutton")

    def _kt_innen(self):
        pad = self._kt_o.get("padding")
        if pad in (None, ""):
            pad = self._kt_s("padding", 0)
        l, t, r, b = T._padding(pad or 0)
        return l + 2, t + 2, r + 2, b + 2

    def _kt_inhalt_groesse(self):
        alt = self._kt_o.get("font")
        self._kt_o["font"] = self._kt_font()
        try:
            return T._TextBild._kt_inhalt_groesse(self)
        finally:
            self._kt_o["font"] = alt

    def _kt_natuerlich(self):
        cw, ch, mit_bild, mit_text = self._kt_inhalt_groesse()
        w = self._kt_o.get("width")
        if w in (None, ""):
            w = self._kt_s("width", 0)
        n = T._int(w)
        if n and (mit_text or not mit_bild):
            zb = fontmod.text_breite("0", self._kt_font())
            cw = max(cw, -n * zb) if n < 0 else max(n * zb, 0)
        l, t, r, b = self._kt_innen()
        return cw + l + r, ch + t + b

    def _kt_knopf_malen(self, kx, ky, relief=None):
        g = self._kt_g_hinten
        bg = self._kt_sf("background")
        _rect(g, bg, kx, ky, self._kt_w, self._kt_h)
        relief = relief or self._kt_s("relief", "raised")
        _clam_rand(g, kx, ky, self._kt_w, self._kt_h, self._kt_sf("bordercolor"),
                   self._kt_sf("lightcolor"), self._kt_sf("darkcolor"), relief)

    def _kt_malen(self, kx, ky):
        self._kt_knopf_malen(kx, ky)
        fg = self._kt_sf("foreground", (0, 0, 0, 1))
        l, t, r, b = self._kt_innen()
        alt = {k: self._kt_o.get(k) for k in ("font", "anchor")}
        self._kt_o["font"] = self._kt_font()
        self._kt_o["anchor"] = self._kt_s("anchor", "center")
        try:
            self._kt_zeichne_inhalt(self._kt_g_inhalt, kx, ky, fg, l, t, self._kt_w - l - r, self._kt_h - t - b)
        finally:
            self._kt_o.update(alt)

    def invoke(self):
        if "disabled" in self._kt_zustand:
            return None
        c = self._kt_o.get("command")
        return c() if c else None

    def _kt_nimmt_fokus(self):
        return "disabled" not in self._kt_zustand and self._kt_o.get("takefocus") not in (0, "0", False)


class _Auswahl(Button):
    """Common part of Checkbutton and Radiobutton."""

    def _kt_ist_gewaehlt(self):
        return False

    def _kt_variable_geaendert(self, var):
        self._kt_zustand_nachziehen()

    def _kt_zustand_nachziehen(self):
        if self._kt_ist_gewaehlt():
            self._kt_zustand.add("selected")
        else:
            self._kt_zustand.discard("selected")
        self._kt_neu_zeichnen()

    def _kt_option_geaendert(self, kw):
        if "variable" in kw or "value" in kw or "onvalue" in kw:
            self._kt_zustand_nachziehen()

    def _kt_innen(self):
        if self._kt_toolbutton():
            return Button._kt_innen(self)
        pad = self._kt_o.get("padding")
        if pad in (None, ""):
            pad = self._kt_s("padding", 2)
        return T._padding(pad or 0)

    def _kt_natuerlich(self):
        if self._kt_toolbutton():
            return Button._kt_natuerlich(self)
        cw, ch, _mb, _mt = self._kt_inhalt_groesse()
        l, t, r, b = self._kt_innen()
        ml, mt, mr, mb = T._padding(self._kt_s("indicatormargin", (1, 1, 4, 1)))
        ind = 11 + ml + mr
        return cw + ind + l + r, max(ch, 11 + mt + mb) + t + b

    def _kt_indikator(self, g, x, y):
        pass

    def _kt_malen(self, kx, ky):
        """Draws a check button / radio button: as Toolbutton like a flat button (relief from
        the style for the current state, e.g. pressed while selected), otherwise the
        indicator followed by the text.
        """
        if self._kt_toolbutton():
            relief = self._kt_s("relief", "flat")
            self._kt_knopf_malen(kx, ky, relief)
            fg = self._kt_sf("foreground", (0, 0, 0, 1))
            l, t, r, b = self._kt_innen()
            alt = {k: self._kt_o.get(k) for k in ("font", "anchor")}
            self._kt_o["font"] = self._kt_font()
            self._kt_o["anchor"] = "center"
            try:
                self._kt_zeichne_inhalt(self._kt_g_inhalt, kx, ky, fg, l, t, self._kt_w - l - r, self._kt_h - t - b)
            finally:
                self._kt_o.update(alt)
            return
        bg = self._kt_sf("background")
        _rect(self._kt_g_hinten, bg, kx, ky, self._kt_w, self._kt_h)
        l, t, r, b = self._kt_innen()
        ml, mt, mr, mb = T._padding(self._kt_s("indicatormargin", (1, 1, 4, 1)))
        ix = kx + l + ml
        iy = ky + (self._kt_h - 11) // 2
        self._kt_indikator(self._kt_g_hinten, ix, iy)
        fg = self._kt_sf("foreground", (0, 0, 0, 1))
        alt = {k: self._kt_o.get(k) for k in ("font", "anchor")}
        self._kt_o["font"] = self._kt_font()
        self._kt_o["anchor"] = "w"
        try:
            x0 = l + ml + 11 + mr
            self._kt_zeichne_inhalt(self._kt_g_inhalt, kx, ky, fg, x0, t, self._kt_w - x0 - r, self._kt_h - t - b)
        finally:
            self._kt_o.update(alt)


class Checkbutton(_Auswahl):
    _kt_klasse = "TCheckbutton"
    _kt_stil_basis = "TCheckbutton"
    _kt_standard = dict(Button._kt_standard, variable=None, onvalue=1, offvalue=0)

    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        if not isinstance(self._kt_o.get("variable"), T.Variable):
            v = T.IntVar(value=self._kt_o.get("offvalue", 0))
            self._kt_o["variable"] = v
            v._kt_beobachten(self)
        self._kt_zustand_nachziehen()

    def _kt_ist_gewaehlt(self):
        v = self._kt_o.get("variable")
        if not isinstance(v, T.Variable):
            return False
        wert = v._kt_roh()
        an = self._kt_o.get("onvalue", 1)
        if isinstance(wert, bool) or isinstance(an, bool):
            try:
                return bool(wert) == bool(T.getboolean(an) if isinstance(an, str) else an) and bool(wert)
            except T.TclError:
                return False
        return str(wert) == str(an) or (wert in (1, True) and an in (1, True, "1"))

    def invoke(self):
        if "disabled" in self._kt_zustand:
            return None
        v = self._kt_o.get("variable")
        if isinstance(v, T.Variable):
            neu = self._kt_o.get("offvalue", 0) if self._kt_ist_gewaehlt() else self._kt_o.get("onvalue", 1)
            if isinstance(v, T.BooleanVar) and neu in (0, 1):
                neu = bool(neu)
            v.set(neu)
        self._kt_zustand_nachziehen()
        c = self._kt_o.get("command")
        return c() if c else None

    def _kt_indikator(self, g, x, y):
        """The check box of a Checkbutton in clam style (11x11 with border and a tick when
        selected).
        """
        ib = self._kt_sf("indicatorbackground", (1, 1, 1, 1))
        _rect(g, ib, x, y, 11, 11)
        rand = _f("#9e9a91")
        dunkel = _f("#cfcdc8")
        _rect(g, rand, x, y + 10, 11, 1)        # top
        _rect(g, rand, x, y, 1, 11)             # left
        _rect(g, dunkel, x + 10, y, 1, 10)      # right
        _rect(g, dunkel, x + 1, y, 10, 1)       # bottom
        if "selected" in self._kt_zustand:
            f = self._kt_sf("indicatorforeground", (0, 0, 0, 1))
            g.add(Color(*f))
            g.add(Line(points=[x + 2.5, y + 2.5, x + 8.5, y + 8.5], width=1.1))
            g.add(Line(points=[x + 2.5, y + 8.5, x + 8.5, y + 2.5], width=1.1))


class Radiobutton(_Auswahl):
    _kt_klasse = "TRadiobutton"
    _kt_stil_basis = "TRadiobutton"
    _kt_standard = dict(Button._kt_standard, variable=None, value="")

    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self._kt_zustand_nachziehen()

    def _kt_ist_gewaehlt(self):
        v = self._kt_o.get("variable")
        if not isinstance(v, T.Variable):
            return False
        return str(v._kt_roh()) == str(self._kt_o.get("value"))

    def invoke(self):
        if "disabled" in self._kt_zustand:
            return None
        v = self._kt_o.get("variable")
        if isinstance(v, T.Variable):
            v.set(self._kt_o.get("value"))
        self._kt_zustand_nachziehen()
        c = self._kt_o.get("command")
        return c() if c else None

    def _kt_indikator(self, g, x, y):
        from kivy.graphics import Ellipse
        ib = self._kt_sf("indicatorbackground", (1, 1, 1, 1))
        rand = _f("#9e9a91")
        g.add(Color(*rand))
        g.add(Ellipse(pos=(x, y), size=(11, 11), segments=24))
        g.add(Color(*ib))
        g.add(Ellipse(pos=(x + 1, y + 1), size=(9, 9), segments=24))
        if "selected" in self._kt_zustand:
            g.add(Color(*self._kt_sf("indicatorforeground", (0, 0, 0, 1))))
            g.add(Ellipse(pos=(x + 3, y + 3), size=(5, 5), segments=16))


class Menubutton(Button):
    _kt_klasse = "TMenubutton"
    _kt_stil_basis = "TMenubutton"
    _kt_standard = dict(Button._kt_standard, menu=None, direction="below")

    def invoke(self):
        m = self._kt_o.get("menu")
        if m:
            m.tk_popup(self.winfo_rootx(), self.winfo_rooty() + self.winfo_height())


class OptionMenu(Menubutton):
    def __init__(self, master, variable, default=None, *values, **kw):
        command = kw.pop("command", None)
        super().__init__(master, textvariable=variable, **kw)
        m = T.Menu(self, tearoff=0)
        for v in values:
            m.add_radiobutton(label=v, variable=variable, value=v,
                              command=(lambda v=v: command(v)) if command else None)
        self._kt_o["menu"] = m
        if default is not None:
            variable.set(default)


# ============================================================
# Entry / Combobox / Spinbox
# ============================================================
class Entry(EditMixin, Widget):
    _kt_klasse = "TEntry"
    _kt_stil_basis = "TEntry"
    _kt_standard = dict(Widget._kt_standard, textvariable=None, show="", state="normal", width=20,
                     font="", justify="left", foreground="", background="", validate="none",
                     validatecommand=None, invalidcommand=None, exportselection=1, cursor="xterm")

    def __init__(self, master=None, widget=None, **kw):
        super().__init__(master, **kw)
        self._kt_edit_init()

    def _kt_option_geaendert(self, kw):
        if "font" not in self._kt_o or not self._kt_o.get("font"):
            pass

    def _kt_innen_text(self):
        pad = T._padding(self._kt_s("padding", 1) or 0)
        return 2 + pad[0], 2 + pad[1], 2 + pad[2] + self._kt_rechts(), 2 + pad[3]

    def _kt_rechts(self):
        return 0

    def _kt_natuerlich(self):
        font = self._kt_font()
        l, t, r, b = self._kt_innen_text()
        return (T._int(self._kt_o.get("width", 20)) * fontmod.text_breite("0", font) + l + r,
                fontmod.zeilen_hoehe(font) + t + b + 2)

    def _kt_feld_malen(self, kx, ky, w):
        g = self._kt_g_hinten
        fb = self._kt_sf("fieldbackground", (1, 1, 1, 1))
        _rect(g, fb, kx, ky, w, self._kt_h)
        _rahmen1(g, self._kt_sf("bordercolor"), kx, ky, w, self._kt_h)
        _rahmen1(g, self._kt_sf("lightcolor"), kx + 1, ky + 1, w - 2, self._kt_h - 2)

    def _kt_malen(self, kx, ky):
        self._kt_feld_malen(kx, ky, self._kt_w)
        self._kt_text_inhalt(kx, ky)

    def _kt_text_inhalt(self, kx, ky):
        fg = (None if "disabled" in self._kt_zustand else _f(self._kt_o.get("foreground"))) or \
            self._kt_sf("foreground", (0, 0, 0, 1))
        alt = self._kt_o.get("font")
        self._kt_o["font"] = self._kt_font()
        if not self._kt_o.get("insertbackground"):
            self._kt_o["insertbackground"] = self._kt_s("insertcolor", "black")
        try:
            self._kt_text_malen(self._kt_g_inhalt, kx, ky, fg, self._kt_sf("selectbackground", (0.29, 0.41, 0.52, 1)),
                             self._kt_sf("selectforeground", (1, 1, 1, 1)), "focus" in self._kt_zustand)
        finally:
            self._kt_o["font"] = alt

    def _kt_pos_bei(self, x):
        alt = self._kt_o.get("font")
        self._kt_o["font"] = self._kt_font()
        try:
            return EditMixin._kt_pos_bei(self, x)
        finally:
            self._kt_o["font"] = alt

    def _kt_hover_aenderung(self):
        pass


class Combobox(Entry):
    _kt_hover_aktiv = True
    _kt_klasse = "TCombobox"
    _kt_stil_basis = "TCombobox"
    _kt_standard = dict(Entry._kt_standard, values=(), height=10, postcommand=None, cursor="")

    def __init__(self, master=None, **kw):
        self._kt_popup = None
        super().__init__(master, **kw)

    def _kt_rechts(self):
        return T._int(self._kt_s("arrowsize", 15)) + 2

    def _kt_malen(self, kx, ky):
        """Draws a combobox: the entry field plus the arrow button on the right."""
        a = self._kt_rechts()
        g = self._kt_g_hinten
        self._kt_feld_malen(kx, ky, self._kt_w)
        # arrow button (clam: raised box inside the field border)
        bx = kx + self._kt_w - a - 1
        _rect(g, self._kt_sf("background"), bx, ky + 1, a, self._kt_h - 2)
        _rect(g, self._kt_sf("lightcolor"), bx, ky + 1, 1, self._kt_h - 2)
        _rect(g, self._kt_sf("darkcolor"), bx + a - 1, ky + 1, 1, self._kt_h - 2)
        _rect(g, self._kt_sf("darkcolor"), bx, ky + 1, a, 1)
        _rect(g, self._kt_sf("bordercolor"), bx - 1, ky, 1, self._kt_h)
        _pfeil(g, self._kt_sf("arrowcolor", (0, 0, 0, 1)), bx + a / 2.0, ky + self._kt_h / 2.0, 7, "down")
        self._kt_text_inhalt(kx, ky)

    def current(self, newindex=None):
        werte = list(self._kt_werte())
        if newindex is None:
            try:
                return werte.index(self.get())
            except ValueError:
                return -1
        self._kt_wert_setzen(str(werte[int(newindex)]))
        self._kt_cur = len(self.get())

    def set(self, value):
        self._kt_wert_setzen(str(value))
        self._kt_cur = len(str(value))
        self._kt_sel = None

    def _kt_werte(self):
        v = self._kt_o.get("values") or ()
        if isinstance(v, str):
            v = v.split()
        return [str(x) for x in v]

    def _kt_aufklappen(self):
        from katiecad.ui.kt import klassen
        if self._kt_popup is not None:
            klassen.popup_schliessen()
            return
        pc = self._kt_o.get("postcommand")
        if pc:
            pc()
        klassen.combobox_aufklappen(self)

    def _kt_waehlen(self, wert):
        self._kt_wert_setzen(wert)
        self._kt_cur = len(wert)
        self._kt_sel = (0, len(wert)) if "readonly" not in self._kt_zustand else None
        self.focus_set()
        self.event_generate("<<ComboboxSelected>>")


class Spinbox(Entry):
    _kt_hover_aktiv = True
    _kt_klasse = "TSpinbox"
    _kt_stil_basis = "TSpinbox"
    _kt_standard = dict(Entry._kt_standard, from_=0.0, to=0.0, increment=1.0, values=(), wrap=False,
                     format="", command=None)

    def __init__(self, master=None, **kw):
        if "from" in kw:
            kw["from_"] = kw.pop("from")
        super().__init__(master, **kw)

    def _kt_rechts(self):
        return 14

    def _kt_malen(self, kx, ky):
        """Draws a spinbox: the entry field plus the up / down arrows on the right."""
        g = self._kt_g_hinten
        self._kt_feld_malen(kx, ky, self._kt_w)
        a = self._kt_rechts()
        bx = kx + self._kt_w - a - 1
        mitte = ky + self._kt_h / 2.0
        _rect(g, self._kt_sf("background"), bx, ky + 1, a, self._kt_h - 2)
        _rect(g, self._kt_sf("bordercolor"), bx - 1, ky, 1, self._kt_h)
        _rect(g, self._kt_sf("darkcolor"), bx, int(mitte), a, 1)
        farbe = self._kt_sf("arrowcolor", (0, 0, 0, 1))
        _pfeil(g, farbe, bx + a / 2.0, mitte + self._kt_h / 4.0, 6, "up")
        _pfeil(g, farbe, bx + a / 2.0, mitte - self._kt_h / 4.0, 6, "down")
        self._kt_text_inhalt(kx, ky)

    def _kt_schritt(self, richtung):
        """Arrow of a spinbox: the next / previous entry of `values`, or the value +/-
        increment, kept within from_ .. to and formatted with `format`. Then runs the command
        and sends <<Increment>> / <<Decrement>>.
        """
        if "disabled" in self._kt_zustand:
            return
        werte = self._kt_o.get("values")
        if werte:
            werte = [str(v) for v in (werte.split() if isinstance(werte, str) else werte)]
            try:
                i = werte.index(self.get())
            except ValueError:
                i = -1
            i = max(0, min(len(werte) - 1, i + richtung))
            self._kt_wert_setzen(werte[i])
        else:
            try:
                v = float(str(self.get()).replace(",", "."))
            except ValueError:
                v = float(self._kt_o.get("from_", 0) or 0)
            inc = float(self._kt_o.get("increment", 1) or 1)
            lo, hi = float(self._kt_o.get("from_", 0) or 0), float(self._kt_o.get("to", 0) or 0)
            v += richtung * inc
            if hi > lo:
                v = max(lo, min(hi, v))
            fmt = self._kt_o.get("format")
            if fmt:
                s = fmt % v
            elif float(inc).is_integer() and float(v).is_integer():
                s = str(int(v))
            else:
                s = ("%.6f" % v).rstrip("0").rstrip(".")
            self._kt_wert_setzen(s)
        self._kt_cur = len(self.get())
        c = self._kt_o.get("command")
        if c:
            c()
        self.event_generate("<<Increment>>" if richtung > 0 else "<<Decrement>>")


# ============================================================
# Scrollbar (clam)
# ============================================================
class Scrollbar(Widget):
    _kt_hover_aktiv = True
    _kt_klasse = "TScrollbar"
    _kt_stil_basis = "TScrollbar"
    _kt_standard = dict(Widget._kt_standard, orient=T.VERTICAL, command=None)

    def __init__(self, master=None, **kw):
        self._kt_anteil = (0.0, 1.0)
        self._kt_drag = None
        super().__init__(master, **kw)

    def set(self, first, last):
        self._kt_anteil = (float(first), float(last))
        self._kt_neu_zeichnen()

    def get(self):
        return self._kt_anteil

    def _kt_pfeil_l(self):
        return T._int(self._kt_s("arrowsize", 14))

    def _kt_natuerlich(self):
        a = self._kt_pfeil_l()
        return (a, 3 * a) if self._kt_o.get("orient") == T.VERTICAL else (3 * a, a)

    def _kt_griff(self):
        a = self._kt_pfeil_l()
        vert = self._kt_o.get("orient") == T.VERTICAL
        lang = (self._kt_h if vert else self._kt_w) - 2 * a
        f0, f1 = self._kt_anteil
        p0 = a + int(f0 * lang)
        p1 = a + int(f1 * lang)
        if p1 - p0 < 10:
            p1 = min(a + lang, p0 + 10)
        return p0, p1, lang

    def _kt_malen(self, kx, ky):
        """Draws a scroll bar: trough, the two arrow buttons and the slider for the visible part
        (_kt_anteil).
        """
        g = self._kt_g_hinten
        vert = self._kt_o.get("orient") == T.VERTICAL
        trog = self._kt_sf("troughcolor", (0.73, 0.71, 0.67, 1))
        _rect(g, trog, kx, ky, self._kt_w, self._kt_h)
        rand, hell, dunkel = self._kt_sf("bordercolor"), self._kt_sf("lightcolor"), self._kt_sf("darkcolor")
        bg = self._kt_sf("background")
        a = self._kt_pfeil_l()
        pf = self._kt_sf("arrowcolor", (0, 0, 0, 1))
        if vert:
            for y0, richtung in ((ky + self._kt_h - a, "up"), (ky, "down")):
                _rect(g, bg, kx, y0, self._kt_w, a)
                _clam_rand(g, kx, y0, self._kt_w, a, rand, hell, dunkel)
                _pfeil(g, pf, kx + self._kt_w / 2.0, y0 + a / 2.0, 7, richtung)
            p0, p1, _l = self._kt_griff()
            if self._kt_anteil != (0.0, 1.0):
                yy = ky + self._kt_h - p1
                _rect(g, bg, kx, yy, self._kt_w, p1 - p0)
                _clam_rand(g, kx, yy, self._kt_w, p1 - p0, rand, hell, dunkel)
        else:
            for x0, richtung in ((kx, "left"), (kx + self._kt_w - a, "right")):
                _rect(g, bg, x0, ky, a, self._kt_h)
                _clam_rand(g, x0, ky, a, self._kt_h, rand, hell, dunkel)
                _pfeil(g, pf, x0 + a / 2.0, ky + self._kt_h / 2.0, 7, richtung)
            p0, p1, _l = self._kt_griff()
            if self._kt_anteil != (0.0, 1.0):
                _rect(g, bg, kx + p0, ky, p1 - p0, self._kt_h)
                _clam_rand(g, kx + p0, ky, p1 - p0, self._kt_h, rand, hell, dunkel)

    def _kt_befehl(self, *args):
        c = self._kt_o.get("command")
        if c:
            c(*args)

    def _kt_nimmt_fokus(self):
        return False

    # -- mouse (from klassen.py)
    def _kt_klick(self, ev):
        """Click on a scroll bar: arrows scroll one unit, the trough one page, the slider starts
        dragging - all through the scroll command (e.g. canvas.yview) like in Tk.
        """
        vert = self._kt_o.get("orient") == T.VERTICAL
        p = ev.y if vert else ev.x
        lang_ges = self._kt_h if vert else self._kt_w
        a = self._kt_pfeil_l()
        p0, p1, lang = self._kt_griff()
        if p < a:
            self._kt_befehl("scroll", -1, "units")
        elif p >= lang_ges - a:
            self._kt_befehl("scroll", 1, "units")
        elif p < p0:
            self._kt_befehl("scroll", -1, "pages")
        elif p > p1:
            self._kt_befehl("scroll", 1, "pages")
        else:
            self._kt_drag = (p, self._kt_anteil[0], lang)

    def _kt_ziehen(self, ev):
        if self._kt_drag is None:
            return
        vert = self._kt_o.get("orient") == T.VERTICAL
        p = ev.y if vert else ev.x
        start, f0, lang = self._kt_drag
        self._kt_befehl("moveto", max(0.0, f0 + (p - start) / max(1, lang)))

    def _kt_los(self, ev):
        self._kt_drag = None


# ============================================================
# Treeview
# ============================================================
class Treeview(Widget):
    _kt_hover_aktiv = True
    _kt_klasse = "Treeview"
    _kt_stil_basis = "Treeview"
    _kt_standard = dict(Widget._kt_standard, columns=(), displaycolumns="#all", show="tree headings",
                     selectmode="extended", height=10, padding="", xscrollcommand=None,
                     yscrollcommand=None)

    def __init__(self, master=None, **kw):
        self._kt_knoten = {"": {"kinder": [], "text": "", "values": (), "open": True, "tags": (),
                             "image": "", "eltern": None}}
        self._kt_spalten = {}             # "#0" / name -> {width, minwidth, stretch, anchor}
        self._kt_kopf = {}                # "#0" / name -> {text, anchor, command, image}
        self._kt_auswahl = []
        self._kt_fokus_item = ""
        self._kt_oben = 0
        self._kt_n = 0
        self._kt_tag_konf = {}
        super().__init__(master, **kw)
        self._kt_spalten.setdefault("#0", {"width": 200, "minwidth": 20, "stretch": True, "anchor": "w"})
        self._kt_kopf.setdefault("#0", {"text": "", "anchor": "center", "command": None, "image": ""})
        for c in self._kt_spalten_namen():
            self._kt_spalten.setdefault(c, {"width": 200, "minwidth": 20, "stretch": True, "anchor": "w"})
            self._kt_kopf.setdefault(c, {"text": "", "anchor": "center", "command": None, "image": ""})

    def _kt_option_geaendert(self, kw):
        if "columns" in kw and hasattr(self, "_kt_spalten"):
            for c in self._kt_spalten_namen():
                self._kt_spalten.setdefault(c, {"width": 200, "minwidth": 20, "stretch": True, "anchor": "w"})
                self._kt_kopf.setdefault(c, {"text": "", "anchor": "center", "command": None, "image": ""})

    def _kt_spalten_namen(self):
        c = self._kt_o.get("columns") or ()
        if isinstance(c, str):
            c = c.split()
        return [str(x) for x in c]

    def _kt_spalte_name(self, c):
        if isinstance(c, int):
            return self._kt_spalten_namen()[c]
        s = str(c)
        if s.startswith("#") and s != "#0":
            return self._kt_spalten_namen()[int(s[1:]) - 1]
        return s

    def _kt_zeigt(self, was):
        show = self._kt_o.get("show", "tree headings")
        if isinstance(show, (tuple, list)):
            show = " ".join(show)
        return was in str(show)

    def _kt_anzeige_spalten(self):
        erg = ["#0"] if self._kt_zeigt("tree") else []
        dc = self._kt_o.get("displaycolumns", "#all")
        if dc in ("#all", ("#all",), "", None):
            erg += self._kt_spalten_namen()
        else:
            erg += [self._kt_spalte_name(c) for c in (dc.split() if isinstance(dc, str) else dc)]
        return erg

    # -- items
    def insert(self, parent, index, iid=None, **kw):
        """insert(parent, index, iid=None, **options): adds an item (text, values, image, open,
        tags) to the tree; without iid one is generated as in Tk (I001, I002 ...). Returns
        the iid.
        """
        if iid is None:
            self._kt_n += 1
            iid = f"I{self._kt_n:03X}"
        iid = str(iid)
        if iid in self._kt_knoten:
            raise T.TclError(f'Item {iid} already exists')
        werte = kw.get("values", ())
        if isinstance(werte, str):
            werte = (werte,)
        k = {"kinder": [], "text": str(kw.get("text", "")), "values": tuple(werte),
             "open": bool(kw.get("open", False)), "tags": _tagliste(kw.get("tags", ())),
             "image": kw.get("image", ""), "eltern": str(parent)}
        self._kt_knoten[iid] = k
        kinder = self._kt_knoten[str(parent)]["kinder"]
        if index in ("end", T.END):
            kinder.append(iid)
        else:
            kinder.insert(int(index), iid)
        self._kt_geaendert()
        return iid

    def delete(self, *items):
        """delete(*items): removes the items with all their children."""
        for it in _flach_items(items):
            it = str(it)
            if it not in self._kt_knoten or it == "":
                continue
            for c in list(self._kt_knoten[it]["kinder"]):
                self.delete(c)
            e = self._kt_knoten[it]["eltern"]
            if e in self._kt_knoten and it in self._kt_knoten[e]["kinder"]:
                self._kt_knoten[e]["kinder"].remove(it)
            del self._kt_knoten[it]
            if it in self._kt_auswahl:
                self._kt_auswahl.remove(it)
            if self._kt_fokus_item == it:
                self._kt_fokus_item = ""
        self._kt_geaendert()

    def detach(self, *items):
        self.delete(*items)

    def get_children(self, item=None):
        return tuple(self._kt_knoten.get(str(item or ""), {"kinder": []})["kinder"])

    def set_children(self, item, *newchildren):
        self._kt_knoten[str(item)]["kinder"] = [str(c) for c in _flach_items(newchildren)]
        self._kt_geaendert()

    def exists(self, item):
        return str(item) in self._kt_knoten

    def parent(self, item):
        return self._kt_knoten[str(item)]["eltern"] or ""

    def index(self, item):
        e = self.parent(item)
        return self._kt_knoten[e]["kinder"].index(str(item))

    def next(self, item):
        e = self.parent(item)
        k = self._kt_knoten[e]["kinder"]
        i = k.index(str(item))
        return k[i + 1] if i + 1 < len(k) else ""

    def prev(self, item):
        e = self.parent(item)
        k = self._kt_knoten[e]["kinder"]
        i = k.index(str(item))
        return k[i - 1] if i > 0 else ""

    def move(self, item, parent, index):
        item = str(item)
        alt = self.parent(item)
        self._kt_knoten[alt]["kinder"].remove(item)
        kinder = self._kt_knoten[str(parent)]["kinder"]
        if index in ("end", T.END):
            kinder.append(item)
        else:
            kinder.insert(int(index), item)
        self._kt_knoten[item]["eltern"] = str(parent)
        self._kt_geaendert()

    reattach = move

    def item(self, item, option=None, **kw):
        """item(iid, option=None, **options): reads one option, all options, or changes them."""
        k = self._kt_knoten.get(str(item))
        if k is None:
            raise T.TclError(f'Item {item} not found')
        if option is not None:
            return k.get(option, "")
        if not kw:
            return {"text": k["text"], "values": list(k["values"]) if k["values"] else "",
                    "open": k["open"], "tags": list(k["tags"]) if k["tags"] else "",
                    "image": k["image"]}
        for key, v in kw.items():
            if key == "values":
                v = (v,) if isinstance(v, str) else tuple(v)
            elif key == "tags":
                v = _tagliste(v)
            elif key == "open":
                v = bool(v)
            k[key] = v
        self._kt_geaendert()

    def set(self, item, column=None, value=None):
        """set(iid, column=None, value=None): value of a column of an item (all columns as dict
        without column), or sets it.
        """
        k = self._kt_knoten[str(item)]
        namen = self._kt_spalten_namen()
        if column is None:
            return {n: (k["values"][i] if i < len(k["values"]) else "") for i, n in enumerate(namen)}
        c = self._kt_spalte_name(column)
        i = namen.index(c)
        if value is None:
            return k["values"][i] if i < len(k["values"]) else ""
        werte = list(k["values"]) + [""] * (len(namen) - len(k["values"]))
        werte[i] = value
        k["values"] = tuple(werte)
        self._kt_geaendert()

    def focus(self, item=None):
        if item is None:
            return self._kt_fokus_item
        self._kt_fokus_item = str(item)
        self._kt_neu_zeichnen()

    def see(self, item):
        """see(iid): opens the parents of the item and scrolls so it is visible."""
        sichtbar = self._kt_sichtbare()
        item = str(item)
        e = self._kt_knoten.get(item, {}).get("eltern")
        while e:
            self._kt_knoten[e]["open"] = True
            e = self._kt_knoten[e]["eltern"]
        sichtbar = self._kt_sichtbare()
        if item in sichtbar:
            i = sichtbar.index(item)
            n = self._kt_sicht()
            if i < self._kt_oben:
                self._kt_oben = i
            elif i >= self._kt_oben + n:
                self._kt_oben = i - n + 1
        self._kt_geaendert()

    # -- selection
    def selection(self, selop=None, items=None):
        if selop is None:
            return tuple(self._kt_auswahl)
        return getattr(self, "selection_" + selop)(items)

    def selection_set(self, *items):
        self._kt_auswahl = [str(i) for i in _flach_items(items) if str(i) in self._kt_knoten]
        self._kt_auswahl_gemeldet()

    def selection_add(self, *items):
        for i in _flach_items(items):
            if str(i) not in self._kt_auswahl and str(i) in self._kt_knoten:
                self._kt_auswahl.append(str(i))
        self._kt_auswahl_gemeldet()

    def selection_remove(self, *items):
        for i in _flach_items(items):
            if str(i) in self._kt_auswahl:
                self._kt_auswahl.remove(str(i))
        self._kt_auswahl_gemeldet()

    def selection_toggle(self, *items):
        for i in _flach_items(items):
            i = str(i)
            if i in self._kt_auswahl:
                self._kt_auswahl.remove(i)
            else:
                self._kt_auswahl.append(i)
        self._kt_auswahl_gemeldet()

    def _kt_auswahl_gemeldet(self):
        self._kt_neu_zeichnen()
        r = self._kt_root_
        r.after_idle(lambda: None if self._kt_zerstoert else
                     self.event_generate("<<TreeviewSelect>>"))

    # -- columns / headings
    def column(self, column, option=None, **kw):
        """column(column, option=None, **options): width, minwidth, stretch and anchor of a
        column - read or set.
        """
        c = self._kt_spalte_name(column)
        d = self._kt_spalten.setdefault(c, {"width": 200, "minwidth": 20, "stretch": True, "anchor": "w"})
        if option is not None:
            return d.get(option)
        if not kw:
            return dict(d, id=c)
        for k, v in kw.items():
            if k in ("width", "minwidth"):
                v = int(v)
            elif k == "stretch":
                v = bool(v) and v not in ("0", "false", "no")
            d[k] = v
        self._kt_layout_planen()
        self._kt_neu_zeichnen()

    def heading(self, column, option=None, **kw):
        c = self._kt_spalte_name(column)
        d = self._kt_kopf.setdefault(c, {"text": "", "anchor": "center", "command": None, "image": ""})
        if option is not None:
            return d.get(option)
        if not kw:
            return dict(d)
        d.update(kw)
        self._kt_neu_zeichnen()

    def tag_configure(self, tagname, option=None, **kw):
        d = self._kt_tag_konf.setdefault(tagname, {})
        if option is not None:
            return d.get(option)
        d.update(kw)
        self._kt_neu_zeichnen()

    def tag_bind(self, tagname, sequence=None, callback=None):
        pass

    def tag_has(self, tagname, item=None):
        if item is None:
            return tuple(i for i, k in self._kt_knoten.items() if tagname in k["tags"])
        return tagname in self._kt_knoten[str(item)]["tags"]

    # -- geometry
    def _kt_zeile_h(self):
        return T._int(self._kt_s("rowheight", 20) or 20)

    def _kt_kopf_h(self):
        if not self._kt_zeigt("headings"):
            return 0
        f = self._kt_kopf_font()
        pad = T._padding(nachschlagen("Heading", "padding", frozenset(), 3) or 3)
        return fontmod.zeilen_hoehe(f) + pad[1] + pad[3] + 2

    def _kt_kopf_font(self):
        return nachschlagen("Treeview.Heading", "font", frozenset(),
                            nachschlagen("Heading", "font", frozenset(), "TkHeadingFont"))

    def _kt_sicht(self):
        return max(1, (self._kt_h - self._kt_kopf_h() - 2) // self._kt_zeile_h())

    def _kt_natuerlich(self):
        breite = sum(self._kt_spalten[c]["width"] for c in self._kt_anzeige_spalten()) + 2
        return breite, T._int(self._kt_o.get("height", 10)) * self._kt_zeile_h() + self._kt_kopf_h() + 2

    def _kt_breiten(self):
        """Column widths for the current widget width (stretchable ones share the rest)."""
        spalten = self._kt_anzeige_spalten()
        b = [self._kt_spalten[c]["width"] for c in spalten]
        rest = self._kt_w - 2 - sum(b)
        dehnbar = [i for i, c in enumerate(spalten) if self._kt_spalten[c].get("stretch", True)]
        if rest > 0 and dehnbar:
            pro = rest // len(dehnbar)
            for i in dehnbar:
                b[i] += pro
            b[dehnbar[-1]] += rest - pro * len(dehnbar)
        return spalten, b

    def _kt_sichtbare(self):
        erg = []

        def lauf(item, tiefe):
            for c in self._kt_knoten[item]["kinder"]:
                erg.append(c)
                self._kt_tiefe[c] = tiefe
                if self._kt_knoten[c]["open"] and self._kt_knoten[c]["kinder"]:
                    lauf(c, tiefe + 1)
        self._kt_tiefe = {}
        lauf("", 0)
        return erg

    def _kt_geaendert(self):
        self._kt_neu_zeichnen()
        self._kt_scroll_melden()

    def _kt_scroll_melden(self):
        cmd = self._kt_o.get("yscrollcommand")
        if cmd:
            n = max(1, len(self._kt_sichtbare()))
            s = self._kt_sicht()
            try:
                cmd(self._kt_oben / n, min(1.0, (self._kt_oben + s) / n))
            except Exception:
                pass

    def yview(self, *args):
        n = max(1, len(self._kt_sichtbare()))
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

    def _kt_setzen(self, x, y, w, h, sichtbar=True):
        super()._kt_setzen(x, y, w, h, sichtbar)
        self._kt_oben = max(0, min(self._kt_oben, max(0, len(self._kt_sichtbare()) - self._kt_sicht())))
        self._kt_scroll_melden()

    def identify_row(self, y):
        kh = self._kt_kopf_h() + 1
        if y < kh:
            return ""
        i = self._kt_oben + (int(y) - kh) // self._kt_zeile_h()
        s = self._kt_sichtbare()
        return s[i] if 0 <= i < len(s) else ""

    def identify_column(self, x):
        spalten, b = self._kt_breiten()
        pos = 1
        for i, w in enumerate(b):
            if x < pos + w:
                c = spalten[i]
                return "#0" if c == "#0" else "#%d" % (self._kt_spalten_namen().index(c) + 1)
            pos += w
        return ""

    def identify_region(self, x, y):
        if y < self._kt_kopf_h():
            return "heading"
        return "cell" if self.identify_row(y) else "nothing"

    def identify(self, component, x, y):
        if component == "row" or component == "item":
            return self.identify_row(y)
        if component == "column":
            return self.identify_column(x)
        return ""

    def bbox(self, item, column=None):
        s = self._kt_sichtbare()
        if str(item) not in s:
            return ""
        i = s.index(str(item)) - self._kt_oben
        if i < 0 or i >= self._kt_sicht():
            return ""
        return (1, self._kt_kopf_h() + 1 + i * self._kt_zeile_h(), self._kt_w - 2, self._kt_zeile_h())

    # -- drawing
    def _kt_malen(self, kx, ky):
        """Draws the tree view: headings, visible rows (indentation, open / closed markers and
        images in the tree column, colours from the item tags), and the selection.
        """
        g, gi = self._kt_g_hinten, self._kt_g_inhalt
        z = self._kt_zustand - {"selected"}
        bg = _f(nachschlagen(self._kt_stil(), "fieldbackground", frozenset(z))) or \
            _f(nachschlagen(self._kt_stil(), "background", frozenset(z)), (1, 1, 1, 1))
        _rect(g, bg, kx, ky, self._kt_w, self._kt_h)
        _rahmen1(g, _f(nachschlagen(self._kt_stil(), "bordercolor", frozenset(z))), kx, ky, self._kt_w, self._kt_h)
        spalten, breiten = self._kt_breiten()
        font = self._kt_s("font", "TkDefaultFont")
        fg = _f(nachschlagen(self._kt_stil(), "foreground", frozenset(z)), (0, 0, 0, 1))
        sel_bg = _f(nachschlagen(self._kt_stil(), "background", frozenset(z | {"selected"})))
        sel_fg = _f(nachschlagen(self._kt_stil(), "foreground", frozenset(z | {"selected"})), fg)
        H = self._kt_h
        kh = self._kt_kopf_h()
        # headings
        if kh:
            hs = "Treeview.Heading"
            hz = frozenset()
            hbg = _f(nachschlagen(hs, "background", hz))
            hfg = _f(nachschlagen(hs, "foreground", hz), (0, 0, 0, 1))
            hf = self._kt_kopf_font()
            x = 1
            for c, w in zip(spalten, breiten):
                bx, by = kx + x, ky + H - 1 - kh
                _rect(g, hbg, bx, by, w, kh)
                _clam_rand(g, bx, by, w, kh, _f(nachschlagen(hs, "bordercolor", hz)),
                           _f(nachschlagen(hs, "lightcolor", hz)), _f(nachschlagen(hs, "darkcolor", hz)))
                k = self._kt_kopf.get(c, {})
                text = str(k.get("text", ""))
                if text:
                    a = k.get("anchor", "center")
                    tw = fontmod.text_breite(text, hf)
                    tx = x + (w - tw) // 2 if a in ("center", "n", "s") else (
                        x + 4 if "w" in a else x + w - tw - 4)
                    self._kt_text_zeichnen(gi, text, hf, hfg, max(x + 2, tx), 1 + kh / 2, "w", kx, ky)
                x += w
        # rows
        rh = self._kt_zeile_h()
        sicht = self._kt_sichtbare()
        namen = self._kt_spalten_namen()
        for n in range(self._kt_oben, min(len(sicht), self._kt_oben + self._kt_sicht())):
            iid = sicht[n]
            k = self._kt_knoten[iid]
            y = 1 + kh + (n - self._kt_oben) * rh
            gewaehlt = iid in self._kt_auswahl
            zbg, zfg = (sel_bg, sel_fg) if gewaehlt else (None, fg)
            for t in k["tags"]:
                tk_ = self._kt_tag_konf.get(t, {})
                if not gewaehlt:
                    zbg = _f(tk_.get("background")) or zbg
                    zfg = _f(tk_.get("foreground")) or zfg
            if zbg is not None:
                _rect(g, zbg, kx + 1, ky + H - y - rh, self._kt_w - 2, rh)
            x = 1
            for c, w in zip(spalten, breiten):
                if c == "#0":
                    text = k["text"]
                    einzug = 4 + 18 * self._kt_tiefe.get(iid, 0)
                    if k["kinder"]:
                        _pfeil(gi, zfg, kx + x + einzug + 4, ky + H - y - rh / 2,
                               7, "down" if k["open"] else "right")
                    if self._kt_zeigt("tree") and (k["kinder"] or self._kt_tiefe.get(iid, 0) or
                                                any(self._kt_knoten[s]["kinder"] for s in self._kt_knoten[""]["kinder"])):
                        einzug += 14
                    bild = k.get("image")
                    if bild:
                        bild = T._BILDER.get(str(bild)) if isinstance(bild, str) else bild
                        if bild:
                            tex = bild._kt_textur()
                            gi.add(Color(1, 1, 1, 1))
                            gi.add(Rectangle(texture=tex, size=(bild.width(), bild.height()),
                                             pos=(kx + x + einzug, ky + H - y - rh / 2 - bild.height() / 2)))
                            einzug += bild.width() + 4
                    a = "w"
                    tx = x + einzug
                else:
                    i = namen.index(c) if c in namen else -1
                    text = str(k["values"][i]) if 0 <= i < len(k["values"]) else ""
                    a = self._kt_spalten[c].get("anchor", "w")
                    tx = x + 4
                if text:
                    tf = font
                    tw = fontmod.text_breite(text, tf)
                    maxb = w - 6
                    if tw > maxb and maxb > 8:
                        text = _kuerzen(text, tf, maxb)
                        tw = fontmod.text_breite(text, tf)
                    if a in ("center", "n", "s"):
                        tx = x + (w - tw) // 2
                    elif "e" in a:
                        tx = x + w - tw - 4
                    self._kt_text_zeichnen(gi, text, tf, zfg, tx, y + rh / 2, "w", kx, ky)
                x += w

    def _kt_klick(self, ev):
        """Click in the tree view: on a heading runs its command; on the open / close marker
        toggles the item (<<TreeviewOpen>> / <<TreeviewClose>>); otherwise selects according
        to selectmode (extended: Ctrl toggles, Shift selects a range).
        """
        self.focus_set()
        kh = self._kt_kopf_h()
        if ev.y < kh:
            c = self.identify_column(ev.x)
            if c:
                cmd = self._kt_kopf.get(self._kt_spalte_name(c) if c != "#0" else "#0", {}).get("command")
                if cmd:
                    cmd()
            return
        iid = self.identify_row(ev.y)
        if not iid:
            return
        k = self._kt_knoten[iid]
        if k["kinder"] and self._kt_zeigt("tree"):
            einzug = 4 + 18 * self._kt_tiefe.get(iid, 0)
            if ev.x < einzug + 14:
                k["open"] = not k["open"]
                self._kt_ereignis("Virtual", _kt_virtuell="<<TreeviewOpen>>" if k["open"] else "<<TreeviewClose>>")
                self._kt_geaendert()
                return
        modus = self._kt_o.get("selectmode", "extended")
        self._kt_fokus_item = iid
        if modus == "none":
            return
        if modus == "extended" and ev.state & EV.CONTROL:
            self.selection_toggle(iid)
        elif modus == "extended" and ev.state & EV.SHIFT and self._kt_auswahl:
            s = self._kt_sichtbare()
            a = s.index(self._kt_auswahl[0]) if self._kt_auswahl[0] in s else 0
            b = s.index(iid)
            lo, hi = sorted((a, b))
            self.selection_set(s[lo:hi + 1])
        else:
            self.selection_set(iid)

    def _kt_taste(self, ev):
        s = self._kt_sichtbare()
        if not s or ev.keysym not in ("Up", "Down"):
            return
        akt = self._kt_fokus_item if self._kt_fokus_item in s else (self._kt_auswahl[0] if self._kt_auswahl else s[0])
        i = s.index(akt) + (1 if ev.keysym == "Down" else -1)
        i = max(0, min(len(s) - 1, i))
        self._kt_fokus_item = s[i]
        self.selection_set(s[i])
        self.see(s[i])

    def _kt_nimmt_fokus(self):
        return True

    def _kt_hover_aenderung(self):
        pass


def _kuerzen(text, font, breite):
    while text and fontmod.text_breite(text + "…", font) > breite:
        text = text[:-1]
    return text + "…"


def _tagliste(t):
    if not t:
        return ()
    if isinstance(t, str):
        return tuple(t.split())
    return tuple(str(x) for x in t)


def _flach_items(items):
    erg = []
    for i in items:
        if isinstance(i, (tuple, list)):
            erg.extend(_flach_items(i))
        else:
            erg.append(i)
    return erg


# ============================================================
# Notebook
# ============================================================
class Notebook(Widget):
    _kt_hover_aktiv = True
    _kt_klasse = "TNotebook"
    _kt_stil_basis = "TNotebook"
    _kt_standard = dict(Widget._kt_standard, width=0, height=0, padding="")

    def __init__(self, master=None, **kw):
        self._kt_tabs = []                # [(widget, {text, state, ...})]
        self._kt_aktiv = None
        super().__init__(master, **kw)

    def add(self, child, **kw):
        """add(child, **options): adds a page (or changes the options of an existing one); the
        first page becomes the selected one.
        """
        for w, o in self._kt_tabs:
            if w is child:
                o.update(kw)
                self._kt_neu_zeichnen()
                return
        self._kt_tabs.append((child, dict({"text": "", "state": "normal", "sticky": "nsew",
                                        "padding": 0, "image": "", "compound": "none"}, **kw)))
        child._kt_manager = "notebook"
        child._kt_geo_master = self
        child._kt_lebt = self._kt_aktiv is None
        if self._kt_aktiv is None:
            self._kt_aktiv = child
        else:
            child._kt_lebt = False
        self._kt_layout_planen()
        self._kt_neu_zeichnen()

    def insert(self, pos, child, **kw):
        self.add(child, **kw)

    def forget(self, tab_id):
        w = self._kt_tab_widget(tab_id)
        self._kt_tabs = [(x, o) for x, o in self._kt_tabs if x is not w]
        w._kt_abbilden(False)
        if self._kt_aktiv is w:
            self._kt_aktiv = self._kt_tabs[0][0] if self._kt_tabs else None
            if self._kt_aktiv:
                self._kt_aktiv._kt_lebt = True
        self._kt_layout_planen()

    hide = forget

    def tabs(self):
        return tuple(str(w) for w, _o in self._kt_tabs)

    def _kt_tab_widget(self, tab_id):
        if isinstance(tab_id, int):
            return self._kt_tabs[tab_id][0]
        if isinstance(tab_id, T.Misc):
            return tab_id
        s = str(tab_id)
        if s == "current":
            return self._kt_aktiv
        for w, _o in self._kt_tabs:
            if str(w) == s:
                return w
        return self.nametowidget(s)

    def select(self, tab_id=None):
        """select(tab_id=None): without argument the selected page, otherwise shows that page
        and sends <<NotebookTabChanged>>.
        """
        if tab_id is None:
            return str(self._kt_aktiv) if self._kt_aktiv else ""
        w = self._kt_tab_widget(tab_id)
        if w is self._kt_aktiv:
            return
        if self._kt_aktiv is not None:
            self._kt_aktiv._kt_abbilden(False)
        self._kt_aktiv = w
        w._kt_lebt = True
        self._kt_layout_planen()
        self._kt_neu_zeichnen()
        self.event_generate("<<NotebookTabChanged>>")

    def index(self, tab_id):
        if tab_id == "end":
            return len(self._kt_tabs)
        w = self._kt_tab_widget(tab_id)
        for i, (x, _o) in enumerate(self._kt_tabs):
            if x is w:
                return i
        raise T.TclError(f"{tab_id} is not managed by {self}")

    def tab(self, tab_id, option=None, **kw):
        w = self._kt_tab_widget(tab_id)
        for x, o in self._kt_tabs:
            if x is w:
                if option:
                    return o.get(option)
                if not kw:
                    return dict(o)
                o.update(kw)
                self._kt_neu_zeichnen()

    def _kt_tab_h(self):
        return fontmod.zeilen_hoehe(self._kt_s("font", "TkDefaultFont")) + 8

    def _kt_tab_breiten(self):
        f = self._kt_s("font", "TkDefaultFont")
        return [fontmod.text_breite(str(o.get("text", "")), f) + 14 for _w, o in self._kt_tabs]

    def _kt_req(self):
        """Requested size of the notebook: the largest page plus the height of the tab row
        (cached per layout pass).
        """
        r = self._kt_root_
        if self._kt_req_pass == r._kt_pass:
            return self._kt_req_wert
        w = h = 0
        for x, _o in self._kt_tabs:
            rw, rh = x._kt_req()
            w, h = max(w, rw), max(h, rh)
        w = max(w, sum(self._kt_tab_breiten()), T._int(self._kt_o.get("width", 0)))
        h = max(h, T._int(self._kt_o.get("height", 0)))
        self._kt_req_pass = r._kt_pass
        self._kt_req_wert = (w + 4, h + self._kt_tab_h() + 4)
        return self._kt_req_wert

    def _kt_anordnen(self):
        th = self._kt_tab_h()
        for x, _o in self._kt_tabs:
            if x is self._kt_aktiv:
                x._kt_lebt = True
                x._kt_setzen(2, th + 2, max(1, self._kt_w - 4), max(1, self._kt_h - th - 4))
            else:
                x._kt_setzen(0, 0, 0, 0, sichtbar=False)
        T.Misc._kt_anordnen(self)

    def _kt_malen(self, kx, ky):
        """Draws the notebook: the tab row (selected tab raised, joined to the page) and the
        border of the page area.
        """
        g = self._kt_g_hinten
        bg = self._kt_sf("background")
        _rect(g, bg, kx, ky, self._kt_w, self._kt_h)
        th = self._kt_tab_h()
        rand = self._kt_sf("bordercolor")
        _rahmen1(g, rand, kx, ky, self._kt_w, self._kt_h - th)
        x = 2
        f = self._kt_s("font", "TkDefaultFont")
        for (w, o), b in zip(self._kt_tabs, self._kt_tab_breiten()):
            sel = w is self._kt_aktiv
            z = frozenset({"selected"}) if sel else frozenset()
            tbg = _f(nachschlagen("TNotebook.Tab", "background", z))
            hoehe = th if sel else th - 2
            _rect(g, tbg, kx + x, ky + self._kt_h - th, b, hoehe)
            _rahmen1(g, rand, kx + x, ky + self._kt_h - th, b, hoehe)
            if sel:
                _rect(g, tbg, kx + x + 1, ky + self._kt_h - th - 1, b - 2, 2)
            tfg = _f(nachschlagen("TNotebook.Tab", "foreground", z), (0, 0, 0, 1))
            self._kt_text_zeichnen(self._kt_g_inhalt, str(o.get("text", "")), f, tfg,
                                x + b / 2, th / 2 + (0 if sel else 1), "center", kx, ky)
            x += b

    def _kt_klick(self, ev):
        if ev.y > self._kt_tab_h():
            return
        x = 2
        for (w, o), b in zip(self._kt_tabs, self._kt_tab_breiten()):
            if x <= ev.x < x + b and o.get("state") != "disabled":
                self.select(w)
                return
            x += b


# ============================================================
# Progressbar / Scale / PanedWindow (simple)
# ============================================================
class Progressbar(Widget):
    _kt_klasse = "TProgressbar"
    _kt_stil_basis = "TProgressbar"
    _kt_standard = dict(Widget._kt_standard, orient=T.HORIZONTAL, length=100, mode="determinate",
                     maximum=100, value=0, variable=None)

    def _kt_natuerlich(self):
        l = T._int(self._kt_o.get("length", 100))
        return (l, 16) if self._kt_o.get("orient") == T.HORIZONTAL else (16, l)

    def _kt_wert(self):
        v = self._kt_o.get("variable")
        try:
            return float(v.get()) if isinstance(v, T.Variable) else float(self._kt_o.get("value", 0))
        except (T.TclError, ValueError):
            return 0.0

    def _kt_malen(self, kx, ky):
        g = self._kt_g_hinten
        _rect(g, self._kt_sf("troughcolor"), kx, ky, self._kt_w, self._kt_h)
        anteil = max(0.0, min(1.0, self._kt_wert() / max(1e-9, float(self._kt_o.get("maximum", 100)))))
        _rect(g, self._kt_sf("background"), kx + 1, ky + 1, int((self._kt_w - 2) * anteil), self._kt_h - 2)
        _rahmen1(g, self._kt_sf("bordercolor"), kx, ky, self._kt_w, self._kt_h)

    def step(self, amount=1.0):
        self._kt_o["value"] = float(self._kt_o.get("value", 0)) + amount
        self._kt_neu_zeichnen()

    def start(self, interval=None):
        pass

    def stop(self):
        pass

    def __setitem__(self, k, v):
        self.configure(**{k: v})


class Scale(Widget):
    _kt_klasse = "TScale"
    _kt_stil_basis = "TScale"
    _kt_standard = dict(Widget._kt_standard, orient=T.HORIZONTAL, length=100, from_=0, to=100,
                     variable=None, command=None, value=0)

    def _kt_natuerlich(self):
        l = T._int(self._kt_o.get("length", 100))
        return (l, 18) if self._kt_o.get("orient") == T.HORIZONTAL else (18, l)

    def get(self):
        v = self._kt_o.get("variable")
        return v.get() if isinstance(v, T.Variable) else self._kt_o.get("value", 0)

    def set(self, value):
        v = self._kt_o.get("variable")
        if isinstance(v, T.Variable):
            v.set(value)
        self._kt_o["value"] = value
        self._kt_neu_zeichnen()


class PanedWindow(Widget):
    _kt_klasse = "TPanedwindow"
    _kt_standard = dict(Widget._kt_standard, orient=T.VERTICAL)

    def add(self, child, **kw):
        child.pack(side=T.LEFT if self._kt_o.get("orient") == T.HORIZONTAL else T.TOP,
                   fill=T.BOTH, expand=True)

    def panes(self):
        return tuple(str(w) for w in self._pack_slaves)


Panedwindow = PanedWindow


class LabeledScale(Frame):
    pass
