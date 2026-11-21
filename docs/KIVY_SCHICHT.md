# Die Kivy-Schicht (`katiecad/ui/kt/`)

Dieses Dokument richtet sich an alle, die am Code von KatieCAD arbeiten. Es erklärt, wie
die Oberfläche auf Kivy läuft, obwohl das Programm gegen die **tkinter**-Schnittstelle
geschrieben ist, wo welcher Teil liegt und worauf man beim Ändern achten muss.

## Grundidee in einem Satz

Das gesamte Programm (`katiecad/ui/app.py`, Dialoge, Seitenleiste …) ruft ganz normal
`tkinter`, `tkinter.ttk`, `tkinter.font` usw. auf. Beim Start ersetzt
`katiecad/ui/kt/installieren()` diese Module in `sys.modules` durch eigene Module, die
dieselbe Schnittstelle anbieten, aber mit Kivy (OpenGL) zeichnen. **Die Programmlogik
merkt davon nichts** – sie bleibt reiner Tk-Code.

```
 app.py, dialogs.py, …     import tkinter as tk; tk.Canvas(...).create_line(...)
            │
            ▼
 sys.modules["tkinter"]  ──►  katiecad/ui/kt/tkmod.py   (statt des echten tkinter)
 sys.modules["tkinter.ttk"] ► katiecad/ui/kt/ttkmod.py
            │
            ▼
 Kivy: ein Fenster, Uhr (Clock), Maus/Tastatur, OpenGL-Zeichenbefehle
```

## Tk oder Kivy – wer entscheidet?

`katiecad/ui/kt/__init__.py`, Funktion `oberflaeche_waehlen()` (aufgerufen ganz am Anfang
von `main.py` / `katiecad/__main__.py`):

| Situation | Ergebnis |
|---|---|
| normal | Kivy |
| Umgebungsvariable `KATIECAD_UI=tk` | echtes Tk wie früher |
| Kivy fehlt oder kann kein OpenGL-Fenster öffnen | automatisch echtes Tk |
| `KATIECAD_TITELLEISTE=system` | Kivy, aber mit der Titelleiste des Betriebssystems |

Die Tk-Variante ist **keine Altlast**, sondern die Rückfallebene: Auf Rechnern ohne
brauchbares OpenGL startet KatieCAD damit trotzdem. Sie darf deshalb nicht entfernt werden,
und neuer Programmcode muss weiterhin unter beiden Oberflächen laufen.

Zum Vergleichen und Fehlersuchen einfach beide Varianten starten:

```powershell
python main.py
$env:KATIECAD_UI = "tk"; python main.py
```

Im Logbuch steht beim Start, welche Oberfläche läuft (`[KatieCAD] Oberflaeche: Kivy, Text: GDI (wie Tk)`).

## Die Dateien

| Datei | Inhalt |
|---|---|
| `__init__.py` | Auswahl Tk/Kivy, Kivy-Konfiguration, Einsetzen der Module in `sys.modules` |
| `_base.py` | gemeinsamer Zustand: das eine Hauptfenster (`ROOT`), Farbumrechnung, Skalierung |
| `tkmod.py` | das Modul `tkinter`: `Tk`, `Toplevel`, `Frame`, `Label`, `Button`, `Menu`, Variablen, `after`, Ereignisverteilung, Fokus |
| `ttkmod.py` | das Modul `tkinter.ttk`: `Style` und alle ttk-Widgets, gezeichnet wie Tks Thema „clam“ |
| `canvas.py` | `tk.Canvas` – die Zeichenfläche des CAD-Programms, der leistungskritische Teil |
| `geometry.py` | die Layout-Manager `pack`, `grid`, `place` (nach Tks eigenen Algorithmen) |
| `events.py` | Ereignis-Sequenzen wie `"<Control-Shift-Z>"` zerlegen und zuordnen, `Event`-Objekte |
| `klassen.py` | Klassenbindungen (Button klickt, Entry nimmt Tasten an …), Kontextmenüs, Combobox-Listen |
| `eingabe.py` | Texteingabe: `Entry`, `Text`, `Listbox` |
| `fontmod.py` | `tkinter.font`: Schriftangaben auflösen, Text messen, Text als Textur |
| `gdi_text.py` | Windows: Text mit GDI/ClearType zeichnen, damit er so scharf aussieht wie unter Tk |
| `dlgmod.py` | `filedialog`, `colorchooser` (systemeigene Dialoge), `messagebox`, `simpledialog` |
| `titelleiste.py` | eigene Titelleiste des Hauptfensters inkl. Knopf „über alle Monitore“ |

