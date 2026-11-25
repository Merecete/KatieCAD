# -*- coding: utf-8 -*-
"""
katiecad/ui/kt/fontmod.py - tkinter.font on Kivy (BSD-3-Clause).

Font specs as Tk knows them ("Segoe UI 9 bold", ("Segoe UI", 9, "bold"), named
fonts, Font objects) are resolved to a TrueType file and a pixel size. Text is
rendered once per (text, font) as a white texture and tinted when drawn.
"""

import os
import sys

from kivy.core.text import Label as _CoreLabel, LabelBase

from katiecad.ui.kt import _base

NORMAL, ROMAN, BOLD, ITALIC = "normal", "roman", "bold", "italic"

# ------------------------------------------------------------
# Font files of the system
# ------------------------------------------------------------
_familien = None        # family (lower case) -> {"regular": pfad, "bold": .., "italic": .., "bolditalic": ..}
_namen = {}             # family (lower case) -> family as written


def _windows_fonts():
    """Installed fonts on Windows as (name, file) pairs, read from the registry (all users and
    the current user). Names like "Segoe UI Bold (TrueType)" are cleaned; collections listed
    as "A & B" give one entry per name.
    """
    import winreg
    ordner = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    erg = []
    for wurzel, pfad in ((winreg.HKEY_LOCAL_MACHINE, ordner),
                         (winreg.HKEY_CURRENT_USER, None)):
        try:
            k = winreg.OpenKey(wurzel, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
        except OSError:
            continue
        i = 0
        while True:
            try:
                name, datei, _t = winreg.EnumValue(k, i)
            except OSError:
                break
            i += 1
            if not isinstance(datei, str) or not datei.lower().endswith((".ttf", ".otf", ".ttc")):
                continue
            if not os.path.isabs(datei):
                datei = os.path.join(pfad or ordner, datei)
            name = name.replace("(TrueType)", "").replace("(OpenType)", "").strip()
            for teil in name.split("&"):
                erg.append((teil.strip(), datei))
    return erg


# fontconfig style names that mean the normal cut (DejaVu calls it "Book", others "Roman" ...);
# without this "DejaVu Sans" had no regular cut and the BOLD file was used for all normal text
_NORMALSTILE = ("regular", "book", "roman", "normal", "text")


def _unix_fonts():
    """Installed fonts on Linux / macOS as (name, file) pairs from fontconfig (`fc-list`); the
    style is appended to the family unless it is "Regular". Empty list if fc-list is missing.
    """
    import subprocess
    try:
        aus = subprocess.run(["fc-list", ":", "family", "style", "file"], capture_output=True,
                             text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    erg = []
    for zeile in aus.splitlines():
        try:
            datei, rest = zeile.split(":", 1)
            fam, _, stil = rest.partition(":style=")
            fam = fam.split(",")[0].strip()
            stil = stil.split(",")[0].strip()
        except ValueError:
            continue
        if not datei.lower().endswith((".ttf", ".otf", ".ttc")):
            continue
        erg.append((f"{fam} {stil}" if stil and stil.lower() not in _NORMALSTILE else fam, datei.strip()))
    return erg


def _mac_fonts():
    """macOS has no fc-list: reads the family and style names of the font files in the system
    folders with fontTools (first font of a collection). The result is cached in
    ~/Library/Caches/KatieCAD/fontindex.json and reused while the folders are unchanged."""
    import json
    ordner = ["/System/Library/Fonts", "/System/Library/Fonts/Supplemental", "/Library/Fonts",
              os.path.expanduser("~/Library/Fonts")]
    stempel = []
    for o in ordner:
        try:
            stempel.append([o, os.stat(o).st_mtime_ns, len(os.listdir(o))])
        except OSError:
            stempel.append([o, 0, 0])
    cache = os.path.expanduser("~/Library/Caches/KatieCAD/fontindex.json")
    try:
        with open(cache, encoding="utf-8") as f:
            d = json.load(f)
        if d.get("stempel") == stempel:
            return [tuple(x) for x in d["fonts"]]
    except (OSError, ValueError, KeyError):
        pass
    erg = []
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return []
    for o in ordner:
        try:
            namen = sorted(os.listdir(o))
        except OSError:
            continue
        for n in namen:
            if not n.lower().endswith((".ttf", ".otf", ".ttc")):
                continue
            pfad = os.path.join(o, n)
            try:
                f = TTFont(pfad, fontNumber=0, lazy=True)
                nm = f["name"]
                fam = (nm.getDebugName(16) or nm.getDebugName(1) or "").strip()
                stil = (nm.getDebugName(17) or nm.getDebugName(2) or "Regular").strip()
                f.close()
            except Exception:
                continue
            if fam:
                erg.append((f"{fam} {stil}" if stil.lower() != "regular" else fam, pfad))
    try:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, "w", encoding="utf-8") as f:
            json.dump({"stempel": stempel, "fonts": erg}, f)
    except OSError:
        pass
    return erg


_STILE = (("bold italic", "bolditalic"), ("bold oblique", "bolditalic"),
          ("bold", "bold"), ("italic", "italic"), ("oblique", "italic"), ("regular", "regular"))


def _familien_laden():
    """Index of the installed fonts, built once: family (lower case) -> {style: file}, with
    style regular / bold / italic / bolditalic taken from the end of the name. Used to turn a
    Tk font spec into a TrueType file.
    """
    global _familien
    if _familien is not None:
        return _familien
    _familien = {}
    try:
        liste = (_windows_fonts() if sys.platform.startswith("win")
                 else _mac_fonts() if sys.platform == "darwin" else _unix_fonts())
    except Exception:
        liste = []
    for name, datei in liste:
        low = name.lower()
        stil = "regular"
        fam = name
        for endung, s in _STILE:
            if low.endswith(" " + endung):
                stil = s
                fam = name[: -len(endung) - 1]
                break
        # weight variants ("Segoe UI Light", "Arial Narrow" ...) stay families of their own,
        # as they are for Tk
        key = fam.lower()
        _namen.setdefault(key, fam)
        _familien.setdefault(key, {}).setdefault(stil, datei)
    return _familien


def _fallback_datei():
    """Kivy's own Roboto font. In a packed program (PyInstaller / AppImage) the Kivy data folder
    is NOT next to kivy/__init__.py, so every plausible place is tried; the first existing wins."""
    import kivy
    name = "Roboto-Regular.ttf"
    kandidaten = []
    try:
        kandidaten.append(os.path.join(kivy.kivy_data_dir, "fonts", name))
    except Exception:
        pass
    try:
        from kivy.resources import resource_find
        kandidaten.append(resource_find("data/fonts/" + name) or "")
    except Exception:
        pass
    kandidaten.append(os.path.join(os.path.dirname(kivy.__file__), "data", "fonts", name))
    basis = getattr(sys, "_MEIPASS", "")
    if basis:
        for teil in (("kivy_install", "data", "fonts"), ("kivy", "data", "fonts"), ("data", "fonts")):
            kandidaten.append(os.path.join(basis, *teil, name))
    for d in kandidaten:
        if d and os.path.isfile(d):
            return d
    # last resort: any installed TrueType sans font, so that the window is never empty
    for d in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf",
              "/usr/share/fonts/dejavu/DejaVuSans.ttf", "/usr/share/fonts/noto/NotoSans-Regular.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
              "C:/Windows/Fonts/arial.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.isfile(d):
            return d
    return kandidaten[0] if kandidaten and kandidaten[0] else name


_ALIAS = {"helvetica": ("arial", "liberation sans", "dejavu sans"),
          "courier": ("courier new", "liberation mono", "dejavu sans mono"),
          "times": ("times new roman", "liberation serif", "dejavu serif"),
          "tkdefaultfont": ("segoe ui", "dejavu sans"),
          "helvetica neue": ("helvetica neue", "arial"),
          "segoe ui": ("segoe ui", "dejavu sans", "arial")}

_registriert = {}
_dateien = {}           # Kivy font name -> regular file (for the glyph coverage)


def _kivy_name(familie):
    """Registers the family with Kivy (regular/bold/italic files) -> Kivy font name."""
    key = (familie or "").lower()
    if key in _registriert:
        return _registriert[key]
    fams = _familien_laden()
    kandidaten = [key] + list(_ALIAS.get(key, ())) + ["segoe ui", "arial", "dejavu sans"]
    dateien = None
    for k in kandidaten:
        if k in fams and "regular" in fams[k]:
            dateien = fams[k]
            break
        if k in fams:            # only a bold/italic cut installed
            d = fams[k]
            dateien = {"regular": next(iter(d.values()))}
            dateien.update(d)
            break
    if dateien is None:
        dateien = {"regular": _fallback_datei()}
    name = "kt_" + key.replace(" ", "_") if key else "kt_default"
    reg = dateien["regular"]
    try:
        LabelBase.register(name, reg, dateien.get("italic"), dateien.get("bold"),
                           dateien.get("bolditalic"))
    except Exception:
        LabelBase.register(name, _fallback_datei())
    _registriert[key] = name
    _dateien[name] = reg
    return name


# ------------------------------------------------------------
# Glyph fallback: Tk/Windows takes missing characters (⋮ ☰ ▸ ✓ ...) from another font;
# SDL2_ttf does not, so the text is split into runs per font.
# ------------------------------------------------------------
_abdeckung_cache = {}
_ERSATZ = ("Segoe UI Symbol", "Segoe UI Emoji", "Arial Unicode MS", "DejaVu Sans",
           "Noto Sans Symbols", "Noto Sans Symbols2", "Symbola",
           "Apple Symbols", "Menlo", "Zapf Dingbats")        # macOS


def _abdeckung(kname):
    """The characters a font file contains (cached, read with fontTools; None if unknown). Text
    with characters the font lacks is split into runs drawn with a fallback font.
    """
    a = _abdeckung_cache.get(kname, False)
    if a is False:
        a = None
        pfad = _dateien.get(kname)
        if pfad:
            try:
                from fontTools.ttLib import TTFont
                f = TTFont(pfad, fontNumber=0, lazy=True)
                a = frozenset(f.getBestCmap() or ())
                f.close()
            except Exception:
                a = None
        _abdeckung_cache[kname] = a
    return a


def _hat(kname, ch):
    a = _abdeckung(kname)
    return a is None or ord(ch) in a or ch in " \t"


def _laeufe(text, k):
    """-> [(part, key)] - one part per font; usually just [(text, k)]."""
    if all(ord(ch) < 0x2000 for ch in text):
        return [(text, k)]
    haupt = _kivy_name(k[0])
    if all(_hat(haupt, ch) for ch in text):
        return [(text, k)]
    erg = []
    for ch in text:
        fam = k[0]
        if not _hat(haupt, ch):
            for e in _ERSATZ:
                if e.lower() in _familien_laden() and _hat(_kivy_name(e), ch):
                    fam = e
                    break
        kk = (fam,) + tuple(k[1:])
        if erg and erg[-1][1] == kk:
            erg[-1] = (erg[-1][0] + ch, kk)
        else:
            erg.append((ch, kk))
    return erg


def families(root=None, displayof=None):
    fams = _familien_laden()
    return tuple(sorted({_namen.get(k, k) for k, v in fams.items()}))


# ------------------------------------------------------------
# Point -> pixel (Tk "scaling")
# ------------------------------------------------------------
def pixel(size):
    """Tk size (points > 0, pixels < 0) -> pixels."""
    try:
        size = float(size)
    except (TypeError, ValueError):
        size = 9
    if size < 0:
        return max(1, int(round(-size)))
    return max(1, int(round(size * _base.skalierung())))


# ------------------------------------------------------------
# Font objects
# ------------------------------------------------------------
_STANDARD = sys.platform.startswith("win") and "Segoe UI" or \
    (sys.platform == "darwin" and "Helvetica Neue" or "DejaVu Sans")
_benannt = {}


class Font:
    _kt_zaehler = 0

    def __init__(self, root=None, font=None, name=None, exists=False, **opt):
        if font is not None:
            fam, size, weight, slant, underline, over = _parse(font)
        else:
            fam, size, weight, slant, underline, over = _STANDARD, 9, NORMAL, ROMAN, 0, 0
        self._opt = {"family": opt.get("family", fam), "size": int(opt.get("size", size)),
                     "weight": opt.get("weight", weight), "slant": opt.get("slant", slant),
                     "underline": int(bool(opt.get("underline", underline))),
                     "overstrike": int(bool(opt.get("overstrike", over)))}
        if name is None:
            Font._kt_zaehler += 1
            name = f"font{Font._kt_zaehler}"
        self.name = name
        if name not in _benannt or not exists:
            _benannt[name] = self

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, Font) and other._opt == self._opt

    def __hash__(self):
        return hash(self.name)

    def actual(self, option=None, displayof=None):
        return self._opt[option] if option else dict(self._opt)

    def cget(self, option):
        return self._opt[option]

    def configure(self, **opt):
        if not opt:
            return dict(self._opt)
        self._opt.update(opt)
        if "size" in opt:
            self._opt["size"] = int(opt["size"])
        _base.alles_neu()                      # widgets using it get re-laid out

    config = configure

    def copy(self):
        return Font(**self._opt)

    def measure(self, text, displayof=None):
        return text_breite(str(text), self)

    def metrics(self, *options, **kw):
        a, d = _metrik(self)
        m = {"ascent": a, "descent": d, "linespace": a + d, "fixed": 0}
        if options:
            return m[options[0]] if len(options) == 1 else tuple(m[o] for o in options)
        return m

    def __getitem__(self, k):
        return self._opt[k]

    def __setitem__(self, k, v):
        self.configure(**{k: v})

    # -- key for the caches
    def _kt_schluessel(self):
        o = self._opt
        return (o["family"], pixel(o["size"]), o["weight"] == BOLD, o["slant"] == ITALIC,
                bool(o["underline"]))


