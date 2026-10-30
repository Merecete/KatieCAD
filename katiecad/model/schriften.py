# -*- coding: utf-8 -*-
"""
katiecad/model/schriften.py - Additional (installed) fonts, no extra library needed.

* scan(): finds installed TrueType fonts (.ttf/.otf) and reads family / style.
* aktiviere(namen): makes chosen fonts known to the program (config key "schriften").
* breite(name, fett): width function in 1/1000 em (text boxes match the real font).
* pdf_objekte(): data for embedding the font into the PDF (TrueType outlines only).

Fonts with CFF outlines (some .otf) and fonts whose licence forbids embedding are still
usable on screen; the PDF then falls back to Helvetica.
"""

import os
import struct
import sys

STANDARD_SCHRIFTEN = ["Arial", "Courier New", "Times New Roman",
                      "Consolas", "Verdana", "Tahoma", "Segoe UI"]

MAX_EINBETTEN = 12 * 1024 * 1024        # bigger font files are not embedded (PDF size)

_aktiv = {}          # family -> {"regular": path or None, "bold": path or None}
_geladen = {}        # path -> TTF or None


def schrift_ordner():
    """Directories where fonts are usually installed."""
    if sys.platform.startswith("win"):
        win = os.environ.get("WINDIR", r"C:\Windows")
        lokal = os.environ.get("LOCALAPPDATA", "")
        liste = [os.path.join(win, "Fonts")]
        if lokal:
            liste.append(os.path.join(lokal, "Microsoft", "Windows", "Fonts"))
        return liste
    if sys.platform == "darwin":
        return ["/System/Library/Fonts", "/Library/Fonts",
                os.path.expanduser("~/Library/Fonts")]
    return ["/usr/share/fonts", "/usr/local/share/fonts",
            os.path.expanduser("~/.fonts"), os.path.expanduser("~/.local/share/fonts")]


