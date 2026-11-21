# -*- coding: utf-8 -*-
"""
katiecad/ui/kt/klassen.py - the class bindings of the Kivy layer (BSD-3-Clause).

Under Tk, buttons click, entries take keys and scroll bars scroll through bindings on
their class ("TButton", "TEntry" ...), which run after the widget's own bindings. The same
is done here, so a widget binding that returns "break" still stops the default behaviour.
Pop-ups (combobox lists, context menus) are overrideredirect Toplevels that close on a
click outside of them.
"""

from katiecad.ui.kt import tkmod as T, fontmod, events as EV


def _knopf_druck(ev):
    w = ev.widget
    if "disabled" in w._kt_zustand:
        return
    w._kt_zustand.add("pressed")
    w._kt_neu_zeichnen()


def _knopf_los(ev):
    w = ev.widget
    war = "pressed" in w._kt_zustand
    w._kt_zustand.discard("pressed")
    w._kt_neu_zeichnen()
    if war and 0 <= ev.x < w._kt_w and 0 <= ev.y < w._kt_h and "disabled" not in w._kt_zustand:
        w.invoke()


def _knopf_taste(ev):
    if ev.keysym in ("space",) or (ev.keysym in ("Return", "KP_Enter") and ev.widget._kt_klasse == "TButton"):
        ev.widget.invoke()


def _edit_druck(ev):
    w = ev.widget
    if "disabled" in w._kt_zustand:
        return
    if isinstance(w, _ttk().Combobox):
        a = w._kt_rechts()
        if ev.x >= w._kt_w - a - 2 or "readonly" in w._kt_zustand:
            w.focus_set()
            w._kt_aufklappen()
            return
    if isinstance(w, _ttk().Spinbox):
        a = w._kt_rechts()
        if ev.x >= w._kt_w - a - 2:
            w.focus_set()
            w._kt_schritt(1 if ev.y < w._kt_h / 2 else -1)
            return
    w._kt_maus_runter(ev)


def _edit_zug(ev):
    w = ev.widget
    if hasattr(w, "_kt_maus_ziehen") and "disabled" not in w._kt_zustand:
        w._kt_maus_ziehen(ev)


def _edit_taste(ev):
    w = ev.widget
    tt = _ttk()
    if isinstance(w, tt.Combobox) and ev.keysym in ("Down",) and not ev.state & EV.CONTROL:
        w._kt_aufklappen()
        return
    if isinstance(w, tt.Spinbox) and ev.keysym in ("Up", "Down"):
        w._kt_schritt(1 if ev.keysym == "Up" else -1)
        return
    w._kt_taste(ev)


def _rad_scrollen(ev):
    w = ev.widget
    n = -1 if ev.delta > 0 else 1
    try:
        w.yview_scroll(n * (1 if isinstance(w, T.Text) else 3 if isinstance(w, T.Listbox) else 3), "units")
    except Exception:
        pass


def _canvas_bewegung(ev):
    w = ev.widget
    w._kt_maus = (w.canvasx(ev.x), w.canvasy(ev.y))
    w._kt_tag_ereignis(ev)


def _canvas_tag(ev):
    ev.widget._kt_tag_ereignis(ev)


def _ttk():
    from katiecad.ui.kt import ttkmod
    return ttkmod


