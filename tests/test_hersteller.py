import sys, os, json, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
import katiecad.common.i18n as I; I.SPRACHE["aktuell"] = "de"
import katiecad.model.core as core
from katiecad.model import blocks as B
from katiecad.reports import netz as N, daten as D, daten_listen as DL, seiten as S
ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

# --- mask: field order IND, MAN, TYP, PER (REF at the bottom), from top to bottom
check(core.ElektroMaske.FELDER == ("IND", "MAN", "TYP", "PER"), "FELDER")
m = core.ElektroMaske(0, 0, {"IND": "-Q1", "MAN": "ABB", "TYP": "S203", "PER": "Zuleitung"})
m.refs = [2]
t = {k.inhalt: k for k in m.aufgeloest() if isinstance(k, core.Text)}
y_ref = [k.y for k in t.values() if k.inhalt.startswith("(")][0]
check(y_ref < t["Zuleitung"].y < t["S203"].y < t["ABB"].y < t["-Q1"].y, "Reihenfolge von unten: REF, PER, TYP, MAN, IND")
check(t["ABB"].hoehe == 1.5 and t["-Q1"].hoehe == 2.5, "Texthöhen")
check(abs((t["ABB"].y - t["S203"].y) - 2.0) < 1e-9 and abs((t["-Q1"].y - t["ABB"].y) - 3.0) < 1e-9, "Abstände")

# --- old data without MAN still load; empty MAN is not drawn
alt = {"typ": "maske", "x": 0, "y": 0, "werte": {"IND": "K1", "TYP": "LC1", "PER": "x"}, "rolle": "haupt"}
m2 = core.element_aus_dict(dict(alt)) if hasattr(core, "element_aus_dict") else core.ElektroMaske(0, 0, alt["werte"])
check(m2.werte.get("MAN", "") == "", "alte Maske ohne MAN lädt")
check(not any(k.inhalt == "MAN" for k in m2.aufgeloest() if isinstance(k, core.Text)), "leeres MAN wird nicht gezeichnet")
m3 = core.ElektroMaske(0, 0, {"IND": "K1", "MAN": "Siemens"}); d = m3.to_dict()
check(d["werte"]["MAN"] == "Siemens", "to_dict enthält MAN")
m3.setze_werte({"MAN": "ABB"}); check(m3.werte["MAN"] == "ABB", "setze_werte")
# terminals and cables stay unchanged
check("MAN" not in core.Klemme.FELDER and "MAN" not in core.Kabel.FELDER, "Klemme/Kabel unverändert")

# --- block attributes get MAN
bd = B.BlockDefinition("T", (0, 0), [core.Rechteck(-5, -5, 5, 5), core.ElektroMaske(8, 0)])
check({a.tag for a in bd.attribut_definitionen()} >= {"IND", "MAN", "TYP", "PER"}, "Block-Attribute enthalten MAN")

# --- device list and parts list
VP = core.Verbindungspunkt
def geraet(x, y, ind, typ="", man=None, rolle="haupt"):
    sym = [core.Rechteck(-5, -5, 5, 5), VP(0, 5, wert="1", tag="P1"), VP(0, -5, wert="2", tag="P2"),
           core.ElektroMaske(8, 0, rolle=rolle)]
    b = core.BlockReferenz(x, y, "Sym", sym)
    b.attribute.update({"IND": ind, "TYP": typ, "PER": ""})
    if man is not None:
        b.attribute["MAN"] = man
    return b
el = [core.Koordinatenfeld(0, 0, 287, 164, 6, 4),
      geraet(40, 100, "K1", "3RT2015", "Siemens"), geraet(80, 100, "K2", "3RT2015", "Siemens"),
      geraet(120, 100, "K3", "3RT2015", "Eaton"), geraet(160, 100, "K4", "3RT2015"),
      geraet(40, 40, "F1", "S203", "MAN")]            # "MAN" = unfilled placeholder
