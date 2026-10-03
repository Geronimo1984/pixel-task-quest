#!/usr/bin/env python3
"""Рисует иконку и собирает «Task Quest.app» (все скины в одном приложении) рядом со скриптом.

Запуск:  python3 build_app.py
После этого приложение можно перетащить в «Программы» или в Dock.
"""
import os
import shutil
import subprocess
import sys
import tkinter as tk

import pixel_tracker as pt
import task_quest

HERE = os.path.dirname(os.path.abspath(__file__))
APPS = [
    # имя приложения, скрипт, функция иконки, id бандла, png-иконка для README
    ("Task Quest", "task_quest.py", task_quest.icon_grid_universal, "local.taskquest", "icon.png"),
]

INFO_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>{name}</string>
  <key>CFBundleDisplayName</key><string>{name}</string>
  <key>CFBundleIdentifier</key><string>{bundle_id}</string>
  <key>CFBundleVersion</key><string>2.0</string>
  <key>CFBundleShortVersionString</key><string>2.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>launcher</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
"""


def build(name, script, grid_fn, bundle_id, png):
    app = os.path.join(HERE, name + ".app")
    iconset = os.path.join(HERE, "AppIcon.iconset")
    os.makedirs(iconset, exist_ok=True)
    for size in (16, 32, 128, 256, 512):
        pt.icon_photo(size, grid_fn).write(os.path.join(iconset, f"icon_{size}x{size}.png"), format="png")
        pt.icon_photo(size * 2, grid_fn).write(os.path.join(iconset, f"icon_{size}x{size}@2x.png"), format="png")
    pt.icon_photo(1024, grid_fn).write(os.path.join(HERE, png), format="png")

    if os.path.exists(app):
        shutil.rmtree(app)
    os.makedirs(os.path.join(app, "Contents", "MacOS"))
    os.makedirs(os.path.join(app, "Contents", "Resources"))
    subprocess.run(["iconutil", "-c", "icns", iconset, "-o",
                    os.path.join(app, "Contents", "Resources", "AppIcon.icns")], check=True)
    shutil.rmtree(iconset)

    with open(os.path.join(app, "Contents", "Info.plist"), "w", encoding="utf-8") as fh:
        fh.write(INFO_PLIST.format(name=name, bundle_id=bundle_id))
    launcher = os.path.join(app, "Contents", "MacOS", "launcher")
    with open(launcher, "w", encoding="utf-8") as fh:
        fh.write(f'#!/bin/zsh\nexec "{sys.executable}" "{os.path.join(HERE, script)}"\n')
    os.chmod(launcher, 0o755)
    subprocess.run(["touch", app])  # чтобы Finder сразу подхватил иконку
    print("Готово:", app)


def main():
    root = tk.Tk()
    root.withdraw()
    for args in APPS:
        build(*args)
    root.destroy()


if __name__ == "__main__":
    main()
