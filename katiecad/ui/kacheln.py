# -*- coding: utf-8 -*-
"""
katiecad/ui/kacheln.py - open drawings side by side in the window ("tiles", BSD-3-Clause).

Builds on the tabs (ui/tabs.py): every tile shows one `Dokument` in a drawing area of its own.
The program logic still works on ONE drawing - the one of the active tile: `self.canvas` is
that tile's drawing area and the drawing state is swapped exactly as for a tab switch. The
other tiles are drawn once (and whenever their size changes) with their own state put in
place for that moment; they react to the mouse only by becoming the active tile.

Up to four tiles; the separators between them can be dragged, a tile header can be dragged
to another position. More open drawings stay reachable through the tab bar: clicking a tab
that is not shown puts its drawing into the active tile.
"""

import tkinter as tk

from katiecad.common.i18n import tr
from katiecad.model.core import FARBEN

MAX_KACHELN = 4
TRENNER = 5            # px between two tiles
MIN_BREITE = 140       # px a tile keeps at least
KLASSE = "KatieKachel"

# while an inactive tile is drawn these parts of the program must not react (they belong to
# the active drawing: palettes, dialogs, the tool preview)
_STILL = ("_layer_anzeige_nachziehen", "_eig_palette_nachziehen", "_xref_dialog_aktualisieren",
          "_vorschau_neu", "_leistung_melden")


class Kachel:
    def __init__(self, dok):
        self.dok = dok
        self.anteil = 1.0
        self.x = 0
        self.w = 0
        self.rahmen = self.kopf = self.titel = self.zu = self.canvas = None
        self.bild_live = []            # keeps the images of this tile's last drawing
        self.zeichnen_id = None