bl = [(0, el)]
nr = lambda i: i + 1
n = N.Netz.aufbauen(bl)
gl = {z["ind"]: z for z in D.geraeteliste(bl, nr, n)}
check(gl["K1"]["hersteller"] == "Siemens" and gl["K3"]["hersteller"] == "Eaton", "Geräteliste: Hersteller")
check(gl["K4"]["hersteller"] == "" and gl["F1"]["hersteller"] == "", "Geräteliste: leer / Platzhalter MAN = leer")
check("hersteller" in [c[0] for c in S._STANDARD["geraete"]], "Spalte Hersteller in der Geräteliste")
kat = [{"typ": "3RT2015", "hersteller": "Schneider", "bestellnr": "X1", "beschreibung": "Schütz"}]
sl = DL.stueckliste(bl, nr, n, kat)
zs = {(r["typ"], r["hersteller"]): r for r in sl}
check(zs[("3RT2015", "Siemens")]["anzahl"] == "2" and zs[("3RT2015", "Siemens")]["kennzeichen"] == ["K1", "K2"], "Stückliste: gleicher Typ + Hersteller zählt zusammen")
check(zs[("3RT2015", "Eaton")]["anzahl"] == "1", "Stückliste: anderer Hersteller = eigene Zeile")
check(zs[("3RT2015", "Schneider")]["anzahl"] == "1" and zs[("3RT2015", "Schneider")]["bestellnr"] == "X1",
      "Stückliste: ohne MAN gilt der Hersteller aus dem Teilekatalog")
check(("S203", "") in zs, "Stückliste: ohne Hersteller")

# --- symbol script: adds only MAN, idempotent, keeps format
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import symbole_man_ergaenzen as SM
tmp = tempfile.mkdtemp()
try:
    daten = {"format": "katiecad-block", "version": 1, "block": {"name": "X", "basispunkt": [0.0, 0.0], "elemente": [
        {"typ": "linie", "x1": 0, "y1": 0, "x2": 1, "y2": 1},
        {"typ": "maske", "x": 1, "y": 2, "werte": {"IND": "IND", "TYP": "TYP", "PER": "PER"}, "rolle": "haupt"},
        {"typ": "maske", "x": 1, "y": 2, "werte": {"IND": "IND", "MAN": "Mein", "TYP": "TYP", "PER": "PER"}}]}}
    for name, nl in (("a.katieblock", "\n"), ("b.katieblock", "\r\n")):
        txt = json.dumps(daten, indent=2, ensure_ascii=False)
        with open(os.path.join(tmp, name), "w", encoding="utf-8", newline="") as f:
            f.write(txt.replace("\n", nl))
    vor = {n: open(os.path.join(tmp, n), encoding="utf-8", newline="").read() for n in ("a.katieblock", "b.katieblock")}
    check(SM.main([tmp, "--pruefen"]) == 0 and all(open(os.path.join(tmp, n), encoding="utf-8", newline="").read() == v for n, v in vor.items()), "Prüfmodus ändert nichts")
    SM.main([tmp])
    for name, nl in (("a.katieblock", "\n"), ("b.katieblock", "\r\n")):
        roh = open(os.path.join(tmp, name), encoding="utf-8", newline="").read()
        neu = json.loads(roh)
        w = [e for e in neu["block"]["elemente"] if e["typ"] == "maske"]
        check(list(w[0]["werte"]) == ["IND", "MAN", "TYP", "PER"] and w[0]["werte"]["MAN"] == "MAN", "MAN nach IND eingefügt " + name)
        check(w[1]["werte"]["MAN"] == "Mein", "vorhandenes MAN bleibt " + name)
        check(("\r\n" in roh) == (nl == "\r\n") and ("\n" in roh.replace("\r\n", "")) == (nl == "\n"), "Zeilenenden bleiben " + name)
        check(neu["block"]["elemente"][0] == daten["block"]["elemente"][0], "Rest unverändert " + name)
    roh1 = open(os.path.join(tmp, "a.katieblock"), encoding="utf-8", newline="").read()
    SM.main([tmp])
    check(open(os.path.join(tmp, "a.katieblock"), encoding="utf-8", newline="").read() == roh1, "zweiter Lauf ändert nichts")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# --- bundled symbols: every device mask has MAN, nothing else changed in the field list
import glob
sym = glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "symbols", "*", "*.katieblock"))
if sym:
    fehlt = []
    for f in sym:
        for e in json.load(open(f, encoding="utf-8"))["block"]["elemente"]:
            if e.get("typ") == "maske" and "MAN" not in e["werte"]:
                fehlt.append(os.path.basename(f))
    check(not fehlt, "Symbole ohne MAN: %s" % fehlt[:3])
for k in ("rep.col.hersteller",):
    check(k in I.TEXTE["de"] and k in I.TEXTE["en"], k)
print(f"test_hersteller - {ok} Checks bestanden")
