# -*- coding: utf-8 -*-
"""
katiecad/ui/kt/canvas.py - tk.Canvas on Kivy/OpenGL (BSD-3-Clause).

Items keep Tk's model (ids, tags, stacking order, coordinates with y downwards). Drawing
instructions are only built when the next frame is drawn, and not item by item: the items
are kept in blocks of _BLOCK in stacking order, and consecutive simple lines, rectangles
and filled ovals of one colour in a block are merged into one Kivy Mesh (built with NumPy),
so thousands of items cost only a few GPU calls. A change only rebuilds its block. Every
frame stays complete and exact - nothing is left out or simplified while zooming.

All blocks sit under one flip transform, so they are drawn in Tk coordinates directly by
the GPU. Scrolling only changes that transform. See docs/KIVY_SCHICHT.md.
"""

import math

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import (Color, Rectangle, Line, Ellipse, Mesh, InstructionGroup,
                           PushMatrix, PopMatrix, Translate, Scale, Rotate)
from kivy.graphics.tesselator import Tesselator, WINDING_ODD, TYPE_POLYGONS

from katiecad.ui.kt import _base, fontmod
from katiecad.ui.kt import tkmod as T


def _flach(args):
    try:
        return [float(a) for a in args]            # usual case: plain numbers
    except TypeError:
        pass
    erg = []
    for a in args:
        if isinstance(a, (tuple, list)):
            erg.extend(_flach(a))
        else:
            erg.append(float(a))
    return erg


_FARBEN = {}


def _farbe(v):
    """Tk colour (name or #rgb) -> RGBA tuple for Kivy, None for "" / None (no fill / no
    outline). Cached, because the same few colours are used by thousands of items.
    """
    try:
        return _FARBEN[v]
    except (KeyError, TypeError):
        pass
    if v is None or v == "":
        return None
    try:
        f = _base.farbe(v)
    except T.TclError:
        f = None
    try:
        _FARBEN[v] = f
    except TypeError:
        pass
    return f


def _stipple(f, stipple):
    if f is not None and stipple:
        a = {"gray75": 0.75, "gray50": 0.5, "gray25": 0.3, "gray12": 0.15}.get(str(stipple), 0.5)
        return (f[0], f[1], f[2], f[3] * a)
    return f


class _Item:
    __slots__ = ("id", "typ", "xy", "o", "tags", "g", "bbox", "blk", "lk", "lp", "neu")

    def __init__(self, ident, typ, xy, o, tags):
        self.id, self.typ, self.xy, self.o, self.tags = ident, typ, xy, o, tags
        self.g = InstructionGroup()
        self.bbox = None
        self.blk = None          # the block (batch of items) it is drawn in
        # run key: items with the same key that follow each other share one mesh of the block
        # (colour, width, round caps); width -1.0 = filled oval, -2.0 = rectangle
        self.lk = None
        self.lp = None           # its points (line) or box (oval, rectangle)
        self.neu = True          # instructions not built yet (done when the frame is drawn)


_BLOCK = 400                     # items per block


class _Block:
    """Up to _BLOCK consecutive items (stacking order). Simple lines of one colour that follow
    each other are drawn as one mesh; a change only rebuilds the block it is in."""
    __slots__ = ("items", "g", "dirty")

    def __init__(self):
        self.items = {}
        self.g = InstructionGroup()
        self.dirty = True


try:
    import numpy as _np
except ImportError:              # pragma: no cover - numpy comes with ezdxf
    _np = None

_KREIS = {}


def _kreis(r):
    """Unit polygon for round caps/joins of a line of radius r."""
    n = 6 if r <= 2 else (10 if r <= 4 else 16)
    k = _KREIS.get(n)
    if k is None:
        k = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n)]
        _KREIS[n] = k
    return k


def _fugen(g, x0, y0, x1, y1, weiter, h, items):
    """Joins of long polylines (circles, arcs, splines are drawn as many short segments):
    two triangles per inner point close the gap between neighbouring segments, so curves
    look as closed as Tk's round joins. Short polylines get round discs instead."""
    if not any(weiter):
        return
    lang = []
    i = 0
    for it in items:                         # only polylines with more than 12 points
        m = len(it.lp) // 2
        k = max(0, m - 1)
        if m > 12:
            lang += range(i, i + k - 1)
        i += k
    if not lang:
        return
    if _np is not None:
        a = _np.array((x0, y0, x1, y1), dtype=_np.float64)
        dx, dy = a[2] - a[0], a[3] - a[1]
        ln = _np.hypot(dx, dy)
        ln[ln == 0] = 1.0
        nx, ny = -dy / ln * h, dx / ln * h
        j = _np.array(lang, dtype=_np.int64)
        px, py = a[2, j], a[3, j]
        n1x, n1y, n2x, n2y = nx[j], ny[j], nx[j + 1], ny[j + 1]
        k = len(j)
        for s0 in range(0, k, 12000):
            s1 = min(k, s0 + 12000)
            q = s1 - s0
            v = _np.zeros((q, 5, 4), dtype=_np.float32)
            v[:, 0, 0], v[:, 0, 1] = px[s0:s1], py[s0:s1]
            v[:, 1, 0], v[:, 1, 1] = px[s0:s1] + n1x[s0:s1], py[s0:s1] + n1y[s0:s1]
            v[:, 2, 0], v[:, 2, 1] = px[s0:s1] + n2x[s0:s1], py[s0:s1] + n2y[s0:s1]
            v[:, 3, 0], v[:, 3, 1] = px[s0:s1] - n1x[s0:s1], py[s0:s1] - n1y[s0:s1]
            v[:, 4, 0], v[:, 4, 1] = px[s0:s1] - n2x[s0:s1], py[s0:s1] - n2y[s0:s1]
            idx = (_np.arange(q, dtype=_np.uint16)[:, None] * 5 +
                   _np.array((0, 1, 2, 0, 3, 4), dtype=_np.uint16)[None, :]).ravel()
            g.add(Mesh(vertices=v.ravel(), indices=idx, mode="triangles"))
        return
    verts, idx, n = [], [], 0
    for i in lang:
        def nrm(t):
            dx, dy = x1[t] - x0[t], y1[t] - y0[t]
            ln = math.hypot(dx, dy) or 1.0
            return -dy / ln * h, dx / ln * h
        (a1, b1), (a2, b2) = nrm(i), nrm(i + 1)
        px, py = x1[i], y1[i]
        verts += (px, py, 0.0, 0.0, px + a1, py + b1, 0.0, 0.0, px + a2, py + b2, 0.0, 0.0,
                  px - a1, py - b1, 0.0, 0.0, px - a2, py - b2, 0.0, 0.0)
        idx += (n, n + 1, n + 2, n, n + 3, n + 4)
        n += 5
        if n > 60000:
            g.add(Mesh(vertices=verts, indices=idx, mode="triangles"))
            verts, idx, n = [], [], 0
    if idx:
        g.add(Mesh(vertices=verts, indices=idx, mode="triangles"))


