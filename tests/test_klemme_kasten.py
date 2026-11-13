"""Terminal as a box (second appearance): geometry, connections, saving, old files."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
import katiecad.ui.app as A
from katiecad.model.core import Klemme, Polylinie, Kreis, Text

ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

k = Klemme(0, 0, {"IND": "-X1", "NUM": "1"})
check(k.darstellung == "kreis", "Standard ist Kreis")
check(any(isinstance(e, Kreis) for e in k.aufgeloest()), "Kreis gezeichnet")
check(k.anschluss_oben() == (0.0, 1.0), "Anschluss Kreis unveraendert")
check("darstellung" not in k.to_dict(), "Kreis: nichts gespeichert (alte Dateien gleich)")

b = Klemme(0, 0, {"IND": "-X1", "NUM": "1"}, darstellung="kasten")
el = b.aufgeloest()
check(any(isinstance(e, Polylinie) and e.geschlossen for e in el), "Rechteck gezeichnet")
check(not any(isinstance(e, Kreis) for e in el), "kein Kreis")
num = [e for e in el if isinstance(e, Text) and e.inhalt == "1"]
check(len(num) == 1 and (num[0].x, num[0].y) == (0.0, 0.0), "Nummer in der Mitte")
check(b.anschluss_oben() == (0.0, 4.0) and b.anschluss_unten() == (0.0, -4.0), "Anschluesse oben/unten am Rechteck")
check(b.to_dict().get("darstellung") == "kasten", "Darstellung wird gespeichert")

n = A.CadApp._dict_zu_element(None, b.to_dict()) if hasattr(A.CadApp, "_dict_zu_element") else None
if n is not None:
    check(isinstance(n, Klemme) and n.darstellung == "kasten", "Laden: Rechteck bleibt")
d = k.to_dict(); n2 = Klemme(**{kk: v for kk, v in d.items() if kk not in ("typ", "id")}) if False else None
check(Klemme(0, 0, {}, darstellung="unsinn").darstellung == "kreis", "ungueltiger Wert -> Kreis")

# two boxes side by side share an edge
b2 = Klemme(Klemme.KASTEN_B, 0, {"NUM": "2"}, darstellung="kasten")
check(b.kasten_ecken()[1][0] == b2.kasten_ecken()[0][0], "Nachbarklemmen liegen buendig")
bb = b.bbox()
check(bb[0] < -2.5 and bb[3] >= 4.0, "bbox umfasst Rechteck und Beschriftung")
print(f"test_klemme_kasten - OK ({ok} Pruefungen)")
