# -*- coding: utf-8 -*-
"""
katiecad/ui/tabs.py - several drawings in one window as tabs (BSD-3-Clause).

The program logic works on ONE drawing (self.elemente, self.layers, ...). Every tab is a
`Dokument` that keeps exactly that state; switching tabs ends a running tool action, stores
the state of the old tab and puts the state of the new one in place - all tools, dialogs
and menus then work unchanged on the drawing that is shown.

A tab holds a single drawing (file or untitled) or one sheet of a project; several sheets
of the same project can be open in tabs (they share the project object, each tab its sheet).
The tab bar above the drawing area appears as soon as more than one drawing is open.
"""

import os
import tkinter as tk

from katiecad.common.i18n import tr
from katiecad.common import fenster as FENSTER
from katiecad.model.core import FARBEN
from katiecad.ui.kacheln import KachelnMixin

# attributes of the program that belong to the drawing shown (taken along by the tab)
DOK_ATTRIBUTE = ("elemente", "layers", "layouts", "aktives_layout", "view_modell", "auswahl",
                 "_undo_stack", "_redo_stack", "_undo_pro_blatt", "_dirty", "_datei_pfad",
                 "projekt", "_gesperrtes_blatt", "_aktiver_viewport", "_3d_state",
                 "_qv_cache", "_ge_cache")
# tk variables of the drawing (their values are taken along)
DOK_VARIABLEN = ("ansicht", "einheit", "massstab", "raster_mm", "fang_mm", "aktiver_layer")


class Dokument:
    _zaehler = 0

    def __init__(self):
        Dokument._zaehler += 1
        self.nr = Dokument._zaehler          # for "Untitled n"
        self.zustand = {}
        self.variablen = {}
        self.blatt = None                    # project sheet of this tab (index)


