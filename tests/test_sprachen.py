# -*- coding: utf-8 -*-
"""Languages: German, English and Spanish have the same keys and placeholders."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
import katiecad.common.i18n as I
from katiecad.common import config as C
ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

T = I.TEXTE
check(set(T) == {"de", "en", "es"}, "Sprachen de/en/es")
for sp in ("en", "es"):
    check(set(T[sp]) == set(T["de"]), f"{sp}: gleiche Schluessel wie de: {sorted(set(T['de']) ^ set(T[sp]))[:5]}")
    schlecht = [k for k in T["de"] if sorted(re.findall(r"\{\w+\}", T[sp][k])) != sorted(re.findall(r"\{\w+\}", T["de"][k]))]
    check(not schlecht, f"{sp}: Platzhalter stimmen: {schlecht[:5]}")
    check(all(str(v).strip() for v in T[sp].values()), f"{sp}: keine leeren Texte")
for k in ("menu.sprache.de", "menu.sprache.en", "menu.sprache.es"):
    check(all(k in T[sp] for sp in T), k)
check("es" in C._UNTERSTUETZTE_SPRACHEN, "config kennt es")
# fallback: Spanish -> English -> German
I.SPRACHE["aktuell"] = "es"
_alt = T["es"].pop("menu.datei")
check(I.tr("menu.datei") == T["en"]["menu.datei"], "fehlender spanischer Text faellt auf Englisch zurueck")
T["es"]["menu.datei"] = _alt
check(I.tr("menu.datei") == "Archivo", "spanischer Text")
I.SPRACHE["aktuell"] = "de"
print(f"OK ({ok} Pruefungen)")
