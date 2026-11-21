# -*- coding: utf-8 -*-
"""
katiecad/ui/kt/events.py - Tk event sequences and event objects on Kivy (BSD-3-Clause).

A binding like "<Control-Shift-Z>" is parsed once into (modifiers, type, detail). For a
real event every bind tag of the widget (widget, class, toplevel, "all") is searched for
the most specific matching binding, exactly like Tk does; "break" stops the chain.
"""

import time

# event.state bits (as Tk on Windows / X11)
SHIFT, LOCK, CONTROL, ALT = 0x1, 0x2, 0x4, 0x20000
B1, B2, B3 = 0x100, 0x200, 0x400
_BTN_BIT = {1: B1, 2: B2, 3: B3}

_TYPEN = {"ButtonPress": "ButtonPress", "Button": "ButtonPress", "ButtonRelease": "ButtonRelease",
          "Motion": "Motion", "Enter": "Enter", "Leave": "Leave", "MouseWheel": "MouseWheel",
          "KeyPress": "KeyPress", "Key": "KeyPress", "KeyRelease": "KeyRelease",
          "Configure": "Configure", "FocusIn": "FocusIn", "FocusOut": "FocusOut",
          "Destroy": "Destroy", "Map": "Map", "Unmap": "Unmap", "Visibility": "Visibility",
          "Expose": "Expose", "Activate": "Activate", "Deactivate": "Deactivate"}
_MODS = {"Control": CONTROL, "Shift": SHIFT, "Alt": ALT, "Lock": LOCK, "Command": CONTROL,
         "Meta": ALT, "Mod1": ALT, "Option": ALT,
         "B1": B1, "Button1": B1, "B2": B2, "Button2": B2, "B3": B3, "Button3": B3}

_cache = {}


class Muster:
    __slots__ = ("mods", "typ", "detail", "anzahl", "virtuell", "text")

    def __init__(self, mods, typ, detail, anzahl, virtuell, text):
        self.mods, self.typ, self.detail = mods, typ, detail
        self.anzahl, self.virtuell, self.text = anzahl, virtuell, text

    def gewicht(self):
        return (self.anzahl, self.detail is not None, bin(self.mods).count("1"))


def parse(seq):
    """'<Control-Button-1>' -> Muster (None for unknown sequences)."""
    m = _cache.get(seq)
    if m is not None or seq in _cache:
        return m
    m = None
    s = seq.strip()
    if s.startswith("<<") and s.endswith(">>"):
        m = Muster(0, "Virtual", s, 1, True, seq)
    elif s.startswith("<") and s.endswith(">"):
        teile = s[1:-1].split("-")
        mods, anzahl, typ, detail = 0, 1, None, None
        rest = []
        for t in teile:
            if not t:
                rest.append("-")          # "<minus>" would be written that way
                continue
            if typ is None and detail is None and t in _MODS:
                mods |= _MODS[t]
            elif typ is None and detail is None and t in ("Double", "Triple", "Quadruple"):
                anzahl = {"Double": 2, "Triple": 3, "Quadruple": 4}[t]
            elif typ is None and detail is None and t == "Any":
                pass
            elif typ is None and t in _TYPEN:
                typ = _TYPEN[t]
            else:
                rest.append(t)
        if rest:
            detail = "-".join(rest)
        if typ is None:
            if detail is not None and detail.isdigit() and len(detail) == 1 and detail in "12345":
                typ = "ButtonPress"           # "<1>", "<Double-1>"
            else:
                typ = "KeyPress"              # "<a>", "<Return>"
        if typ in ("ButtonPress", "ButtonRelease") and detail is not None:
            try:
                detail = int(detail)
            except ValueError:
                pass
        m = Muster(mods, typ, detail, anzahl, False, seq)
    else:                                     # a single printable character
        if len(s) == 1:
            m = Muster(0, "KeyPress", KEYSYM_VON_ZEICHEN.get(s, s), 1, False, seq)
    _cache[seq] = m
    return m


def passt(muster, ev):
    """Does the binding match the event? (extra modifiers are allowed, like Tk)."""
    if muster.typ != ev.type_name:
        return False
    if muster.mods & ev.state != muster.mods:
        return False
    if muster.typ in ("ButtonPress", "ButtonRelease"):
        if muster.detail is not None and muster.detail != ev.num:
            return False
        if muster.anzahl > 1 and getattr(ev, "_kt_klicks", 1) < muster.anzahl:
            return False
    elif muster.typ in ("KeyPress", "KeyRelease"):
        if muster.detail is not None and muster.detail != ev.keysym:
            return False
    elif muster.virtuell:
        return muster.text == ev._kt_virtuell
    return True


