"""DWG writer (ezdwg adapter) with fake ezdwg / ezdxf objects - the real libraries are not available here."""
import sys, os, types
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
from katiecad.fileio import dwg_schreiben as W, cad_import

ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

class Dxf(dict):
    def get(self, k, d=None): return dict.get(self, k, d)
    def __getattr__(self, k):
        try: return self[k]
        except KeyError: raise AttributeError(k)

class E:
    def __init__(self, art, **dxf):
        self._a = art; self.dxf = Dxf(dxf); self.attribs = []; self.closed = False
    def dxftype(self): return self._a

class Raum:
    def __init__(self, mtext=True, spitze=False): self.calls = []; self.mtext = mtext
    def add_line(self, p, q, layer=None, color_index=None, true_color=None): self.calls.append(("line", p, q, layer, color_index, true_color)); return 1
    def add_circle(self, c, radius=None, layer=None, **k): self.calls.append(("circle", c, radius, layer))
    def add_arc(self, c, radius=None, start_angle=None, end_angle=None, layer=None, **k): self.calls.append(("arc", c, radius, start_angle, end_angle))
    def add_lwpolyline(self, pts, closed=False, layer=None, **k): self.calls.append(("lw", list(pts), closed))
    def add_text(self, t, p, height=None, rotation=None, layer=None, **k): self.calls.append(("text", t, p, height, rotation))
    def add_blockref(self, name, insert=None, rotation=None, layer=None, **k): self.calls.append(("ref", name, insert, rotation)); return "ref"
    def add_attrib(self, ref, tag, text, insert=None, height=None): self.calls.append(("attrib", tag, text))

class Zeichnung(Raum):
    def __init__(self, v):
        super().__init__(); self.v = v; self.layers = {}; self.saved = None
        self.blocks = types.SimpleNamespace(new=lambda n, base_point=None: Raum())
    def modelspace(self): return self
    def save(self, pfad, strict=True): self.saved = (pfad, strict)

class Doc:
    def __init__(self, ents):
        self.ents = ents
        self.layers = [types.SimpleNamespace(dxf=Dxf(name="0", color=7)), types.SimpleNamespace(dxf=Dxf(name="CD", color=1))]
        self.blocks = []
    def modelspace(self): return self.ents

zeichnungen = []
def neu(version="AC1015"):
    if neu.fail_32 and version == "AC1032": raise RuntimeError("32 nicht moeglich")
    z = Zeichnung(version); zeichnungen.append(z); return z
neu.fail_32 = False
sys.modules["ezdwg"] = types.SimpleNamespace(new=neu)

# _aufruf drops unknown parameters
r = Raum()
W._aufruf(r.add_line, (0, 0), (1, 1), layer="A", unbekannt=5, color_index=None)
check(r.calls[0] == ("line", (0, 0), (1, 1), "A", None, None), "_aufruf filtert Parameter")

