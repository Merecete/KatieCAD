"""DWG export test (run on your PC):  python tools/dwg_test.py [ausgabeordner]

Builds a small ezdxf drawing with all common entity types, writes it as DWG with the built-in
ezdwg writer (and with the ODA File Converter, if installed, for comparison), reads the
files back with ezdwg and prints what arrived. Then open the *.dwg files in AutoCAD / another CAD
program and compare with the DXF written next to them.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ezdxf
from katiecad.fileio import dwg_schreiben, cad_import


def beispiel():
    doc = ezdxf.new("R2018", setup=True)
    doc.layers.add("WAND", color=6)
    doc.layers.add("ROT", color=1)
    doc.layers.add("TRUE", dxfattribs={"true_color": 0x3D7FD1})
    msp = doc.modelspace()
    msp.add_line((0, 0), (100, 0), dxfattribs={"layer": "ROT"})
    msp.add_circle((50, 50), 20, dxfattribs={"layer": "TRUE"})
    msp.add_arc((50, 50), 30, 0, 90)                       # 0..90 degrees: quarter circle top right
    msp.add_lwpolyline([(0, 0), (40, 0), (40, 30), (0, 30)], close=True, dxfattribs={"layer": "WAND"})
    msp.add_lwpolyline([(120, 0, 0.5), (160, 0, 0), (160, 30, 0)], format="xyb")  # with bulge
    msp.add_text("Test ABC äöü", dxfattribs={"insert": (0, 60), "height": 5, "rotation": 15})
    msp.add_mtext("Zeile 1\\PZeile 2", dxfattribs={"insert": (0, 80), "char_height": 4})
    blk = doc.blocks.new("TESTBLOCK")
    blk.add_line((0, 0), (10, 10))
    blk.add_circle((5, 5), 3)
    blk.add_attdef("ID", (0, 12), dxfattribs={"height": 2})
    ref = msp.add_blockref("TESTBLOCK", (200, 0), dxfattribs={"rotation": 30})
    ref.add_auto_attribs({"ID": "P-001"})
    msp.add_ellipse((250, 30), major_axis=(30, 0), ratio=0.5)
    msp.add_spline([(300, 0), (320, 30), (340, -10), (360, 20)])
    h = msp.add_hatch(color=2)
    h.paths.add_polyline_path([(400, 0), (430, 0), (430, 30), (400, 30)], is_closed=True)
    return doc


def zaehlen(pfad):
    import ezdwg
    d = ezdwg.read(pfad)
    try:
        from collections import Counter
        c = Counter(e.dxftype if isinstance(getattr(e, "dxftype", None), str) else type(e).__name__
                    for e in d.modelspace().query())
        return dict(c)
    except Exception as ex:
        return f"gelesen (Zählung nicht möglich: {ex})"


def main():
    ziel = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="katiecad_dwgtest_")
    os.makedirs(ziel, exist_ok=True)
    doc = beispiel()
    doc.saveas(os.path.join(ziel, "vergleich.dxf"))
    print("Ordner:", ziel)
    for version in ("R2018", "R2000"):
        pfad = os.path.join(ziel, f"ezdwg_{version}.dwg")
        try:
            b = dwg_schreiben.dxf_doc_zu_dwg(doc, pfad, version)
            print(f"[ezdwg {version}] {b.text()}")
            for f in b.fehler:
                print("   Hinweis:", f)
            print("   zurückgelesen:", zaehlen(pfad))
        except Exception as ex:
            print(f"[ezdwg {version}] FEHLER: {ex}")
    if cad_import.oda_verfuegbar():
        pfad = os.path.join(ziel, "oda.dwg")
        try:
            cad_import.DWG_MOTOR = "oda"
            print("[ODA]", cad_import.dxf_doc_als_dwg_speichern(doc, pfad))
            print("   zurückgelesen:", zaehlen(pfad))
        except Exception as ex:
            print("[ODA] FEHLER:", ex)
    else:
        print("[ODA] nicht installiert (nur zum Vergleich, nicht nötig)")
    print("\nBitte die *.dwg in AutoCAD o.ä. öffnen und mit vergleich.dxf vergleichen.")
    print("Der Viertelbogen (Radius 30) muss oben rechts vom Kreismittelpunkt (50,50) liegen;"
          " liegt er falsch, steht in dwg_schreiben.py ARC_IN_RADIANTEN auf True.")


if __name__ == "__main__":
    main()
