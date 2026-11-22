# -*- coding: utf-8 -*-
"""
katiecad/ui/kt - a Tkinter-compatible layer on Kivy (BSD-3-Clause).

KatieCAD's user interface is written against the tkinter API. `installieren()` puts this
layer in place of tkinter (sys.modules), so the same program code runs with Kivy/OpenGL
drawing. The environment variable KATIECAD_UI=tk keeps the original Tk interface.

    python main.py                 -> Kivy
    KATIECAD_UI=tk python main.py  -> Tk (as before)
"""

import os
import sys

_installiert = [False]


def gewuenscht():
    """Which interface: "kivy" (default) or "tk"."""
    return "tk" if os.environ.get("KATIECAD_UI", "").strip().lower() in ("tk", "tkinter") else "kivy"


def oberflaeche_waehlen():
    """Called by the start scripts before the user interface is imported. Without a usable
    Kivy (not installed, no OpenGL window) KatieCAD falls back to the Tk interface."""
    if gewuenscht() == "kivy":
        try:
            installieren()
        except BaseException as e:            # also SystemExit from Kivy's window search
            print(f"[KatieCAD] Kivy nicht verfuegbar ({e!r}) - Tk-Oberflaeche wird verwendet.")


def _kivy_vorbereiten():
    """Kivy settings that must be made before the Kivy window exists: no command line parsing and
    no log files of Kivy, plain mouse input (no touch emulation, no red dots on right click),
    Escape does not quit, the window size of the Tk version, at most 60 frames per second and -
    unless KATIECAD_TITELLEISTE=system - the own title bar.
    """
    os.environ.setdefault("KIVY_NO_ARGS", "1")            # the file argument is ours
    os.environ.setdefault("KIVY_NO_FILELOG", "1")
    os.environ.setdefault("KIVY_LOG_MODE", "PYTHON")
    if "KIVY_NO_CONSOLELOG" not in os.environ and not os.environ.get("KATIECAD_KIVY_LOG"):
        os.environ["KIVY_NO_CONSOLELOG"] = "1"
    from kivy.config import Config
    Config.set("input", "mouse", "mouse,disable_multitouch")   # right click: no red dots
    Config.set("kivy", "exit_on_escape", "0")
    Config.set("kivy", "desktop", "1")
    Config.set("graphics", "width", "1500")
    Config.set("graphics", "height", "950")
    Config.set("graphics", "resizable", "1")
    Config.set("graphics", "multisamples", "0")
    Config.set("graphics", "maxfps", "60")
    # own title bar (titelleiste.py) - must be set before the window exists, so the module
    # (which needs the window) is not imported here
    if os.environ.get("KATIECAD_TITELLEISTE", "").strip().lower() != "system":
        Config.set("graphics", "custom_titlebar", "1")
    Config.set("kivy", "keyboard_mode", "system")
    for k in list(Config.options("input")):
        if k != "mouse":
            Config.remove_option("input", k)                 # no touch providers (wm_touch ...)


# Kivy versions the layer was written and tested for: (minimum, first version NOT tested).
KIVY_GETESTET = ((2, 3, 0), (3, 0, 0))


def _kivy_version_pruefen():
    """Warns in the log when the installed Kivy is outside the tested range. The layer replaces
    tkinter and relies on Kivy details, so a new major version may break it silently."""
    try:
        import kivy
        teile = []
        for t in kivy.__version__.replace("-", ".").split(".")[:3]:
            digits = "".join(c for c in t if c.isdigit())
            teile.append(int(digits) if digits else 0)
        v = tuple(teile + [0] * (3 - len(teile)))
        lo, hi = KIVY_GETESTET
        if not (lo <= v < hi):
            print(f"[KatieCAD] Warnung: Kivy {kivy.__version__} liegt ausserhalb des getesteten "
                  f"Bereichs {'.'.join(map(str, lo))} bis <{'.'.join(map(str, hi))}. "
                  f"Bei Problemen: KATIECAD_UI=tk startet die Tk-Oberflaeche.")
    except Exception as e:                      # never block the start because of this check
        print(f"[KatieCAD] Kivy-Version nicht pruefbar: {e!r}")



def installieren():
    """Puts the layer in place of tkinter: imports the real tkinter first (the native file and
    colour dialogs still need it, see dlgmod.py), opens the Kivy window (raises if that is not
    possible - the caller then stays with Tk) and replaces tkinter, tkinter.ttk, tkinter.font,
    the dialog modules and PIL.ImageTk in sys.modules by the modules of this layer. Runs once.
    """
    if _installiert[0]:
        return
    # the real tkinter is still needed for the native file and colour dialogs
    import tkinter as _tk                    # noqa: F401
    import tkinter.filedialog                # noqa: F401
    import tkinter.colorchooser              # noqa: F401
    import tkinter.messagebox                # noqa: F401
    echte = {k: v for k, v in sys.modules.items() if k == "tkinter" or k.startswith("tkinter.")}
    _kivy_vorbereiten()
    from kivy.core.window import Window      # raises/exits without a usable window provider
    if Window is None:
        raise RuntimeError("no Kivy window")
    for k in echte:
        del sys.modules[k]
    from katiecad.ui.kt import tkmod, ttkmod, fontmod, dlgmod
    dlgmod.ECHT.update(echte)
    module = {"tkinter": tkmod, "tkinter.ttk": ttkmod, "tkinter.font": fontmod,
              "tkinter.filedialog": dlgmod.filedialog, "tkinter.colorchooser": dlgmod.colorchooser,
              "tkinter.messagebox": dlgmod.messagebox, "tkinter.simpledialog": dlgmod.simpledialog,
              "tkinter.constants": tkmod}
    for name, m in module.items():
        sys.modules[name] = m
        if "." in name:
            setattr(tkmod, name.split(".", 1)[1], m)
    # PIL.ImageTk -> PhotoImage of this layer
    try:
        import PIL
        import types
        it = types.ModuleType("PIL.ImageTk")
        it.PhotoImage = lambda image=None, size=None, **kw: tkmod.PhotoImage._kt_aus_pil(image)
        it.BitmapImage = it.PhotoImage
        sys.modules["PIL.ImageTk"] = it
        PIL.ImageTk = it
    except ImportError:
        pass
    _kivy_version_pruefen()
    _installiert[0] = True
