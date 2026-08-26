# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller config for Crazyy-Simulation.exe (PC edition)."""
import os

block_cipher = None
ROOT = os.path.abspath(SPECPATH)

datas = []
assets = os.path.join(ROOT, "game_assets")
if os.path.isdir(assets):
    datas.append((assets, "game_assets"))
icon = os.path.join(ROOT, "icon.ico")
if os.path.isfile(icon):
    datas.append((icon, "."))
env_file = os.path.join(ROOT, ".env")
if os.path.isfile(env_file):
    datas.append((env_file, "."))

a = Analysis(
    [os.path.join(ROOT, "main_pc.py")],
    pathex=[ROOT, os.path.join(ROOT, "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "game",
        "settings",
        "assets",
        "branding",
        "menu_battle",
        "vfx",
        "cloud_sync",
        "platform_config",
        "pc",
        "pc.windowing",
        "pc.controls",
        "mobile",
        "mobile.scaling",
        "mobile.lifecycle",
        "mobile.touch_hud",
        "ai",
        "ai.enemy_ai",
        "ui",
        "ui.auth_ui",
        "ui.level_select_ui",
        "ui.store_ui",
        "ui.settings_ui",
        "pymongo",
        "cryptography",
        "bcrypt",
        "dotenv",
        "google_auth_oauthlib",
        "google.auth",
        "requests",
        "pygame",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Crazyy-Simulation",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon if os.path.isfile(icon) else None,
)
