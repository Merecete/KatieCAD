"""KatieCAD Normschrift: built-in stroke font (width, PDF output, screen strokes)."""
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

check(N.ist_normschrift("KatieCAD Normschrift") and N.ist_kursiv("KatieCAD Normschrift kursiv"), "Namen")
check("KatieCAD Normschrift" in core.SCHRIFTARTEN and "KatieCAD Normschrift kursiv" in core.SCHRIFTARTEN,
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
t = core.Text(0, 0, "Test 123", 3.5, 0, "KatieCAD Normschrift")
check(abs(t.masse()[0] - N.breite("Test 123", 3.5)) < 1e-9, "Text.masse nutzt Normschrift-Breite")
check(core.pdf_textbreite("Test", 5.0 / core.CAD_VERSALHOEHE, False, "Arial") != N.breite("Test", 5.0), "Arial unveraendert")

# PDF: strokes become lines, no font reference
s = core.PdfSeite(210, 297)
s.text(20, 100, "Ø 12,5", 5, 0, "#000000", familie="KatieCAD Normschrift")
s.text(20, 80, "A", 5, 30, "#ff0000", mitte=True, familie="KatieCAD Normschrift kursiv", fett=True)
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
f(("t", 10, 10, "Hallo\nWelt", 3.5, 0, "KatieCAD Normschrift", "unten_links"), "#fff", tf, 4.0, ("t",), (0, 0, 800, 600))
check(len(a.canvas.l) > 10 and not any(x[0] == "TEXT" for x in a.canvas.l), "Bildschirm: Strichzuege")
check(abs(a.canvas.l[0][1]["width"] - 3.5 * 0.1 * 4.0) < 1e-6, "Bildschirm: Strichbreite")
ys_px = [v for (args, _k) in a.canvas.l for v in args[1::2]]
check(min(ys_px) >= 0 and max(ys_px) <= 400, "Bildschirm: Text liegt am Einfuegepunkt")
print(f"test_normschrift - OK ({ok} Pruefungen)")
