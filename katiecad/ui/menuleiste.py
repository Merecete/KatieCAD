# -*- coding: utf-8 -*-
"""
katiecad/ui/menuleiste.py - Own menu bar for Linux/X11 and Windows (BSD-3-Clause).

Why: the native Tk menu bar grabs mouse and keyboard. On X11/XWayland
(GNOME) this grab is not honoured: after switching to another application
the open menu stays on screen on top of the foreign window. This menu bar
has no grab; it simply closes when the window loses the focus or when the
user clicks elsewhere. On Windows it replaces the native bar, which is always
white and cannot follow the colour scheme.

The menus are still ordinary (never posted) tk.Menu objects used as data
model: this class only reads their entries (label, accelerator, state,
check marks) and calls `menu.invoke(index)`.
"""

import sys
import tkinter as tk
import tkinter.font as tkfont


class _Pop:
    """One drop-down (or sub-menu) window with its rows."""
    __slots__ = ("pop", "zeilen", "aktiv", "ebene", "anz", "cv", "ys")

    def __init__(self, pop, ebene):
        self.pop, self.zeilen, self.aktiv, self.ebene = pop, [], None, ebene
        self.cv, self.ys = None, []   # canvas; per row (y0, y1)
        self.anz = []      # per row: [bg, fg, mark] as currently shown (only changes are sent to Tk)


def menue_position(x, y, br, ho, bereich, links_von=None):
    """Position of a pop-up of size (br, ho) wanted at (x, y), kept inside the monitor area
    (left, top, right, bottom); a sub menu goes to the left of its parent (links_von) when
    there is no room on the right."""
    l, t, r, b = bereich
    if links_von is not None and x + br > r:
        x = links_von - br
    x = max(l, min(x, r - br))
    y = max(t, min(y, b - ho))
    return x, y


