"""Security: manipulated files must not reach outside the project, CSV is free of formulas."""
import os, sys, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
from katiecad.model.project import Projekt, ProjektFehler, blattdatei_sicher, FORMAT_KENNUNG
from katiecad.model.core import polygon_schraffur
from katiecad.reports.anwenden import csv_sicher, csv_schreiben

ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

# ---- sheet file names -------------------------------------------------------------------
for gut in ("Blatt_001.cadjson", "Seite 2.cadjson", "plan.CADJSON"):
    check(blattdatei_sicher(gut), "erlaubt: " + gut)
for schlecht in ("../x.cadjson", "..\\x.cadjson", "/etc/passwd", "C:\\x.cadjson", "sub/x.cadjson",
                 "x.txt", "", "..", ".", None, 5, "a\x00b.cadjson", "x" * 300 + ".cadjson"):
    check(not blattdatei_sicher(schlecht), "abgelehnt: " + repr(schlecht)[:30])

tmp = tempfile.mkdtemp()
def projekt_schreiben(datei):
    pfad = os.path.join(tmp, "p.katieprojekt")
    json.dump({"format": FORMAT_KENNUNG, "name": "p",
               "blaetter": [{"name": "A", "datei": datei}]}, open(pfad, "w"))
    return pfad
check(Projekt.laden(projekt_schreiben("Blatt_001.cadjson")).blaetter[0].datei == "Blatt_001.cadjson", "normales Projekt")
for boese in ("../../wichtig.cadjson", "/tmp/wichtig.cadjson", "C:\\wichtig.cadjson"):
    try:
        Projekt.laden(projekt_schreiben(boese))
        check(False, "boeser Blattname muss abgelehnt werden: " + boese)
    except ProjektFehler as e:
        check(str(e) == "unsichere_datei", "Fehlercode fuer " + boese)

# ---- CSV: no formulas ----------------------------------------------------------------------
for text in ("=1+1", "+cmd|' /C calc'!A0", "-2+3", "@SUM(A1)", "\t=1", "=HYPERLINK(\"http://x\")"):
    check(csv_sicher(text).startswith("'"), "Formel entschaerft: " + text[:12])
for text in ("12", "-5", "3,5", "-0.25", "K1", "", "Motor"):
    check(csv_sicher(text) == text, "unveraendert: " + repr(text))
class _S:
    def __init__(self, titel, key): self.titel, self.key = titel, key
pf = os.path.join(tmp, "t.csv")
csv_schreiben(pf, [_S("Name", "n")], [{"n": "=cmd()"}, {"n": "Q1"}])
inhalt = open(pf, encoding="utf-8-sig").read().split()
check(inhalt == ["Name", "'=cmd()", "Q1"], "CSV-Datei enthaelt keine Formel")

# ---- absurdly dense hatching does not hang -----------------------------------------------
gross = [(0, 0), (1e9, 0), (1e9, 1e9), (0, 1e9)]
check(polygon_schraffur(gross, [45], 5.0) == [], "extrem dichte Schraffur wird abgebrochen")
check(len(polygon_schraffur([(0, 0), (100, 0), (100, 100), (0, 100)], [45], 10.0)) > 5, "normale Schraffur")
print(f"test_sicherheit - OK ({ok} Pruefungen)")