class TTF:
    """Minimal reader for a TrueType/OpenType font file."""

    def __init__(self, daten):
        self.daten = daten
        if len(daten) < 12:
            raise ValueError("zu kurz")
        tag = daten[:4]
        if tag not in (b"\x00\x01\x00\x00", b"true", b"OTTO"):
            raise ValueError("kein TrueType/OpenType")
        n = struct.unpack(">H", daten[4:6])[0]
        self.tab = {}
        for i in range(n):
            t, _cs, off, ln = struct.unpack(">4sIII", daten[12 + 16 * i:28 + 16 * i])
            self.tab[t.decode("latin-1")] = (off, ln)
        self.cff = tag == b"OTTO" or "CFF " in self.tab
        if "head" not in self.tab or "hhea" not in self.tab or "hmtx" not in self.tab:
            raise ValueError("Tabellen fehlen")
        o = self.tab["head"][0]
        self.upem = struct.unpack(">H", daten[o + 18:o + 20])[0] or 1000
        self.bbox = struct.unpack(">hhhh", daten[o + 36:o + 44])
        o = self.tab["hhea"][0]
        self.ascent, self.descent = struct.unpack(">hh", daten[o + 4:o + 8])
        self.n_hm = struct.unpack(">H", daten[o + 34:o + 36])[0]
        self._breiten = None
        self._cmap = None
        self.fs_type = 0
        self.gewicht = 400
        self.cap = 0
        if "OS/2" in self.tab:
            o, ln = self.tab["OS/2"]
            self.gewicht = struct.unpack(">H", daten[o + 4:o + 6])[0]
            self.fs_type = struct.unpack(">H", daten[o + 8:o + 10])[0]
            if ln >= 90:
                self.cap = struct.unpack(">h", daten[o + 88:o + 90])[0]
        self.italic = 0.0
        if "post" in self.tab:
            o = self.tab["post"][0]
            self.italic = struct.unpack(">i", daten[o + 4:o + 8])[0] / 65536.0

    # --- names -------------------------------------------------------
    def namen(self):
        """-> {nameID: text} (preferably Windows/English)."""
        out = {}
        if "name" not in self.tab:
            return out
        o, _ln = self.tab["name"]
        d = self.daten
        anz, so = struct.unpack(">HH", d[o + 2:o + 6])
        for i in range(anz):
            pid, eid, lid, nid, ln, off = struct.unpack(">6H", d[o + 6 + 12 * i:o + 18 + 12 * i])
            if nid not in (1, 2, 4, 6, 16, 17):
                continue
            roh = d[o + so + off:o + so + off + ln]
            try:
                if pid in (0, 3):
                    text = roh.decode("utf-16-be")
                elif pid == 1 and eid == 0:
                    text = roh.decode("mac_roman")
                else:
                    continue
            except UnicodeDecodeError:
                continue
            bevorzugt = pid == 3 and lid == 0x409
            if nid not in out or bevorzugt:
                out[nid] = text
        return out

    def familie_stil(self):
        n = self.namen()
        return (n.get(1) or n.get(16) or "").strip(), (n.get(2) or n.get(17) or "").strip()

    # --- widths and character map ----------------------------------------
    def _lade_breiten(self):
        o = self.tab["hmtx"][0]
        d = self.daten
        n = self.n_hm
        self._breiten = [struct.unpack(">H", d[o + 4 * i:o + 4 * i + 2])[0] for i in range(n)]

    def gid_breite(self, gid):
        """Advance width of a glyph in 1/1000 em."""
        if self._breiten is None:
            self._lade_breiten()
        if not self._breiten:
            return 500
        w = self._breiten[gid] if gid < len(self._breiten) else self._breiten[-1]
        return w * 1000.0 / self.upem

    def _lade_cmap(self):
        self._cmap = {}
        if "cmap" not in self.tab:
            return
        o, _ln = self.tab["cmap"]
        d = self.daten
        anz = struct.unpack(">H", d[o + 2:o + 4])[0]
        kand = []
        for i in range(anz):
            pid, eid, off = struct.unpack(">HHI", d[o + 4 + 8 * i:o + 12 + 8 * i])
            fmt = struct.unpack(">H", d[o + off:o + off + 2])[0]
            rang = 0
            if pid == 3 and eid == 10 and fmt == 12:
                rang = 4
            elif pid == 0 and fmt == 12:
                rang = 3
            elif pid == 3 and eid == 1 and fmt == 4:
                rang = 2
            elif pid == 0 and fmt == 4:
                rang = 1
            if rang:
                kand.append((rang, o + off, fmt))
        if not kand:
            return
        kand.sort(reverse=True)
        _r, p, fmt = kand[0]
        if fmt == 12:
            ng = struct.unpack(">I", d[p + 12:p + 16])[0]
            for g in range(ng):
                s, e, gid = struct.unpack(">III", d[p + 16 + 12 * g:p + 28 + 12 * g])
                if e - s > 70000:
                    continue
                for c in range(s, e + 1):
                    self._cmap[c] = gid + (c - s)
        else:
            segx2 = struct.unpack(">H", d[p + 6:p + 8])[0]
            sn = segx2 // 2
            endp = p + 14
            startp = endp + segx2 + 2
            deltap = startp + segx2
            rangep = deltap + segx2
            for k in range(sn):
                e = struct.unpack(">H", d[endp + 2 * k:endp + 2 * k + 2])[0]
                s = struct.unpack(">H", d[startp + 2 * k:startp + 2 * k + 2])[0]
                dl = struct.unpack(">h", d[deltap + 2 * k:deltap + 2 * k + 2])[0]
                ro = struct.unpack(">H", d[rangep + 2 * k:rangep + 2 * k + 2])[0]
                for c in range(s, e + 1):
                    if c == 0xFFFF:
                        continue
                    if ro == 0:
                        gid = (c + dl) & 0xFFFF
                    else:
                        a = rangep + 2 * k + ro + 2 * (c - s)
                        if a + 2 > len(d):
                            continue
                        gid = struct.unpack(">H", d[a:a + 2])[0]
                        if gid:
                            gid = (gid + dl) & 0xFFFF
                    if gid:
                        self._cmap[c] = gid

    def gid(self, ch):
        if self._cmap is None:
            self._lade_cmap()
        return self._cmap.get(ord(ch), 0)

    def breite(self, ch):
        return self.gid_breite(self.gid(ch))

    def text_breite(self, s):
        """Width of a string in 1/1000 em."""
        return sum(self.breite(c) for c in s)

    def einbettbar(self):
        """TrueType outlines, licence allows embedding, not huge."""
        return (not self.cff and "glyf" in self.tab and not (self.fs_type & 0x0002)
                and len(self.daten) <= MAX_EINBETTEN)


