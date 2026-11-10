"""ISO: built-in stroke font (width, PDF output, screen strokes)."""
import sys, os, types
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
import katiecad.ui.app as A
import katiecad.model.core as core
from katiecad.model import normschrift as N

ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

check(N.ist_normschrift("ISO") and N.ist_kursiv("ISO kursiv"), "Namen")
check("ISO" in core.SCHRIFTARTEN and "ISO kursiv" in core.SCHRIFTARTEN,
      "Schrift steht in der Schriftliste")
for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ÄÖÜäöüß.,:;!?()[]/+-=<>_*#%&°±µ²³ØøΩ~€":
    check(ch in N._G and N._G[ch][1], "Zeichen vorhanden: " + ch)
# proportions: cap height 10, x-height 7, descender 3
ys = lambda c: [p[1] for z in N.glyphe(c)[1] for p in z]
check(abs(max(ys("H")) - 10) < 1e-6 and abs(min(ys("H"))) < 1e-6, "Grossbuchstaben 10/10 h")
check(abs(max(ys("x")) - 7) < 1e-6 and abs(min(ys("p")) + 3) < 1e-6, "Kleinbuchstaben 7/10 h, Unterlaenge 3/10 h")
check(abs(N.strichbreite(10) - 1.0) < 1e-9, "Strichbreite 1/10 h")
# width: scales with height; space = 6/10 h
check(abs(N.breite("HH", 10) - 2 * 6.5 - N.ABSTAND) < 1e-9, "Textbreite")
check(abs(N.breite("HH", 5) * 2 - N.breite("HH", 10)) < 1e-9, "Breite skaliert mit der Hoehe")
check(N.breite("A B", 10) > N.breite("AB", 10) + 5, "Wortabstand")
check(N.breite("A\nBBBB", 10) == N.breite("BBBB", 10), "mehrzeilig: breiteste Zeile")
# slanted: x grows with y
g0 = N.zeile_zuege("I", 10, False)[0]; g1 = N.zeile_zuege("I", 10, True)[0]
check(abs(g0[1][0] - g0[0][0]) < 1e-9 and g1[1][0] - g1[0][0] > 2.5, "kursiv: 15 Grad Neigung")
# unknown character -> box, not an error
check(len(N.zeile_zuege("☃", 5)) == 1, "unbekanntes Zeichen -> Kasten")
# text element uses the stroke font width
t = core.Text(0, 0, "Test 123", 3.5, 0, "ISO")
check(abs(t.masse()[0] - N.breite("Test 123", 3.5)) < 1e-9, "Text.masse nutzt Normschrift-Breite")
check(core.pdf_textbreite("Test", 5.0 / core.CAD_VERSALHOEHE, False, "Arial") != N.breite("Test", 5.0), "Arial unveraendert")

# PDF: strokes become lines, no font reference
s = core.PdfSeite(210, 297)
s.text(20, 100, "Ø 12,5", 5, 0, "#000000", familie="ISO")
s.text(20, 80, "A", 5, 30, "#ff0000", mitte=True, familie="ISO kursiv", fett=True)
check(all(" Tj " not in o for o in s.ops) and len(s.ops) >= 8, "PDF: Linien statt Schrift")
check(len(s.to_bytes()) > 500, "PDF erzeugbar")

# screen: strokes drawn as lines with width h/10 * scale
class Rec:
    def __init__(self): self.l = []
    def create_line(self, *a, **k): self.l.append((a, k))
    def create_text(self, *a, **k): self.l.append(("TEXT",))
