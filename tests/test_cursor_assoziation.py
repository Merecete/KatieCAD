"""CURSORSIZE, file association files, default colour 'by layer'."""
import os, sys, re
from types import SimpleNamespace as NS
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
from katiecad.model.core import BEFEHLE
from katiecad.ui import app as A

ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1
def lies(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()

for k in ("CURSORSIZE", "CURSORGROESSE", "FADENKREUZ"):
    check(BEFEHLE.get(k) == "cursorsize", "Alias " + k)

class Canvas:
    def __init__(self): self.linien = []
    def delete(self, *a): self.linien = []
    def winfo_width(self): return 1000
    def winfo_height(self): return 600
    def create_line(self, x0, y0, x1, y1, **k): self.linien.append((x0, y0, x1, y1))
def kreuz(n, x=300, y=200):
    c = Canvas(); s = NS(canvas=c, cursor_prozent=n)
    A.CadApp._fadenkreuz(s, x, y)
    return c.linien
check(kreuz(100) == [(0, 200, 1000, 200), (300, 0, 300, 600)], "100 = ueber die ganze Flaeche")
l = kreuz(10)
check(l[0] == (270.0, 200, 330.0, 200) and l[1] == (300, 170.0, 300, 230.0), "10 %: Kreuz um den Cursor, beide Arme gleich lang")
check(l[0][2] - l[0][0] == l[1][3] - l[1][1], "horizontal = vertikal")
check(kreuz(1)[0][2] - kreuz(1)[0][0] >= 6, "Mindestlaenge")

check(A.CadApp._cursor_prozent_lesen.__func__ if hasattr(A.CadApp._cursor_prozent_lesen, "__func__") else A.CadApp._cursor_prozent_lesen, "lesen vorhanden")

# file association
iss = lies("installer/KatieCAD.iss")
check("ChangesAssociations=yes" in iss and ".cadjson" in iss and ".katieprj" in iss, "Inno: Zuordnung")
check('Tasks: assoc' in iss and 'Name: "assoc"' in iss and '"%1"' in iss, "Inno: Aufgabe und Befehl mit %1")
check(iss.count("uninsdeletekey") >= 2, "Inno: wird beim Deinstallieren entfernt")
import xml.dom.minidom as md
d = md.parseString(lies("installer/katiecad-mime.xml"))
globs = [g.getAttribute("pattern") for g in d.getElementsByTagName("glob")]
check(globs == ["*.cadjson", "*.katieprj"], "MIME: Endungen")
for f in ("installer/build_deb.sh", "installer/build_appimage.sh"):
    t = lies(f)
    check("MimeType=application/x-katiecad;application/x-katiecad-project;" in t and "katiecad-mime.xml" in t, f)
check("update-mime-database" in lies("installer/build_deb.sh"), "deb: MIME-Datenbank aktualisieren")
check("%F" in lies("installer/build_deb.sh"), "Exec mit %F")
check("CFBundleDocumentTypes" in lies("tools/macos_plist.py"), "macOS")
check("datei_von_aussen_oeffnen" in lies("katiecad/ui/app.py") and "sys.argv[1:]" in lies("katiecad/ui/app.py"), "Start mit Dateiargument")
check(re.search(r'eigene_farbe = tk\.BooleanVar\(value=False\)', lies("katiecad/ui/app.py")), "Standard: Farbe von Layer")
# layer list: shows the layer of the selection; choosing moves objects, current layer stays
class Var:
    def __init__(s, v): s.v = v
    def get(s): return s.v
    def set(s, v): s.v = v
def mk(auswahl, anzeige, wz="auswahl"):
    return NS(auswahl=auswahl, layers={"0": 1, "Rot": 2, "Blau": 3}, aktiver_layer=Var("0"),
              layer_anzeige=Var(anzeige), aktives_werkzeug=Var(wz), _snapshot=lambda: None,
              _mark_dirty=lambda: None, redraw=lambda: None, status=NS(set=lambda t: None),
              _layer_auswahl=lambda: [e for e in auswahl if hasattr(e, "layer")],
              _layer_info_aktualisieren=lambda: None)
e1, e2 = NS(layer="Rot"), NS(layer="Rot")
st = mk([e1, e2], "Blau")
A.CadApp._layer_gewechselt(st)
check(e1.layer == "Blau" and e2.layer == "Blau" and st.aktiver_layer.get() == "0", "Auswahl -> Layer, aktueller Layer bleibt")
st = mk([], "Rot"); A.CadApp._layer_gewechselt(st)
check(st.aktiver_layer.get() == "Rot", "ohne Auswahl: wird aktueller Layer")
st = mk([e1], "0"); st.aktiver_layer.set("Rot"); e1.layer = "Blau"
A.CadApp._layer_anzeige_nachziehen(st); check(st.layer_anzeige.get() == "Blau", "Anzeige = Layer des Objekts")
st.auswahl = []; st._layer_auswahl = lambda: []
A.CadApp._layer_anzeige_nachziehen(st); check(st.layer_anzeige.get() == "Rot", "nichts gewaehlt: aktueller Layer")
st = mk([NS(layer="Rot"), NS(layer="Blau")], "0"); A.CadApp._layer_anzeige_nachziehen(st)
check(st.layer_anzeige.get() == "*VERSCHIEDEN*" or "VARI" in st.layer_anzeige.get().upper() or "VERSCH" in st.layer_anzeige.get().upper(), "gemischt")
st = mk([NS(layer="Blau")], "0", wz="linie"); A.CadApp._layer_anzeige_nachziehen(st)
check(st.layer_anzeige.get() == "0", "beim Zeichnen: aktueller Layer")
print("OK     test_cursor_assoziation - OK (%d Pruefungen)" % ok)