def _parse(spec):
    """Tk font description -> (family, size, weight, slant, underline, overstrike)."""
    if isinstance(spec, Font):
        o = spec._opt
        return o["family"], o["size"], o["weight"], o["slant"], o["underline"], o["overstrike"]
    if isinstance(spec, str):
        if spec in _benannt:
            return _parse(_benannt[spec])
        if spec.startswith("{"):
            fam, _, rest = spec[1:].partition("}")
            teile = [fam] + rest.split()
        else:
            teile = spec.split()
            # "Segoe UI 9 bold": family may contain spaces -> up to the first number
            for i, t in enumerate(teile):
                if t.lstrip("-").isdigit():
                    teile = [" ".join(teile[:i])] + teile[i:]
                    break
            else:
                teile = [" ".join(teile)]
        spec = teile
    spec = list(spec) if spec else []
    fam = spec[0] if spec else _STANDARD
    size = 9
    if len(spec) > 1:
        try:
            size = int(float(spec[1]))
        except (TypeError, ValueError):
            pass
    weight, slant, ul, ov = NORMAL, ROMAN, 0, 0
    for t in spec[2:]:
        for w in str(t).split():
            if w == "bold":
                weight = BOLD
            elif w == "italic":
                slant = ITALIC
            elif w == "underline":
                ul = 1
            elif w == "overstrike":
                ov = 1
    return fam or _STANDARD, size, weight, slant, ul, ov


