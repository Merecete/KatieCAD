# -*- coding: utf-8 -*-
"""
katiecad/common/fenster.py - working with several KatieCAD windows (BSD-3-Clause).

Every KatieCAD window is a process of its own. What they share:

* the clipboard: copying writes the copied objects to <config folder>/zwischenablage.json
  as well; pasting takes the newest copy, no matter which window made it;
* sheet locks: a project sheet that is open in one window gets "<sheet file>.lock" with the
  process id; another window does not open it (a lock of a process that no longer runs
  is ignored - e.g. after a crash);
* "new window": starts KatieCAD again (optionally with a file / a project sheet).
"""

import json
import os
import subprocess
import sys
import time

DATEI = "zwischenablage.json"


# ------------------------------------------------------------ clipboard
def zwischenablage_schreiben(ordner, elemente, basis=None, mit_basis=False):
    """Writes the copied objects (dicts) atomically; -> time stamp of the copy."""
    zeit = time.time()
    daten = {"format": "katiecad-zwischenablage", "zeit": zeit, "pid": os.getpid(),
             "elemente": elemente, "basis": list(basis) if basis else None,
             "mit_basis": bool(mit_basis)}
    try:
        os.makedirs(ordner, exist_ok=True)
        ziel = os.path.join(ordner, DATEI)
        tmp = ziel + f".{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False)
        os.replace(tmp, ziel)
    except (OSError, TypeError, ValueError):
        pass
    return zeit


def zwischenablage_lesen(ordner):
    """-> dict (zeit, pid, elemente, basis, mit_basis) or None."""
    try:
        with open(os.path.join(ordner, DATEI), "r", encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict) or d.get("format") != "katiecad-zwischenablage" \
            or not isinstance(d.get("elemente"), list):
        return None
    return d


# ------------------------------------------------------------ sheet locks
def _lebt(pid):
    """True if the process `pid` still runs (a lock file of a crashed window must not block a sheet
    for ever). Windows: OpenProcess + exit code STILL_ACTIVE; elsewhere signal 0.
    """
    if pid == os.getpid():
        return True
    if pid <= 0:
        return False
    if sys.platform.startswith("win"):
        try:
            import ctypes
            k = ctypes.windll.kernel32
            h = k.OpenProcess(0x1000, False, pid)           # QUERY_LIMITED_INFORMATION
            if not h:
                return False
            code = ctypes.c_ulong()
            ok = k.GetExitCodeProcess(h, ctypes.byref(code))
            k.CloseHandle(h)
            return bool(ok) and code.value == 259           # STILL_ACTIVE
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False


def gesperrt_von(pfad):
    """Process id of ANOTHER running window that has the sheet open, else None."""
    try:
        with open(pfad + ".lock", "r", encoding="utf-8") as f:
            pid = int(f.read().strip() or 0)
    except (OSError, ValueError):
        return None
    if pid == os.getpid() or not _lebt(pid):
        return None
    return pid


def sperren(pfad):
    try:
        with open(pfad + ".lock", "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass


def freigeben(pfad):
    """Removes the lock - only our own."""
    if not pfad:
        return
    try:
        with open(pfad + ".lock", "r", encoding="utf-8") as f:
            pid = int(f.read().strip() or 0)
        if pid == os.getpid():
            os.remove(pfad + ".lock")
    except (OSError, ValueError):
        pass


# ------------------------------------------------------------ new window
def neues_fenster(*argumente):
    """Starts another KatieCAD window (same program, same interface)."""
    if getattr(sys, "frozen", False):
        befehl = [sys.executable]
        ordner = os.path.dirname(sys.executable)
    else:
        befehl = [sys.executable, "-m", "katiecad"]
        ordner = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    befehl += [str(a) for a in argumente]
    kw = {}
    if sys.platform.startswith("win"):
        kw["creationflags"] = 0x00000008 | 0x00000200        # DETACHED | NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    try:
        subprocess.Popen(befehl, cwd=ordner, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         close_fds=True, **kw)
        return True
    except OSError:
        return False
