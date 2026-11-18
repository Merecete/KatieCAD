"""Backup files (.bak) and autosave (fileio/sicherung.py) - without Tk."""
import os, sys, tempfile, json, time
sys.path.insert(0, ".")
from katiecad.fileio import sicherung as S

n = 0
def ok(c, t):
    global n
    n += 1
    assert c, t

with tempfile.TemporaryDirectory() as d:
    f = os.path.join(d, "a.cadjson")
    ok(S.bak_anlegen(f) is False, "no file -> no .bak")
    open(f, "w").write("v1")
    ok(S.bak_anlegen(f) and open(f + ".bak").read() == "v1", ".bak holds the old version")
    open(f, "w").write("v2"); S.bak_anlegen(f)
    ok(open(f + ".bak").read() == "v2" and not os.path.exists(f + ".bak.tmp"), "replaced, no leftovers")
    ln = os.path.join(d, "l.cadjson")
    try:
        os.symlink(f, ln); ok(S.bak_anlegen(ln) is False, "symlink is skipped")
    except OSError:
        pass
    ok(S.bak_anlegen(d) is False, "folder is skipped")
    ok(S.minuten_pruefen(None) == 10 and S.minuten_pruefen("x") == 10, "default")
    ok(S.minuten_pruefen(0) == 0 and S.minuten_pruefen(-5) == 0 and S.minuten_pruefen(9999) == S.MAX_MINUTEN, "limits")

    k = os.path.join(d, "cfg")
    ok(S.verwaiste(k) == [], "no folder")
    own = os.getpid()
    ok(S.schreiben(k, own, {"elemente": []}, "x.cadjson"), "write")
    ok(S.verwaiste(k) == [], "own process is not an orphan")
    tot = 2 ** 22 + 12345                                  # PID that does not exist
    while S._prozess_lebt(tot):
        tot += 1
    S.schreiben(k, tot, {"elemente": [1]}, "alt.cadjson")
    time.sleep(0.01)
    S.schreiben(k, tot + 1, {"elemente": [2]}, None)
    v = S.verwaiste(k)
    ok(len(v) == 2 and v[0][3] == {"elemente": [2]} and v[1][2] == "alt.cadjson", "orphans, newest first")
    open(os.path.join(S.ordner(k), "autosave_77.json"), "w").write("{kaputt")
    open(os.path.join(S.ordner(k), "autosave_x.json"), "w").write("{}")
    open(os.path.join(S.ordner(k), "autosave_78.json"), "w").write(json.dumps({"format": "fremd", "daten": {}}))
    ok(len(S.verwaiste(k)) == 2, "broken / foreign files are skipped")
    S.datei_entfernen(v[0][0]); ok(len(S.verwaiste(k)) == 1, "remove")
    S.loeschen(k, own); ok(not os.path.exists(os.path.join(S.ordner(k), "autosave_%d.json" % own)), "own deleted")
    S.loeschen(k, own)                                      # again: no error
    ok(S.schreiben(os.path.join(d, "f", "x"), own, {"a": object()}) is None, "unserialisable -> None")
    # only the newest orphan is parsed; defective ones are set aside
    k2 = os.path.join(d, "cfg2"); a_ = tot + 10
    S.schreiben(k2, a_, {"elemente": [1]}); os.utime(S._pfad(k2, a_), (1, 1))
    S.schreiben(k2, a_ + 1, {"elemente": [2]})
    v2 = S.verwaiste(k2, maximal=1)
    ok(len(v2) == 1 and v2[0][3] == {"elemente": [2]}, "maximal=1 -> newest only")
    S.beiseite_legen(v2[0][0])
    ok(os.path.exists(v2[0][0] + ".defekt") and len(S.verwaiste(k2)) == 1, "set aside: not offered again")
print("OK     test_sicherung - OK (%d Pruefungen)" % n)