def _datei_laden(pfad):
    if pfad in _geladen:
        return _geladen[pfad]
    try:
        with open(pfad, "rb") as f:
            t = TTF(f.read())
    except (OSError, ValueError, struct.error):
        t = None
    _geladen[pfad] = t
    return t


def _kopf_lesen(pfad):
    """Reads only the name table of a font file -> (family, style, cff) or None."""
    try:
        with open(pfad, "rb") as f:
            kopf = f.read(12)
            if kopf[:4] not in (b"\x00\x01\x00\x00", b"true", b"OTTO"):
                return None
            n = struct.unpack(">H", kopf[4:6])[0]
            tabs = f.read(16 * n)
            tab = {}
            for i in range(n):
                t, _cs, off, ln = struct.unpack(">4sIII", tabs[16 * i:16 * i + 16])
                tab[t.decode("latin-1")] = (off, ln)
            if "name" not in tab or "hmtx" not in tab:
                return None
            f.seek(tab["name"][0])
            nd = f.read(min(tab["name"][1], 65536))
    except (OSError, struct.error, UnicodeDecodeError):
        return None
    try:
        anz, so = struct.unpack(">HH", nd[2:6])
        out = {}
        for i in range(anz):
            pid, eid, lid, nid, ln, off = struct.unpack(">6H", nd[6 + 12 * i:18 + 12 * i])
            if nid not in (1, 2, 16, 17):
                continue
            roh = nd[so + off:so + off + ln]
            if pid in (0, 3):
                text = roh.decode("utf-16-be")
            elif pid == 1 and eid == 0:
                text = roh.decode("mac_roman")
            else:
                continue
            if nid not in out or (pid == 3 and lid == 0x409):
                out[nid] = text
    except (struct.error, UnicodeDecodeError):
        return None
    fam = (out.get(1) or out.get(16) or "").strip()
    stil = (out.get(2) or out.get(17) or "").strip()
    if not fam:
        return None
    return fam, stil, ("glyf" not in tab)


def scan(ordner=None):
    """Searches the font directories.
    -> {family: {"regular": path|None, "bold": path|None, "cff": bool}}"""
    erg = {}
    for wurzel in (ordner if ordner is not None else schrift_ordner()):
        if not os.path.isdir(wurzel):
            continue
        for pfad, _dirs, dateien in os.walk(wurzel):
            for fn in dateien:
                if not fn.lower().endswith((".ttf", ".otf")):
                    continue
                voll = os.path.join(pfad, fn)
                k = _kopf_lesen(voll)
                if not k:
                    continue
                fam, stil, cff = k
                s = stil.lower()
                if "italic" in s or "oblique" in s:
                    continue
                if s in ("regular", "normal", "book", ""):
                    slot = "regular"
                elif s == "bold":
                    slot = "bold"
                else:
                    continue                      # other styles are separate families
                e = erg.setdefault(fam, {"regular": None, "bold": None, "cff": cff})
                if e[slot] is None:
                    e[slot] = voll
                e["cff"] = e["cff"] and cff
    return erg


# ------------------------------------------------------------------
# active fonts
# ------------------------------------------------------------------
def aktiviere(namen, gefunden=None):
    """Makes the fonts `namen` known (looks them up on the disk if needed).
    -> list of the names that were found."""
    global _aktiv
    namen = [n for n in namen if n and n not in STANDARD_SCHRIFTEN]
    if not namen:
        _aktiv = {}
        return []
    if gefunden is None:
        gefunden = scan()
    _aktiv = {n: gefunden[n] for n in namen if n in gefunden}
    return [n for n in namen if n in _aktiv]


