#!/bin/sh
# Builds a single-file AppImage from the PyInstaller output (dist/KatieCAD).
# Usage: installer/build_appimage.sh <version> [arch]      (arch: x86_64 (default) or aarch64)
# Needs: dist/KatieCAD (run PyInstaller first); curl, wget or python3 to download appimagetool. appimagetool is downloaded if it is not
# found in PATH or via the APPIMAGETOOL variable. No FUSE needed (extract-and-run).
set -e
VER="$1"; ARCH="${2:-x86_64}"
[ -n "$VER" ] || { echo "Usage: $0 <version> [arch]"; exit 1; }
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ -x "$ROOT/dist/KatieCAD/KatieCAD" ] || { echo "dist/KatieCAD/KatieCAD missing - run PyInstaller first"; exit 1; }
APPDIR="$ROOT/build/KatieCAD.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/lib/katiecad" "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/icons/hicolor/256x256/apps"
cp -r "$ROOT/dist/KatieCAD/." "$APPDIR/usr/lib/katiecad/"
cp "$ROOT/KatieCAD.png" "$APPDIR/katiecad.png"
cp "$ROOT/KatieCAD.png" "$APPDIR/.DirIcon"
cp "$ROOT/KatieCAD.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/katiecad.png"
cat > "$APPDIR/katiecad.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=KatieCAD
GenericName=Electrical CAD
Comment=2D/3D CAD for electrical engineering
Exec=KatieCAD %F
Icon=katiecad
Terminal=false
Categories=Graphics;Engineering;Electronics;
Keywords=CAD;electrical;schematic;switchgear;DXF;
StartupWMClass=KatieCAD
DESK
mkdir -p "$APPDIR/usr/share/metainfo"
sed -e "s/@VERSION@/$VER/" -e "s/@DATE@/$(date -u +%Y-%m-%d)/" \
    "$ROOT/installer/io.github.merecete.KatieCAD.metainfo.xml" \
    > "$APPDIR/usr/share/metainfo/io.github.merecete.KatieCAD.appdata.xml"
cp "$APPDIR/katiecad.desktop" "$APPDIR/usr/share/applications/katiecad.desktop"
cat > "$APPDIR/AppRun" <<'RUN'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/lib/katiecad/KatieCAD" "$@"
RUN
chmod +x "$APPDIR/AppRun"

# appimagetool: fixed release + SHA-256 check (no unchecked "continuous" download)
AIT_VER="1.9.0"
case "$ARCH" in
  x86_64)  AIT_SHA="46fdd785094c7f6e545b61afcfb0f3d98d8eab243f644b4b17698c01d06083d1" ;;
  aarch64) AIT_SHA="04f45ea45b5aa07bb2b071aed9dbf7a5185d3953b11b47358c1311f11ea94a96" ;;
  *)       AIT_SHA="" ;;
esac
sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1
  else python3 -c "import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], 'rb').read()).hexdigest())" "$1"
  fi
}
TOOL="${APPIMAGETOOL:-$(command -v appimagetool || true)}"
if [ -z "$TOOL" ]; then
  if [ -z "$AIT_SHA" ]; then
    echo "No checksum known for architecture $ARCH. Install appimagetool yourself and set APPIMAGETOOL=/path/to/appimagetool"
    exit 1
  fi
  TOOL="$ROOT/build/appimagetool-$AIT_VER-$ARCH.AppImage"
  if [ -f "$TOOL" ] && [ "$(sha256_of "$TOOL")" != "$AIT_SHA" ]; then
    rm -f "$TOOL"
  fi
  if [ ! -f "$TOOL" ]; then
    URL="https://github.com/AppImage/appimagetool/releases/download/$AIT_VER/appimagetool-$ARCH.AppImage"
    mkdir -p "$ROOT/build"
    if command -v curl >/dev/null 2>&1; then
      curl -fsSL -o "$TOOL" "$URL"
    elif command -v wget >/dev/null 2>&1; then
      wget -q -O "$TOOL" "$URL"
    elif command -v python3 >/dev/null 2>&1; then
      python3 -c "import sys, urllib.request as u; u.urlretrieve(sys.argv[1], sys.argv[2])" "$URL" "$TOOL"
    else
      echo "Neither curl, wget nor python3 found. Download $URL manually, make it executable"
      echo "and run:  APPIMAGETOOL=/path/to/appimagetool.AppImage sh installer/build_appimage.sh $VER"
      exit 1
    fi
    if [ "$(sha256_of "$TOOL")" != "$AIT_SHA" ]; then
      echo "Checksum of the downloaded appimagetool does not match - file deleted."
      rm -f "$TOOL"
      exit 1
    fi
  fi
  chmod +x "$TOOL"
fi
command -v file >/dev/null 2>&1 || { echo "The 'file' command is required by appimagetool. Debian/Ubuntu: sudo apt install file"; exit 1; }
mkdir -p "$ROOT/release"
OUT="$ROOT/release/KatieCAD-${VER}-Linux-${ARCH}.AppImage"
ARCH="$ARCH" APPIMAGE_EXTRACT_AND_RUN=1 "$TOOL" --no-appstream "$APPDIR" "$OUT"
chmod +x "$OUT"
echo "Done: $OUT"
