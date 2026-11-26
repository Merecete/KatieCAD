# -*- coding: utf-8 -*-
"""
katiecad/ui/kt/dlgmod.py - filedialog, colorchooser, messagebox and simpledialog for the
Kivy layer (BSD-3-Clause).

File and colour dialogs stay the native ones of the system: they are opened through the
real tkinter (an invisible Tk root), exactly the dialogs the Tk version showed. The Kivy
window simply waits meanwhile, as it did under Tk. simpledialog is rebuilt with the layer's
own widgets, looking like Tk's plain dialog.
"""

import sys
import types

from katiecad.ui.kt import tkmod as T

ECHT = {}          # the real tkinter modules (filled by kt.installieren)
_echte_wurzel = [None]


def _wurzel():
    """The invisible root window of the real tkinter for the native dialogs (created once, hidden,
    always on top, with the KatieCAD icon).
    """
    r = _echte_wurzel[0]
    tk = ECHT["tkinter"]
    if r is None:
        r = tk.Tk()
        r.withdraw()
        try:                                  # KatieCAD symbol instead of the Tk feather
            from katiecad.ui.app import _symbol_datei
            ico = _symbol_datei("KatieCAD.ico")
            if ico and sys.platform.startswith("win"):
                r.iconbitmap(default=ico)
        except Exception:
            pass
        try:
            r.attributes("-topmost", True)
        except Exception:
            pass
        _echte_wurzel[0] = r
    return r


def _nativ(modul, funktion, kw):
    """Opens a native dialog of the real tkinter (e.g. filedialog.askopenfilename) and returns its
    result. The button release that closed the native dialog never reaches the Kivy window, so
    the pressed buttons and the mouse target of the layer are cleared afterwards.
    """
    kw.pop("parent", None)
    r = _wurzel()
    try:
        r.lift()
        erg = getattr(ECHT[modul], funktion)(parent=r, **kw)
    finally:
        try:
            r.update()
        except Exception:
            pass
    root = T._base.ROOT[0]
    if root is not None:
        root._kt_knoepfe.clear()           # the button release went to the native dialog
        root._kt_maus_ziel = None
    return erg


def _modul(name, **funktionen):
    m = types.ModuleType(name)
    for k, v in funktionen.items():
        setattr(m, k, v)
    return m


# ------------------------------------------------------------ macOS: system dialogs without Tk
# Tk 9 cannot be started inside the SDL / Kivy process on the Mac (it asks the application object
# for macOSVersion, which SDLApplication does not have -> the whole program is terminated). So the
# file and colour dialogs are the system ones, opened through osascript (a separate process).
def _as_text(t):
    return '"' + str(t).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _mac_endungen(filetypes):
    """File name extensions of the Tk filetypes list (wildcard-only entries are ignored)."""
    liste = []
    try:
        for eintrag in filetypes or []:
            muster = eintrag[1]
            muster = muster.split() if isinstance(muster, str) else list(muster)
            for m in muster:
                m = str(m).strip()
                if m.startswith("*.") and len(m) > 2 and not any(c in m[2:] for c in "*?[]"):
                    e = m[2:].lower().lstrip(".")
                    if e and e not in liste:
                        liste.append(e)
    except (TypeError, IndexError):
        return []
    return liste


def _osascript(zeilen):
    """Runs an AppleScript; returns the text it prints, or None when cancelled or on error."""
    import subprocess
    try:
        r = subprocess.run(["osascript", "-e", "tell current application to activate"]
                           + [x for z in zeilen for x in ("-e", z)],
                           capture_output=True, text=True, timeout=None)
    except (OSError, ValueError):
        return None
    if r.returncode != 0:
        return None                      # cancelled (error -128) or not possible
    return r.stdout.rstrip("\n")


