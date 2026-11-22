# -*- coding: utf-8 -*-
"""
katiecad/ui/kt/macmenu.py - macOS: the "About KatieCAD" entry of the application menu opens
KatieCAD's own info window instead of the standard Cocoa panel (BSD-3-Clause).

SDL creates the application menu; its first entry calls orderFrontStandardAboutPanel:. Without
extra packages (no pyobjc) the entry is redirected through the Objective-C runtime (ctypes) to a
small target object that calls `funktion` in the Kivy main loop. Does nothing (and never raises)
on other systems or when anything is different than expected.
"""

import ctypes
import ctypes.util
import sys

_gehalten = []                    # keeps the callback / target alive


def ueber_umleiten(funktion):
    """True when the entry was redirected."""
    if sys.platform != "darwin" or _gehalten:
        return bool(_gehalten)
    try:
        objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc") or "/usr/lib/libobjc.A.dylib")
        ctypes.cdll.LoadLibrary("/System/Library/Frameworks/AppKit.framework/AppKit")
        vp, ul = ctypes.c_void_p, ctypes.c_ulong
        objc.objc_getClass.restype = vp
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = vp
        objc.sel_registerName.argtypes = [ctypes.c_char_p]
        objc.objc_allocateClassPair.restype = vp
        objc.objc_allocateClassPair.argtypes = [vp, ctypes.c_char_p, ctypes.c_size_t]
        objc.class_addMethod.restype = ctypes.c_bool
        objc.class_addMethod.argtypes = [vp, vp, vp, ctypes.c_char_p]
        objc.objc_registerClassPair.argtypes = [vp]
        senden = ctypes.cast(objc.objc_msgSend, ctypes.c_void_p).value

        def msg(restype, *argtypes):
            return ctypes.CFUNCTYPE(restype, vp, vp, *argtypes)(senden)

        sel = lambda n: objc.sel_registerName(n)                       # noqa: E731
        m0 = msg(vp)
        m_idx = msg(vp, ul)
        m_vp = msg(None, vp)

        app = m0(objc.objc_getClass(b"NSApplication"), sel(b"sharedApplication"))
        menue = m0(app, sel(b"mainMenu"))
        if not menue:
            return False
        eintrag0 = m_idx(menue, sel(b"itemAtIndex:"), 0)
        untermenue = m0(eintrag0, sel(b"submenu"))
        about = m_idx(untermenue, sel(b"itemAtIndex:"), 0)
        if not about:
            return False
        aktion = m0(about, sel(b"action"))
        if aktion != sel(b"orderFrontStandardAboutPanel:"):
            return False                      # not the entry we expect: leave it alone

        def _aufruf(selbst, _cmd, sender):
            try:
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: funktion(), 0)
            except Exception as ex:
                print(f"[KatieCAD] Info-Menue: {ex}")

        imp_typ = ctypes.CFUNCTYPE(None, vp, vp, vp)
        imp = imp_typ(_aufruf)
        klasse = objc.objc_allocateClassPair(objc.objc_getClass(b"NSObject"), b"KatieCADInfoZiel", 0)
        if not klasse:
            return False
        objc.class_addMethod(klasse, sel(b"ueber:"), ctypes.cast(imp, vp), b"v@:@")
        objc.objc_registerClassPair(klasse)
        ziel = m0(m0(klasse, sel(b"alloc")), sel(b"init"))
        m_vp(about, sel(b"setTarget:"), ziel)
        m_vp(about, sel(b"setAction:"), sel(b"ueber:"))
        _gehalten.extend([imp, ziel, klasse])
        return True
    except Exception as ex:
        print(f"[KatieCAD] Info-Menue nicht umgeleitet: {ex}")
        return False