def aktive_namen():
    return sorted(_aktiv, key=str.lower)


def ist_zusatz(name):
    return name in _aktiv


def _ttf(name, fett):
    e = _aktiv.get(name)
    if not e:
        return None
    pfad = (e["bold"] if fett and e["bold"] else None) or e["regular"] or e["bold"]
    return _datei_laden(pfad) if pfad else None


def breite(name, fett=False):
    """Function s -> width in 1/1000 em for an active extra font, else None."""
    t = _ttf(name, fett)
    return t.text_breite if t else None


def pdf_ttf(name, fett=False):
    """TTF object if the font can be embedded into the PDF, else None."""
    t = _ttf(name, fett)
    return t if (t and t.einbettbar()) else None


# ------------------------------------------------------------------
# PDF objects
# ------------------------------------------------------------------
def _hex16(n):
    return "%04X" % n


def pdf_objekte(ttf, basis, gids, nr):
    """PDF objects of an embedded font (Type0 / Identity-H).
    ttf: TTF, basis: name for BaseFont, gids: {gid: unicode char}, nr: first free object
    number. -> (list of object bodies; the first one is the Type0 font, nr..nr+4)"""
    import zlib
    sicher = "".join(c if c.isalnum() else "-" for c in basis) or "Font"
    skala = 1000.0 / ttf.upem
    bb = [int(round(v * skala)) for v in ttf.bbox]
    flags = 4 | (64 if ttf.italic else 0)
    w = " ".join("%d [%d]" % (g, round(ttf.gid_breite(g))) for g in sorted(gids))
    daten = zlib.compress(ttf.daten)
    bf = ["/CIDInit /ProcSet findresource begin 12 dict begin begincmap",
          "/CMapName /Adobe-Identity-UCS def /CMapType 2 def",
          "1 begincodespacerange <0000> <FFFF> endcodespacerange"]
    items = sorted(gids.items())
    for i in range(0, len(items), 100):
        teil = items[i:i + 100]
        bf.append("%d beginbfchar" % len(teil))
        for g, ch in teil:
            u = ord(ch)
            if u > 0xFFFF:
                u -= 0x10000
                hx = "%04X%04X" % (0xD800 + (u >> 10), 0xDC00 + (u & 0x3FF))
            else:
                hx = "%04X" % u
            bf.append("<%s> <%s>" % (_hex16(g), hx))
        bf.append("endbfchar")
    bf.append("endcmap CMapName currentdict /CMap defineresource pop end end")
    tounicode = zlib.compress("\n".join(bf).encode("ascii"))
    obj = [
        ("<< /Type /Font /Subtype /Type0 /BaseFont /%s /Encoding /Identity-H "
         "/DescendantFonts [%d 0 R] /ToUnicode %d 0 R >>" % (sicher, nr + 1, nr + 4)).encode("latin-1"),
        ("<< /Type /Font /Subtype /CIDFontType2 /BaseFont /%s /CIDSystemInfo "
         "<< /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> /FontDescriptor %d 0 R "
         "/CIDToGIDMap /Identity /DW 500 /W [%s] >>" % (sicher, nr + 2, w)).encode("latin-1"),
        ("<< /Type /FontDescriptor /FontName /%s /Flags %d /FontBBox [%d %d %d %d] "
         "/ItalicAngle %.2f /Ascent %d /Descent %d /CapHeight %d /StemV 80 "
         "/FontFile2 %d 0 R >>" % (sicher, flags, bb[0], bb[1], bb[2], bb[3], ttf.italic,
                                   round(ttf.ascent * skala), round(ttf.descent * skala),
                                   round((ttf.cap or ttf.ascent * 0.7) * skala), nr + 3)
         ).encode("latin-1"),
        (b"<< /Length %d /Length1 %d /Filter /FlateDecode >>\nstream\n"
         % (len(daten), len(ttf.daten))) + daten + b"\nendstream",
        (b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(tounicode))
        + tounicode + b"\nendstream",
    ]
    return obj
