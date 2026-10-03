#!/usr/bin/env python3
"""Рисует иконку и собирает «Pixel Task Quest.app» рядом со скриптом.

Запуск:  python3 build_app.py
После этого приложение можно перетащить в «Программы» или в Dock.
"""
import os
import shutil
import subprocess
import sys
import tkinter as tk

import pixel_tracker as pt

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "Pixel Task Quest.app")
SCRIPT = os.path.join(HERE, "pixel_tracker.py")

INFO_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Pixel Task Quest</string>
  <key>CFBundleDisplayName</key><string>Pixel Task Quest</string>
  <key>CFBundleIdentifier</key><string>local.pixeltaskquest</string>
  <key>CFBundleVersion</key><string>1.1</string>
  <key>CFBundleShortVersionString</key><string>1.1</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>launcher</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
"""


def main():
    root = tk.Tk()
    root.withdraw()
    iconset = os.path.join(HERE, "AppIcon.iconset")
    os.makedirs(iconset, exist_ok=True)
    for size in (16, 32, 128, 256, 512):
        pt.icon_photo(size).write(os.path.join(iconset, f"icon_{size}x{size}.png"), format="png")
        pt.icon_photo(size * 2).write(os.path.join(iconset, f"icon_{size}x{size}@2x.png"), format="png")
    pt.icon_photo(1024).write(os.path.join(HERE, "icon.png"), format="png")
    root.destroy()

    if os.path.exists(APP):
        shutil.rmtree(APP)
    os.makedirs(os.path.join(APP, "Contents", "MacOS"))
    os.makedirs(os.path.join(APP, "Contents", "Resources"))
    subprocess.run(["iconutil", "-c", "icns", iconset, "-o",
                    os.path.join(APP, "Contents", "Resources", "AppIcon.icns")], check=True)
    shutil.rmtree(iconset)

    with open(os.path.join(APP, "Contents", "Info.plist"), "w", encoding="utf-8") as fh:
        fh.write(INFO_PLIST)
    launcher = os.path.join(APP, "Contents", "MacOS", "launcher")
    with open(launcher, "w", encoding="utf-8") as fh:
        fh.write(f'#!/bin/zsh\nexec "{sys.executable}" "{SCRIPT}"\n')
    os.chmod(launcher, 0o755)
    subprocess.run(["touch", APP])  # чтобы Finder сразу подхватил иконку
    print("Готово:", APP)


if __name__ == "__main__":
    main()
