"""External references (XREF): placed like a block, read-only, only the path is saved."""
import os, sys, json, tempfile, time
from unittest.mock import MagicMock
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
import katiecad.ui.app as A
import katiecad.model.core as C
from katiecad.model.core import (XrefElement, BlockReferenz, ZUSAMMENGESETZT, Linie, Text, Wand,
                                 Oeffnung, Polylinie, Layer)
from katiecad.common import i18n

ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

tmp = tempfile.mkdtemp()

# ---- core: placing, transform, read-only, save ---------------------------------------
datei = os.path.join(tmp, "grundriss.cadjson")
open(datei, "w").write("{}")
inhalt = [[Linie(0, 0, 100, 0)]]
C.XREF_LADER = lambda p: list(inhalt[0])
C.XREF_BASIS = lambda: tmp
C.XREF_PRUEFSEKUNDEN = 0.0

r = XrefElement(1000, 500, "grundriss.cadjson")
check(isinstance(r, BlockReferenz) and isinstance(r, ZUSAMMENGESETZT), "wie ein Block")
check(r.typ == "xref" and r.xname == "grundriss", "Typ/Name")
k = r.aufgeloest()
check(len(k) == 1 and abs(k[0].x1 - 1000) < 1e-6 and abs(k[0].x2 - 1100) < 1e-6, "Position")
r.winkel = 90
r._cache = None
k = r.aufgeloest()
check(abs(k[0].x2 - 1000) < 1e-6 and abs(k[0].y2 - 600) < 1e-6, "Drehung")
r.winkel = 0; r.skalierung = 2.0; r._cache = None
check(abs(r.aufgeloest()[0].x2 - 1200) < 1e-6, "Massstab")
r.skalierung = 1.0; r._cache = None
b = r.bbox()
check(abs(b[0] - 1000) < 1e-6 and abs(b[2] - 1100) < 1e-6, "bbox")
check(r.attribut_definitionen() == [] and r.geraet_maske() is None, "nicht elektrisch")
check(r.griffe() == [("p", 1000, 500)], "nur ein Griff (Position)")

d = r.to_dict()
check(set(d) >= {"typ", "pfad", "x", "y", "winkel", "skalierung", "sichtbar"}, "to_dict")
check("elemente" not in d, "Inhalt wird nicht gespeichert")
r2 = XrefElement(**{k_: v for k_, v in d.items() if k_ != "typ"})
check(r2.x == 1000 and r2.pfad == "grundriss.cadjson" and r2.sichtbar, "Rundlauf")

# ---- on / off ------------------------------------------------------------------------
r.sichtbar = False
check(r.aufgeloest() == [], "ausgeschaltet: nichts gezeichnet")
bb = r.bbox()
check(bb[0] == bb[2] == 1000, "ausgeschaltet: bbox ist ein Punkt")
r.sichtbar = True

# ---- file changes are picked up, missing file -----------------------------------------
inhalt[0] = [Linie(0, 0, 100, 0), Linie(0, 0, 0, 100)]
os.utime(datei, (time.time() + 5, time.time() + 5))
check(len(r.aufgeloest()) == 2, "geaenderte Datei wird neu gelesen")
inhalt[0] = [Linie(0, 0, 5, 0)]
r.neu_laden()
check(len(r.aufgeloest()) == 1, "Aktualisieren")
fehlt = XrefElement(0, 0, "gibt_es_nicht.cadjson")
check(fehlt.aufgeloest() == [] and fehlt.fehler == "fehlt", "fehlende Datei")
check(r.fehler == "", "kein Fehler")

# ---- relative path + stored absolute path as fallback -----------------------------------
check(r.abs_pfad() == os.path.normpath(datei), "relativer Pfad")
C.XREF_BASIS = lambda: os.path.join(tmp, "woanders")
alt = XrefElement(0, 0, "grundriss.cadjson", pfad_abs=datei)
check(alt.abs_pfad() == os.path.normpath(datei), "absoluter Pfad als Ersatz")
C.XREF_BASIS = lambda: tmp

