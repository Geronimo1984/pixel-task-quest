#!/usr/bin/env python3
"""Task Quest — ретро-трекер времени задач с переключаемыми скинами.

Скины (по умолчанию — moon):
  moon  — волшебная аркада с сердечками-блоками и мессенджер в духе Windows XP (task_quest_moon.py)
  2000  — неоновый RPG-интерфейс, окошки Windows 98 и комната с призраком (task_quest_2000.py)
  term  — зелёный фосфорный терминал с падающими символами и полутоновым глазом (task_quest_terminal.py)
  player — плеер K-Jofol с вращающимися дисками Kirby Air Ride, Bratz и Resident Evil 4 (task_quest_player.py)

Кнопка SKIN открывает список скинов с мини-иконками. Таймер, квесты и история при смене скина сохраняются,
выбранный скин запоминается до следующего запуска.

Запуск:  python3 task_quest.py
"""
import json
import math
import os
import sys
import tkinter as tk

import pixel_tracker as pt
import task_quest_2000 as tq
import task_quest_moon as tm
import task_quest_terminal as tt
import task_quest_player as tp
from pixel_tracker import mix
from task_quest_2000 import N

SKINS = {"moon": ("Moon", tm.AppMoon), "2000": ("2000", tq.App2), "term": ("Terminal", tt.AppTerminal),
         "player": ("Player", tp.AppPlayer)}  # порядок = порядок переключения
DEFAULT_SKIN = "moon"
SKIN_INFO = {
    "moon": "Волшебная аркада, Кирби и мессенджер",
    "2000": "Неоновый RPG, Windows 98 и призрак",
    "term": "Зелёный фосфорный терминал",
    "player": "Плеер K-Jofol и вращающиеся диски",
}
ICON = 34  # размер мини-иконки в списке скинов


def skin_icon(name):
    """Мини-иконка 34×34 в стиле скина (собрана из его же графики)."""
    img = tk.PhotoImage(width=ICON, height=ICON)

    def square(top, bottom, border):
        for y in range(ICON):
            img.put(mix(top, bottom, y / (ICON - 1)), to=(1, y, ICON - 1, y + 1))
        for x, y in ((0, 0), (ICON - 1, 0), (0, ICON - 1), (ICON - 1, ICON - 1)):
            img.transparency_set(x, y, True)
        img.put(border, to=(1, 0, ICON - 1, 1)); img.put(border, to=(1, ICON - 1, ICON - 1, ICON))
        img.put(border, to=(0, 1, 1, ICON - 1)); img.put(border, to=(ICON - 1, 1, ICON, ICON - 1))

    def sprite(rows, pal, x0, y0, s=1):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != "." and pal.get(ch):
                    img.put(pal[ch], to=(x0 + i * s, y0 + j * s, x0 + (i + 1) * s, y0 + (j + 1) * s))

    if name == "moon":        # Кирби на звезде на ночном индиго
        square("#2c3478", "#141640", "#f6a3d6")
        sprite(tm.KIRBY, tm.KIRBY_PAL, 0, 3)
    elif name == "2000":      # призрак с джойстиком на небе из окна
        square("#5b3fd1", "#8fd8ff", "#ff4fa3")
        sprite(tq.GHOST, tq.P2, 1, 1, 2)
    elif name == "term":      # зелёный терминал: «>_» и строки развёртки
        square("#020a05", "#000000", "#39ff6a")
        for y in range(3, ICON - 3, 3):
            img.put("#04150a", to=(2, y, ICON - 2, y + 1))
        sprite(tq.FONT[">"], {"#": "#39ff6a"}, 6, 10, 2)
        img.put("#39ff6a", to=(18, 22, 28, 24))
    elif name == "player":    # диск в приводе плеера
        square("#5a6a5c", "#1c221d", "#9fb19d")
        disc = tk.PhotoImage(file=os.path.join(pt.APP_DIR, "assets", "disc_kirby_small.png")).subsample(2)
        img.tk.call(img, "copy", disc, "-to", 3, 3, "-compositingrule", "overlay")
    return img


