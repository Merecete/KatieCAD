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

# alignment: line = left / right edge of the duct
vl = core.kanal_versatz([(0, 0), (1000, 0), (1000, 1000)], "links", 60)
vr = core.kanal_versatz([(0, 0), (1000, 0), (1000, 1000)], "rechts", 60)
check(abs(vl[0][1] + 30) < 1e-6 and abs(vl[1][0] - 1030) < 1e-6 and abs(vl[1][1] + 30) < 1e-6, "Versatz links (Linie = linke Kante)")
check(abs(vr[0][1] - 30) < 1e-6 and abs(vr[1][0] - 970) < 1e-6, "Versatz rechts")
check(core.kanal_versatz([(0, 0), (5, 5)], "mitte", 60) == [(0.0, 0.0), (5.0, 5.0)], "Versatz mitte")
for lang in ("de", "en", "es"):
    check(all(("dlg.kanal.ausr." + a) in i18n.TEXTE[lang] for a in ("mitte", "links", "rechts")), "i18n Ausrichtung " + lang)

# duct hatch
kh = core.Kabelkanal([(0, 0), (1000, 0)], breite=60, schraffur="schraeg", schraffur_abstand=20)
n0 = len(core.Kabelkanal([(0, 0), (1000, 0)], breite=60).prims())
check(n0 == 1 and len(kh.prims()) > 30, "Kanal Schraffur schraeg")
check(len(core.Kabelkanal([(0, 0), (1000, 0)], breite=60, schraffur="kreuz").prims()) > len(core.Kabelkanal([(0, 0), (1000, 0)], breite=60, schraffur="schraeg").prims()), "Kreuzschraffur")
check(len(core.Kabelkanal([(0, 0), (1000, 0)], breite=60, schraffur="voll").flaechen()) == 1 and not core.Kabelkanal([(0, 0), (1000, 0)], breite=60).flaechen(), "Vollflaeche")
check(len(kh.prims(schraffur=False)) == 1, "ohne Schraffur fuer Fang")
dh = kh.to_dict(); dh.pop("typ", None)
check(core.Kabelkanal(**dh).schraffur == "schraeg" and core.Kabelkanal(**dh).schraffur_abstand == 20, "Schraffur Round-Trip")
tstk = core.kanal_formstueck(((0, 0), (1000, 0), 60), ((500, 30), (500, 1000), 60))
th = core.Kabelkanal(tstk["punkte"], art="t", breite=60, schraffur="schraeg", schraffur_abstand=10)
check(len(th.prims()) > 5, "T-Stueck schraffiert (nicht konvex)")
hl = core.polygon_schraffur([(0, 0), (100, 0), (100, 100), (0, 100)], [45.0], 20)
check(len(hl) >= 7 and any(abs(l[0][0] - l[0][1]) < 1e-6 for l in hl) and all(abs(p[0]) <= 100.001 and abs(p[1]) <= 100.001 for l in hl for p in l), "polygon_schraffur im Rechteck")

# wall opening (breakthrough): gap in the wall, only reveals
wd = core.Wand([(0, 0), (4000, 0)], dicke=240)
od = core.Oeffnung("durchbruch", 2000, 0, 0, breite=600)
check(od.art == "durchbruch" and len(od.prims()) == 2, "Durchbruch nur Laibungen")
of = core.Oeffnung("fenster", 1000, 0, 0)
check(len(of.prims()) == 4, "Fenster unveraendert")
core.wand_verknuepfen([wd, od])
check(len(wd._luecken) == 1 and not wd._fenster, "Durchbruch schneidet Luecke")
check(len(wd.koerper()) == 2, "Wandkoerper zweiteilig")
for lang in ("de", "en", "es"):
    check(all(k in i18n.TEXTE[lang] for k in ("tb.wz.durchbruch", "menu.einfuegen.durchbruch", "dlg.wand.titel_durchbruch", "dlg.wand.titel_vorgabe_durchbruch", "dlg.wand.art.durchbruch", "msg.wand.durchbruch")), "i18n Durchbruch " + lang)
check("durchbruch" in icons.NAMEN and core.BEFEHLE["DURCHBRUCH"] == "tool:durchbruch", "Icon/Befehl Durchbruch")

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
