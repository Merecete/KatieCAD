# -*- coding: utf-8 -*-
"""
PyInstaller hook for the Kivy user interface (katiecad/ui/kt).

PyInstaller's own Kivy hook collects the Kivy modules and data; the native libraries of
Kivy on Windows (SDL2, GLEW, ANGLE from the kivy_deps packages) live outside the Python
packages and are added here, next to KatieCAD.exe. Without them the program starts with the
Tk interface (automatic fallback).

Used with:  pyinstaller --additional-hooks-dir installer/hooks ...
"""
import os

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("kivy.core") + [
    "kivy.core.window.window_sdl2", "kivy.core.text.text_sdl2", "kivy.core.image.img_sdl2",
    "kivy.core.clipboard.clipboard_winctypes", "kivy.core.clipboard.clipboard_sdl2",
    "kivy.graphics.tesselator", "fontTools.ttLib",
]

# Kivy's Roboto font is the last-resort font of the interface; without it the window stays empty
try:
    from PyInstaller.utils.hooks import collect_data_files
    datas = collect_data_files("kivy", includes=["data/fonts/*"])
except Exception:
    datas = []

binaries = []
try:
    import kivy_deps
    for name in ("sdl2", "glew", "angle"):
        try:
            mod = __import__("kivy_deps." + name, fromlist=["dep_bins"])
        except ImportError:
            continue
        for ordner in getattr(mod, "dep_bins", []):
            if not os.path.isdir(ordner):
                continue
            for datei in os.listdir(ordner):
                if datei.lower().endswith(".dll"):
                    binaries.append((os.path.join(ordner, datei), "."))
except ImportError:              # Linux / macOS: the Kivy wheel carries its libraries itself
    pass
