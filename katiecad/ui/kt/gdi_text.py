# -*- coding: utf-8 -*-
"""
katiecad/ui/kt/gdi_text.py - text rendering with Windows GDI (BSD-3-Clause).

Tk draws its text on Windows with GDI (ClearType). SDL_ttf/FreeType renders the same font
noticeably thinner and softer, which on the dark colour scheme makes small text hard to read.
Here the text is rendered by GDI exactly like Tk does - same glyph shapes, same widths
(GetTextExtentPoint32 is what Tk's font measure uses). GDI falls back to other fonts for
missing characters (⋮ ☰ ▸ ✓) by itself.

The ClearType result keeps its coverage per sub pixel (RGB); fontmod.text_zeichnen blends
it per colour channel like GDI does, so the text is as crisp as under Tk.
"""

import ctypes
import sys
from ctypes import wintypes

VERFUEGBAR = sys.platform.startswith("win")

if VERFUEGBAR:
    _gdi = ctypes.windll.gdi32
    _user = ctypes.windll.user32

    class _BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                    ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                    ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                    ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                    ("biClrImportant", wintypes.DWORD)]

    class _SIZE(ctypes.Structure):
        _fields_ = [("cx", wintypes.LONG), ("cy", wintypes.LONG)]

    class _TEXTMETRICW(ctypes.Structure):
        _fields_ = [("tmHeight", wintypes.LONG), ("tmAscent", wintypes.LONG),
                    ("tmDescent", wintypes.LONG), ("tmInternalLeading", wintypes.LONG),
                    ("tmExternalLeading", wintypes.LONG), ("tmAveCharWidth", wintypes.LONG),
                    ("tmMaxCharWidth", wintypes.LONG), ("tmWeight", wintypes.LONG),
                    ("tmOverhang", wintypes.LONG), ("tmDigitizedAspectX", wintypes.LONG),
                    ("tmDigitizedAspectY", wintypes.LONG), ("tmFirstChar", wintypes.WCHAR),
                    ("tmLastChar", wintypes.WCHAR), ("tmDefaultChar", wintypes.WCHAR),
                    ("tmBreakChar", wintypes.WCHAR), ("tmItalic", ctypes.c_byte),
                    ("tmUnderlined", ctypes.c_byte), ("tmStruckOut", ctypes.c_byte),
                    ("tmPitchAndFamily", ctypes.c_byte), ("tmCharSet", ctypes.c_byte)]

    _gdi.CreateFontW.restype = wintypes.HANDLE
    _gdi.CreateFontW.argtypes = [ctypes.c_int] * 5 + [wintypes.DWORD] * 8 + [wintypes.LPCWSTR]
    _gdi.CreateCompatibleDC.restype = wintypes.HDC
    _gdi.CreateCompatibleDC.argtypes = [wintypes.HDC]
    _gdi.SelectObject.restype = wintypes.HANDLE
    _gdi.SelectObject.argtypes = [wintypes.HDC, wintypes.HANDLE]
    _gdi.CreateDIBSection.restype = wintypes.HANDLE
    _gdi.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.c_void_p, wintypes.UINT,
                                      ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE,
                                      wintypes.DWORD]
    _gdi.DeleteObject.argtypes = [wintypes.HANDLE]
    _gdi.GetTextExtentPoint32W.argtypes = [wintypes.HDC, wintypes.LPCWSTR, ctypes.c_int,
                                           ctypes.POINTER(_SIZE)]
    _gdi.TextOutW.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.LPCWSTR,
                              ctypes.c_int]
    _gdi.GetTextMetricsW.argtypes = [wintypes.HDC, ctypes.POINTER(_TEXTMETRICW)]
    _gdi.SetTextColor.argtypes = [wintypes.HDC, wintypes.DWORD]
    _gdi.SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]

    _CLEARTYPE_QUALITY = 5
    _dc = None
    _fonts = {}


def _dc_holen():
    global _dc
    if _dc is None:
        _dc = _gdi.CreateCompatibleDC(None)
        _gdi.SetBkMode(_dc, 1)                     # TRANSPARENT
        _gdi.SetTextColor(_dc, 0x00FFFFFF)
    return _dc


def _font(key):
    """key = (family, px, bold, italic, underline) -> HFONT (like Tk: height = -px)."""
    f = _fonts.get(key)
    if f is None:
        fam, px, fett, kursiv, ul = key
        f = _gdi.CreateFontW(-int(px), 0, 0, 0, 700 if fett else 400, 1 if kursiv else 0,
                             1 if ul else 0, 0, 1, 0, 0, _CLEARTYPE_QUALITY, 0, fam)
        _fonts[key] = f
    return f


def metrik(key):
    """-> (ascent, descent) like Tk's font metrics."""
    dc = _dc_holen()
    _gdi.SelectObject(dc, _font(key))
    tm = _TEXTMETRICW()
    _gdi.GetTextMetricsW(dc, ctypes.byref(tm))
    return tm.tmAscent, tm.tmDescent


def breite(text, key):
    if not text:
        return 0
    dc = _dc_holen()
    _gdi.SelectObject(dc, _font(key))
    s = _SIZE()
    _gdi.GetTextExtentPoint32W(dc, text, len(text), ctypes.byref(s))
    return s.cx


def rendern(text, key):
    """-> (width, height, RGBA bytes top row first): white text, alpha = coverage."""
    dc = _dc_holen()
    _gdi.SelectObject(dc, _font(key))
    a, d = metrik(key)
    w = max(1, breite(text, key) + (2 if key[3] else 0))       # italic overhang
    h = max(1, a + d)
    bih = _BITMAPINFOHEADER()
    bih.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
    bih.biWidth, bih.biHeight = w, -h                          # top-down
    bih.biPlanes, bih.biBitCount = 1, 32
    bits = ctypes.c_void_p()
    bmp = _gdi.CreateDIBSection(dc, ctypes.byref(bih), 0, ctypes.byref(bits), None, 0)
    if not bmp:
        return None
    alt = _gdi.SelectObject(dc, bmp)
    try:
        ctypes.memset(bits, 0, w * h * 4)
        _gdi.TextOutW(dc, 0, 0, text, len(text))
        roh = ctypes.string_at(bits, w * h * 4)                # BGRA, coverage per sub pixel
    finally:
        _gdi.SelectObject(dc, alt)
        _gdi.DeleteObject(bmp)
    # ClearType: one coverage value per sub pixel (R, G, B) - blended per channel when drawn
    # (fontmod.text_zeichnen), alpha = strongest sub pixel
    try:
        import numpy as np
        b = np.frombuffer(roh, dtype=np.uint8).reshape(h, w, 4)
        out = np.empty((h, w, 4), dtype=np.uint8)
        out[:, :, 0] = b[:, :, 2]
        out[:, :, 1] = b[:, :, 1]
        out[:, :, 2] = b[:, :, 0]
        out[:, :, 3] = b[:, :, :3].max(axis=2)
        daten = out.tobytes()
    except ImportError:
        daten = bytearray(w * h * 4)
        for i in range(w * h):
            bb, gg, rr = roh[4 * i], roh[4 * i + 1], roh[4 * i + 2]
            daten[4 * i:4 * i + 4] = bytes((rr, gg, bb, max(rr, gg, bb)))
        daten = bytes(daten)
    return w, h, daten
