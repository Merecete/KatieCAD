# -*- coding: utf-8 -*-
"""
katiecad/ui/kt/tkmod.py - the "tkinter" module of the Kivy layer (BSD-3-Clause).

Every widget is a Python object with Tk's API (options, pack/grid, bind, after ...) and
draws itself into one Kivy widget. Kivy only provides the window, the clock, the input and
the OpenGL drawing; layout, event dispatch and focus follow Tk's rules, so the program
logic above it stays unchanged.

All Toplevels live inside the one Kivy window (Kivy has a single window per process); a
normal Toplevel gets a title bar that can be dragged, overrideredirect ones (pop-ups,
tool tips) have none.
"""

import sys
import time
import math

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget as _KWidget
from kivy.uix.stencilview import StencilView as _KStencil
from kivy.graphics import (Color, Rectangle, Line, InstructionGroup, PushMatrix, PopMatrix,
                           Translate, Scale)
from kivy.base import EventLoop
from kivy.core.clipboard import Clipboard

from katiecad.ui.kt import _base, events as EV, fontmod
from katiecad.ui.kt.geometry import (GeometrieMixin, pack_req, pack_anordnen, grid_req,
                                     grid_anordnen, place_anordnen)

TkVersion = 8.6
TclVersion = 8.6
wantobjects = 1

# ------------------------------------------------------------ constants
N, S, W, E = "n", "s", "w", "e"
NW, SW, NE, SE = "nw", "sw", "ne", "se"
NS, EW, NSEW = "ns", "ew", "nsew"
CENTER = "center"
NONE, X, Y, BOTH = "none", "x", "y", "both"
LEFT, TOP, RIGHT, BOTTOM = "left", "top", "right", "bottom"
RAISED, SUNKEN, FLAT, RIDGE, GROOVE, SOLID = "raised", "sunken", "flat", "ridge", "groove", "solid"
HORIZONTAL, VERTICAL = "horizontal", "vertical"
NUMERIC = "numeric"
CHAR, WORD = "char", "word"
BASELINE = "baseline"
INSIDE, OUTSIDE = "inside", "outside"
SEL, SEL_FIRST, SEL_LAST = "sel", "sel.first", "sel.last"
END, INSERT, CURRENT, ANCHOR, ALL = "end", "insert", "current", "anchor", "all"
NORMAL, DISABLED, ACTIVE, HIDDEN = "normal", "disabled", "active", "hidden"
CASCADE, CHECKBUTTON, COMMAND, RADIOBUTTON, SEPARATOR = (
    "cascade", "checkbutton", "command", "radiobutton", "separator")
SINGLE, BROWSE, MULTIPLE, EXTENDED = "single", "browse", "multiple", "extended"
DOTBOX, UNDERLINE = "dotbox", "underline"
PIESLICE, CHORD, ARC = "pieslice", "chord", "arc"
FIRST, LAST = "first", "last"
BUTT, PROJECTING, ROUND = "butt", "projecting", "round"
BEVEL, MITER = "bevel", "miter"
MOVETO, SCROLL, UNITS, PAGES = "moveto", "scroll", "units", "pages"
YES, NO, TRUE, FALSE = 1, 0, 1, 0
READABLE, WRITABLE, EXCEPTION = 2, 4, 8


class TclError(Exception):
    pass


class EventType(str):
    pass


Event = EV.Event

# ============================================================
# Variables
# ============================================================
_VARS = {}
_var_zaehler = [0]


class Variable:
    _kt_default = ""

    def __init__(self, master=None, value=None, name=None):
        _var_zaehler[0] += 1
        self._name = name or f"PY_VAR{_var_zaehler[0]}"
        self._kt_wert = self._kt_default if value is None else value
        self._kt_traces = []            # [(modes, callback, name)]
        self._kt_lese_traces = False
        self._kt_beobachter = []        # widgets showing the value
        _VARS[self._name] = self

    def __str__(self):
        return self._name

    def __eq__(self, other):
        return isinstance(other, Variable) and other._name == self._name

    def __hash__(self):
        return hash(self._name)

    def set(self, value):
        self._kt_wert = value
        for w in list(self._kt_beobachter):
            try:
                w._kt_variable_geaendert(self)
            except Exception:
                pass
        for modes, cb, _n in list(self._kt_traces):
            if "write" in modes or "w" in modes:
                cb(self._name, "", "write")

    initialize = set

    def _kt_roh(self):
        return self._kt_wert

    def get(self):
        if self._kt_lese_traces:
            for modes, cb, _n in list(self._kt_traces):
                if "read" in modes or "r" in modes:
                    cb(self._name, "", "read")
        return self._kt_wert

    def trace_add(self, mode, callback):
        modes = (mode,) if isinstance(mode, str) else tuple(mode)
        _var_zaehler[0] += 1
        name = f"trace{_var_zaehler[0]}"
        self._kt_traces.append((modes, callback, name))
        self._kt_lese_traces = any("read" in m or "r" in m for m, _c, _n in self._kt_traces)
        return name

    def trace_remove(self, mode, cbname):
        self._kt_traces = [t for t in self._kt_traces if t[2] != cbname]
        self._kt_lese_traces = any("read" in m or "r" in m for m, _c, _n in self._kt_traces)

    def trace_info(self):
        return [(t[0], t[2]) for t in self._kt_traces]

    def trace_variable(self, mode, callback):
        m = {"w": "write", "r": "read", "u": "unset"}.get(mode, mode)
        return self.trace_add(m, lambda *a: callback(*a))

    trace = trace_variable

    def trace_vdelete(self, mode, cbname):
        self.trace_remove(mode, cbname)

    def _kt_beobachten(self, w):
        if w not in self._kt_beobachter:
            self._kt_beobachter.append(w)

    def _kt_vergessen(self, w):
        if w in self._kt_beobachter:
            self._kt_beobachter.remove(w)


class StringVar(Variable):
    _kt_default = ""

    def get(self):
        if self._kt_lese_traces:
            Variable.get(self)
        v = self._kt_wert
        return v if type(v) is str else str(v)


class IntVar(Variable):
    _kt_default = 0

    def get(self):
        v = super().get()
        if isinstance(v, bool):
            return int(v)
        if isinstance(v, int):
            return v
        try:
            return int(str(v).strip())
        except ValueError:
            try:
                return int(float(str(v).strip()))
            except ValueError:
                raise TclError(f'expected integer but got "{v}"')


class DoubleVar(Variable):
    _kt_default = 0.0

    def get(self):
        v = super().get()
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
        try:
            return float(str(v).strip())
        except ValueError:
            raise TclError(f'expected floating-point number but got "{v}"')


class BooleanVar(Variable):
    _kt_default = False

    def set(self, value):
        super().set(value)

    def get(self):
        v = super().get()
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(v)
        s = str(v).strip().lower()
        if s in ("1", "true", "yes", "on"):
            return True
        if s in ("0", "false", "no", "off", ""):
            return False
        raise TclError(f'expected boolean value but got "{v}"')


def getint(v):
    return int(v)


def getdouble(v):
    return float(v)


def getboolean(v):
    return BooleanVar(value=v).get()


# ============================================================
# Kivy widgets used as drawing surface
# ============================================================
class _Flaeche(_KWidget):
    """Plain Kivy widget; never handles input itself (dispatch is ours)."""

    def on_touch_down(self, t):
        return False

    def on_touch_move(self, t):
        return False

    def on_touch_up(self, t):
        return False


class _ClipFlaeche(_KStencil):
    def on_touch_down(self, t):
        return False

    def on_touch_move(self, t):
        return False

    def on_touch_up(self, t):
        return False


# ============================================================
# Option handling
# ============================================================
_ALIAS = {"bg": "background", "fg": "foreground", "bd": "borderwidth",
          "invcmd": "invalidcommand", "vcmd": "validatecommand"}
# options whose change needs a new layout (the rest only a new drawing)
_GROESSE = {"text", "textvariable", "font", "image", "width", "height", "padx", "pady",
            "borderwidth", "highlightthickness", "padding", "compound", "wraplength",
            "style", "values", "orient", "length", "show", "underline", "relief"}

_pfad_zaehler = {}


def _rgba(farbe, standard=None):
    try:
        f = _base.farbe(farbe)
    except TclError:
        f = None
    return f if f is not None else standard


