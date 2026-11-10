"""Model grid: major lines every 5th line from the origin at every zoom / offset."""
import sys, os, types
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
import katiecad.ui.app as A

ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

class V:
    def __init__(s, v): s.v = v
    def get(s): return s.v
class Cv:
    def __init__(s): s.l = []
    def delete(s, *a): pass
    def winfo_width(s): return 1200
    def winfo_height(s): return 700
    def create_line(s, *a, **k): s.l.append((a, k))
    def create_oval(s, *a, **k): s.l.append(("O", a, k))
    def tag_lower(s, *a): pass

def lauf(zoom, ox, oy, raster=5.0, punkt=False, farbe=None):
    a = types.SimpleNamespace(canvas=Cv(), raster_sichtbar=V(True), raster_punktiert=V(punkt),
                              view={"zoom": zoom, "ox": ox, "oy": oy}, bg_modell="#ffffff",
                              raster_mm=raster, _ist_layout=lambda: False, raster_farbe=farbe)
    a._raster_farben = lambda: A.CadApp._raster_farben(a)
    a._zahl = lambda x, d: x
    A.CadApp._zeichne_raster(a)
    return a.canvas.l

for zoom in (0.5, 1.0, 1.37, 2.0, 3.3, 7.77, 10.0):
    for ox, oy in ((100.0, 300.5), (-333.3, 123.7), (0.0, 0.0)):
        l = lauf(zoom, ox, oy)
        step = 5.0 * zoom
        while step < 12: step *= 5
        senkr = [(a[0], k["width"]) for a, k in l if a[0] == a[2] and k["width"] in (1, 2)]
        for x, wdt in senkr:
            i = round((x - ox) / step)
            check((wdt == 2) == (i % 5 == 0), "Hauptlinie jede 5. Linie (zoom %s ox %s x %s)" % (zoom, ox, x))
        gross = sorted({x for x, wdt in senkr if wdt == 2 and 0 <= x <= 1200})
        abst = {round(b - a_) for a_, b in zip(gross, gross[1:])}
        check(len(abst) <= 2 and (not abst or max(abst) - min(abst) <= 1), "gleiche Abstaende der Hauptlinien zoom %s" % zoom)
l = lauf(2.0, 50, 50, punkt=True)
check(sum(1 for x in l if x[0] == "O") > 10 and len(l) - sum(1 for x in l if x[0] == "O") == 2, "punktiertes Raster: Punkte + 2 Achsen")
# grid colour: default unchanged, chosen colour mixed with the background
fl = {k["fill"] for a, k in lauf(2.0, 50, 50) if "fill" in k}
check("#c8c8c8" in fl and "#909090" in fl, "Standard-Rasterfarben unveraendert")
fr = {k["fill"] for a, k in lauf(2.0, 50, 50, farbe="#d14d4d") if "fill" in k}
check("#c8c8c8" not in fr and len(fr) >= 3, "gewaehlte Rasterfarbe")
from katiecad.model import core as _c
check(_c.farbe_mischen("#000000", "#ffffff", 0.5) == "#808080" and _c.farbe_mischen("#102030", "#102030", 0.7) == "#102030", "farbe_mischen")
check(len(_c.RASTER_PRESETS) == 8, "Raster-Vorgaben")
from katiecad.common import i18n
for lang in ("de", "en", "es"):
    check(all(("dlg.rasterfarbe.preset_%d" % i) in i18n.TEXTE[lang] for i in range(8)) and all(k in i18n.TEXTE[lang] for k in ("dlg.farbe.eigene", "tb.rasterfarbe", "menu.ansicht.rasterfarbe", "menu.ansicht.rasterfarbe_std", "dlg.rasterfarbe.standard")), "i18n Rasterfarbe " + lang)
print(f"test_raster - OK ({ok} Pruefungen)")
