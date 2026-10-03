#!/usr/bin/env python3
"""Task Quest — ретро-трекер времени задач с переключаемыми скинами.

Скины:
  pixel — ночная пиксельная сцена с кошечкой Мяу-Луной (pixel_tracker.py)
  2000  — неоновый RPG-интерфейс, окошки Windows 98 и комната с призраком (task_quest_2000.py)
  moon  — волшебная аркада с сердечками-блоками и мессенджер в духе Windows XP (task_quest_moon.py)

Переключение — кнопка SKIN. Таймер, квесты и история при смене скина сохраняются,
выбранный скин запоминается до следующего запуска.

Запуск:  python3 task_quest.py
"""
import json
import math
import sys
import tkinter as tk

import pixel_tracker as pt
import task_quest_2000 as tq
import task_quest_moon as tm
from pixel_tracker import mix
from task_quest_2000 import N

SKINS = {"pixel": ("Pixel", pt.App), "2000": ("2000", tq.App2), "moon": ("Moon", tm.AppMoon)}
SKIN_ORDER = list(SKINS)


# ── Общая иконка: пиксельный секундомер — то, что объединяет все скины ─────
def icon_grid_universal():
    n, lo, hi, r = 64, 5, 58, 9

    def inside(x, y, pad=0):
        a, b, rr = lo + pad, hi - pad, r - pad
        if not (a <= x <= b and a <= y <= b):
            return False
        cx, cy = min(max(x, a + rr), b - rr), min(max(y, a + rr), b - rr)
        return (x - cx) ** 2 + (y - cy) ** 2 <= rr * rr

    g = [[None] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            if not inside(x, y):
                continue
            if not inside(x, y, 2):
                g[y][x] = N["ink"]
            else:  # диагональный градиент: ночь → лаванда → розовый
                t = min(1, max(0, (x + y - 2 * lo) / (2 * (hi - lo))))
                g[y][x] = mix("#2a1f6b", "#7a4fd0", t * 2) if t < 0.5 else mix("#7a4fd0", "#ff7ab8", (t - 0.5) * 2)

    def put(x, y, col):
        if 0 <= x < n and 0 <= y < n and g[y][x] is not None:
            g[y][x] = col

    cx, cy, R = 31.5, 35.5, 18
    # кнопка-заводная головка и боковая кнопка
    for x in range(28, 36):
        for y in range(10, 19):
            put(x, y, N["ink"] if x in (28, 35) or y == 10 else N["pink"])
    for x in range(30, 34):
        put(x, 11, "#ffb3d9")
    for x in range(44, 49):
        for y in range(16, 21):
            put(x, y, N["ink"] if x in (44, 48) or y in (16, 20) else N["pink"])
    # корпус: обводка, неоновый ободок, циферблат
    for y in range(n):
        for x in range(n):
            d = math.hypot(x - cx, y - cy)
            if d <= R + 1.2:
                if d > R:
                    put(x, y, N["ink"])
                elif d > R - 3:
                    put(x, y, N["pink"] if (x - cx) + (y - cy) > -6 else "#ff9fd0")
                elif d > R - 4:
                    put(x, y, N["ink"])
                else:
                    put(x, y, "#e9e4ff" if (x - cx) + (y - cy) > 8 else "#fdfaff")
    # деления на 12 / 3 / 6 / 9 и мелкие риски
    for ang in range(0, 360, 30):
        rad = math.radians(ang)
        big = ang % 90 == 0
        for k in ((10, 11, 12) if big else (12,)):
            put(round(cx + k * math.sin(rad)), round(cy - k * math.cos(rad)), N["ink"] if big else "#9d8fd6")
    # стрелки: минутная вверх, секундная розовая на «2 часа», центр
    for k in range(1, 11):
        put(31, round(cy) - k, N["ink"])
        put(32, round(cy) - k, N["ink"])
    for k in range(1, 12):
        put(round(cx + k * math.sin(math.radians(60))), round(cy - k * math.cos(math.radians(60))), "#ff3d8b")
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            put(32 + dx, 36 + dy, N["ink"])
    put(32, 36, N["yellow"])
    # искорки и сердечко-значок
    for sx, sy in ((12, 13), (53, 27), (11, 47)):
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            put(sx + dx, sy + dy, N["yellow"])
    for sx, sy in ((19, 20), (48, 54), (16, 33)):
        put(sx, sy, "#ffffff")
    for j, row in enumerate(HEART_BADGE):
        for i, ch in enumerate(row):
            if ch != ".":
                put(42 + i, 41 + j, {"K": N["ink"], "R": "#ff3d8b", "W": "#ffffff"}[ch])
    return g


HEART_BADGE = [
    ".KKK.KKK.",
    "KRRRKRRRK",
    "KRWRRRRRK",
    "KRRRRRRRK",
    ".KRRRRRK.",
    "..KRRRK..",
    "...KRK...",
    "....K....",
]


class Shell:
    """Окно, в котором живёт текущий скин; умеет менять его на лету."""

    def __init__(self, root, skin):
        self.root = root
        self.app = None
        try:
            self.icon = pt.icon_photo(256, icon_grid_universal)
            root.iconphoto(True, self.icon)
        except tk.TclError:
            pass
        self.load_skin(skin if skin in SKINS else "pixel", first=True)

    def load_skin(self, name, first=False):
        topmost = False
        if self.app:
            topmost = self.app.topmost
            self.app.save()
            self.app.teardown()
        self.app = SKINS[name][1](self.root)
        self.app.on_switch = self.next_skin
        self.app.topmost = topmost
        self.app.data["skin"] = name
        self.app.save()
        if not first:
            self.app.show_toast(f"Скин: {SKINS[name][0]} ✓", 25)

    def next_skin(self):
        cur = self.app.data.get("skin", "pixel")
        nxt = SKIN_ORDER[(SKIN_ORDER.index(cur) + 1) % len(SKIN_ORDER)]
        # меняем после обработки клика, чтобы не удалять холст посреди его же события
        self.root.after_idle(lambda: self.load_skin(nxt))


def saved_skin():
    try:
        with open(pt.DATA_FILE, encoding="utf-8") as fh:
            return json.load(fh).get("skin", "pixel")
    except (OSError, ValueError):
        return "pixel"


def main(skin=None):
    root = tk.Tk()
    if not pt.acquire_lock():
        root.withdraw()
        pt.messagebox.showinfo("Task Quest уже открыт", "Трекер уже запущен — переключись на его окно.")
        root.destroy()
        return
    Shell(root, skin or saved_skin())
    root.mainloop()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