def installieren(root):
    k = root._kt_bind_klassen

    def setzen(klasse, seq, f):
        k.setdefault(klasse, {}).setdefault(seq, []).append(f)

    for kl in ("Button", "TButton", "Toolbutton"):
        setzen(kl, "<ButtonPress-1>", _knopf_druck)
        setzen(kl, "<ButtonRelease-1>", _knopf_los)
        setzen(kl, "<KeyPress>", _knopf_taste)
    for kl in ("TCheckbutton", "TRadiobutton", "Checkbutton", "Radiobutton", "TMenubutton"):
        setzen(kl, "<ButtonPress-1>", _knopf_druck)
        setzen(kl, "<ButtonRelease-1>", _knopf_los)
        setzen(kl, "<KeyPress>", lambda e: e.keysym == "space" and e.widget.invoke())
    for kl in ("Entry", "TEntry", "TCombobox", "TSpinbox", "Spinbox", "Text"):
        setzen(kl, "<ButtonPress-1>", _edit_druck)
        setzen(kl, "<B1-Motion>", _edit_zug)
        setzen(kl, "<KeyPress>", _edit_taste)
    setzen("Text", "<MouseWheel>", _rad_scrollen)
    setzen("TSpinbox", "<MouseWheel>",
           lambda e: e.widget._kt_schritt(1 if e.delta > 0 else -1) if e.widget.focus_get() is e.widget else None)
    setzen("Listbox", "<ButtonPress-1>", lambda e: e.widget._kt_klick(e))
    setzen("Listbox", "<KeyPress>", lambda e: e.widget._kt_taste(e))
    setzen("Listbox", "<MouseWheel>", _rad_scrollen)
    setzen("Treeview", "<ButtonPress-1>", lambda e: e.widget._kt_klick(e))
    setzen("Treeview", "<KeyPress>", lambda e: e.widget._kt_taste(e))
    setzen("Treeview", "<MouseWheel>", lambda e: e.widget.yview_scroll(-1 if e.delta > 0 else 1, "units"))
    for kl in ("TScrollbar", "Scrollbar"):
        setzen(kl, "<ButtonPress-1>", lambda e: e.widget._kt_klick(e) if hasattr(e.widget, "_kt_klick")
               else _tk_scrollbar_klick(e))
        setzen(kl, "<B1-Motion>", lambda e: e.widget._kt_ziehen(e) if hasattr(e.widget, "_kt_ziehen") else None)
        setzen(kl, "<ButtonRelease-1>", lambda e: e.widget._kt_los(e) if hasattr(e.widget, "_kt_los") else None)
    setzen("TNotebook", "<ButtonPress-1>", lambda e: e.widget._kt_klick(e))
    setzen("Canvas", "<Motion>", _canvas_bewegung)
    for seq in ("<ButtonPress>", "<ButtonRelease>", "<Double-ButtonPress>"):
        setzen("Canvas", seq, _canvas_tag)


def _tk_scrollbar_klick(e):
    w = e.widget
    vert = w._kt_o.get("orient") == T.VERTICAL
    p = e.y if vert else e.x
    p0, p1, _l = w._kt_griff()
    if p < p0:
        w._kt_befehl("scroll", -1, "pages")
    elif p > p1:
        w._kt_befehl("scroll", 1, "pages")


# ============================================================
# Pop-ups
# ============================================================
_offen = []          # open pop-up Toplevels (stack)


def popup_schliessen():
    while _offen:
        p = _offen.pop()
        ziel = getattr(p, "_kt_besitzer", None)
        try:
            p.destroy()
        except Exception:
            pass
        if ziel is not None:
            ziel._kt_popup = None
    r = T._base.ROOT[0]
    if r is not None:
        r._kt_popups = []


def _popup_neu(besitzer, x, y, w, h):
    r = T._base.ROOT[0]
    top = T.Toplevel(besitzer)
    top.overrideredirect(True)
    top._kt_besitzer = besitzer
    top.geometry(f"{max(1, w)}x{max(1, h)}+{int(x)}+{int(y)}")
    _offen.append(top)
    r._kt_popups = list(_offen)
    return top


def _opt(r, endung, standard):
    for k, v in r._kt_optionen.items():
        if k.endswith(endung):
            return v
    return standard


