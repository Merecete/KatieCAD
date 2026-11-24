import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
import katiecad.common.i18n as I; I.SPRACHE["aktuell"] = "de"
from katiecad.ui import toolbar_dock as TD
ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

# --- pure helpers
check(TD.ziel_position(0.05, 0.5) == "links" and TD.ziel_position(0.05, 0.05) == "oben"
      and TD.ziel_position(0.95, 0.5) == "rechts" and TD.ziel_position(0.5, 0.5, "links") == "links", "Zielposition links")
check("links" in TD.POSITIONEN and TD.VERTIKAL == ("links", "rechts"), "Positionen")

# --- fakes
class W:
    def __init__(s, name="w", kinder=0):
        s.name, s.m, s.kinder, s.bindings = name, None, [], {}
        for i in range(kinder):
            s.kinder.append(W(f"{name}.{i}"))
    def winfo_children(s): return list(s.kinder)
    def winfo_manager(s): return s.m or ""
    def pack_info(s): return {"side": "left"}
    def pack_forget(s): s.m = None
    def grid_forget(s): s.m = None
    def pack(s, **kw): s.m = "pack"; s.opt = kw
    def grid(s, **kw): s.m = "grid"; s.opt = kw
    def tkraise(s): pass
    def winfo_reqwidth(s): return 200
    def winfo_width(s): return 1000
    def winfo_height(s): return 800
    def winfo_rootx(s): return 0
    def winfo_rooty(s): return 0
    def bind(s, ev, fn, add=None): s.bindings[ev] = fn
    def update_idletasks(s): pass
    def after(s, *a): return 1

store = {}
TD.lade_konfiguration = lambda: dict(store)
def _speichern(cfg): store.clear(); store.update(cfg)
TD.speichere_konfiguration = _speichern

class Menu:
    gebaut = []
    def __init__(s, *a, **k): s.eintraege = []; Menu.gebaut.append(s)
    def add_command(s, **k): s.eintraege.append(k.get("label"))
    def add_separator(s): s.eintraege.append("-")
    def index(s, i): return len(s.eintraege) - 1 if s.eintraege else None
TD.tk.Menu = Menu
class Var:
    def __init__(s, value=None): s.v = value
    def set(s, v): s.v = v
    def get(s): return s.v
TD.tk.BooleanVar = Var
TD.ttk.Frame = lambda *a, **k: W("frame")
class Btn(W):
    def __init__(s, *a, **k): super().__init__("btn"); s.cmd = k.get("command")
TD.ttk.Button = Btn

class App(TD.ToolbarDockMixin):
    def __init__(s):
        s.root = W("root")
        s.tb1, s.tbB, s.tbE, s.tbD = (W(n, 3) for n in ("tb1", "tbB", "tbE", "tbD"))
        s.tb2 = W("tb2")
        s._koord_bar = W("koord")
        s._tab_leiste = W("tabs")
        s.gezeigt = []
        s.status = type("S", (), {"set": lambda self, t: setattr(s, "msg", t)})()
    def _menue_zeigen(s, m, x, y): s.gezeigt.append(m)

a = App()
check(all(a.toolbar_sichtbar(n) for n in TD.LEISTEN), "am Anfang alles sichtbar")
a._toolbar_anordnen()
check(a.tbB.m is not None and a._zone("oben").m == "pack", "angeordnet")
# hide one bar
a.toolbar_sichtbar_setzen("bau", False)
check(not a.toolbar_sichtbar("bau") and store["toolbar_aus"] == ["bau"], "Bau ausgeblendet und gespeichert")
check(a.tbB.m is None and all(c.m is None for c in a.tbB.winfo_children()), "Bau nicht mehr im Layout")
check(a.tb1.m is not None, "andere bleiben")
# restore
a.toolbar_sichtbar_setzen("bau", True)
check(a.toolbar_sichtbar("bau") and store["toolbar_aus"] == [] and a.tbB.m is not None, "Bau wieder da")
# hide everything: the way back stays
for n in TD.LEISTEN:
    a.toolbar_sichtbar_setzen(n, False)
check(all(not a.toolbar_sichtbar(n) for n in TD.LEISTEN), "alles aus")
check(a._tb_notleiste is not None and a._tb_notleiste.m == "grid" and a._zone("oben").m == "pack",
      "Notleiste bleibt sichtbar, wenn alle Leisten aus sind")
# right click menu offers everything
a.toolbar_menue_zeigen("", 10, 10)
m = a.gezeigt[-1]
check(sum(1 for e in m.eintraege if e and "einblenden" in e) >= 5, "Menue: alle Leisten einblendbar + alle")
# show one -> notleiste away
a.toolbar_sichtbar_setzen("werkzeug", True)
check(a._tb_notleiste.m is None and a.tb1.m is not None, "Notleiste weg, sobald eine Leiste sichtbar ist")
# all back via menu command
a.toolbar_alle_einblenden()
check(all(a.toolbar_sichtbar(n) for n in TD.LEISTEN) and store["toolbar_aus"] == [], "Alle einblenden")
# context menu of a visible bar contains 'hide'
a.toolbar_menue_zeigen("elektro", 1, 1)
check(any(e and "ausblenden" in e for e in a.gezeigt[-1].eintraege), "Menue: ausblenden")
# left docking
a.toolbar_position_setzen("links", "3d")
check(a.toolbar_position("3d") == "links" and a._zone("links").m == "pack"
      and a._zone("links").opt["before"] is a._tab_leiste, "Leiste links neben der Seitenleiste")
check(store["toolbar_pos_3d"] == "links", "Position gespeichert")
# default layout
a.toolbar_sichtbar_setzen("bau", False)
a.toolbar_standard()
check(all(a.toolbar_position(n) == "oben" for n in TD.LEISTEN) and all(a.toolbar_sichtbar(n) for n in TD.LEISTEN)
      and a.toolbar_reihenfolge() == list(TD.LEISTEN), "Standardanordnung")
# right-click bindings
a._toolbar_rechtsklick_binden(a.tbB, "bau")
ev = f"<ButtonRelease-{TD.BTN_RECHTS}>"
check(ev in a.tbB.bindings and all(ev in c.bindings for c in a.tbB.kinder), "Rechtsklick auf Leiste und Symbole")
class E: x_root = 5; y_root = 6
n0 = len(a.gezeigt)
check(a.tbB.bindings[ev](E()) == "break" and len(a.gezeigt) == n0 + 1, "Rechtsklick oeffnet das Menue")
# persisted hidden state is read at start
store["toolbar_aus"] = ["elektro", "unsinn"]
b = App()
check(not b.toolbar_sichtbar("elektro") and b.toolbar_sichtbar("bau"), "Start: gespeicherter Zustand")
for sp in ("de", "en", "es", "fr"):
    for k in ("menu.ansicht.tb_links", "menu.ansicht.tb_anzeigen", "menu.ansicht.tb_alle", "menu.ansicht.tb_standard",
              "tb.ausblenden", "tb.einblenden_n", "tb.einblenden", "msg.tb.ausgeblendet"):
        check(I.TEXTE[sp].get(k), f"i18n {k} {sp}")
print("test_leisten OK", ok)