def _dicke_mesh(g, farbe, w, items):
    """Thick lines of one colour/width: quads per segment + discs for round caps and
    corners, all in as few meshes as possible."""
    h = w / 2.0
    x0, y0, x1, y1 = [], [], [], []
    weiter = []                              # per segment: the next one continues the polyline
    punkte = []                              # discs (caps / corners)
    for it in items:
        pts = it.lp
        x0 += pts[0:-2:2]
        y0 += pts[1:-2:2]
        x1 += pts[2::2]
        y1 += pts[3::2]
        m = len(pts) // 2
        weiter += [True] * (m - 2) + [False] if m >= 2 else []
        if it.lk[2]:                         # round caps
            punkte += ((pts[0], pts[1]), (pts[-2], pts[-1]))
        if 2 < m <= 12:                      # corners of short polylines: round discs
            punkte += [(pts[2 * j], pts[2 * j + 1]) for j in range(1, m - 1)]
    kreis = _kreis(h)
    nk = len(kreis)
    g.add(Color(*farbe))
    _fugen(g, x0, y0, x1, y1, weiter, h, items)
    if _np is not None and len(x0) >= 64:      # numpy only pays off for larger runs
        a = _np.array((x0, y0, x1, y1), dtype=_np.float64)
        dx, dy = a[2] - a[0], a[3] - a[1]
        ln = _np.hypot(dx, dy)
        ln[ln == 0] = 1.0
        nx, ny = -dy / ln * h, dx / ln * h
        n = len(x0)
        for s0 in range(0, n, 15000):
            s1 = min(n, s0 + 15000)
            k = s1 - s0
            v = _np.zeros((k, 4, 4), dtype=_np.float32)
            v[:, 0, 0] = a[0, s0:s1] + nx[s0:s1]
            v[:, 0, 1] = a[1, s0:s1] + ny[s0:s1]
            v[:, 1, 0] = a[2, s0:s1] + nx[s0:s1]
            v[:, 1, 1] = a[3, s0:s1] + ny[s0:s1]
            v[:, 2, 0] = a[2, s0:s1] - nx[s0:s1]
            v[:, 2, 1] = a[3, s0:s1] - ny[s0:s1]
            v[:, 3, 0] = a[0, s0:s1] - nx[s0:s1]
            v[:, 3, 1] = a[1, s0:s1] - ny[s0:s1]
            idx = (_np.arange(k, dtype=_np.uint16)[:, None] * 4 +
                   _np.array((0, 1, 2, 0, 2, 3), dtype=_np.uint16)).ravel()
            g.add(Mesh(vertices=v.ravel(), indices=idx, mode="triangles"))
    elif x0:
        verts, idx, n = [], [], 0
        for i in range(len(x0)):
            dx, dy = x1[i] - x0[i], y1[i] - y0[i]
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln * h, dx / ln * h
            verts += (x0[i] + nx, y0[i] + ny, 0.0, 0.0, x1[i] + nx, y1[i] + ny, 0.0, 0.0,
                      x1[i] - nx, y1[i] - ny, 0.0, 0.0, x0[i] - nx, y0[i] - ny, 0.0, 0.0)
            idx += (n, n + 1, n + 2, n, n + 2, n + 3)
            n += 4
            if n > 60000:
                g.add(Mesh(vertices=verts, indices=idx, mode="triangles"))
                verts, idx, n = [], [], 0
        if idx:
            g.add(Mesh(vertices=verts, indices=idx, mode="triangles"))
    if punkte:
        # discs: same index pattern for every disc, only shifted -> built once per size
        ring = [(cx * h, cy * h) for cx, cy in kreis]
        muster = []
        for j in range(nk):
            muster += (0, 1 + j, 1 + (j + 1) % nk)
        pro = nk + 1
        max_n = 60000 // pro
        if _np is not None and len(punkte) >= 32:
            p = _np.array(punkte, dtype=_np.float32)
            r = _np.array([(0.0, 0.0)] + ring, dtype=_np.float32)            # centre + ring
            muster_a = _np.array(muster, dtype=_np.uint16)
            for s0 in range(0, len(p), max_n):
                teil = p[s0:s0 + max_n]
                k = len(teil)
                v = _np.zeros((k, pro, 4), dtype=_np.float32)
                v[:, :, :2] = teil[:, None, :] + r[None, :, :]
                idx = (_np.arange(k, dtype=_np.uint16)[:, None] * pro + muster_a[None, :]).ravel()
                g.add(Mesh(vertices=v.ravel(), indices=idx, mode="triangles"))
            return
        for s0 in range(0, len(punkte), max_n):
            teil = punkte[s0:s0 + max_n]
            verts = []
            for px, py in teil:
                verts += (px, py, 0.0, 0.0)
                for cx, cy in ring:
                    verts += (px + cx, py + cy, 0.0, 0.0)
            idx = [i + k * pro for k in range(len(teil)) for i in muster]
            g.add(Mesh(vertices=verts, indices=idx, mode="triangles"))


def _rechtecke_mesh(g, farbe, items):
    """Filled rectangles of one colour as quads of one mesh."""
    verts, idx, n = [], [], 0
    g.add(Color(*farbe))
    for it in items:
        x0, y0, x1, y1 = it.lp
        verts += (x0, y0, 0.0, 0.0, x1, y0, 0.0, 0.0, x1, y1, 0.0, 0.0, x0, y1, 0.0, 0.0)
        idx += (n, n + 1, n + 2, n, n + 2, n + 3)
        n += 4
        if n > 60000:
            g.add(Mesh(vertices=verts, indices=idx, mode="triangles"))
            verts, idx, n = [], [], 0
    if idx:
        g.add(Mesh(vertices=verts, indices=idx, mode="triangles"))


def _ovale_mesh(g, farbe, items):
    """Filled ovals of one colour as triangles of one mesh."""
    _ovale_boxen(g, farbe, [it.lp for it in items])


def _ovale_boxen(g, farbe, boxen):
    """Filled ellipses (x0, y0, x1, y1) of one colour; ellipses with the same number of
    segments are generated together with numpy (e.g. thousands of grid dots)."""
    g.add(Color(*farbe))
    gruppen = {}
    for b in boxen:
        n = max(8, min(64, int(max(b[2] - b[0], b[3] - b[1]) * 0.75) + 6))
        gruppen.setdefault(n, []).append(b)
    for n, bl in gruppen.items():
        k = _kreis_n(n)
        pro = n + 1
        muster = []
        for j in range(n):
            muster += (0, 1 + j, 1 + (j + 1) % n)
        max_n = 60000 // pro
        for s0 in range(0, len(bl), max_n):
            teil = bl[s0:s0 + max_n]
            if _np is not None and len(teil) >= 16:
                a = _np.array(teil, dtype=_np.float32)
                c = _np.stack(((a[:, 0] + a[:, 2]) / 2, (a[:, 1] + a[:, 3]) / 2), axis=1)
                rr = _np.stack(((a[:, 2] - a[:, 0]) / 2, (a[:, 3] - a[:, 1]) / 2), axis=1)
                ring = _np.array([(0.0, 0.0)] + k, dtype=_np.float32)       # centre + ring
                v = _np.zeros((len(teil), pro, 4), dtype=_np.float32)
                v[:, :, :2] = c[:, None, :] + ring[None, :, :] * rr[:, None, :]
                idx = (_np.arange(len(teil), dtype=_np.uint16)[:, None] * pro +
                       _np.array(muster, dtype=_np.uint16)[None, :]).ravel()
                g.add(Mesh(vertices=v.ravel(), indices=idx, mode="triangles"))
                continue
            verts = []
            for x0, y0, x1, y1 in teil:
                cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
                verts += (cx, cy, 0.0, 0.0)
                for ux, uy in k:
                    verts += (cx + ux * rx, cy + uy * ry, 0.0, 0.0)
            idx = [i + q * pro for q in range(len(teil)) for i in muster]
            g.add(Mesh(vertices=verts, indices=idx, mode="triangles"))


def _ring_ovale(g, farben, items):
    """Ovals with a 1 px outline in another colour (grid dots): outline as the larger
    ellipse, fill on top - like Tk's fill + outline."""
    rand, fuellung = farben
    # pixel box like Tk/GDI: pixels floor(x0) .. floor(x1); the outline is its outer pixel ring
    # (canvas coordinates are pixel centres, so the box edges lie half a pixel outside)
    aussen, innen = [], []
    for it in items:
        x0, y0, x1, y1 = (math.floor(v) for v in it.lp)
        aussen.append((x0 - 0.5, y0 - 0.5, x1 + 0.5, y1 + 0.5))
        if x1 - x0 >= 2 and y1 - y0 >= 2:
            innen.append((x0 + 0.5, y0 + 0.5, x1 - 0.5, y1 - 0.5))
    _ovale_boxen(g, rand, aussen)
    if innen:
        _ovale_boxen(g, fuellung, innen)


def _kreis_n(n):
    k = _KREIS.get(n)
    if k is None:
        k = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n)]
        _KREIS[n] = k
    return k


def _lauf_meshes(g, farbe, lauf):
    """All geometry of one run (one colour): thin lines as GL lines, thick lines, filled
    rectangles and ovals as triangles - two or three meshes for the whole run."""
    duenn, dick, rechtecke, ovale = [], {}, [], []
    if lauf[0].lk[1] == -3.0:                 # key = (outline, fill): only ring ovals
        _ring_ovale(g, farbe, lauf)
        return
    for it in lauf:
        w = it.lk[1]
        if w == -2.0:
            rechtecke.append(it)
        elif w < 0:
            ovale.append(it)
        elif w <= 1.5:
            duenn.append(it.lp)
        else:
            dick.setdefault(w, []).append(it)
    if duenn:
        _duenne_mesh(g, farbe, duenn)
    for w, items in dick.items():
        _dicke_mesh(g, farbe, w, items)
    if rechtecke:
        _rechtecke_mesh(g, farbe, rechtecke)
    if ovale:
        _ovale_mesh(g, farbe, ovale)


