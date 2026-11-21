# -*- coding: utf-8 -*-
"""
katiecad/ui/kt/geometry.py - the Tk geometry managers pack, grid and place (BSD-3-Clause).

The algorithms follow Tk's own (tkPack.c / tkGrid.c / tkPlace.c), so a dialog built with
pack/grid gets the same sizes and positions as under Tk.
"""


def _setzen_in(m, s, x, y, w, h, sichtbar=True):
    """Places slave s of geometry master m; with pack/grid(in_=...) the master may be a
    descendant of the slave's parent: the position is then converted to the parent."""
    if s.master is not m:
        w_ = m
        while w_ is not None and w_ is not s.master:
            x += w_._kt_x + w_._kt_kind_versatz_x()
            y += w_._kt_y + w_._kt_kind_versatz_y()
            if not (w_._kt_lebt and w_._kt_sichtbar):
                sichtbar = False
            w_ = w_.master
    s._kt_setzen(x, y, w, h, sichtbar=sichtbar)


def _paar(v):
    """padx=4 or padx=(2, 6) -> (left, right)."""
    if v is None or v == "":
        return 0, 0
    if isinstance(v, (tuple, list)):
        if len(v) == 1:
            return int(v[0]), int(v[0])
        return int(v[0]), int(v[1])
    if isinstance(v, str) and " " in v.strip():
        a, b = v.split()[:2]
        return int(float(a)), int(float(b))
    v = int(float(v))
    return v, v


def _sticky(s):
    s = (s or "").lower().replace(",", "").replace(" ", "")
    return set(s)