a = types.SimpleNamespace(canvas=Rec(), _font_cache={})
f = types.MethodType(A.CadApp._zeichne_text_prim, a)
tf = lambda x, y: (x * 4, 400 - y * 4)
f(("t", 10, 10, "Hallo\nWelt", 3.5, 0, "ISO", "unten_links"), "#fff", tf, 4.0, ("t",), (0, 0, 800, 600))
check(len(a.canvas.l) > 10 and not any(x[0] == "TEXT" for x in a.canvas.l), "Bildschirm: Strichzuege")
check(abs(a.canvas.l[0][1]["width"] - 3.5 * 0.1 * 4.0) < 1e-6, "Bildschirm: Strichbreite")
ys_px = [v for (args, _k) in a.canvas.l for v in args[1::2]]
check(min(ys_px) >= 0 and max(ys_px) <= 400, "Bildschirm: Text liegt am Einfuegepunkt")
# old development names still work
check(N.ist_normschrift("KatieCAD Normschrift kursiv") and N.ist_kursiv("KatieCAD Normschrift kursiv"), "alte Namen als Alias")
# strokes in drawing coordinates: same as PDF baseline logic
zw = N.zuege_welt("HI", 10, 20, 5, 0.0)
check(abs(min(p[0] for z in zw for p in z) - 10) < 1e-9 and abs(min(p[1] for z in zw for p in z) - 20) < 1e-9, "zuege_welt: Grundlinie am Startpunkt")
zr = N.zuege_welt("I", 0, 0, 5, 90.0)
check(abs(zr[0][1][0] + 5) < 1e-9 and abs(zr[0][1][1]) < 1e-9, "zuege_welt gedreht (90 Grad)")
tt = core.Text(5, 5, "AB", 4.0, 0.0, "ISO")
sw = tt.striche_welt()
check(sw and min(p[0] for z in sw for p in z) >= 5 - 1e-9 and min(p[1] for z in sw for p in z) >= 5 - 1e-9, "Text.striche_welt")
check(core.Text(0, 0, "A", 3, 0, "Arial").striche_welt() is None, "keine Striche fuer andere Schriften")

# DXF (fake ezdxf objects): text mode -> TEXT with ISO style, lines mode -> polylines
from katiecad.fileio import dxf_projekt as DP
class FakeStyles(dict):
    def add(self, name, font=""):
        st = types.SimpleNamespace(dxf=types.SimpleNamespace(oblique=0.0, font=font)); self[name] = st; return st
class FakeEnt:
    def __init__(self, k, a, att): self.k, self.a, self.att = k, a, att
    def set_placement(self, *a, **k): pass
class FakeMsp:
    def __init__(self): self.e = []
    def add_text(self, t, dxfattribs=None): e = FakeEnt("text", t, dxfattribs or {}); self.e.append(e); return e
    def add_lwpolyline(self, pts, close=False, dxfattribs=None): self.e.append(FakeEnt("pl", pts, dxfattribs or {}))
    def add_hatch(self, **k): raise AssertionError
class FakeDoc:
    def __init__(self): self.styles = FakeStyles(); self.layers = FakeStyles(); self.m = FakeMsp()
    def modelspace(self): return self.m
FakeStyles.__contains__ = dict.__contains__
def dxf_lauf(modus):
    doc = FakeDoc(); doc.layers.add = lambda name, color=7: doc.layers.__setitem__(name, 1)
    sei = DP.DxfSeite(100, 100)
    sei.text(10, 10, "Ab", 5.0, 0.0, "#000000", familie="ISO kursiv")
    sei.text(10, 30, "Ab", 5.0, 0.0, "#000000", familie="Arial")
    DP.ISO_MODUS = modus
    DP.dxf_projekt_schreiben(doc, [("S1", sei)])
    DP.ISO_MODUS = "text"
    return doc
d = dxf_lauf("text")
txts = [e for e in d.m.e if e.k == "text" and e.a == "Ab"]
check(len(txts) == 2 and txts[0].att.get("style") == "ISO_kursiv" and "style" not in txts[1].att, "DXF Text-Modus: ISO-Stil nur fuer ISO")
check(d.styles["ISO_kursiv"].dxf.oblique == 15.0, "DXF: kursiver Stil 15 Grad")
d = dxf_lauf("linien")
pl = [e for e in d.m.e if e.k == "pl" and e.att.get("layer") == "Blatt_01"]
check(len(pl) >= 3 and len([e for e in d.m.e if e.k == "text" and e.a == "Ab"]) == 1, "DXF Linien-Modus: Striche als Polylinien, Arial bleibt Text")

# reports: chosen font is used for all report texts, default stays Arial
from katiecad.reports import seiten as S
bi = [S.BlattInfo("B1", [core.Linie(0, 0, 10, 0)], "")]
v, h = S.berichte_erzeugen(bi, "Demo", {"anlage": "X"}, {"deckblatt", "inhalt"}, None, "de", schrift="ISO")
fams = {e.schriftart for sei in v for e in sei.elemente if isinstance(e, core.Text)}
check(fams == {"ISO"}, "Dokumente: gewaehlte Schriftart %s" % fams)
v, h = S.berichte_erzeugen(bi, "Demo", {"anlage": "X"}, {"deckblatt", "inhalt"}, None, "de")
check({e.schriftart for sei in v for e in sei.elemente if isinstance(e, core.Text)} == {"Arial"}, "Dokumente: Standard Arial")

print(f"test_normschrift - OK ({ok} Pruefungen)")
