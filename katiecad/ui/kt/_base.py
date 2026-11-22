# -*- coding: utf-8 -*-
"""
katiecad/ui/kt/_base.py - shared state of the Kivy layer (BSD-3-Clause).
"""

ROOT = [None]            # the tk.Tk instance
_skal = [None]


def skalierung():
    """Pixels per point, like Tk's "tk scaling" (96 dpi -> 1.333)."""
    if _skal[0] is None:
        dpi = 96.0
        try:
            from kivy.core.window import Window
            dpi = float(Window.dpi) or 96.0
        except Exception:
            pass
        dpi = max(dpi, 96.0)         # macOS reports 72 dpi (points): text would be 25 % too small
        faktor = 1.0
        try:                       # manual correction, e.g. KATIECAD_SKALIERUNG=1.25 (0.5 ... 3)
            import os
            faktor = min(3.0, max(0.5, float(os.environ.get("KATIECAD_SKALIERUNG", "1") or 1)))
        except ValueError:
            pass
        _skal[0] = dpi / 72.0 * faktor
    return _skal[0]


_bildschirm = [None]


def auf_bildschirm(w, h):
    """macOS: limits a wished window size to the screen (menu bar, Dock and window frame are left out). A
    window larger than the screen is shrunk by the system, but Kivy does not notice, so the
    top of the program would be cut off. Elsewhere / if the size is unknown: unchanged."""
    import sys
    if not sys.platform == "darwin":
        return w, h
    if _bildschirm[0] is None:
        _bildschirm[0] = (0, 0)
        try:
            import subprocess
            erg = subprocess.run(
                ["osascript", "-e",
                 'tell application "Finder" to get bounds of window of desktop'],
                capture_output=True, text=True, timeout=5).stdout
            z = [int(t) for t in erg.replace(",", " ").split()]
            if len(z) == 4:
                _bildschirm[0] = (z[2] - z[0], z[3] - z[1])
        except Exception:
            pass
    sw, sh = _bildschirm[0]
    if sw <= 0 or sh <= 0:
        return w, h
    return min(w, sw - 40), min(h, sh - 200)


def alles_neu():
    """Something global changed (a named font): measure and draw every widget again."""
    r = ROOT[0]
    if r is not None:
        r._kt_alles_ungueltig()


def farbe(name, standard=(0, 0, 0, 1)):
    """Tk colour ("#rgb", "#rrggbb", "#rrrrggggbbbb", names) -> (r, g, b, a) or None for ""."""
    if name is None or name == "":
        return None
    if isinstance(name, tuple):
        return name
    try:
        return _farb_cache[name]
    except KeyError:
        pass
    s = str(name).strip()
    erg = None
    if s.startswith("#"):
        h = s[1:]
        n = len(h) // 3
        if n and len(h) == 3 * n:
            try:
                m = 16 ** n - 1
                erg = (int(h[:n], 16) / m, int(h[n:2 * n], 16) / m, int(h[2 * n:], 16) / m, 1.0)
            except ValueError:
                erg = None
    else:
        rgb = FARB_NAMEN.get(s.lower().replace(" ", ""))
        if rgb is not None:
            erg = (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1.0)
    if erg is None:
        from katiecad.ui.kt.tkmod import TclError
        raise TclError(f'unknown color name "{name}"')
    _farb_cache[name] = erg
    return erg


_farb_cache = {}

FARB_NAMEN = {
    "black": (0, 0, 0), "white": (255, 255, 255), "red": (255, 0, 0), "green": (0, 128, 0),
    "lime": (0, 255, 0), "blue": (0, 0, 255), "yellow": (255, 255, 0), "cyan": (0, 255, 255),
    "magenta": (255, 0, 255), "gray": (190, 190, 190), "grey": (190, 190, 190),
    "darkgray": (169, 169, 169), "darkgrey": (169, 169, 169), "lightgray": (211, 211, 211),
    "lightgrey": (211, 211, 211), "orange": (255, 165, 0), "purple": (160, 32, 240),
    "brown": (165, 42, 42), "pink": (255, 192, 203), "navy": (0, 0, 128),
    "darkblue": (0, 0, 139), "darkred": (139, 0, 0), "darkgreen": (0, 100, 0),
    "gold": (255, 215, 0), "silver": (192, 192, 192), "maroon": (176, 48, 96),
    "olive": (128, 128, 0), "teal": (0, 128, 128), "violet": (238, 130, 238),
    "gray50": (127, 127, 127), "grey50": (127, 127, 127), "gray25": (64, 64, 64),
    "gray75": (191, 191, 191), "systembuttonface": (240, 240, 240),
    "systemwindow": (255, 255, 255), "systembuttontext": (0, 0, 0),
    "systemwindowtext": (0, 0, 0), "systemhighlight": (0, 120, 215),
    "systemhighlighttext": (255, 255, 255), "systemdisabledtext": (109, 109, 109),
    "lightblue": (173, 216, 230), "lightyellow": (255, 255, 224), "darkorange": (255, 140, 0),
    "steelblue": (70, 130, 180), "skyblue": (135, 206, 235), "crimson": (220, 20, 60),
    "khaki": (240, 230, 140), "salmon": (250, 128, 114), "coral": (255, 127, 80),
    "tomato": (255, 99, 71), "turquoise": (64, 224, 208), "indigo": (75, 0, 130),
    "beige": (245, 245, 220), "ivory": (255, 255, 240), "wheat": (245, 222, 179),
}
