"""Block variants (like EPLAN): definition, instance, save/load, switching."""
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
import katiecad.ui.app as A
import katiecad.model.core as core
from katiecad.model.blocks import block_speichern, block_laden

ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

a = A.CadApp.__new__(A.CadApp)

def var(textpos):
    return [core.Kreis(0, 0, 5), core.AttributDefinition(*textpos, tag="IND", wert="X")]

d = core.BlockDefinition("Steckdose", (0, 0), var((8, 0)))
check(d.varianten == [] and len(d.variante_liste()) == 1, "ohne Varianten: eine")
check(d.variante_hinzufuegen("", var((0, 8))) == "B", "automatischer Name B")
d.variante_hinzufuegen("C", var((-8, 0)))
check([n for n, _ in d.variante_liste()] == ["A", "B", "C"], "drei Varianten")
d.variante_hinzufuegen("B", var((0, -8)))
check(len(d.variante_liste()) == 3, "gleicher Name ersetzt")

pfad = os.path.join(tempfile.mkdtemp(), "x.katieblock")
block_speichern(pfad, d)
d2 = block_laden(pfad, a._dict_zu_element)
check([n for n, _ in d2.variante_liste()] == ["A", "B", "C"], "Speichern/Laden: Varianten bleiben")
check(d2.elemente is d2.varianten[0][1], "elemente = erste Variante")

ref = core.BlockReferenz(100, 50, "Steckdose", d2.elemente, varianten=d2.varianten)
ref.setze_attribute({"IND": "XD1"})
def textpos(r):
    return [(round(t.x), round(t.y)) for t in r.aufgeloest() if isinstance(t, core.Text)][0]
check(textpos(ref) == (108, 50), "Variante A: Text rechts")
check(ref.setze_variante(2) and textpos(ref) == (92, 50), "Variante C: Text links")
check(ref.attribute["IND"] == "XD1", "Attributwert bleibt beim Wechsel")
check(not ref.setze_variante(2) and not ref.setze_variante(9), "ungueltiger Wechsel")

# Instanz speichern / laden
dd = ref.to_dict()
dd = dict(dd)
kinder = [a._dict_zu_element(k) for k in dd["elemente"]]
check(dd["variante"] == 2 and len(dd["varianten"]) == 3, "Instanz-Dict")
ref2 = a._dict_zu_element(dict(dd, typ="block"))
check(isinstance(ref2, core.BlockReferenz) and ref2.variante == 2 and len(ref2.varianten) == 3,
      "Instanz laden")
check(textpos(ref2) == (92, 50), "geladene Instanz zeigt Variante C")

# zusaetzlich gedreht: Text bleibt lesbar
ref.winkel = 180
t = [t for t in ref.aufgeloest() if isinstance(t, core.Text)][0]
check(abs(t.winkel) < 1e-6 or abs(t.winkel - 360) < 1e-6, "Drehung 180: Text nicht auf dem Kopf")

# Block ohne Varianten bleibt wie bisher
r0 = core.BlockReferenz(0, 0, "K", [core.Kreis(0, 0, 5)])
check("varianten" not in r0.to_dict() and not r0.setze_variante(1), "ohne Varianten unveraendert")
print(f"test_varianten - OK ({ok} Pruefungen)")