Dazu gehört `installer/hooks/hook-katiecad.ui.kt.py`: Er sorgt dafür, dass PyInstaller die
Kivy-Bibliotheken (SDL2, GLEW, ANGLE) in die fertige `KatieCAD.exe` packt.

## Namenskonventionen

* **`_kt_…`** – alles Interne der Schicht. Die Vorsilbe verhindert Namenskonflikte: Das
  Programm leitet eigene Klassen von `tk.Frame`, `tk.Toplevel` usw. ab und vergibt dort
  eigene Attribute; ohne Vorsilbe würde es versehentlich Interna der Schicht überschreiben.
  **Neue interne Attribute und Methoden immer mit `_kt_` beginnen.**
* **`_kt_k_…`** – Methoden, die Kivy direkt aufruft (Maus, Tastatur, Fenstergröße,
  Schließen). Sie stehen in `Tk` (tkmod.py) und übersetzen Kivy-Ereignisse in Tk-Ereignisse.
* **`_kt_o`** – die Tk-Optionen eines Widgets (`background`, `text`, `relief` …) als dict;
  `config()`/`cget()` lesen und schreiben dort.
* **`_kt_x`, `_kt_y`, `_kt_w`, `_kt_h`** – Lage und Größe in Tk-Koordinaten (Pixel, y nach
  unten) relativ zum Elternwidget; `_kt_abs()` liefert die Lage im Fenster.
* Die übrigen Namen sind wie im restlichen Projekt deutsch (`zeichnen`, `anordnen`,
  `darstellen`, `ausloesen` …); Kommentare und Docstrings sind englisch.

## Wie ein Bild entsteht

Tk zeichnet „wenn es Zeit hat“, und genauso arbeitet die Schicht:

1. Eine Änderung (z. B. `label.config(text=…)`, `pack()`, `canvas.create_line(…)`) zeichnet
   **nicht sofort**, sondern merkt nur vor: `_kt_layout_planen()` (Größe/Lage könnte sich
   ändern) oder `_kt_neu_zeichnen()` (nur das Aussehen ändert sich).
2. Vor dem nächsten Kivy-Bild läuft `Tk._kt_layout_jetzt()`:
   * `_kt_anordnen()` berechnet mit pack/grid/place (geometry.py) alle Größen und Lagen,
   * `_kt_zeichnen_tick()` → `_kt_darstellen()` jedes sichtbaren Widgets: Es baut seine
     Kivy-Zeichenbefehle neu, aber nur, wenn es vorgemerkt ist,
   * danach werden gesammelte `<Configure>`-Ereignisse verschickt
     (`_kt_ereignisse_senden`), wie Tk sie nach einer Größenänderung schickt.
3. Kivy zeigt das Bild mit OpenGL an.

`update()` und `update_idletasks()` erzwingen Schritt 2 sofort, wie unter Tk.

### Die Zeichenfläche (`canvas.py`)

Die Zeichenfläche ist der Grund für die Umstellung (Geschwindigkeit). Wichtig:

* Jedes Canvas-Element behält Tks Modell (Nummer, Tags, Reihenfolge, Koordinaten mit y nach
  unten). Gezeichnet wird aber **nicht Element für Element**: Erst beim nächsten Bild werden
  die Elemente in Blöcken von 400 zusammengefasst und gleichfarbige Linien, Flächen und
  Punkte mit NumPy zu wenigen großen Kivy-`Mesh`-Objekten verbaut (`_kt_bauen`,
  `_block_bauen`, `_lauf_meshes`). Tausende Linien kosten so nur wenige GPU-Aufrufe.
* Jedes Bild ist **vollständig und exakt** – es wird beim Zoomen nichts weggelassen oder
  vereinfacht. Diese Anforderung ist bewusst so festgelegt; Beschleunigungen dürfen das
  Aussehen nicht verändern.
* Linienenden, Ecken und gefüllte Kreise werden so berechnet, dass sie pixelgenau wie unter
  Tk (Windows-GDI) aussehen (`_dicke_mesh`, `_fugen`, `_ovale_boxen`). Das Canvas ist um einen
  halben Pixel verschoben, Texte werden dafür zurückverschoben – sonst wirken 1-Pixel-Linien
  unscharf.
* Texte gehen über `fontmod.text_zeichnen` (unter Windows über GDI mit ClearType).

## Wie ein Mausklick ankommt