_schluessel_cache = {}


def schluessel(spec):
    """Font description -> (family, px, bold, italic, underline) (cached)."""
    if spec is None or spec == "":
        spec = "TkDefaultFont"
    if isinstance(spec, Font):
        return spec._kt_schluessel()
    try:
        return _schluessel_cache[spec]
    except (KeyError, TypeError):
        pass
    if isinstance(spec, str) and spec in _benannt:
        return _benannt[spec]._kt_schluessel()
    fam, size, weight, slant, ul, _ov = _parse(spec)
    k = (fam, pixel(size), weight == BOLD, slant == ITALIC, bool(ul))
    try:
        _schluessel_cache[spec] = k
    except TypeError:
        _schluessel_cache[tuple(spec)] = k
    return k


def _label(text, k):
    fam, px, fett, kursiv, ul = k
    return _CoreLabel(text=text, font_name=_kivy_name(fam), font_size=px, bold=fett,
                      italic=kursiv, underline=ul, padding=0, color=(1, 1, 1, 1))


_metrik_cache = {}


# Windows: text like Tk with GDI (ClearType); KATIECAD_KT_TEXT=sdl forces SDL_ttf
_GDI = None


def _gdi():
    global _GDI
    if _GDI is None:
        _GDI = False
        if sys.platform.startswith("win") and os.environ.get("KATIECAD_KT_TEXT", "").lower() != "sdl":
            try:
                from katiecad.ui.kt import gdi_text
                if gdi_text.metrik(("Segoe UI", 12, False, False, False))[0] > 0:
                    _GDI = gdi_text
            except Exception:
                _GDI = False
    return _GDI


