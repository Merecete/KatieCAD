# -*- coding: utf-8 -*-
"""Draw order: reihenfolge_aendern (front / back / one step), selection order kept."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
from katiecad.ui.app import CadApp

f = CadApp.reihenfolge_aendern


def check(c, m):
    assert c, "FEHLER: " + m


a, b, c, d, e = "a", "b", "c", "d", "e"
l = [a, b, c, d, e]
check(f(l, [b, d], "vorn") and l == [a, c, e, b, d], "vorn")
l = [a, b, c, d, e]
check(f(l, [b, d], "hinten") and l == [b, d, a, c, e], "hinten")
l = [a, b, c, d, e]
check(f(l, [b], "vor") and l == [a, c, b, d, e], "eine Ebene vor")
l = [a, b, c, d, e]
check(f(l, [b, c], "vor") and l == [a, d, b, c, e], "Gruppe vor")
l = [a, b, c, d, e]
check(f(l, [d], "zurueck") and l == [a, b, d, c, e], "eine Ebene zurueck")
l = [a, b, c, d, e]
check(not f(l, [e], "vorn") and l == [a, b, c, d, e], "schon vorn")
check(not f(l, [a], "hinten"), "schon hinten")
check(not f(l, [e], "vor") and not f(l, [a], "zurueck"), "Rand")
l = [a, b, c, d, e]
check(f(l, [d, e], "zurueck") and l == [a, b, d, e, c], "Gruppe am Rand zurueck")
print("OK test_reihenfolge")