# ---- loader of the app: hidden layers, colours, walls, blocks ---------------------------
a = A.CadApp.__new__(A.CadApp)
a.dezimalkomma = MagicMock(); a.dezimalkomma.get.return_value = False
a._einh_faktor = lambda: 1.0
a.projekt = None
a._datei_pfad = None
layers = [Layer("0").to_dict(), Layer("Waende", "#ff8800", 0.5).to_dict(),
          Layer("Hilfe", "#00ff00", 0.25, False).to_dict()]
wand = Wand([(0, 0), (4000, 0)], dicke=240, layer="Waende")
tuer = Oeffnung("tuer", x=2000, y=0, layer="Waende")
elems = [Linie(0, 0, 10, 0, layer="Waende").to_dict(),
         Linie(0, 0, 10, 10, layer="Hilfe").to_dict(),
         Text(5, 5, "Raum", layer="0").to_dict(),
         wand.to_dict(), tuer.to_dict()]
quelle = os.path.join(tmp, "plan.cadjson")
json.dump({"layers": layers, "elemente": elems}, open(quelle, "w"))
out = a._xref_datei_laden(quelle)
check(out, "Loader liefert Elemente")
check(not any(e.layer == "Hilfe" for e in out), "ausgeblendeter Layer bleibt draussen")
check(all(e.eig_farbe for e in out), "Farben sind aufgeloest")
li = [e for e in out if type(e) is Linie]
check(li and li[0].farbe == "#ff8800" and abs(li[0].staerke - 0.5) < 1e-9, "Layerfarbe/-staerke uebernommen")
check(any(isinstance(e, Polylinie) for e in out), "Wand/Tuer als Geometrie")
check(any(type(e) is Text and e.inhalt == "Raum" for e in out), "Text")
# a gap for the door: the wall outline needs more segments than without the door
out_ohne = a._xref_backen([Wand([(0, 0), (4000, 0)], dicke=240, layer="Waende")], {"Waende": Layer("Waende")})
out_mit = a._xref_backen([Wand([(0, 0), (4000, 0)], dicke=240, layer="Waende"),
                          Oeffnung("tuer", x=2000, y=0, layer="Waende")], {"Waende": Layer("Waende")})
check(len(out_mit) > len(out_ohne), "Tuer schneidet Luecke in die Wand")

# ---- paths in the app -------------------------------------------------------------------
a._datei_pfad = os.path.join(tmp, "haupt.cadjson")
check(a._xref_basis() == tmp, "Basis = Ordner der Datei")
check(a._xref_pfad_speichern(quelle) == "plan.cadjson", "relativ gespeichert")
a._datei_pfad = None
check(os.path.isabs(a._xref_pfad_speichern(quelle)), "ohne Basis absolut")

# ---- a reference cannot be exploded by the app (guarded) ---------------------------------
src = open(A.__file__, encoding="utf-8").read()
check("not isinstance(e, XrefElement)" in src, "Sprengen ausgeschlossen")

# ---- command, i18n -------------------------------------------------------------------------
check(C.BEFEHLE.get("XREF") == "xref:verwalten", "Befehl XREF")
keys = ["menu.bloecke.xref", "menu.bloecke.xref_hinzu", "dlg.xref.titel", "dlg.xref.hinweis",
        "dlg.xref.name", "dlg.xref.sichtbar", "dlg.xref.status", "dlg.xref.datei", "dlg.xref.leer",
        "dlg.xref.hinzufuegen", "dlg.xref.umschalten", "dlg.xref.aktualisieren", "dlg.xref.pfad",
        "dlg.xref.entfernen", "dlg.xref.status.ok", "dlg.xref.status.aus", "dlg.xref.status.fehlt",
        "dlg.xref.status.fehler", "dlg.xref.status.zutief", "dlg.xref.dateityp",
        "msg.xref.einfuegepunkt", "msg.xref.eingefuegt", "msg.xref.entfernt", "msg.xref.selbst",
        "msg.xref.layout", "msg.xref.nicht_sprengen", "msg.xref.lesefehler"]
for lang in ("de", "en", "es"):
    for k_ in keys:
        check(k_ in i18n.TEXTE[lang], f"i18n {lang} {k_}")
print(f"test_xref - OK ({ok} Pruefungen)")
