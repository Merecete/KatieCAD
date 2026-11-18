# -*- coding: utf-8 -*-
"""
katiecad/fileio/sicherung.py - Backup files and automatic saving (NO Tkinter, BSD-3-Clause).

* .bak: before a file is overwritten, the previous version is copied to "<file>.bak"
  (like AutoCAD); one generation, the next save replaces it.
* Autosave: the open drawing is written from time to time into the program's
  own folder "<config folder>/autosave" - never over the original. A clean save or a
  normal exit removes it again; what is left over after a crash is offered at the next start.
"""
import json
import os
import shutil
import sys
import time

BAK_ENDUNG = ".bak"
STANDARD_MINUTEN = 10
MAX_MINUTEN = 120
_PRAEFIX = "autosave_"
_ENDUNG = ".json"
MAX_GROESSE = 512 * 1024 * 1024         # larger autosave files are not loaded


def bak_pfad(pfad):
    return pfad + BAK_ENDUNG


def bak_anlegen(pfad):
    """Copies an existing regular file to '<file>.bak' (replaces an older one).
    -> True if a copy was made. Never raises: a failing backup must not prevent saving."""
    try:
        if os.path.islink(pfad) or not os.path.isfile(pfad):
            return False
        ziel = bak_pfad(pfad)
        tmp = ziel + ".tmp"
        shutil.copy2(pfad, tmp)
        os.replace(tmp, ziel)
        return True
    except OSError as e:
        print(f"[KatieCAD] Sicherungsdatei konnte nicht angelegt werden: {e}")
        return False


def minuten_pruefen(wert, standard=STANDARD_MINUTEN):
    """Interval from the configuration: 0 = off, otherwise 1..MAX_MINUTEN."""
    try:
        m = int(wert)
    except (TypeError, ValueError):
        return standard
    return max(0, min(MAX_MINUTEN, m))


def ordner(konfig_ordner):
    return os.path.join(konfig_ordner, "autosave")


def _pfad(konfig_ordner, pid):
    return os.path.join(ordner(konfig_ordner), "%s%d%s" % (_PRAEFIX, int(pid), _ENDUNG))


def schreiben(konfig_ordner, pid, daten, quelle=None):
    """Writes the autosave of process `pid` atomically. `quelle` = file the drawing comes
    from (or None). -> path, or None on error."""
    pfad = _pfad(konfig_ordner, pid)
    try:
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
        tmp = pfad + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"format": "katiecad-autosave", "zeit": time.time(),
                       "quelle": quelle, "daten": daten}, f, ensure_ascii=False)
        os.replace(tmp, pfad)
        return pfad
    except (OSError, TypeError, ValueError) as e:
        print(f"[KatieCAD] Autospeichern fehlgeschlagen: {e}")
        return None


def loeschen(konfig_ordner, pid):
    try:
        os.remove(_pfad(konfig_ordner, pid))
    except OSError:
        pass


def _prozess_lebt(pid):
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    try:
        if sys.platform.startswith("win"):
            import ctypes
            k32 = ctypes.windll.kernel32
            h = k32.OpenProcess(0x1000, False, pid)      # QUERY_LIMITED_INFORMATION
            if not h:
                return False
            k32.CloseHandle(h)
            return True
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except (OSError, ValueError, AttributeError):
        return False


def beiseite_legen(pfad):
    """Renames a defective autosave to '*.defekt' (kept for a manual look, no longer offered)."""
    try:
        os.replace(pfad, pfad + ".defekt")
    except OSError:
        datei_entfernen(pfad)


def verwaiste(konfig_ordner, eigene_pid=None, maximal=None):
    """Autosave files of processes that no longer exist (crash), newest first:
    [(path, time, source, data)]. Broken or oversized files are skipped."""
    eigene_pid = os.getpid() if eigene_pid is None else eigene_pid
    erg = []
    try:
        namen = os.listdir(ordner(konfig_ordner))
    except OSError:
        return erg

    def _mtime(n):
        try:
            return os.path.getmtime(os.path.join(ordner(konfig_ordner), n))
        except OSError:
            return 0.0
    namen.sort(key=_mtime, reverse=True)            # newest first: only these are parsed
    for n in namen:
        if maximal is not None and len(erg) >= maximal:
            break
        if not (n.startswith(_PRAEFIX) and n.endswith(_ENDUNG)):
            continue
        try:
            pid = int(n[len(_PRAEFIX):-len(_ENDUNG)])
        except ValueError:
            continue
        if pid == eigene_pid or _prozess_lebt(pid):
            continue
        pfad = os.path.join(ordner(konfig_ordner), n)
        try:
            if os.path.getsize(pfad) > MAX_GROESSE:
                continue
            with open(pfad, "r", encoding="utf-8") as f:
                d = json.load(f)
            if (not isinstance(d, dict) or d.get("format") != "katiecad-autosave"
                    or not isinstance(d.get("daten"), dict)):
                continue
            erg.append((pfad, float(d.get("zeit") or 0), d.get("quelle"), d["daten"]))
        except (OSError, ValueError):
            continue
    erg.sort(key=lambda x: x[1], reverse=True)
    return erg


def datei_entfernen(pfad):
    try:
        os.remove(pfad)
    except OSError:
        pass