class Event:
    """What a Tk callback receives."""

    def __init__(self, type_name, widget, **kw):
        self.type_name = type_name
        self.type = type_name
        self.widget = widget
        self.x = self.y = 0
        self.x_root = self.y_root = 0
        self.num = "??"
        self.delta = 0
        self.keysym = "??"
        self.keycode = 0
        self.keysym_num = 0
        self.char = ""
        self.state = 0
        self.width = self.height = 0
        self.time = int(time.monotonic() * 1000)
        self.serial = 0
        self.focus = False
        self.send_event = False
        self._kt_virtuell = None
        self._kt_klicks = 1
        for k, v in kw.items():
            setattr(self, k, v)

    def __repr__(self):
        return f"<{self.type_name} event x={self.x} y={self.y} keysym={self.keysym}>"


# ------------------------------------------------------------
# Kivy key names -> Tk keysyms
# ------------------------------------------------------------
KEYSYM = {
    "enter": "Return", "return": "Return", "numpadenter": "KP_Enter", "escape": "Escape",
    "backspace": "BackSpace", "tab": "Tab", "delete": "Delete", "insert": "Insert",
    "home": "Home", "end": "End", "pageup": "Prior", "pagedown": "Next",
    "left": "Left", "right": "Right", "up": "Up", "down": "Down", "spacebar": "space",
    "shift": "Shift_L", "rshift": "Shift_R", "lctrl": "Control_L", "rctrl": "Control_R",
    "ctrl": "Control_L", "alt": "Alt_L", "ralt": "Alt_R", "alt-gr": "ISO_Level3_Shift",
    "capslock": "Caps_Lock", "numlock": "Num_Lock", "screenlock": "Scroll_Lock",
    "lsuper": "Super_L", "rsuper": "Super_R", "menu": "Menu", "print": "Print",
    "pause": "Pause", "pipe": "bar",
    "numpad0": "KP_0", "numpad1": "KP_1", "numpad2": "KP_2", "numpad3": "KP_3",
    "numpad4": "KP_4", "numpad5": "KP_5", "numpad6": "KP_6", "numpad7": "KP_7",
    "numpad8": "KP_8", "numpad9": "KP_9", "numpaddecimal": "KP_Decimal",
    "numpaddivide": "KP_Divide", "numpadmul": "KP_Multiply", "numpadsubstract": "KP_Subtract",
    "numpadadd": "KP_Add",
}
for _i in range(1, 25):
    KEYSYM[f"f{_i}"] = f"F{_i}"

KEYSYM_VON_ZEICHEN = {
    " ": "space", "!": "exclam", '"': "quotedbl", "#": "numbersign", "$": "dollar",
    "%": "percent", "&": "ampersand", "'": "apostrophe", "(": "parenleft", ")": "parenright",
    "*": "asterisk", "+": "plus", ",": "comma", "-": "minus", ".": "period", "/": "slash",
    ":": "colon", ";": "semicolon", "<": "less", "=": "equal", ">": "greater",
    "?": "question", "@": "at", "[": "bracketleft", "\\": "backslash", "]": "bracketright",
    "^": "asciicircum", "_": "underscore", "`": "grave", "{": "braceleft", "|": "bar",
    "}": "braceright", "~": "asciitilde", "ä": "adiaeresis", "ö": "odiaeresis",
    "ü": "udiaeresis", "Ä": "Adiaeresis", "Ö": "Odiaeresis", "Ü": "Udiaeresis",
    "ß": "ssharp", "§": "section", "°": "degree", "´": "acute",
}
_SHIFT_ZEICHEN = {"1": "!", "2": '"', "3": "§", "4": "$", "5": "%", "6": "&", "7": "/",
                  "8": "(", "9": ")", "0": "=", "ß": "?", "+": "*", "#": "'", "-": "_",
                  ",": ";", ".": ":", "<": ">"}


def keysym_aus(name, codepoint, shift):
    """(Kivy key name, codepoint, shift) -> (keysym, char)."""
    if name in KEYSYM:
        ks = KEYSYM[name]
        ch = {"Return": "\r", "KP_Enter": "\r", "Escape": "\x1b", "BackSpace": "\x08",
              "Tab": "\t", "space": " ", "Delete": "\x7f"}.get(ks, "")
        return ks, ch
    ch = codepoint or (name if name and len(name) == 1 else "")
    if not ch:
        return (name or "??"), ""
    if len(ch) == 1 and ch.isalpha():
        ch = ch.upper() if shift else ch.lower()
        return KEYSYM_VON_ZEICHEN.get(ch, ch), ch
    if shift and ch in _SHIFT_ZEICHEN:
        ch = _SHIFT_ZEICHEN[ch]
    return KEYSYM_VON_ZEICHEN.get(ch, ch), ch