def _metrik(spec):
    """Ascent and descent (pixels) of a font, as font.metrics() returns them under Tk. Windows:
    from GDI; otherwise from Kivy's line height, split 80 / 20 like Tk.
    """
    k = schluessel(spec)
    m = _metrik_cache.get(k)
    if m is None and _gdi():
        m = _gdi().metrik(k)
        _metrik_cache[k] = m
    if m is None:
        h = _label("Ãg", k).get_extents("Ãg")[1]
        # SDL2 reports the whole line height; split it like Tk (ascent ~ 80 %)
        a = int(round(h * 0.8))
        m = (a, h - a)
        _metrik_cache[k] = m
    return m


_breite_cache = {}


def text_breite(text, spec):
    """Width of `text` in pixels for the font spec (the longest line for several lines), the
    same value Tk's font.measure() gives. Cached, because layout asks for the same texts very
    often.
    """
    k = schluessel(spec)
    try:
        return _breite_cache[(text, k)]
    except KeyError:
        pass
    if not text:
        w = 0
    elif _gdi():
        w = max(_gdi().breite(z, k) for z in text.split("\n"))
    else:
        w = 0
        for z in text.split("\n"):
            w = max(w, sum(_label(t, kk).get_extents(t)[0] for t, kk in _laeufe(z, k)))
    if len(_breite_cache) > 20000:
        _breite_cache.clear()
    _breite_cache[(text, k)] = w
    return w


