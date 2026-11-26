# -*- coding: utf-8 -*-
"""
katiecad/ui/toolbar_dock.py - Dockable symbol toolbar (mixin of CadApp, BSD-3-Clause).

There is one symbol toolbar per department (tools, electrical, 3D). Each can
sit on top, at the bottom or at the right edge of the window, independently
of the others. Drag the grip at the start of a bar towards an edge and
release - it snaps there - or choose View > Toolbars. At the right edge the
symbols wrap into several columns. The choices are stored in the configuration.
"""

import sys
import tkinter as tk
from tkinter import ttk

from katiecad.common.i18n import tr
from katiecad.model.core import FARBEN

from katiecad.common.config import lade_konfiguration, speichere_konfiguration

POSITIONEN = ("oben", "unten", "links", "rechts")
VERTIKAL = ("links", "rechts")                           # areas where the symbols wrap into columns
# real Tk on the Mac: right button = 2; the Kivy layer sends 3 on every system
BTN_RECHTS = "2" if (sys.platform == "darwin" and not tk.__name__.startswith("katiecad.ui.kt")) else "3"
ZELLE_PX = 36                 # height of one symbol row at the right edge


def ziel_position(relx, rely, aktuell="oben", links=0.12):
    """Docking edge for a pointer position inside the window (0..1). `links`: right edge of the
    left drop area (the project sidebar plus a margin) as a fraction of the window width; it
    reaches from just below the toolbars to just above the status bar."""
    if relx > 0.85:
        return "rechts"
    if relx < links and 0.15 <= rely <= 0.88:
        return "links"
    if rely > 0.78:
        return "unten"
    if rely < 0.22:
        return "oben"
    return aktuell


