# -*- coding: utf-8 -*-
"""
tools/symbole_man_ergaenzen.py - adds the manufacturer field <MAN> to the device masks of
the symbol library (version 1.1.1).

What it does (and ONLY this): in every .katieblock file below the given folder, each device
mask (typ "maske") that has no MAN field yet gets  "MAN": "MAN"  right after "IND".
Nothing else in the files is touched; files without a change are not rewritten, line
endings and the final newline stay as they are. Running it twice changes nothing.

Unlike tools/make_symbols.py this does NOT regenerate or delete symbols - hand-drawn
symbols stay as they are.

Usage (from the project folder):
    python tools/symbole_man_ergaenzen.py --pruefen      # only show what would change
    python tools/symbole_man_ergaenzen.py                # change the files in ./symbols
    python tools/symbole_man_ergaenzen.py "C:\\path\\to\\symbols"
"""
import json
import os
import sys

REIHENFOLGE = ("IND", "MAN", "TYP", "PER")


def _werte_neu(werte):
    """{IND, TYP, PER, ...} -> same plus MAN right after IND (order IND, MAN, TYP, PER)."""
    neu = {}
    for k in ("IND",):
        if k in werte:
            neu[k] = werte[k]
    neu["MAN"] = "MAN"
    for k, v in werte.items():
        if k not in neu:
            neu[k] = v
    return neu


def datei_bearbeiten(pfad, schreiben=True):
    """-> number of masks that got MAN (0 = file unchanged)."""
    with open(pfad, "r", encoding="utf-8", newline="") as f:
        roh = f.read()
    daten = json.loads(roh)
    block = daten.get("block") if isinstance(daten, dict) else None
    if not isinstance(block, dict):
        return 0
    n = 0
    for el in block.get("elemente", []):
        if isinstance(el, dict) and el.get("typ") == "maske":
            w = el.get("werte")
            if isinstance(w, dict) and "MAN" not in w:
                el["werte"] = _werte_neu(w)
                n += 1
    if n and schreiben:
        text = json.dumps(daten, indent=2, ensure_ascii=False)
        if "\r\n" in roh:
            text = text.replace("\n", "\r\n")
        if roh.endswith("\n"):
            text += "\r\n" if "\r\n" in roh else "\n"
        tmp = pfad + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp, pfad)
    return n


def main(argv):
    pruefen = "--pruefen" in argv
    args = [a for a in argv if not a.startswith("--")]
    wurzel = args[0] if args else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "symbols")
    if not os.path.isdir(wurzel):
        print("Ordner nicht gefunden:", wurzel)
        return 1
    dateien = geaendert = masken = fehler = 0
    for pfad, _d, namen in os.walk(wurzel):
        for fn in sorted(namen):
            if not fn.lower().endswith(".katieblock"):
                continue
            dateien += 1
            voll = os.path.join(pfad, fn)
            try:
                n = datei_bearbeiten(voll, schreiben=not pruefen)
            except (OSError, ValueError) as e:
                fehler += 1
                print("FEHLER", voll, e)
                continue
            if n:
                geaendert += 1
                masken += n
                print(("wuerde aendern: " if pruefen else "geaendert: ") + os.path.relpath(voll, wurzel), "(%d Maske)" % n)
    print("%d Dateien geprueft, %d %s, %d Masken ergaenzt, %d Fehler"
          % (dateien, geaendert, "wuerden geaendert" if pruefen else "geaendert", masken, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
