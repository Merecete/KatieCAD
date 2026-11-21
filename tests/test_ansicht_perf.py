"""Zoom/pan: view changes are coalesced into one redraw and skip the model recalculation."""
import os, sys
from types import SimpleNamespace as NS
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
import katiecad.ui.app as A

ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

class Root:
    def __init__(s): s.q = {}; s.n = 0
    def after_idle(s, f): s.n += 1; s.q[s.n] = f; return s.n
    def after_cancel(s, i): s.q.pop(i, None)
    def laufen(s):
        for i in list(s.q): s.q.pop(i)()

def fake(layout=False):
    s = NS(root=Root(), aufrufe=[], _ansicht_wartet=None, _ist_layout=lambda: layout,
           elemente=[1, 2], layers={"0": 1}, raster=0)
    s.redraw = lambda nur_ansicht=False: s.aufrufe.append(nur_ansicht)
    s._zeichne_raster = lambda: setattr(s, "raster", s.raster + 1)
    s._ansicht_neuzeichnen = lambda: A.CadApp._ansicht_neuzeichnen(s)
    return s

s = fake()
for _ in range(50):
    A.CadApp._ansicht_planen(s)                   # 50 wheel / motion events
check(len(s.root.q) == 1, "viele Ereignisse -> nur ein geplantes Neuzeichnen")
check(s.aufrufe == [], "noch nicht gezeichnet")
s.root.laufen()
check(s.aufrufe == [True], "ein Neuzeichnen, nur Ansicht")
check(s._ansicht_wartet is None and s.raster == 0, "Zustand zurueckgesetzt, Raster nicht doppelt (Modell)")
A.CadApp._ansicht_planen(s)
A.CadApp._ansicht_sofort(s)
check(s.aufrufe == [True, True] and not s.root.q, "sofort: sofort gezeichnet, Planung abgebrochen")
A.CadApp._ansicht_sofort(s)
check(len(s.aufrufe) == 2, "nichts ausstehend -> kein Neuzeichnen")
sl = fake(True)
A.CadApp._ansicht_neuzeichnen(sl)
check(sl.raster == 1, "Layout: Blatt wird mitgezeichnet")
check(A.CadApp._modell_stand_jetzt(s) != A.CadApp._modell_stand_jetzt(NS(elemente=[1], layers={"0": 1}, _ist_layout=lambda: False)),
      "Modellstand erkennt geaenderte Elementzahl")
print(f"test_ansicht_perf - OK ({ok} Pruefungen)")
