"""Roof geometry: weighted straight skeleton of a closed outline (no holes).

Every edge i of the outline has its own slope; the roof surface above the outline is the
surface whose face over edge i is inclined by the slope of that edge (hip roof for equal
slopes, a nearly vertical slope gives a gable). The roof is built by a wavefront simulation
(edge events and split events): time = height above the eaves.

dach_flaechen(punkte, neigungen, hoehe=None) ->
    {"flaechen": [(edge index, [(x, y, z), ...])],   one planar polygon per outline edge (the
                                                    index is the index in the given outline)
     "plateau": [(x, y, z), ...] or None,           flat top when the roof is cut at `hoehe`
     "grate": [((x, y, z), (x, y, z)), ...]}        ridges, hips and valleys
"""
import math

EPS = 1e-7
SPEED_GIEBEL = 1e-3                      # horizontal run per height of a (nearly) vertical gable face


def _geschwindigkeit(neigung_grad):
    if neigung_grad >= 89.9:
        return SPEED_GIEBEL
    return max(SPEED_GIEBEL, 1.0 / math.tan(math.radians(max(1.0, neigung_grad))))


class _V:
    __slots__ = ("P", "T", "vel", "prev", "next")

    def __init__(self, P, T, vel, prev, next_):
        self.P, self.T, self.vel, self.prev, self.next = P, T, vel, prev, next_

    def pos(self, t):
        d = t - self.T
        return (self.P[0] + self.vel[0] * d, self.P[1] + self.vel[1] * d)


def _flaeche(p):
    return sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p))) / 2.0


