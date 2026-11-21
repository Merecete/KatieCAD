# -*- coding: utf-8 -*-
"""Collects the licence texts of the third-party packages that go into the program.

Run it in the build environment AFTER `pip install -r requirements.txt` and BEFORE PyInstaller:

    python tools/lizenzen_sammeln.py            # -> build/licenses/
    python tools/lizenzen_sammeln.py <folder>

The packages from requirements.txt and everything they need (recursively) are looked up in the
installed packages; for each one the licence/notice files shipped with the package are copied to
<folder>/<package>-<version>/ together with a short INFO.txt (name, version, licence, author).
The build scripts then add the folder to the program as `licenses/`.
Wheels such as Pillow or numpy bring licence files of the libraries they contain - these are
copied as well, which is exactly what the licences of those libraries require.
Packages that ship no licence file of their own get the texts kept in installer/lizenzen/
(see MITGELIEFERT below).
Exit code 1 if a package of requirements.txt is not installed or has no licence file.
"""
import os
import re
import shutil
import sys
from importlib import metadata

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Packages without licence files of their own: normalised name -> (files in installer/lizenzen,
# note for INFO.txt). Their licences still require the text to be shipped with the program.
MITGELIEFERT = {
    "kivy-deps-glew": (["GLEW-LICENSE.txt"],
                       "Licence text of GLEW (glew32.dll) from https://github.com/nigels-com/glew"),
    "kivy-deps-angle": (["ANGLE-LICENSE.txt"],
                        "Licence text of ANGLE (libEGL.dll, libGLESv2.dll) from "
                        "https://github.com/google/angle"),
    "pypiwin32": ([], "Empty compatibility package that only installs pywin32 - "
                      "its licence is in the pywin32 folder."),
}
_LIZENZORDNER = os.path.join(WURZEL, "installer", "lizenzen")
_LIZENZDATEI = re.compile(r"(^|/)(licen[sc]e|copying|notice|authors|copyright)[^/]*$", re.I)


def _name(zeile):
    m = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", zeile)
    return m.group(1) if m else None


def requirements_namen(pfad=None):
    pfad = pfad or os.path.join(WURZEL, "requirements.txt")
    out = []
    with open(pfad, encoding="utf-8") as f:
        for z in f:
            z = z.split("#")[0].strip()
            if z:
                n = _name(z)
                if n:
                    out.append(n)
    return out


def _norm(n):
    return re.sub(r"[-_.]+", "-", n).lower()


def abhaengigkeiten(namen):
    """-> {normalised name: Distribution} of the packages and everything they need (without extras)."""
    gefunden, fehlend, offen = {}, [], list(namen)
    while offen:
        n = offen.pop()
        k = _norm(n)
        if k in gefunden:
            continue
        try:
            d = metadata.distribution(n)
        except metadata.PackageNotFoundError:
            fehlend.append(n)
            continue
        gefunden[k] = d
        for r in d.requires or []:
            if "extra ==" in r.replace('"', "'").replace("  ", " ") or "extra==" in r.replace(" ", ""):
                continue                     # optional extras are not installed
            rn = _name(r)
            if rn:
                offen.append(rn)
    return gefunden, fehlend


def lizenz_dateien(dist):
    return [f for f in (dist.files or []) if _LIZENZDATEI.search(str(f).replace("\\", "/"))]


def lizenz_name(dist):
    md = dist.metadata
    return (md.get("License-Expression") or (md.get("License") or "").strip().split("\n")[0]
            or "; ".join(c.split("::")[-1].strip() for c in md.get_all("Classifier") or []
                         if c.startswith("License ::")) or "?")


def sammeln(ziel, namen=None):
    namen = namen or requirements_namen()
    pakete, fehlend = abhaengigkeiten(namen)
    if os.path.isdir(ziel):
        shutil.rmtree(ziel)
    os.makedirs(ziel)
    ohne = []
    with open(os.path.join(ziel, "VERSIONS.txt"), "w", encoding="utf-8") as vf:
        vf.write("Third-party packages included in this build (name, version, license)\n\n")
        for k in sorted(pakete):
            vf.write("%-28s %-12s %s\n" % (pakete[k].metadata["Name"], pakete[k].version,
                                           lizenz_name(pakete[k])))
    for k in sorted(pakete):
        d = pakete[k]
        ordner = os.path.join(ziel, "%s-%s" % (d.metadata["Name"], d.version))
        os.makedirs(ordner)
        dateien = lizenz_dateien(d)
        for f in dateien:
            shutil.copy2(str(d.locate_file(f)), os.path.join(ordner, os.path.basename(str(f))))
        eigene, hinweis = MITGELIEFERT.get(k, ([], None)) if not dateien else ([], None)
        for name in eigene:                  # licence text kept in installer/lizenzen
            shutil.copy2(os.path.join(_LIZENZORDNER, name), os.path.join(ordner, name))
        with open(os.path.join(ordner, "INFO.txt"), "w", encoding="utf-8") as fh:
            md = d.metadata
            fh.write("%s %s\nLicense: %s\nAuthor: %s\nHome page: %s\n" % (
                md["Name"], d.version, lizenz_name(d),
                md.get("Author") or md.get("Author-email") or "?", md.get("Home-page") or "?"))
            if hinweis:
                fh.write("\n%s\n" % hinweis)
        if not dateien and hinweis is None:
            ohne.append(md["Name"])
    return pakete, fehlend, ohne


def main(argv):
    ziel = argv[1] if len(argv) > 1 else os.path.join(WURZEL, "build", "licenses")
    pakete, fehlend, ohne = sammeln(ziel)
    for k in sorted(pakete):
        d = pakete[k]
        print("  %-28s %-12s %s" % (d.metadata["Name"], d.version, lizenz_name(d)))
    print("%d packages -> %s" % (len(pakete), ziel))
    if fehlend:
        print("NOT INSTALLED:", ", ".join(fehlend))
    if ohne:
        print("WITHOUT licence file:", ", ".join(ohne))
    return 1 if (fehlend or ohne) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
