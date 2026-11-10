"""Cable ducts: geometry, fittings, 3D bodies, i18n parity, tool wiring (stubs only)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
from katiecad.model import core
from katiecad.common import i18n
from katiecad.ui import toolbar_dock as TD, icons

ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

# straight piece
k = core.Kabelkanal([(0, 0), (1000, 0)], breite=60, hoehe=40)
check(abs(k.laenge() - 1000) < 1e-6, "Laenge")
check(k.punkt_im_koerper(500, 20, 1) and not k.punkt_im_koerper(500, 50, 1), "Treffer")
check(core.KANAL_LAYER == "CD" and core.KANAL_LAYER_FARBE[0] == "#ff3030", "Layer CD rot")
d = k.to_dict(); d.pop("typ", None)
k2 = core.Kabelkanal(**d)
check(k2.breite == 60 and k2.hoehe == 40 and k2.art == "gerade", "Round-Trip")

# fittings
a = ((0, 0), (1000, 0), 60)
r = core.kanal_formstueck(a, ((1030, 0), (2000, 0), 60))
check(r and r["art"] == "verbinder", "Verbinder")
r = core.kanal_formstueck(a, ((1000, 30), (1000, 1000), 60))
check(r and r["art"] == "winkel" and len(r["punkte"]) == 4, "Winkel")
r = core.kanal_formstueck(((0, 0), (1000, 0), 60), ((500, 30), (500, 1000), 60))
check(r and r["art"] == "t", "T-Stueck")
check(core.kanal_formstueck(a, ((5000, 5000), (6000, 5000), 60)) is None, "zu weit")
w = core.Kabelkanal(r["punkte"], art="winkel", breite=60, hoehe=40)
check(w.art == "winkel" and w.laenge() >= 0, "Formstueck-Element")

# chain corners: butt joint, outer corner square
ks = core.kanal_kette([(0, 0), (1000, 0), (1000, 1000)], 60)
check(len(ks) == 2 and abs(ks[0][1][0] - 1030) < 1e-6 and abs(ks[1][0][1] + 30) < 1e-6, "Kette Ecke buendig")
check(len(core.kanal_kette([(0, 0), (1000, 0), (1000, 1000), (0, 1000)], 60, True)) == 4, "Kette geschlossen")
check(core.kanal_kette([(0, 0), (500, 0), (1000, 0)], 60)[0][1] == (500.0, 0.0), "gerade: keine Verlaengerung")

# drop of a toolbar between two others (by screen rectangle)
class _TB:
    def __init__(s, x): s.x = x
    def winfo_rootx(s): return s.x
    def winfo_rooty(s): return 0
    def winfo_width(s): return 100
    def winfo_height(s): return 30
class _A(TD.ToolbarDockMixin):
    def __init__(s):
        s._tb_reihe = ["werkzeug", "elektro", "3d", "bau"]
        s._tb_pos_werte = {n: "oben" for n in TD.LEISTEN}
        s.b = {"werkzeug": _TB(0), "elektro": _TB(100), "3d": _TB(200), "bau": _TB(300)}
    def _leiste(s, n): return s.b[n]
    def _toolbar_reihe_speichern(s): pass
_a = _A()
check(_a._leiste_ablegen("bau", 210, 10) and _a._tb_reihe == ["werkzeug", "elektro", "bau", "3d"], "Bau vor 3D ablegen")
_a = _A()
check(_a._leiste_ablegen("bau", 190, 10) and _a._tb_reihe == ["werkzeug", "elektro", "bau", "3d"], "Bau hinter Elektro ablegen")

# 3D body
prof = core.kanal_rechteck((0, 0), (1000, 0), 60)
b = core.Koerper3D("prisma", profil=prof, hoehe=40, kanal={"art": "gerade", "breite": 60})
p1, p2, br = core.kanal_aus_koerper(b)
check(abs(br - 60) < 1e-6 and abs(p2[0] - p1[0] - 1000) < 1e-6, "kanal_aus_koerper")
d = b.to_dict(); d.pop("typ", None)
check(core.Koerper3D(**d).kanal["art"] == "gerade", "3D Round-Trip")
check(core.kanal_aus_koerper(core.Koerper3D("prisma", profil=prof, hoehe=5)) is None, "kein Kanal")

# wiring
check(TD.LEISTEN == ("werkzeug", "bau", "elektro", "3d") and TD.LEISTEN_ATTR["bau"] == "tbB", "Leiste Bau")
check("kanal" in icons.NAMEN and "kanalverb" in icons.NAMEN, "Icons")
check(core.BEFEHLE["KANAL"] == "tool:kanal" and core.BEFEHLE["KANALVERBINDEN"] == "tool:kanalverb", "Befehle")

# i18n parity
keys = [s for s in i18n.TEXTE["de"] if "kanal" in s or s in ("tb.bau", "menu.ansicht.tb_bau")]
check(len(keys) >= 25, "Schluessel vorhanden")
for lang in ("en", "es"):
    check(all(s in i18n.TEXTE[lang] for s in keys), "i18n " + lang)
print("test_kanal - OK (%d Pruefungen)" % ok)