# ============================================================
# Misc: what every widget (and Tk) has
# ============================================================
class Misc:
    _kt_klasse = "Widget"
    _kt_standard = {}
    _kt_ist_toplevel = False

    # ---------------------------------------------------- creation
    def _kt_anlegen(self, master, cnf, kw):
        if cnf:
            kw = {**cnf, **kw}
        name = kw.pop("name", None)
        self.master = master
        self._kt_root_ = master._kt_root_ if master is not None else self
        self.tk = self._kt_root_._kt_interp if master is not None else None
        self.children = {}
        if name is None:
            basis = "!" + self.__class__.__name__.lower()
            n = _pfad_zaehler.get((id(master), basis), 0) + 1
            _pfad_zaehler[(id(master), basis)] = n
            name = basis if n == 1 else f"{basis}{n}"
        self._name = name
        if master is None:
            self._kt_pfad = "."
        else:
            self._kt_pfad = (master._kt_pfad.rstrip(".") + "." + name) if master._kt_pfad != "." else "." + name
            master.children[name] = self
        self._kt_o = {}
        for k, v in self._kt_standard.items():
            self._kt_o[k] = v
        self._kt_bindungen = {}           # sequence -> [callback]
        self._kt_manager = None
        self._kt_geo_master = None
        self._kt_pinfo = {}
        self._pack_slaves, self._grid_slaves, self._kt_place_slaves = [], [], []
        self._grid_spalten, self._kt_grid_zeilen = {}, {}
        self._kt_propagate = True
        self._kt_x = self._kt_y = 0
        self._kt_w = self._kt_h = 1
        self._kt_lebt = False            # managed by a geometry manager
        self._kt_sichtbar = False        # got a size > 0
        self._kt_zerstoert = False
        self._kt_req_pass = -1
        self._kt_req_wert = (1, 1)
        self._kt_zeichnen_noetig = True
        self._kt_zustand = set()         # "active", "pressed", "focus", "disabled", "selected" ...
        self._kt_cursor = ""
        self._kt_k = self._kt_kivy_flaeche()
        self._kt_g_hinten = InstructionGroup()
        self._kt_g_inhalt = InstructionGroup()
        self._kt_k.canvas.add(self._kt_g_hinten)
        self._kt_k.canvas.add(self._kt_g_inhalt)
        self._kt_eltern_k = None
        self._kt_bindtags = None
        if master is not None:
            self._kt_root_._kt_widgets[self._kt_pfad] = self
        self._kt_konfig(kw, neu=True)

    def _kt_kivy_flaeche(self):
        return _Flaeche(size_hint=(None, None))

    _kt_hover_aktiv = False          # gets the "active" state while the pointer is over it

    # state changes the widget may want to show (hover, focus); default: nothing
    def _kt_hover_aenderung(self):
        pass

    def _kt_fokus_aenderung(self):
        pass

    def _kt_nimmt_fokus(self):
        tf = self._kt_o.get("takefocus")
        return bool(tf) and tf not in ("0", 0)

    def __str__(self):
        return self._kt_pfad

    def __repr__(self):
        return f"<{self.__class__.__module__}.{self.__class__.__name__} object {self._kt_pfad}>"

    @property
    def _kt_w_name(self):
        return self._kt_pfad

    # ---------------------------------------------------- options
    def _kt_konfig(self, kw, neu=False):
        layout = False
        for k, v in kw.items():
            k = _ALIAS.get(k, k)
            alt = self._kt_o.get(k)
            if k in ("textvariable", "variable", "listvariable"):
                if isinstance(alt, Variable):
                    alt._kt_vergessen(self)
                if isinstance(v, str) and v in _VARS:
                    v = _VARS[v]
                if isinstance(v, Variable):
                    v._kt_beobachten(self)
            if k == "cursor":
                self._kt_cursor = v or ""
            if k == "state":
                self._kt_state_option(v)
            self._kt_o[k] = v
            if k in _GROESSE:
                layout = True
        self._kt_option_geaendert(kw)
        if layout and not neu:
            self._kt_layout_planen()
        self._kt_neu_zeichnen()

    def _kt_state_option(self, v):
        if v in (DISABLED, "disabled"):
            self._kt_zustand.add("disabled")
        else:
            self._kt_zustand.discard("disabled")
        if v == "readonly":
            self._kt_zustand.add("readonly")
        elif v in ("normal", NORMAL):
            self._kt_zustand.discard("readonly")

    def _kt_option_geaendert(self, kw):
        pass

    def configure(self, cnf=None, **kw):
        if isinstance(cnf, str):
            k = _ALIAS.get(cnf, cnf)
            v = self._kt_o.get(k, "")
            return (cnf, k, k.capitalize(), self._kt_standard.get(k, ""), v)
        if cnf:
            kw = {**cnf, **kw}
        if not kw:
            return {k: (k, k, k.capitalize(), self._kt_standard.get(k, ""), v) for k, v in self._kt_o.items()}
        self._kt_konfig(kw)

    config = configure

    def cget(self, key):
        k = _ALIAS.get(key, key)
        if k not in self._kt_o and k not in self._kt_standard:
            if k in ("menu",):
                return ""
            raise TclError(f'unknown option "-{key}"')
        v = self._kt_o.get(k, "")
        return "" if v is None else v

    def __getitem__(self, key):
        return self.cget(key)

    def __setitem__(self, key, value):
        self.configure(**{key: value})

    def keys(self):
        return list(self._kt_o)

    def _kt_variable_geaendert(self, var):
        self._kt_layout_planen()
        self._kt_neu_zeichnen()

    # ---------------------------------------------------- tree
    def winfo_children(self):
        return [c for c in self.children.values() if not c._kt_zerstoert]

    def winfo_toplevel(self):
        w = self
        while not w._kt_ist_toplevel:
            w = w.master
        return w

    def _kt_toplevel(self):
        return self.winfo_toplevel()

    def nametowidget(self, name):
        name = str(name)
        if name == ".":
            return self._kt_root_
        try:
            return self._kt_root_._kt_widgets[name]
        except KeyError:
            if not name.startswith("."):
                w = self._kt_root_._kt_widgets.get(self._kt_pfad.rstrip(".") + "." + name)
                if w is not None:
                    return w
            raise KeyError(name)

    _kt_nametowidget = nametowidget

    def winfo_exists(self):
        return 0 if self._kt_zerstoert else 1

    def winfo_class(self):
        return self._kt_klasse

    def winfo_name(self):
        return self._name

    def winfo_parent(self):
        return str(self.master) if self.master is not None else ""

    def winfo_id(self):
        return id(self)

    def _kt_root(self):
        return self._kt_root_

    # ---------------------------------------------------- geometry info
    def winfo_width(self):
        return int(self._kt_w) if self._kt_sichtbar or self._kt_ist_toplevel else 1

    def winfo_height(self):
        return int(self._kt_h) if self._kt_sichtbar or self._kt_ist_toplevel else 1

    def winfo_reqwidth(self):
        self._kt_req_frisch()
        return int(self._kt_req()[0])

    def winfo_reqheight(self):
        self._kt_req_frisch()
        return int(self._kt_req()[1])

    def _kt_req_frisch(self):
        r = self._kt_root_
        if r._kt_layout_offen:
            r._kt_layout_jetzt()

    def winfo_x(self):
        return int(self._kt_x)

    def winfo_y(self):
        return int(self._kt_y)

    def _kt_abs(self):
        """Position in window coordinates (Tk orientation: y downwards)."""
        x = y = 0
        w = self
        while w is not None:
            x += w._kt_x
            y += w._kt_y
            if w._kt_ist_toplevel:
                x, y = x + w._kt_client_dx(), y + w._kt_client_dy()
                break
            x, y = x + w._kt_kind_versatz_x(), y + w._kt_kind_versatz_y()
            w = w.master
        return x, y

    def _kt_kind_versatz_x(self):
        return 0

    def _kt_kind_versatz_y(self):
        return 0

    def winfo_rootx(self):
        return int(self._kt_abs()[0])

    def winfo_rooty(self):
        return int(self._kt_abs()[1])

    def winfo_ismapped(self):
        return 1 if (self._kt_ist_abgebildet()) else 0

    def winfo_viewable(self):
        return self.winfo_ismapped()

    def _kt_ist_abgebildet(self):
        w = self
        while w is not None:
            if w._kt_zerstoert:
                return False
            if w._kt_ist_toplevel:
                return w._kt_sichtbar
            if not (w._kt_lebt and w._kt_sichtbar):
                return False
            w = w.master
        return True

    def winfo_screenwidth(self):
        return int(Window.width)

    def winfo_screenheight(self):
        return int(Window.height)

    def winfo_vrootx(self):
        return 0

    def winfo_vrooty(self):
        return 0

    def winfo_vrootwidth(self):
        return int(Window.width)

    def winfo_vrootheight(self):
        return int(Window.height)

    def winfo_pointerxy(self):
        return self._kt_root_._kt_maus_tk()

    def winfo_pointerx(self):
        return self.winfo_pointerxy()[0]

    def winfo_pointery(self):
        return self.winfo_pointerxy()[1]

    def winfo_containing(self, x, y, displayof=None):
        return self._kt_root_._kt_widget_bei(x, y)

    def winfo_rgb(self, farbe):
        f = _base.farbe(farbe)
        return tuple(int(c * 65535) for c in f[:3])

    def winfo_fpixels(self, v):
        return float(_mass(v))

    def winfo_pixels(self, v):
        return int(round(_mass(v)))

    def winfo_depth(self):
        return 24

    def winfo_screen(self):
        return ":0"

    # ---------------------------------------------------- timing
    def after(self, ms, func=None, *args):
        return self._kt_root_._kt_after(ms, func, args)

    def after_idle(self, func, *args):
        return self._kt_root_._kt_after("idle", func, args)

    def after_cancel(self, ident):
        self._kt_root_._kt_after_cancel(ident)

    def update_idletasks(self):
        self._kt_root_._kt_layout_jetzt()

    def update(self):
        self._kt_root_._kt_layout_jetzt()
        self._kt_root_._kt_ein_schritt()

    def wait_window(self, window=None):
        w = window or self
        r = self._kt_root_
        while not w._kt_zerstoert and not r._kt_ende:
            r._kt_ein_schritt()

    def wait_variable(self, name):
        var = name if isinstance(name, Variable) else _VARS.get(str(name))
        if var is None:
            return
        flag = {"ok": False}
        n = var.trace_add("write", lambda *a: flag.update(ok=True))
        r = self._kt_root_
        while not flag["ok"] and not r._kt_ende:
            r._kt_ein_schritt()
        var.trace_remove("write", n)

    waitvar = wait_variable

    def wait_visibility(self, window=None):
        self.update_idletasks()

    def mainloop(self, n=0):
        self._kt_root_._kt_hauptschleife()

    def quit(self):
        self._kt_root_._kt_beenden()

    # ---------------------------------------------------- bindings
    def bind(self, sequence=None, func=None, add=None):
        return self._kt_binden(self._kt_bindungen, sequence, func, add)

    @staticmethod
    def _kt_binden(tabelle, sequence, func, add):
        if sequence is None:
            return tuple(tabelle)
        if func is None:
            liste = tabelle.get(sequence)
            return "" if not liste else "bound"
        if isinstance(func, str):
            return ""
        if add and str(add).startswith("+") or add is True:
            tabelle.setdefault(sequence, []).append(func)
        else:
            tabelle[sequence] = [func]
        EV.parse(sequence)
        return f"{id(func)}{sequence}"

    def unbind(self, sequence, funcid=None):
        if funcid is None:
            self._kt_bindungen.pop(sequence, None)
        else:
            liste = self._kt_bindungen.get(sequence, [])
            self._kt_bindungen[sequence] = [f for f in liste if f"{id(f)}{sequence}" != funcid]

    def bind_all(self, sequence=None, func=None, add=None):
        return self._kt_binden(self._kt_root_._kt_bind_all, sequence, func, add)

    def unbind_all(self, sequence):
        self._kt_root_._kt_bind_all.pop(sequence, None)

    def bind_class(self, klasse, sequence=None, func=None, add=None):
        tab = self._kt_root_._kt_bind_klassen.setdefault(klasse, {})
        return self._kt_binden(tab, sequence, func, add)

    def unbind_class(self, klasse, sequence):
        self._kt_root_._kt_bind_klassen.get(klasse, {}).pop(sequence, None)

    def bindtags(self, tags=None):
        if tags is None:
            return tuple(self._kt_bindtags_liste())
        self._kt_bindtags = list(tags)

    def _kt_bindtags_liste(self):
        if self._kt_bindtags is not None:
            return self._kt_bindtags
        top = self.winfo_toplevel()
        if top is self:
            return [self._kt_pfad, self._kt_klasse, "all"]
        return [self._kt_pfad, self._kt_klasse, top._kt_pfad, "all"]

    def event_generate(self, sequence, **kw):
        m = EV.parse(sequence)
        if m is None:
            return
        if m.virtuell:
            ev = Event("Virtual", self, **kw)
            ev._kt_virtuell = m.text
        else:
            ev = Event(m.typ, self, **kw)
            if m.typ in ("KeyPress", "KeyRelease") and m.detail:
                ev.keysym = m.detail
            if m.typ in ("ButtonPress", "ButtonRelease") and m.detail:
                ev.num = m.detail
            ev.state = m.mods
        self._kt_root_._kt_ausloesen(self, ev)

    def event_add(self, virtual, *sequences):
        pass

    # ---------------------------------------------------- focus / grab
    def focus_set(self):
        self._kt_root_._kt_fokus_setzen(self)

    focus = focus_set

    def focus_force(self):
        self._kt_root_._kt_fokus_setzen(self)

    def focus_get(self):
        return self._kt_root_._kt_fokus

    def focus_displayof(self):
        return self._kt_root_._kt_fokus

    def focus_lastfor(self):
        return self._kt_root_._kt_fokus or self.winfo_toplevel()

    def tk_focusNext(self):
        return self._kt_root_._kt_fokus_nachbar(self, 1)

    def tk_focusPrev(self):
        return self._kt_root_._kt_fokus_nachbar(self, -1)

    def grab_set(self):
        self._kt_root_._kt_grab = self

    grab_set_global = grab_set

    def grab_release(self):
        if self._kt_root_._kt_grab is self:
            self._kt_root_._kt_grab = None

    def grab_current(self):
        return self._kt_root_._kt_grab

    def grab_status(self):
        return "local" if self._kt_root_._kt_grab is self else None

    # ---------------------------------------------------- clipboard
    def clipboard_clear(self, **kw):
        self._kt_root_._kt_ablage = ""
        try:
            Clipboard.copy("")
        except Exception:
            pass

    def clipboard_append(self, text, **kw):
        self._kt_root_._kt_ablage += str(text)
        try:
            Clipboard.copy(self._kt_root_._kt_ablage)
        except Exception:
            pass

    def clipboard_get(self, **kw):
        try:
            t = Clipboard.paste()
        except Exception:
            t = self._kt_root_._kt_ablage
        if t is None:
            raise TclError("CLIPBOARD selection doesn't exist")
        return t.replace("\r\n", "\n")

    def selection_get(self, **kw):
        return self.clipboard_get()

    # ---------------------------------------------------- misc
    def option_add(self, pattern, value, priority=None):
        self._kt_root_._kt_optionen[pattern] = value

    def option_get(self, name, klasse):
        return ""

    def register(self, func, subst=None, needcleanup=1):
        name = f"py{id(func)}"
        self._kt_root_._kt_befehle[name] = func
        return name

    _kt_register = register

    def getvar(self, name="PY_VAR"):
        v = _VARS.get(str(name))
        return v._kt_roh() if v is not None else ""

    def setvar(self, name="PY_VAR", value="1"):
        v = _VARS.get(str(name))
        if v is not None:
            v.set(value)

    def bell(self, displayof=0):
        pass

    def winfo_atom(self, *a):
        return 0

    def lift(self, aboveThis=None):
        self._kt_stapeln(oben=True)

    tkraise = lift

    def lower(self, belowThis=None):
        self._kt_stapeln(oben=False)

    def _kt_stapeln(self, oben):
        m = self.master
        if m is None:
            return
        name = self._name
        kinder = m.children
        if name in kinder:
            w = kinder.pop(name)
            if oben:
                kinder[name] = w
            else:
                m.children = {name: w, **kinder}
        if self._kt_eltern_k is not None:
            self._kt_abhaengen()
            self._kt_anhaengen()

    # ---------------------------------------------------- destroy
    def destroy(self):
        if self._kt_zerstoert:
            return
        for c in list(self.children.values()):
            c.destroy()
        r = self._kt_root_
        try:
            self._kt_ereignis("Destroy")
        except Exception:
            pass
        self._kt_zerstoert = True
        for k in ("textvariable", "variable", "listvariable"):
            v = self._kt_o.get(k)
            if isinstance(v, Variable):
                v._kt_vergessen(self)
        if self._kt_manager:
            try:
                self._kt_geo_vergessen()
            except Exception:
                pass
        for liste in (self._pack_slaves, self._grid_slaves, self._kt_place_slaves):
            for s in list(liste):
                s._kt_manager = None
                s._kt_geo_master = None
        self._kt_abhaengen()
        if self.master is not None:
            self.master.children.pop(self._name, None)
        if r is not self:
            r._kt_widgets.pop(self._kt_pfad, None)
            r._kt_widget_weg(self)
        self._kt_bindungen = {}

    # ---------------------------------------------------- internal: events
    def _kt_ereignis(self, typ, **kw):
        ev = Event(typ, self, **kw)
        self._kt_root_._kt_ausloesen(self, ev)
        return ev

    # ---------------------------------------------------- internal: layout / drawing
    def _kt_layout_planen(self):
        r = self._kt_root_
        if r is not None and not self._kt_zerstoert:
            r._kt_layout_anfordern()

    def _kt_neu_zeichnen(self):
        self._kt_zeichnen_noetig = True
        r = self._kt_root_
        if r is not None:
            r._kt_zeichnen_anfordern(self)

    def _kt_innen(self):
        """Inner border (left, top, right, bottom): borderwidth + highlight + padding."""
        b = _int(self._kt_o.get("borderwidth", 0)) + _int(self._kt_o.get("highlightthickness", 0))
        pl = pt = pr = pb = 0
        pad = self._kt_o.get("padding")
        if pad not in (None, ""):
            pl, pt, pr, pb = _padding(pad)
        return b + pl, b + pt, b + pr, b + pb

    def _kt_req(self):
        r = self._kt_root_
        if self._kt_req_pass == r._kt_pass:
            return self._kt_req_wert
        l, t, rr, b = self._kt_innen()
        kinder = [s for s in self._pack_slaves if s._kt_lebt] or [s for s in self._grid_slaves if s._kt_lebt]
        if self._kt_propagate and kinder:
            if self._pack_slaves and any(s._kt_lebt for s in self._pack_slaves):
                cw, ch = pack_req(self)
                if self._grid_slaves:
                    gw, gh = grid_req(self)
                    cw, ch = max(cw, gw), max(ch, gh)
            else:
                cw, ch = grid_req(self)
            w, h = cw + l + rr, ch + t + b
        else:
            w, h = self._kt_natuerlich()
        w, h = max(1, int(w)), max(1, int(h))
        self._kt_req_pass = r._kt_pass
        self._kt_req_wert = (w, h)
        return w, h

    def _kt_natuerlich(self):
        l, t, r, b = self._kt_innen()
        w = _mass(self._kt_o.get("width", 0) or 0)
        h = _mass(self._kt_o.get("height", 0) or 0)
        return max(w, l + r), max(h, t + b)

    def _kt_setzen(self, x, y, w, h, sichtbar=True):
        geaendert = (w, h) != (self._kt_w, self._kt_h)
        bewegt = (x, y) != (self._kt_x, self._kt_y)
        war = self._kt_sichtbar
        self._kt_x, self._kt_y = int(x), int(y)
        if sichtbar:
            self._kt_w, self._kt_h = int(w), int(h)
        self._kt_sichtbar = bool(sichtbar)
        if self._kt_sichtbar != war:
            if self._kt_sichtbar:
                self._kt_anhaengen()
                self._kt_root_._kt_spaeter(self, "Map")
            else:
                self._kt_abhaengen()
                self._kt_root_._kt_spaeter(self, "Unmap")
        if self._kt_sichtbar and (geaendert or bewegt or not war):
            self._kt_zeichnen_noetig = self._kt_zeichnen_noetig or geaendert or not war
            self._kt_root_._kt_spaeter(self, "Configure")

    def _kt_abbilden_planen(self):
        self._kt_lebt = True
        self._kt_layout_planen()

    def _kt_abbilden(self, an):
        self._kt_lebt = an
        if not an and self._kt_sichtbar:
            self._kt_sichtbar = False
            self._kt_abhaengen()
            self._kt_root_._kt_spaeter(self, "Unmap")

    def _kt_anordnen(self):
        """Places the slaves (recursively)."""
        if self._pack_slaves:
            pack_anordnen(self)
        if self._grid_slaves:
            grid_anordnen(self)
        if self._kt_place_slaves:
            place_anordnen(self)
        for c in list(self.children.values()):
            if c._kt_lebt and c._kt_sichtbar and not c._kt_ist_toplevel:
                c._kt_anordnen()

    def _kt_kivy_eltern(self):
        return self.master._kt_k if self.master is not None else None

    def _kt_anhaengen(self):
        """Puts the Kivy widget into the parent's one, keeping Tk's stacking order."""
        if self._kt_zerstoert:
            return
        ek = self._kt_kivy_eltern()
        if ek is None or self._kt_k.parent is ek:
            self._kt_eltern_k = ek
            return
        if self._kt_k.parent is not None:
            self._kt_k.parent.remove_widget(self._kt_k)
        # Kivy: index 0 = drawn last (on top). Keep the order of master.children.
        geschwister = [c._kt_k for c in self.master.children.values()
                       if c is not self and c._kt_k.parent is ek] if self.master else []
        nach = 0
        if self.master is not None:
            sichtbar_nach = False
            for c in self.master.children.values():
                if c is self:
                    sichtbar_nach = True
                    continue
                if sichtbar_nach and c._kt_k.parent is ek:
                    nach += 1
        try:
            ek.add_widget(self._kt_k, index=min(nach, len(geschwister)))
        except Exception:
            ek.add_widget(self._kt_k)
        self._kt_eltern_k = ek
        self._kt_zeichnen_noetig = True

    def _kt_abhaengen(self):
        if self._kt_k.parent is not None:
            self._kt_k.parent.remove_widget(self._kt_k)
        self._kt_eltern_k = None

    def _kt_kivy_pos(self):
        x, y = self._kt_abs()
        return x, _fh() - y - self._kt_h

    def _kt_darstellen(self):
        """Moves the Kivy widget and redraws when needed (called once per frame)."""
        if not self._kt_sichtbar or self._kt_zerstoert:
            return
        kx, ky = self._kt_kivy_pos()
        k = self._kt_k
        if (k.x, k.y) != (kx, ky):
            k.pos = (kx, ky)
            self._kt_zeichnen_noetig = True
        if tuple(k.size) != (self._kt_w, self._kt_h):
            k.size = (self._kt_w, self._kt_h)
            self._kt_zeichnen_noetig = True
        if self._kt_zeichnen_noetig:
            self._kt_zeichnen_noetig = False
            self._kt_g_hinten.clear()
            self._kt_g_inhalt.clear()
            self._kt_malen(kx, ky)

    # -- drawing helpers (Tk coordinates inside the widget -> Kivy)
    def _kt_malen(self, kx, ky):
        self._kt_hintergrund(kx, ky)

    def _kt_farbe_opt(self, name, standard=None):
        return _rgba(self._kt_o.get(name), standard)

    def _kt_hintergrund(self, kx, ky, farbe=None):
        g = self._kt_g_hinten
        bg = farbe if farbe is not None else self._kt_farbe_opt("background")
        w, h = self._kt_w, self._kt_h
        if bg is not None:
            g.add(Color(*bg))
            g.add(Rectangle(pos=(kx, ky), size=(w, h)))
        ht = _int(self._kt_o.get("highlightthickness", 0))
        if ht > 0:
            hf = self._kt_farbe_opt("highlightcolor" if "focus" in self._kt_zustand
                                 else "highlightbackground") or bg or (0, 0, 0, 1)
            if hf is not None:
                _rahmen(g, kx, ky, w, h, ht, hf)
        bd = _int(self._kt_o.get("borderwidth", 0))
        relief = self._kt_o.get("relief", FLAT)
        if bd > 0 and relief != FLAT:
            _relief(g, kx + ht, ky + ht, w - 2 * ht, h - 2 * ht, bd, relief, bg or (0.5, 0.5, 0.5, 1))

    def _kt_text_zeichnen(self, g, text, font, farbe, x, y, anchor="nw", kx=0, ky=0):
        """Draws one line of text at (x, y) in widget coordinates (Tk orientation)."""
        tex = fontmod.text_textur(text, font)
        if tex is None:
            return
        tw, th = tex.size
        if anchor in ("n", "s", "center"):
            x -= tw / 2
        elif "e" in anchor:
            x -= tw
        if anchor in ("w", "e", "center"):
            y -= th / 2
        elif "s" in anchor:
            y -= th
        fontmod.text_zeichnen(g, tex, farbe, (int(kx + x), int(ky + self._kt_h - y - th)), (tw, th))