def _mac_dateidialog(funktion, kw):
    import os
    titel = kw.get("title")
    prompt = (" with prompt " + _as_text(titel)) if titel else ""
    ordner = kw.get("initialdir")
    ort = ""
    if ordner and os.path.isdir(str(ordner)):
        ort = " default location (POSIX file %s)" % _as_text(os.path.abspath(str(ordner)))
    if funktion in ("askopenfilename", "askopenfilenames", "askopenfile", "askopenfiles"):
        endungen = _mac_endungen(kw.get("filetypes"))
        typen = (" of type {%s}" % ", ".join(_as_text(e) for e in endungen)) if endungen else ""
        mehrere = funktion in ("askopenfilenames", "askopenfiles")
        if mehrere:
            z = ["set r to choose file%s%s%s with multiple selections allowed" % (prompt, typen, ort),
                 "set o to \"\"", "repeat with f in r", "set o to o & POSIX path of f & linefeed",
                 "end repeat", "o"]
        else:
            z = ["POSIX path of (choose file%s%s%s)" % (prompt, typen, ort)]
        erg = _osascript(z)
        if mehrere:
            return tuple(x for x in (erg or "").split("\n") if x)
        return erg or ""
    if funktion == "askdirectory":
        return _osascript(["POSIX path of (choose folder%s%s)" % (prompt, ort)]) or ""
    # asksaveasfilename
    name = kw.get("initialfile") or ""
    vorgabe = (" default name " + _as_text(name)) if name else ""
    erg = _osascript(["POSIX path of (choose file name%s%s%s)" % (prompt, vorgabe, ort)]) or ""
    ende = kw.get("defaultextension") or ""
    if erg and ende and not os.path.splitext(erg)[1]:
        erg += ende if ende.startswith(".") else "." + ende
    return erg


def _mac_farbe(kw):
    start = kw.get("initialcolor") or "#808080"
    try:
        h = str(start).lstrip("#")
        rgb = [int(h[i:i + 2], 16) * 257 for i in (0, 2, 4)]
    except (ValueError, IndexError):
        rgb = [32896, 32896, 32896]
    erg = _osascript(["choose color default color {%d, %d, %d}" % tuple(rgb)])
    try:
        r, g, b = [max(0, min(255, round(int(x) / 257))) for x in erg.replace(",", " ").split()]
    except (AttributeError, ValueError):
        return (None, None)
    return ((r, g, b), "#%02x%02x%02x" % (r, g, b))


def _mac_aufraeumen():
    root = T._base.ROOT[0]
    if root is not None:
        root._kt_knoepfe.clear()
        root._kt_maus_ziel = None


# ------------------------------------------------------------ filedialog
def _fd(funktion):
    def f(**kw):
        if sys.platform == "darwin":
            kw.pop("parent", None)
            try:
                return _mac_dateidialog(funktion, kw)
            finally:
                _mac_aufraeumen()
        erg = _nativ("tkinter.filedialog", funktion, kw)
        return erg
    f.__name__ = funktion
    return f


filedialog = _modul(
    "tkinter.filedialog",
    askopenfilename=_fd("askopenfilename"), askopenfilenames=_fd("askopenfilenames"),
    asksaveasfilename=_fd("asksaveasfilename"), askdirectory=_fd("askdirectory"),
    askopenfile=_fd("askopenfile"), asksaveasfile=_fd("asksaveasfile"),
    askopenfiles=_fd("askopenfiles"))


# ------------------------------------------------------------ colorchooser
def askcolor(color=None, **kw):
    if color is not None:
        kw["initialcolor"] = color
    if sys.platform == "darwin":
        try:
            return _mac_farbe(kw)
        finally:
            _mac_aufraeumen()
    return _nativ("tkinter.colorchooser", "askcolor", kw)


colorchooser = _modul("tkinter.colorchooser", askcolor=askcolor, Chooser=None)


# ------------------------------------------------------------ messagebox (native look of Tk)
def _mb(funktion):
    def f(title=None, message=None, **kw):
        if title is not None:
            kw["title"] = title
        if message is not None:
            kw["message"] = message
        return _nativ("tkinter.messagebox", funktion, kw)
    f.__name__ = funktion
    return f


