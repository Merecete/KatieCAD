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
check(len(S.koerper_netze(el)) >= 4, "Netze in der Szene")

# cache follows changes
W.hoehe = 3000
check(zmax(S.virtuelle_netze(W)[0]) == 3000 or max(zmax(x) for x in S.virtuelle_netze(W)) == 3000, "Cache aktualisiert")

for sp in ("de", "en", "es", "fr"):
    check(i18n.TEXTE[sp].get("dlg.wand.hoehe"), "i18n " + sp)
print("test_wand3d OK", ok)