class TabsMixin(KachelnMixin):
    # ---------------------------------------------------- set-up
    def _tabs_init(self):
        self._dokumente = [Dokument()]
        self._dok_aktiv = 0
        self._tab_leiste = None
        self._tab_wechsel_laeuft = False
        self._kacheln_init()                 # drawings side by side (ui/kacheln.py)

    def _tabs_da(self):
        return hasattr(self, "_dokumente")

    # ---------------------------------------------------- state of a drawing
    def _dok_sichern(self, dok):
        dok.zustand = {a: getattr(self, a, None) for a in DOK_ATTRIBUTE}
        dok.variablen = {}
        for v in DOK_VARIABLEN:
            var = getattr(self, v, None)
            if var is not None:
                try:
                    dok.variablen[v] = var.get()
                except tk.TclError:
                    pass
        p = self.projekt
        dok.blatt = p.aktiv if p is not None else None

    def _dok_einsetzen(self, dok):
        for a, wert in dok.zustand.items():
            setattr(self, a, wert)
        for v, wert in dok.variablen.items():
            var = getattr(self, v, None)
            if var is not None:
                var.set(wert)
        p = self.projekt
        if p is not None and dok.blatt is not None and 0 <= dok.blatt < len(p.blaetter):
            p.aktiv = dok.blatt
        self._modell_stand = None                   # the model caches belong to the drawing
        self._ansicht_neu_aufbauen()

    def _ansicht_neu_aufbauen(self):
        """The visible parts after the drawing changed (as after loading a file)."""
        try:
            self.layer_cb.config(values=list(self.layers.keys()))
            if self.aktiver_layer.get() not in self.layers:
                self.aktiver_layer.set("0")
        except (AttributeError, tk.TclError):
            pass
        bg = self.bg_modell if not self._ist_layout() else self.bg_layout
        try:
            self.canvas.config(bg=bg)
            self.bg_btn.config(bg=bg)
        except (AttributeError, tk.TclError):
            pass
        for f in ("_layout_switcher_neu_aufbauen", "_update_kontext_widgets", "redraw",
                  "_zeichne_raster", "_viewport_modus_anzeige_aktualisieren",
                  "_layer_info_aktualisieren", "_aktualisiere_undo_redo", "_update_titel",
                  "_3d_anzeige_nachziehen"):
            try:
                getattr(self, f)()
            except Exception as e:
                print(f"[KatieCAD] Tab: {f}: {e}")
        try:
            self.seitenleiste.aktualisieren()
        except Exception:
            pass

    def _aktionen_beenden(self, drei_d=True):
        """Ends whatever tool action is running before the drawing is exchanged
        (drei_d=False: an open 3D view stays - a tile keeps its 3D view)."""
        try:
            self._paste_abbrechen()
        except Exception:
            pass
        for _ in range(4):
            try:
                self._escape()
            except Exception:
                break
        try:
            if drei_d and self.ansicht3d_aktiv():
                self.ansicht3d_setzen(False)
        except Exception:
            pass
        try:
            if self.aktives_werkzeug.get() != "auswahl":
                self.aktives_werkzeug.set("auswahl")
                self._werkzeug_gewechselt()
        except Exception:
            pass

    # ---------------------------------------------------- tabs
    def tab_aktivieren(self, index):
        if not self._tabs_da() or not (0 <= index < len(self._dokumente)) \
                or index == self._dok_aktiv or self._tab_wechsel_laeuft:
            return
        self._tab_wechsel_laeuft = True
        try:
            self._aktionen_beenden(drei_d=not self.kacheln_aktiv())
            self._dok_sichern(self._dokumente[self._dok_aktiv])
            if self.kacheln_aktiv():
                self._kachel_wechsel(self._dokumente[index])
            self._dok_aktiv = index
            self._dok_einsetzen(self._dokumente[index])
        finally:
            self._tab_wechsel_laeuft = False
        self._tab_leiste_zeichnen()

    def _tab_unberuehrt(self):
        """True if the current tab is an empty, untouched, untitled drawing (it is reused
        when a file is opened, like a single window would be)."""
        return (not self.elemente and not self._dirty and not self._datei_pfad
                and self.projekt is None
                and not any(getattr(l, "elemente", None) for l in self.layouts))

    def tab_neu(self):
        """Opens a new tab with an empty drawing and makes it the current one."""
        if not self._tabs_da():
            return
        self._aktionen_beenden(drei_d=not self.kacheln_aktiv())
        self._dok_sichern(self._dokumente[self._dok_aktiv])
        dok = Dokument()
        self._dokumente.insert(self._dok_aktiv + 1, dok)
        self._dok_aktiv += 1
        if self.kacheln_aktiv():
            self._kachel_neues_dok(dok)
        # fresh state: new objects - nothing may be shared with the other tab
        self.projekt = None
        self._undo_pro_blatt = {}
        self._gesperrtes_blatt = None
        self._datei_pfad = None
        self._aktiver_viewport = None
        self._3d_state = None
        self._qv_cache, self._ge_cache = {}, {}
        self.view_modell = {"zoom": 1.5, "ox": 100, "oy": 700}
        self.auswahl = []
        self._undo_stack, self._redo_stack = [], []
        self._zeichnung_anwenden(self._leere_zeichnung_daten(einstellungen_uebernehmen=False),
                                 layer_zuruecksetzen=True)
        self._undo_reset()
        self._mark_clean()
        try:
            self.seitenleiste.aktualisieren()
        except Exception:
            pass
        self._tab_leiste_zeichnen()

    def _tab_vorbereiten(self):
        """Before a file / project is opened: a new tab unless the current one is unused.
        -> True if a new tab was opened."""
        if not self._tabs_da() or self._tab_unberuehrt():
            return False
        self.tab_neu()
        return True

    def tab_schliessen(self, index=None, fragen=True):
        """Closes a tab (asks about unsaved changes). -> False if cancelled."""
        if not self._tabs_da():
            return False
        if index is None:
            index = self._dok_aktiv
        if index != self._dok_aktiv:
            self.tab_aktivieren(index)
        if fragen and self._dirty and not self._projekt_aenderungen_klaeren("schliessen"):
            return False
        FENSTER.freigeben(getattr(self, "_gesperrtes_blatt", None))
        self._gesperrtes_blatt = None
        if len(self._dokumente) == 1:            # last tab: becomes an empty drawing
            del self._dokumente[0]
            self._dokumente = [Dokument()]
            self._dok_aktiv = 0
            self.projekt = None
            self._undo_pro_blatt = {}
            self._datei_pfad = None
            self._zeichnung_anwenden(self._leere_zeichnung_daten(einstellungen_uebernehmen=False),
                                     layer_zuruecksetzen=True)
            self._undo_reset()
            self._mark_clean()
            self._ansicht_neu_aufbauen()
            self._tab_leiste_zeichnen()
            return True
        self._aktionen_beenden()
        weg = self._dokumente.pop(self._dok_aktiv)
        naechste = self._kachel_dok_weg(weg) if self.kacheln_aktiv() else None
        if naechste is not None:
            neu = self._dokumente.index(naechste)
        else:
            neu = min(self._dok_aktiv, len(self._dokumente) - 1)
        self._dok_aktiv = neu
        self._dok_einsetzen(self._dokumente[neu])
        self._tab_leiste_zeichnen()
        return True

    def tabs_andere_schliessen(self, index):
        self.tab_aktivieren(index)
        behalten = self._dokumente[self._dok_aktiv]
        for dok in list(self._dokumente):
            if dok is behalten:
                continue
            if not self.tab_schliessen(self._dokumente.index(dok)):
                return
        if behalten in self._dokumente:
            self.tab_aktivieren(self._dokumente.index(behalten))

    def tabs_alle_klaeren(self):
        """Before quitting: asks for every changed tab. -> False if cancelled."""
        if not self._tabs_da():
            return True
        for i in range(len(self._dokumente)):
            dok = self._dokumente[i]
            geaendert = self._dirty if i == self._dok_aktiv else dok.zustand.get("_dirty")
            if not geaendert:
                continue
            self.tab_aktivieren(i)
            if not self._projekt_aenderungen_klaeren("beenden"):
                return False
            self._dirty = False                    # "No" = discard: no second question
        return True

    def tabs_sperren_freigeben(self):
        if not self._tabs_da():
            return
        for i, dok in enumerate(self._dokumente):
            pfad = self._gesperrtes_blatt if i == self._dok_aktiv else dok.zustand.get("_gesperrtes_blatt")
            FENSTER.freigeben(pfad)

    def tab_wechsel_naechster(self, richtung=1):
        if self._tabs_da() and len(self._dokumente) > 1:
            self.tab_aktivieren((self._dok_aktiv + richtung) % len(self._dokumente))
        return "break"

    # ---------------------------------------------------- finding open drawings
    def _tab_mit_datei(self, pfad):
        pfad = os.path.normcase(os.path.abspath(pfad))
        for i, dok in enumerate(self._dokumente):
            d = self._datei_pfad if i == self._dok_aktiv else dok.zustand.get("_datei_pfad")
            p = self.projekt if i == self._dok_aktiv else dok.zustand.get("projekt")
            if d and p is None and os.path.normcase(os.path.abspath(d)) == pfad:
                return i
        return None

    def _tab_mit_blatt(self, projekt, blatt_datei):
        for i, dok in enumerate(self._dokumente):
            p = self.projekt if i == self._dok_aktiv else dok.zustand.get("projekt")
            b = (p.aktiv if i == self._dok_aktiv else dok.blatt) if p is not None else None
            if p is not None and b is not None and 0 <= b < len(p.blaetter) \
                    and os.path.normcase(p.projektdatei) == os.path.normcase(projekt.projektdatei) \
                    and p.blaetter[b].datei == blatt_datei:
                return i
        return None

    def blatt_in_neuem_tab(self, index):
        """Opens sheet `index` of the current project in a new tab (or shows the tab that
        has it already)."""
        p = self.projekt
        if p is None or not (0 <= index < len(p.blaetter)):
            return
        schon = self._tab_mit_blatt(p, p.blaetter[index].datei)
        if schon is not None:
            self.tab_aktivieren(schon)
            return
        if FENSTER.gesperrt_von(p.blatt_pfad(index)):
            from katiecad.ui import meldung as messagebox
            messagebox.showinfo(tr("msg.projekt.titel"),
                                tr("msg.fenster.gesperrt", name=p.blaetter[index].name),
                                parent=self.root)
            return
        aktiv_vorher = p.aktiv
        self.tab_neu()
        # the new tab shares the project object; the other tab keeps its own sheet
        self._dokumente[self._dok_aktiv - 1].blatt = aktiv_vorher
        self.projekt = p
        self._einpolig_sync()
        self._undo_pro_blatt = {}
        self._blatt_laden(index)
        self._tab_leiste_zeichnen()

    # ---------------------------------------------------- the tab bar
    def _tab_titel(self, i):
        aktiv = i == self._dok_aktiv
        dok = self._dokumente[i]
        z = dok.zustand
        p = self.projekt if aktiv else z.get("projekt")
        datei = self._datei_pfad if aktiv else z.get("_datei_pfad")
        dirty = self._dirty if aktiv else z.get("_dirty")
        if p is not None:
            b = p.aktiv if aktiv else dok.blatt
            if b is not None and 0 <= b < len(p.blaetter):
                text = f"{p.name} – {p.nummer(b)} {p.blaetter[b].name}"
            else:
                text = p.name
        elif datei:
            text = os.path.splitext(os.path.basename(datei))[0]
        else:
            text = tr("tabs.unbenannt", n=dok.nr)
        return text + (" *" if dirty else "")

    def _tab_leiste_zeichnen(self):
        if not self._tabs_da():
            return
        self._kacheln_var_setzen()             # check mark in the View menu
        zeigen = len(self._dokumente) > 1
        leiste = self._tab_leiste
        if not zeigen:
            if leiste is not None:
                leiste.destroy()
                self._tab_leiste = None
            return
        if leiste is None:
            leiste = tk.Frame(self.root, bg=FARBEN["bg_dunkel"], bd=0, highlightthickness=0)
            ziel = self._zeichenflaeche()
            leiste.pack(side=tk.TOP, fill=tk.X, before=ziel)
            self._tab_leiste = leiste
        for w in leiste.winfo_children():
            w.destroy()
        schrift = ("Segoe UI", 9)
        for i in range(len(self._dokumente)):
            aktiv = i == self._dok_aktiv
            bg = FARBEN["bg_mittel"] if aktiv else FARBEN["bg_dunkel"]
            fg = FARBEN["text_hell"] if aktiv else FARBEN["text_dim"]
            tab = tk.Frame(leiste, bg=bg, highlightthickness=1,
                           highlightbackground=FARBEN["cyan"] if aktiv else FARBEN["rand"])
            tab.pack(side=tk.LEFT, padx=(4 if i == 0 else 0, 2), pady=(4, 0))
            text = tk.Label(tab, text=self._tab_titel(i), bg=bg, fg=fg, font=schrift,
                            padx=10, pady=3, cursor="hand2")
            text.pack(side=tk.LEFT)
            zu = tk.Label(tab, text="✕", bg=bg, fg=fg, font=schrift, padx=6, pady=3,
                          cursor="hand2")
            zu.pack(side=tk.LEFT)
            for w in (tab, text):
                w.bind("<Button-1>", lambda e, i=i: self.tab_aktivieren(i))
                w.bind("<Button-2>", lambda e, i=i: self.tab_schliessen(i))
                w.bind("<Button-3>", lambda e, i=i: self._tab_kontextmenue(e, i))
            zu.bind("<Button-1>", lambda e, i=i: self.tab_schliessen(i))
            zu.bind("<Enter>", lambda e, w=zu: w.config(fg=FARBEN["rot"]))
            zu.bind("<Leave>", lambda e, w=zu, f=fg: w.config(fg=f))
        self._kacheln_koepfe()

    def _tab_kontextmenue(self, event, index):
        m = tk.Menu(self.root, tearoff=0, bg=FARBEN["bg_mittel"], fg=FARBEN["cyan"],
                    activebackground=FARBEN["cyan"], activeforeground=FARBEN["bg_dunkel"])
        m.add_command(label=tr("tabs.schliessen"), command=lambda: self.tab_schliessen(index))
        m.add_command(label=tr("tabs.andere_schliessen"),
                      command=lambda: self.tabs_andere_schliessen(index))
        m.add_separator()
        if self.kacheln_aktiv():
            m.add_command(label=tr("tabs.als_tabs"), command=self.kacheln_aus)
            m.add_command(label=tr("tabs.breiten_gleich"), command=self._kacheln_gleich)
        else:
            m.add_command(label=tr("tabs.kacheln"), command=self.kacheln_an)
        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()
