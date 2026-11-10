"""DWG import diagnosis (run on your PC):  python tools/dwg_diagnose.py datei.dwg [ausgabe.dxf]

Reads the DWG with the built-in ezdwg (LibreDWG as fallback), and prints: entity types in the model space, extents, blocks with base points and INSERTs. Optionally
saves the converted DXF of each engine next to the given path (name_<engine>.dxf) so you can open
them in a CAD program and compare - this shows whether a wrong picture comes from the DWG
conversion or from KatieCAD's import.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from katiecad.fileio import cad_import


def bericht(doc, name, ausgabe):
    msp = doc.modelspace()
    arten = Counter(e.dxftype() for e in msp)
    print(f"\n=== {name} ===")
    print("Modellbereich:", dict(arten))
    try:
        from ezdxf import bbox
        b = bbox.extents(msp)
        print("Ausdehnung:", b.extmin, "bis", b.extmax)
    except Exception as ex:
        print("Ausdehnung: nicht berechenbar:", ex)
    bl = [b for b in doc.blocks if not b.name.startswith("*")]
    print(f"Blöcke: {len(bl)}")
    for b in bl[:25]:
        try:
            bp = tuple(b.block.dxf.base_point)
        except Exception:
            bp = "?"
        print(f"  {b.name}: {len(list(b))} Elemente, Basispunkt {bp}, "
              f"Typen {dict(Counter(e.dxftype() for e in b))}")
    ins = [e for e in msp if e.dxftype() == "INSERT"]
    for e in ins[:15]:
        d = e.dxf
        print(f"  INSERT {d.name}: Pos {tuple(d.insert)}, Skala "
              f"({d.get('xscale', 1)}, {d.get('yscale', 1)}, {d.get('zscale', 1)}), "
              f"Drehung {d.get('rotation', 0)}, Extrusion {tuple(d.get('extrusion', (0, 0, 1)))}")
    if ausgabe:
        ziel = os.path.splitext(ausgabe)[0] + "_" + name.replace(" ", "_") + ".dxf"
        doc.saveas(ziel)
        print("DXF gespeichert:", ziel)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    pfad = sys.argv[1]
    ausgabe = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        doc, quelle = cad_import.dwg_zu_dxf_doc(pfad)
        bericht(doc, quelle, ausgabe)
    except Exception as ex:
        print(f"\n=== DWG nicht lesbar: {ex}")


if __name__ == "__main__":
    main()