def spalten_zeilen(anzahl, hoehe_px):
    """Rows per column for the right-hand toolbar."""
    return max(6, min(anzahl, int(hoehe_px // ZELLE_PX)))


LEISTEN = ("werkzeug", "bau", "elektro", "3d")            # order inside a docking area
LEISTEN_ATTR = {"werkzeug": "tb1", "bau": "tbB", "elektro": "tbE", "3d": "tbD"}
CONFIG_KEY = {"werkzeug": "toolbar_pos", "bau": "toolbar_pos_bau", "elektro": "toolbar_pos_elektro",
              "3d": "toolbar_pos_3d"}


class ToolbarDockMixin:
    _tb_pos_werte = None
    _tb_info = None
    _tb_resize_id = None
    _tb_zonen = None

    # ---- order inside a docking area ------------------------------------
    def toolbar_reihenfolge(self):
        if getattr(self, "_tb_reihe", None) is None:
            try:
                r = lade_konfiguration().get("toolbar_reihenfolge")
            except Exception:
                r = None
            if isinstance(r, list) and all(n in LEISTEN for n in r) and len(set(r)) == len(r):
                r = list(r)
                for n in LEISTEN:                      # bars added in later versions: at their default place
                    if n not in r:
                        r.insert(min(LEISTEN.index(n), len(r)), n)
                self._tb_reihe = r
            else:
                self._tb_reihe = list(LEISTEN)
        return self._tb_reihe

    def toolbar_verschieben(self, name, schritt):
        """Moves a bar one place towards the front (-1) or the back (+1) of its area."""
        r = self.toolbar_reihenfolge()
        pos = self.toolbar_position(name)
        gleiche = [n for n in r if self.toolbar_position(n) == pos]
        if name not in gleiche:
            return
        i = gleiche.index(name) + schritt
        if not 0 <= i < len(gleiche):
            return
        andere = gleiche[i]
        a, b = r.index(name), r.index(andere)
        r[a], r[b] = r[b], r[a]
        self._toolbar_reihe_speichern()

    def toolbar_vor(self, name, ziel):
        """Places bar `name` directly in front of bar `ziel`."""
        r = self.toolbar_reihenfolge()
        if name == ziel or name not in r or ziel not in r:
            return
        r.remove(name)
        r.insert(r.index(ziel), name)
        self._toolbar_reihe_speichern()

    def _toolbar_reihe_speichern(self):
        try:
            cfg = lade_konfiguration()
            cfg["toolbar_reihenfolge"] = list(self._tb_reihe)
            speichere_konfiguration(cfg)
        except Exception:
            pass
        self._toolbar_anordnen()

    # ---- show / hide --------------------------------------------------
    def _tb_aus_liste(self):
        if getattr(self, "_tb_aus", None) is None:
            try:
                a = lade_konfiguration().get("toolbar_aus")
            except Exception:
                a = None
            self._tb_aus = [n for n in (a or []) if n in LEISTEN] if isinstance(a, list) else []
        return self._tb_aus

    def toolbar_sichtbar(self, name):
        return name not in self._tb_aus_liste()

    def _tb_aus_speichern(self):
        try:
            cfg = lade_konfiguration()
            cfg["toolbar_aus"] = list(self._tb_aus_liste())
            speichere_konfiguration(cfg)
        except Exception:
            pass

    def toolbar_sichtbar_setzen(self, name, sichtbar):
        """Shows / hides one bar (stored in the configuration)."""
        if name not in LEISTEN:
            return
        aus = self._tb_aus_liste()
        if sichtbar and name in aus:
            aus.remove(name)
        elif not sichtbar and name not in aus:
            aus.append(name)
        self._tb_aus_speichern()
        self._toolbar_sicht_vars_pflegen()
        self._toolbar_anordnen()

    def toolbar_alle_einblenden(self):
        self._tb_aus_liste().clear()
        self._tb_aus_speichern()
        self._toolbar_sicht_vars_pflegen()
        self._toolbar_anordnen()

    def toolbar_standard(self):
        """Original layout: every bar visible, on top, in the original order."""
        self._tb_aus_liste().clear()
        self._tb_reihe = list(LEISTEN)
        self._tb_pos_werte = {n: "oben" for n in LEISTEN}
        try:
            cfg = lade_konfiguration()
            cfg["toolbar_aus"] = []
            cfg["toolbar_reihenfolge"] = list(LEISTEN)
            for n in LEISTEN:
                cfg[CONFIG_KEY[n]] = "oben"
            speichere_konfiguration(cfg)
        except Exception:
            pass
        self._toolbar_sicht_vars_pflegen()
        self._toolbar_anordnen()

    def toolbar_sicht_var(self, name):
        """BooleanVar of the check entry View > Toolbars > <bar> > Show."""
        if getattr(self, "_tb_sicht_vars", None) is None:
            self._tb_sicht_vars = {}
        v = self._tb_sicht_vars.get(name)
        if v is None:
            v = self._tb_sicht_vars[name] = tk.BooleanVar(value=self.toolbar_sichtbar(name))
        return v

    def _toolbar_sicht_vars_pflegen(self):
        for n, v in (getattr(self, "_tb_sicht_vars", None) or {}).items():
            try:
                v.set(self.toolbar_sichtbar(n))
            except Exception:
                pass

    def toolbar_menue_zeigen(self, name, x, y):
        """Context menu of a bar: hide it, show the hidden ones, restore everything."""
        m = tk.Menu(self.root, tearoff=0, bg=FARBEN["bg_mittel"], fg=FARBEN["cyan"],
                    activebackground=FARBEN["cyan"], activeforeground=FARBEN["bg_dunkel"])
        if name in LEISTEN and self.toolbar_sichtbar(name):
            m.add_command(label=tr("tb.ausblenden", n=tr("menu.ansicht.tb_" + name)),
                          command=lambda: self._toolbar_ausblenden_hinweis(name))
        aus = [n for n in LEISTEN if not self.toolbar_sichtbar(n)]
        if aus:
            if m.index("end") is not None:
                m.add_separator()
            for n in aus:
                m.add_command(label=tr("tb.einblenden_n", n=tr("menu.ansicht.tb_" + n)),
                              command=lambda n=n: self.toolbar_sichtbar_setzen(n, True))
            if len(aus) > 1:
                m.add_command(label=tr("menu.ansicht.tb_alle"), command=self.toolbar_alle_einblenden)
        m.add_separator()
        m.add_command(label=tr("menu.ansicht.tb_standard"), command=self.toolbar_standard)
        self._menue_zeigen(m, x, y)

    def _toolbar_ausblenden_hinweis(self, name):
        self.toolbar_sichtbar_setzen(name, False)
        try:
            self.status.set(tr("msg.tb.ausgeblendet"))
        except Exception:
            pass

    def _toolbar_rechtsklick_binden(self, tb, name):
        """Right click on a bar (also on its symbols) opens its context menu."""
        def zeigen(e):
            self.toolbar_menue_zeigen(name, e.x_root, e.y_root)
            return "break"
        ereignis = f"<ButtonRelease-{BTN_RECHTS}>"

        def rek(w, ersetzen=False):
            try:
                if ersetzen:
                    w.bind(ereignis, zeigen)            # the bar itself persists: no double binding
                else:
                    w.bind(ereignis, zeigen, add="+")
            except Exception:
                pass
            for ch in w.winfo_children():
                rek(ch)
        rek(tb, True)

    def _notleiste(self):
        """Small bar that is shown while every toolbar is hidden: the way back."""
        nl_ = getattr(self, "_tb_notleiste", None)
        if nl_ is None:
            nl_ = self._tb_notleiste = ttk.Frame(self._zone("oben"))
            ttk.Button(nl_, text=tr("tb.einblenden"),
                       command=lambda: self.toolbar_menue_zeigen(
                           "", self.root.winfo_rootx() + 20, self.root.winfo_rooty() + 80)).pack(side=tk.LEFT)
            self._toolbar_rechtsklick_binden(nl_, "")
        return nl_

    # ---- positions ----------------------------------------------------
    def toolbar_position(self, name="werkzeug"):
        if self._tb_pos_werte is None:
            self._tb_pos_werte = {}
        if name not in self._tb_pos_werte:
            try:
                pos = lade_konfiguration().get(CONFIG_KEY[name], "oben")
            except Exception:
                pos = "oben"
            self._tb_pos_werte[name] = pos if pos in POSITIONEN else "oben"
        return self._tb_pos_werte[name]

    def toolbar_position_setzen(self, pos, name="werkzeug", speichern=True):
        if pos not in POSITIONEN or name not in CONFIG_KEY:
            return
        self.toolbar_position(name)
        self._tb_pos_werte[name] = pos
        if speichern:
            try:
                cfg = lade_konfiguration()
                cfg[CONFIG_KEY[name]] = pos
                speichere_konfiguration(cfg)
            except Exception:
                pass
        self._toolbar_anordnen()

    def _leiste(self, name):
        return getattr(self, LEISTEN_ATTR[name], None)

    def _zone(self, pos):
        """Frame that holds all bars docked at `pos` (created on demand)."""
        if self._tb_zonen is None:
            self._tb_zonen = {}
        z = self._tb_zonen.get(pos)
        if z is None:
            z = ttk.Frame(self.root)
            self._tb_zonen[pos] = z
        return z

    # ---- layout -------------------------------------------------------
    def _toolbar_anordnen(self):
        """(Re)places the three symbol toolbars according to their stored positions."""
        if self._tb_info is None:
            self._tb_info = {}
        koord = getattr(self, "_koord_bar", None)
        belegt = {p: [] for p in POSITIONEN}
        nl_ = getattr(self, "_tb_notleiste", None)
        if nl_ is not None:
            nl_.grid_forget()
        for name in self.toolbar_reihenfolge():
            tb = self._leiste(name)
            if tb is None:
                continue
            pos = self.toolbar_position(name)
            if pos != "oben" and koord is None:
                pos = "oben"
            if self.toolbar_sichtbar(name):
                belegt[pos].append(name)
            for ch in tb.winfo_children():
                if ch.winfo_manager() == "pack":
                    self._tb_info[ch] = ch.pack_info()
            for ch in tb.winfo_children():
                ch.pack_forget()
                ch.grid_forget()
            tb.pack_forget()
        for pos in POSITIONEN:
            self._zone(pos).pack_forget()
        # docking areas
        alle_aus = not any(belegt.values()) and any(self._leiste(n) is not None for n in LEISTEN)
        if alle_aus:                                   # never leave the user without a way back
            self._zone("oben").pack(side=tk.TOP, fill=tk.X, before=self.tb2)
            self._notleiste().grid(row=50, column=0, sticky="nw")
        if belegt["oben"]:
            self._zone("oben").pack(side=tk.TOP, fill=tk.X, before=self.tb2)
        if belegt["unten"] and koord is not None:
            self._zone("unten").pack(side=tk.BOTTOM, fill=tk.X, after=koord)
        if belegt["rechts"] and koord is not None:
            self._zone("rechts").pack(side=tk.RIGHT, fill=tk.Y, after=koord)
        if belegt["links"] and koord is not None:
            vor = getattr(self, "_tab_leiste", None)
            if vor is None:
                vor = self._zeichenflaeche()
            try:
                self._zone("links").pack(side=tk.LEFT, fill=tk.Y, before=vor)
            except tk.TclError:                        # reference widget not packed in the window
                self._zone("links").pack(side=tk.LEFT, fill=tk.Y)
        for pos, namen in belegt.items():
            zone = self._zone(pos)
            for name in namen:
                tb = self._leiste(name)
                if pos in VERTIKAL:
                    tb.pack(in_=zone, side=tk.TOP, fill=tk.X, anchor="n")
                    tb.tkraise()
                if pos in VERTIKAL:
                    self._leiste_gitter(name, len(namen))
                else:
                    for ch in tb.winfo_children():
                        info = self._tb_info.get(ch)
                        if info:
                            info = {k: v for k, v in info.items() if k != "in"}
                            ch.pack(**info)
                        else:
                            ch.pack(side=tk.LEFT)
        for pos in ("oben", "unten"):
            self._zone_reihen(pos, belegt[pos])
        if not getattr(self, "_tb_binding", False):
            self._tb_binding = True
            self.root.bind("<Configure>", self._toolbar_groesse, add="+")

    def _zone_reihen(self, pos, namen):
        """Bars on top/bottom sit side by side and wrap into a new row when too wide."""
        if not namen:
            return
        zone = self._zone(pos)
        try:
            self.root.update_idletasks()
        except Exception:
            return
        frei = self.root.winfo_width()
        frei = frei if frei > 300 else 1200
        # every row is its own frame: bars of different rows must not share grid columns
        # (a wide bar of row 2 would otherwise push the bars of row 1 apart)
        zeilen = [[]]
        x = 0
        for name in namen:
            w = self._leiste(name).winfo_reqwidth()
            if x and x + w > frei:
                zeilen.append([])
                x = 0
            zeilen[-1].append(name)
            x += w
        if not hasattr(self, "_zone_zeilen"):
            self._zone_zeilen = {}
        rahmen = self._zone_zeilen.setdefault(pos, [])
        for r in rahmen[len(zeilen):]:
            r.grid_forget()
        for i, namen_z in enumerate(zeilen):
            while len(rahmen) <= i:
                rahmen.append(ttk.Frame(zone))
            zf = rahmen[i]
            zf.grid(row=i, column=0, sticky="nw")
            for name in namen_z:
                tb = self._leiste(name)
                tb.grid_forget()
                tb.pack(in_=zf, side=tk.LEFT, anchor="nw")
                tb.tkraise()                  # must lie above its zone, else it is hidden

    def _leiste_gitter(self, name, anzahl_rechts):
        tb = self._leiste(name)
        sichtbar = [c for c in tb.winfo_children() if not isinstance(c, ttk.Separator)]
        hoehe = (self.root.winfo_height() - 230) // max(1, anzahl_rechts)
        n = spalten_zeilen(len(sichtbar), hoehe)
        for i, ch in enumerate(sichtbar):
            ch.grid(row=i % n, column=i // n, padx=1, pady=1, sticky="w")
        return n

    def _toolbar_groesse(self, event=None):
        if self._tb_resize_id is not None:
            try:
                self.root.after_cancel(self._tb_resize_id)
            except Exception:
                pass
        self._tb_resize_id = self.root.after(250, self._toolbar_neu_gitter)

    def _toolbar_neu_gitter(self):
        self._tb_resize_id = None
        def sicht(pos):
            return [n for n in self.toolbar_reihenfolge() if self._leiste(n) is not None
                    and self.toolbar_position(n) == pos and self.toolbar_sichtbar(n)]
        seiten = {p: sicht(p) for p in VERTIKAL}
        key = (self.root.winfo_height() // ZELLE_PX, self.root.winfo_width() // 40,
               tuple(len(v) for v in seiten.values()))
        if getattr(self, "_tb_zeilen", None) == key:
            return
        self._tb_zeilen = key
        for namen in seiten.values():
            for n in namen:
                self._leiste_gitter(n, len(namen))
        for pos in ("oben", "unten"):
            self._zone_reihen(pos, sicht(pos))

    def _leiste_ablegen(self, name, px, py):
        """Drop at screen point (px, py): the bar under it of the same area decides; left half =
        before it, right half = behind it. True when handled."""
        r = self.toolbar_reihenfolge()
        pos = self.toolbar_position(name)
        for n in LEISTEN:
            tb = self._leiste(n)
            if n == name or tb is None or self.toolbar_position(n) != pos or not self.toolbar_sichtbar(n):
                continue
            try:
                x0, y0 = tb.winfo_rootx(), tb.winfo_rooty()
                x1, y1 = x0 + tb.winfo_width(), y0 + tb.winfo_height()
            except Exception:
                continue
            if x0 <= px <= x1 and y0 <= py <= y1:
                if (px - x0) * 2 < (x1 - x0) if pos not in VERTIKAL else (py - y0) * 2 < (y1 - y0):
                    self.toolbar_vor(name, n)
                else:
                    r.remove(name)
                    r.insert(r.index(n) + 1, name)
                    self._toolbar_reihe_speichern()
                return True
        return False

    def _links_grenze(self, fensterbreite):
        """Right edge of the left drop area as a fraction of the window width: the project
        sidebar (when visible) plus a margin of 80 px."""
        breite = 0
        try:
            sl = getattr(self, "seitenleiste", None)
            if sl is not None and sl.ist_sichtbar():
                breite = sl.winfo_width()
        except Exception:
            breite = 0
        return min(0.5, max(0.08, (breite + 80) / max(1, fensterbreite)))

    def _toolbar_griff_binden(self, griff, name="werkzeug"):
        """Drag the grip to an edge of the window and release."""
        def los(e):
            try:
                w = max(1, self.root.winfo_width())
                h = max(1, self.root.winfo_height())
                px, py = self.root.winfo_pointerxy()
                relx = (px - self.root.winfo_rootx()) / w
                rely = (py - self.root.winfo_rooty()) / h
            except Exception:
                return
            neu = ziel_position(relx, rely, self.toolbar_position(name), self._links_grenze(w))
            if neu != self.toolbar_position(name):
                self.toolbar_position_setzen(neu, name)
                return
            # same area: dropped on another bar (found by its screen rectangle, so gaps,
            # tooltips and the label do not matter) -> before / behind it
            if self._leiste_ablegen(name, px, py):
                return
            try:
                unter = self.root.winfo_containing(px, py)
            except Exception:
                unter = None
            while unter is not None and unter is not self.root:
                for n in LEISTEN:
                    if n != name and self._leiste(n) is unter and \
                            self.toolbar_position(n) == self.toolbar_position(name):
                        r = self.toolbar_reihenfolge()
                        if r.index(n) < r.index(name):
                            self.toolbar_vor(name, n)
                        else:                         # behind it: swap places
                            r.remove(name)
                            r.insert(r.index(n) + 1, name)
                            self._toolbar_reihe_speichern()
                        return
                unter = getattr(unter, "master", None)
        griff.bind("<ButtonRelease-1>", los)
