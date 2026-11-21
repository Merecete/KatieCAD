# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('symbols', 'symbols'), ('title_blocks', 'title_blocks'), ('report_templates', 'report_templates'), ('build/licenses', 'licenses'), ('LICENSE', '.'), ('THIRD_PARTY_NOTICES.txt', '.'), ('docs', 'docs'), ('KatieCAD.ico', '.'), ('KatieCAD.png', '.'), ('KatieCAD_Maskottchen.png', '.'), ('KatieCAD_Banner.png', '.'), ('KatieCAD_Banner_dunkel.png', '.')]
binaries = []
hiddenimports = []
hiddenimports += collect_submodules('katiecad')
hiddenimports += collect_submodules('ezdxf')
hiddenimports += collect_submodules('pypdf')
tmp_ret = collect_all('ezdwg')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['installer/hooks'],          # Kivy: SDL2 / GLEW / ANGLE libraries
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='KatieCAD',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['KatieCAD.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='KatieCAD',
)
