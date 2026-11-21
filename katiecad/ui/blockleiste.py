# -*- coding: utf-8 -*-
"""
katiecad/ui/blockleiste.py - the block browser as a bar docked left or right of the drawing
area (BSD-3-Clause).

Same content as the block browser dialog (folders, blocks, preview - the logic is shared,
dialogs.BlockBrowserBasis), arranged from top to bottom so it fits a narrow bar. A double
click or "Insert" starts inserting the block exactly like the dialog does (the user then
clicks the insertion point). The bar stays open while drawing.

Switched on and off with View > Block browser bar (off / left / right) or the button
"Dock as bar" in the dialog. Dragging the header moves the bar to the other side (as does
the ⇄ button); its inner edge changes the width. Side and width are kept in the configuration
("blockleiste_seite", "blockleiste_breite"). The methods of CadApp used are in BlockleisteMixin.
"""

import os
import tkinter as tk
from tkinter import ttk

from katiecad.common.config import lade_konfiguration, speichere_konfiguration
from katiecad.common.i18n import tr
from katiecad.model.core import FARBEN
from katiecad.ui.dialogs import BlockBrowserBasis

BREITE_STANDARD = 300
BREITE_MIN = 200
BREITE_MAX = 600
SEITEN = ("links", "rechts")


class Blockleiste(BlockBrowserBasis, ttk.Frame):
    def __init__(self, parent, app, breite=None):
        super().__init__(parent, padding=(6, 6))
        self.app = app
        self.wurzeln = list(app._block_wurzeln())
        self._lader = app._block_datei_laden
        self._dateien = {}
        self.seite = "rechts"
        self.breite = max(BREITE_MIN, min(BREITE_MAX, int(breite or BREITE_STANDARD)))
        self.configure(width=self.breite)
        self.pack_propagate(False)
        # drag handle between bar and drawing area (a sibling in the main window)
        self.griff = tk.Frame(parent, width=5, cursor="sb_h_double_arrow", bg=FARBEN["bg_mittel"])
        self.griff.bind("<Enter>", lambda e: self.griff.config(bg=FARBEN["cyan"]))
        self.griff.bind("<Leave>", lambda e: self.griff.config(bg=FARBEN["bg_mittel"]))
        self.griff.bind("<B1-Motion>", self._ziehen)
        self.griff.bind("<ButtonRelease-1>", lambda e: self.app._blockleiste_merken())
        self._bauen()
        self._baum_aufbauen()

    # ---------------------------------------------------- widgets
    def _bauen(self):
        kopf = ttk.Frame(self, cursor="fleur")
        kopf.pack(fill=tk.X)
        titel = ttk.Label(kopf, text=tr("dlg.bb.titel"), style="Title.TLabel", cursor="fleur")
        titel.pack(side=tk.LEFT, fill=tk.X, expand=True)
        for w in (kopf, titel):              # drag the header to the other side of the window
            w.bind("<B1-Motion>", self._kopf_ziehen)
        # close and "other side" as small buttons at the right end of the header
        ttk.Button(kopf, text="✕", width=3, command=lambda: self.app.blockleiste_setzen("")
                   ).pack(side=tk.RIGHT)
        self.btn_seite = ttk.Button(kopf, text="⇄", width=3, command=self.app.blockleiste_seite_wechseln)
        self.btn_seite.pack(side=tk.RIGHT, padx=(0, 4))

        ttk.Label(self, text=tr("dlg.bb.ordner"), style="Hint.TLabel").pack(anchor=tk.W, pady=(8, 2))
        bf = ttk.Frame(self)
        bf.pack(fill=tk.X)
        self.baum = ttk.Treeview(bf, show="tree", selectmode="browse", height=7)
        sb = ttk.Scrollbar(bf, orient=tk.VERTICAL, command=self.baum.yview)
        self.baum.configure(yscrollcommand=sb.set)
        self.baum.pack(side=tk.LEFT, fill=tk.X, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.baum.bind("<<TreeviewSelect>>", lambda e: self._ordner_gewaehlt())

        ttk.Label(self, text=tr("dlg.bb.dateien"), style="Hint.TLabel").pack(anchor=tk.W, pady=(8, 2))
        unten = ttk.Frame(self)                  # packed before the list: list takes the rest
        unten.pack(side=tk.BOTTOM, fill=tk.X)
        lf = ttk.Frame(self)
        lf.pack(fill=tk.BOTH, expand=True)
        self.liste = ttk.Treeview(lf, columns=("name",), show="headings", selectmode="browse")
        self.liste.heading("name", text=tr("dlg.block.auswahl.name"))
        self.liste.column("name", width=200, anchor=tk.W)
        sl = ttk.Scrollbar(lf, orient=tk.VERTICAL, command=self.liste.yview)
        self.liste.configure(yscrollcommand=sl.set)
        self.liste.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sl.pack(side=tk.RIGHT, fill=tk.Y)
        self.liste.bind("<<TreeviewSelect>>", lambda e: self._datei_gewaehlt())
        self.liste.bind("<Double-Button-1>", lambda e: self._einfuegen())
        self.liste.bind("<Return>", lambda e: self._einfuegen())

        self.vorschau = tk.Canvas(unten, width=BREITE_STANDARD - 20, height=200, highlightthickness=1)
        self.vorschau.pack(fill=tk.X, pady=(8, 0))
        self._vorschau_breite = None
        self.vorschau.bind("<Configure>", self._vorschau_neu)
        self.info = ttk.Label(unten, text="", style="Hint.TLabel", justify=tk.LEFT,
                              wraplength=self.breite - 20)
        self.info.pack(anchor=tk.W, pady=(4, 0))
        knoepfe = ttk.Frame(unten)
        knoepfe.pack(fill=tk.X, pady=(6, 0))
        self.btn_ein = ttk.Button(knoepfe, text=tr("dlg.bb.einfuegen"), command=self._einfuegen)
        self.btn_ein.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(knoepfe, text=tr("dlg.bb.ordner_hinzu"), command=self._ordner_hinzu).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        self.btn_del = None                      # deleting files stays in the dialog

    # ---------------------------------------------------- docking
    def andocken(self, seite, vor):
        """Shows the bar on `seite` ("links" / "rechts") next to the drawing area: packed
        before `vor` (the drawing area or the tab bar), the handle between bar and drawing."""
        self.seite = seite
        self.pack_forget()
        self.griff.pack_forget()
        s = tk.LEFT if seite == "links" else tk.RIGHT
        self.pack(side=s, fill=tk.Y, before=vor)
        self.griff.pack(side=s, fill=tk.Y, before=vor)

    def abdocken(self):
        self.pack_forget()
        self.griff.pack_forget()

    def zerstoeren(self):
        self.griff.destroy()
        self.destroy()

    def _kopf_ziehen(self, ev):
        """Header dragged: the bar docks on the half of the window the mouse is in (it moves
        over while dragging; the widgets are only re-packed, so the drag goes on)."""
        top = self.winfo_toplevel()
        x = ev.x_root - top.winfo_rootx()
        seite = "links" if x < top.winfo_width() / 2 else "rechts"
        if seite != self.seite:
            self.app.blockleiste_setzen(seite)

    def _ziehen(self, ev):
        if self.seite == "links":
            neu = ev.x_root - self.winfo_rootx()
        else:
            neu = self.winfo_rootx() + self.winfo_width() - ev.x_root
        neu = max(BREITE_MIN, min(BREITE_MAX, int(neu)))
        if neu != self.breite:
            self.breite = neu
            self.configure(width=neu)
            self.info.configure(wraplength=neu - 20)

    # ---------------------------------------------------- content
    def _vorschau_groesse(self):
        """The preview follows the width of the bar (the dialog uses a fixed size)."""
        w = self.vorschau.winfo_width()
        return (w if w > 20 else BREITE_STANDARD - 20), 200

    def _vorschau_neu(self, ev):
        if ev.width != self._vorschau_breite:          # width changed: draw the preview to fit
            self._vorschau_breite = ev.width
            if self._datei():
                self._datei_gewaehlt()

    def wurzeln_pruefen(self):
        """Builds the folder tree anew when the folders changed (another project opened)."""
        neu = list(self.app._block_wurzeln())
        for name, pfad in self.wurzeln:                 # folders added in the bar stay
            if all(os.path.normpath(pfad) != os.path.normpath(p) for _n, p in neu):
                neu.append((name, pfad))
        if neu != self.wurzeln:
            alt = self._ordner()
            self.wurzeln = neu
            self._baum_aufbauen(alt)

    def _ordner_hinzu(self):
        BlockBrowserBasis._ordner_hinzu(self)
        self.app._block_wurzeln_merken(self.wurzeln)

    def _einfuegen(self):
        pf = self._datei()
        if pf:
            self.app.block_aus_datei_einfuegen(pf)


class BlockleisteMixin:
    """Methods of CadApp for the docked block browser."""

    _blockleiste = None

    def _blockleiste_var(self):
        """Variable of the radio entries View > Block browser bar ("", "links", "rechts")."""
        v = getattr(self, "_blockleiste_seite_var", None)
        if v is None:
            v = self._blockleiste_seite_var = tk.StringVar(value="")
        return v

    def blockleiste_setzen(self, seite):
        """Docks the block browser left / right of the drawing area, "" closes it."""
        seite = seite if seite in SEITEN else ""
        bl = self._blockleiste
        if not seite:
            if bl is not None:
                bl.abdocken()
        else:
            if bl is None:
                cfg = self._blockleiste_konfig()
                bl = self._blockleiste = Blockleiste(self.root, self, cfg.get("blockleiste_breite"))
            bl.wurzeln_pruefen()
            tabs = getattr(self, "_tab_leiste", None)
            bl.andocken(seite, tabs if tabs is not None else self._zeichenflaeche())
        self._blockleiste_var().set(seite)
        self._blockleiste_merken()

    def blockleiste_seite_wechseln(self):
        bl = self._blockleiste
        if bl is not None:
            self.blockleiste_setzen("links" if bl.seite == "rechts" else "rechts")

    def _blockleiste_offen(self):
        return self._blockleiste is not None and self._blockleiste.winfo_ismapped()

    def _blockleiste_wiederherstellen(self):
        """At start: the bar as it was when the program was closed."""
        seite = self._blockleiste_konfig().get("blockleiste_seite") or ""
        if seite in SEITEN:
            self.blockleiste_setzen(seite)

    def _blockleiste_wurzeln_pruefen(self):
        if self._blockleiste is not None:
            try:
                self._blockleiste.wurzeln_pruefen()
            except Exception as ex:
                print(f"[KatieCAD] Blockleiste: {ex}")

    @staticmethod
    def _blockleiste_konfig():
        try:
            return lade_konfiguration()
        except Exception:
            return {}

    def _blockleiste_merken(self):
        try:
            cfg = lade_konfiguration()
            cfg["blockleiste_seite"] = self._blockleiste_var().get()
            if self._blockleiste is not None:
                cfg["blockleiste_breite"] = int(self._blockleiste.breite)
            speichere_konfiguration(cfg)
        except Exception as ex:
            print(f"[KatieCAD] Konfiguration: {ex}")
