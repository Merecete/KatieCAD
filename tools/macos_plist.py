# -*- coding: utf-8 -*-
"""Sets version/name in the Info.plist of the macOS app and signs it again
(ad hoc). Usage: python tools/macos_plist.py dist/KatieCAD.app <version>"""
import plistlib, subprocess, sys

app, ver = sys.argv[1], sys.argv[2]
pfad = app + "/Contents/Info.plist"
with open(pfad, "rb") as f:
    pl = plistlib.load(f)
pl["CFBundleShortVersionString"] = ver
pl["CFBundleVersion"] = ver
pl["CFBundleName"] = "KatieCAD"
pl["CFBundleDisplayName"] = "KatieCAD"
pl["NSHumanReadableCopyright"] = "BSD 3-Clause License - Merecete"
pl["CFBundleDocumentTypes"] = [        # double click on .cadjson / .katieprj opens KatieCAD
    {"CFBundleTypeName": "KatieCAD drawing", "CFBundleTypeRole": "Editor",
     "CFBundleTypeExtensions": ["cadjson"], "LSHandlerRank": "Owner"},
    {"CFBundleTypeName": "KatieCAD project", "CFBundleTypeRole": "Editor",
     "CFBundleTypeExtensions": ["katieprj"], "LSHandlerRank": "Owner"},
]
with open(pfad, "wb") as f:
    plistlib.dump(pl, f)
subprocess.run(["codesign", "--force", "--deep", "-s", "-", app], check=False)
print("Info.plist:", ver)