ents = [
    E("LINE", start=(0, 0, 0), end=(10, 0, 0), layer="CD", color=1),
    E("CIRCLE", center=(5, 5, 0), radius=3, layer="CD"),
    E("ARC", center=(0, 0, 0), radius=4, start_angle=0, end_angle=90, layer="0"),
    E("TEXT", text="Hallo", insert=(1, 2, 0), height=2.5, rotation=10, layer="0"),
    E("MTEXT", insert=(0, 0, 0), char_height=3, layer="0"), E("INSERT", name="B1", insert=(3, 4, 0), rotation=45, layer="0"),
    E("DIMENSION", layer="0"), E("IMAGE", layer="0"),
]
ents[4].text = "Z1\\PZ2"
at = E("ATTRIB", tag="ID", text="P1", insert=(3, 5, 0), height=1); ents[5].attribs = [at]
lw = E("LWPOLYLINE", layer="0"); lw.closed = True; lw.get_points = lambda f: [(0, 0, 0), (4, 0, 0), (4, 3, 0)]
bg = E("LWPOLYLINE", layer="0"); bg.get_points = lambda f: [(0, 0, 0.5), (4, 0, 0)]
bg.virtual_entities = lambda: [E("ARC", center=(2, 0, 0), radius=2, start_angle=0, end_angle=180, layer="0")]
el = E("ELLIPSE", layer="0"); el.flattening = lambda d: [(0, 0, 0), (1, 1, 0), (2, 0, 0)]
ents += [lw, bg, el]
b = W.dxf_doc_zu_dwg(Doc(ents), "x.dwg", "R2018")
z = zeichnungen[-1]
arten = [c[0] for c in z.calls]
check(b.version == "AC1032" and z.v == "AC1032", "Version AC1032")
check(z.saved == ("x.dwg", False), "gespeichert (strict=False)")
check(("line", (0.0, 0.0), (10.0, 0.0), "CD", 1, None) in z.calls, "Linie mit Layer/Farbe")
check(("circle", (5.0, 5.0), 3.0, "CD") in z.calls and ("arc", (0.0, 0.0), 4.0, 0, 90) in z.calls, "Kreis / Bogen")
check(("text", "Hallo", (1.0, 2.0), 2.5, 10.0) in z.calls, "Text")
check(arten.count("text") == 3, "MText als 2 Textzeilen (+ 1 Text)")
check(("ref", "B1", (3.0, 4.0), 45.0) in z.calls and ("attrib", "ID", "P1") in z.calls, "Block + Attribut")
check(("lw", [(0, 0), (4, 0), (4, 3)], True) in z.calls, "LWPolylinie geschlossen")
check(("arc", (2.0, 0.0), 2.0, 0, 180) in z.calls, "Bulge -> Bogen")
check(arten.count("line") >= 3, "Ellipse -> Linien")
check(b.uebersprungen["DIMENSION"] == 1 and b.uebersprungen["IMAGE"] == 1, "Unbekanntes gezaehlt")
check(b.ersetzt["ELLIPSE"] == 1 and b.ersetzt["MTEXT"] == 1 and b.ersetzt["LWPOLYLINE"] == 1, "Ersetzt gezaehlt")
check("CD" in z.layers and z.layers["CD"] and "0" not in z.layers, "Layer uebertragen")
check("nicht übernommen" in b.text() and "als Linien" in b.text(), "Berichtstext")

# fallback to the older format
neu.fail_32 = True
b = W.dxf_doc_zu_dwg(Doc(ents[:1]), "y.dwg", "R2018")
check(b.version == "AC1015", "Rueckfall auf AC1015")
neu.fail_32 = False

# engine choice in cad_import
txt = cad_import.dxf_doc_als_dwg_speichern(Doc(ents[:1]), "z.dwg")
check(txt.startswith("ezdwg:") and "1 Elemente" in txt, "cad_import nutzt ezdwg")
check(not hasattr(cad_import, "oda_verfuegbar"), "ODA entfernt")
from katiecad.common import i18n
for lang in ("de", "en", "es"):
    check(all(k in i18n.TEXTE[lang] for k in ("msg.dwg.bericht", "menu.datei.import", "menu.datei.export", "menu.datei.export_projekt", "dlg.import.alle", "dlg.import.unbekannt", "msg.dwgp.fertig", "dlg.importziel.titel", "dlg.importziel.frage", "dlg.importziel.neu", "dlg.importziel.einfuegen")), "i18n DWG " + lang)
import tempfile
with tempfile.TemporaryDirectory() as td:
    for kopf, erwartet in ((b"AC1021", "AC1021"), (b"AC1032", "AC1032"), (b"XXXXXX", "")):
        pf = os.path.join(td, "t.dwg"); open(pf, "wb").write(kopf + b"\0" * 20)
        check(cad_import.dwg_version(pf) == erwartet, "dwg_version " + erwartet)
check(cad_import.dwg_version(os.path.join(td, "fehlt.dwg")) == "", "dwg_version fehlende Datei")
check(all("msg.dwg.r2007_hinweis" in i18n.TEXTE[l] for l in ("de", "en", "es")), "i18n R2007-Hinweis")
print(f"test_dwg_schreiben - OK ({ok} Pruefungen)")
