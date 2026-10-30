import sys, os, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
import katiecad.common.i18n as I; I.SPRACHE["aktuell"] = "de"
import katiecad.model.core as core
from katiecad.model import schriften as SF
ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

# standard fonts untouched
check(core.SCHRIFTARTEN == SF.STANDARD_SCHRIFTEN, "Standardliste")
check(abs(core.pdf_textbreite("Hallo", 10) - core.pdf_textbreite("Hallo", 10, False, "Arial")) < 1e-9, "Arial bleibt Helvetica")

# a real font file somewhere on this machine (skip silently if there is none)
gef = SF.scan()
gef = {n: e for n, e in gef.items() if e["regular"] and not e["cff"]}
if gef:
    name = sorted(gef)[0]
    check(SF.aktiviere([name], gef) == [name] and SF.ist_zusatz(name), "aktiviert")
    core.schriftarten_aktualisieren()
    check(core.SCHRIFTARTEN[-1] == name and core.SCHRIFTARTEN[:7] == SF.STANDARD_SCHRIFTEN, "Liste erweitert")
    f = SF.breite(name)
    check(f is not None and f("Hallo") > 0 and f("HH") == 2 * f("H"), "Breiten aus der Schriftdatei")
    check(abs(core.pdf_textbreite("Hallo", 10, False, name) - f("Hallo") / 100.0) < 1e-9, "pdf_textbreite nutzt Schrift")
    t = core.Text(0, 0, "Hallo", 5, 0, name)
    check(abs(t.masse()[0] - f("Hallo") * (5 / core.CAD_VERSALHOEHE) / 1000.0) < 1e-6 or t.masse()[0] >= core.TEXT_BREITE * 5, "Text.masse")
    sp = core.PdfSeite(100, 50)
    sp.text(10, 10, "Hallo Ø", 5, 0, "#000000", False, False, name)
    sp.text(10, 30, "Fett", 5, 0, "#000000", True, True, name)
    pdf = core.pdf_mehrseitig([sp])
    check(pdf.startswith(b"%PDF") and b"Identity-H" in pdf and b"/FontFile2" in pdf, "PDF bettet Schrift ein")
    check(b"/FX0" in pdf and b"/FX1" in pdf, "zwei Schnitte (normal/fett)")
    tmp = tempfile.mkdtemp()
    try:
        pf = os.path.join(tmp, "t.pdf"); open(pf, "wb").write(pdf)
        if shutil.which("qpdf"):
            r = subprocess.run(["qpdf", "--check", pf], capture_output=True, text=True)
            check(r.returncode in (0, 3), "qpdf: PDF formal in Ordnung")
        if shutil.which("pdftotext"):
            r = subprocess.run(["pdftotext", pf, "-"], capture_output=True, text=True)
            check("Hallo" in r.stdout and "Fett" in r.stdout, "pdftotext liest den Text")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
else:
    print("(keine Schriftdatei gefunden - Embedding-Tests übersprungen)")

# unknown / empty
SF.aktiviere([])
core.schriftarten_aktualisieren()
check(core.SCHRIFTARTEN == SF.STANDARD_SCHRIFTEN, "Zurück auf Standard")
check(SF.breite("GibtEsNicht") is None and SF.pdf_ttf("GibtEsNicht") is None, "unbekannte Schrift")
sp = core.PdfSeite(50, 50); sp.text(5, 5, "x", 3, 0, "#000000", False, False, "GibtEsNicht")
check(b"/F1" in core.pdf_mehrseitig([sp]) and not hasattr(sp, "zusatz"), "Fallback Helvetica")
for k in ("menu.ansicht.schriften", "dlg.schriften.titel", "dlg.schriften.hinweis", "dlg.schriften.suche",
          "dlg.schriften.nur_bildschirm", "dlg.schriften.nur_gewaehlt", "dlg.schriften.keine_waehlen", "dlg.schriften.zaehler", "dlg.schriften.keine", "msg.schriften_gesetzt"):
    check(k in I.TEXTE["de"] and k in I.TEXTE["en"], k)
print(f"test_schriften - {ok} Checks bestanden")