class SkinPicker:
    """Окошко со списком скинов: мини-иконка, название и описание в каждой строке."""
    ROW = 58

    def __init__(self, shell):
        self.shell = shell
        root = shell.root
        self.top = top = tk.Toplevel(root)
        top.title("Выбор скина")
        top.resizable(False, False)
        top.transient(root)
        top.configure(bg="#16162e")
        width, height = 370, self.ROW * len(SKINS) + 52
        self.cv = tk.Canvas(top, width=width, height=height, bg="#16162e", highlightthickness=0)
        self.cv.pack()
        self.icons = {name: skin_icon(name) for name in SKINS}
        self.current = shell.app.data.get("skin", DEFAULT_SKIN)
        self.hover = SKIN_ORDER.index(self.current) if self.current in SKINS else 0
        self.width = width
        self.draw()
        self.cv.bind("<Motion>", self.on_motion)
        self.cv.bind("<Button-1>", self.on_click)
        top.bind("<Up>", lambda e: self.move(-1))
        top.bind("<Down>", lambda e: self.move(1))
        top.bind("<Return>", lambda e: self.choose(SKIN_ORDER[self.hover]))
        top.bind("<Escape>", lambda e: self.close())
        top.protocol("WM_DELETE_WINDOW", self.close)
        root.update_idletasks()
        x = root.winfo_rootx() + (root.winfo_width() - width) // 2
        y = root.winfo_rooty() + 120
        top.geometry(f"+{x}+{y}")
        top.grab_set()
        top.focus_set()

    def draw(self):
        cv = self.cv
        cv.delete("all")
        cv.create_text(16, 22, text="Выбери скин", fill="#ffffff", font=("Tahoma", 14, "bold"), anchor="w")
        cv.create_text(self.width - 16, 22, text="↑ ↓ Enter", fill="#7d7fb0", font=("Tahoma", 10), anchor="e")
        for i, name in enumerate(SKIN_ORDER):
            y = 44 + i * self.ROW
            if i == self.hover:
                cv.create_rectangle(8, y, self.width - 8, y + self.ROW - 6, fill="#2a2b5a", outline="#6f74d8")
            cv.create_image(18, y + (self.ROW - 6) / 2, image=self.icons[name], anchor="w")
            cv.create_text(64, y + 17, text=SKINS[name][0], fill="#ffffff", font=("Tahoma", 13, "bold"), anchor="w")
            cv.create_text(64, y + 36, text=SKIN_INFO[name], fill="#b4b7e6", font=("Tahoma", 10), anchor="w")
            if name == self.current:
                cv.create_text(self.width - 22, y + 26, text="✓", fill="#7dffb0", font=("Tahoma", 16, "bold"))

    def row_at(self, y):
        i = int((y - 44) // self.ROW)
        return i if 0 <= i < len(SKIN_ORDER) else None

    def on_motion(self, e):
        i = self.row_at(e.y)
        if i is not None and i != self.hover:
            self.hover = i
            self.draw()

    def on_click(self, e):
        i = self.row_at(e.y)
        if i is not None:
            self.choose(SKIN_ORDER[i])

    def move(self, d):
        self.hover = (self.hover + d) % len(SKIN_ORDER)
        self.draw()

    def choose(self, name):
        self.close()
        if name != self.current:
            self.shell.root.after_idle(lambda: self.shell.load_skin(name))

    def close(self):
        self.shell.picker = None
        self.top.grab_release()
        self.top.destroy()
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
        self.picker = None
        try:
            self.icon = pt.icon_photo(256, icon_grid_universal)
            root.iconphoto(True, self.icon)
        except tk.TclError:
            pass
        self.load_skin(skin if skin in SKINS else DEFAULT_SKIN, first=True)

    def load_skin(self, name, first=False):
        topmost = False
        if self.app:
            topmost = self.app.topmost
            self.app.save()
            self.app.teardown()
        self.app = SKINS[name][1](self.root)
        self.app.on_switch = self.pick_skin
        self.app.topmost = topmost
        self.app.data["skin"] = name
        self.app.save()
        if not first:
            self.app.show_toast(f"Скин: {SKINS[name][0]} ✓", 25)

    def pick_skin(self):
        """Кнопка SKIN открывает список скинов."""
        if self.picker is None:
            self.picker = SkinPicker(self)



def saved_skin():
    try:
        with open(pt.DATA_FILE, encoding="utf-8") as fh:
            return json.load(fh).get("skin", DEFAULT_SKIN)
    except (OSError, ValueError):
        return DEFAULT_SKIN


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