def _duenne_mesh(g, farbe, polylinien):
    """1 px lines (GL lines, like Tk's): one mesh per 60000 points."""
    g.add(Color(*farbe))
    if _np is not None and len(polylinien) > 64:
        laengen = [len(p) // 2 for p in polylinien]
        alle = _np.fromiter((v for p in polylinien for v in p), dtype=_np.float32)
        pkt = alle.reshape(-1, 2)
        n = len(pkt)
        # segment j -> (j, j + 1) unless j is the last point of its polyline
        ende = _np.cumsum(laengen) - 1
        start = _np.ones(n, dtype=bool)
        start[ende] = False
        seg = _np.nonzero(start)[0]
        for s0 in range(0, n, 60000):
            s1 = min(n, s0 + 60000)
            teil = seg[(seg >= s0) & (seg < s1 - 1)]
            # segments crossing the chunk border go into the next chunk
            v = _np.zeros((s1 - s0, 4), dtype=_np.float32)
            v[:, :2] = pkt[s0:s1]
            idx = _np.empty(len(teil) * 2, dtype=_np.uint16)
            idx[0::2] = teil - s0
            idx[1::2] = teil - s0 + 1
            if len(idx):
                g.add(Mesh(vertices=v.ravel(), indices=idx, mode="lines"))
            rest = seg[seg == s1 - 1]
            if len(rest) and s1 < n:
                g.add(Mesh(vertices=_np.array([pkt[s1 - 1, 0], pkt[s1 - 1, 1], 0, 0,
                                                pkt[s1, 0], pkt[s1, 1], 0, 0], dtype=_np.float32),
                           indices=_np.array([0, 1], dtype=_np.uint16), mode="lines"))
        return
    verts, idx, n = [], [], 0
    for pts in polylinien:
        m = len(pts) // 2
        for j in range(m):
            verts += (pts[2 * j], pts[2 * j + 1], 0.0, 0.0)
        for j in range(m - 1):
            idx += (n + j, n + j + 1)
        n += m
        if n > 60000:
            g.add(Mesh(vertices=verts, indices=idx, mode="lines"))
            verts, idx, n = [], [], 0
    if idx:
        g.add(Mesh(vertices=verts, indices=idx, mode="lines"))


def _geo_bbox(it):
    """Box of a geometry item of the shared meshes (incl. line width)."""
    lp = it.lp
    w = it.lk[1]
    if w < 0:
        return lp[0], lp[1], lp[2], lp[3]
    xs, ys = lp[0::2], lp[1::2]
    h = w / 2.0 + 1.0
    return min(xs) - h, min(ys) - h, max(xs) + h, max(ys) + h


def _item_box(it):
    """Box of another item (text, image, dashed line ...) - only for the overlap test."""
    if it.bbox is not None:
        return it.bbox
    xy = it.xy
    if len(xy) < 2:
        return None
    w = float(it.o.get("width", 1) or 1) / 2.0 + 1.0
    xs, ys = xy[0::2], xy[1::2]
    return min(xs) - w, min(ys) - w, max(xs) + w, max(ys) + w


def _harte_stellen(liste):
    """Indices of the non-geometry items that must keep their exact place in the stacking
    order: those overlapped by geometry that comes after them. All others may be drawn after
    the geometry of the block - which looks exactly the same, because nothing there covers
    them - so the geometry is not cut into many small meshes."""
    geo = [(i, _geo_bbox(it)) for i, it in enumerate(liste) if it.lk is not None]
    andere = [(i, it) for i, it in enumerate(liste) if it.lk is None]
    if not geo or not andere:
        return set(i for i, _it in andere)
    hart = set()
    if _np is not None and len(geo) > 32:
        seq = _np.array([i for i, _b in geo])
        bb = _np.array([b for _i, b in geo], dtype=_np.float64)
        for i, it in andere:
            r = _item_box(it)
            if r is None:
                continue
            m = (seq > i) & (bb[:, 0] <= r[2]) & (bb[:, 2] >= r[0]) & (bb[:, 1] <= r[3]) & (bb[:, 3] >= r[1])
            if m.any():
                hart.add(i)
    else:
        for i, it in andere:
            r = _item_box(it)
            if r is None:
                continue
            for j, b in geo:
                if j > i and b[0] <= r[2] and b[2] >= r[0] and b[1] <= r[3] and b[3] >= r[1]:
                    hart.add(i)
                    break
    return hart


def _block_bauen(b):
    """Rebuilds the drawing instructions of one block. Consecutive geometry items with the same
    run key (colour, width ...) become one mesh (_lauf_meshes). Other items (texts, images,
    irregular shapes) are drawn after the geometry of the block unless geometry that comes
    later overlaps them (_harte_stellen) - only then the geometry run is closed at their
    place, so the stacking order stays exactly that of Tk.
    """
    g = b.g
    g.clear()
    liste = list(b.items.values())
    hart = _harte_stellen(liste)
    lauf = []
    key = None
    wartend = []                 # other items drawn after the current geometry (see above)

    def fertig():
        if lauf:
            _lauf_meshes(g, key, lauf)

    for i, it in enumerate(liste):
        k = it.lk
        if k is None:
            if i in hart:                     # exact place: close the geometry before it
                fertig()
                lauf, key = [], None
                for w_ in wartend:
                    g.add(w_.g)
                wartend = []
                g.add(it.g)
            else:
                wartend.append(it)
            continue
        if k[0] != key:
            fertig()
            lauf, key = [], k[0]
        lauf.append(it)
    fertig()
    for w_ in wartend:
        g.add(w_.g)


_STANDARD = {
    "line": {"fill": "black", "width": 1.0, "dash": "", "capstyle": "butt", "joinstyle": "round",
             "smooth": False, "splinesteps": 12, "arrow": "none", "state": "", "stipple": "",
             "arrowshape": (8, 10, 3), "dashoffset": 0},
    "rectangle": {"fill": "", "outline": "black", "width": 1.0, "dash": "", "state": "",
                  "stipple": ""},
    "oval": {"fill": "", "outline": "black", "width": 1.0, "dash": "", "state": "", "stipple": ""},
    "polygon": {"fill": "black", "outline": "", "width": 1.0, "dash": "", "smooth": False,
                "splinesteps": 12, "joinstyle": "round", "state": "", "stipple": ""},
    "arc": {"fill": "", "outline": "black", "width": 1.0, "dash": "", "start": 0.0,
            "extent": 90.0, "style": "pieslice", "state": "", "stipple": ""},
    "text": {"text": "", "font": "TkDefaultFont", "fill": "black", "anchor": "center",
             "justify": "left", "width": 0, "angle": 0.0, "state": "", "underline": -1},
    "image": {"image": "", "anchor": "center", "state": ""},
    "window": {"window": "", "anchor": "center", "width": 0, "height": 0, "state": ""},
}


def _glatt(pts, geschlossen, schritte=12):
    """Tk's smooth=True: parabolic spline through the midpoints."""
    p = [(pts[i], pts[i + 1]) for i in range(0, len(pts) - 1, 2)]
    if len(p) < 3:
        return pts
    if geschlossen:
        if p[0] == p[-1]:
            p = p[:-1]
        n = len(p)
        segs = [((p[i - 1][0] + p[i][0]) / 2, (p[i - 1][1] + p[i][1]) / 2) for i in range(n)]
        erg = []
        for i in range(n):
            a = segs[i]
            c = p[i]
            b = segs[(i + 1) % n]
            for k in range(schritte):
                t = k / schritte
                erg += [(1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0],
                        (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]]
        return erg
    erg = [p[0][0], p[0][1]]
    n = len(p)
    for i in range(1, n - 1):
        a = p[0] if i == 1 else ((p[i - 1][0] + p[i][0]) / 2, (p[i - 1][1] + p[i][1]) / 2)
        c = p[i]
        b = p[n - 1] if i == n - 2 else ((p[i][0] + p[i + 1][0]) / 2, (p[i][1] + p[i + 1][1]) / 2)
        for k in range(1, schritte + 1):
            t = k / schritte
            erg += [(1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0],
                    (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]]
    return erg


def _dash_muster(dash, breite):
    """Tk dash option -> list of on/off lengths in pixels (".", "-", "_", "," as in Tk or a
    sequence of numbers); None for a solid line.
    """
    if not dash:
        return None
    if isinstance(dash, str):
        zeichen = {".": (2, 4), "-": (6, 4), "_": (8, 4), ",": (4, 4), " ": None}
        m = []
        for ch in dash:
            z = zeichen.get(ch)
            if z:
                m += list(z)
        return m or None
    m = [max(1.0, float(x)) for x in dash]
    if len(m) % 2:
        m = m * 2
    return m


def _striche(pts, muster, versatz=0.0):
    """Polyline -> list of dash segments [[x0, y0, x1, y1, ...], ...]."""
    erg = []
    i_m = 0
    rest = muster[0]
    an = True
    aktuell = [pts[0], pts[1]]
    for i in range(0, len(pts) - 3, 2):
        x0, y0, x1, y1 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
        dl = math.hypot(x1 - x0, y1 - y0)
        pos = 0.0
        while dl - pos > rest:
            pos += rest
            t = pos / dl
            px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if an:
                aktuell += [px, py]
                erg.append(aktuell)
            aktuell = [px, py]
            an = not an
            i_m = (i_m + 1) % len(muster)
            rest = muster[i_m]
        rest -= dl - pos
        if an:
            aktuell += [x1, y1]
        else:
            aktuell = [x1, y1]
    if an and len(aktuell) >= 4:
        erg.append(aktuell)
    return erg


def _dicke_striche(g, segs, w):
    """Thick dashes as one mesh of quads (Kivy's Line has no dashes above width 1)."""
    verts, idx = [], []
    h = w / 2.0
    n = 0
    for s in segs:
        for i in range(0, len(s) - 3, 2):
            x0, y0, x1, y1 = s[i], s[i + 1], s[i + 2], s[i + 3]
            dx, dy = x1 - x0, y1 - y0
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln * h, dx / ln * h
            verts += [x0 + nx, y0 + ny, 0, 0, x1 + nx, y1 + ny, 0, 0,
                      x1 - nx, y1 - ny, 0, 0, x0 - nx, y0 - ny, 0, 0]
            idx += [n, n + 1, n + 2, n, n + 2, n + 3]
            n += 4
            if n > 60000:
                g.add(Mesh(vertices=verts, indices=idx, mode="triangles"))
                verts, idx, n = [], [], 0
    if idx:
        g.add(Mesh(vertices=verts, indices=idx, mode="triangles"))


_CAP = {"butt": "none", "projecting": "square", "round": "round"}
_JOIN = {"round": "round", "bevel": "bevel", "miter": "miter"}


def _linie(g, pts, farbe, breite, dash=None, cap="butt", join="round", zu=False):
    """Draws a polyline item on its own (not merged into a block mesh): dashed (thick dashes as
    own triangles, _dicke_striche) or solid with Kivy's Line, caps and joins mapped to
    Kivy's; closed if `zu`.
    """
    if len(pts) < 4:
        return
    g.add(Color(*farbe))
    muster = _dash_muster(dash, breite) if dash else None
    if muster:
        if zu:
            pts = list(pts) + [pts[0], pts[1]]
        segs = _striche(pts, muster)
        if breite <= 1.5:
            for s in segs:
                g.add(Line(points=s, width=1))
        else:
            _dicke_striche(g, segs, breite)
        return
    if breite <= 1.5:
        g.add(Line(points=pts, width=1, close=zu))
    else:
        g.add(Line(points=pts, width=breite / 2.0, cap=_CAP.get(cap, "none"),
                   joint=_JOIN.get(join, "round"), close=zu))


def _fuellen(g, pts, farbe, konvex=False):
    """Fills a polygon: convex shapes as triangle fan, others through Kivy's tesselator (odd
    winding rule like Tk).
    """
    n = len(pts) // 2
    if n < 3:
        return
    g.add(Color(*farbe))
    if konvex:
        verts = []
        for i in range(n):
            verts += [pts[2 * i], pts[2 * i + 1], 0, 0]
        g.add(Mesh(vertices=verts, indices=list(range(n)), mode="triangle_fan"))
        return
    tess = Tesselator()
    tess.add_contour(pts)
    if not tess.tesselate(WINDING_ODD, TYPE_POLYGONS):
        return
    for verts, idx in tess.meshes:
        g.add(Mesh(vertices=verts, indices=idx, mode="triangle_fan"))


def _ellipse_punkte(x0, y0, x1, y1, start=0.0, umfang=360.0, mitte=False):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = abs(x1 - x0) / 2, abs(y1 - y0) / 2
    n = max(8, min(360, int(max(rx, ry) * abs(umfang) / 360 * 0.9) + 8))
    pts = [cx, cy] if mitte else []
    for k in range(n + 1):
        a = math.radians(start + umfang * k / n)
        pts += [cx + rx * math.cos(a), cy - ry * math.sin(a)]
    return pts


def _gespiegelt(tex):
    tc = tex.tex_coords
    return (tc[6], tc[7], tc[4], tc[5], tc[2], tc[3], tc[0], tc[1])


def _konvex(pts):
    """True if the polygon (flat list x0, y0, x1, y1 ...) is convex - then it can be filled as a
    simple triangle fan.
    """
    n = len(pts) // 2
    if n <= 3:
        return True
    vorz = 0
    for i in range(n):
        x0, y0 = pts[2 * i], pts[2 * i + 1]
        x1, y1 = pts[(2 * i + 2) % (2 * n)], pts[(2 * i + 3) % (2 * n)]
        x2, y2 = pts[(2 * i + 4) % (2 * n)], pts[(2 * i + 5) % (2 * n)]
        k = (x1 - x0) * (y2 - y1) - (y1 - y0) * (x2 - x1)
        if k:
            s = 1 if k > 0 else -1
            if vorz and s != vorz:
                return False
            vorz = s
    return True


class Canvas(T.BaseWidget):
    _kt_klasse = "Canvas"
    _kt_standard = {"background": "#ffffff", "borderwidth": 0, "relief": T.FLAT,
                 "highlightthickness": 1, "highlightbackground": "#f0f0f0",
                 "highlightcolor": "#000000", "width": 378, "height": 265, "cursor": "",
                 "scrollregion": "", "xscrollcommand": None, "yscrollcommand": None,
                 "xscrollincrement": 0, "yscrollincrement": 0, "confine": True,
                 "closeenough": 1.0, "takefocus": "", "state": "normal",
                 "selectbackground": "#c3c3c3", "insertbackground": "#000000"}

    def __init__(self, master=None, cnf=None, **kw):
        self._kt_items = {}             # id -> _Item
        self._kt_ordnung = {}           # id -> None, stacking order (first = bottom)
        self._kt_tag_index = {}         # tag -> {id: None}
        self._kt_naechste_id = 1
        self._kt_xorg = 0.0             # canvas coordinate at the window's left edge
        self._kt_yorg = 0.0
        self._kt_maus = None
        self._kt_tag_bindungen = {}
        self._kt_bloecke = []
        self._kt_flush_trigger = Clock.create_trigger(self._kt_flush, -1)
        super().__init__(master, cnf, **kw)
        k = self._kt_k
        self._kt_g_items = InstructionGroup()
        self._kt_trans = Translate(0, 0)
        self._kt_g_vorne = InstructionGroup()
        g = self._kt_g_inhalt
        g.add(PushMatrix())
        g.add(self._kt_trans)
        g.add(Scale(1, -1, 1))
        g.add(self._kt_g_items)
        g.add(PopMatrix())
        k.canvas.after.add(self._kt_g_vorne)

    def _kt_kivy_flaeche(self):
        return T._ClipFlaeche(size_hint=(None, None))

    def _kt_innen(self):
        b = T._int(self._kt_o.get("borderwidth", 0)) + T._int(self._kt_o.get("highlightthickness", 0))
        return b, b, b, b

    def _kt_natuerlich(self):
        b = self._kt_innen()[0]
        return T._mass(self._kt_o.get("width", 378)) + 2 * b, T._mass(self._kt_o.get("height", 265)) + 2 * b

    def _kt_option_geaendert(self, kw):
        if "scrollregion" in kw:
            self._kt_scroll_melden()

    def _kt_nimmt_fokus(self):
        tf = self._kt_o.get("takefocus")
        return bool(tf) and tf not in ("0", 0)

    # ---------------------------------------------------- drawing
    def _kt_darstellen(self):
        """Shows the canvas for this frame: moves the Kivy widget to its place, sets the
        transform that turns Tk canvas coordinates (y downwards, scroll origin) into window
        coordinates - shifted by half a pixel so 1-pixel lines hit pixel centres - builds the
        changed blocks (_kt_flush) and redraws background and border when needed.
        """
        if not self._kt_sichtbar or self._kt_zerstoert:
            return
        kx, ky = self._kt_kivy_pos()
        k = self._kt_k
        if (k.x, k.y) != (kx, ky) or tuple(k.size) != (self._kt_w, self._kt_h):
            k.pos = (kx, ky)
            k.size = (self._kt_w, self._kt_h)
            self._kt_zeichnen_noetig = True
        self._kt_trans.xy = (kx - self._kt_xorg + 0.5, ky + self._kt_h + self._kt_yorg - 0.5)
        self._kt_flush()
        if self._kt_zeichnen_noetig:
            self._kt_zeichnen_noetig = False
            self._kt_g_hinten.clear()
            self._kt_g_vorne.clear()
            bg = self._kt_farbe_opt("background")
            if bg is not None:
                self._kt_g_hinten.add(Color(*bg))
                self._kt_g_hinten.add(Rectangle(pos=(kx, ky), size=(self._kt_w, self._kt_h)))
            ht = T._int(self._kt_o.get("highlightthickness", 0))
            if ht:
                hf = self._kt_farbe_opt("highlightcolor" if "focus" in self._kt_zustand
                                     else "highlightbackground") or bg
                if hf is not None:
                    T._rahmen(self._kt_g_vorne, kx, ky, self._kt_w, self._kt_h, ht, hf)
            bd = T._int(self._kt_o.get("borderwidth", 0))
            if bd and self._kt_o.get("relief", "flat") != "flat":
                T._relief(self._kt_g_vorne, kx + ht, ky + ht, self._kt_w - 2 * ht, self._kt_h - 2 * ht, bd,
                          self._kt_o.get("relief"), bg or (0.5, 0.5, 0.5, 1))

    def _kt_fokus_aenderung(self):
        if T._int(self._kt_o.get("highlightthickness", 0)):
            self._kt_neu_zeichnen()

    # ---------------------------------------------------- blocks
    def _kt_dirty(self, b):
        if b is not None and not b.dirty:
            b.dirty = True
        self._kt_flush_trigger()

    def _kt_flush(self, *_a):
        bauen = self._kt_bauen
        for b in self._kt_bloecke:
            if b.dirty:
                b.dirty = False
                for it in b.items.values():
                    if it.neu:
                        bauen(it)
                _block_bauen(b)

    def _kt_einreihen(self, it):
        b = self._kt_bloecke[-1] if self._kt_bloecke else None
        if b is None or len(b.items) >= _BLOCK:
            b = _Block()
            self._kt_bloecke.append(b)
            self._kt_g_items.add(b.g)
        b.items[it.id] = it
        it.blk = b
        self._kt_dirty(b)

    def _kt_aendern(self, it):
        it.neu = True
        it.bbox = None
        self._kt_dirty(it.blk)

    def _kt_bauen(self, it):
        """Builds the Kivy instructions of one item from its type, coordinates and options.
        Simple lines, rectangles and filled ovals only get a run key (`lk`) and points
        (`lp`): they are drawn together with their neighbours in a shared mesh of the block.
        Everything else draws into the item's own InstructionGroup. Also computes the
        bounding box.
        """
        it.neu = False
        g = it.g
        g.clear()
        it.bbox = None
        it.lk = it.lp = None
        o = it.o
        if o.get("state") == "hidden":
            return
        typ = it.typ
        xy = it.xy
        if typ == "line":
            f = _stipple(_farbe(o.get("fill")), o.get("stipple"))
            if f is None or len(xy) < 4:
                return
            pts = _glatt(xy, False, int(o.get("splinesteps", 12))) if _wahr(o.get("smooth")) else xy
            w = float(o.get("width", 1) or 1)
            if not o.get("dash") and len(pts) >= 4:
                # drawn in the block's shared mesh: (colour, width, round caps)
                it.lk = (f, w if w > 1.5 else 1.0, o.get("capstyle", "butt") == "round")
                it.lp = list(pts)
                return
            _linie(g, pts, f, float(o.get("width", 1) or 1), o.get("dash"), o.get("capstyle", "butt"),
                   o.get("joinstyle", "round"))
        elif typ == "rectangle":
            if len(xy) < 4:
                return
            x0, y0, x1, y1 = min(xy[0], xy[2]), min(xy[1], xy[3]), max(xy[0], xy[2]), max(xy[1], xy[3])
            f = _stipple(_farbe(o.get("fill")), o.get("stipple"))
            ol = _farbe(o.get("outline"))
            if f is not None and not o.get("dash"):
                w = float(o.get("width", 1) or 0)
                if ol is None or w <= 0:
                    it.lk, it.lp = (f, -2.0, False), (x0, y0, x1, y1)
                    return
                if ol == f and w <= 1.5:              # outline in the fill colour: one px larger
                    it.lk, it.lp = (f, -2.0, False), (x0, y0, x1 + 1, y1 + 1)
                    return
            if f is not None:
                g.add(Color(*f))
                g.add(Rectangle(pos=(x0, y0), size=(x1 - x0, y1 - y0)))
            w = float(o.get("width", 1) or 0)
            if ol is not None and w > 0:
                if o.get("dash"):
                    _linie(g, [x0, y0, x1, y0, x1, y1, x0, y1], ol, w, o.get("dash"), zu=True)
                elif w <= 1.5:
                    g.add(Color(*ol))
                    g.add(Line(rectangle=(x0, y0, max(0, x1 - x0 - 1), max(0, y1 - y0 - 1)), width=1))
                else:
                    g.add(Color(*ol))
                    h = w / 2
                    g.add(Line(rectangle=(x0 + h - 0.5, y0 + h - 0.5, max(0, x1 - x0 - w), max(0, y1 - y0 - w)),
                               width=w / 2, joint="miter"))
        elif typ == "oval":
            if len(xy) < 4:
                return
            x0, y0, x1, y1 = min(xy[0], xy[2]), min(xy[1], xy[3]), max(xy[0], xy[2]), max(xy[1], xy[3])
            f = _stipple(_farbe(o.get("fill")), o.get("stipple"))
            ol = _farbe(o.get("outline"))
            w = float(o.get("width", 1) or 0)
            if f is not None and (ol is None or w <= 0 or (ol == f and w <= 1.5)) and not o.get("dash"):
                it.lk = (f, -1.0, False)              # filled oval: shared mesh of the block
                it.lp = (x0, y0, x1, y1) if ol is None or w <= 0 else (x0 - 0.5, y0 - 0.5, x1 + 0.5, y1 + 0.5)
                return
            if f is not None and ol is not None and 0 < w <= 1.5 and not o.get("dash"):
                it.lk = ((ol, f), -3.0, False)        # filled oval with outline (grid dots)
                it.lp = (x0, y0, x1, y1)
                return
            if f is not None:
                g.add(Color(*f))
                seg = max(12, min(180, int((x1 - x0 + y1 - y0) / 2)))
                g.add(Ellipse(pos=(x0, y0), size=(x1 - x0, y1 - y0), segments=seg))
            if ol is not None and w > 0:
                if o.get("dash"):
                    _linie(g, _ellipse_punkte(x0, y0, x1, y1), ol, w, o.get("dash"))
                else:
                    g.add(Color(*ol))
                    seg = max(12, min(180, int((x1 - x0 + y1 - y0) / 2)))
                    g.add(Line(ellipse=(x0, y0, x1 - x0, y1 - y0, 0, 360, seg),
                               width=1 if w <= 1.5 else w / 2))
        elif typ == "polygon":
            if len(xy) < 4:
                return
            glatt = _wahr(o.get("smooth"))
            pts = _glatt(xy, True, int(o.get("splinesteps", 12))) if glatt else list(xy)
            if len(pts) >= 4 and pts[0] == pts[-2] and pts[1] == pts[-1]:
                pts = pts[:-2]
            f = _stipple(_farbe(o.get("fill")), o.get("stipple"))
            if f is not None:
                _fuellen(g, pts, f, _konvex(pts))
            ol = _farbe(o.get("outline"))
            w = float(o.get("width", 1) or 0)
            if ol is not None and w > 0:
                _linie(g, pts, ol, w, o.get("dash"), join=o.get("joinstyle", "round"), zu=True)
        elif typ == "arc":
            if len(xy) < 4:
                return
            x0, y0, x1, y1 = min(xy[0], xy[2]), min(xy[1], xy[3]), max(xy[0], xy[2]), max(xy[1], xy[3])
            st = float(o.get("start", 0))
            ex = float(o.get("extent", 90))
            stil = o.get("style", "pieslice")
            f = _stipple(_farbe(o.get("fill")), o.get("stipple"))
            if f is not None and stil != "arc":
                pts = _ellipse_punkte(x0, y0, x1, y1, st, ex, mitte=(stil == "pieslice"))
                _fuellen(g, pts, f, konvex=(stil == "pieslice" and abs(ex) <= 180) or stil == "chord")
            ol = _farbe(o.get("outline"))
            w = float(o.get("width", 1) or 0)
            if ol is not None and w > 0:
                bogen = _ellipse_punkte(x0, y0, x1, y1, st, ex)
                if stil == "pieslice":
                    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                    _linie(g, [cx, cy] + bogen, ol, w, o.get("dash"), zu=True)
                elif stil == "chord":
                    _linie(g, bogen, ol, w, o.get("dash"), zu=True)
                else:
                    _linie(g, bogen, ol, w, o.get("dash"))
        elif typ == "text":
            self._kt_text_bauen(it)
        elif typ == "image":
            bild = o.get("image")
            if isinstance(bild, str):
                bild = T._BILDER.get(bild)
            if not bild or len(xy) < 2:
                return
            tex = bild._kt_textur()
            bw, bh = bild.width(), bild.height()
            x, y = _verankern(o.get("anchor", "center"), xy[0], xy[1], bw, bh)
            g.add(Color(1, 1, 1, 1))
            g.add(Rectangle(texture=tex, pos=(round(x) - 0.5, round(y) - 0.5), size=(bw, bh),
                            tex_coords=_gespiegelt(tex)))
            it.bbox = (x, y, x + bw, y + bh)

    def _kt_text_bauen(self, it):
        """Builds a text item: wraps it at `width`, measures it, places it by anchor and justify
        (also rotated by `angle`) and draws it with fontmod.text_zeichnen (GDI / ClearType on
        Windows).
        """
        o, g, xy = it.o, it.g, it.xy
        text = str(o.get("text", ""))
        if not text or len(xy) < 2:
            it.bbox = (xy[0], xy[1], xy[0], xy[1]) if len(xy) >= 2 else None
            return
        f = _farbe(o.get("fill"))
        font = o.get("font") or "TkDefaultFont"
        breite = T._mass(o.get("width", 0) or 0)
        zeilen = fontmod.umbrechen(text, font, breite) if breite > 0 else text.split("\n")
        lh = fontmod.zeilen_hoehe(font)
        bs = [fontmod.text_breite(z, font) for z in zeilen]
        tw, th = max(bs or [0]), lh * len(zeilen)
        winkel = float(o.get("angle", 0) or 0)
        x, y = xy[0], xy[1]
        lx, ly = _verankern(o.get("anchor", "center"), 0, 0, tw, th)
        just = o.get("justify", "left")
        if winkel:
            g.add(PushMatrix())
            g.add(Translate(x, y))
            g.add(Rotate(angle=-winkel, axis=(0, 0, 1)))
            ox, oy = 0, 0
        else:
            ox, oy = x, y
        if f is not None:
            for i, z in enumerate(zeilen):
                tex = fontmod.text_textur(z, font)
                if tex is None:
                    continue
                if just == "center":
                    zx = lx + (tw - bs[i]) / 2
                elif just == "right":
                    zx = lx + tw - bs[i]
                else:
                    zx = lx
                # -0.5: cancels the half pixel of the canvas transform (meant for 1 px
                # lines), so the text lands exactly on the pixel grid and stays sharp
                fontmod.text_zeichnen(g, tex, f, (round(ox + zx) - 0.5, round(oy + ly + i * lh) - 0.5),
                                      tex.size, _gespiegelt(tex))
        if winkel:
            g.add(PopMatrix())
            # bounding box of the rotated text
            a = math.radians(winkel)
            ca, sa = math.cos(a), math.sin(a)
            ecken = [(lx, ly), (lx + tw, ly), (lx + tw, ly + th), (lx, ly + th)]
            xs = [x + px * ca + py * sa for px, py in ecken]
            ys = [y - px * sa + py * ca for px, py in ecken]
            it.bbox = (min(xs), min(ys), max(xs), max(ys))
        else:
            it.bbox = (x + lx, y + ly, x + lx + tw, y + ly + th)

    # ---------------------------------------------------- item creation
    def _kt_neu(self, typ, args, kw):
        """Shared code of all create_* methods: reads coordinates, tags and options, gives the
        item the next id, puts it on top of the stacking order and into the last block.
        Nothing is drawn yet - that happens at the next frame.
        """
        if args and isinstance(args[-1], dict):
            kw = {**args[-1], **kw}
            args = args[:-1]
        xy = _flach(args)
        tags = kw.pop("tags", None)
        if tags is None:
            tags = kw.pop("tag", None)
        o = dict(_STANDARD[typ])
        o.update(kw)
        ident = self._kt_naechste_id
        self._kt_naechste_id += 1
        tl = _tags(tags)
        it = _Item(ident, typ, xy, o, tl)
        self._kt_items[ident] = it
        self._kt_ordnung[ident] = None
        for t in tl:
            self._kt_tag_index.setdefault(t, {})[ident] = None
        if typ == "window":
            self._kt_fenster_setzen(it)
        else:
            self._kt_einreihen(it)          # built later, once per frame (see _kt_flush)
        return ident

    def create_line(self, *args, **kw):
        return self._kt_neu("line", args, kw)

    def create_rectangle(self, *args, **kw):
        return self._kt_neu("rectangle", args, kw)

    def create_oval(self, *args, **kw):
        return self._kt_neu("oval", args, kw)

    def create_polygon(self, *args, **kw):
        return self._kt_neu("polygon", args, kw)

    def create_arc(self, *args, **kw):
        return self._kt_neu("arc", args, kw)

    def create_text(self, *args, **kw):
        return self._kt_neu("text", args, kw)

    def create_image(self, *args, **kw):
        return self._kt_neu("image", args, kw)

    def create_window(self, *args, **kw):
        return self._kt_neu("window", args, kw)

    def create_bitmap(self, *args, **kw):
        kw.pop("bitmap", None)
        return self._kt_neu("image", args, kw)

    # ---------------------------------------------------- embedded windows
    def _kt_fenster_setzen(self, it):
        w = it.o.get("window")
        if isinstance(w, str) and w:
            w = self.nametowidget(w)
            it.o["window"] = w
        if w:
            w._kt_manager = "canvas"
            w._kt_geo_master = self
            w._kt_lebt = True
            self._kt_layout_planen()

    def _kt_anordnen(self):
        """Lays out the canvas and the widgets embedded with create_window (they are placed at
        their item's position and anchor and hidden with state=hidden).
        """
        T.Misc._kt_anordnen(self)
        for i in self._kt_ordnung:
            it = self._kt_items[i]
            if it.typ != "window":
                continue
            w = it.o.get("window")
            if not w or w._kt_zerstoert:
                continue
            rw, rh = w._kt_req()
            bw = int(T._mass(it.o.get("width") or 0)) or rw
            bh = int(T._mass(it.o.get("height") or 0)) or rh
            x, y = _verankern(it.o.get("anchor", "center"), it.xy[0], it.xy[1], bw, bh)
            it.bbox = (x, y, x + bw, y + bh)
            sichtbar = it.o.get("state") != "hidden"
            w._kt_setzen(int(round(x - self._kt_xorg)), int(round(y - self._kt_yorg)), bw, bh, sichtbar=sichtbar)
            if sichtbar:
                w._kt_anordnen()

    # ---------------------------------------------------- item lookup
    def _kt_ids(self, tag_or_id):
        """-> list of item ids (stacking order) for an id or tag."""
        if tag_or_id is None:
            return []
        if isinstance(tag_or_id, int):
            return [tag_or_id] if tag_or_id in self._kt_items else []
        s = str(tag_or_id)
        if s.isdigit():
            i = int(s)
            return [i] if i in self._kt_items else []
        if s == "all":
            return list(self._kt_ordnung)
        if s == "current":
            c = self._kt_aktuell()
            return [c] if c is not None else []
        if any(ch in s for ch in "&|^!") and s not in self._kt_tag_index:
            return [i for i in self._kt_ordnung if _tag_ausdruck(s, self._kt_items[i].tags)]
        d = self._kt_tag_index.get(s)
        if not d:
            return []
        if len(d) == 1:
            return list(d)
        if len(d) * 4 < len(self._kt_ordnung):
            pos = {}
            for n, i in enumerate(self._kt_ordnung):
                if i in d:
                    pos[i] = n
            return sorted(d, key=pos.__getitem__)
        return [i for i in self._kt_ordnung if i in d]

    def _kt_erstes(self, tag_or_id):
        if isinstance(tag_or_id, int):
            return self._kt_items.get(tag_or_id)
        ids = self._kt_ids(tag_or_id)
        return self._kt_items[ids[0]] if ids else None

    def find_all(self):
        return tuple(self._kt_ordnung)

    def find_withtag(self, tagOrId):
        return tuple(self._kt_ids(tagOrId))

    def find_overlapping(self, x1, y1, x2, y2):
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        erg = []
        for i in self._kt_ordnung:
            b = self._kt_item_bbox(self._kt_items[i])
            if b and b[0] <= x2 and b[2] >= x1 and b[1] <= y2 and b[3] >= y1:
                erg.append(i)
        return tuple(erg)

    def find_enclosed(self, x1, y1, x2, y2):
        erg = []
        for i in self._kt_ordnung:
            b = self._kt_item_bbox(self._kt_items[i])
            if b and b[0] >= x1 and b[2] <= x2 and b[1] >= y1 and b[3] <= y2:
                erg.append(i)
        return tuple(erg)

    def find_closest(self, x, y, halo=None, start=None):
        bester, d_best = None, None
        for i in self._kt_ordnung:
            b = self._kt_item_bbox(self._kt_items[i])
            if not b:
                continue
            dx = max(b[0] - x, 0, x - b[2])
            dy = max(b[1] - y, 0, y - b[3])
            d = math.hypot(dx, dy)
            if d_best is None or d <= d_best:
                bester, d_best = i, d
        return (bester,) if bester is not None else ()

    def find_above(self, tagOrId):
        ids = self._kt_ids(tagOrId)
        if not ids:
            return ()
        o = list(self._kt_ordnung)
        n = o.index(ids[-1])
        return (o[n + 1],) if n + 1 < len(o) else ()

    def find_below(self, tagOrId):
        ids = self._kt_ids(tagOrId)
        if not ids:
            return ()
        o = list(self._kt_ordnung)
        n = o.index(ids[0])
        return (o[n - 1],) if n > 0 else ()

    def _kt_aktuell(self):
        if self._kt_maus is None:
            return None
        x, y = self._kt_maus
        for i in reversed(list(self._kt_ordnung)):
            b = self._kt_item_bbox(self._kt_items[i])
            if b and b[0] - 1 <= x <= b[2] + 1 and b[1] - 1 <= y <= b[3] + 1:
                return i
        return None

    def _kt_item_bbox(self, it):
        """Bounding box of an item in canvas coordinates (with half the line width), as bbox()
        and find_overlapping() need it. Texts and images are built first, their size is only
        known then.
        """
        if it.neu and it.typ in ("text", "image"):
            self._kt_bauen(it)                  # their size is only known once built
        if it.bbox is not None:
            return it.bbox
        xy = it.xy
        if not xy or it.o.get("state") == "hidden":
            return None
        if it.typ in ("text", "image", "window"):
            return it.bbox
        xs, ys = xy[0::2], xy[1::2]
        w = float(it.o.get("width", 1) or 1) / 2 if it.typ in ("line", "polygon") else \
            float(it.o.get("width", 1) or 1) / 2
        it.bbox = (min(xs) - w, min(ys) - w, max(xs) + w, max(ys) + w)
        return it.bbox

    def bbox(self, *args):
        boxen = []
        for a in (args or ("all",)):
            for i in self._kt_ids(a):
                b = self._kt_item_bbox(self._kt_items[i])
                if b:
                    boxen.append(b)
        if not boxen:
            return None
        return (int(math.floor(min(b[0] for b in boxen))), int(math.floor(min(b[1] for b in boxen))),
                int(math.ceil(max(b[2] for b in boxen))), int(math.ceil(max(b[3] for b in boxen))))

    def type(self, tagOrId):
        it = self._kt_erstes(tagOrId)
        return it.typ if it else None

    def gettags(self, tagOrId):
        it = self._kt_erstes(tagOrId)
        return tuple(it.tags) if it else ()

    # ---------------------------------------------------- item changes
    def delete(self, *args):
        """delete(tagOrId ...): removes the items, their tags and embedded windows. Blocks that
        became empty are dropped, the others are rebuilt at the next frame.
        """
        weg = []
        for a in args:
            weg.extend(self._kt_ids(a))
        if not weg:
            return
        weg = set(weg)
        bloecke = set()
        for i in weg:
            it = self._kt_items.pop(i, None)
            if it is None:
                continue
            if it.blk is not None:
                it.blk.items.pop(i, None)
                bloecke.add(it.blk)
                it.blk = None
            self._kt_ordnung.pop(i, None)
            for t in it.tags:
                d = self._kt_tag_index.get(t)
                if d is not None:
                    d.pop(i, None)
                    if not d:
                        del self._kt_tag_index[t]
            if it.typ == "window":
                w = it.o.get("window")
                if w and not w._kt_zerstoert:
                    w._kt_manager = None
                    w._kt_setzen(0, 0, 0, 0, sichtbar=False)
                    w._kt_lebt = False
        leer = [b for b in bloecke if not b.items]
        if len(leer) == len(self._kt_bloecke):
            self._kt_g_items.clear()
            for b in leer:
                b.g.clear()
            self._kt_bloecke = []
        else:
            for b in leer:
                self._kt_bloecke.remove(b)
                b.g.clear()
                self._kt_g_items.remove(b.g)
        for b in bloecke:
            if b.items:
                self._kt_dirty(b)

    def _kt_neu_ordnen(self):
        """New stacking order: distribute all items over new blocks."""
        g = self._kt_g_items
        g.clear()
        for b in self._kt_bloecke:
            b.g.clear()
        self._kt_bloecke = []
        items = self._kt_items
        b = None
        for i in self._kt_ordnung:
            it = items[i]
            if it.typ == "window":
                continue
            if b is None or len(b.items) >= _BLOCK:
                b = _Block()
                self._kt_bloecke.append(b)
                g.add(b.g)
            b.items[i] = it
            it.blk = b
        self._kt_flush_trigger()

    def coords(self, tagOrId, *args):
        """coords(tagOrId): the coordinates of the first matching item; with arguments it moves
        that item (rebuilt at the next frame).
        """
        it = self._kt_erstes(tagOrId)
        if it is None:
            return []
        if not args:
            return list(it.xy)
        it.xy = _flach(args)
        it.bbox = None
        if it.typ == "window":
            self._kt_layout_planen()
        else:
            self._kt_aendern(it)
        return None

    def itemconfigure(self, tagOrId, cnf=None, **kw):
        """itemconfigure(tagOrId, **options): without options returns the options of the first
        item (in Tk's tuple form); otherwise changes them for all matching items, including a
        new tag list.
        """
        if cnf:
            kw = {**cnf, **kw}
        ids = self._kt_ids(tagOrId)
        if not kw:
            it = self._kt_items[ids[0]] if ids else None
            return {k: (k, "", "", "", v) for k, v in it.o.items()} if it else {}
        neu_tags = kw.pop("tags", None)
        for i in ids:
            it = self._kt_items[i]
            if neu_tags is not None:
                for t in it.tags:
                    d = self._kt_tag_index.get(t)
                    if d:
                        d.pop(i, None)
                it.tags = _tags(neu_tags)
                for t in it.tags:
                    self._kt_tag_index.setdefault(t, {})[i] = None
            geaendert = False
            for k, v in kw.items():
                if it.o.get(k) != v:
                    it.o[k] = v
                    geaendert = True
            if geaendert:
                if it.typ == "window":
                    self._kt_fenster_setzen(it)
                    self._kt_layout_planen()
                else:
                    self._kt_aendern(it)

    itemconfig = itemconfigure

    def itemcget(self, tagOrId, option):
        it = self._kt_erstes(tagOrId)
        if it is None:
            return ""
        v = it.o.get(option, "")
        return "" if v is None else v

    def move(self, tagOrId, dx, dy):
        dx, dy = float(dx), float(dy)
        for i in self._kt_ids(tagOrId):
            it = self._kt_items[i]
            xy = it.xy
            it.xy = [v + (dx if n % 2 == 0 else dy) for n, v in enumerate(xy)]
            it.bbox = None
            if it.typ == "window":
                self._kt_layout_planen()
            else:
                self._kt_aendern(it)

    def moveto(self, tagOrId, x="", y=""):
        b = self.bbox(tagOrId)
        if not b:
            return
        dx = float(x) - b[0] if x != "" else 0
        dy = float(y) - b[1] if y != "" else 0
        self.move(tagOrId, dx, dy)

    def scale(self, tagOrId, xOrigin, yOrigin, xScale, yScale):
        xo, yo, sx, sy = float(xOrigin), float(yOrigin), float(xScale), float(yScale)
        for i in self._kt_ids(tagOrId):
            it = self._kt_items[i]
            it.xy = [(xo + (v - xo) * sx) if n % 2 == 0 else (yo + (v - yo) * sy)
                     for n, v in enumerate(it.xy)]
            it.bbox = None
            self._kt_aendern(it)

    def addtag_withtag(self, newtag, tagOrId):
        for i in self._kt_ids(tagOrId):
            it = self._kt_items[i]
            if newtag not in it.tags:
                it.tags.append(newtag)
                self._kt_tag_index.setdefault(newtag, {})[i] = None

    def addtag_all(self, newtag):
        self.addtag_withtag(newtag, "all")

    def addtag(self, newtag, how, *args):
        """addtag(newtag, how, ...): Tk's general form for withtag, all, overlapping, enclosed
        and closest.
        """
        if how == "withtag":
            self.addtag_withtag(newtag, args[0])
        elif how == "all":
            self.addtag_all(newtag)
        elif how == "overlapping":
            for i in self.find_overlapping(*args):
                self.addtag_withtag(newtag, i)
        elif how == "enclosed":
            for i in self.find_enclosed(*args):
                self.addtag_withtag(newtag, i)
        elif how == "closest":
            for i in self.find_closest(*args[:2]):
                self.addtag_withtag(newtag, i)

    def addtag_overlapping(self, newtag, x1, y1, x2, y2):
        self.addtag(newtag, "overlapping", x1, y1, x2, y2)

    def addtag_enclosed(self, newtag, x1, y1, x2, y2):
        self.addtag(newtag, "enclosed", x1, y1, x2, y2)

    def dtag(self, tagOrId, tagToDelete=None):
        weg = tagToDelete if tagToDelete is not None else tagOrId
        for i in self._kt_ids(tagOrId):
            it = self._kt_items[i]
            if weg in it.tags:
                it.tags.remove(weg)
                d = self._kt_tag_index.get(weg)
                if d:
                    d.pop(i, None)

    # ---------------------------------------------------- stacking
    def tag_raise(self, tagOrId, aboveThis=None):
        """tag_raise(tagOrId, aboveThis): moves the items to the top of the stacking order (or
        just above `aboveThis`), keeping their relative order.
        """
        ids = self._kt_ids(tagOrId)
        if not ids:
            return
        if aboveThis is None:
            alle = list(self._kt_ordnung)
            if alle[-len(ids):] == ids:
                return                     # already on top
            menge = set(ids)
            rest = [i for i in alle if i not in menge]
            self._kt_ordnung = dict.fromkeys(rest + ids)
        else:
            ziel = self._kt_ids(aboveThis)
            if not ziel:
                return
            menge = set(ids)
            rest = [i for i in self._kt_ordnung if i not in menge]
            n = rest.index(ziel[-1]) + 1 if ziel[-1] in rest else len(rest)
            self._kt_ordnung = dict.fromkeys(rest[:n] + ids + rest[n:])
        self._kt_neu_ordnen()

    def tag_lower(self, tagOrId, belowThis=None):
        """tag_lower(tagOrId, belowThis): moves the items to the bottom of the stacking order
        (or just below `belowThis`).
        """
        ids = self._kt_ids(tagOrId)
        if not ids:
            return
        if belowThis is None:
            alle = list(self._kt_ordnung)
            if alle[:len(ids)] == ids:
                return                     # already at the bottom
            menge = set(ids)
            rest = [i for i in alle if i not in menge]
            self._kt_ordnung = dict.fromkeys(ids + rest)
        else:
            ziel = self._kt_ids(belowThis)
            if not ziel:
                return
            menge = set(ids)
            rest = [i for i in self._kt_ordnung if i not in menge]
            n = rest.index(ziel[0]) if ziel[0] in rest else 0
            self._kt_ordnung = dict.fromkeys(rest[:n] + ids + rest[n:])
        self._kt_neu_ordnen()

    lift = tkraise = tag_raise
    lower = tag_lower

    # ---------------------------------------------------- tag bindings
    def tag_bind(self, tagOrId, sequence=None, func=None, add=None):
        tab = self._kt_tag_bindungen.setdefault(str(tagOrId), {})
        return T.Misc._kt_binden(tab, sequence, func, add)

    def tag_unbind(self, tagOrId, sequence, funcid=None):
        self._kt_tag_bindungen.get(str(tagOrId), {}).pop(sequence, None)

    def _kt_tag_ereignis(self, ev):
        """Calls tag bindings of the item under the pointer (from the class binding)."""
        if not self._kt_tag_bindungen:
            return
        c = self._kt_aktuell()
        if c is None:
            return
        it = self._kt_items[c]
        from katiecad.ui.kt import events as EV
        for tag in [str(c)] + list(it.tags):
            tab = self._kt_tag_bindungen.get(tag)
            if not tab:
                continue
            for seq, funcs in tab.items():
                m = EV.parse(seq)
                if m is not None and EV.passt(m, ev):
                    for f in list(funcs):
                        f(ev)

    # ---------------------------------------------------- scrolling
    def canvasx(self, screenx, gridspacing=None):
        v = float(screenx) + self._kt_xorg
        if gridspacing:
            v = round(v / gridspacing) * gridspacing
        return v

    def canvasy(self, screeny, gridspacing=None):
        v = float(screeny) + self._kt_yorg
        if gridspacing:
            v = round(v / gridspacing) * gridspacing
        return v

    def _kt_region(self):
        sr = self._kt_o.get("scrollregion")
        if not sr:
            return None
        if isinstance(sr, str):
            sr = sr.split()
        try:
            return tuple(float(v) for v in sr[:4])
        except (TypeError, ValueError):
            return None

    def _kt_sicht(self, achse):
        """Visible part along an axis as fractions (first, last) of the scroll region - the
        value xview() / yview() return and scroll bars use.
        """
        r = self._kt_region()
        inset = self._kt_innen()[0]
        if achse == "x":
            org, groesse = self._kt_xorg + inset, self._kt_w - 2 * inset
            r0, r1 = (r[0], r[2]) if r else (org, org + groesse)
        else:
            org, groesse = self._kt_yorg + inset, self._kt_h - 2 * inset
            r0, r1 = (r[1], r[3]) if r else (org, org + groesse)
        laenge = max(1.0, r1 - r0)
        a = (org - r0) / laenge
        e = (org + groesse - r0) / laenge
        return max(0.0, min(1.0, a)), max(0.0, min(1.0, e))

    def _kt_setze_org(self, achse, wert):
        """Sets the scroll origin of an axis; with confine (default) it is kept inside the
        scroll region like in Tk. Only moves the transform - nothing is rebuilt.
        """
        r = self._kt_region()
        inset = self._kt_innen()[0]
        if r and _wahr(self._kt_o.get("confine", True)):
            if achse == "x":
                groesse = self._kt_w - 2 * inset
                wert = max(r[0] - inset, min(wert, r[2] - groesse - inset))
                wert = max(wert, r[0] - inset) if r[2] - r[0] <= groesse else wert
            else:
                groesse = self._kt_h - 2 * inset
                wert = max(r[1] - inset, min(wert, r[3] - groesse - inset))
                wert = max(wert, r[1] - inset) if r[3] - r[1] <= groesse else wert
        if achse == "x":
            if wert == self._kt_xorg:
                return
            self._kt_xorg = wert
        else:
            if wert == self._kt_yorg:
                return
            self._kt_yorg = wert
        self._kt_scroll_melden()
        self._kt_layout_planen()
        self._kt_neu_zeichnen()

    def _kt_scroll_melden(self):
        for achse, opt in (("x", "xscrollcommand"), ("y", "yscrollcommand")):
            cmd = self._kt_o.get(opt)
            if cmd:
                a, e = self._kt_sicht(achse)
                try:
                    cmd(a, e)
                except Exception:
                    pass

    def _kt_view(self, achse, args):
        """xview / yview: without arguments the visible fractions, otherwise "moveto" a fraction
        or "scroll" n units / pages.
        """
        if not args:
            return self._kt_sicht(achse)
        r = self._kt_region()
        inset = self._kt_innen()[0]
        groesse = (self._kt_w if achse == "x" else self._kt_h) - 2 * inset
        r0, r1 = ((r[0], r[2]) if achse == "x" else (r[1], r[3])) if r else (0, groesse)
        org = self._kt_xorg if achse == "x" else self._kt_yorg
        if args[0] == "moveto":
            self._kt_setze_org(achse, r0 + float(args[1]) * (r1 - r0) - inset)
        elif args[0] == "scroll":
            n, was = int(float(args[1])), args[2]
            if was.startswith("page"):
                schritt = 0.9 * groesse
            else:
                inc = T._mass(self._kt_o.get("xscrollincrement" if achse == "x" else "yscrollincrement") or 0)
                schritt = inc if inc > 0 else groesse / 10
            self._kt_setze_org(achse, org + n * schritt)
        return None

    def xview(self, *args):
        return self._kt_view("x", args)

    def yview(self, *args):
        return self._kt_view("y", args)

    def xview_moveto(self, fraction):
        self._kt_view("x", ("moveto", fraction))

    def yview_moveto(self, fraction):
        self._kt_view("y", ("moveto", fraction))

    def xview_scroll(self, number, what):
        self._kt_view("x", ("scroll", number, what))

    def yview_scroll(self, number, what):
        self._kt_view("y", ("scroll", number, what))

    def _kt_setzen(self, x, y, w, h, sichtbar=True):
        alt = (self._kt_w, self._kt_h)
        super()._kt_setzen(x, y, w, h, sichtbar)
        if (self._kt_w, self._kt_h) != alt:
            self._kt_scroll_melden()

    # ---------------------------------------------------- misc
    def postscript(self, **kw):
        return ""

    def focus(self, *args):
        if not args:
            return self.focus_set()
        return ""

    def icursor(self, *a):
        pass

    def select_clear(self):
        pass


def _verankern(anchor, x, y, w, h):
    a = anchor or "center"
    if a in ("n", "center", "s"):
        x -= w / 2
    elif "e" in a:
        x -= w
    if a in ("w", "center", "e"):
        y -= h / 2
    elif "s" in a:
        y -= h
    return x, y


def _tags(tags):
    if tags is None or tags == "":
        return []
    if isinstance(tags, str):
        return tags.split()
    return [str(t) for t in tags]


def _wahr(v):
    if isinstance(v, str):
        return v.lower() in ("1", "true", "yes", "bezier", "raw")
    return bool(v)


def _tag_ausdruck(expr, tags):
    """Tag expressions like "a&&b", "!a", "a||b" (simplified, no parentheses)."""
    menge = set(tags)
    for oder in expr.split("||"):
        ok = True
        for und in oder.split("&&"):
            und = und.strip()
            if und.startswith("!"):
                if und[1:] in menge:
                    ok = False
            elif und not in menge:
                ok = False
        if ok:
            return True
    return False
