#!/usr/bin/env python3
"""Task Quest — ретро-трекер времени задач с переключаемыми скинами.

Скины:
  pixel — ночная пиксельная сцена с кошечкой Мяу-Луной (pixel_tracker.py)
  2000  — неоновый RPG-интерфейс, окошки Windows 98 и комната с призраком (task_quest_2000.py)

Переключение — кнопка SKIN. Таймер, квесты и история при смене скина сохраняются,
выбранный скин запоминается до следующего запуска.

Запуск:  python3 task_quest.py
"""
import json
import sys
import tkinter as tk

import pixel_tracker as pt
import task_quest_2000 as tq
from pixel_tracker import C, mix, moon_cells
from task_quest_2000 import FONT, N, P2, RINGS

SKINS = {"pixel": ("Pixel", pt.App), "2000": ("2000", tq.App2)}
SKIN_ORDER = list(SKINS)


# ── Общая иконка: слева ночной мир Pixel, справа мир 2000 ───────────────────
def icon_grid_combined():
    n, lo, hi, r = 128, 10, 117, 18

    def inside(x, y, pad=0):
        a, b, rr = lo + pad, hi - pad, r - pad
        if not (a <= x <= b and a <= y <= b):
            return False
        cx, cy = min(max(x, a + rr), b - rr), min(max(y, a + rr), b - rr)
        return (x - cx) ** 2 + (y - cy) ** 2 <= rr * rr

    def split(y):  # пиксельная «молния» между мирами
        return 63 + (3 if (y // 6) % 2 else -3)

    g = [[None] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            if not inside(x, y):
                continue
            right = x >= split(y)
            if not inside(x, y, 4):
                g[y][x] = N["ink"]
            elif not inside(x, y, 6):
                g[y][x] = N["pink"] if right else C["yellow"]
            elif y < 30:  # заголовок окна в духе Windows 98
                g[y][x] = mix(N["title1"], N["title2"], (x - lo) / (hi - lo))
            elif y < 32:
                g[y][x] = N["ink"]
            elif y < 98:
                g[y][x] = (mix("#5b3fd1", "#8fd8ff", (y - 32) / 66) if right
                           else mix("#3b2d85", "#1f1650", (y - 32) / 66))
            elif right:
                g[y][x] = "#ff4f8b" if (x // 4 + y // 4) % 2 else "#ff7aa8"
            elif y < 104:
                g[y][x] = C["grass"] if (x // 6) % 2 else C["grass2"]
            else:
                g[y][x] = C["dirt"] if (x // 6 + y // 6) % 2 else C["dirt2"]

    def put(x, y, col, s=2):
        for dy in range(s):
            for dx in range(s):
                if g[y + dy][x + dx] not in (None, N["ink"]):
                    g[y + dy][x + dx] = col

    def sprite(rows, x0, y0, s, pal):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != "." and pal.get(ch):
                    put(x0 + i * s, y0 + j * s, pal[ch], s)

    # молния-разделитель
    for y in range(32, 112):
        x = split(y)
        if inside(x, y, 6):
            put(x - 1, y, C["text"], 1)
    # заголовок: название и кнопки окна
    cx = 20
    for ch in "TASK QUEST":
        glyph = FONT[ch]
        for j, row in enumerate(glyph):
            for i, px in enumerate(row):
                if px == "#":
                    put(cx + i, 19 + j, N["white"], 1)
        cx += len(glyph[0]) + 1
    for bx in (84, 93, 102):
        for yy in range(18, 26):
            for xx in range(bx, bx + 7):
                g[yy][xx] = N["gray"]
    # левый мир: луна и звёзды
    for i, j in moon_cells(5, 3):
        put(34 + i * 2, 36 + j * 2, C["yellow"])
    for sx, sy in ((18, 40), (26, 58), (56, 44)):
        put(sx, sy, C["yellow"])
    for sx, sy in ((20, 76), (50, 36)):
        for dx, dy in ((0, 0), (2, 0), (-2, 0), (0, 2), (0, -2)):
            put(sx + dx, sy + dy, C["yellow"])
    # правый мир: радужные пузыри
    for (bx, by), rr in (((82, 44), 4), ((106, 40), 3), ((110, 64), 2)):
        for i, j, col in RINGS[rr]:
            put(bx + i * 2, by + j * 2, col)
        put(bx - rr, by - rr, N["white"])
    # герои: кошечка и призрак
    sprite(pt.CAT_AWAKE, 16, 52, 3, pt.PALETTE)
    sprite(tq.GHOST, 64, 52, 3, P2)
    return g


class Shell:
    """Окно, в котором живёт текущий скин; умеет менять его на лету."""

    def __init__(self, root, skin):
        self.root = root
        self.app = None
        try:
            self.icon = pt.icon_photo(256, icon_grid_combined)
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