# ============================================================
# Mixin for widgets
# ============================================================
class GeometrieMixin:
    # ---------------------------------------------------- pack
    def pack_configure(self, cnf=None, **kw):
        """pack() / pack_configure(): takes the widget into the pack list of its master (or of
        `in_`), at the position given by before/after, and stores the options (side, fill,
        expand, anchor, padding). The master is laid out again before the next frame.
        """
        if cnf:
            kw = {**cnf, **kw}
        master = kw.pop("in_", None) or kw.pop("in", None) or self.master
        if self._kt_manager != "pack" or self._kt_geo_master is not master:
            self._kt_geo_vergessen()
            info = {"side": "top", "fill": "none", "expand": False, "anchor": "center",
                    "padx": (0, 0), "pady": (0, 0), "ipadx": 0, "ipady": 0}
            self._kt_pinfo = info
            self._kt_manager = "pack"
            self._kt_geo_master = master
            vor, nach = kw.pop("before", None), kw.pop("after", None)
            liste = master._pack_slaves
            if vor is not None and vor in liste:
                liste.insert(liste.index(vor), self)
            elif nach is not None and nach in liste:
                liste.insert(liste.index(nach) + 1, self)
            else:
                liste.append(self)
        else:
            vor, nach = kw.pop("before", None), kw.pop("after", None)
            liste = master._pack_slaves
            if vor is not None or nach is not None:
                liste.remove(self)
                if vor is not None and vor in liste:
                    liste.insert(liste.index(vor), self)
                elif nach is not None and nach in liste:
                    liste.insert(liste.index(nach) + 1, self)
                else:
                    liste.append(self)
        i = self._kt_pinfo
        for k, v in kw.items():
            if k in ("padx", "pady"):
                i[k] = _paar(v)
            elif k in ("ipadx", "ipady"):
                i[k] = int(float(v))
            elif k == "expand":
                i[k] = bool(v) and v not in ("0", "false", "no")
            elif k in ("side", "fill", "anchor"):
                i[k] = str(v)
        self._kt_abbilden_planen()

    pack = pack_configure

    def pack_forget(self):
        if self._kt_manager == "pack":
            self._kt_geo_vergessen()

    def pack_info(self):
        if self._kt_manager != "pack":
            from katiecad.ui.kt.tkmod import TclError
            raise TclError(f'window "{self}" isn\'t packed')
        i = dict(self._kt_pinfo)
        i["in"] = self._kt_geo_master
        return i

    def pack_slaves(self):
        return list(self._pack_slaves)

    def pack_propagate(self, flag=None):
        if flag is None:
            return self._kt_propagate
        self._kt_propagate = bool(flag)
        self._kt_layout_planen()

    propagate = pack_propagate

    # ---------------------------------------------------- grid
    def grid_configure(self, cnf=None, **kw):
        """grid() / grid_configure(): takes the widget into the grid of its master; without
        `row` it goes into the next free row like in Tk. Options of a former grid() call are
        kept (grid_remove / grid again).
        """
        if cnf:
            kw = {**cnf, **kw}
        master = kw.pop("in_", None) or kw.pop("in", None) or self.master
        neu = self._kt_manager != "grid" or self._kt_geo_master is not master
        if neu:
            alt = getattr(self, "_kt_grid_gemerkt", None) if self._kt_geo_master is master else None
            self._kt_geo_vergessen()
            info = alt or {"row": None, "column": 0, "rowspan": 1, "columnspan": 1, "sticky": set(),
                           "padx": (0, 0), "pady": (0, 0), "ipadx": 0, "ipady": 0}
            self._kt_pinfo = info
            self._kt_manager = "grid"
            self._kt_geo_master = master
            master._grid_slaves.append(self)
        i = self._kt_pinfo
        for k, v in kw.items():
            if k in ("padx", "pady"):
                i[k] = _paar(v)
            elif k in ("ipadx", "ipady"):
                i[k] = int(float(v))
            elif k == "sticky":
                i[k] = _sticky(v)
            elif k in ("row", "column", "rowspan", "columnspan"):
                i[k] = max(0 if k in ("row", "column") else 1, int(v))
        if i["row"] is None:
            # first empty row of the master
            belegt = [s._kt_pinfo["row"] + s._kt_pinfo["rowspan"] for s in master._grid_slaves
                      if s is not self and s._kt_pinfo.get("row") is not None]
            i["row"] = max(belegt) if belegt else 0
        self._kt_abbilden_planen()

    grid = grid_configure

    def grid_forget(self):
        if self._kt_manager == "grid":
            self._kt_geo_vergessen()

    def grid_remove(self):
        if self._kt_manager == "grid":
            gemerkt = dict(self._kt_pinfo)
            self._kt_geo_vergessen()
            self._kt_grid_gemerkt = gemerkt

    def grid_info(self):
        if self._kt_manager != "grid":
            return {}
        i = dict(self._kt_pinfo)
        i["sticky"] = "".join(sorted(i["sticky"]))
        i["in"] = self._kt_geo_master
        return i

    def grid_slaves(self, row=None, column=None):
        erg = []
        for s in reversed(self._grid_slaves):
            i = s._kt_pinfo
            if row is not None and not (i["row"] <= row < i["row"] + i["rowspan"]):
                continue
            if column is not None and not (i["column"] <= column < i["column"] + i["columnspan"]):
                continue
            erg.append(s)
        return erg

    def grid_size(self):
        sp = max([s._kt_pinfo["column"] + s._kt_pinfo["columnspan"] for s in self._grid_slaves] or [0])
        ze = max([s._kt_pinfo["row"] + s._kt_pinfo["rowspan"] for s in self._grid_slaves] or [0])
        return sp, ze

    def grid_propagate(self, flag=None):
        return self.pack_propagate(flag)

    def _kt_rc_konfig(self, tabelle, index, cnf=None, **kw):
        """Shared code of columnconfigure / rowconfigure: stores weight, minsize, pad and
        uniform for one index, a list of indices or "all"; without options it returns the
        settings of the (first) index.
        """
        if cnf:
            kw = {**cnf, **kw}
        if isinstance(index, (tuple, list)):
            idx = list(index)
        elif index == "all":
            idx = sorted({s._kt_pinfo["column" if tabelle is self._grid_spalten else "row"]
                          for s in self._grid_slaves})
        else:
            idx = [int(index)]
        if not kw:
            return dict(tabelle.get(idx[0], {})) if idx else {}
        for i in idx:
            d = tabelle.setdefault(int(i), {})
            for k, v in kw.items():
                if k in ("weight", "minsize", "pad"):
                    d[k] = int(float(v))
                elif k == "uniform":
                    d[k] = v or None
        self._kt_layout_planen()

    def grid_columnconfigure(self, index, cnf=None, **kw):
        return self._kt_rc_konfig(self._grid_spalten, index, cnf, **kw)

    def grid_rowconfigure(self, index, cnf=None, **kw):
        return self._kt_rc_konfig(self._kt_grid_zeilen, index, cnf, **kw)

    columnconfigure = grid_columnconfigure
    rowconfigure = grid_rowconfigure

    def grid_bbox(self, column=None, row=None, col2=None, row2=None):
        return (0, 0, self._kt_w, self._kt_h)

    # ---------------------------------------------------- place
    def place_configure(self, cnf=None, **kw):
        """place() / place_configure(): takes the widget into the place list of its master and
        stores the absolute and relative position and size and the anchor.
        """
        if cnf:
            kw = {**cnf, **kw}
        master = kw.pop("in_", None) or kw.pop("in", None) or self.master
        if self._kt_manager != "place" or self._kt_geo_master is not master:
            self._kt_geo_vergessen()
            self._kt_pinfo = {"x": 0, "y": 0, "relx": 0.0, "rely": 0.0, "width": None,
                           "height": None, "relwidth": None, "relheight": None, "anchor": "nw"}
            self._kt_manager = "place"
            self._kt_geo_master = master
            master._kt_place_slaves.append(self)
        i = self._kt_pinfo
        for k, v in kw.items():
            if k in ("x", "y"):
                i[k] = int(float(v))
            elif k in ("relx", "rely"):
                i[k] = float(v)
            elif k in ("width", "height"):
                i[k] = None if v in (None, "") else int(float(v))
            elif k in ("relwidth", "relheight"):
                i[k] = None if v in (None, "") else float(v)
            elif k == "anchor":
                i[k] = str(v)
        self._kt_abbilden_planen()

    place = place_configure

    def place_forget(self):
        if self._kt_manager == "place":
            self._kt_geo_vergessen()

    def place_info(self):
        return dict(self._kt_pinfo) if self._kt_manager == "place" else {}

    def place_slaves(self):
        return list(self._kt_place_slaves)

    # ---------------------------------------------------- common
    def winfo_manager(self):
        return self._kt_manager or ""

    def _kt_geo_vergessen(self):
        m = self._kt_geo_master
        if m is not None:
            for liste in (m._pack_slaves, m._grid_slaves, m._kt_place_slaves):
                if self in liste:
                    liste.remove(self)
            m._kt_layout_planen()
        self._kt_manager = None
        self._kt_geo_master = None
        self._kt_abbilden(False)


