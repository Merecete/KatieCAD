"""Walls / doors / windows as solids in 3D: wall height, openings, sill height, i18n."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
from katiecad.model import core, szene3d as S
from katiecad.common import i18n

ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

W = core.Wand([(0, 0), (4000, 0)], dicke=200, hoehe=2600)
check(W.hoehe == 2600 and core.Wand([(0, 0), (1, 0)]).hoehe == core.WAND_HOEHE_STANDARD, "Hoehe/Standard")
d = W.to_dict(); d.pop("typ", None)
check("hoehe" in d and "_oeff3" not in d and "_netz3d" not in d, "gespeichert ohne Laufzeitdaten")
check(core.Wand(**d).hoehe == 2600, "Round-Trip")
old = dict(d); old.pop("hoehe")
check(core.Wand(**old).hoehe == 2500, "alte Datei: Standardhoehe")

def zmax(nz): return max(p[2] for p in nz.punkte)
def zmin(nz): return min(p[2] for p in nz.punkte)

# solid wall without openings: one body of full height
n = S.virtuelle_netze(W)
check(len(n) == 1 and zmin(n[0]) == 0 and zmax(n[0]) == 2600, "volle Wand")

T = core.Oeffnung("tuer", 1000, 0)
F = core.Oeffnung("fenster", 3000, 0)
F.bruestung = 900; F.hoehe = 1000
el = [W, T, F]
core.wand_verknuepfen(el)
check(len(W._oeff3) == 2, "zwei Oeffnungen")
st = W.stuecke3d()
hs = sorted({(round(a), round(b)) for _q, a, b in st})
check((0, 2600) in hs and (2010, 2600) in hs, f"Sturz ueber Tuer {hs}")
check((0, 900) in hs and (1900, 2600) in hs, f"Bruestung / Sturz am Fenster {hs}")
check(not any(a < 900 and b > 900 and a > 0 for _q, a, b in st), "keine Stuecke im Fensterbereich")
# volume of the wall = full volume - openings
vol = sum(abs(sum(q[i][0] * q[(i + 1) % 4][1] - q[(i + 1) % 4][0] * q[i][1] for i in range(4))) / 2 * (b - a)
          for q, a, b in st)
voll = 4000 * 200 * 2600
frei = 1010 * 200 * 2010 + 1250 * 200 * 1000 * 0 + F.breite * 200 * 1000
check(abs(vol - (voll - 1010 * 200 * 2010 - F.breite * 200 * 1000)) < voll * 0.01, f"Volumen {vol}")

# leaf / pane: in 3D from sill height
fl = S.virtuelle_netze(F)
check(len(fl) == 1 and zmin(fl[0]) > 900 and zmax(fl[0]) < 1900, "Fensterscheibe ab Bruestung")
check(S.hat_netze(W) and S.hat_netze(T) and not S.hat_netze(core.Linie(0, 0, 1, 1)), "hat_netze")
check(S.flache_zuege(W) == [] if hasattr(S, "flache_zuege") else True, "Wand nicht flach")
check(len(S.koerper_netze(el)) == 3, "Netze in der Szene")
check(len(S.virtuelle_netze(W)) == 1, "Wand = ein Netz")
# no lines inside flat faces: all edges of the wall mesh are real edges (door gap -> no cut lines)
_k = S.virtuelle_netze(W)[0].kanten
check(len(_k) < 60, f"wenige Kanten {len(_k)}")
# wall hit by ray / tool wiring
from katiecad.model import geom3d as G
check(S.wand_treffer([W], G.Kamera(skala=0.12, ziel=(2000, 0, 1000)), 400, 300, 400, 300) is not None, "Wand-Treffer")
check(S.wand_treffer([core.Linie(0, 0, 1, 1)], G.Kamera(), 400, 300, 400, 300) is None, "kein Treffer")
Fz = core.Oeffnung("fenster", 100, 0); Fz.bruestung = 500
S_verschieben = S.verschieben_achse([Fz], "z", 200)
check(Fz.bruestung == 700, "Fenster per Z-Pfeil hoeher")
S.verschieben_achse([Fz], "z", -5000)
check(Fz.bruestung == 0, "nicht unter den Boden")
from katiecad.ui import ansicht3d as A3
check(set(A3.BAU_MODI) == {"treppe", "wand", "raum", "decke", "dach", "tuer", "fenster", "durchbruch", "wandverb"} and all(m in A3.Ansicht3D.MODI for m in A3.BAU_MODI), "Bau-Modi")
for sp in ("de", "en", "es", "fr"):
    for m in A3.BAU_MODI:
        check(i18n.TEXTE[sp].get("d3.modus." + m), f"i18n d3.modus.{m} {sp}")

# cache follows changes
W.hoehe = 3000
check(zmax(S.virtuelle_netze(W)[0]) == 3000 or max(zmax(x) for x in S.virtuelle_netze(W)) == 3000, "Cache aktualisiert")

for sp in ("de", "en", "es", "fr"):
    check(i18n.TEXTE[sp].get("dlg.wand.hoehe"), "i18n " + sp)
print("test_wand3d OK", ok)
# snap: wall centre line + corners also in 3D (join walls); long meshes must not collapse to cap centres
_W2 = core.Wand([(0, 0), (4000, 0), (4000, 3000)], dicke=240)
_pk = {(round(p[0]), round(p[1])) for p, a in S.fang_kandidaten([_W2]) if abs(p[2]) < 1e-6}
check((4000, 3000) in _pk and (4120, -120) in _pk, "Fang: Mittellinie + Ecken der Wand")
_pa = {(round(p[0]), round(p[1])) for p, a in S.fang_kandidaten([_W2]) if abs(p[2]) < 1e-6 and a == "achse"}
check((0, 0) in _pa and (4000, 0) in _pa, "Fang: Wandachse")
for sp in ("de", "en", "es", "fr"):
    check(i18n.TEXTE[sp].get("d3.fang.achse"), "i18n achse " + sp)

# ---- floor / ceiling (Decke) ----
from katiecad.ui import dialogs as _dlg
_dk = core.Decke([(0, 0), (4000, 0), (4000, 3000), (0, 3000)], art="decke", dicke=200, hoehe=2500)
check(_dk.typ == "decke" and _dk.geschlossen and _dk.z_bereich() == (2500, 2700), "Decke z-Bereich")
_bd = core.Decke([(0, 0), (4000, 0), (4000, 3000)], art="boden", dicke=250, hoehe=0)
check(_bd.z_bereich() == (-250, 0), "Boden z-Bereich (Oberkante)")
_n = S.virtuelle_netze(_dk)
check(len(_n) == 1 and min(p[2] for p in _n[0].punkte) == 2500 and max(p[2] for p in _n[0].punkte) == 2700, "Decke als 3D-Koerper")
_d = _dk.to_dict(); check("_netz3d" not in _d and _d["typ"] == "decke", "to_dict")
_d.pop("typ"); check(core.Decke(**_d).dicke == 200, "Round-Trip")
check(core.Decke(**{**_d, "art": "xyz"}).art == "decke", "ungueltige Art")
check(S.hat_netze(_dk) and S.zuege3(_dk) == [], "Decke: 3D-Koerper, nicht flach")
_dk.hoehe = 3000
check(min(p[2] for p in S.virtuelle_netze(_dk)[0].punkte) == 3000, "Cache folgt der Hoehe")
_e = core.Decke([(0, 0), (10, 0), (10, 10)]); _e.skalieren(0, 0, 2) if hasattr(_e, "skalieren") else None
from katiecad.ui import app as _app
check(A3.BAU_PUNKTE.count("decke") == 1 and A3.WERKZEUG_3D["decke"] == "decke", "3D-Werkzeug decke")
for sp in ("de", "en", "es", "fr"):
    for k in ("tb.wz.decke", "menu.einfuegen.decke", "dlg.decke.titel_vorgabe", "dlg.decke.titel", "dlg.decke.art", "dlg.decke.art.boden",
              "dlg.decke.art.decke", "dlg.decke.dicke", "dlg.decke.hoehe.boden", "dlg.decke.hoehe.decke", "dlg.decke.hinweis",
              "msg.decke.klick", "msg.decke.hinweis", "msg.decke.fertig", "d3.modus.decke"):
        check(i18n.TEXTE[sp].get(k), f"i18n {k} {sp}")
print("test_wand3d Decke OK", ok)

# ---- command line always ready ----
from unittest.mock import MagicMock
import katiecad.ui.app as _A
def _app_fokus(fokus_widget, toplevels=(), grab=None):
    a = _A.CadApp.__new__(_A.CadApp)
    a.root = MagicMock(); a.entry_eingabe = MagicMock()
    a.entry_eingabe.winfo_viewable.return_value = True
    a.root.winfo_children.return_value = list(toplevels)
    a.root.grab_current.return_value = grab
    a.root.focus_get.return_value = fokus_widget
    return a
_c = MagicMock(); _c.winfo_class.return_value = "Canvas"
_a = _app_fokus(_c); _a._eingabe_fokus_pruefen()
check(_a.entry_eingabe.focus_set.called, "Fokus: Zeichenflaeche -> Befehlszeile")
_f = MagicMock(); _f.winfo_class.return_value = "TEntry"
_a = _app_fokus(_f); _a._eingabe_fokus_pruefen()
check(not _a.entry_eingabe.focus_set.called, "Fokus: anderes Eingabefeld bleibt")
_a = _app_fokus(_c, grab=object()); _a._eingabe_fokus_pruefen()
check(not _a.entry_eingabe.focus_set.called, "Fokus: modaler Dialog bleibt")
_a = _app_fokus(None); _a._eingabe_fokus_pruefen()
check(_a.entry_eingabe.focus_set.called, "Fokus: nirgends -> Befehlszeile")
_a = _app_fokus(_c); _a.entry_eingabe.get.return_value = "abc"; _a.root.focus_get.return_value = _a.entry_eingabe
check(_a._eingabe_hat_text(), "Text in der Befehlszeile erkannt")
print("test_wand3d Fokus OK", ok)
_pt = [(round(p[0]), round(p[1]), round(p[2])) for p, a in S.fang_kandidaten([_W2]) if a == "achse"]
check((4000, 3000, 2500) in _pt and (4000, 3000, 0) in _pt, "Fang: Wandachse unten und oben")

# ---- storeys (Etage) ----
_w0 = core.Wand([(0, 0), (4000, 0)], dicke=200, hoehe=2500)
_d0 = core.Decke([(0, 0), (4000, 0), (4000, 3000), (0, 3000)], art="decke", dicke=200, hoehe=2500, etage=0)
_w1 = core.Wand([(0, 0), (4000, 0)], dicke=200, hoehe=2400, etage=1)
_t1 = core.Oeffnung("tuer", 1000, 0, etage=1)
_t0 = core.Oeffnung("tuer", 3000, 0, etage=0)
_all = [_w0, _d0, _w1, _t1, _t0]
check(core.etage_basis(_all, 0) == 0 and core.etage_basis(_all, 1) == 2700, "Etage 1 beginnt auf der Decke")
check(core.etage_basis(_all, 2) is None, "Etage 2 gibt es noch nicht")
core.wand_verknuepfen(_all)
check(_w1._zbasis == 2700 and _w0._zbasis == 0 and _t1._zbasis == 2700, "Bodenhoehe je Etage")
check(len(_w0._oeff3) == 1 and len(_w1._oeff3) == 1, "Tueren nur in Waenden der eigenen Etage")
_nz1 = S.virtuelle_netze(_w1)[0]
check(min(p[2] for p in _nz1.punkte) == 2700 and max(p[2] for p in _nz1.punkte) == 5100, "Wand Etage 1 ueber der Decke")
_tn = S.virtuelle_netze(_t1)[0]
check(min(p[2] for p in _tn.punkte) >= 2700, "Tuerblatt in Etage 1")
_dd = _d0.to_dict(); _wd = _w1.to_dict()
check(_wd["etage"] == 1 and "_zbasis" not in _wd and _dd["etage"] == 0, "Etage gespeichert, Bodenhoehe nicht")
_wd.pop("typ"); check(core.Wand(**_wd).etage == 1, "Round-Trip Etage")
_d1 = core.Decke([(0, 0), (4000, 0), (4000, 3000)], art="decke", dicke=250, hoehe=2400, etage=1)
core.wand_verknuepfen(_all + [_d1])
check(core.etage_basis(_all + [_d1], 2) == 2700 + 2400 + 250, "Etage 2 nach Decke ueber Etage 1")
check(min(p[2] for p in S.virtuelle_netze(_d1)[0].punkte) == 2700 + 2400, "Decke ueber Etage 1: absolute Hoehe")
for sp in ("de", "en", "es", "fr"):
    for k in ("dlg.etage", "dlg.etage.hinweis", "dlg.etage.hinweis_decke", "msg.etage.fehlt"):
        check(i18n.TEXTE[sp].get(k), f"i18n {k} {sp}")
print("test_wand3d Etage OK", ok)

# ---- stairs (Treppe) ----
for _art in core.TREPPE_ARTEN:
    _tp = core.Treppe(0, 0, 30, art=_art, hoehe=2700)
    _n = _tp.anzahl()
    check(_n == 15 and abs(_tp.steigung() - 180) < 1e-9, f"Treppe {_art}: 15 Steigungen")
    check(len(_tp.stufen()) == _n - 1, f"Treppe {_art}: n-1 Auftritte/Podest")
    _st = _tp.stuecke3d()
    check(abs(max(b for _q, _a, b in _st) - 2700 + 180) < 1e-6, f"Treppe {_art}: oberste Stufe eine Steigung unter dem Boden darueber")
    _nz = S.virtuelle_netze(_tp)
    check(len(_nz) == 1 and len(_nz[0].kanten) > 20, f"Treppe {_art}: 3D-Netz")
    check(S.hat_netze(_tp) and _tp.bbox()[2] > _tp.bbox()[0], f"Treppe {_art}: bbox/3D")
    _d = _tp.to_dict(); check("_zbasis" not in _d and _d["typ"] == "treppe", "Treppe to_dict")
    _d.pop("typ"); check(core.Treppe(**_d).art == _art, "Treppe Round-Trip")
_g = core.Treppe(100, 200, 0, art="gerade", breite=1000, auftritt=280)
check(abs(_g.bbox()[2] - (100 + 14 * 280)) < 1e-6 and abs(_g.bbox()[1] - (200 - 500)) < 1e-6, "gerade: Lauflaenge 14 x Auftritt")
check(_g.punkt_im_koerper(300, 200) and not _g.punkt_im_koerper(300, 900), "Treffer")
_g.drehen(100, 200, 90)
check(abs(_g.winkel - 90) < 1e-6 and abs(_g.bbox()[3] - (200 + 14 * 280)) < 1e-6, "drehen")
_g.griff_bewegen("r", 100, 0); check(abs(_g.winkel - 270) < 1e-6, "Drehgriff")
_s = core.Treppe(0, 0, 0, richtung="links"); _s.spiegeln(0, 0, 1, 0)
check(_s.richtung == "rechts", "spiegeln dreht die Abbiegerichtung")
_f = core.Treppe(0, 0, 0, bauweise="frei", dicke=50)
check(all(abs(b - a - 50) < 1e-6 or a == 0 for _q, a, b in _f.stuecke3d()), "frei: duenne Stufen")
_etw = core.Treppe(0, 0, 0, etage=1)
core.wand_verknuepfen([_w0, _d0, _etw])
check(_etw._zbasis == 2700, "Treppe auf Etage 1")
check(min(p[2] for p in S.virtuelle_netze(_etw)[0].punkte) == 2700, "Treppe: 3D-Hoehe ueber der Decke")
check(A3.WERKZEUG_3D["treppe"] == "treppe" and "treppe" in A3.BAU_MODI, "3D-Werkzeug treppe")
for sp in ("de", "en", "es", "fr"):
    for k in ("tb.wz.treppe", "menu.einfuegen.treppe", "dlg.treppe.titel_vorgabe", "dlg.treppe.art.u", "dlg.treppe.hinweis", "msg.treppe.fertig", "d3.modus.treppe"):
        check(i18n.TEXTE[sp].get(k), f"i18n {k} {sp}")
print("test_wand3d Treppe OK", ok)

# ---- stairs: railing, stringers, break line, ceiling opening ----
for _art in ("gerade", "l", "u", "wendel"):
    _g = core.Treppe(0, 0, 0, art=_art, gelaender="beidseitig", wangen=True)
    _gg = _g.gelaender3d()
    check(len(_gg["schienen"]) == 2 and len(_gg["wangen"]) == 2 and _gg["pfosten"], f"Gelaender {_art}")
    _top = max(z for pl in _gg["schienen"] for _x, _y, z in pl)
    check(abs(_top - (_g.hoehe + _g.gelaender_hoehe)) < 1e-6, f"Gelaender {_art}: Hoehe am oberen Ende")
    _nz = S.virtuelle_netze(_g)
    check(len(_nz) >= 4, f"Treppe {_art}: Netze fuer Koerper, Gelaender, Wangen")
    check(core.Treppe(0, 0, 0, art=_art, gelaender="links").gelaender3d()["schienen"].__len__() == 1, f"nur links {_art}")
    check(core.Treppe(0, 0, 0, art=_art).gelaender3d()["schienen"] == [], f"ohne Gelaender {_art}")
_sp = core.Treppe(0, 0, 0, gelaender="links"); _sp.spiegeln(0, 0, 1, 0)
check(_sp.gelaender == "rechts", "spiegeln: Gelaenderseite")
_bl = core.Treppe(0, 0, 0, bruchlinie=True)
check(len(_bl.prims()) > len(core.Treppe(0, 0, 0).prims()) and _bl._bruchlinie(), "Bruchlinie + gestrichelte Stufen")
_dk = core.Decke([(-3000, -4000), (6000, -4000), (6000, 4000), (-3000, 4000)], art="decke", hoehe=2500, etage=0)
for _art in ("gerade", "l", "u", "wendel"):
    _tr = core.Treppe(0, 0, 30, art=_art, etage=0)
    core.wand_verknuepfen([_dk, _tr])
    check(len(_dk._aussparungen) == 1, f"Durchbruch {_art}")
    _n = S.virtuelle_netze(_dk)[0]
    _fl = 0.0
    for _f in _n.flaechen:
        if len(_f) == 3 and all(abs(_n.punkte[i][2] - 2700) < 1e-6 for i in _f):
            _p = [_n.punkte[i] for i in _f]
            _fl += abs((_p[1][0] - _p[0][0]) * (_p[2][1] - _p[0][1]) - (_p[1][1] - _p[0][1]) * (_p[2][0] - _p[0][0])) / 2
    check(abs(_fl - (9000 * 8000 - abs(sum(S._flaeche2(l) for l in _dk._aussparungen)))) < 1.0, f"Decke mit Loch {_art}: Flaeche")
_tr = core.Treppe(0, 0, 0, durchbruch=False)
core.wand_verknuepfen([_dk, _tr]); check(_dk._aussparungen == [], "Durchbruch aus")
_tr = core.Treppe(0, 0, 0, etage=1)
core.wand_verknuepfen([_dk, _tr]); check(_dk._aussparungen == [], "andere Etage: kein Durchbruch")
_tr = core.Treppe(0, 0, 0)
_dk2 = core.Decke([(-100, -100), (500, -100), (500, 500), (-100, 500)], art="decke", hoehe=2500)
core.wand_verknuepfen([_dk2, _tr]); check(_dk2._aussparungen == [], "Loch ragt aus der Decke: kein Schnitt")
_bo = core.Decke([(-3000, -4000), (6000, -4000), (6000, 4000), (-3000, 4000)], art="boden", hoehe=0, etage=0)
core.wand_verknuepfen([_bo, core.Treppe(0, 0, 0)]); check(_bo._aussparungen == [], "Boden bekommt keinen Durchbruch")
check("_aussparungen" not in _dk.to_dict() and "gelaender" in core.Treppe(0, 0, 0).to_dict(), "Speichern")
for sp in ("de", "en", "es", "fr"):
    for k in ("dlg.treppe.gelaender", "dlg.treppe.gelaender.keins", "dlg.treppe.gelaender.beidseitig", "dlg.treppe.gelaender_hoehe",
              "dlg.treppe.wangen", "dlg.treppe.bruchlinie", "dlg.treppe.durchbruch"):
        check(i18n.TEXTE[sp].get(k), f"i18n {k} {sp}")
print("test_wand3d Treppe Gelaender/Durchbruch OK", ok)

# ---- roofs ----
import math
from katiecad.model import dach as _DM
_rp = [(0, 0), (10000, 0), (10000, 6000), (0, 6000)]
_r1 = core.Dach(_rp)
check(abs(_r1.firsthoehe_berechnet() - 3000 * math.tan(math.radians(35))) < 1.0, "Walmdach: Firsthoehe aus Neigung")
_n1 = S.virtuelle_netze(_r1)
check(len(_n1) == 1 and len(_n1[0].punkte) == 6 and len(_n1[0].kanten) == 9, "Walmdach: 6 Punkte, 9 Kanten")
_r2 = core.Dach(_rp, giebel=[2, 4])
check(_r2.giebel == [2, 4] and abs(_r2.firsthoehe_berechnet() - _r1.firsthoehe_berechnet()) < 1.0, "Satteldach mit Giebeln")
check(len(_r2.prims()) > len(core.Dach(_rp).prims()) - 3, "Giebel im Plan markiert")
_r3 = core.Dach(_rp, spitz=False, firsthoehe=800)
check(abs(_r3.firsthoehe_berechnet() - 800) < 1.0 and _r3.geometrie()["plateau"], "Dachhoehe: Plateau")
_r4 = core.Dach([(0, 0), (10000, 0), (10000, 4000), (4000, 4000), (4000, 10000), (0, 10000)])
_gm = _r4.geometrie()
_fl = sum(abs(_DM._flaeche([(x, y) for x, y, z in p])) for _e, p in _gm["flaechen"])
check(abs(_fl - 64e6) < 1e3 and len(_gm["grate"]) >= 8, "L-Grundriss: Kehle, Flaechen decken den Umriss")
_r5 = core.Dach(list(reversed(_r4.punkte)))
check(abs(sum(abs(_DM._flaeche([(x, y) for x, y, z in p])) for _e, p in _r5.geometrie()["flaechen"]) - 64e6) < 1e3, "Umlaufsinn egal")
_r6 = core.Dach([(0, 0), (5000, 0), (10000, 0), (10000, 6000), (5000, 6000), (0, 6000)])
check(abs(sum(abs(_DM._flaeche([(x, y) for x, y, z in p])) for _e, p in _r6.geometrie()["flaechen"]) - 60e6) < 1e3, "Punkt mitten auf einer Kante")
_dd = _r2.to_dict(); _dd.pop("typ", None)
_r7 = core.Dach(**_dd)
check(_r7.giebel == [2, 4] and "_zbasis" not in _r2.to_dict() and "_dachgeo" not in _r2.to_dict(), "Speichern/Laden")
_dk0 = core.Decke([(0, 0), (4000, 0), (4000, 3000), (0, 3000)], art="decke", hoehe=2500, etage=0)
_r8 = core.Dach(_rp, etage=1)
core.wand_verknuepfen([_dk0, _r8])
check(_r8._zbasis == 2700, "Dach auf Etage 1: Hoehe ueber der Decke")
check(abs(min(p[2] for p in S.virtuelle_netze(_r8)[0].punkte) - (2700 + _r8.traufe)) < 1e-6, "Dach 3D: Traufhoehe")
_fk = []
S._el_fang(_r1, _fk)
check(len(_fk) >= 6 and all(k == "end" for _p, k in _fk), "Dach: Fangpunkte (Traufe und First)")
check(A3.BAU_PUNKTE.count("dach") == 1 and A3.WERKZEUG_3D["dach"] == "dach", "3D-Werkzeug dach")
_ap2 = _A.CadApp.__new__(_A.CadApp); _ap2._etage_filter = 0
check(_ap2._etage_ausgeblendet(_r1) and not _A.CadApp.__new__(_A.CadApp).__dict__.get("x"), "Dach in der Etagenansicht ausgeblendet")
_ap2._etage_filter = None
check(not _ap2._etage_ausgeblendet(_r1), "Dach bei Gesamt sichtbar")
check(core.BEFEHLE.get("DACH") == "tool:dach" and core.BEFEHLE.get("ROOF") == "tool:dach", "Befehl DACH")
for sp in ("de", "en", "es", "fr"):
    for k in ("tb.wz.dach", "menu.einfuegen.dach", "msg.dach.klick", "msg.dach.hinweis", "msg.dach.fertig", "dlg.dach.titel",
              "dlg.dach.titel_vorgabe", "dlg.dach.neigung", "dlg.dach.spitz", "dlg.dach.firsthoehe", "dlg.dach.traufe",
              "dlg.dach.giebel", "dlg.dach.hinweis", "dlg.dach.zahl", "d3.modus.dach"):
        check(i18n.TEXTE[sp].get(k), f"i18n {k} {sp}")
print("test_wand3d Dach OK", ok)

# ---- view: one storey ----
_ap = _A.CadApp.__new__(_A.CadApp)
_ap.__dict__["_ctx_liste"] = lambda: _all
check(not _ap._etage_ausgeblendet(_w0) and not _ap._etage_ausgeblendet(core.Linie(0, 0, 1, 1)), "Gesamt: nichts ausgeblendet")
_ap._etage_filter = 1
check(_ap._etage_ausgeblendet(_w0) and not _ap._etage_ausgeblendet(_w1) and _ap._etage_ausgeblendet(_t0)
      and not _ap._etage_ausgeblendet(_t1), "Etage 1: Etage 0 ausgeblendet")
check(not _ap._etage_ausgeblendet(_d0) and _ap._etage_ausgeblendet(_d1), "Etage 1: Boden (Decke ueber 0) sichtbar, eigene Decke weg")
_tu = core.Treppe(0, 0, 0, etage=0); _tu0 = core.Treppe(0, 0, 0, etage=0, durchbruch=False)
check(not _ap._etage_ausgeblendet(_tu) and _ap._etage_ausgeblendet(_tu0), "Etage 1: Treppe von unten sichtbar (mit Durchbruch)")
check(_tu.prims_unten() and all(not c for _p, c in _tu.prims_unten()[:-2]), "Treppe von unten: gestrichelt")
check(_A._treppe_von_unten(_ap, _tu) and not _A._treppe_von_unten(_ap, core.Treppe(0, 0, 0, etage=1)), "von unten erkannt")
_ap._etage_filter = 0
check(_ap._etage_ausgeblendet(_d0) and _ap._etage_ausgeblendet(_d1), "Etage 0: Decke weg (Innenraum frei)")
_bo = core.Decke([(0, 0), (1, 0), (1, 1)], art="boden", etage=0)
check(not _ap._etage_ausgeblendet(_bo), "Etage 0: eigener Boden sichtbar")
_ap._etage_filter = 1
check(not _ap._etage_ausgeblendet(core.Linie(0, 0, 1, 1)) and not _ap._etage_ausgeblendet(core.Text(0, 0, "x")), "andere Objekte bleiben")
check(_ap._etagen_vorhanden() == [0, 1], "vorhandene Etagen aus den Bauteilen")
_ap._etage_filter = None
for sp in ("de", "en", "es", "fr"):
    for k in ("menu.ansicht.etage", "menu.ansicht.etage_gesamt", "menu.ansicht.etage_n", "dlg.etage_ansicht.leer", "msg.etage.alle", "msg.etage.nur"):
        check(i18n.TEXTE[sp].get(k), f"i18n {k} {sp}")
print("test_wand3d Etagenansicht OK", ok)