def _fh():
    """Height of the window as the layout knows it (Kivy's Window.height lags behind a
    size set by the program)."""
    r = _base.ROOT[0]
    return r._kt_fenster_h if r is not None else Window.height


def _int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def _mass(v):
    """Tk distance ("10", 10, "2c", "1i", "5p") -> pixels."""
    if v is None or v == "":
        return 0
    if isinstance(v, (int, float)):
        return v
    s = str(v).strip()
    try:
        if s[-1] in "cimp":
            z = float(s[:-1])
            dpi = _base.skalierung() * 72
            return z * {"c": dpi / 2.54, "i": dpi, "m": dpi / 25.4, "p": dpi / 72}[s[-1]]
        return float(s)
    except (ValueError, IndexError):
        return 0


def _padding(p):
    if isinstance(p, (int, float)):
        p = int(p)
        return p, p, p, p
    if isinstance(p, str):
        p = [_int(x) for x in p.split()]
    p = [_int(x) for x in p]
    if len(p) == 1:
        return p[0], p[0], p[0], p[0]
    if len(p) == 2:
        return p[0], p[1], p[0], p[1]
    if len(p) == 3:
        return p[0], p[1], p[2], p[1]
    return p[0], p[1], p[2], p[3]


def _rahmen(g, kx, ky, w, h, dicke, farbe):
    g.add(Color(*farbe))
    d = dicke
    g.add(Rectangle(pos=(kx, ky), size=(w, d)))
    g.add(Rectangle(pos=(kx, ky + h - d), size=(w, d)))
    g.add(Rectangle(pos=(kx, ky), size=(d, h)))
    g.add(Rectangle(pos=(kx + w - d, ky), size=(d, h)))


def _heller(f, faktor):
    return tuple(min(1.0, c * faktor) if faktor > 1 else c * faktor for c in f[:3]) + (1,)


