"""Culling of large drawings: elements outside the view / smaller than a pixel are not drawn."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
import katiecad.ui.app as A
from katiecad.model.core import Linie, Kreis, Polylinie, Text, Wand, Kabelkanal

ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

fenster = (0.0, 0.0, 1000.0, 1000.0, 1.0)         # visible area in mm, zoom 1 px/mm
aus = A.CadApp._ausserhalb
check(not aus(Linie(10, 10, 100, 100), fenster), "Linie sichtbar")
check(aus(Linie(2000, 2000, 2100, 2100), fenster), "Linie ausserhalb")
check(not aus(Linie(-50, 500, 50, 500), fenster), "Linie ragt herein")
check(aus(Linie(500, 500, 500.2, 500.2), fenster), "winzige Linie")
check(not aus(Linie(500, 500, 500.2, 500.2), (0, 0, 1000, 1000, 100.0)), "gleiche Linie bei starkem Zoom sichtbar")
check(aus(Kreis(5000, 5000, 10), fenster), "Kreis ausserhalb")
check(not aus(Kreis(500, 500, 10), fenster), "Kreis sichtbar")
check(aus(Polylinie([(3000, 0), (3100, 50)]), fenster), "Polylinie ausserhalb")
check(not aus(Polylinie([(10, 10), (50, 80)]), fenster), "Polylinie sichtbar")
# a tiny text is not culled by size (only by position)
t = Text(500, 500, "x", 0.1)
check(not aus(t, fenster), "kleiner Text sichtbar")
check(aus(Text(9000, 9000, "x", 5), fenster), "Text ausserhalb")
# walls and ducts are always drawn
check(not aus(Wand([(5000, 5000), (5100, 5000)]), fenster), "Wand nie ausgeblendet")
check(not aus(Kabelkanal([(5000, 5000), (5100, 5000)]), fenster), "Kanal nie ausgeblendet")
check(A.KULL_AB >= 100, "Schwelle")
print(f"test_kull - OK ({ok} Pruefungen)")
