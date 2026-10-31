"""Boolean union / difference of closed 3D meshes (BSP tree, pure Python, no dependencies).

Input are closed meshes (`geom3d.Netz`), output is one mesh of convex polygons with the
outline edges of the merged solid (edges inside coplanar areas and smooth transitions
between facets of round bodies are left out).

Own implementation of the classic BSP approach (Naylor et al.): every solid is a set of
oriented polygons; a polygon is cut by the planes of the other solid and the parts inside
the other solid are removed."""
import bisect
import math

from katiecad.model import geom3d as G

EPS = 1e-5                 # distance to a plane (mm) that still counts as "on the plane"
GLATT_WINKEL = 30.0        # edges between faces bending less than this are not drawn
_FRONT, _BACK, _SPAN = 1, 2, 3


class CSGFehler(ValueError):
    """The bodies cannot be merged (e.g. mesh not closed)."""


# --------------------------------------------------------------------------
# vector helpers
# --------------------------------------------------------------------------
def _sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def _len(a): return math.sqrt(_dot(a, a))


def _normale(pts):
    """Newell normal (unit vector) of a planar polygon or None if degenerate."""
    n = (0.0, 0.0, 0.0)
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        n = (n[0] + (a[1] - b[1]) * (a[2] + b[2]),
             n[1] + (a[2] - b[2]) * (a[0] + b[0]),
             n[2] + (a[0] - b[0]) * (a[1] + b[1]))
    ln = _len(n)
    if ln < 1e-9:
        return None
    return (n[0] / ln, n[1] / ln, n[2] / ln)


# --------------------------------------------------------------------------
# BSP
# --------------------------------------------------------------------------
class _Poly:
    __slots__ = ("v", "n", "w")

    def __init__(self, v, n, w):
        self.v, self.n, self.w = v, n, w

    def flip(self):
        self.v.reverse()
        self.n = (-self.n[0], -self.n[1], -self.n[2])
        self.w = -self.w


def _poly(pts):
    n = _normale(pts)
    if n is None:
        return None
    return _Poly(list(pts), n, _dot(n, pts[0]))


def _teilen(n, w, p, kof, kob, vorn, hinten):
    """Splits polygon p by the plane (n, w) into the lists."""
    typ = 0
    arten = []
    for v in p.v:
        t = _dot(n, v) - w
        a = _BACK if t < -EPS else (_FRONT if t > EPS else 0)
        typ |= a
        arten.append(a)
    if typ == 0:
        (kof if _dot(n, p.n) > 0 else kob).append(p)
    elif typ == _FRONT:
        vorn.append(p)
    elif typ == _BACK:
        hinten.append(p)
    else:
        f, b = [], []
        m = len(p.v)
        for i in range(m):
            j = (i + 1) % m
            ti, tj = arten[i], arten[j]
            vi, vj = p.v[i], p.v[j]
            if ti != _BACK:
                f.append(vi)
            if ti != _FRONT:
                b.append(vi)
            if (ti | tj) == _SPAN:
                t = (w - _dot(n, vi)) / _dot(n, _sub(vj, vi))
                x = (vi[0] + (vj[0] - vi[0]) * t, vi[1] + (vj[1] - vi[1]) * t,
                     vi[2] + (vj[2] - vi[2]) * t)
                f.append(x)
                b.append(x)
        if len(f) >= 3:
            vorn.append(_Poly(f, p.n, p.w))
        if len(b) >= 3:
            hinten.append(_Poly(b, p.n, p.w))