def _relief(g, kx, ky, w, h, bd, relief, bg):
    hell, dunkel = _heller(bg, 1.45) if sum(bg[:3]) > 0.05 else (0.35, 0.35, 0.35, 1), _heller(bg, 0.55)
    if relief == SOLID:
        _rahmen(g, kx, ky, w, h, bd, (0, 0, 0, 1))
        return
    if relief in (SUNKEN, GROOVE):
        hell, dunkel = dunkel, hell
    oben_links, unten_rechts = hell, dunkel
    if relief in (RIDGE, GROOVE):
        d = max(1, bd // 2)
        _rahmen(g, kx, ky, w, h, d, oben_links)
        _rahmen(g, kx + d, ky + d, w - 2 * d, h - 2 * d, max(1, bd - d), unten_rechts)
        return
    g.add(Color(*oben_links))
    g.add(Rectangle(pos=(kx, ky + h - bd), size=(w, bd)))
    g.add(Rectangle(pos=(kx, ky), size=(bd, h)))
    g.add(Color(*unten_rechts))
    g.add(Rectangle(pos=(kx, ky), size=(w, bd)))
    g.add(Rectangle(pos=(kx + w - bd, ky), size=(bd, h)))


# ============================================================
# Widget base: Misc + geometry managers
# ============================================================
class BaseWidget(Misc, GeometrieMixin):
    def __init__(self, master=None, cnf=None, **kw):
        if master is None:
            master = _base.ROOT[0]
            if master is None:
                master = Tk()
        self._kt_anlegen(master, cnf, kw)


class Widget(BaseWidget):
    pass


# ============================================================
# The Tcl interpreter stand-in (tk.call / tk.eval)
# ============================================================
class _Interp:
    def __init__(self, root):
        self._kt_root = root

    def call(self, *args):
        if args[:2] == ("tk", "windowingsystem"):
            import sys
            return "win32" if sys.platform.startswith("win") else (
                "aqua" if sys.platform == "darwin" else "x11")
        if args[:2] == ("tk", "scaling"):
            return _base.skalierung()
        if args and args[0] == "info" and args[1:2] == ("patchlevel",):
            return "8.6.13"
        if args and args[0] == "wm":
            return ""
        return ""

    def eval(self, script):
        return ""

    def globalgetvar(self, name):
        v = _VARS.get(str(name))
        return v._kt_roh() if v is not None else ""

    getvar = globalgetvar

    def globalsetvar(self, name, value):
        v = _VARS.get(str(name))
        if v is not None:
            v.set(value)

    setvar = globalsetvar

    def splitlist(self, s):
        if isinstance(s, (tuple, list)):
            return tuple(s)
        return tuple(str(s).split())

    def getboolean(self, v):
        return getboolean(v)

    def getint(self, v):
        return int(v)

    def getdouble(self, v):
        return float(v)

    def createcommand(self, name, func):
        self._kt_root._kt_befehle[name] = func

    def deletecommand(self, name):
        self._kt_root._kt_befehle.pop(name, None)


# ============================================================
# Wm: methods of Tk and Toplevel
# ============================================================
TITEL_H = 28


class Wm:
    _kt_ist_toplevel = True

    def _kt_wm_init(self):
        self._kt_titel = ""
        self._kt_geo_gesetzt = None        # (w, h) fixed by geometry()
        self._kt_pos_gesetzt = None        # (x, y)
        self._kt_ohne_rahmen = False
        self._kt_protokolle = {}
        self._kt_minsize = (1, 1)
        self._kt_maxsize = (100000, 100000)
        self._kt_groesse_aenderbar = (True, True)
        self._kt_attribute = {}
        self._kt_letzter_fokus = None
        self._kt_zustand_wm = "normal"

    def title(self, string=None):
        if string is None:
            return self._kt_titel
        self._kt_titel = str(string)
        self._kt_titel_gesetzt()

    wm_title = title

    def _kt_titel_gesetzt(self):
        self._kt_zeichnen_noetig = True
        self._kt_neu_zeichnen()

    def geometry(self, newGeometry=None):
        if newGeometry is None:
            return f"{self._kt_w}x{self._kt_h}+{self._kt_x}+{self._kt_y}"
        g = str(newGeometry).strip()
        groesse, pos = g, None
        for i, ch in enumerate(g):
            if ch in "+-" and i > 0:
                groesse, pos = g[:i], g[i:]
                break
            if ch in "+-" and i == 0:
                groesse, pos = "", g
                break
        if groesse and "x" in groesse:
            w, h = groesse.split("x")
            self._kt_geo_gesetzt = (int(w), int(h))
        if pos:
            teile = []
            aktuell = ""
            for ch in pos:
                if ch in "+-" and aktuell:
                    teile.append(aktuell)
                    aktuell = ch
                else:
                    aktuell += ch
            teile.append(aktuell)
            if len(teile) >= 2:
                x, y = int(teile[0].replace("+", "")), int(teile[1].replace("+", ""))
                self._kt_pos_gesetzt = (x, y)
        self._kt_geometrie_angewandt()
        self._kt_layout_planen()

    wm_geometry = geometry

    def _kt_geometrie_angewandt(self):
        pass

    def overrideredirect(self, flag=None):
        if flag is None:
            return self._kt_ohne_rahmen
        self._kt_ohne_rahmen = bool(flag)
        self._kt_layout_planen()

    wm_overrideredirect = overrideredirect

    def protocol(self, name=None, func=None):
        if func is None:
            return self._kt_protokolle.get(name, "")
        self._kt_protokolle[name] = func

    wm_protocol = protocol

    def minsize(self, width=None, height=None):
        if width is None:
            return self._kt_minsize
        self._kt_minsize = (int(width), int(height))

    wm_minsize = minsize

    def maxsize(self, width=None, height=None):
        if width is None:
            return self._kt_maxsize
        self._kt_maxsize = (int(width), int(height))

    wm_maxsize = maxsize

    def resizable(self, width=None, height=None):
        if width is None:
            return self._kt_groesse_aenderbar
        self._kt_groesse_aenderbar = (bool(width), bool(height if height is not None else width))

    wm_resizable = resizable

    def transient(self, master=None):
        self._kt_transient = master

    wm_transient = transient

    def attributes(self, *args):
        if len(args) == 1:
            return self._kt_attribute.get(str(args[0]).lstrip("-"), "")
        for k, v in zip(args[::2], args[1::2]):
            self._kt_attribute[str(k).lstrip("-")] = v
            if str(k).lstrip("-") == "topmost" and v:
                self.lift()
        return ""

    wm_attributes = attributes

    def iconphoto(self, default=False, *images):
        pass

    wm_iconphoto = iconphoto

    def iconbitmap(self, bitmap=None, default=None):
        pass

    wm_iconbitmap = iconbitmap

    def iconname(self, name=None):
        return ""

    def group(self, w=None):
        pass

    def state(self, newstate=None):
        if newstate is None:
            return self._kt_zustand_wm
        self._kt_zustand_wm = newstate
        if newstate == "withdrawn":
            self.withdraw()
        elif newstate == "iconic":
            self.iconify()
        elif newstate in ("normal", "zoomed"):
            self.deiconify()
        return ""

    wm_state = state

    def withdraw(self):
        self._kt_zustand_wm = "withdrawn"
        self._kt_fenster_zeigen(False)

    wm_withdraw = withdraw

    def deiconify(self):
        if self._kt_zustand_wm in ("withdrawn", "iconic"):
            self._kt_zustand_wm = "normal"
        self._kt_fenster_zeigen(True)

    wm_deiconify = deiconify

    def iconify(self):
        self._kt_zustand_wm = "iconic"
        self._kt_fenster_zeigen(False)

    wm_iconify = iconify

    def frame(self):
        return hex(id(self))

    def winfo_toplevel(self):
        return self

    def _kt_client_dx(self):
        return 0

    def _kt_client_dy(self):
        return 0


# ============================================================
# Tk (root window = the Kivy window)
# ============================================================
class Tk(Wm, Misc, GeometrieMixin):
    _kt_klasse = "Tk"
    _kt_standard = {"background": "#f0f0f0", "menu": "", "highlightthickness": 0, "borderwidth": 0}

    def __init__(self, screenName=None, baseName=None, className="Tk", useTk=True, sync=False,
                 use=None):
        if _base.ROOT[0] is not None and not _base.ROOT[0]._kt_zerstoert:
            raise TclError("only one Tk root window is supported by the Kivy layer")
        self._kt_widgets = {}
        self._kt_interp = None
        self._kt_wm_init()
        self._kt_pass = 0
        self._kt_layout_offen = False
        self._kt_toplevels = []            # stacking order, last = on top
        self._kt_after_ids = {}
        self._kt_after_n = 0
        self._kt_bind_all = {}
        self._kt_bind_klassen = {}
        self._kt_optionen = {}
        self._kt_befehle = {}
        self._kt_fokus = None
        self._kt_grab = None
        self._kt_ablage = ""
        self._kt_ende = False
        self._kt_zeichnen_liste = set()
        self._kt_spaeter_liste = []
        self._kt_maus_widget = None        # widget under the pointer
        self._kt_maus_ziel = None          # implicit grab while a button is held
        self._kt_knoepfe = set()
        self._kt_letzter_klick = (0, 0, 0, 0, 0)  # (zeit, x, y, num, anzahl)
        self._kt_cursor_name = None
        self._kt_titel_drag = None
        self._kt_popups = []
        self._kt_text_erlaubt = True
        self._kt_schleife_laeuft = False
        _base.ROOT[0] = self
        global _default_root
        _default_root = self
        self._kt_anlegen(None, None, {})
        self._kt_interp = _Interp(self)
        self.tk = self._kt_interp
        self._kt_root_ = self
        self._kt_widgets["."] = self
        self._kt_sichtbar = True
        self._kt_lebt = True
        self._kt_titel_h = 0                # own title bar of the main window (titelleiste.py)
        self._kt_leiste = None
        self._kt_fenster_w = int(Window.width)
        self._kt_fenster_h = int(Window.height)
        self._kt_rand = (0, 0, 0, 0)        # maximised with own title bar: off-screen frame
        self._kt_w, self._kt_h = int(Window.width), int(Window.height)
        # Kivy: our root surface + one layer for the Toplevels above it
        self._kt_ebene = _Flaeche(size_hint=(None, None), size=Window.size, pos=(0, 0))
        Window.add_widget(self._kt_k)
        Window.add_widget(self._kt_ebene)
        self._kt_k.pos = (0, 0)
        self._kt_k.size = Window.size
        self._kt_eltern_k = Window
        self._kt_trigger_layout = Clock.create_trigger(self._kt_layout_tick, -1)
        self._kt_trigger_zeichnen = Clock.create_trigger(self._kt_zeichnen_tick, -1)
        self._kt_bewegung_offen = None
        self._kt_trigger_bewegung = Clock.create_trigger(self._kt_bewegung_senden, -1)
        Window.bind(on_mouse_down=self._kt_k_maus_runter, on_mouse_up=self._kt_k_maus_hoch,
                    on_mouse_move=self._kt_k_maus_zug, mouse_pos=self._kt_k_maus_pos,
                    on_key_down=self._kt_k_taste_runter, on_key_up=self._kt_k_taste_hoch,
                    on_textinput=self._kt_k_text, on_resize=self._kt_k_groesse,
                    on_request_close=self._kt_k_schliessen, focus=self._kt_k_fenster_fokus,
                    on_cursor_leave=self._kt_k_maus_raus)
        # a size set by the program reaches us as a property change, not always as on_resize
        Window.bind(size=lambda _w, gr: self._kt_k_groesse(Window, gr[0], gr[1]))
        try:
            Window.clearcolor = (0, 0, 0, 1)
        except Exception:
            pass
        from katiecad.ui.kt import titelleiste
        self._kt_leiste = titelleiste.einrichten(self)
        if self._kt_leiste is not None:
            self._kt_titel_h = titelleiste.HOEHE
            self._kt_h = self._kt_fenster_h - self._kt_titel_h
            Window.bind(focus=lambda _w, an: (setattr(self._kt_leiste, "aktiv", bool(an)),
                                               self._kt_leiste.zeichnen()))
        self._kt_layout_anfordern()
        from katiecad.ui.kt import klassen
        klassen.installieren(self)
        print("[KatieCAD] Oberflaeche: Kivy, Text: "
              + ("GDI (wie Tk)" if fontmod._gdi() else "SDL_ttf"))

    # ---------------------------------------------------- window manager
    def _kt_titel_gesetzt(self):
        try:
            Window.set_title(self._kt_titel)
        except Exception:
            pass
        if self._kt_leiste is not None:
            self._kt_leiste.zeichnen()

    def _kt_client_dx(self):
        return self._kt_rand[0]

    def _kt_client_dy(self):
        return self._kt_rand[1] + self._kt_titel_h

    def _kt_rand_setzen(self, maximiert):
        """Windows places a maximised window's frame outside the screen (about 8 px per
        side); with our own title bar that strip belongs to the client area, so the content
        keeps clear of it."""
        r = 0
        if maximiert and sys.platform.startswith("win"):
            try:
                import ctypes
                u = ctypes.windll.user32
                r = u.GetSystemMetrics(32) + u.GetSystemMetrics(92)   # SIZEFRAME + PADDEDBORDER
            except Exception:
                r = 8
        self._kt_rand = (r, r, r, r)
        self._kt_k_groesse(Window, self._kt_fenster_w, self._kt_fenster_h, erzwingen=True)

    def _kt_geometrie_angewandt(self):
        if self._kt_geo_gesetzt:
            w, h = self._kt_geo_gesetzt
            h += self._kt_titel_h             # geometry() means the content, as under Tk
            try:
                Window.size = (w, h)
            except Exception:
                pass
            self._kt_k_groesse(Window, w, h)
        if self._kt_pos_gesetzt:
            try:
                Window.left, Window.top = self._kt_pos_gesetzt
            except Exception:
                pass

    def minsize(self, width=None, height=None):
        if width is None:
            return self._kt_minsize
        self._kt_minsize = (int(width), int(height))
        try:
            Window.minimum_width, Window.minimum_height = self._kt_minsize
        except Exception:
            pass

    wm_minsize = minsize

    def state(self, newstate=None):
        if newstate is None:
            return self._kt_zustand_wm
        self._kt_zustand_wm = newstate
        try:
            if newstate == "zoomed":
                Window.maximize()
            elif newstate == "iconic":
                Window.minimize()
            elif newstate == "normal":
                Window.restore()
            elif newstate == "withdrawn":
                Window.hide()
        except Exception:
            pass
        return ""

    wm_state = state

    def _kt_fenster_zeigen(self, an):
        try:
            Window.show() if an else Window.hide()
        except Exception:
            pass

    def iconbitmap(self, bitmap=None, default=None):
        pfad = default or bitmap
        if pfad:
            try:
                Window.set_icon(str(pfad))
            except Exception:
                pass

    wm_iconbitmap = iconbitmap

    def iconphoto(self, default=False, *images):
        for im in images:
            pfad = getattr(im, "_kt_datei", None)
            if pfad:
                try:
                    Window.set_icon(pfad)
                except Exception:
                    pass

    wm_iconphoto = iconphoto

    def createcommand(self, name, func):
        self._kt_befehle[name] = func

    def report_callback_exception(self, exc, val, tb):
        import traceback
        traceback.print_exception(exc, val, tb)

    def destroy(self):
        if self._kt_zerstoert:
            return
        for t in list(self._kt_toplevels):
            t.destroy()
        Misc.destroy(self)
        self._kt_ende = True
        _base.ROOT[0] = None
        global _default_root
        _default_root = None
        try:
            from kivy.base import stopTouchApp
            stopTouchApp()
        except Exception:
            pass
        try:
            Window.close()
        except Exception:
            pass

    def _kt_beenden(self):
        self._kt_ende = True
        try:
            from kivy.base import stopTouchApp
            stopTouchApp()
        except Exception:
            pass

    # ---------------------------------------------------- main loop
    def _kt_hauptschleife(self):
        if self._kt_schleife_laeuft:
            while not self._kt_ende:
                self._kt_ein_schritt()
            return
        self._kt_schleife_laeuft = True
        self._kt_starten()
        try:
            while not self._kt_ende and not EventLoop.quit:
                self._kt_ein_schritt()
        finally:
            self._kt_schleife_laeuft = False

    def _kt_starten(self):
        if EventLoop.status != "started":
            from kivy.base import _runTouchApp_prepare
            _runTouchApp_prepare(None)

    def _kt_ein_schritt(self):
        """One round of the Kivy event loop (also used for nested loops: wait_window)."""
        if EventLoop.status != "started":
            self._kt_starten()
        try:
            EventLoop.idle()
            if EventLoop.window:
                EventLoop.window.mainloop()
        except Exception:
            import traceback
            traceback.print_exc()
        if EventLoop.quit:
            self._kt_ende = True

    # ---------------------------------------------------- after
    def _kt_after(self, ms, func, args):
        self._kt_after_n += 1
        ident = f"after#{self._kt_after_n}"
        if func is None:
            # after(ms) without a function: sleep while processing events
            ende = time.monotonic() + (0 if ms == "idle" else ms / 1000)
            while time.monotonic() < ende and not self._kt_ende:
                self._kt_ein_schritt()
            return None

        def lauf(_dt, ident=ident):
            if self._kt_after_ids.pop(ident, None) is None:
                return
            if self._kt_zerstoert:
                return
            try:
                func(*args)
            except Exception:
                import sys
                self.report_callback_exception(*sys.exc_info())

        ev = Clock.schedule_once(lauf, 0 if ms == "idle" else max(0, ms) / 1000)
        self._kt_after_ids[ident] = ev
        return ident

    def _kt_after_cancel(self, ident):
        ev = self._kt_after_ids.pop(ident, None) if ident else None
        if ev is not None:
            ev.cancel()

    # ---------------------------------------------------- layout
    def _kt_alles_ungueltig(self):
        for w in list(self._kt_widgets.values()):
            w._kt_zeichnen_noetig = True
            self._kt_zeichnen_liste.add(w)
        self._kt_layout_anfordern()

    def _kt_layout_anfordern(self):
        if not self._kt_layout_offen:
            self._kt_layout_offen = True
            try:
                self._kt_trigger_layout()
            except Exception:
                pass

    def _kt_zeichnen_anfordern(self, w):
        self._kt_zeichnen_liste.add(w)
        try:
            self._kt_trigger_zeichnen()
        except Exception:
            pass

    def _kt_layout_tick(self, _dt=None):
        self._kt_layout_jetzt()

    def _kt_layout_jetzt(self):
        if not self._kt_layout_offen:
            self._kt_ereignisse_senden()
            return
        self._kt_layout_offen = False
        self._kt_pass += 1
        self._kt_anordnen()
        for t in list(self._kt_toplevels):
            if not t._kt_zerstoert:
                t._kt_toplevel_anordnen()
        self._kt_zeichnen_tick()
        self._kt_ereignisse_senden()

    def _kt_spaeter(self, w, typ):
        self._kt_spaeter_liste.append((w, typ))

    def _kt_ereignisse_senden(self):
        liste, self._kt_spaeter_liste = self._kt_spaeter_liste, []
        gesehen = set()
        for w, typ in liste:
            if w._kt_zerstoert or (id(w), typ) in gesehen:
                continue
            gesehen.add((id(w), typ))
            if typ == "Configure":
                w._kt_ereignis("Configure", width=w._kt_w, height=w._kt_h, x=w._kt_x, y=w._kt_y)
            else:
                w._kt_ereignis(typ)

    def _kt_zeichnen_tick(self, _dt=None):
        if self._kt_layout_offen:
            self._kt_layout_jetzt()
            return
        # everything visible: position + (re)draw; parents first
        self._kt_alle_darstellen(self)
        for t in self._kt_toplevels:
            if t._kt_sichtbar and not t._kt_zerstoert:
                self._kt_alle_darstellen(t)
        self._kt_zeichnen_liste.clear()

    def _kt_alle_darstellen(self, w):
        if w._kt_zerstoert or not w._kt_sichtbar:
            return
        w._kt_darstellen()
        for c in list(w.children.values()):
            if not c._kt_ist_toplevel and c._kt_lebt and c._kt_sichtbar:
                self._kt_alle_darstellen(c)
        nach = getattr(w, "_nach_darstellen", None)
        if nach:
            nach()

    def _kt_darstellen(self):
        k = self._kt_k
        if tuple(k.size) != (self._kt_fenster_w, self._kt_fenster_h):
            k.size = (self._kt_fenster_w, self._kt_fenster_h)
            self._kt_ebene.size = (self._kt_fenster_w, self._kt_fenster_h)
            self._kt_zeichnen_noetig = True
        if self._kt_zeichnen_noetig:
            self._kt_zeichnen_noetig = False
            self._kt_g_hinten.clear()
            self._kt_g_inhalt.clear()
            bg = self._kt_farbe_opt("background", (0.94, 0.94, 0.94, 1))
            self._kt_g_hinten.add(Color(*bg))
            self._kt_g_hinten.add(Rectangle(pos=(0, 0), size=(self._kt_fenster_w, self._kt_fenster_h)))
            if self._kt_leiste is not None:
                self._kt_leiste.zeichnen()          # its colours follow the background

    def _kt_abs(self):
        return self._kt_client_dx(), self._kt_client_dy()

    def _kt_kivy_pos(self):
        return 0, 0

    def _kt_widget_weg(self, w):
        if self._kt_fokus is w:
            self._kt_fokus = None
        if self._kt_grab is w:
            self._kt_grab = None
        if self._kt_maus_widget is w:
            self._kt_maus_widget = None
        if self._kt_maus_ziel is w:
            self._kt_maus_ziel = None
        if w in self._kt_toplevels:
            self._kt_toplevels.remove(w)
            self._kt_fokus_zurueck()
        self._kt_zeichnen_liste.discard(w)

    # ---------------------------------------------------- hit test
    def _kt_maus_tk(self):
        mx, my = Window.mouse_pos
        return int(mx), int(_fh() - 1 - my)

    def _kt_widget_bei(self, x, y, nur_grab=True):
        grab = self._kt_grab if nur_grab else None
        for t in reversed(self._kt_toplevels):
            if not t._kt_sichtbar or t._kt_zerstoert:
                continue
            if grab is not None and not _ist_in(t, grab.winfo_toplevel()):
                continue
            tx, ty = t._kt_x, t._kt_y
            if tx <= x < tx + t._kt_aussen_w() and ty <= y < ty + t._kt_aussen_h():
                w = _suchen(t, x - t._kt_x - t._kt_client_dx(), y - t._kt_y - t._kt_client_dy())
                return w or t
        if grab is not None and grab.winfo_toplevel() is not self:
            return None
        return _suchen(self, x - self._kt_client_dx(), y - self._kt_client_dy()) or self

    # ---------------------------------------------------- dispatch
    def _kt_ausloesen(self, widget, ev):
        """Calls the bindings of every bind tag of the widget (Tk order); "break" stops."""
        for tag in widget._kt_bindtags_liste():
            if tag == widget._kt_pfad:
                tab = widget._kt_bindungen
            elif tag == "all":
                tab = self._kt_bind_all
            elif tag in self._kt_widgets:
                tab = self._kt_widgets[tag]._kt_bindungen
            else:
                tab = self._kt_bind_klassen.get(tag)
            if not tab:
                continue
            bester, gewicht = None, None
            for seq, funcs in tab.items():
                m = EV.parse(seq)
                if m is None or not funcs or not EV.passt(m, ev):
                    continue
                g = m.gewicht()
                if gewicht is None or g > gewicht:
                    bester, gewicht = funcs, g
            if bester is None:
                continue
            stop = False
            for f in list(bester):
                try:
                    erg = f(ev)
                except Exception:
                    import sys
                    self.report_callback_exception(*sys.exc_info())
                    erg = None
                if erg == "break":
                    stop = True
                    break
            if stop or widget._kt_zerstoert:
                return True
        return False

    def _kt_maus_ereignis(self, w, typ, x, y, **kw):
        ax, ay = w._kt_abs()
        ev = Event(typ, w, x=int(x - ax), y=int(y - ay), x_root=int(x), y_root=int(y),
                   state=self._kt_modifier_state(), **kw)
        self._kt_ausloesen(w, ev)
        return ev

    def _kt_modifier_state(self):
        s = 0
        mods = getattr(Window, "modifiers", []) or []
        if "shift" in mods:
            s |= EV.SHIFT
        if "ctrl" in mods:
            s |= EV.CONTROL
        if "alt" in mods:
            s |= EV.ALT
        if "capslock" in mods:
            s |= EV.LOCK
        if "meta" in mods:
            import sys
            if sys.platform == "darwin":
                s |= EV.CONTROL
        for b in self._kt_knoepfe:
            s |= EV._BTN_BIT.get(b, 0)
        return s

    def _kt_kette(self, w):
        erg = []
        while w is not None:
            erg.append(w)
            if w._kt_ist_toplevel:
                break
            w = w.master
        return erg

    def _kt_hover(self, neu, x, y):
        alt = self._kt_maus_widget
        if neu is alt:
            return
        alt_k = self._kt_kette(alt) if alt is not None and not alt._kt_zerstoert else []
        neu_k = self._kt_kette(neu) if neu is not None else []
        for w in alt_k:
            if w not in neu_k and not w._kt_zerstoert:
                w._kt_zustand.discard("active")
                w._kt_hover_aenderung()
                self._kt_maus_ereignis(w, "Leave", x, y)
        self._kt_maus_widget = neu
        for w in reversed(neu_k):
            if w not in alt_k and not w._kt_zerstoert:
                if w._kt_hover_aktiv:            # like Tk: only buttons & co. become "active"
                    w._kt_zustand.add("active")
                w._kt_hover_aenderung()
                self._kt_maus_ereignis(w, "Enter", x, y)
        self._kt_cursor_setzen(neu)

    def _kt_cursor_setzen(self, w):
        name = ""
        while w is not None and not name:
            name = w._kt_cursor
            w = None if w._kt_ist_toplevel else w.master
        k = _CURSOR.get(name, "arrow")
        if k != self._kt_cursor_name:
            self._kt_cursor_name = k
            try:
                Window.set_system_cursor(k)
            except Exception:
                pass

    # Motion compression like Tk: many pointer moves between two frames -> one Motion event
    # with the latest position (the 3D view redraws the whole scene per Motion)
    def _kt_k_maus_pos(self, _win, pos):
        self._kt_bewegung_offen = self._kt_bewegung_offen or "pos"
        self._kt_trigger_bewegung()

    def _kt_k_maus_zug(self, _win, _x, _y, _mods):
        self._kt_bewegung_offen = "zug"
        self._kt_trigger_bewegung()

    def _kt_bewegung_senden(self, *_a):
        art, self._kt_bewegung_offen = self._kt_bewegung_offen, None
        if art == "zug":
            self._kt_bewegung_zug()
        elif art == "pos":
            self._kt_bewegung_pos()

    def _kt_bewegung_pos(self):
        if self._kt_ende:
            return
        x, y = self._kt_maus_tk()
        if self._kt_knoepfe and self._kt_maus_ziel is not None:
            return                      # handled by on_mouse_move (button held)
        neu = self._kt_widget_bei(x, y)
        if self._kt_leiste is not None:
            self._kt_leiste.setze_hover(self._kt_leiste.knopf_bei(x, y)
                                        if neu is self and y < self._kt_client_dy() else None)
        self._kt_hover(neu, x, y)
        if neu is not None:
            self._kt_maus_ereignis(neu, "Motion", x, y)

    def _kt_k_maus_raus(self, *_a):
        x, y = self._kt_maus_tk()
        if not self._kt_knoepfe:
            self._kt_hover(None, x, y)

    def _kt_bewegung_zug(self):
        x, y = self._kt_maus_tk()
        if self._kt_titel_drag is not None:
            top, dx, dy = self._kt_titel_drag
            if not top._kt_zerstoert:
                top._kt_pos_gesetzt = (max(-top._kt_w + 60, min(self._kt_w - 60, x - dx)),
                                    max(0, min(self._kt_h - TITEL_H, y - dy)))
                top._kt_x, top._kt_y = top._kt_pos_gesetzt
                self._kt_zeichnen_anfordern(top)
                self._kt_layout_anfordern()
            return
        w = self._kt_maus_ziel
        if w is None or w._kt_zerstoert:
            return
        self._kt_maus_ereignis(w, "Motion", x, y)

    def _kt_k_maus_runter(self, _win, _x, _y, button, _mods):
        self._kt_bewegung_senden()              # pending move first (event order as under Tk)
        x, y = self._kt_maus_tk()
        if button in ("scrollup", "scrolldown", "scrollleft", "scrollright"):
            w = self._kt_widget_bei(x, y)
            if w is None:
                return
            delta = {"scrolldown": 120, "scrollup": -120}.get(button, 0)
            if button in ("scrollleft", "scrollright"):
                ev = self._kt_maus_ereignis(w, "MouseWheel", x, y,
                                         delta=120 if button == "scrollleft" else -120)
                ev.state |= EV.SHIFT
                return
            self._kt_maus_ereignis(w, "MouseWheel", x, y, delta=delta)
            return
        num = {"left": 1, "middle": 2, "right": 3, "mouse4": 4, "mouse5": 5}.get(button, 1)
        w = self._kt_widget_bei(x, y)
        if self._kt_leiste is not None and w is self and y < self._kt_client_dy() and num == 1:
            if self._kt_leiste.runter(x, y):
                self._kt_knoepfe.add(num)
                return
        if self._kt_popups:
            if w is None or not any(_ist_in(w, p) for p in self._kt_popups):
                from katiecad.ui.kt import klassen
                klassen.popup_schliessen()
                return                  # like Tk's grab: the click only closes the pop-up
        if w is None:
            self._kt_grab_klick_aussen()
            return
        top = w.winfo_toplevel()
        if isinstance(top, Toplevel) and num == 1:
            treffer = top._kt_titel_treffer(x, y)
            if treffer == "close":
                top._kt_schliessen_wunsch()
                return
            if treffer == "drag":
                top.lift()
                self._kt_titel_drag = (top, x - top._kt_x, y - top._kt_y)
                self._kt_knoepfe.add(num)
                return
        if isinstance(top, Toplevel) and not top._kt_ohne_rahmen:
            if self._kt_toplevels and self._kt_toplevels[-1] is not top:
                top.lift()
        self._kt_hover(w, x, y)
        t, lx, ly, ln, anz = self._kt_letzter_klick
        jetzt = time.monotonic()
        if ln == num and jetzt - t < 0.5 and abs(lx - x) < 5 and abs(ly - y) < 5:
            anz += 1
        else:
            anz = 1
        self._kt_letzter_klick = (jetzt, x, y, num, anz)
        ev_state = self._kt_modifier_state()
        self._kt_knoepfe.add(num)
        self._kt_maus_ziel = w
        ax, ay = w._kt_abs()
        ev = Event("ButtonPress", w, x=int(x - ax), y=int(y - ay), x_root=int(x), y_root=int(y),
                   num=num, state=ev_state, _kt_klicks=anz)
        self._kt_ausloesen(w, ev)

    def _kt_grab_klick_aussen(self):
        pass

    def _kt_k_maus_hoch(self, _win, _x, _y, button, _mods):
        self._kt_bewegung_senden()
        if button.startswith("scroll"):
            return
        x, y = self._kt_maus_tk()
        num = {"left": 1, "middle": 2, "right": 3, "mouse4": 4, "mouse5": 5}.get(button, 1)
        if self._kt_titel_drag is not None:
            self._kt_titel_drag = None
            self._kt_knoepfe.discard(num)
            return
        if self._kt_leiste is not None and self._kt_leiste.gedrueckt is not None:
            self._kt_knoepfe.discard(num)
            self._kt_leiste.los(x, y)
            return
        w = self._kt_maus_ziel
        state = self._kt_modifier_state()
        self._kt_knoepfe.discard(num)
        if w is not None and not w._kt_zerstoert:
            ax, ay = w._kt_abs()
            ev = Event("ButtonRelease", w, x=int(x - ax), y=int(y - ay), x_root=int(x),
                       y_root=int(y), num=num, state=state)
            self._kt_ausloesen(w, ev)
        if not self._kt_knoepfe:
            self._kt_maus_ziel = None
            neu = self._kt_widget_bei(x, y)
            self._kt_hover(neu, x, y)

    # -- keyboard
    def _kt_tasten_ziel(self):
        f = self._kt_fokus
        if f is not None and not f._kt_zerstoert:
            if self._kt_grab is None or _ist_in(f, self._kt_grab.winfo_toplevel()):
                return f
        if self._kt_grab is not None:
            return self._kt_grab.winfo_toplevel()
        for t in reversed(self._kt_toplevels):
            if t._kt_sichtbar and not t._kt_ohne_rahmen:
                return t
        return self

    def _kt_k_taste_runter(self, _win, key, scancode, codepoint, modifiers):
        self._kt_bewegung_senden()
        name = Window._system_keyboard.keycode_to_string(key) if hasattr(Window, "_system_keyboard") else ""
        shift = "shift" in modifiers
        keysym, char = EV.keysym_aus(name, codepoint, shift)
        state = self._kt_modifier_state()
        if state & EV.CONTROL and char and len(char) == 1 and char.isalpha():
            char = chr(ord(char.lower()) - 96)
        if keysym == "Tab" and shift:
            keysym = "ISO_Left_Tab" if False else "Tab"
        w = self._kt_tasten_ziel()
        ev = Event("KeyPress", w, keysym=keysym, char=char, keycode=key, state=state,
                   x_root=self._kt_maus_tk()[0], y_root=self._kt_maus_tk()[1])
        gebrochen = self._kt_ausloesen(w, ev)
        self._kt_text_erlaubt = not gebrochen
        if not gebrochen and keysym == "Tab" and not w._kt_zerstoert and not isinstance(w, Text):
            ziel = self._kt_fokus_nachbar(w, -1 if shift else 1)
            if ziel is not None:
                ziel.focus_set()
                if hasattr(ziel, "select_range"):
                    ziel.select_range(0, END)
        return True            # we handled it (no Kivy default like ESC = quit)

    def _kt_k_taste_hoch(self, _win, key, scancode=None, *a):
        name = Window._system_keyboard.keycode_to_string(key) if hasattr(Window, "_system_keyboard") else ""
        keysym, char = EV.keysym_aus(name, "", "shift" in (getattr(Window, "modifiers", []) or []))
        w = self._kt_tasten_ziel()
        ev = Event("KeyRelease", w, keysym=keysym, char=char, keycode=key,
                   state=self._kt_modifier_state())
        self._kt_ausloesen(w, ev)
        return True

    def _kt_k_text(self, _win, text):
        if not self._kt_text_erlaubt:
            return
        w = self._kt_tasten_ziel()
        f = getattr(w, "_kt_text_eingabe", None)
        if f is not None and not (self._kt_modifier_state() & EV.CONTROL):
            f(text)

    # -- focus
    def _kt_fokus_setzen(self, w):
        alt = self._kt_fokus
        if alt is w:
            return
        self._kt_fokus = w
        if alt is not None and not alt._kt_zerstoert:
            alt._kt_zustand.discard("focus")
            alt._kt_fokus_aenderung()
            alt._kt_ereignis("FocusOut")
        if w is not None and not w._kt_zerstoert:
            w._kt_zustand.add("focus")
            w._kt_fokus_aenderung()
            top = w.winfo_toplevel()
            top._kt_letzter_fokus = w
            w._kt_ereignis("FocusIn")

    def _kt_fokus_zurueck(self):
        f = self._kt_fokus
        if f is not None and not f._kt_zerstoert:
            return
        self._kt_fokus = None
        for t in reversed([self] + self._kt_toplevels):
            if t._kt_sichtbar and not t._kt_zerstoert and not t._kt_ohne_rahmen:
                lf = t._kt_letzter_fokus
                if lf is not None and not lf._kt_zerstoert:
                    self._kt_fokus_setzen(lf)
                return

    def _kt_fokus_nachbar(self, w, richtung):
        top = w.winfo_toplevel()
        liste = []

        def sammeln(x):
            for c in x.children.values():
                if c._kt_ist_toplevel or c._kt_zerstoert:
                    continue
                if c._kt_lebt and c._kt_sichtbar:
                    if c._kt_nimmt_fokus():
                        liste.append(c)
                    sammeln(c)
        sammeln(top)
        if not liste:
            return None
        if w in liste:
            i = (liste.index(w) + richtung) % len(liste)
        else:
            i = 0
        return liste[i]

    def _kt_k_fenster_fokus(self, _win, an):
        f = self._kt_fokus
        if f is None or f._kt_zerstoert:
            f = self
        if not an:
            f._kt_ereignis("FocusOut")
        else:
            f._kt_ereignis("FocusIn")

    def _kt_k_groesse(self, _win, w, h, erzwingen=False):
        if (int(w), int(h)) == (self._kt_fenster_w, self._kt_fenster_h) and not self._kt_layout_offen \
                and not erzwingen:
            return
        l, t, r, b = self._kt_rand
        self._kt_fenster_w, self._kt_fenster_h = int(w), int(h)
        self._kt_w = int(w) - l - r
        self._kt_h = int(h) - t - self._kt_titel_h - b
        if self._kt_leiste is not None:
            self._kt_leiste.zeichnen()
        self._kt_ebene.size = (w, h)
        self._kt_zeichnen_noetig = True
        self._kt_layout_anfordern()
        self._kt_spaeter(self, "Configure")
        for t in self._kt_toplevels:
            t._kt_zeichnen_noetig = True

    def _kt_k_schliessen(self, *_a, **_k):
        f = self._kt_protokolle.get("WM_DELETE_WINDOW")
        if f is not None:
            try:
                f()
            except Exception:
                import sys
                self.report_callback_exception(*sys.exc_info())
            return not self._kt_ende          # True = Kivy must not close by itself
        self.destroy()
        return False


_CURSOR = {"": "arrow", "arrow": "arrow", "left_ptr": "arrow", "crosshair": "crosshair",
           "tcross": "crosshair", "cross": "crosshair", "hand2": "hand", "hand1": "hand",
           "fleur": "size_all", "sizing": "size_all", "sb_h_double_arrow": "size_we",
           "sb_v_double_arrow": "size_ns", "size_we": "size_we", "size_ns": "size_ns",
           "watch": "wait", "xterm": "ibeam", "ibeam": "ibeam", "no": "no",
           "size_nw_se": "size_nwse", "size_ne_sw": "size_nesw", "bottom_right_corner": "size_nwse",
           "none": "arrow"}


def _ist_in(w, top):
    """Is w (or its toplevel) a descendant of top?"""
    while w is not None:
        if w is top:
            return True
        w = w.master
    return False


def _suchen(w, x, y):
    """Deepest visible child of w containing (x, y) (coordinates relative to w)."""
    kinder = [c for c in w.children.values()
              if not c._kt_ist_toplevel and c._kt_lebt and c._kt_sichtbar and not c._kt_zerstoert]
    dx, dy = w._kt_kind_versatz_x(), w._kt_kind_versatz_y()
    for c in reversed(kinder):
        cx, cy = c._kt_x + dx, c._kt_y + dy
        if cx <= x < cx + c._kt_w and cy <= y < cy + c._kt_h:
            return _suchen(c, x - cx, y - cy) or c
    return None


# ============================================================
# Toplevel
# ============================================================
class Toplevel(Wm, BaseWidget):
    _kt_klasse = "Toplevel"
    _kt_standard = {"background": "#f0f0f0", "borderwidth": 0, "highlightthickness": 0,
                 "relief": FLAT, "menu": ""}

    def __init__(self, master=None, cnf=None, **kw):
        self._kt_wm_init()
        BaseWidget.__init__(self, master, cnf, **kw)
        r = self._kt_root_
        self._kt_sichtbar = True
        self._kt_lebt = True
        self._kt_erst_gezeigt = False
        self._kt_titel = r._kt_titel or "tk"
        self._kt_titel_drag = None
        r._kt_toplevels.append(self)
        self._kt_anhaengen()
        self._kt_layout_planen()

    def _kt_kivy_eltern(self):
        return self._kt_root_._kt_ebene

    def _kt_anhaengen(self):
        ek = self._kt_kivy_eltern()
        if self._kt_k.parent is not ek:
            if self._kt_k.parent is not None:
                self._kt_k.parent.remove_widget(self._kt_k)
            ek.add_widget(self._kt_k)          # newest Toplevel on top
        self._kt_eltern_k = ek

    def lift(self, aboveThis=None):
        r = self._kt_root_
        if self in r._kt_toplevels:
            r._kt_toplevels.remove(self)
            r._kt_toplevels.append(self)
        self._kt_abhaengen()
        self._kt_anhaengen()

    tkraise = lift

    def lower(self, belowThis=None):
        r = self._kt_root_
        if self in r._kt_toplevels:
            r._kt_toplevels.remove(self)
            r._kt_toplevels.insert(0, self)
        self._kt_abhaengen()
        ek = self._kt_kivy_eltern()
        ek.add_widget(self._kt_k, index=len(ek.children))
        self._kt_eltern_k = ek

    def _kt_fenster_zeigen(self, an):
        self._kt_sichtbar = an
        if an:
            self._kt_anhaengen()
            self._kt_layout_planen()
        else:
            self._kt_abhaengen()
            if self._kt_root_._kt_fokus is not None and _ist_in(self._kt_root_._kt_fokus, self):
                self._kt_root_._kt_fokus = None
                self._kt_root_._kt_fokus_zurueck()

    def _kt_client_dx(self):
        return 0 if self._kt_ohne_rahmen else 1

    def _kt_client_dy(self):
        return 0 if self._kt_ohne_rahmen else TITEL_H

    def _kt_aussen_w(self):
        return self._kt_w + (0 if self._kt_ohne_rahmen else 2)

    def _kt_aussen_h(self):
        return self._kt_h + (0 if self._kt_ohne_rahmen else TITEL_H + 1)

    def winfo_rootx(self):
        return int(self._kt_x + self._kt_client_dx())

    def winfo_rooty(self):
        return int(self._kt_y + self._kt_client_dy())

    def _kt_abs(self):
        return self._kt_x + self._kt_client_dx(), self._kt_y + self._kt_client_dy()

    def _kt_toplevel_anordnen(self):
        if not self._kt_sichtbar:
            return
        rw, rh = self._kt_req()
        if self._kt_geo_gesetzt:
            w, h = self._kt_geo_gesetzt
        else:
            w, h = rw, rh
        w = max(self._kt_minsize[0], min(self._kt_maxsize[0], w))
        h = max(self._kt_minsize[1], min(self._kt_maxsize[1], h))
        if self._kt_pos_gesetzt:
            x, y = self._kt_pos_gesetzt
        elif not self._kt_erst_gezeigt:
            r = self._kt_root_
            x = max(0, (r._kt_w - w) // 2)
            y = r._kt_client_dy() + max(0, (r._kt_h - h) // 3)
            self._kt_pos_gesetzt = (x, y)
        else:
            x, y = self._kt_x, self._kt_y
        self._kt_erst_gezeigt = True
        geaendert = (w, h) != (self._kt_w, self._kt_h)
        self._kt_x, self._kt_y, self._kt_w, self._kt_h = int(x), int(y), int(w), int(h)
        if geaendert:
            self._kt_zeichnen_noetig = True
            self._kt_root_._kt_spaeter(self, "Configure")
        self._kt_anordnen()

    def _kt_kivy_pos(self):
        return self._kt_x, _fh() - self._kt_y - self._kt_aussen_h()

    def _kt_darstellen(self):
        if not self._kt_sichtbar:
            return
        kx, ky = self._kt_kivy_pos()
        k = self._kt_k
        aw, ah = self._kt_aussen_w(), self._kt_aussen_h()
        if (k.x, k.y) != (kx, ky) or tuple(k.size) != (aw, ah):
            k.pos, k.size = (kx, ky), (aw, ah)
            self._kt_zeichnen_noetig = True
        if self._kt_zeichnen_noetig:
            self._kt_zeichnen_noetig = False
            g = self._kt_g_hinten
            g.clear()
            self._kt_g_inhalt.clear()
            bg = self._kt_farbe_opt("background", (0.94, 0.94, 0.94, 1))
            if not self._kt_ohne_rahmen:
                # shadow, frame, title bar
                g.add(Color(0, 0, 0, 0.35))
                g.add(Rectangle(pos=(kx + 4, ky - 4), size=(aw, ah)))
                rand = _heller(bg, 1.9) if sum(bg[:3]) < 1.2 else _heller(bg, 0.6)
                g.add(Color(*rand))
                g.add(Rectangle(pos=(kx, ky), size=(aw, ah)))
                titel_bg = _heller(bg, 0.7) if sum(bg[:3]) < 1.2 else _heller(bg, 0.9)
                g.add(Color(*titel_bg))
                g.add(Rectangle(pos=(kx + 1, ky + ah - TITEL_H), size=(aw - 2, TITEL_H - 1)))
                vg = (0.95, 0.95, 0.95, 1) if sum(bg[:3]) < 1.2 else (0.1, 0.1, 0.1, 1)
                tex = fontmod.text_textur(self._kt_titel, "TkDefaultFont")
                if tex is not None:
                    fontmod.text_zeichnen(g, tex, vg, (kx + 10, int(ky + ah - TITEL_H / 2 - tex.size[1] / 2)),
                                          tex.size)
                x_tex = fontmod.text_textur("✕", ("Segoe UI", 10))
                if x_tex is not None:
                    fontmod.text_zeichnen(g, x_tex, vg, (kx + aw - 22 - x_tex.size[0] / 2,
                                                         int(ky + ah - TITEL_H / 2 - x_tex.size[1] / 2)),
                                          x_tex.size)
                g.add(Color(*bg))
                g.add(Rectangle(pos=(kx + 1, ky + 1), size=(self._kt_w, self._kt_h)))
            else:
                g.add(Color(*bg))
                g.add(Rectangle(pos=(kx, ky), size=(self._kt_w, self._kt_h)))
                ht = _int(self._kt_o.get("highlightthickness", 0))
                if ht:
                    _rahmen(g, kx, ky, self._kt_w, self._kt_h, ht,
                            self._kt_farbe_opt("highlightbackground", (0, 0, 0, 1)))

    # -- title bar: drag / close
    def _kt_titel_treffer(self, x, y):
        """(x, y) window coordinates -> "close", "drag" or None."""
        if self._kt_ohne_rahmen:
            return None
        lx, ly = x - self._kt_x, y - self._kt_y
        if 0 <= ly < TITEL_H and 0 <= lx < self._kt_aussen_w():
            if lx >= self._kt_aussen_w() - 40:
                return "close"
            return "drag"
        return None

    def _kt_schliessen_wunsch(self):
        f = self._kt_protokolle.get("WM_DELETE_WINDOW")
        if f is not None:
            f()
        else:
            self.destroy()

    def destroy(self):
        if self._kt_zerstoert:
            return
        r = self._kt_root_
        if r._kt_grab is not None and _ist_in(r._kt_grab, self):
            r._kt_grab = None
        BaseWidget.destroy(self)


# ============================================================
# Frame / Label / Button
# ============================================================
class Frame(BaseWidget):
    _kt_klasse = "Frame"
    _kt_standard = {"background": "#f0f0f0", "borderwidth": 0, "relief": FLAT,
                 "highlightthickness": 0, "width": 0, "height": 0, "padx": 0, "pady": 0,
                 "cursor": ""}

    def _kt_innen(self):
        l, t, r, b = Misc._kt_innen(self)
        px, py = _int(self._kt_o.get("padx", 0)), _int(self._kt_o.get("pady", 0))
        return l + px, t + py, r + px, b + py


class LabelFrame(Frame):
    _kt_klasse = "Labelframe"
    _kt_standard = dict(Frame._kt_standard, text="", borderwidth=2, relief=GROOVE, font="TkDefaultFont",
                     foreground="#000000", labelanchor="nw")

    def _kt_innen(self):
        l, t, r, b = Frame._kt_innen(self)
        if self._kt_o.get("text"):
            t += fontmod.zeilen_hoehe(self._kt_o.get("font"))
        return l, t, r, b


class _TextBild:
    """Text and/or image content as Label and Button have it."""

    def _kt_anzeige_text(self):
        var = self._kt_o.get("textvariable")
        if isinstance(var, Variable):
            return str(var._kt_roh())
        t = self._kt_o.get("text", "")
        return "" if t is None else str(t)

    def _kt_zeilen(self):
        text = self._kt_anzeige_text()
        font = self._kt_o.get("font")
        wl = _mass(self._kt_o.get("wraplength", 0) or 0)
        if wl > 0:
            return fontmod.umbrechen(text, font, wl)
        return text.split("\n") if text else []

    def _kt_bild(self):
        b = self._kt_o.get("image")
        if isinstance(b, (tuple, list)):
            b = b[0] if b else None
        if isinstance(b, str):
            b = _BILDER.get(b)
        return b if b else None

    def _kt_inhalt_groesse(self):
        font = self._kt_o.get("font")
        zeilen = self._kt_zeilen()
        lh = fontmod.zeilen_hoehe(font)
        tw = max([fontmod.text_breite(z, font) for z in zeilen] or [0])
        th = lh * max(1, len(zeilen))            # Tk keeps one line even for an empty text
        bild = self._kt_bild()
        comp = self._kt_o.get("compound", "none") or "none"
        if bild is not None:
            bw, bh = bild.width(), bild.height()
            if comp in ("none", "", None) or not zeilen:
                return bw, bh, True, False
            if comp in ("left", "right"):
                return bw + tw + 2, max(bh, th), True, True
            if comp in ("top", "bottom"):
                return max(bw, tw), bh + th + 2, True, True
            return max(bw, tw), max(bh, th), True, True
        return tw, th, False, True

    def _kt_zeichne_inhalt(self, g, kx, ky, fg, x0, y0, bw_, bh_):
        """Text/image into the box (x0, y0, bw_, bh_) using anchor/justify."""
        font = self._kt_o.get("font")
        zeilen = self._kt_zeilen()
        lh = fontmod.zeilen_hoehe(font)
        cw, ch, mit_bild, mit_text = self._kt_inhalt_groesse()
        anchor = self._kt_o.get("anchor", "center") or "center"
        if anchor in ("n", "center", "s"):
            x = x0 + (bw_ - cw) // 2
        elif "w" in anchor:
            x = x0
        else:
            x = x0 + bw_ - cw
        if anchor in ("w", "center", "e"):
            y = y0 + (bh_ - ch) // 2
        elif "n" in anchor:
            y = y0
        else:
            y = y0 + bh_ - ch
        bild = self._kt_bild()
        comp = self._kt_o.get("compound", "none") or "none"
        tx, ty = x, y
        if mit_bild and bild is not None:
            bw, bh = bild.width(), bild.height()
            if not mit_text or comp in ("none", "", None):
                ix, iy = x + (cw - bw) // 2, y + (ch - bh) // 2
                mit_text = False
            elif comp == "left":
                ix, iy = x, y + (ch - bh) // 2
                tx = x + bw + 2
            elif comp == "right":
                ix, iy = x + cw - bw, y + (ch - bh) // 2
            elif comp == "top":
                ix, iy = x + (cw - bw) // 2, y
                ty = y + bh + 2
            elif comp == "bottom":
                ix, iy = x + (cw - bw) // 2, y + ch - bh
            else:
                ix, iy = x + (cw - bw) // 2, y + (ch - bh) // 2
            tex = bild._kt_textur()
            if tex is not None:
                g.add(Color(1, 1, 1, 0.45 if "disabled" in self._kt_zustand else 1))
                g.add(Rectangle(texture=tex, pos=(int(kx + ix), int(ky + self._kt_h - iy - bh)),
                                size=(bw, bh)))
        if mit_text and zeilen:
            tw_max = max(fontmod.text_breite(z, font) for z in zeilen)
            just = self._kt_o.get("justify", "center") or "center"
            if comp in ("top", "bottom") and mit_bild:
                tx = x + (cw - tw_max) // 2
            for i, z in enumerate(zeilen):
                zw = fontmod.text_breite(z, font)
                if just == "center":
                    zx = tx + (tw_max - zw) // 2
                elif just == "right":
                    zx = tx + tw_max - zw
                else:
                    zx = tx
                self._kt_text_zeichnen(g, z, font, fg, zx, ty + i * lh, "nw", kx, ky)


class Label(_TextBild, BaseWidget):
    _kt_klasse = "Label"
    _kt_standard = {"background": "#f0f0f0", "foreground": "#000000", "text": "", "font": "TkDefaultFont",
                 "borderwidth": 0, "relief": FLAT, "highlightthickness": 0, "padx": 1, "pady": 1,
                 "anchor": "center", "justify": "center", "wraplength": 0, "width": 0,
                 "height": 0, "image": "", "compound": "none", "cursor": "",
                 "activebackground": "#ececec", "activeforeground": "#000000",
                 "disabledforeground": "#a3a3a3", "state": NORMAL}

    def _kt_innen(self):
        b = _int(self._kt_o.get("borderwidth", 0)) + _int(self._kt_o.get("highlightthickness", 0))
        return b, b, b, b

    def _kt_natuerlich(self):
        cw, ch, mit_bild, _mt = self._kt_inhalt_groesse()
        font = self._kt_o.get("font")
        b = self._kt_innen()[0]
        px, py = _int(self._kt_o.get("padx", 1)), _int(self._kt_o.get("pady", 1))
        wz = _int(self._kt_o.get("width", 0))
        hz = _int(self._kt_o.get("height", 0))
        if wz:
            cw = wz if mit_bild else wz * fontmod.text_breite("0", font)
        if hz:
            ch = hz if mit_bild else hz * fontmod.zeilen_hoehe(font)
        return cw + 2 * px + 2 * b, ch + 2 * py + 2 * b

    def _kt_malen(self, kx, ky):
        aktiv = "active" in self._kt_zustand and self._kt_o.get("state") == ACTIVE
        bg = self._kt_farbe_opt("activebackground" if aktiv else "background")
        self._kt_hintergrund(kx, ky, bg)
        fg = self._kt_farbe_opt("disabledforeground" if "disabled" in self._kt_zustand else
                             ("activeforeground" if aktiv else "foreground"), (0, 0, 0, 1))
        b = self._kt_innen()[0]
        px, py = _int(self._kt_o.get("padx", 1)), _int(self._kt_o.get("pady", 1))
        self._kt_zeichne_inhalt(self._kt_g_inhalt, kx, ky, fg, b + px, b + py,
                             self._kt_w - 2 * (b + px), self._kt_h - 2 * (b + py))

    def _kt_hover_aenderung(self):
        pass

    def _kt_fokus_aenderung(self):
        if _int(self._kt_o.get("highlightthickness", 0)):
            self._kt_neu_zeichnen()

    def _kt_nimmt_fokus(self):
        return False


class Message(Label):
    _kt_klasse = "Message"


class Button(Label):
    _kt_klasse = "Button"
    _kt_hover_aktiv = True
    _kt_standard = dict(Label._kt_standard, borderwidth=2, relief=RAISED, padx=8, pady=2,
                     highlightthickness=1, command=None, overrelief="")

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__(master, cnf, **kw)
        self._kt_gedrueckt = False
        self.bind_class_intern()

    def bind_class_intern(self):
        pass

    def invoke(self):
        c = self._kt_o.get("command")
        if c and "disabled" not in self._kt_zustand:
            return c()

    def flash(self):
        pass

    def _kt_hover_aenderung(self):
        self._kt_neu_zeichnen()

    def _kt_malen(self, kx, ky):
        aktiv = "active" in self._kt_zustand and "disabled" not in self._kt_zustand
        bg = self._kt_farbe_opt("activebackground" if aktiv else "background")
        relief = SUNKEN if self._kt_zustand & {"pressed"} else self._kt_o.get("relief", RAISED)
        alt = self._kt_o.get("relief")
        self._kt_o["relief"] = relief
        self._kt_hintergrund(kx, ky, bg)
        self._kt_o["relief"] = alt
        fg = self._kt_farbe_opt("disabledforeground" if "disabled" in self._kt_zustand else
                             ("activeforeground" if aktiv else "foreground"), (0, 0, 0, 1))
        b = self._kt_innen()[0]
        px, py = _int(self._kt_o.get("padx", 1)), _int(self._kt_o.get("pady", 1))
        self._kt_zeichne_inhalt(self._kt_g_inhalt, kx, ky, fg, b + px, b + py,
                             self._kt_w - 2 * (b + px), self._kt_h - 2 * (b + py))

    def _kt_nimmt_fokus(self):
        return "disabled" not in self._kt_zustand


class Checkbutton(Button):
    _kt_klasse = "Checkbutton"
    _kt_standard = dict(Label._kt_standard, onvalue=1, offvalue=0, variable=None, command=None,
                     indicatoron=1, selectcolor="#ffffff")


class Radiobutton(Button):
    _kt_klasse = "Radiobutton"
    _kt_standard = dict(Label._kt_standard, value="", variable=None, command=None, indicatoron=1,
                     selectcolor="#ffffff")


# ============================================================
# Scrollbar (tk) - drawn like the ttk one
# ============================================================
class Scrollbar(BaseWidget):
    _kt_klasse = "Scrollbar"
    _kt_hover_aktiv = True
    _kt_standard = {"orient": VERTICAL, "command": None, "background": "#d9d9d9",
                 "troughcolor": "#c3c3c3", "width": 14, "borderwidth": 0,
                 "highlightthickness": 0, "activebackground": "#ececec", "cursor": ""}

    def __init__(self, master=None, cnf=None, **kw):
        self._kt_anteil = (0.0, 1.0)
        self._kt_drag = None
        super().__init__(master, cnf, **kw)

    def set(self, first, last):
        self._kt_anteil = (float(first), float(last))
        self._kt_neu_zeichnen()

    def get(self):
        return self._kt_anteil

    def _kt_farben(self):
        return (self._kt_farbe_opt("troughcolor", (0.8, 0.8, 0.8, 1)),
                self._kt_farbe_opt("activebackground" if "active" in self._kt_zustand else "background",
                                (0.6, 0.6, 0.6, 1)))

    def _kt_natuerlich(self):
        b = _int(self._kt_o.get("width", 14))
        return (b, 20) if self._kt_o.get("orient") == VERTICAL else (20, b)

    def _kt_griff(self):
        a, e = self._kt_anteil
        lang = self._kt_h if self._kt_o.get("orient") == VERTICAL else self._kt_w
        p0 = int(a * lang)
        p1 = max(p0 + 12, int(e * lang))
        return p0, min(lang, p1), lang

    def _kt_malen(self, kx, ky):
        trog, griff = self._kt_farben()
        g = self._kt_g_hinten
        g.add(Color(*trog))
        g.add(Rectangle(pos=(kx, ky), size=(self._kt_w, self._kt_h)))
        p0, p1, _l = self._kt_griff()
        g.add(Color(*griff))
        if self._kt_o.get("orient") == VERTICAL:
            g.add(Rectangle(pos=(kx + 2, ky + self._kt_h - p1), size=(self._kt_w - 4, p1 - p0)))
        else:
            g.add(Rectangle(pos=(kx + p0, ky + 2), size=(p1 - p0, self._kt_h - 4)))

    def _kt_hover_aenderung(self):
        self._kt_neu_zeichnen()

    def _kt_fokus_aenderung(self):
        pass

    def _kt_nimmt_fokus(self):
        return False

    # driven by the class bindings in klassen.py
    def _kt_befehl(self, *args):
        c = self._kt_o.get("command")
        if c:
            c(*args)


# ============================================================
# Menu (data model; shown by the menu renderer in klassen.py)
# ============================================================
class Menu(BaseWidget):
    _kt_klasse = "Menu"
    _kt_standard = {"tearoff": 1, "background": "#f0f0f0", "foreground": "#000000",
                 "activebackground": "#0078d7", "activeforeground": "#ffffff",
                 "disabledforeground": "#6d6d6d", "font": "TkMenuFont", "borderwidth": 1,
                 "relief": FLAT, "postcommand": None, "selectcolor": "#000000",
                 "activeborderwidth": 0, "tearoffcommand": None, "title": "", "type": "normal"}

    def __init__(self, master=None, cnf=None, **kw):
        self._kt_eintraege = []
        super().__init__(master, cnf, **kw)

    def _kt_req(self):
        return (1, 1)

    # -- entries
    def _kt_neu(self, typ, cnf, kw, index=None):
        if cnf:
            kw = {**cnf, **kw}
        e = {"type": typ, "label": "", "accelerator": "", "state": NORMAL, "command": None,
             "underline": -1, "image": "", "compound": "none", "font": "", "foreground": "",
             "background": "", "columnbreak": 0, "hidemargin": 0}
        if typ == "checkbutton":
            e.update(onvalue=1, offvalue=0, variable=None)
        if typ == "radiobutton":
            e.update(value=kw.get("label", ""), variable=None)
        if typ == "cascade":
            e["menu"] = ""
        for k, v in kw.items():
            if k == "menu" and v is not None:
                v = str(v)
            e[k] = v
        if typ == "checkbutton" and e.get("variable") is None:
            e["variable"] = BooleanVar(value=False)
        if index is None:
            self._kt_eintraege.append(e)
        else:
            self._kt_eintraege.insert(index, e)

    def add(self, itemType, cnf=None, **kw):
        self._kt_neu(itemType, cnf, kw)

    def add_command(self, cnf=None, **kw):
        self._kt_neu("command", cnf, kw)

    def add_cascade(self, cnf=None, **kw):
        self._kt_neu("cascade", cnf, kw)

    def add_checkbutton(self, cnf=None, **kw):
        self._kt_neu("checkbutton", cnf, kw)

    def add_radiobutton(self, cnf=None, **kw):
        self._kt_neu("radiobutton", cnf, kw)

    def add_separator(self, cnf=None, **kw):
        self._kt_neu("separator", cnf, kw)

    def insert(self, index, itemType, cnf=None, **kw):
        self._kt_neu(itemType, cnf, kw, self._kt_idx(index))

    def insert_command(self, index, cnf=None, **kw):
        self.insert(index, "command", cnf, **kw)

    def insert_separator(self, index, cnf=None, **kw):
        self.insert(index, "separator", cnf, **kw)

    def insert_cascade(self, index, cnf=None, **kw):
        self.insert(index, "cascade", cnf, **kw)

    def insert_checkbutton(self, index, cnf=None, **kw):
        self.insert(index, "checkbutton", cnf, **kw)

    def _kt_idx(self, index):
        n = len(self._kt_eintraege)
        if index in (END, "last"):
            return n - 1 if n else None
        if index == "active":
            return None
        if isinstance(index, int):
            return index
        s = str(index)
        if s.isdigit():
            return int(s)
        if s.startswith("@"):
            return None
        for i, e in enumerate(self._kt_eintraege):
            if e.get("label") == s:
                return i
        for i, e in enumerate(self._kt_eintraege):
            if str(e.get("label", "")).startswith(s):
                return i
        raise TclError(f'bad menu entry index "{index}"')

    def index(self, index):
        if index in (END, "last"):
            return len(self._kt_eintraege) - 1 if self._kt_eintraege else None
        return self._kt_idx(index)

    def delete(self, index1, index2=None):
        i1 = self._kt_idx(index1)
        if i1 is None:
            return
        i2 = self._kt_idx(index2) if index2 is not None else i1
        if i2 is None:
            i2 = len(self._kt_eintraege) - 1
        del self._kt_eintraege[i1:i2 + 1]

    def entrycget(self, index, option):
        i = self._kt_idx(index)
        if i is None or i >= len(self._kt_eintraege):
            raise TclError(f'bad menu entry index "{index}"')
        e = self._kt_eintraege[i]
        if option not in e:
            raise TclError(f'unknown option "-{option}"')
        v = e[option]
        return "" if v is None else v

    def entryconfigure(self, index, cnf=None, **kw):
        if cnf:
            kw = {**cnf, **kw}
        i = self._kt_idx(index)
        if i is None:
            return
        e = self._kt_eintraege[i]
        if not kw:
            return {k: (k, "", "", "", v) for k, v in e.items()}
        for k, v in kw.items():
            if k == "menu" and v is not None:
                v = str(v)
            e[k] = v

    entryconfig = entryconfigure

    def type(self, index):
        i = self._kt_idx(index)
        if i is None:
            raise TclError(f'bad menu entry index "{index}"')
        if self._kt_o.get("tearoff") and False:
            pass
        return self._kt_eintraege[i]["type"]

    def invoke(self, index):
        i = self._kt_idx(index)
        if i is None:
            return
        e = self._kt_eintraege[i]
        if e.get("state") == DISABLED:
            return
        typ = e["type"]
        var = e.get("variable")
        if isinstance(var, str):
            var = _VARS.get(var)
        if typ == "checkbutton" and var is not None:
            an = str(var._kt_roh()) == str(e.get("onvalue", 1)) or var._kt_roh() is True and e.get("onvalue", 1) in (1, True)
            var.set(e.get("offvalue", 0) if an else e.get("onvalue", 1))
            if isinstance(var, BooleanVar) and e.get("onvalue", 1) in (1, True):
                var.set(not an)
        elif typ == "radiobutton" and var is not None:
            var.set(e.get("value"))
        c = e.get("command")
        if c:
            return c()

    def tk_popup(self, x, y, entry=""):
        from katiecad.ui.kt import klassen
        klassen.menue_zeigen(self, x, y)

    post = tk_popup

    def unpost(self):
        from katiecad.ui.kt import klassen
        klassen.menue_schliessen(self)

    def activate(self, index):
        pass

    def yposition(self, index):
        return 0

    def _kt_natuerlich(self):
        return (1, 1)

    def _kt_malen(self, kx, ky):
        pass

    def _kt_hover_aenderung(self):
        pass

    def _kt_fokus_aenderung(self):
        pass

    def _kt_nimmt_fokus(self):
        return False


class OptionMenu(Button):
    def __init__(self, master, variable, value, *values, **kw):
        super().__init__(master, textvariable=variable)
        self._kt_menu = Menu(self, tearoff=0)
        for v in (value,) + values:
            self._kt_menu.add_radiobutton(label=v, variable=variable, value=v,
                                       command=kw.get("command") and (lambda v=v: kw["command"](v)))
        self.configure(command=lambda: self._kt_menu.tk_popup(self.winfo_rootx(),
                                                           self.winfo_rooty() + self.winfo_height()))


# ============================================================
# PhotoImage
# ============================================================
_BILDER = {}
_bild_zaehler = [0]


class Image:
    pass


class PhotoImage(Image):
    def __init__(self, name=None, cnf=None, master=None, **kw):
        if cnf:
            kw = {**cnf, **kw}
        _bild_zaehler[0] += 1
        self.name = name or f"pyimage{_bild_zaehler[0]}"
        self._kt_pil = None
        self._kt_tex = None
        self._kt_datei = None
        from PIL import Image as _PI
        data = kw.get("data")
        datei = kw.get("file")
        if data is not None:
            import base64
            import io
            roh = data if isinstance(data, (bytes, bytearray)) else str(data).encode("ascii")
            try:
                roh = base64.b64decode(roh, validate=False)
            except Exception:
                pass
            self._kt_pil = _PI.open(io.BytesIO(roh)).convert("RGBA")
        elif datei is not None:
            self._kt_datei = str(datei)
            self._kt_pil = _PI.open(self._kt_datei).convert("RGBA")
        else:
            w, h = int(kw.get("width", 1) or 1), int(kw.get("height", 1) or 1)
            self._kt_pil = _PI.new("RGBA", (w, h), (0, 0, 0, 0))
        _BILDER[self.name] = self

    @classmethod
    def _kt_aus_pil(cls, bild):
        p = cls.__new__(cls)
        _bild_zaehler[0] += 1
        p.name = f"pyimage{_bild_zaehler[0]}"
        p._kt_pil = bild.convert("RGBA")
        p._kt_tex = None
        p._kt_datei = getattr(bild, "filename", None) or None
        _BILDER[p.name] = p
        return p

    def __str__(self):
        return self.name

    def width(self):
        return self._kt_pil.size[0]

    def height(self):
        return self._kt_pil.size[1]

    def _kt_textur(self):
        if self._kt_tex is None:
            from kivy.graphics.texture import Texture
            w, h = self._kt_pil.size
            t = Texture.create(size=(w, h), colorfmt="rgba")
            t.blit_buffer(self._kt_pil.tobytes(), colorfmt="rgba", bufferfmt="ubyte")
            t.flip_vertical()
            t.mag_filter = "nearest" if max(w, h) <= 64 else "linear"
            self._kt_tex = t
        return self._kt_tex

    def _kt_geaendert(self):
        self._kt_tex = None
        r = _base.ROOT[0]
        if r is not None:
            r._kt_alles_ungueltig()

    def zoom(self, x, y=""):
        y = y or x
        from PIL import Image as _PI
        w, h = self._kt_pil.size
        return PhotoImage._kt_aus_pil(self._kt_pil.resize((w * int(x), h * int(y)), _PI.Resampling.NEAREST))

    def subsample(self, x, y=""):
        y = y or x
        w, h = self._kt_pil.size
        return PhotoImage._kt_aus_pil(self._kt_pil.resize((max(1, w // int(x)), max(1, h // int(y)))))

    def copy(self):
        return PhotoImage._kt_aus_pil(self._kt_pil.copy())

    def put(self, data, to=None):
        if isinstance(data, str) and data.startswith("#") and to:
            f = _base.farbe(data)
            x0, y0 = to[0], to[1]
            x1, y1 = (to[2], to[3]) if len(to) >= 4 else (x0 + 1, y0 + 1)
            from PIL import ImageDraw
            ImageDraw.Draw(self._kt_pil).rectangle(
                (x0, y0, x1 - 1, y1 - 1), fill=tuple(int(c * 255) for c in f[:3]) + (255,))
        self._kt_geaendert()

    def get(self, x, y):
        return self._kt_pil.getpixel((x, y))[:3]

    def blank(self):
        from PIL import Image as _PI
        self._kt_pil = _PI.new("RGBA", self._kt_pil.size, (0, 0, 0, 0))
        self._kt_geaendert()

    def configure(self, **kw):
        if "file" in kw or "data" in kw:
            neu = PhotoImage(**kw)
            self._kt_pil = neu._kt_pil
            self._kt_geaendert()

    config = configure

    def write(self, filename, format=None, from_coords=None):
        self._kt_pil.save(filename)

    def type(self):
        return "photo"


class BitmapImage(PhotoImage):
    pass


def image_names():
    return tuple(_BILDER)


def mainloop(n=0):
    r = _base.ROOT[0]
    if r is not None:
        r.mainloop()


NoDefaultRoot = lambda: None


_default_root = None


from katiecad.ui.kt.canvas import Canvas            # noqa: E402
from katiecad.ui.kt.eingabe import Entry, Text, Listbox, Spinbox, Scale   # noqa: E402