def zeilen_hoehe(spec):
    a, d = _metrik(spec)
    return a + d


_tex_cache = {}


def text_textur(text, spec):
    """White texture of a (single-line) text; None for empty text."""
    if not text:
        return None
    k = schluessel(spec)
    t = _tex_cache.get((text, k))
    if t is None:
        try:
            laeufe = None if _gdi() else _laeufe(text, k)
            if laeufe is None:
                t = _gdi_textur(text, k)
            elif len(laeufe) == 1:
                lb = _label(text, laeufe[0][1])
                lb.refresh()
                t = lb.texture
            else:
                t = _zusammensetzen(laeufe)
        except Exception:
            t = None
        if len(_tex_cache) > 6000:
            _tex_cache.clear()
        _tex_cache[(text, k)] = t
    return t


_fbos = []

# ------------------------------------------------------------
# Drawing a text texture. GDI textures carry ClearType coverage per sub pixel: they are
# drawn in two passes with per-channel blending  dst = dst * (1 - cov) + farbe * cov.
# ------------------------------------------------------------
_blend_alt = []


def _blend_text1(_instr=None):
    from kivy.graphics import opengl as gl
    if not _blend_alt:
        _blend_alt.extend((gl.glGetIntegerv(gl.GL_BLEND_SRC_RGB)[0], gl.glGetIntegerv(gl.GL_BLEND_DST_RGB)[0],
                           gl.glGetIntegerv(gl.GL_BLEND_SRC_ALPHA)[0], gl.glGetIntegerv(gl.GL_BLEND_DST_ALPHA)[0]))
    gl.glBlendFuncSeparate(gl.GL_ZERO, gl.GL_ONE_MINUS_SRC_COLOR, gl.GL_ZERO, gl.GL_ONE)


def _blend_text2(_instr=None):
    from kivy.graphics import opengl as gl
    gl.glBlendFuncSeparate(gl.GL_ONE, gl.GL_ONE, gl.GL_ZERO, gl.GL_ONE)