def combobox_aufklappen(cb):
    r = cb._kt_root_
    popup_schliessen()
    werte = cb._kt_werte()
    if not werte:
        return
    font = cb._kt_font()
    zh = fontmod.zeilen_hoehe(font) + 2
    n = min(len(werte), max(1, T._int(cb._kt_o.get("height", 10))))
    h = n * zh + 4
    x, y = cb.winfo_rootx(), cb.winfo_rooty() + cb.winfo_height()
    if y + h > r._kt_h:
        y = max(0, cb.winfo_rooty() - h)
    top = _popup_neu(cb, x, y, cb.winfo_width(), h)
    top.configure(background="#000000")
    lb = T.Listbox(top, font=font, height=n, exportselection=False, borderwidth=0,
                   highlightthickness=0, activestyle="none",
                   background=_opt(r, "Listbox.background", "#ffffff"),
                   foreground=_opt(r, "Listbox.foreground", "#000000"),
                   selectbackground=_opt(r, "Listbox.selectBackground", "#4a6984"),
                   selectforeground=_opt(r, "Listbox.selectForeground", "#ffffff"))
    sb = None
    if len(werte) > n:
        sb = _ttk().Scrollbar(top, orient=T.VERTICAL, command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        sb.pack(side=T.RIGHT, fill=T.Y, pady=1, padx=(0, 1))
    lb.pack(side=T.LEFT, fill=T.BOTH, expand=True, padx=1, pady=1)
    for v in werte:
        lb.insert(T.END, v)
    try:
        i = werte.index(cb.get())
        lb.selection_set(i)
        lb.see(i)
        lb._kt_aktiv = i
    except ValueError:
        pass
    cb._kt_popup = top

    def waehlen(_e=None):
        sel = lb.curselection()
        popup_schliessen()
        if sel:
            cb._kt_waehlen(werte[sel[0]])
        else:
            cb.focus_set()
        return "break"

    def bewegung(e):
        i = lb.nearest(e.y)
        if (i,) != lb.curselection():
            lb._kt_gewaehlt = {i}
            lb._kt_aktiv = i
            lb._kt_neu_zeichnen()

    lb.bind("<Motion>", bewegung)
    lb.bind("<ButtonRelease-1>", waehlen)
    lb.bind("<Return>", waehlen)
    lb.bind("<KP_Enter>", waehlen)
    lb.bind("<Escape>", lambda e: (popup_schliessen(), cb.focus_set(), "break")[-1])
    lb.bind("<Tab>", waehlen)
    lb.focus_set()


# ------------------------------------------------------------ context menus (tk_popup)
def menue_schliessen(menu=None):
    """Closes the open context menu (only if it belongs to `menu`)."""
    if menu is not None and not any(getattr(p, "_kt_besitzer", None) is menu for p in _offen):
        return
    popup_schliessen()


def menue_zeigen(menu, x, y, ebene=0):
    if ebene == 0:
        popup_schliessen()
    pc = menu._kt_o.get("postcommand")
    if pc:
        pc()
    r = menu._kt_root_
    bg = menu._kt_o.get("background") or "#f0f0f0"
    fg = menu._kt_o.get("foreground") or "#000000"
    if menu._kt_o.get("background") == menu._kt_standard.get("background"):
        bg = _opt(r, "Menu.background", bg)
    if menu._kt_o.get("foreground") == menu._kt_standard.get("foreground"):
        fg = _opt(r, "Menu.foreground", fg)
    abg = menu._kt_o.get("activebackground")
    if abg == menu._kt_standard.get("activebackground"):
        abg = _opt(r, "Menu.activeBackground", abg)
    afg = menu._kt_o.get("activeforeground")
    if afg == menu._kt_standard.get("activeforeground"):
        afg = _opt(r, "Menu.activeForeground", afg)
    sperr = menu._kt_o.get("disabledforeground") or "#6d6d6d"
    font = menu._kt_o.get("font") or "TkMenuFont"
    zh = fontmod.zeilen_hoehe(font) + 8
    eintraege = menu._kt_eintraege
    breite_l = max([fontmod.text_breite(str(e.get("label", "")), font) for e in eintraege] or [40])
    breite_a = max([fontmod.text_breite(str(e.get("accelerator", "")), font) for e in eintraege] or [0])
    breite = 28 + breite_l + (24 + breite_a if breite_a else 0) + 24
    hoehe = 4
    zeilen = []
    for i, e in enumerate(eintraege):
        h = 7 if e["type"] == "separator" else zh
        zeilen.append((hoehe, hoehe + h, i))
        hoehe += h
    hoehe += 2
    x = max(0, min(int(x), r._kt_w - breite))
    y = max(0, min(int(y), r._kt_h - hoehe))
    top = _popup_neu(menu, x, y, breite, hoehe)
    top.configure(background=bg, highlightthickness=1, highlightbackground="#808080")
    cv = T.Canvas(top, background=bg, highlightthickness=1, highlightbackground="#808080",
                  width=breite - 2, height=hoehe - 2, borderwidth=0)
    cv.pack(fill=T.BOTH, expand=True)
    rects, texte = {}, {}
    for y0, y1, i in zeilen:
        e = eintraege[i]
        if e["type"] == "separator":
            cv.create_line(4, (y0 + y1) // 2, breite - 6, (y0 + y1) // 2, fill="#808080")
            continue
        rects[i] = cv.create_rectangle(2, y0, breite - 4, y1, fill=bg, outline="")
        farbe = sperr if e.get("state") == T.DISABLED else fg
        marke = ""
        var = e.get("variable")
        if isinstance(var, str):
            var = T._VARS.get(var)
        if e["type"] == "checkbutton" and var is not None:
            an = e.get("onvalue", 1)
            wert = var._kt_roh()
            if str(wert) == str(an) or (wert is True and an in (1, True)):
                marke = "✓"
        elif e["type"] == "radiobutton" and var is not None and str(var._kt_roh()) == str(e.get("value")):
            marke = "•"
        t1 = cv.create_text(10, (y0 + y1) // 2, text=marke, anchor="w", fill=farbe, font=font)
        t2 = cv.create_text(28, (y0 + y1) // 2, text=str(e.get("label", "")), anchor="w",
                            fill=farbe, font=font)
        rechts = str(e.get("accelerator", "")) + ("  ▸" if e["type"] == "cascade" else "")
        t3 = cv.create_text(breite - 12, (y0 + y1) // 2, text=rechts, anchor="e", fill=farbe, font=font)
        texte[i] = (t1, t2, t3)
    zustand = {"aktiv": None, "sub": None}

    def zeile_bei(py):
        for y0, y1, i in zeilen:
            if y0 <= py < y1 and eintraege[i]["type"] != "separator":
                return i
        return None

    def markieren(i):
        if zustand["aktiv"] == i:
            return
        for j in (zustand["aktiv"], i):
            if j is None or j not in rects:
                continue
            an = j == i and eintraege[j].get("state") != T.DISABLED
            cv.itemconfigure(rects[j], fill=abg if an else bg)
            farbe = (afg if an else (sperr if eintraege[j].get("state") == T.DISABLED else fg))
            for t in texte[j]:
                cv.itemconfigure(t, fill=farbe)
        zustand["aktiv"] = i
        # sub menu
        while len(_offen) > ebene + 1:
            p = _offen.pop()
            try:
                p.destroy()
            except Exception:
                pass
        r._kt_popups = list(_offen)
        if i is not None and eintraege[i]["type"] == "cascade" and eintraege[i].get("state") != T.DISABLED:
            try:
                sub = menu.nametowidget(eintraege[i].get("menu"))
            except KeyError:
                sub = None
            if sub is not None:
                y0 = next(z[0] for z in zeilen if z[2] == i)
                menue_zeigen(sub, x + breite - 4, y + y0, ebene + 1)

    def bewegung(e):
        markieren(zeile_bei(e.y))

    def klick(e):
        i = zeile_bei(e.y)
        if i is None:
            return
        en = eintraege[i]
        if en["type"] == "cascade" or en.get("state") == T.DISABLED:
            return
        popup_schliessen()
        menu.invoke(i)

    cv.bind("<Motion>", bewegung)
    cv.bind("<ButtonRelease-1>", klick)
    cv.bind("<ButtonRelease-3>", klick)
    top.bind("<Escape>", lambda e: popup_schliessen())
    if ebene == 0:
        cv.focus_set()
