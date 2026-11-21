# -*- coding: utf-8 -*-
"""
katiecad/ui/kt/titelleiste.py - own title bar of the main window (BSD-3-Clause).

With Kivy's custom_titlebar the system title bar disappears and this one is drawn in the
style of the dialogs (colours follow the main window), the same on Windows, Linux and macOS.
Moving the window, snapping to screen edges and double click to maximise stay with the
operating system (the bar is the "drag area"); only the buttons are ours. On Windows the
native frame stays: resizing at the edges, shadow and rounded corners as usual.

macOS: close / minimise / zoom as the three coloured dots on the left, title centred.
Windows / Linux: minimise / maximise / close on the right, close turns red on hover.

KATIECAD_TITELLEISTE=system keeps the title bar of the operating system.
"""

import os
import sys

from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line, Ellipse, InstructionGroup
from kivy.uix.widget import Widget

from katiecad.ui.kt import fontmod

HOEHE = 32
KNOPF_B = 46                          # Windows: width of one button
MAC = sys.platform == "darwin"


def gewuenscht():
    return os.environ.get("KATIECAD_TITELLEISTE", "").strip().lower() != "system"


def _heller(f, faktor):
    return tuple(min(1.0, c * faktor) for c in f[:3]) + (1.0,)


class Titelleiste(Widget):
    def __init__(self, root, **kw):
        super().__init__(size_hint=(None, None), **kw)
        self.root_tk = root
        self.hover = None             # "min" / "max" / "zu" under the pointer
        self.gedrueckt = None
        self.aktiv = True
        self.maximiert = False
        self._g = InstructionGroup()
        self.canvas.add(self._g)
        self._symbol = None

    # ---------------------------------------------------- geometry (Tk coordinates: y down)
    def knoepfe(self):
        """-> [(name, x0, x1)] in window x coordinates."""
        l, _t, r, _b = self.root_tk._kt_rand
        w = int(self.root_tk._kt_fenster_w) - r
        if MAC:
            return [("zu", l + 8, l + 28), ("min", l + 28, l + 48), ("max", l + 48, l + 68)]
        return [("min", w - 3 * KNOPF_B, w - 2 * KNOPF_B), ("max", w - 2 * KNOPF_B, w - KNOPF_B),
                ("zu", w - KNOPF_B, w)]

    def knopf_bei(self, x, y):
        y -= self.root_tk._kt_rand[1]
        if y < 0 or y >= HOEHE:
            return None
        for name, x0, x1 in self.knoepfe():
            if x0 <= x < x1:
                return name
        return None

    def in_drag_area(self, x, y):
        """Called by Kivy/SDL for the system hit test (Kivy coordinates, y from the bottom):
        True = this point moves the window (the bar outside of our buttons)."""
        ty = self.root_tk._kt_fenster_h - y
        return 0 <= ty - self.root_tk._kt_rand[1] < HOEHE and self.knopf_bei(x, ty) is None

    # ---------------------------------------------------- state
    def setze_hover(self, name):
        if name != self.hover:
            self.hover = name
            self.zeichnen()

    def runter(self, x, y):
        self.gedrueckt = self.knopf_bei(x, y)
        self.zeichnen()
        return self.gedrueckt is not None

    def los(self, x, y):
        name, self.gedrueckt = self.gedrueckt, None
        self.zeichnen()
        if name is None or name != self.knopf_bei(x, y):
            return
        try:
            if name == "min":
                Window.minimize()
            elif name == "max":
                Window.restore() if self.maximiert else Window.maximize()
            elif name == "zu":
                if self.root_tk._kt_k_schliessen() is False:
                    pass
        except Exception:
            pass

    # ---------------------------------------------------- drawing
    def _farben(self):
        bg = self.root_tk._kt_farbe_opt("background", (0.94, 0.94, 0.94, 1))
        dunkel = sum(bg[:3]) < 1.2
        leiste = bg if dunkel else _heller(bg, 0.92)
        rand = _heller(bg, 1.9) if dunkel else _heller(bg, 0.6)
        text = (0.95, 0.95, 0.95, 1) if dunkel else (0.1, 0.1, 0.1, 1)
        if not self.aktiv:
            text = tuple(c * 0.55 + b * 0.45 for c, b in zip(text[:3], leiste[:3])) + (1,)
        hover = _heller(leiste, 2.2) if dunkel else _heller(leiste, 0.85)
        return leiste, rand, text, hover

    def _symbol_textur(self):
        if self._symbol is None:
            self._symbol = False
            try:
                from katiecad.ui.app import _symbol_datei
                from PIL import Image
                from kivy.graphics.texture import Texture
                pfad = _symbol_datei("KatieCAD.png")
                if pfad:
                    im = Image.open(pfad).convert("RGBA").resize((16, 16), Image.Resampling.LANCZOS)
                    t = Texture.create(size=(16, 16), colorfmt="rgba")
                    t.blit_buffer(im.tobytes(), colorfmt="rgba", bufferfmt="ubyte")
                    t.flip_vertical()
                    self._symbol = t
            except Exception:
                self._symbol = False
        return self._symbol or None

    def zeichnen(self, *_a):
        W, H = int(self.root_tk._kt_fenster_w), int(self.root_tk._kt_fenster_h)   # (Kivy lags)
        l, t, r, _b = self.root_tk._kt_rand
        H -= t                                           # maximised: frame strip above the bar
        self.pos, self.size = (0, H - HOEHE), (W, HOEHE)
        g = self._g
        g.clear()
        leiste, rand, text, hover = self._farben()
        y0 = H - HOEHE                                   # Kivy: bottom of the bar
        g.add(Color(*leiste))
        g.add(Rectangle(pos=(0, y0), size=(W, HOEHE + t)))   # incl. the strip above (maximised)
        g.add(Color(*rand))
        g.add(Rectangle(pos=(0, y0), size=(W, 1)))
        titel = self.root_tk._kt_titel or "KatieCAD"
        tex = fontmod.text_textur(titel, "TkDefaultFont")
        if MAC:
            farben = {"zu": (1.0, 0.37, 0.34, 1), "min": (1.0, 0.74, 0.18, 1), "max": (0.16, 0.79, 0.25, 1)}
            for name, x0, x1 in self.knoepfe():
                c = farben[name] if self.aktiv else (0.45, 0.45, 0.45, 1)
                g.add(Color(*c))
                g.add(Ellipse(pos=((x0 + x1) / 2 - 6, y0 + HOEHE / 2 - 6), size=(12, 12), segments=24))
                if self.hover in ("zu", "min", "max"):                # symbols on hover, like macOS
                    g.add(Color(0.3, 0.1, 0.1, 0.8))
                    cx, cy = (x0 + x1) / 2, y0 + HOEHE / 2
                    if name == "zu":
                        g.add(Line(points=[cx - 3, cy - 3, cx + 3, cy + 3], width=1))
                        g.add(Line(points=[cx - 3, cy + 3, cx + 3, cy - 3], width=1))
                    elif name == "min":
                        g.add(Line(points=[cx - 3.5, cy, cx + 3.5, cy], width=1))
                    else:
                        g.add(Line(points=[cx - 3, cy, cx + 3, cy], width=1))
                        g.add(Line(points=[cx, cy - 3, cx, cy + 3], width=1))
            if tex is not None:
                fontmod.text_zeichnen(g, tex, text, (int(W / 2 - tex.size[0] / 2),
                                                     int(y0 + HOEHE / 2 - tex.size[1] / 2)), tex.size)
            return
        x = 10 + l
        sym = self._symbol_textur()
        if sym is not None:
            g.add(Color(1, 1, 1, 1 if self.aktiv else 0.6))
            g.add(Rectangle(texture=sym, pos=(x, y0 + (HOEHE - 16) // 2), size=(16, 16)))
            x += 24
        if tex is not None:
            fontmod.text_zeichnen(g, tex, text, (x, int(y0 + HOEHE / 2 - tex.size[1] / 2)), tex.size)
        for name, x0, x1 in self.knoepfe():
            aktiv = self.hover == name or self.gedrueckt == name
            if aktiv:
                g.add(Color(*((0.77, 0.17, 0.11, 1) if name == "zu" else hover)))
                g.add(Rectangle(pos=(x0, y0 + 1), size=(x1 - x0, HOEHE - 1)))
            g.add(Color(*((1, 1, 1, 1) if aktiv and name == "zu" else text)))
            cx, cy = int((x0 + x1) / 2) + 0.5, int(y0 + HOEHE / 2) + 0.5
            if name == "min":
                g.add(Line(points=[cx - 5, cy, cx + 5, cy], width=1))
            elif name == "max":
                if self.maximiert:                        # restore: two overlapping squares
                    g.add(Line(rectangle=(cx - 5, cy - 5, 8, 8), width=1))
                    g.add(Line(points=[cx - 3, cy + 3, cx - 3, cy + 5, cx + 5, cy + 5, cx + 5, cy - 3,
                                       cx + 3, cy - 3], width=1))
                else:
                    g.add(Line(rectangle=(cx - 5, cy - 5, 10, 10), width=1))
            else:
                g.add(Line(points=[cx - 5, cy - 5, cx + 5, cy + 5], width=1))
                g.add(Line(points=[cx - 5, cy + 5, cx + 5, cy - 5], width=1))


def einrichten(root):
    """-> Titelleiste or None (system title bar)."""
    if not gewuenscht() or not getattr(Window, "custom_titlebar", False):
        return None
    leiste = Titelleiste(root)
    Window.add_widget(leiste)
    try:
        if not Window.set_custom_titlebar(leiste):
            Window.remove_widget(leiste)
            return None
    except Exception:
        Window.remove_widget(leiste)
        return None

    def maximiert(an):
        leiste.maximiert = an
        root._kt_rand_setzen(an)
        leiste.zeichnen()

    Window.bind(on_maximize=lambda *_a: maximiert(True), on_restore=lambda *_a: maximiert(False),
                on_minimize=lambda *_a: None, size=leiste.zeichnen)
    leiste.zeichnen()
    return leiste