def _blend_zurueck(_instr=None):
    from kivy.graphics import opengl as gl
    if _blend_alt:
        gl.glBlendFuncSeparate(*_blend_alt)


def text_zeichnen(g, tex, farbe, pos, size, tex_coords=None):
    """Adds the instructions that draw text texture `tex` in colour `farbe` to group g."""
    from kivy.graphics import Color, Rectangle, Callback
    kw = {"texture": tex, "pos": pos, "size": size}
    if tex_coords is not None:
        kw["tex_coords"] = tex_coords
    if not _gdi():
        g.add(Color(*farbe))
        g.add(Rectangle(**kw))
        return
    r, gg, b = farbe[0], farbe[1], farbe[2]
    a = farbe[3] if len(farbe) > 3 else 1.0
    g.add(Callback(_blend_text1))
    g.add(Color(a, a, a, 1))
    g.add(Rectangle(**kw))
    g.add(Callback(_blend_text2))
    g.add(Color(r * a, gg * a, b * a, 1))
    g.add(Rectangle(**kw))
    g.add(Callback(_blend_zurueck))


def _gdi_textur(text, k):
    from kivy.graphics.texture import Texture
    erg = _gdi().rendern(text, k)
    if erg is None:
        return None
    w, h, daten = erg
    t = Texture.create(size=(w, h), colorfmt="rgba")
    t.blit_buffer(daten, colorfmt="rgba", bufferfmt="ubyte")
    t.flip_vertical()                     # like Kivy's label textures (rows top first)
    t.mag_filter = t.min_filter = "nearest"     # pixel exact, never smeared
    return t


def _zusammensetzen(laeufe):
    """Text from several fonts -> one texture (rendered side by side in an Fbo)."""
    from kivy.graphics import Fbo, Rectangle, ClearColor, ClearBuffers, Color
    texturen = []
    for t, kk in laeufe:
        lb = _label(t, kk)
        lb.refresh()
        texturen.append(lb.texture)
    breite = sum(t.size[0] for t in texturen if t is not None)
    hoehe = max((t.size[1] for t in texturen if t is not None), default=1)
    fbo = Fbo(size=(max(1, breite), max(1, hoehe)))
    with fbo:
        ClearColor(0, 0, 0, 0)
        ClearBuffers()
        Color(1, 1, 1, 1)
        x = 0
        for t in texturen:
            if t is None:
                continue
            Rectangle(texture=t, pos=(x, (hoehe - t.size[1]) // 2), size=t.size)
            x += t.size[0]
    fbo.draw()
    _fbos.append(fbo)
    if len(_fbos) > 500:
        del _fbos[:100]
    return fbo.texture


def umbrechen(text, spec, breite):
    """Splits text into lines of at most `breite` pixels (Tk wraplength / width)."""
    zeilen = []
    for absatz in str(text).split("\n"):
        if breite <= 0 or text_breite(absatz, spec) <= breite:
            zeilen.append(absatz)
            continue
        aktuell = ""
        for wort in absatz.split(" "):
            versuch = wort if not aktuell else aktuell + " " + wort
            if text_breite(versuch, spec) <= breite or not aktuell:
                aktuell = versuch
            else:
                zeilen.append(aktuell)
                aktuell = wort
        zeilen.append(aktuell)
    return zeilen


def nametofont(name, root=None):
    try:
        return _benannt[str(name)]
    except KeyError:
        from katiecad.ui.kt.tkmod import TclError
        raise TclError(f'named font "{name}" does not exist')


def names(root=None):
    return tuple(_benannt)


def _standard_fonts():
    for name, size, extra in (("TkDefaultFont", 9, {}), ("TkTextFont", 9, {}),
                              ("TkMenuFont", 9, {}), ("TkHeadingFont", 9, {"weight": BOLD}),
                              ("TkCaptionFont", 9, {}), ("TkSmallCaptionFont", 8, {}),
                              ("TkIconFont", 9, {}), ("TkTooltipFont", 8, {})):
        Font(name=name, family=_STANDARD, size=size, **extra)
    Font(name="TkFixedFont", family="Courier New" if sys.platform.startswith("win") else "DejaVu Sans Mono",
         size=10)


_standard_fonts()