1. Kivy ruft `Tk._kt_k_maus_runter()` auf.
2. Die Schicht sucht das Widget unter der Maus (`_kt_widget_bei`); solange eine Taste
   gedrückt ist, gehen alle Bewegungen an dieses Widget (`_kt_maus_ziel`, wie Tks
   „impliziter Grab“).
3. Ein `Event` wird gebaut und `Tk._kt_ausloesen()` sucht in den **Bindtags** des Widgets
   (Widget → Klasse → Toplevel → `"all"`) jeweils die genaueste passende Bindung
   (events.py). Gibt eine Funktion `"break"` zurück, ist Schluss – exakt Tks Regel.
4. Mausbewegungen werden zusammengefasst (`_kt_bewegung_senden`): Bei einer langsamen
   Zeichnung wird nur die letzte Position verarbeitet, statt hinterherzuhinken.

Die Standardreaktionen der Widgets (Button wird gedrückt, Entry nimmt ein Zeichen an,
Scrollbar scrollt) sind – wie in Tk – Bindungen auf den Klassennamen und stehen in
`klassen.py`.

## Fenster, Dialoge, Menüs

* Kivy hat **ein** Fenster pro Programm. Das Hauptfenster (`Tk`) ist dieses Fenster;
  jedes `Toplevel` (Dialog, Werkzeugfenster) wird **innerhalb** davon gezeichnet, mit
  eigener Titelleiste zum Verschieben. `overrideredirect`-Toplevels (Popups, Tooltips)
  haben keine.
* Datei- und Farbauswahl bleiben die Dialoge des Betriebssystems: `dlgmod.py` öffnet sie
  über ein unsichtbares echtes Tk.
* Kontextmenüs (`Menu.tk_popup`) und Combobox-Listen sind Popups aus `klassen.py`. Die
  Menüleiste zeichnet KatieCAD selbst (`katiecad/ui/menuleiste.py`).

## Bekannte Unterschiede zu Tk – und wie sie abgefangen sind

Diese Stellen haben schon Fehler verursacht; wer dort ändert, sollte sie kennen:

* **`tk_popup` wartet nicht.** Unter Tk blockiert ein Kontextmenü, bis etwas gewählt ist;
  hier kehrt es sofort zurück. Das Programm schließt bei jedem Mausklick alle offenen Menüs
  (`app.py`, `_menues_schliessen_binden`). Damit ein Menü nicht im selben Klick wieder
  zugeht, merkt sich `menue_zeigen()` das auslösende Ereignis (`_kt_gepostet_bei`), und
  `menue_schliessen()` ignoriert Klicks, die in ein offenes Menü gehen.
* **Wahrheitswerte von Variablen.** Tk speichert `BooleanVar(True)` als `1`; `getvar()` /
  `globalgetvar()` liefern deshalb `1`/`0` (`_tcl_wert`), sonst fehlen Häkchen im Menü.
* **Widgets nicht während eines Maus-Zugs neu erzeugen.** Wird das Widget zerstört, unter
  dem die Maustaste gedrückt wurde, geht der Zug verloren (`_kt_widget_weg` löscht
  `_kt_maus_ziel`). Beispiel: Trenner der Kacheln und Tabs werden beim Ziehen nur neu
  angeordnet, nicht neu gebaut.
* **Gemeinsame ctypes-Funktionen.** `ctypes.windll.user32` ist prozessweit; setzt ein Modul
  `argtypes`, gilt das für alle. `titelleiste.py` benutzt deshalb eine eigene
  `ctypes.WinDLL("user32")`.

## Eine fehlende Tk-Funktion ergänzen

1. Unter Tk nachsehen, was die Funktion genau tut (Rückgabewerte, Sonderfälle) – das
   Programm verlässt sich darauf.
2. In der passenden Datei ergänzen (Widget-Methoden meist in `tkmod.py`, Klasse `Misc`
   oder das Widget selbst; Canvas in `canvas.py`; ttk in `ttkmod.py`).
3. Ändert sie Größe oder Lage: `self._kt_layout_planen()`; ändert sie nur das Aussehen:
   `self._kt_neu_zeichnen()`. Nie direkt zeichnen.
4. Beide Oberflächen starten und vergleichen (`KATIECAD_UI=tk`).

## Prüfen

* `python tests/run_all.py` – alle Tests (laufen mit der Kivy-Schicht).
* `tests/test_ansicht_perf.py` – Zeitmessung des Neuzeichnens.
* Im Programm: *Einstellungen › Zeichengeschwindigkeit anzeigen (Messung)* schreibt die Zeichenzeiten in die
  Statuszeile.