class MenuLeiste(tk.Frame):
    def __init__(self, parent, bg, fg, aktiv_bg, aktiv_fg, sperr_fg="#6b5c8a"):
        super().__init__(parent, bg=bg, bd=0, highlightthickness=0)
        self._bg, self._fg = bg, fg
        self._abg, self._afg = aktiv_bg, aktiv_fg
        self._sperr = sperr_fg
        self._eintraege = []           # [(label_widget, tk.Menu)]
        self._offen = None             # index of the open menu
        self._stapel = []              # open windows: [drop-down, sub-menu, sub-sub-menu ...]
        self._cache = {}               # index -> _Pop: built once
        self._subcache = {}            # str(tk.Menu) -> _Pop of a sub-menu
        try:
            self._font = tkfont.nametofont("TkMenuFont")
        except tk.TclError:
            self._font = tkfont.nametofont("TkDefaultFont")
        top = self.winfo_toplevel()
        top.bind("<FocusOut>", self._fokus_aus, add="+")
        top.bind("<Unmap>", lambda e: self.schliessen(), add="+")
        top.bind("<Configure>", self._fenster_bewegt, add="+")
        top.bind("<F10>", self._f10, add="+")
        top.bind_all("<ButtonPress>", self._klick, add="+")
        top.bind_all("<Key>", self._taste, add="+")

    # ------------------------------------------------------------
    def farben_setzen(self, bg, fg, aktiv_bg, aktiv_fg, sperr_fg=None):
        """New colours (colour scheme change); takes effect with the next setze()."""
        self._bg, self._fg, self._abg, self._afg = bg, fg, aktiv_bg, aktiv_fg
        if sperr_fg:
            self._sperr = sperr_fg
        self.config(bg=bg)

    def setze(self, eintraege):
        """eintraege: [(label, tk.Menu)] - rebuilds the bar."""
        self.schliessen()
        for w, _m in self._eintraege:
            w.destroy()
        for p in list(self._cache.values()) + list(self._subcache.values()):
            try:
                p.pop.destroy()
            except tk.TclError:
                pass
        self._cache = {}
        self._subcache = {}
        self._eintraege = []
        for i, (label, menu) in enumerate(eintraege):
            w = tk.Label(self, text=label, bg=self._bg, fg=self._fg,
                         font=self._font, padx=8, pady=3, bd=0)
            w.pack(side=tk.LEFT)
            w.bind("<Button-1>", lambda e, i=i: self._umschalten(i))
            w.bind("<Enter>", lambda e, i=i: self._ueber(i))
            self._eintraege.append((w, menu))
        self.after(200, self._vorbauen)

    def _vorbauen(self):
        """Builds all drop-downs once in the background (opening is then
        instant); they are only refreshed when opened."""
        for i in range(len(self._eintraege)):
            if i not in self._cache:
                try:
                    self._cache[i] = self._pop_bauen(self._eintraege[i][1], 0)
                except tk.TclError:
                    return
        # sub-menus too (building a window lazily on first hover is what felt slow)
        for i in range(len(self._eintraege)):
            if not self._sub_vorbauen(self._cache.get(i)):
                return

    def _sub_vorbauen(self, p, tiefe=0):
        """Builds the sub-menu windows below p (recursively). False on error."""
        if p is None or tiefe > 4:
            return True
        for _y, idx, _st, _w, menu in list(p.zeilen):
            try:
                if menu.type(idx) != "cascade":
                    continue
                ziel = self.nametowidget(menu.entrycget(idx, "menu"))
            except (tk.TclError, KeyError):
                continue
            k = str(ziel)
            try:
                if k not in self._subcache:
                    self._subcache[k] = self._pop_bauen(ziel, p.ebene + 1)
            except tk.TclError:
                return False
            if not self._sub_vorbauen(self._subcache[k], tiefe + 1):
                return False
        return True

    def _faerben(self):
        for i, (w, _m) in enumerate(self._eintraege):
            if i == self._offen:
                w.config(bg=self._abg, fg=self._afg)
            else:
                w.config(bg=self._bg, fg=self._fg)

    # ------------------------------------------------------------
    def _umschalten(self, i):
        if self._offen == i:
            self.schliessen()
        else:
            self.oeffnen(i)

    def _ueber(self, i):
        if self._offen is not None and self._offen != i:
            self.oeffnen(i)

    def oeffnen(self, i, tastatur=False):
        self._stapel_schliessen(0)
        self._offen = i
        self._faerben()
        w, menu = self._eintraege[i]
        if i not in self._cache:
            self._cache[i] = self._pop_bauen(menu, 0)
        p = self._cache[i]
        self._markierung_loeschen(p)
        self._auffrischen(p)
        self._anzeigen(p, w.winfo_rootx(), w.winfo_rooty() + w.winfo_height())
        self._stapel = [p]
        if tastatur:
            self._weiter(+1)

    def _anzeigen(self, p, x, y, links_von=None):
        """Shows window p at (x, y); stays on the screen. links_von = x where the window
        goes to the left of its parent if there is no room on the right."""
        br, ho = p.pop.winfo_reqwidth(), p.pop.winfo_reqheight()
        x, y = menue_position(x, y, br, ho, self._monitor_rechteck(x, y), links_von)
        p.pop.geometry("+%d+%d" % (x, y))
        p.pop.update_idletasks()          # lay out first, so that no empty window flashes up
        p.pop.deiconify()
        p.pop.lift()

    def _monitor_rechteck(self, x, y):
        """Work area (left, top, right, bottom) of the monitor that contains the point (x, y).
        Windows: the real monitor (so the menu stays on the monitor of the window when
        there are several); elsewhere the whole virtual screen."""
        if sys.platform.startswith("win"):
            try:
                import ctypes
                from ctypes import wintypes

                class _MI(ctypes.Structure):
                    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]
                u32 = ctypes.windll.user32
                u32.MonitorFromPoint.restype = wintypes.HANDLE
                u32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
                u32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_MI)]
                hm = u32.MonitorFromPoint(wintypes.POINT(int(x), int(y)), 2)   # NEAREST
                mi = _MI()
                mi.cbSize = ctypes.sizeof(_MI)
                if hm and u32.GetMonitorInfoW(hm, ctypes.byref(mi)):
                    r = mi.rcWork
                    return (r.left, r.top, r.right, r.bottom)
            except Exception:
                pass
        try:
            vx, vy = self.winfo_vrootx(), self.winfo_vrooty()
            vw, vh = self.winfo_vrootwidth(), self.winfo_vrootheight()
            if vw > 0 and vh > 0:
                return (vx, vy, vx + vw, vy + vh)
        except tk.TclError:
            pass
        return (0, 0, self.winfo_screenwidth(), self.winfo_screenheight())

    def _lesen(self, menu, idx):
        """(type, text, accelerator, state, check mark) of a menu entry."""
        typ = menu.type(idx)
        try:
            text = menu.entrycget(idx, "label")
        except tk.TclError:
            text = ""
        try:
            accel = menu.entrycget(idx, "accelerator")
        except tk.TclError:
            accel = ""
        try:
            state = menu.entrycget(idx, "state")
        except tk.TclError:
            state = "normal"
        marke = ""
        if typ in ("checkbutton", "radiobutton"):
            try:
                var = menu.entrycget(idx, "variable")
                wert = menu.tk.globalgetvar(str(var))
                soll = menu.entrycget(idx, "onvalue" if typ == "checkbutton"
                                      else "value")
                if str(wert) == str(soll):
                    marke = "\u2713"
            except tk.TclError:
                pass
        if typ == "cascade":
            accel = accel + "  \u25b8"
        return typ, text, accel, state, marke

    def _pop_bauen(self, menu, ebene):
        """One window with ONE canvas (instead of ~4 widgets per row): on X11/XWayland every
        widget is a window of its own, which made opening slow."""
        pop = tk.Toplevel(self)
        pop.withdraw()
        pop.overrideredirect(True)
        try:
            pop.attributes("-topmost", True)
        except tk.TclError:
            pass
        rahmen = tk.Frame(pop, bg=self._fg, bd=0)
        rahmen.pack(fill=tk.BOTH, expand=True)
        p = _Pop(pop, ebene)
        try:
            ende = menu.index("end")
        except tk.TclError:
            ende = None
        eintraege = []
        if ende is not None:
            for idx in range(ende + 1):
                typ, text, accel, state, marke = self._lesen(menu, idx)
                if typ != "tearoff":
                    eintraege.append((typ, idx, text, accel, state, marke))
        f = self._font
        zh = f.metrics("linespace") + 6                  # row height (3 px above/below)
        markb = 2 * f.measure("0")
        textb = max([f.measure(e[2]) for e in eintraege if e[0] != "separator"] or [0])
        accb = max([f.measure(e[3]) for e in eintraege if e[0] != "separator"] or [0])
        br = markb + 2 + textb + 24 + accb + 10
        ho = sum(7 if e[0] == "separator" else zh for e in eintraege)
        cv = tk.Canvas(rahmen, width=br, height=max(ho, 1), bg=self._bg, bd=0,
                       highlightthickness=0, relief="flat", takefocus=0)
        cv.pack(padx=1, pady=1)
        p.cv = cv
        y = 0
        for typ, idx, text, accel, state, marke in eintraege:
            if typ == "separator":
                cv.create_line(2, y + 3, br - 2, y + 3, fill=self._fg)
                y += 7
                continue
            fg = self._fg if state != "disabled" else self._sperr
            yz = y + zh // 2
            r = cv.create_rectangle(0, y, br, y + zh, fill=self._bg, outline="")
            t1 = cv.create_text(0, yz, text=marke, anchor="w", fill=fg, font=f)
            t2 = cv.create_text(markb + 2, yz, text=text, anchor="w", fill=fg, font=f)
            t3 = cv.create_text(br - 10, yz, text=accel, anchor="e", fill=fg, font=f)
            p.zeilen.append((y, idx, state, (r, t1, t2, t3), menu))
            p.ys.append((y, y + zh))
            p.anz.append([self._bg, fg, marke])
            y += zh
        cv.bind("<Motion>", lambda e, p=p: self._maus(p, e.y))
        cv.bind("<Enter>", lambda e, p=p: self._maus(p, e.y))
        cv.bind("<ButtonRelease-1>", lambda e, p=p: self._ausloesen(p, self._zeile_bei(p, e.y)))
        pop.update_idletasks()
        return p

    @staticmethod
    def _zeile_bei(p, y):
        for nr, (y0, y1) in enumerate(p.ys):
            if y0 <= y < y1:
                return nr
        return None

    def _maus(self, p, y):
        nr = self._zeile_bei(p, y)
        if nr is not None and nr != p.aktiv:
            self._markieren(p, nr)

    def _auffrischen(self, p):
        """Takes over state and check marks of the menu entries."""
        for nr, z in enumerate(p.zeilen):
            y0, idx, _alt, ids, menu = z
            _t, _text, _acc, state, marke = self._lesen(menu, idx)
            fg = self._fg if state != "disabled" else self._sperr
            self._zeile_faerben(p, nr, self._bg, fg, marke)
            p.zeilen[nr] = (y0, idx, state, ids, menu)

    def _zeile_faerben(self, p, nr, bg, fg, marke=None):
        """Sets colours (and check mark) of a row; Tk is only touched when something changed."""
        r, t1, t2, t3 = p.zeilen[nr][3]
        alt = p.anz[nr]
        if alt[0] != bg:
            p.cv.itemconfigure(r, fill=bg)
        if alt[1] != fg:
            for t in (t1, t2, t3):
                p.cv.itemconfigure(t, fill=fg)
        if marke is not None and alt[2] != marke:
            p.cv.itemconfigure(t1, text=marke)
        p.anz[nr] = [bg, fg, marke if marke is not None else alt[2]]

    def _markierung_loeschen(self, p):
        """Removes the highlight (when opening again)."""
        if p.aktiv is not None and p.aktiv < len(p.zeilen):
            z = p.zeilen[p.aktiv]
            fg = self._fg if z[2] != "disabled" else self._sperr
            self._zeile_faerben(p, p.aktiv, self._bg, fg)
        p.aktiv = None

    def _markieren(self, p, nr, mit_untermenue=True):
        if p.aktiv is not None and p.aktiv < len(p.zeilen):
            z = p.zeilen[p.aktiv]
            fg = self._fg if z[2] != "disabled" else self._sperr
            self._zeile_faerben(p, p.aktiv, self._bg, fg)
        p.aktiv = nr
        if nr is None:
            return
        z = p.zeilen[nr]
        if z[2] == "disabled":
            self._stapel_schliessen(p.ebene + 1)
            return
        self._zeile_faerben(p, nr, self._abg, self._afg)
        if mit_untermenue and self._ist_cascade(z):
            self._sub_oeffnen(p, nr)
        else:
            self._stapel_schliessen(p.ebene + 1)

    @staticmethod
    def _ist_cascade(z):
        try:
            return z[4].type(z[1]) == "cascade"
        except tk.TclError:
            return False

    def _sub_oeffnen(self, p, nr):
        """Opens the sub-menu of row nr of window p (to the right of the row)."""
        y0, idx, _st, _w, menu = p.zeilen[nr]
        try:
            ziel = self.nametowidget(menu.entrycget(idx, "menu"))
        except (tk.TclError, KeyError):
            return
        schluessel = str(ziel)
        if (len(self._stapel) > p.ebene + 1
                and self._stapel[p.ebene + 1] is self._subcache.get(schluessel)):
            return                                   # already open
        self._stapel_schliessen(p.ebene + 1)
        sub = self._subcache.get(schluessel)
        if sub is None:
            sub = self._subcache[schluessel] = self._pop_bauen(ziel, p.ebene + 1)
        sub.ebene = p.ebene + 1
        self._markierung_loeschen(sub)
        self._auffrischen(sub)
        px = p.pop.winfo_rootx()
        self._anzeigen(sub, px + p.pop.winfo_width() - 2, p.cv.winfo_rooty() + y0 - 2,
                       links_von=px + 2)
        del self._stapel[p.ebene + 1:]
        self._stapel.append(sub)

    def _stapel_schliessen(self, ab):
        """Closes the sub-menus from level `ab` on (0 = everything)."""
        for p in self._stapel[ab:]:
            try:
                p.pop.withdraw()
            except tk.TclError:
                pass
        del self._stapel[ab:]

    def _ausloesen(self, p, nr):
        if nr is None or nr >= len(p.zeilen):
            return
        z = p.zeilen[nr]
        _z, idx, state, _w, menu = z
        if state == "disabled":
            return
        if self._ist_cascade(z):                     # a click opens the sub-menu
            self._markieren(p, nr)
            return
        self.schliessen()
        # after closing, so that dialogs are not blocked by the pop-up
        self.after(10, lambda: self._aufrufen(menu, idx))

    @staticmethod
    def _aufrufen(menu, idx):
        try:
            menu.invoke(idx)
        except tk.TclError:
            pass

    # ------------------------------------------------------------
    def schliessen(self):
        self._stapel_schliessen(0)
        if self._offen is not None:
            self._offen = None
            self._faerben()

    def ist_offen(self):
        return self._offen is not None

    # ------------------------------------------------------------
    def _fokus_aus(self, event):
        if self._offen is None or event.widget is not self.winfo_toplevel():
            return
        # focus moves within the application? Then it is not "away".
        self.after(80, self._fokus_pruefen)

    def _fokus_pruefen(self):
        try:
            if self.winfo_toplevel().focus_displayof() is None:
                self.schliessen()
        except tk.TclError:
            pass

    def _fenster_bewegt(self, event):
        if self._offen is None or event.widget is not self.winfo_toplevel():
            return
        self.schliessen()

    def _klick(self, event):
        if self._offen is None:
            return
        w = event.widget
        fenster = {id(p.pop) for p in self._stapel}
        try:
            while w is not None:
                if w is self or id(w) in fenster:
                    return
                w = w.master
        except Exception:
            return
        self.schliessen()

    def _f10(self, event=None):
        if self._eintraege and self._offen is None:
            self.oeffnen(0, tastatur=True)
            return "break"

    def _weiter(self, richtung):
        if not self._stapel:
            return
        p = self._stapel[-1]
        n = len(p.zeilen)
        if not n:
            return
        nr = p.aktiv
        for _ in range(n):
            if nr is None:
                nr = 0 if richtung > 0 else n - 1
            else:
                nr = (nr + richtung) % n
            if p.zeilen[nr][2] != "disabled":
                self._markieren(p, nr, mit_untermenue=False)
                return

    def _taste(self, event):
        if self._offen is None or not self._stapel:
            return
        k = event.keysym
        p = self._stapel[-1]
        if k == "Escape":
            if len(self._stapel) > 1:
                self._stapel_schliessen(len(self._stapel) - 1)
            else:
                self.schliessen()
        elif k == "Down":
            self._weiter(+1)
        elif k == "Up":
            self._weiter(-1)
        elif k == "Right":
            z = p.zeilen[p.aktiv] if p.aktiv is not None and p.aktiv < len(p.zeilen) else None
            if z is not None and z[2] != "disabled" and self._ist_cascade(z):
                self._sub_oeffnen(p, p.aktiv)
                if len(self._stapel) > p.ebene + 1:
                    self._weiter(+1)
            elif len(self._stapel) == 1:
                self.oeffnen((self._offen + 1) % len(self._eintraege), tastatur=True)
        elif k == "Left":
            if len(self._stapel) > 1:
                self._stapel_schliessen(len(self._stapel) - 1)
            else:
                self.oeffnen((self._offen - 1) % len(self._eintraege), tastatur=True)
        elif k in ("Return", "KP_Enter"):
            if p.aktiv is not None:
                z = p.zeilen[p.aktiv]
                if self._ist_cascade(z) and z[2] != "disabled":
                    self._sub_oeffnen(p, p.aktiv)
                    if len(self._stapel) > p.ebene + 1:
                        self._weiter(+1)
                else:
                    self._ausloesen(p, p.aktiv)
        else:
            return
        return "break"
