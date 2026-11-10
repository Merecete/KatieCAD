"""
katiecad/fileio/dwg_schreiben.py - DWG export without an external converter (ezdwg, MIT).

Translates an ezdxf document (the one KatieCAD builds for the DXF export) entity by entity into a
new ezdwg drawing and saves it. Contains NO Tkinter, ezdwg is imported on first use.

ezdwg writes a subset of entities. What it cannot write directly is converted to something it can
(ellipses / splines / bulge polylines -> lines and arcs, hatches -> boundary lines) or counted in
the report ("uebersprungen") so the user can be told. The ezdwg calls are made through
_aufruf(), which only passes the parameters the installed ezdwg version knows - so small API
differences between ezdwg versions do not break the export.
"""
import inspect
import math
from collections import Counter

VERSIONEN = {"R2000": "AC1015", "R2004": "AC1015", "R2007": "AC1032", "R2010": "AC1032",
             "R2013": "AC1032", "R2018": "AC1032", "AC1015": "AC1015", "AC1032": "AC1032"}

# ezdwg angle unit of add_arc: degrees (set to True if a test shows radians)
ARC_IN_RADIANTEN = False


class SchreibBericht:
    def __init__(self):
        self.geschrieben = 0
        self.uebersprungen = Counter()      # entity type -> count (not written)
        self.ersetzt = Counter()            # entity type -> count (written as lines / arcs)
        self.fehler = []                    # readable messages (first few)
        self.version = ""

    def text(self):
        t = [f"{self.geschrieben} Elemente geschrieben ({self.version})"]
        if self.ersetzt:
            t.append("als Linien/Bögen: " + ", ".join(f"{k} {v}" for k, v in self.ersetzt.items()))
        if self.uebersprungen:
            t.append("nicht übernommen: " + ", ".join(f"{k} {v}" for k, v in self.uebersprungen.items()))
        return "; ".join(t)


def verfuegbar():
    try:
        import ezdwg  # noqa: F401
        return hasattr(ezdwg, "new")
    except Exception:
        return False


def _aufruf(fn, *pos, **kw):
    """Calls fn, passing only the keyword arguments it accepts (None values dropped)."""
    kw = {k: v for k, v in kw.items() if v is not None}
    try:
        par = inspect.signature(fn).parameters
        if not any(p.kind == p.VAR_KEYWORD for p in par.values()):
            kw = {k: v for k, v in kw.items() if k in par}
    except (TypeError, ValueError):
        pass
    return fn(*pos, **kw)


def _a(e, name, standard=None):
    d = e.dxf
    try:
        if hasattr(d, "get"):
            w = d.get(name, standard)
        else:
            w = getattr(d, name, standard)
    except Exception:
        return standard
    return standard if w is None else w


def _p(v):
    """(x, y) from a Vec3 / tuple."""
    try:
        return (float(v[0]), float(v[1]))
    except TypeError:
        return (float(v.x), float(v.y))


def _farbe(e):
    """kwargs for colour: color_index (1..255) and / or true_color."""
    kw = {}
    c = _a(e, "color", 256)
    if isinstance(c, int) and 1 <= c <= 255:
        kw["color_index"] = c
    tc = _a(e, "true_color", None)
    if isinstance(tc, int):
        kw["true_color"] = tc
    return kw


def _flaeche_kw(e):
    kw = {"layer": _a(e, "layer", "0")}
    kw.update(_farbe(e))
    return kw


