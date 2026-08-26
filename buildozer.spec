[app]
title = Crazyy Simulation
package.name = crazyysimulation
package.domain = com.iambkram
source.dir = .
source.include_exts = py,png,jpg,jpeg,gif,webp,svg,kv,atlas,ttf,otf,mp3,ogg,wav,json,txt,ico,md
source.include_patterns = game_assets/*,pc/*,mobile/*,src/*,src/ai/*,src/ui/*
source.exclude_dirs = tests,bin,venv,.venv,.git,.idea,.vscode,.buildozer,dist,build
source.exclude_patterns = setup.py,main_pc.py,Crazyy-Simulation.spec
version = 1.0.0
# Landscape 800x600 logical playfield; pygame.SCALED letterboxes 19.5:9 / 20:9.
orientation = landscape
fullscreen = 1
requirements = python3,pygame,android,pyjnius,pymongo,dnspython,cryptography,bcrypt,python-dotenv,requests,certifi,google-auth,google-auth-oauthlib,oauthlib
presplash.filename =
icon.filename =
android.permissions = INTERNET,ACCESS_NETWORK_STATE,VIBRATE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True
android.logcat_filters = *:S python:D
android.entrypoint = org.kivy.android.PythonActivity
android.apptheme = "@android:style/Theme.NoTitleBar"
android.meta_data =
p4a.branch = master
# Root main.py is the mobile entry (Buildozer requires this filename).
# Do not change source.dir; keep shared engine under src/.

[buildozer]
log_level = 2
warn_on_root = 1