# ============================================================
# Requested size of a master
# ============================================================
def pack_req(m):
    """Size a pack master asks for (width, height), computed like Tk's pack: slaves packed
    top/bottom are stacked vertically, left/right ones side by side, each with its padding;
    the result is the size that just fits all of them.
    """
    breite = hoehe = max_b = max_h = 0
    for s in m._pack_slaves:
        if not s._kt_lebt:
            continue
        i = s._kt_pinfo
        sw, sh = s._kt_req()
        px = i["padx"][0] + i["padx"][1] + 2 * i["ipadx"]
        py = i["pady"][0] + i["pady"][1] + 2 * i["ipady"]
        if i["side"] in ("top", "bottom"):
            max_b = max(max_b, sw + px + breite)
            hoehe += sh + py
        else:
            max_h = max(max_h, sh + py + hoehe)
            breite += sw + px
    return max(max_b, breite), max(max_h, hoehe)


def _x_ausdehnung(slaves, ab, hohlraum):
    """How many extra pixels each expanding slave gets horizontally, considering only slaves
    from position `ab` on (Tk's XExpansion in tkPack.c). `hohlraum` is the width still free.
    """
    min_exp = hohlraum
    anzahl = 0
    for s in slaves[ab:]:
        i = s._kt_pinfo
        kind = s._kt_req()[0] + i["padx"][0] + i["padx"][1] + 2 * i["ipadx"]
        if i["side"] in ("top", "bottom"):
            if anzahl:
                min_exp = min(min_exp, (hohlraum - kind) // anzahl)
        else:
            hohlraum -= kind
            if i["expand"]:
                anzahl += 1
    if anzahl:
        min_exp = min(min_exp, hohlraum // anzahl)
    return max(0, min_exp)


def _y_ausdehnung(slaves, ab, hohlraum):
    """Vertical counterpart of _x_ausdehnung (Tk's YExpansion)."""
    min_exp = hohlraum
    anzahl = 0
    for s in slaves[ab:]:
        i = s._kt_pinfo
        kind = s._kt_req()[1] + i["pady"][0] + i["pady"][1] + 2 * i["ipady"]
        if i["side"] in ("left", "right"):
            if anzahl:
                min_exp = min(min_exp, (hohlraum - kind) // anzahl)
        else:
            hohlraum -= kind
            if i["expand"]:
                anzahl += 1
    if anzahl:
        min_exp = min(min_exp, hohlraum // anzahl)
    return max(0, min_exp)


def _anker(anchor, fx, fy, fw, fh, w, h):
    """Position (x, y) of a widget of size (w, h) inside the frame (fx, fy, fw, fh) for a Tk
    anchor (n, ne, e, se, s, sw, w, nw, center).
    """
    a = anchor
    if a in ("n", "center", "s"):
        x = fx + (fw - w) // 2
    elif "w" in a:
        x = fx
    else:
        x = fx + fw - w
    if a in ("w", "center", "e"):
        y = fy + (fh - h) // 2
    elif "n" in a:
        y = fy
    else:
        y = fy + fh - h
    return x, y


def pack_anordnen(m):
    """Places the pack slaves of master `m` (Tk's ArrangePacking): each slave in turn gets a
    parcel cut from the remaining cavity on its side, enlarged by expand, then the slave is
    placed in its parcel according to fill and anchor. A slave left without any room is
    hidden, as in Tk.
    """
    l, t, r, b = m._kt_innen()
    cx, cy = l, t
    cw, ch = m._kt_w - l - r, m._kt_h - t - b
    slaves = [s for s in m._pack_slaves if s._kt_lebt]
    for n, s in enumerate(slaves):
        i = s._kt_pinfo
        sw, sh = s._kt_req()
        padx, pady = i["padx"][0] + i["padx"][1], i["pady"][0] + i["pady"][1]
        if i["side"] in ("top", "bottom"):
            fw = cw
            fh = sh + pady + 2 * i["ipady"]
            if i["expand"]:
                fh += _y_ausdehnung(slaves, n, ch)
            ch -= fh
            if ch < 0:
                fh += ch
                ch = 0
            fx = cx
            if i["side"] == "top":
                fy = cy
                cy += fh
            else:
                fy = cy + ch
        else:
            fh = ch
            fw = sw + padx + 2 * i["ipadx"]
            if i["expand"]:
                fw += _x_ausdehnung(slaves, n, cw)
            cw -= fw
            if cw < 0:
                fw += cw
                cw = 0
            fy = cy
            if i["side"] == "left":
                fx = cx
                cx += fw
            else:
                fx = cx + cw
        w = sw + 2 * i["ipadx"]
        if i["fill"] in ("x", "both") or w > fw - padx:
            w = fw - padx
        h = sh + 2 * i["ipady"]
        if i["fill"] in ("y", "both") or h > fh - pady:
            h = fh - pady
        x, y = _anker(i["anchor"], fx + i["padx"][0], fy + i["pady"][0], fw - padx, fh - pady, w, h)
        if w <= 0 or h <= 0:
            _setzen_in(m, s, x, y, 0, 0, sichtbar=False)
        else:
            _setzen_in(m, s, x, y, w, h)


# ------------------------------------------------------------ grid
def _grid_raster(m):
    """-> (column sizes, row sizes) requested, plus info per slave."""
    slaves = [s for s in m._grid_slaves if s._kt_lebt]
    sp_n = max([s._kt_pinfo["column"] + s._kt_pinfo["columnspan"] for s in slaves] or [0])
    ze_n = max([s._kt_pinfo["row"] + s._kt_pinfo["rowspan"] for s in slaves] or [0])
    sp_n = max(sp_n, max(list(m._grid_spalten) or [-1]) + 1)
    ze_n = max(ze_n, max(list(m._kt_grid_zeilen) or [-1]) + 1)
    spalten = [m._grid_spalten.get(k, {}).get("minsize", 0) for k in range(sp_n)]
    zeilen = [m._kt_grid_zeilen.get(k, {}).get("minsize", 0) for k in range(ze_n)]
    pad_s = [m._grid_spalten.get(k, {}).get("pad", 0) for k in range(sp_n)]
    pad_z = [m._kt_grid_zeilen.get(k, {}).get("pad", 0) for k in range(ze_n)]
    mehr = []
    for s in slaves:
        i = s._kt_pinfo
        sw, sh = s._kt_req()
        w = sw + i["padx"][0] + i["padx"][1] + 2 * i["ipadx"]
        h = sh + i["pady"][0] + i["pady"][1] + 2 * i["ipady"]
        if i["columnspan"] == 1:
            k = i["column"]
            spalten[k] = max(spalten[k], w + pad_s[k])
        else:
            mehr.append(("s", i["column"], i["columnspan"], w))
        if i["rowspan"] == 1:
            k = i["row"]
            zeilen[k] = max(zeilen[k], h + pad_z[k])
        else:
            mehr.append(("z", i["row"], i["rowspan"], h))
    # slaves spanning several columns/rows: distribute the missing size (weighted columns first)
    for art, start, n, groesse in mehr:
        liste = spalten if art == "s" else zeilen
        konf = m._grid_spalten if art == "s" else m._kt_grid_zeilen
        jetzt = sum(liste[start:start + n])
        if groesse > jetzt:
            fehlt = groesse - jetzt
            gew = [konf.get(k, {}).get("weight", 0) for k in range(start, start + n)]
            summe = sum(gew)
            if summe:
                for j, g in enumerate(gew):
                    liste[start + j] += fehlt * g // summe
                liste[start + n - 1] += fehlt - sum(fehlt * g // summe for g in gew)
            else:
                liste[start + n - 1] += fehlt
    # uniform groups
    for liste, konf in ((spalten, m._grid_spalten), (zeilen, m._kt_grid_zeilen)):
        gruppen = {}
        for k, d in konf.items():
            if d.get("uniform") and k < len(liste):
                gruppen.setdefault(d["uniform"], []).append(k)
        for ks in gruppen.values():
            pro = max(liste[k] / max(1, konf[k].get("weight", 1) or 1) for k in ks)
            for k in ks:
                liste[k] = int(pro * max(1, konf[k].get("weight", 1) or 1))
    return slaves, spalten, zeilen


def grid_req(m):
    _s, spalten, zeilen = _grid_raster(m)
    return sum(spalten), sum(zeilen)


def _verteilen(liste, konf, verfuegbar):
    """Distributes the available length among the grid columns (or rows) `liste` (their
    requested sizes): extra space goes to the weighted ones in proportion to their weight,
    missing space is taken from them without going below minsize. Returns the sizes and the
    start positions (one more than columns).
    """
    groessen = list(liste)
    diff = verfuegbar - sum(groessen)
    gew = [konf.get(k, {}).get("weight", 0) for k in range(len(groessen))]
    summe = sum(gew)
    if diff and summe:
        if diff > 0:
            rest = diff
            for k, g in enumerate(gew):
                if g:
                    add = diff * g // summe
                    groessen[k] += add
                    rest -= add
            for k in range(len(gew) - 1, -1, -1):
                if gew[k]:
                    groessen[k] += rest
                    break
        else:
            # shrink weighted columns, never below their minsize
            fehlt = -diff
            for _runde in range(4):
                aktiv = [k for k, g in enumerate(gew)
                         if g and groessen[k] > konf.get(k, {}).get("minsize", 0)]
                if not aktiv or fehlt <= 0:
                    break
                s = sum(gew[k] for k in aktiv)
                weg = 0
                for k in aktiv:
                    d = min(groessen[k] - konf.get(k, {}).get("minsize", 0), fehlt * gew[k] // s or 1)
                    groessen[k] -= d
                    weg += d
                fehlt -= weg
                if weg == 0:
                    break
    pos = [0]
    for g in groessen:
        pos.append(pos[-1] + g)
    return groessen, pos


def grid_anordnen(m):
    """Places the grid slaves of master `m`: column widths and row heights from _grid_raster,
    distributed with _verteilen; each slave fills its cells (span, padding, pad of the
    column/row) according to sticky, otherwise it keeps its requested size and is centred on
    that axis. A slave left without any room is hidden.
    """
    slaves, spalten, zeilen = _grid_raster(m)
    if not slaves:
        return
    l, t, r, b = m._kt_innen()
    bw, bh = m._kt_w - l - r, m._kt_h - t - b
    _gs, xs = _verteilen(spalten, m._grid_spalten, bw)
    _gz, ys = _verteilen(zeilen, m._kt_grid_zeilen, bh)
    # grid anchor "nw": unused space stays right/bottom
    for s in slaves:
        i = s._kt_pinfo
        c0, c1 = i["column"], i["column"] + i["columnspan"]
        r0, r1 = i["row"], i["row"] + i["rowspan"]
        fx = l + xs[c0] + i["padx"][0]
        fy = t + ys[r0] + i["pady"][0]
        pad_s = m._grid_spalten.get(c0, {}).get("pad", 0)
        pad_z = m._kt_grid_zeilen.get(r0, {}).get("pad", 0)
        fx += pad_s // 2
        fy += pad_z // 2
        fw = xs[c1] - xs[c0] - i["padx"][0] - i["padx"][1] - pad_s
        fh = ys[r1] - ys[r0] - i["pady"][0] - i["pady"][1] - pad_z
        sw, sh = s._kt_req()
        w = min(sw + 2 * i["ipadx"], fw)
        h = min(sh + 2 * i["ipady"], fh)
        st = i["sticky"]
        if "w" in st and "e" in st:
            w = fw
        if "n" in st and "s" in st:
            h = fh
        if "w" in st and "e" in st or "w" in st:
            x = fx
        elif "e" in st:
            x = fx + fw - w
        else:
            x = fx + (fw - w) // 2
        if "n" in st and "s" in st or "n" in st:
            y = fy
        elif "s" in st:
            y = fy + fh - h
        else:
            y = fy + (fh - h) // 2
        if w <= 0 or h <= 0:
            _setzen_in(m, s, x, y, 0, 0, sichtbar=False)
        else:
            _setzen_in(m, s, x, y, w, h)


# ------------------------------------------------------------ place
def place_anordnen(m):
    """Places the place slaves of master `m`: absolute x/y/width/height plus the relative parts
    (relx, relwidth ...) of the master's size, shifted by the anchor.
    """
    for s in m._kt_place_slaves:
        if not s._kt_lebt:
            continue
        i = s._kt_pinfo
        sw, sh = s._kt_req()
        w = i["width"] if i["width"] is not None else sw
        h = i["height"] if i["height"] is not None else sh
        if i["relwidth"] is not None:
            w = int(i["relwidth"] * m._kt_w) + (i["width"] or 0)
        if i["relheight"] is not None:
            h = int(i["relheight"] * m._kt_h) + (i["height"] or 0)
        x = i["x"] + int(i["relx"] * m._kt_w)
        y = i["y"] + int(i["rely"] * m._kt_h)
        a = i["anchor"]
        if a in ("n", "center", "s"):
            x -= w // 2
        elif "e" in a:
            x -= w
        if a in ("w", "center", "e"):
            y -= h // 2
        elif "s" in a:
            y -= h
        _setzen_in(m, s, x, y, max(0, w), max(0, h), sichtbar=w > 0 and h > 0)