messagebox = _modul(
    "tkinter.messagebox",
    showinfo=_mb("showinfo"), showwarning=_mb("showwarning"), showerror=_mb("showerror"),
    askquestion=_mb("askquestion"), askokcancel=_mb("askokcancel"), askyesno=_mb("askyesno"),
    askyesnocancel=_mb("askyesnocancel"), askretrycancel=_mb("askretrycancel"),
    INFO="info", WARNING="warning", ERROR="error", QUESTION="question", OK="ok",
    CANCEL="cancel", YES="yes", NO="no", ABORT="abort", RETRY="retry", IGNORE="ignore",
    OKCANCEL="okcancel", YESNO="yesno", YESNOCANCEL="yesnocancel", RETRYCANCEL="retrycancel")


# ------------------------------------------------------------ simpledialog
class _Abfrage:
    """Like tkinter.simpledialog: Label, Entry, OK / Cancel (plain Tk look)."""

    def __init__(self, title, prompt, initialvalue=None, parent=None, umwandeln=str,
                 minvalue=None, maxvalue=None, fehlertext=""):
        self.ergebnis = None
        root = T._base.ROOT[0]
        eltern = parent.winfo_toplevel() if parent is not None else root
        dlg = T.Toplevel(eltern)
        dlg.title(title or "")
        dlg.resizable(False, False)
        T.Label(dlg, text=prompt, justify=T.LEFT).grid(row=0, padx=5, sticky=T.W)
        e = T.Entry(dlg, name="entry")
        e.grid(row=1, padx=5, sticky=T.W + T.E)
        if initialvalue is not None:
            e.insert(0, str(initialvalue))
            e.select_range(0, T.END)
        box = T.Frame(dlg)
        self._dlg, self._kt_e = dlg, e

        def ok(_ev=None):
            """OK / Return in the input dialog: converts and checks the value (type, minimum,
            maximum like Tk's simpledialog); on an error the message is shown and the dialog
            stays open.
            """
            s = e.get()
            try:
                wert = umwandeln(s)
            except ValueError:
                fehler(fehlertext or "Not a valid value.")
                return "break"
            if minvalue is not None and wert < minvalue:
                fehler(f"The allowed minimum value is {minvalue}. Please try again.")
                return "break"
            if maxvalue is not None and wert > maxvalue:
                fehler(f"The allowed maximum value is {maxvalue}. Please try again.")
                return "break"
            self.ergebnis = wert
            schliessen()
            return "break"

        def abbruch(_ev=None):
            schliessen()
            return "break"

        def fehler(text):
            messagebox.showwarning("Illegal value", text + "\nPlease try again")
            e.focus_set()

        def schliessen():
            dlg.grab_release()
            dlg.destroy()

        T.Button(box, text="OK", width=10, command=ok, default=T.ACTIVE).pack(side=T.LEFT, padx=5, pady=5)
        T.Button(box, text="Cancel", width=10, command=abbruch).pack(side=T.LEFT, padx=5, pady=5)
        box.grid(row=2)
        dlg.bind("<Return>", ok)
        dlg.bind("<KP_Enter>", ok)
        dlg.bind("<Escape>", abbruch)
        dlg.protocol("WM_DELETE_WINDOW", abbruch)
        dlg.update_idletasks()
        if eltern is not None and eltern is not root:
            x = eltern.winfo_rootx() + 50
            y = eltern.winfo_rooty() + 50
            dlg.geometry(f"+{x}+{y}")
        e.focus_set()
        dlg.grab_set()
        dlg.wait_window()


def askstring(title, prompt, **kw):
    return _Abfrage(title, prompt, kw.get("initialvalue"), kw.get("parent")).ergebnis


def askinteger(title, prompt, **kw):
    return _Abfrage(title, prompt, kw.get("initialvalue"), kw.get("parent"), int,
                    kw.get("minvalue"), kw.get("maxvalue"), "Not an integer.").ergebnis


def askfloat(title, prompt, **kw):
    return _Abfrage(title, prompt, kw.get("initialvalue"), kw.get("parent"), float,
                    kw.get("minvalue"), kw.get("maxvalue"), "Not a floating-point value.").ergebnis


class Dialog:
    def __init__(self, parent, title=None):
        pass


simpledialog = _modul("tkinter.simpledialog", askstring=askstring, askinteger=askinteger,
                      askfloat=askfloat, Dialog=Dialog)