class _Schreiber:
    def __init__(self, drawing, bericht, ziel_version):
        self.d = drawing
        self.b = bericht
        self.neu = ziel_version
        self.kopf_bloecke = set()

    # ---- single entity types ------------------------------------------
    def linie(self, raum, p, q, kw):
        _aufruf(raum.add_line, p, q, **kw)

    def kreis(self, raum, e, kw):
        _aufruf(raum.add_circle, _p(e.dxf.center), radius=float(e.dxf.radius), **kw)

    def bogen(self, raum, mitte, r, a0, a1, kw):
        if ARC_IN_RADIANTEN:
            a0, a1 = math.radians(a0), math.radians(a1)
        fn = raum.add_arc
        par = {}
        try:
            par = inspect.signature(fn).parameters
        except (TypeError, ValueError):
            pass
        n0 = "start_angle" if "start_angle" in par or not par else ("start" if "start" in par else "start_angle")
        n1 = "end_angle" if "end_angle" in par or not par else ("end" if "end" in par else "end_angle")
        _aufruf(fn, mitte, radius=float(r), **{n0: a0, n1: a1}, **kw)

    def polylinie(self, raum, e, kw):
        pts = [tuple(p) for p in e.get_points("xyb")]
        geschl = bool(getattr(e, "closed", False))
        if any(abs(p[2]) > 1e-12 for p in pts):          # bulges: lines + arcs
            self.b.ersetzt["LWPOLYLINE"] += 1
            for v in e.virtual_entities():
                self.element(raum, v, kw_ueberschreiben=kw)
            return
        punkte = [(p[0], p[1]) for p in pts]
        try:
            _aufruf(raum.add_lwpolyline, punkte, closed=geschl, **kw)
        except Exception:
            self.b.ersetzt["LWPOLYLINE"] += 1
            self._streckenzug(raum, punkte, geschl, kw)

    def _streckenzug(self, raum, punkte, geschlossen, kw):
        paare = list(zip(punkte, punkte[1:]))
        if geschlossen and len(punkte) > 2:
            paare.append((punkte[-1], punkte[0]))
        for a, b in paare:
            self.linie(raum, a, b, kw)

    def text(self, raum, e, kw):
        t = _a(e, "text", "")
        _aufruf(raum.add_text, t, _p(_a(e, "insert", (0, 0))), height=float(_a(e, "height", 2.5)),
                rotation=float(_a(e, "rotation", 0.0)), **kw)

    def mtext(self, raum, e, kw):
        t = getattr(e, "text", "") or ""
        pos = _p(_a(e, "insert", (0, 0)))
        h = float(_a(e, "char_height", 2.5))
        rot = float(_a(e, "rotation", 0.0))
        try:
            _aufruf(raum.add_mtext, t, pos, height=h, rotation=rot, **kw)
            return
        except Exception:
            pass
        self.b.ersetzt["MTEXT"] += 1                      # fall back: one TEXT per line
        for i, zeile in enumerate(t.replace("\\P", "\n").split("\n")):
            x = pos[0] + math.sin(math.radians(rot)) * h * 1.5 * i
            y = pos[1] - math.cos(math.radians(rot)) * h * 1.5 * i
            _aufruf(raum.add_text, zeile, (x, y), height=h, rotation=rot, **kw)

    def einfuegung(self, raum, e, kw):
        name = _a(e, "name", "")
        ref = _aufruf(raum.add_blockref, name, insert=_p(_a(e, "insert", (0, 0))),
                      rotation=float(_a(e, "rotation", 0.0)),
                      xscale=_a(e, "xscale", None), yscale=_a(e, "yscale", None), **kw)
        for at in getattr(e, "attribs", []) or []:
            try:
                _aufruf(raum.add_attrib, ref, _a(at, "tag", ""), _a(at, "text", ""),
                        insert=_p(_a(at, "insert", (0, 0))), height=float(_a(at, "height", 2.5)))
            except Exception as ex:
                self.b.fehler.append(f"ATTRIB: {ex}")

    def ersatz(self, raum, e, art, kw):
        """ELLIPSE / SPLINE / HATCH -> lines of the outline."""
        try:
            if art == "HATCH":
                for pfad in e.paths:
                    pts = []
                    if hasattr(pfad, "vertices"):
                        pts = [(v[0], v[1]) for v in pfad.vertices]
                    elif hasattr(pfad, "edges"):
                        for ed in pfad.edges:
                            if hasattr(ed, "start"):
                                pts.append(_p(ed.start))
                    if len(pts) > 1:
                        self._streckenzug(raum, pts, True, kw)
                self.b.uebersprungen["HATCH (nur Rand)"] += 1
                return
            pts = [(float(v[0]), float(v[1])) for v in e.flattening(0.1)]
            if len(pts) > 1:
                self._streckenzug(raum, pts, False, kw)
                self.b.ersetzt[art] += 1
            else:
                self.b.uebersprungen[art] += 1
        except Exception:
            self.b.uebersprungen[art] += 1

    # ---- dispatcher --------------------------------------------------------
    def element(self, raum, e, kw_ueberschreiben=None):
        art = e.dxftype()
        kw = kw_ueberschreiben or _flaeche_kw(e)
        try:
            if art == "LINE":
                self.linie(raum, _p(e.dxf.start), _p(e.dxf.end), kw)
            elif art == "CIRCLE":
                self.kreis(raum, e, kw)
            elif art == "ARC":
                self.bogen(raum, _p(e.dxf.center), e.dxf.radius, e.dxf.start_angle, e.dxf.end_angle, kw)
            elif art == "LWPOLYLINE":
                self.polylinie(raum, e, kw)
                return self._gezaehlt(art)
            elif art == "TEXT":
                self.text(raum, e, kw)
            elif art == "MTEXT":
                self.mtext(raum, e, kw)
            elif art == "INSERT":
                self.einfuegung(raum, e, kw)
            elif art in ("ELLIPSE", "SPLINE", "HATCH"):
                self.ersatz(raum, e, art, kw)
                return self._gezaehlt(art)
            elif art == "POINT":
                _aufruf(raum.add_point, _p(e.dxf.location), **kw)
            else:
                self.b.uebersprungen[art] += 1
                return
            self.b.geschrieben += 1
        except Exception as ex:
            self.b.uebersprungen[art] += 1
            if len(self.b.fehler) < 8:
                self.b.fehler.append(f"{art}: {ex}")

    def _gezaehlt(self, art):
        if art not in self.b.uebersprungen:
            self.b.geschrieben += 1

    # ---- tables ---------------------------------------------------------------
    def ebenen(self, doc):
        try:
            for l in doc.layers:
                name = l.dxf.name
                if name == "0":
                    continue
                d = {}
                tc = _a(l, "true_color", None)
                if isinstance(tc, int):
                    d["true_color"] = tc
                else:
                    aci = abs(int(_a(l, "color", 7)))
                    try:
                        from ezdxf.colors import aci2rgb
                        r, g, b = aci2rgb(aci)
                        d["true_color"] = (r << 16) | (g << 8) | b
                    except Exception:
                        d["color_index"] = aci
                try:
                    self.d.layers[name] = d
                except Exception:
                    self.d.layers[name] = {k: v for k, v in d.items() if k == "color_index"} or {}
        except Exception as ex:
            self.b.fehler.append(f"Layer: {ex}")

    def bloecke(self, doc):
        for blk in doc.blocks:
            n = blk.name
            if n.startswith("*"):
                continue
            try:
                try:
                    bd = self.d.blocks.new(n, base_point=tuple(blk.block.dxf.base_point))
                except Exception:
                    bd = self.d.blocks.new(n)
                for e in blk:
                    self.element(bd, e)
            except Exception as ex:
                self.b.fehler.append(f"Block {n}: {ex}")


def dxf_doc_zu_dwg(doc, pfad, version="R2018"):
    """Writes the ezdxf document as DWG. Returns a SchreibBericht, raises RuntimeError."""
    try:
        import ezdwg
    except Exception as ex:
        raise RuntimeError(f"ezdwg nicht verfügbar: {ex}")
    ziel = VERSIONEN.get(str(version).upper(), "AC1032")
    letzter = None
    for v in ((ziel, "AC1015") if ziel != "AC1015" else ("AC1015",)):
        bericht = SchreibBericht()
        bericht.version = v
        try:
            drawing = ezdwg.new(v) if v != "AC1015" else ezdwg.new()
            s = _Schreiber(drawing, bericht, v)
            s.ebenen(doc)
            s.bloecke(doc)
            raum = drawing.modelspace()
            for e in doc.modelspace():
                s.element(raum, e)
            _aufruf(drawing.save, pfad, strict=False)     # unsupported parts were counted above
            return bericht
        except Exception as ex:                              # try the older format once
            letzter = ex
    raise RuntimeError(f"DWG-Export mit ezdwg fehlgeschlagen: {letzter}")