def dach_flaechen(punkte, neigungen, hoehe=None):
    pts = [tuple(map(float, p)) for p in punkte]
    n0 = len(pts)
    if n0 < 3:
        return {"flaechen": [], "plateau": None, "grate": []}
    # duplicate points are removed (edge index map), counter-clockwise outline
    idx = list(range(n0))
    clean, cidx = [], []
    for i, p in enumerate(pts):
        if clean and math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) < 1e-6:
            continue
        clean.append(p)
        cidx.append(i)
    if len(clean) > 1 and math.hypot(clean[0][0] - clean[-1][0], clean[0][1] - clean[-1][1]) < 1e-6:
        clean.pop()
        cidx.pop()
    # points in the middle of a straight edge (same slope on both sides) are dropped
    wieder = True
    while wieder and len(clean) > 3:
        wieder = False
        for k in range(len(clean)):
            a_, b_, c_ = clean[k - 1], clean[k], clean[(k + 1) % len(clean)]
            kr = (b_[0] - a_[0]) * (c_[1] - b_[1]) - (b_[1] - a_[1]) * (c_[0] - b_[0])
            dt = (b_[0] - a_[0]) * (c_[0] - b_[0]) + (b_[1] - a_[1]) * (c_[1] - b_[1])
            l1 = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
            l2 = math.hypot(c_[0] - b_[0], c_[1] - b_[1])
            n1 = neigungen[cidx[k - 1]] if cidx[k - 1] < len(neigungen) else 35.0
            n2 = neigungen[cidx[k]] if cidx[k] < len(neigungen) else 35.0
            if abs(kr) < 1e-6 * l1 * l2 and dt > 0 and abs(n1 - n2) < 1e-9:
                del clean[k]
                del cidx[k]
                wieder = True
                break
    n = len(clean)
    if n < 3 or abs(_flaeche(clean)) < 1e-6:
        return {"flaechen": [], "plateau": None, "grate": []}
    ccw = _flaeche(clean) > 0
    if not ccw:
        clean = list(reversed(clean))
        # edge k of the reversed outline runs from clean[k] to clean[k+1]; it is the original edge
        # that ran from the later to the earlier point
        orig = [cidx[(n - 2 - k) % n] for k in range(n)]
        # reversed point list: r[k] = c[n-1-k]; the edge r[k] -> r[k+1] = c[n-1-k] -> c[n-2-k] is
        # the original edge starting at c[n-2-k]
    else:
        orig = list(cidx)
    speed = [_geschwindigkeit(neigungen[o] if o < len(neigungen) else 35.0) for o in orig]
    ED, EN, EC = [], [], []
    for i in range(n):
        a, b = clean[i], clean[(i + 1) % n]
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        dx, dy = (b[0] - a[0]) / d, (b[1] - a[1]) / d
        ED.append((dx, dy))
        EN.append((-dy, dx))
        EC.append(-dy * a[0] + dx * a[1])

    def neu(P, T, prev, nxt):
        na, nb = EN[prev], EN[nxt]
        sa, sb = speed[prev], speed[nxt]
        det = na[0] * nb[1] - na[1] * nb[0]
        if abs(det) < 1e-9:                                    # (anti-)parallel neighbours
            vel = (na[0] * sa, na[1] * sa)
        else:
            vel = ((sa * nb[1] - sb * na[1]) / det, (na[0] * sb - nb[0] * sa) / det)
        return _V(P, T, vel, prev, nxt)

    loops = [[neu(clean[i], 0.0, (i - 1) % n, i) for i in range(n)]]
    arcs = []                                                  # (P0, T0, P1, T1, (a, b))

    def arc(v, P1, T1):
        P0 = v.pos(v.T)
        if math.hypot(P1[0] - P0[0], P1[1] - P0[1]) < 1e-6 and abs(T1 - v.T) < 1e-6:
            return
        arcs.append((v.P, v.T, P1, T1, (v.prev, v.next)))

    tn = 0.0
    top = hoehe if (hoehe is not None and hoehe > 0) else None
    zaehler = 0
    while loops and zaehler < 20 * n + 100:
        zaehler += 1
        best = None
        for li, L in enumerate(loops):
            m = len(L)
            for i in range(m):
                u, w = L[i], L[(i + 1) % m]
                e = u.next
                pu, pw = u.pos(tn), w.pos(tn)
                ln = (pw[0] - pu[0]) * ED[e][0] + (pw[1] - pu[1]) * ED[e][1]
                rate = (w.vel[0] - u.vel[0]) * ED[e][0] + (w.vel[1] - u.vel[1]) * ED[e][1]
                if rate < -EPS:
                    t = tn + max(0.0, ln) / (-rate)
                    if best is None or t < best[0] - 1e-9:
                        best = (t, "edge", li, i, None)
                v = L[i]
                cr = ED[v.prev][0] * ED[v.next][1] - ED[v.prev][1] * ED[v.next][0]
                if cr >= -1e-9:
                    continue                                    # convex vertex: no split
                pv = v.pos(tn)
                for j in range(m):
                    if j == i or (j + 1) % m == i:
                        continue
                    a_, b_ = L[j], L[(j + 1) % m]
                    e2 = a_.next
                    den = EN[e2][0] * v.vel[0] + EN[e2][1] * v.vel[1] - speed[e2]
                    if den >= -EPS:
                        continue
                    d0 = EN[e2][0] * pv[0] + EN[e2][1] * pv[1] - (EC[e2] + speed[e2] * tn)
                    t = tn - d0 / den
                    if t < tn - 1e-9:
                        continue
                    q = v.pos(t)
                    pa, pb = a_.pos(t), b_.pos(t)
                    s_ = (q[0] - pa[0]) * ED[e2][0] + (q[1] - pa[1]) * ED[e2][1]
                    l_ = (pb[0] - pa[0]) * ED[e2][0] + (pb[1] - pa[1]) * ED[e2][1]
                    if s_ < -1e-6 or s_ > l_ + 1e-6 or l_ < -1e-6:
                        continue
                    if best is None or t < best[0] - 1e-9:
                        best = (t, "split", li, i, j)
        if best is None or (top is not None and best[0] > top):
            break
        t, art, li, i, j = best
        tn = max(tn, t)
        L = loops[li]
        m = len(L)
        if art == "edge":
            u, w = L[i], L[(i + 1) % m]
            N = u.pos(t)
            N2 = w.pos(t)
            N = ((N[0] + N2[0]) / 2, (N[1] + N2[1]) / 2)
            arc(u, N, t)
            arc(w, N, t)
            x = neu(N, t, u.prev, w.next)
            wi = (i + 1) % m
            neu_l = []
            for k, v in enumerate(L):
                if k == i:
                    neu_l.append(x)
                elif k != wi:
                    neu_l.append(v)
            loops[li] = neu_l
            L = neu_l
            if len(L) <= 2:
                _abschliessen(L, t, arc, arcs)
                loops.pop(li)
        else:
            v = L[i]
            a_, b_ = L[j], L[(j + 1) % m]
            N = v.pos(t)
            arc(v, N, t)
            e2 = a_.next
            v1 = neu(N, t, e2, v.next)                          # continues with the next edge of v
            v2 = neu(N, t, v.prev, e2)
            # loop 1: v1, v+1, ..., a_ ; loop 2: v2, b_, ..., v-1
            seq = [L[(i + k) % m] for k in range(m)]            # v first
            ia = seq.index(a_)
            l1 = [v1] + seq[1:ia + 1]
            l2 = [v2] + seq[ia + 1:]
            loops.pop(li)
            for ll in (l1, l2):
                if len(ll) <= 2:
                    _abschliessen(ll, t, arc, arcs)
                else:
                    loops.append(ll)
    # remaining loops (cut at the roof height)
    plateau = []
    if loops and top is not None:
        for L in loops:
            m = len(L)
            ps = [v.pos(top) for v in L]
            for k, v in enumerate(L):
                arc(v, ps[k], top)
                arcs.append((ps[k], top, ps[(k + 1) % m], top, (v.next, -1)))
            plateau.append([(p[0], p[1], top) for p in ps])
    # faces: walk along the arcs that belong to an outline edge
    def key(P, T):
        return (round(P[0], 2), round(P[1], 2), round(T, 2))
    faces = []
    for e in range(n):
        a, b = clean[e], clean[(e + 1) % n]
        adj = {}
        for (P0, T0, P1, T1, lab) in arcs:
            if e in lab:
                k0, k1 = key(P0, T0), key(P1, T1)
                if k0 == k1:
                    continue
                adj.setdefault(k0, []).append((k1, (P1, T1)))
                adj.setdefault(k1, []).append((k0, (P0, T0)))
        ka, kb = key(a, 0.0), key(b, 0.0)
        poly = [(a[0], a[1], 0.0), (b[0], b[1], 0.0)]
        cur, prev = kb, ka
        benutzt = set()
        for _ in range(4 * len(arcs) + 8):
            if cur == ka:
                break
            nxts = [x for x in adj.get(cur, []) if x[0] != prev and (cur, x[0]) not in benutzt]
            if not nxts:
                nxts = [x for x in adj.get(cur, []) if (cur, x[0]) not in benutzt]
            if not nxts:
                break
            k1, (P1, T1) = nxts[0]
            benutzt.add((cur, k1))
            benutzt.add((k1, cur))
            prev, cur = cur, k1
            if cur != ka:
                poly.append((P1[0], P1[1], T1))
        faces.append((orig[e], poly))
    grate = []
    seen = set()
    for (P0, T0, P1, T1, lab) in arcs:
        if lab[1] == -1:
            continue
        k = (key(P0, T0), key(P1, T1))
        if k in seen or (k[1], k[0]) in seen:
            continue
        seen.add(k)
        grate.append(((P0[0], P0[1], T0), (P1[0], P1[1], T1)))
    return {"flaechen": faces, "plateau": plateau or None, "grate": grate}


def _abschliessen(L, t, arc, arcs):
    """A wavefront loop with two vertices is finished: the traces end here; the two vertices
    are the ends of the last ridge."""
    ps = [v.pos(t) for v in L]
    for v, p in zip(L, ps):
        arc(v, p, t)
    if len(L) == 2:
        (x0, y0), (x1, y1) = ps
        if math.hypot(x1 - x0, y1 - y0) > 1e-6:
            arcs.append((ps[0], t, ps[1], t, (L[0].next, L[1].next)))
