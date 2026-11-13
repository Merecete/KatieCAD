"""Spanish tag names of title blocks are filled in automatically."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub  # noqa: F401
from katiecad.model import titleblock as TB
from katiecad.model.core import AttributDefinition, Viewport

ok = 0
def check(c, m):
    global ok
    assert c, "FEHLER: " + m
    ok += 1

tags = ["DIBUJADO", "DIBUJADO_FECHA", "REVISADO", "REVISADO_FECHA", "NUMEROPLANO", "PAGINA",
        "FORMATO", "UBICACION", "TITULO1", "TITULO2", "TITULO3", "EMPRESA", "CLIENTE",
        "ESTADO1", "MODIFICACION1", "MODIFICACION1_NOMBRE", "MODIFICACION1_FECHA",
        "MODIFICACION4", "MODIFICACION4_NOMBRE", "MODIFICACION4_FECHA", "ESTADO3"]
for t in tags:
    check(TB.is_auto_tag(t), "automatisch: " + t)
check(not TB.is_auto_tag("MI_CAMPO_LIBRE"), "freies Feld bleibt frei")
check(TB.parse_rev_tag("MODIFICACION2_NOMBRE") == (2, "name"), "Zeile 2 Name")
check(TB.parse_rev_tag("MODIFICACION3_FECHA") == (3, "datum"), "Zeile 3 Fecha")
check(TB.parse_rev_tag("ESTADO4") == (4, "stand"), "Zeile 4 Estado")

daten = {"gezeichnet": "Ana", "geprueft": "Luis", "zeichnungsnummer": "E-01", "kunde": "ACME",
         "rev": [{"stand": "A", "aenderung": "Cambio", "name": "Ana", "datum": "01.01.2026"}]}
info = TB.info_values(2, 5, "Hoja X", "Planta", "es", "A3 (420x297)", None, daten, "Sala 1")
v = {"DIBUJADO": "Ana", "REVISADO": "Luis", "NUMEROPLANO": "E-01", "PAGINA": "2", "FORMATO": "A3",
     "UBICACION": "Sala 1", "TITULO1": "ACME", "TITULO3": "Hoja X", "ESTADO1": None}
for k, w in v.items():
    if w is not None:
        check(info.get(k) == w, f"{k} = {w} (ist {info.get(k)!r})")
check(info.get("REV1_INDICE") == "A" and info.get("REV1_MODIFICACION") == "Cambio", "Revisionszeile")

# ends up in the attribute dictionary of a title block
ads = [AttributDefinition(0, i * 5, None, 2.5, 0.0, "Arial", "unten_links", tag=t, prompt=t, wert="")
       for i, t in enumerate(["DIBUJADO", "PAGINA", "FORMATO", "MODIFICACION1", "MODIFICACION1_NOMBRE", "ESTADO1"])]
blk = TB.make_block("t_es", ads, 297, 210)
n = TB.refresh_fields([blk], info, "1:1")
check(blk.attribute.get("DIBUJADO") == "Ana" and blk.attribute.get("PAGINA") == "2"
      and blk.attribute.get("FORMATO") == "A3", "Felder werden gefuellt")
check(blk.attribute.get("MODIFICACION1") == "Cambio" and blk.attribute.get("MODIFICACION1_NOMBRE") == "Ana"
      and blk.attribute.get("ESTADO1") == "A", "Revisionstabelle wird gefuellt")
print(f"test_titelblock_es - OK ({ok} Pruefungen)")