class KachelnMixin:
    # ---------------------------------------------------- state
    def _kacheln_init(self):
        self._kacheln = None           # list of Kachel while the tiles are shown
        self._kachel_feld = None
        self._kachel_original = None   # the drawing area of the tab view
        self._kachel_zug_daten = None  # header being dragged
        self._kachel_klasse_da = False
        self._kachel_klick_schlucken = False

    def kacheln_aktiv(self):
        return bool(getattr(self, "_kacheln", None))

    def _zeichenflaeche(self):
        """The widget in the window's packing order that holds the drawing (for `before=`)."""
        if self.kacheln_aktiv():
            return self._kachel_feld
        w3 = getattr(self, "_ansicht3d", None)
        return w3 if w3 is not None else self.canvas

    def _kachel_von(self, dok):
        for k in self._kacheln or ():
            if k.dok is dok:
                return k
        return None

    def _kachel_aktiv(self):
        return self._kachel_von(self._dokumente[self._dok_aktiv])

    # ---------------------------------------------------- on / off
    def kacheln_an(self):
        if self.kacheln_aktiv() or len(self._dokumente) < 2:
            return
        try:
            if self.ansicht3d_aktiv():
                self.ansicht3d_setzen(False)
        except Exception:
            pass
        self._aktionen_beenden()
        aktiv = self._dokumente[self._dok_aktiv]
        self._dok_sichern(aktiv)
        doks = self._dokumente[:MAX_KACHELN]
        if aktiv not in doks:
            doks = doks[:MAX_KACHELN - 1] + [aktiv]
        self._kachel_klasse_binden()
        feld = tk.Frame(self.root, bg=FARBEN["bg_dunkel"], bd=0, highlightthickness=0)
        feld.pack(fill=tk.BOTH, expand=True, before=self.canvas)
        self._kachel_original = self.canvas
        self.canvas.pack_forget()
        self._kachel_feld = feld
        self._kacheln = []
        for d in doks:
            self._kachel_bauen(d)
        feld.bind("<Configure>", lambda e: self._kacheln_anordnen())
        self.canvas = self._kachel_aktiv().canvas
        self._kacheln_anordnen()
        self._kacheln_koepfe()
        self._ansicht_neu_aufbauen()
        for k in self._kacheln:
            self._kachel_spaeter_zeichnen(k)
        self._tab_leiste_zeichnen()

    def kacheln_aus(self):
        if not self.kacheln_aktiv():
            return
        self._aktionen_beenden()
        for k in self._kacheln:
            if k.zeichnen_id is not None:
                try:
                    self.root.after_cancel(k.zeichnen_id)
                except Exception:
                    pass
        self.canvas = self._kachel_original
        self.canvas.pack(fill=tk.BOTH, expand=True, before=self._kachel_feld)
        self._kachel_feld.destroy()
        self._kachel_feld = None
        self._kacheln = None
        self._kachel_original = None
        self._ansicht_neu_aufbauen()
        self._tab_leiste_zeichnen()

    # ---------------------------------------------------- building a tile
    def _kachel_bauen(self, dok, position=None):
        k = Kachel(dok)
        feld = self._kachel_feld
        k.rahmen = tk.Frame(feld, bg=FARBEN["bg_dunkel"], bd=0, highlightthickness=0)
        k.kopf = tk.Frame(k.rahmen, bg=FARBEN["bg_dunkel"], bd=0, highlightthickness=0,
                          cursor="fleur")
        k.kopf.pack(side=tk.TOP, fill=tk.X)
        schrift = ("Segoe UI", 9)
        k.titel = tk.Label(k.kopf, text="", anchor="w", bg=FARBEN["bg_dunkel"],
                           fg=FARBEN["text_dim"], font=schrift, padx=8, pady=2, cursor="fleur")
        k.titel.pack(side=tk.LEFT, fill=tk.X, expand=True)
        k.zu = tk.Label(k.kopf, text="✕", bg=FARBEN["bg_dunkel"], fg=FARBEN["text_dim"],
                        font=schrift, padx=6, pady=2, cursor="hand2")
        k.zu.pack(side=tk.RIGHT)
        k.zu.bind("<Button-1>", lambda e, k=k: self._kachel_schliessen(k))
        k.zu.bind("<Enter>", lambda e, w=k.zu: w.config(fg=FARBEN["rot"]))
        k.zu.bind("<Leave>", lambda e, k=k: self._kacheln_koepfe())
        for w in (k.kopf, k.titel):
            w.bind("<Button-1>", lambda e, k=k: self._kachel_zug_start(e, k))
            w.bind("<B1-Motion>", lambda e, k=k: self._kachel_zug(e, k))
            w.bind("<ButtonRelease-1>", lambda e, k=k: self._kachel_zug_ende(e, k))
            w.bind("<Button-2>", lambda e, k=k: self._kachel_schliessen(k))
            w.bind("<Button-3>", lambda e, k=k: self._kachel_kontextmenue(e, k))
        c = tk.Canvas(k.rahmen, bg=self.bg_modell, highlightthickness=1,
                      highlightbackground=FARBEN["rand"], cursor="crosshair")
        c.pack(fill=tk.BOTH, expand=True)
        k.canvas = c
        # the same mouse handling as the drawing area of the tab view (they act on
        # self.canvas, which is this canvas while the tile is the active one)
        vorher = self.canvas
        self.canvas = c
        try:
            self._bind_events()
        finally:
            self.canvas = vorher
        c.bind("<Configure>", lambda e, k=k: self._kachel_groesse(k))
        c.bindtags((KLASSE,) + tuple(c.bindtags()))
        if position is None:
            self._kacheln.append(k)
        else:
            self._kacheln.insert(position, k)
        n = len(self._kacheln)
        for x in self._kacheln:                   # a new tile: all of them equally wide
            x.anteil = 1.0 / n
        return k

    def _kachel_klasse_binden(self):
        """Mouse on a tile that is not the active one: a click makes it the active tile
        (left click only that; middle/right/wheel then act as usual on it), everything else
        is ignored there."""
        if self._kachel_klasse_da:
            return
        self._kachel_klasse_da = True
        r = self.root

        def inaktiv(e):
            return self.kacheln_aktiv() and e.widget is not self.canvas

        def druecken(e, weiter):
            if not inaktiv(e):
                return None
            k = next((k for k in self._kacheln if k.canvas is e.widget), None)
            if k is not None:
                self._kachel_aktivieren(k)
            if not weiter or e.widget is not self.canvas:
                self._kachel_klick_schlucken = True     # its drag / release as well
                return "break"
            return None

        def sperren(e):
            return "break" if inaktiv(e) else None

        def links_weiter(e):
            if self._kachel_klick_schlucken:
                return "break"
            return sperren(e)

        def links_los(e):
            if self._kachel_klick_schlucken:
                self._kachel_klick_schlucken = False
                return "break"
            return sperren(e)

        r.bind_class(KLASSE, "<Button-1>", lambda e: druecken(e, False))
        for b in (2, 3):
            r.bind_class(KLASSE, f"<Button-{b}>", lambda e: druecken(e, True))
        r.bind_class(KLASSE, "<MouseWheel>", lambda e: druecken(e, True))
        r.bind_class(KLASSE, "<Button-4>", lambda e: druecken(e, True))
        r.bind_class(KLASSE, "<Button-5>", lambda e: druecken(e, True))
        r.bind_class(KLASSE, "<B1-Motion>", links_weiter)
        r.bind_class(KLASSE, "<ButtonRelease-1>", links_los)
        for seq in ("<Motion>", "<B2-Motion>", "<B3-Motion>",
                    "<ButtonRelease-2>", "<ButtonRelease-3>",
                    "<Double-Button-1>", "<Double-Button-2>", "<Double-Button-3>",
                    "<Leave>", "<Control-Button-1>", "<Control-ButtonRelease-1>"):
            r.bind_class(KLASSE, seq, sperren)

    # ---------------------------------------------------- layout
    def _kacheln_anordnen(self):
        feld = self._kachel_feld
        if feld is None or not self._kacheln:
            return
        for w in list(feld.winfo_children()):
            if getattr(w, "_kachel_trenner", False):
                w.destroy()
        n = len(self._kacheln)
        breite = max(feld.winfo_width(), 1)
        hoehe = max(feld.winfo_height(), 1)
        platz = max(breite - TRENNER * (n - 1), n)
        summe = sum(k.anteil for k in self._kacheln) or 1.0
        x = 0
        for i, k in enumerate(self._kacheln):
            w = platz - (x - TRENNER * i) if i == n - 1 else round(platz * k.anteil / summe)
            k.x, k.w = x, max(w, 1)
            k.rahmen.place(x=k.x, y=0, width=k.w, height=hoehe)
            x += k.w
            if i < n - 1:
                t = tk.Frame(feld, bg=FARBEN["bg_dunkel"], width=TRENNER, bd=0,
                             highlightthickness=0, cursor="sb_h_double_arrow")
                t._kachel_trenner = True
                t.place(x=x, y=0, width=TRENNER, height=hoehe)
                t.bind("<B1-Motion>", lambda e, i=i: self._trenner_ziehen(e, i))
                t.bind("<Enter>", lambda e, t=t: t.config(bg=FARBEN["rand"]))
                t.bind("<Leave>", lambda e, t=t: t.config(bg=FARBEN["bg_dunkel"]))
                x += TRENNER

    def _trenner_ziehen(self, e, i):
        links, rechts = self._kacheln[i], self._kacheln[i + 1]
        x = e.x_root - self._kachel_feld.winfo_rootx()
        paar = links.w + rechts.w
        neu = min(max(x - links.x, MIN_BREITE), paar - MIN_BREITE)
        if paar <= 2 * MIN_BREITE or neu == links.w:
            return
        summe = links.anteil + rechts.anteil
        links.anteil = summe * neu / paar
        rechts.anteil = summe - links.anteil
        self._kacheln_anordnen()

    def _kachel_groesse(self, k):
        if k.dok is self._dokumente[self._dok_aktiv] and k.canvas is self.canvas:
            self._zeichne_raster()
        self._kachel_spaeter_zeichnen(k)

    def _kachel_spaeter_zeichnen(self, k, ms=60):
        """Draws a tile again once the size settles (dragging a separator)."""
        if k.zeichnen_id is not None:
            try:
                self.root.after_cancel(k.zeichnen_id)
            except Exception:
                pass
        k.zeichnen_id = self.root.after(ms, lambda: self._kachel_zeichnen(k))

    # ---------------------------------------------------- header: activate, move, close
    def _kacheln_koepfe(self):
        if not self.kacheln_aktiv():
            return
        aktiv = self._dokumente[self._dok_aktiv]
        for k in self._kacheln:
            if k.dok not in self._dokumente:
                continue
            ist = k.dok is aktiv
            bg = FARBEN["bg_mittel"] if ist else FARBEN["bg_dunkel"]
            fg = FARBEN["cyan"] if ist else FARBEN["text_dim"]
            try:
                k.kopf.config(bg=bg)
                k.titel.config(bg=bg, fg=fg, text=self._tab_titel(self._dokumente.index(k.dok)))
                k.zu.config(bg=bg, fg=fg)
                k.canvas.config(highlightbackground=FARBEN["cyan"] if ist else FARBEN["rand"])
            except tk.TclError:
                pass

    def _kachel_aktivieren(self, k):
        if k.dok in self._dokumente:
            self.tab_aktivieren(self._dokumente.index(k.dok))

    def _kachel_zug_start(self, e, k):
        self._kachel_zug_daten = {"x": e.x_root, "bewegt": False}

    def _kachel_zug(self, e, k):
        z = self._kachel_zug_daten
        if z is None:
            return
        if not z["bewegt"] and abs(e.x_root - z["x"]) < 6:
            return
        z["bewegt"] = True
        x = e.x_root - self._kachel_feld.winfo_rootx()
        andere = [a for a in self._kacheln if a is not k]
        # the place where the middle of the dragged tile comes nearest to the mouse (each
        # tile keeps its width, the others keep their order)
        beste, abstand, links = 0, None, 0
        for p in range(len(andere) + 1):
            mitte = links + k.w / 2
            if abstand is None or abs(mitte - x) < abstand:
                beste, abstand = p, abs(mitte - x)
            if p < len(andere):
                links += andere[p].w + TRENNER
        if self._kacheln.index(k) != beste:
            andere.insert(beste, k)
            self._kacheln = andere
            self._kacheln_anordnen()

    def _kachel_zug_ende(self, e, k):
        z, self._kachel_zug_daten = self._kachel_zug_daten, None
        if z is not None and not z["bewegt"]:
            self._kachel_aktivieren(k)

    def _kachel_schliessen(self, k):
        if k.dok in self._dokumente:
            self.tab_schliessen(self._dokumente.index(k.dok))

    def _kachel_kontextmenue(self, e, k):
        m = tk.Menu(self.root, tearoff=0, bg=FARBEN["bg_mittel"], fg=FARBEN["cyan"],
                    activebackground=FARBEN["cyan"], activeforeground=FARBEN["bg_dunkel"])
        m.add_command(label=tr("tabs.als_tabs"), command=self.kacheln_aus)
        m.add_command(label=tr("tabs.breiten_gleich"), command=self._kacheln_gleich)
        m.add_separator()
        m.add_command(label=tr("tabs.schliessen"), command=lambda: self._kachel_schliessen(k))
        try:
            m.tk_popup(e.x_root, e.y_root)
        finally:
            m.grab_release()

    def _kacheln_gleich(self):
        if self.kacheln_aktiv():
            for k in self._kacheln:
                k.anteil = 1.0 / len(self._kacheln)
            self._kacheln_anordnen()

    # ---------------------------------------------------- hooks for the tabs
    def _kachel_wechsel(self, dok):
        """Before `dok` becomes the current drawing: its tile's canvas becomes self.canvas
        (a drawing not shown goes into the active tile)."""
        alt = self.canvas
        ak = next((k for k in self._kacheln if k.canvas is alt), None)
        if ak is not None:
            ak.bild_live = self._bild_live        # its images stay alive while it is shown
        for tag in ("snapmarker", "fadenkreuz", "vorschau"):
            try:
                alt.delete(tag)
            except Exception:
                pass
        k = self._kachel_von(dok)
        if k is None:
            k = self._kachel_aktiv() or self._kacheln[0]
            k.dok = dok
        self.canvas = k.canvas

    def _kachel_neues_dok(self, dok):
        """A new drawing (new tab) is opened while the tiles are shown: a tile of its own
        next to the active one, or - with all tiles in use - into the active tile."""
        alt = next((k for k in self._kacheln if k.canvas is self.canvas), None)
        if len(self._kacheln) < MAX_KACHELN:
            pos = self._kacheln.index(alt) + 1 if alt is not None else len(self._kacheln)
            k = self._kachel_bauen(dok, pos)
            self._kacheln_anordnen()
        else:
            k = alt or self._kacheln[-1]
            k.dok = dok
        self._kachel_wechsel(dok)

    def _kachel_dok_weg(self, dok):
        """`dok` was closed: its tile goes away. -> the drawing to show next (one in a tile),
        or None when the tiles were ended."""
        k = self._kachel_von(dok)
        if k is not None:
            i = self._kacheln.index(k)
            if k.zeichnen_id is not None:
                try:
                    self.root.after_cancel(k.zeichnen_id)
                except Exception:
                    pass
            self._kacheln.remove(k)
            if self._kacheln:
                self._kacheln[min(i, len(self._kacheln) - 1)].anteil += k.anteil
            if k.canvas is self.canvas:
                self.canvas = self._kachel_original      # until the next one is chosen
            k.rahmen.destroy()
        else:
            i = 0
        # a drawing that is open but not shown fills the gap
        frei = [d for d in self._dokumente if self._kachel_von(d) is None]
        if len(self._kacheln) < 2 and frei:
            n = self._kachel_bauen(frei[0], min(i, len(self._kacheln)))
            self._kacheln_anordnen()
            self._kachel_spaeter_zeichnen(n)
        if len(self._kacheln) < 2:
            rest = self._kacheln[0].dok if self._kacheln else None
            self.canvas = self._kachel_original
            self.canvas.pack(fill=tk.BOTH, expand=True, before=self._kachel_feld)
            self._kachel_feld.destroy()
            self._kachel_feld = None
            self._kacheln = None
            self._kachel_original = None
            return None
        self._kacheln_anordnen()
        naechste = self._kacheln[min(i, len(self._kacheln) - 1)]
        self.canvas = naechste.canvas
        return naechste.dok

    # ---------------------------------------------------- drawing an inactive tile
    def _kachel_zeichnen(self, k):
        k.zeichnen_id = None
        if not self.kacheln_aktiv() or k not in self._kacheln or k.dok not in self._dokumente:
            return
        aktiv = self._dokumente[self._dok_aktiv]
        if k.dok is aktiv:
            if k.canvas is self.canvas:
                self.redraw(nur_ansicht=True)
            return
        self._dok_sichern(aktiv)
        extra = {a: getattr(self, a, None)
                 for a in ("canvas", "temp_ids", "_bild_live", "_modell_stand", "_vp_fang_cache")}
        for f in _STILL:
            setattr(self, f, lambda *a, **kw: None)
        try:
            self.canvas = k.canvas
            for a, wert in k.dok.zustand.items():
                setattr(self, a, wert)
            for v, wert in k.dok.variablen.items():
                var = getattr(self, v, None)
                if var is not None:
                    var.set(wert)
            p = self.projekt
            if p is not None and k.dok.blatt is not None and 0 <= k.dok.blatt < len(p.blaetter):
                p.aktiv = k.dok.blatt
            self.temp_ids = []
            self._modell_stand = None
            try:
                k.canvas.config(bg=self.bg_layout if self._ist_layout() else self.bg_modell)
            except tk.TclError:
                pass
            try:
                self.redraw()
            except Exception as ex:
                print(f"[KatieCAD] Kachel: {ex}")
            k.bild_live = self._bild_live
        finally:
            for f in _STILL:
                try:
                    delattr(self, f)
                except AttributeError:
                    pass
            for a, wert in aktiv.zustand.items():
                setattr(self, a, wert)
            for v, wert in aktiv.variablen.items():
                var = getattr(self, v, None)
                if var is not None:
                    var.set(wert)
            p = self.projekt
            if p is not None and aktiv.blatt is not None and 0 <= aktiv.blatt < len(p.blaetter):
                p.aktiv = aktiv.blatt
            for a, wert in extra.items():
                setattr(self, a, wert)
