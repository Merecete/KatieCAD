@echo off
rem Local build for Windows (run inside the repository folder):  installer\build_windows.bat
cd /d "%~dp0\.."
python -m venv .venv-build
call .venv-build\Scripts\activate
pip install -r requirements.txt pyinstaller
python tools\lizenzen_sammeln.py build\licenses || echo WARNING: licence texts incomplete - see message above
set DOCS=
if exist docs set DOCS=--add-data "docs;docs"
pyinstaller --noconfirm --windowed --name KatieCAD --icon KatieCAD.ico ^
  --additional-hooks-dir installer\hooks --collect-submodules katiecad --collect-submodules ezdxf --collect-submodules pypdf --collect-all ezdwg ^
  --add-data "symbols;symbols" --add-data "title_blocks;title_blocks" ^
  --add-data "report_templates;report_templates" --add-data "build\licenses;licenses" ^
  --add-data "LICENSE;." --add-data "THIRD_PARTY_NOTICES.txt;." %DOCS% ^
  --add-data "KatieCAD.ico;." --add-data "KatieCAD.png;." --add-data "KatieCAD_Maskottchen.png;." --add-data "KatieCAD_Banner.png;." --add-data "KatieCAD_Banner_dunkel.png;." main.py
echo Done: dist\KatieCAD\KatieCAD.exe  (next: Inno Setup, see docs\BUILD.md)