class _Knoten:
    __slots__ = ("n", "w", "vorn", "hinten", "polys")

    def __init__(self, polys=None):
        self.n = None
        self.w = 0.0
        self.vorn = None
        self.hinten = None
        self.polys = []
        if polys:
            self.bauen(polys)

    @staticmethod
    def _ebene_waehlen(polys):
        """Splitting plane with few cuts and balanced sides (sampled)."""
        if len(polys) <= 2:
            return polys[0]
        kand = [polys[int(i * len(polys) / 8)] for i in range(min(8, len(polys)))]
        probe = polys if len(polys) <= 120 else polys[::max(1, len(polys) // 120)]
        best, bw = kand[0], None
        for c in kand:
            nv = nh = ns = 0
            for p in probe:
                if p is c:
                    continue
                typ = 0
                for v in p.v:
                    t = _dot(c.n, v) - c.w
                    typ |= _BACK if t < -EPS else (_FRONT if t > EPS else 0)
                if typ == _SPAN:
                    ns += 1
                elif typ == _FRONT:
                    nv += 1
                elif typ == _BACK:
                    nh += 1
            wert = ns * 3.0 + abs(nv - nh) * 0.3
            if bw is None or wert < bw:
                best, bw = c, wert
        return best

    def bauen(self, polys):
        stack = [(self, list(polys))]
        while stack:
            k, ps = stack.pop()
            if not ps:
                continue
            if k.n is None:
                c = _Knoten._ebene_waehlen(ps)
                k.n, k.w = c.n, c.w
            vorn, hinten = [], []
            for p in ps:
                _teilen(k.n, k.w, p, k.polys, k.polys, vorn, hinten)
            if vorn:
                if k.vorn is None:
                    k.vorn = _Knoten()
                stack.append((k.vorn, vorn))
            if hinten:
                if k.hinten is None:
                    k.hinten = _Knoten()
                stack.append((k.hinten, hinten))

    def invertieren(self):
        stack = [self]
        while stack:
            k = stack.pop()
            for p in k.polys:
                p.flip()
            if k.n is not None:
                k.n = (-k.n[0], -k.n[1], -k.n[2])
                k.w = -k.w
            k.vorn, k.hinten = k.hinten, k.vorn
            if k.vorn:
                stack.append(k.vorn)
            if k.hinten:
                stack.append(k.hinten)

    def beschneiden(self, polys):
        """The parts of `polys` outside the solid this tree describes."""
        out = []
        stack = [(self, list(polys))]
        while stack:
            k, ps = stack.pop()
            if k.n is None:
                out.extend(ps)
                continue
            vorn, hinten = [], []
            for p in ps:
                _teilen(k.n, k.w, p, vorn, hinten, vorn, hinten)
            if k.vorn:
                stack.append((k.vorn, vorn))
            else:
                out.extend(vorn)
            if k.hinten:
                stack.append((k.hinten, hinten))
        return out

    def beschneide_an(self, anderer):
        stack = [self]
        while stack:
            k = stack.pop()
            k.polys = anderer.beschneiden(k.polys)
            if k.vorn:
                stack.append(k.vorn)
            if k.hinten:
                stack.append(k.hinten)

    def alle(self):
        out, stack = [], [self]
        while stack:
            k = stack.pop()
            out.extend(k.polys)
            if k.vorn:
                stack.append(k.vorn)
            if k.hinten:
                stack.append(k.hinten)
        return out


def _vereinigung(a, b):
    a.beschneide_an(b)
    b.beschneide_an(a)
    b.invertieren()
    b.beschneide_an(a)
    b.invertieren()
    a.bauen(b.alle())
    return a


def _differenz(a, b):
    a.invertieren()
    a.beschneide_an(b)
    b.beschneide_an(a)
    b.invertieren()
    b.beschneide_an(a)
    b.invertieren()
    a.bauen(b.alle())
    a.invertieren()
    return a


# --------------------------------------------------------------------------
# mesh -> oriented triangles
# --------------------------------------------------------------------------
def dreiecke_orientiert(netz):
    """Closed mesh -> [(p, q, r)] with consistent outward winding. CSGFehler if the mesh
    is not closed (every edge must belong to exactly two triangles)."""
    index, punkte = {}, []

    def vid(p):
        key = (round(p[0], 5), round(p[1], 5), round(p[2], 5))
        i = index.get(key)
        if i is None:
            i = index[key] = len(punkte)
            punkte.append((float(p[0]), float(p[1]), float(p[2])))
        return i

    polys = []
    for fl in netz.flaechen:
        ids = [vid(netz.punkte[i]) for i in fl]
        sauber = [ids[0]]
        for i in ids[1:]:
            if i != sauber[-1]:
                sauber.append(i)
        if len(sauber) > 1 and sauber[0] == sauber[-1]:
            sauber.pop()
        if len(sauber) >= 3:
            polys.append(sauber)
    # T-junctions (merged bodies): a point that lies on the edge of a neighbouring face is
    # inserted into that edge, so that the surface is watertight
    index = _Achsenindex(punkte, set(i for pl in polys for i in pl))
    tris = []
    for sauber in polys:
        erweitert = []
        for k in range(len(sauber)):
            a, b = sauber[k], sauber[(k + 1) % len(sauber)]
            erweitert.append(a)
            erweitert.extend(index.auf_kante(a, b))
        sauber = erweitert
        pts = [punkte[i] for i in sauber]
        for (i, j, k) in G.triangulieren(pts):
            t = (sauber[i], sauber[j], sauber[k])
            if len(set(t)) < 3:
                continue
            a, b, c = punkte[t[0]], punkte[t[1]], punkte[t[2]]
            if _len(_cross(_sub(b, a), _sub(c, a))) < 1e-9:
                continue
            tris.append(t)
    if len(tris) < 4:
        raise CSGFehler("mesh too small")
    kanten = {}
    for ti, t in enumerate(tris):
        for e in range(3):
            a, b = t[e], t[(e + 1) % 3]
            kanten.setdefault((min(a, b), max(a, b)), []).append(ti)
    if any(len(v) != 2 for v in kanten.values()):
        raise CSGFehler("mesh not closed")
    drehen = [None] * len(tris)
    drehen[0] = False
    stapel = [0]
    while stapel:
        ti = stapel.pop()
        t = tris[ti]
        if drehen[ti]:
            t = (t[0], t[2], t[1])
        for e in range(3):
            a, b = t[e], t[(e + 1) % 3]
            for tj in kanten[(min(a, b), max(a, b))]:
                if tj == ti:
                    continue
                u = tris[tj]
                # the neighbour must run b -> a in its final orientation
                vorwaerts = any((u[f], u[(f + 1) % 3]) == (a, b) for f in range(3))
                soll = vorwaerts          # runs a -> b: has to be turned
                if drehen[tj] is None:
                    drehen[tj] = soll
                    stapel.append(tj)
                elif drehen[tj] != soll:
                    raise CSGFehler("mesh not orientable")
    out = []
    vol = 0.0
    for ti, t in enumerate(tris):
        if drehen[ti]:
            t = (t[0], t[2], t[1])
        a, b, c = punkte[t[0]], punkte[t[1]], punkte[t[2]]
        vol += _dot(a, _cross(b, c)) / 6.0
        out.append((a, b, c))
    if vol < 0:
        out = [(a, c, b) for (a, b, c) in out]
    return out


def _polys(dreiecke):
    out = []
    for t in dreiecke:
        p = _poly(list(t))
        if p is not None:
            out.append(p)
    return out


# --------------------------------------------------------------------------
# public
# --------------------------------------------------------------------------
class _KantenIndex:
    """The drawn edges of the input meshes: a smooth edge of the result is kept when it lies on
    one of them (cylinders keep their few vertical lines, spheres their meridians)."""

    def __init__(self, strecken):
        self.strecken = strecken
        alle = [p for s in strecken for p in s]
        if alle:
            lo = [min(p[k] for p in alle) for k in range(3)]
            hi = [max(p[k] for p in alle) for k in range(3)]
        else:
            lo, hi = [0, 0, 0], [1, 1, 1]
        self.lo = lo
        self.zell = max(max(hi[k] - lo[k] for k in range(3)) / 48.0, 1e-3)
        self.raster = {}
        for si, (a, b) in enumerate(strecken):
            c0 = self._zelle(((min(a[k], b[k]) for k in range(3))))
            c1 = self._zelle(((max(a[k], b[k]) for k in range(3))))
            n = (c1[0] - c0[0] + 1) * (c1[1] - c0[1] + 1) * (c1[2] - c0[2] + 1)
            if n > 400:
                continue
            for x in range(c0[0], c1[0] + 1):
                for y in range(c0[1], c1[1] + 1):
                    for z in range(c0[2], c1[2] + 1):
                        self.raster.setdefault((x, y, z), []).append(si)

    def _zelle(self, p):
        p = tuple(p)
        return tuple(int(math.floor((p[k] - self.lo[k]) / self.zell)) for k in range(3))

    def enthaelt(self, a, b):
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
        for si in self.raster.get(self._zelle(m), ()):
            p, q = self.strecken[si]
            pq = _sub(q, p)
            l2 = _dot(pq, pq)
            if l2 < 1e-12:
                continue
            for x in (a, b, m):
                t = _dot(_sub(x, p), pq) / l2
                if t < -1e-6 or t > 1 + 1e-6:
                    break
                d = _sub(x, (p[0] + pq[0] * t, p[1] + pq[1] * t, p[2] + pq[2] * t))
                if _len(d) > 1e-3:
                    break
            else:
                return True
        return False


def vereinigen(koerper):
    """koerper: [(host Netz, [cutter Netz, ...])] - every body is its host mesh minus the
    cutters (holes, cut-outs). -> {"p": points, "k": edges, "f": faces} of the union."""
    baum = None
    strecken = []
    for host, cutter in koerper:
        for nz in [host] + list(cutter):
            strecken.extend((nz.punkte[i], nz.punkte[j]) for i, j in nz.kanten)
    for host, cutter in koerper:
        k = _Knoten(_polys(dreiecke_orientiert(host)))
        for c in cutter:
            k = _differenz(k, _Knoten(_polys(dreiecke_orientiert(c))))
        if baum is None:
            baum = k
        else:
            baum = _vereinigung(baum, k)
    polys = baum.alle() if baum else []
    if not polys:
        raise CSGFehler("empty result")
    return _zu_netz(polys, _KantenIndex(strecken))


# --------------------------------------------------------------------------
# result -> mesh with outline edges
# --------------------------------------------------------------------------
class _Raster:
    """Merges points closer than `tol` (spatial hash)."""

    def __init__(self, tol=2e-4):
        self.tol = tol
        self.zellen = {}
        self.punkte = []

    def id(self, p):
        t = self.tol
        c = (int(math.floor(p[0] / t)), int(math.floor(p[1] / t)), int(math.floor(p[2] / t)))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for i in self.zellen.get((c[0] + dx, c[1] + dy, c[2] + dz), ()):
                        q = self.punkte[i]
                        if abs(q[0] - p[0]) <= t and abs(q[1] - p[1]) <= t and abs(q[2] - p[2]) <= t:
                            return i
        self.punkte.append((p[0], p[1], p[2]))
        i = len(self.punkte) - 1
        self.zellen.setdefault(c, []).append(i)
        return i


def _auf_strecke(p, a, b, tol=2e-4):
    """Parameter t (0 < t < 1) if p lies on the segment a-b, else None."""
    ab = _sub(b, a)
    l2 = _dot(ab, ab)
    if l2 < 1e-12:
        return None
    t = _dot(_sub(p, a), ab) / l2
    if t <= 1e-7 or t >= 1 - 1e-7:
        return None
    q = (a[0] + ab[0] * t, a[1] + ab[1] * t, a[2] + ab[2] * t)
    if abs(q[0] - p[0]) > tol or abs(q[1] - p[1]) > tol or abs(q[2] - p[2]) > tol:
        return None
    return t


class _Achsenindex:
    """Points sorted along x / y / z to find the points near an edge quickly."""

    def __init__(self, punkte, ids):
        self.punkte = punkte
        self.sortiert = []
        for ax in range(3):
            self.sortiert.append(sorted((punkte[i][ax], i) for i in ids))
        self.schluessel = [[w for w, _i in s] for s in self.sortiert]

    def auf_kante(self, a, b):
        pa, pb = self.punkte[a], self.punkte[b]
        ax = max(range(3), key=lambda k: abs(pb[k] - pa[k]))
        lo, hi = sorted((pa[ax], pb[ax]))
        s, ks = self.sortiert[ax], self.schluessel[ax]
        i0 = bisect.bisect_left(ks, lo - 1e-3)
        i1 = bisect.bisect_right(ks, hi + 1e-3)
        out = []
        for _w, i in s[i0:i1]:
            if i in (a, b):
                continue
            t = _auf_strecke(self.punkte[i], pa, pb)
            if t is not None:
                out.append((t, i))
        out.sort()
        return [i for _t, i in out]


def _zerlegen(a, b, index):
    zw = index.auf_kante(a, b)
    ketten = [a] + zw + [b]
    return list(zip(ketten, ketten[1:]))


def _zu_netz(polys, eigene=None):
    rs = _Raster()
    flaechen = []        # (ids, n, w)
    for p in polys:
        ids = []
        for v in p.v:
            i = rs.id(v)
            if not ids or ids[-1] != i:
                ids.append(i)
        if len(ids) > 1 and ids[0] == ids[-1]:
            ids.pop()
        if len(ids) < 3:
            continue
        pts = [rs.punkte[i] for i in ids]
        n = _normale(pts)
        if n is None:
            continue
        flaechen.append((ids, n, _dot(n, pts[0])))
    punkte = rs.punkte

    # 1. coplanar groups
    gruppen = []                          # [n, w, [flaechen index]]
    for fi, (_ids, n, w) in enumerate(flaechen):
        for g in gruppen:
            if _dot(g[0], n) > 1 - 1e-9 and abs(g[1] - w) < 1e-3:
                g[2].append(fi)
                break
        else:
            gruppen.append([n, w, [fi]])

    # 2. boundary of each group (shared edges cancel)
    kanten = {}                           # (min, max) -> list of group normals
    alle_ids = set(i for ids, _n, _w in flaechen for i in ids)
    for n, _w, fl in gruppen:
        ids_g = set(i for fi in fl for i in flaechen[fi][0])
        index = _Achsenindex(punkte, ids_g)
        gerichtet = {}
        for fi in fl:
            ids = flaechen[fi][0]
            for k in range(len(ids)):
                a, b = ids[k], ids[(k + 1) % len(ids)]
                for (x, y) in _zerlegen(a, b, index):
                    gerichtet[(x, y)] = gerichtet.get((x, y), 0) + 1
        for (x, y), c in gerichtet.items():
            rest = c - gerichtet.get((y, x), 0)
            if rest > 0:
                kanten.setdefault((min(x, y), max(x, y)), []).append(n)

    # 3. pieces of different groups along the same line -> common subdivision
    ids_k = set(i for e in kanten for i in e)
    index = _Achsenindex(punkte, ids_k)
    fein = {}
    for (a, b), ns in kanten.items():
        for (x, y) in _zerlegen(a, b, index):
            lst = fein.setdefault((min(x, y), max(x, y)), [])
            for n in ns:
                if not any(_dot(n, m) > 1 - 1e-9 for m in lst):
                    lst.append(n)

    # 4. skip smooth transitions (facets of round bodies)
    cmin = math.cos(math.radians(GLATT_WINKEL))
    zeichnen = {}
    for e, ns in fein.items():
        if len(ns) == 2 and _dot(ns[0], ns[1]) > cmin:
            if eigene is None or not eigene.enthaelt(punkte[e[0]], punkte[e[1]]):
                continue
        zeichnen[e] = True

    # 5. merge collinear pieces at vertices with exactly two edges
    nachbar = {}
    for (a, b) in zeichnen:
        nachbar.setdefault(a, set()).add(b)
        nachbar.setdefault(b, set()).add(a)
    geaendert = True
    while geaendert:
        geaendert = False
        for v in list(nachbar):
            nb = nachbar.get(v)
            if nb is None or len(nb) != 2:
                continue
            a, b = tuple(nb)
            u, w = _sub(punkte[a], punkte[v]), _sub(punkte[b], punkte[v])
            lu, lw = _len(u), _len(w)
            if lu < 1e-9 or lw < 1e-9:
                continue
            if _dot(u, w) / (lu * lw) < -1 + 1e-7 and a != b:
                nachbar[a].discard(v)
                nachbar[b].discard(v)
                nachbar[a].add(b)
                nachbar[b].add(a)
                del nachbar[v]
                geaendert = True
    kk = set()
    for a, nb in nachbar.items():
        for b in nb:
            kk.add((min(a, b), max(a, b)))

    # 6. compact output
    benutzt = sorted(alle_ids | set(i for e in kk for i in e))
    neu = {old: i for i, old in enumerate(benutzt)}
    return {"p": [[round(punkte[i][0], 4), round(punkte[i][1], 4), round(punkte[i][2], 4)]
                  for i in benutzt],
            "k": [[neu[a], neu[b]] for (a, b) in sorted(kk)],
            "f": [[neu[i] for i in ids] for ids, _n, _w in flaechen]}
