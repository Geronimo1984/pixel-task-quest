#!/usr/bin/env python3
"""Task Quest 2000 — вторая версия трекера времени в новом стиле.

Неоновый RPG-интерфейс (HP/MP, инвентарь, уровень), окошки в духе Windows 98
и уютная ретро-комната с призраком, ЭЛТ-телевизором и окном в небо.

Логика и данные общие с pixel_tracker.py (tracker_data.json): обе версии
показывают одни и те же квесты и историю. Одновременно запускать их нельзя.

Запуск:  python3 task_quest_2000.py
"""
import math
import random
import time
import tkinter as tk
from tkinter import font as tkfont

import pixel_tracker as pt
from kanban import KanbanMixin, done_prefix
from pixel_tracker import CLOUD, HEART, LEVEL_SEC, STAR, fmt_hms, mix

W, H = 480, 820
IDLE_SEC = 10 * 60          # через сколько минут простоя спросить «ARE YOU HERE??»
FOCUS_SEC = 25 * 60         # HP: фокус-блок текущей сессии
DAY_GOAL_SEC = 8 * 3600     # MP: цель на день

N = {
    "bg": "#120d2a", "dot": "#231a4f", "panel": "#1a1440", "row": "#221a50", "sel": "#3a2a7a",
    "pink": "#ff4fa3", "violet": "#b98cff", "cyan": "#3fe0ff", "yellow": "#ffe14d",
    "red": "#ff3b5c", "blue": "#2f9bff", "green": "#3ddc84", "white": "#ffffff", "ink": "#0b0820",
    "gray": "#c0c0c8", "gray_d": "#808088", "gray_l": "#e4e4ec", "black": "#000000",
    "title1": "#1a2a9a", "title2": "#5aa8ff", "wood": "#8a5a3c",
}

P2 = dict(pt.PALETTE)
P2.update({"D": "#3a3550", "T": "#2bb3a8", "t": "#1f8a82", "O": "#ff8a3d", "o": "#e0602a",
           "B": "#2f6fd9", "G": "#3ddc84", "w": "#dfe6ff", "P": "#ff9fcf"})

# ── Пиксельный шрифт 5×7 (латиница, цифры, знаки) ───────────────────────────
FONT = dict(pt.DIGITS)
FONT.update({
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "!": ["#", "#", "#", "#", "#", ".", "#"],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    ".": [".", ".", ".", ".", ".", ".", "#"],
    "/": ["....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."],
    "-": ["...", "...", "...", "###", "...", "...", "..."],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    ">": ["#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."],
    " ": ["...", "...", "...", "...", "...", "...", "..."],
})

# ── Спрайты ─────────────────────────────────────────────────────────────────
GHOST = [
    "......KKKK......",
    "....KKWWWWKK....",
    "...KWWWWWWWWK...",
    "..KWWWWWWWWWWK..",
    "..KWWKKWWKKWWK..",
    "..KWWKKWWKKWWK..",
    ".KWWWWWWWWWWWWK.",
    ".KWPPWWWWWWPPWK.",
    ".KWWWWWWWWWWWWK.",
    "KWWKKKKKKKKKKWWK",
    "KWKDYDDDDDDRDKWK",
    "KWKYYYDDDDRDCKWK",
    "KWKDYDDDDDDGDKWK",
    "KWWKKKKKKKKKKWWK",
    "KWWWWWWWWWWWWWWK",
    ".KKK.KKKKKK.KKK.",
]
GHOST_SLEEP = GHOST[:4] + ["..KWWWWWWWWWWK..", "..KWKKKWWKKKWK.."] + GHOST[6:]
GHOST_PRESS = GHOST[:11] + ["KWKYYYDDDDWDCKWK"] + GHOST[12:]
# пасхалка: испуганный призрак — глаза-блюдца, рот «О», джойстик выронил
GHOST_SCARED = GHOST[:3] + [
    "..KWKKKWWKKKWK..",
    "..KWKWKWWKWKWK..",
    "..KWKKKWWKKKWK..",
    ".KWWWWWKKWWWWWK.",
    ".KWWWWKWWKWWWWK.",
    ".KWWWWWKKWWWWWK.",
] + ["KWWWWWWWWWWWWWWK"] * 5 + GHOST[14:]
PAD = [
    ".KKKKKKKKKK.",
    "KDYDDDDDDRDK",
    "KYYYDDDDRDCK",
    "KDYDDDDDDGDK",
    ".KKKKKKKKKK.",
]
GHOST_AWAY_SEC = 15

FISH = [
    "....KKKK......",
    "..KKOWOOK...KK",
    ".KOOOWOOOK.KOK",
    "KOKOOWOOOWKOOK",
    "KOOOOWOOOWOOOK",
    ".KOOOWOOOK.KOK",
    "..KKOWOOK...KK",
    "....KKKK......",
]

SKELETON = [
    "..WWW..",
    ".WKWKW.",
    "..WWW..",
    "...W...",
    ".WWWWW.",
    "W.WWW.W",
    "..WWW..",
    "..W.W..",
    ".W...W.",
    "W.....W",
]

FOLDER = [
    "KKKKK.........",
    "KOOOOK........",
    "KOOOOOKKKKKKKK",
    "KOYYYYYYYYYYYK",
    "KOYYYYYYYYYYYK",
    "KOYYBBBBBYYYYK",
    "KOYYYYYYYYYYYK",
    "KOYYYYYYYYYYYK",
    "KOYYYYYYYYYYYK",
    "KKKKKKKKKKKKKK",
]

GLOBE = [
    "...KKKKKK...",
    ".KKBBGGBBKK.",
    ".KBGGGGBBBK.",
    "KBBGGGBBBBBK",
    "KBBBGGBBGGBK",
    "KBBBBBBGGGGK",
    "KGBBBBBGGGBK",
    "KGGBBBBBGBBK",
    "KBGGBBBBBBBK",
    ".KBGBBBBBBK.",
    ".KKBBBBBBKK.",
    "...KKKKKK...",
]

FLOPPY = [
    "KKKKKKKKKKK.",
    "KBBDDDDDKBBK",
    "KBBDDKDDKBBK",
    "KBBDDKDDKBBK",
    "KBBDDDDDKBBK",
    "KBBBBBBBBBBK",
    "KBwwwwwwwwBK",
    "KBwKKKKKKwBK",
    "KBwwwwwwwwBK",
    "KBwKKKKKwwBK",
    "KBwwwwwwwwBK",
    "KKKKKKKKKKKK",
]

PIN = [
    "...KKKK...",
    "..KRRRRK..",
    "..KRWRRK..",
    "..KRRRRK..",
    ".KKRRRRKK.",
    "KRRRRRRRRK",
    ".KKKKKKKK.",
    "....KK....",
    "....KK....",
    "....KK....",
    ".....K....",
]

BUBBLE_ICON = [
    "...CCCC...",
    ".CC....PP.",
    ".CWW.....P",
    "C.W......P",
    "C........P",
    "C........G",
    "C........G",
    ".C......G.",
    ".CC....GG.",
    "...GGGG...",
]

BOMB = [
    ".........Y..",
    "........YOY.",
    ".......KNY..",
    "......KN....",
    "...KKKKK....",
    "..KDDDDDK...",
    ".KDwDDDDDK..",
    ".KDwDDDDDK..",
    ".KDDDDDDDK..",
    ".KDDDDDDDK..",
    "..KDDDDDK...",
    "...KKKKK....",
]

SKIN_ICON = [  # палитра художника — смена скина
    "...KKKKKK...",
    ".KKNNNNNNKK.",
    "KNNRRNNYYNNK",
    "KNNRRNNYYNNK",
    "KNNNNNNNNNNK",
    "KNCCNNNKKNNK",
    "KNCCNNK..KNK",
    "KNNNNNK..KNK",
    ".KNNGGNKKNK.",
    "..KNGGNNNK..",
    "...KKKKKK...",
]

SLOT_X0, SLOT_STEP, SLOT_W = 19, 45, 40  # ячейки инвентаря

RAINBOW = ["#3fe0ff", "#b98cff", "#ff4fa3", "#ffe14d", "#3ddc84"]
NOISE = ["#15142a", "#2a2840", "#4a4866", "#7a7898", "#b8b6d0", "#e8e6ff", "#ff4fa3", "#3fe0ff"]

ROOM = (17, 95, 463, 311)      # внутренняя область комнаты
SKY = (292, 110, 446, 194)     # небо в окне
SCREEN = (42, 188, 112, 234)   # экран телевизора
PANELS = [(10, 8, 300, 80), (308, 8, 470, 80), (10, 88, 470, 318), (10, 326, 470, 440),
          (10, 546, 470, 718), (10, 726, 250, 812), (258, 726, 470, 812)]


def ring_cells(r):
    cells = []
    for j in range(-r, r + 1):
        for i in range(-r, r + 1):
            if r - 0.5 <= math.hypot(i, j) < r + 0.5:
                k = int((math.atan2(j, i) + math.pi) / math.tau * len(RAINBOW)) % len(RAINBOW)
                cells.append((i, j, RAINBOW[k]))
    return cells


RINGS = {r: ring_cells(r) for r in range(2, 8)}


# ── Иконка «2000» ───────────────────────────────────────────────────────────
def icon_grid_2000():
    n, lo, hi, r = 64, 5, 58, 9

    def inside(x, y, pad=0):
        a, b, rr = lo + pad, hi - pad, r - pad
        if not (a <= x <= b and a <= y <= b):
            return False
        cx, cy = min(max(x, a + rr), b - rr), min(max(y, a + rr), b - rr)
        return (x - cx) ** 2 + (y - cy) ** 2 <= rr * rr

    g = [[None] * n for _ in range(n)]
    rnd = random.Random(7)
    for y in range(n):
        for x in range(n):
            if not inside(x, y):
                continue
            if not inside(x, y, 2):
                g[y][x] = N["ink"]
            elif not inside(x, y, 3):
                g[y][x] = N["pink"]
            elif y < 14:
                g[y][x] = mix(N["title1"], N["title2"], (x - lo) / (hi - lo))
            elif y < 15:
                g[y][x] = N["ink"]
            elif y < 44:
                g[y][x] = mix("#5b3fd1", "#8fd8ff", (y - 15) / 29)
            else:
                g[y][x] = "#ff4f8b" if (x // 2 + y // 2) % 2 else "#ff7aa8"
                if rnd.random() < 0.12:
                    g[y][x] = "#ffe14d" if rnd.random() < 0.3 else "#c21f4a"
    for bx in (40, 45, 50):  # кнопочки окна в заголовке
        for yy in range(9, 13):
            for xx in range(bx, bx + 4):
                g[yy][xx] = N["gray"]
    for x in range(8, 58):  # холмы на горизонте
        h = int(3 + 2 * math.sin(x * 0.25) + 1.5 * math.sin(x * 0.7))
        for y in range(44 - h, 44):
            if g[y][x] not in (None, N["ink"], N["pink"]):
                g[y][x] = "#7a7fe0"
    for (cx, cy), rr in (((15, 24), 4), ((50, 22), 3), ((47, 34), 2)):
        for i, j, col in RINGS[rr]:
            g[cy + j][cx + i] = col
        g[cy - rr // 2][cx - rr // 2] = N["white"]
    for j, row in enumerate(GHOST):
        for i, ch in enumerate(row):
            if ch != ".":
                for dy in range(2):
                    for dx in range(2):
                        g[20 + j * 2 + dy][16 + i * 2 + dx] = P2[ch]
    return g


class App2(KanbanMixin, pt.App):
    ROWS = 4
    ROW_H = 32
    LIST_TOP = 580

    def __init__(self, root):  # noqa: super().__init__ не вызываем — у этой версии своя сцена
        self.root = root
        root.title("Task Quest · 2000")
        root.resizable(False, False)
        root.configure(bg=N["bg"])
        families = set(tkfont.families())
        fam = next((f for f in ("Menlo", "Monaco", "Consolas", "Courier New", "Courier") if f in families),
                   "TkFixedFont")
        self.font = lambda size, bold=True: (fam, size, "bold" if bold else "normal")

        self.cv = tk.Canvas(root, width=W, height=H, bg=N["bg"], highlightthickness=0)
        self.cv.pack()
        self.on_switch = None  # задаётся оболочкой task_quest.py

        self.f = 0
        self.layer = "dyn"
        self.particles = []
        self.pressed = {}
        self.hits = []
        self.scroll = 0
        self.toast = None
        self.topmost = False
        self.idle_since = time.time()
        self.ghost_state = None  # None | ("scared", кадр) | ("gone", до какого времени) | ("back", кадр)
        self.clouds = [[330, 128, 0.3], [430, 150, 0.2], [520, 120, 0.25]]
        self.fish = []
        self.bubbles = [self.new_bubble(random.uniform(ROOM[1], ROOM[3])) for _ in range(7)]

        self.load()
        self.data.setdefault("fx", True)
        self.last_lv = self.level()[0]

        self.draw_static()
        self.build_entry()

        self.cv.bind("<Button-1>", self.on_click)
        self.kb_init()   # режим «Канбан» в журнале квестов
        self.cv.bind("<MouseWheel>", self.on_wheel)
        self.cv.bind("<Button-4>", lambda e: self.scroll_by(-1))
        self.cv.bind("<Button-5>", lambda e: self.scroll_by(1))
        root.bind("<space>", self.on_space)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        if not self.data["tasks"]:
            self.show_toast("Добавь первый квест ↓", 60)
        elif self.data["running"]:
            self.show_toast("С возвращением! Таймер шёл ♥", 50)
        self.tick()

    # ── действия, специфичные для версии ───────────────────────────────────
    def build_entry(self):
        self.entry = tk.Entry(self.root, font=self.font(13), bg=N["ink"], fg=N["cyan"],
                              insertbackground=N["pink"], relief="flat",
                              highlightthickness=3, highlightbackground=N["violet"], highlightcolor=N["pink"])
        self.cv.create_window(12, 506, anchor="nw", window=self.entry, width=380, height=32)
        self.placeholder = "новый квест..."
        self.placeholder_on = False
        self.set_placeholder()
        self.entry.bind("<FocusIn>", self.clear_placeholder)
        self.entry.bind("<FocusOut>", lambda e: self.set_placeholder())
        self.entry.bind("<Return>", self.add_task)

    def set_placeholder(self):
        if not self.entry.get():
            self.placeholder_on = True
            self.entry.config(fg=N["violet"])
            self.entry.insert(0, self.placeholder)

    def clear_placeholder(self, _e=None):
        if self.placeholder_on:
            self.entry.delete(0, "end")
            self.entry.config(fg=N["cyan"])
            self.placeholder_on = False

    def stop(self):
        super().stop()
        self.idle_since = time.time()

    def toggle_fx(self):
        self.press("fx")
        self.data["fx"] = not self.data["fx"]
        self.save()
        self.show_toast("Пузыри и рыбки: " + ("ВКЛ" if self.data["fx"] else "ВЫКЛ"), 20)

    def dismiss_idle(self):
        self.press("maybe")
        self.idle_since = time.time()
        self.show_toast("Жду тебя ♥", 20)

    @staticmethod
    def new_bubble(y=None):
        return {"x": random.uniform(ROOM[0] + 10, ROOM[2] - 10), "y": y if y is not None else ROOM[3] + 20,
                "r": random.randint(3, 7), "speed": random.uniform(0.4, 1.1), "ph": random.uniform(0, 6)}

    def update_particles(self):
        super().update_particles()
        for p in self.particles:
            if p["kind"] in ("steam", "note", "float"):
                p["vx"] = math.sin(p["life"] / 3 + p.get("ph", 0)) * 0.5

    # ── примитивы рисования (с поддержкой статичного слоя и обрезки) ───────
    # Спрайты, пиксельный текст, кружки, блоки и пузыри собираются один раз в картинку и дальше выводятся
    # одним элементом холста вместо десятков прямоугольников — кадр рисуется в разы быстрее.
    def cached(self, key, w, h, paint):
        cache = self.__dict__.setdefault("_img_cache", {})
        img = cache.pop(key, None)
        if img is None:
            if len(cache) > 600:     # меняющиеся надписи (время) не копятся: убираем давно не нужные
                for old in list(cache)[:200]:
                    del cache[old]
            img = tk.PhotoImage(width=max(1, w), height=max(1, h))
            paint(img)
        cache[key] = img             # недавно использованные — в конце очереди
        return img

    def sprite(self, rows, cx, bottom, sx=4.0, sy=None, color=None, flip=False, clip=None, pal=None):
        if clip:
            return self.sprite_rects(rows, cx, bottom, sx, sy, color, flip, clip, pal)
        pal = pal or P2
        sy = sy or sx
        w, h = len(rows[0]), len(rows)

        def paint(img):
            for j, row in enumerate(rows):
                row = row[::-1] if flip else row
                i = 0
                while i < w:
                    ch = row[i]
                    k = i + 1
                    while k < w and row[k] == ch:
                        k += 1
                    x1, x2, y1, y2 = round(i * sx), round(k * sx), round(j * sy), round((j + 1) * sy)
                    if ch != "." and x2 > x1 and y2 > y1:
                        img.put(color or pal[ch], to=(x1, y1, x2, y2))
                    i = k
        img = self.cached(("spr", id(rows), sx, sy, color, flip, id(pal)), round(w * sx), round(h * sy), paint)
        self.place(round(cx - w * sx / 2), round(bottom - h * sy), img)

    def ptext(self, s, x, y, scale, color, anchor="w", shadow=None):
        glyphs = [FONT.get(ch, FONT["?"]) for ch in s.upper()]
        total = sum(len(g[0]) for g in glyphs) * scale + (len(glyphs) - 1) * scale
        off = max(1, scale // 2 + 1) if shadow else 0

        def paint(img):
            for o, col in ([(off, shadow)] if shadow else []) + [(0, color)]:
                cx = 0
                for g in glyphs:
                    for j, row in enumerate(g):
                        for i, ch in enumerate(row):
                            if ch == "#":
                                img.put(col, to=(round(cx + i * scale + o), round(j * scale + o),
                                                 round(cx + (i + 1) * scale + o), round((j + 1) * scale + o)))
                    cx += (len(g[0]) + 1) * scale
        img = self.cached(("txt", s.upper(), scale, color, shadow), round(total + off), round(7 * scale + off), paint)
        x -= total / 2 if anchor == "center" else total if anchor == "e" else 0
        self.place(round(x), round(y), img)
        return total

    def begin_static(self):
        """Неподвижный фон рисуется в одну картинку: Tk не перебирает сотни элементов в каждом кадре."""
        self.layer = "static"
        self.bg_img = tk.PhotoImage(width=int(self.cv["width"]), height=int(self.cv["height"]))
        self.cv.create_image(0, 0, image=self.bg_img, anchor="nw", tags="static")

    def place(self, x, y, img):
        """Картинка на холст, а в статичном слое — прямо в общую картинку фона."""
        if self.layer == "static" and getattr(self, "bg_img", None):
            fx, fy = max(0, -x), max(0, -y)
            if fx < img.width() and fy < img.height():
                self.bg_img.tk.call(self.bg_img, "copy", img, "-from", fx, fy, img.width(), img.height(),
                                    "-to", x + fx, y + fy)
        else:
            self.cv.create_image(x, y, image=img, anchor="nw", tags=self.layer)

    def rect(self, x1, y1, x2, y2, fill, outline="", width=0, clip=None):
        if self.layer == "static" and getattr(self, "bg_img", None) and not outline:
            x1, y1 = max(0, round(x1)), max(0, round(y1))
            x2, y2 = min(self.bg_img.width(), round(x2)), min(self.bg_img.height(), round(y2))
            if x2 > x1 and y2 > y1:
                self.bg_img.put(fill, to=(x1, y1, x2, y2))
            return
        if clip:
            x1, y1, x2, y2 = max(x1, clip[0]), max(y1, clip[1]), min(x2, clip[2]), min(y2, clip[3])
            if x1 >= x2 or y1 >= y2:
                return
        self.cv.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=width, tags=self.layer)

    def bubble(self, cx, cy, r):
        def paint(img):
            for i, j, col in RINGS[r]:
                img.put(col, to=(i + r, j + r, i + r + 1, j + r + 1))
            img.put("#ffffff", to=(r - r // 2, r - r // 2, r - r // 2 + 1, r - r // 2 + 1))
        img = self.cached(("bub", r), 2 * r + 1, 2 * r + 1, paint)
        self.place(cx - r, cy - r, img)

    def text(self, x, y, s, color, size=12, anchor="center", shadow=None):
        if shadow:
            self.cv.create_text(x + 1, y + 1, text=s, fill=shadow, font=self.font(size), anchor=anchor,
                                tags=self.layer)
        self.cv.create_text(x, y, text=s, fill=color, font=self.font(size), anchor=anchor, tags=self.layer)

    def sprite_rects(self, rows, cx, bottom, sx=4.0, sy=None, color=None, flip=False, clip=None, pal=None):
        """Спрайт прямоугольниками — только для обрезанных спрайтов (clip)."""
        pal = pal or P2
        sy = sy or sx
        w, h = len(rows[0]), len(rows)
        x0, y0 = cx - w * sx / 2, bottom - h * sy
        for j, row in enumerate(rows):
            if flip:
                row = row[::-1]
            i = 0
            while i < w:
                ch = row[i]
                if ch == ".":
                    i += 1
                    continue
                k = i
                while k < w and row[k] == ch:
                    k += 1
                self.rect(round(x0 + i * sx), round(y0 + j * sy), round(x0 + k * sx), round(y0 + (j + 1) * sy),
                          color or pal[ch], clip=clip)
                i = k

    def neon(self, x1, y1, x2, y2, fill=N["panel"]):
        self.rect(x1 - 2, y1 - 2, x2 + 2, y2 + 2, mix(N["pink"], N["bg"], 0.6))
        self.rect(x1, y1, x2, y2, N["pink"])
        self.rect(x1 + 3, y1 + 3, x2 - 3, y2 - 3, N["ink"])
        self.rect(x1 + 5, y1 + 5, x2 - 5, y2 - 5, N["violet"])
        self.rect(x1 + 7, y1 + 7, x2 - 7, y2 - 7, fill)

    def bevel(self, x1, y1, x2, y2, fill=N["gray"], sunken=False):
        if sunken:
            self.rect(x1, y1, x2, y2, N["white"])
            self.rect(x1, y1, x2 - 2, y2 - 2, N["gray_d"])
            self.rect(x1 + 2, y1 + 2, x2 - 2, y2 - 2, N["black"])
            self.rect(x1 + 4, y1 + 4, x2 - 2, y2 - 2, fill)
        else:
            self.rect(x1, y1, x2, y2, N["black"])
            self.rect(x1, y1, x2 - 2, y2 - 2, N["white"])
            self.rect(x1 + 2, y1 + 2, x2 - 2, y2 - 2, N["gray_d"])
            self.rect(x1 + 2, y1 + 2, x2 - 4, y2 - 4, fill)

    def win_window(self, x1, y1, x2, y2, title):
        self.bevel(x1, y1, x2, y2)
        tx1, ty1, tx2, ty2 = x1 + 5, y1 + 5, x2 - 5, y1 + 25
        bands = 16
        for i in range(bands):
            self.rect(tx1 + (tx2 - tx1) * i / bands, ty1, tx1 + (tx2 - tx1) * (i + 1) / bands + 1, ty2,
                      mix(N["title1"], N["title2"], i / (bands - 1)))
        self.ptext(title, tx1 + 6, ty1 + 3, 2, N["white"])
        for k in range(3):
            bx2 = tx2 - 3 - (2 - k) * 19
            bx1, by1, by2 = bx2 - 16, ty1 + 3, ty2 - 3
            self.bevel(bx1, by1, bx2, by2)
            if k == 0:
                self.rect(bx1 + 4, by2 - 6, bx1 + 10, by2 - 4, N["black"])
            elif k == 1:
                self.rect(bx1 + 4, by1 + 3, bx1 + 12, by2 - 4, N["black"])
                self.rect(bx1 + 5, by1 + 5, bx1 + 11, by2 - 5, N["gray"])
            else:
                self.ptext("X", bx1 + 5, by1 + 3, 1, N["black"])

    def win_button(self, name, x1, y1, x2, y2, label, color, cb, scale=2):
        down = self.pressed.get(name, -1) >= self.f
        self.bevel(x1, y1, x2, y2, sunken=down)
        o = 2 if down else 0
        self.ptext(label, (x1 + x2) / 2 + o, (y1 + y2) / 2 - 7 * scale / 2 + o, scale, color, anchor="center")
        self.hits.append((x1, y1, x2, y2, cb))

    def bar(self, x1, y1, x2, y2, frac, color):
        self.rect(x1, y1, x2, y2, N["cyan"])
        self.rect(x1 + 2, y1 + 2, x2 - 2, y2 - 2, N["ink"])
        w = (x2 - x1 - 4) * max(0.0, min(1.0, frac))
        if w >= 1:
            self.rect(x1 + 2, y1 + 2, x1 + 2 + w, y2 - 2, color)
            self.rect(x1 + 2, y1 + 2, x1 + 2 + w, y1 + 4, pt.lighten(color, 0.5))

    # ── статичный слой: рисуется один раз ─────────────────────────────────
    def draw_static(self):
        self.begin_static()
        rnd = random.Random(2000)

        # фон в точку, как полутоновая печать
        for row, y in enumerate(range(4, H, 10)):
            for x in range(5 * (row % 2), W, 10):
                if not any(a - 3 <= x <= c + 3 and b - 3 <= y <= d + 3 for a, b, c, d in PANELS):
                    self.rect(x, y, x + 2, y + 2, N["dot"])

        # HUD
        self.neon(*PANELS[0])
        self.ptext("HP", 24, 36, 2, N["yellow"], shadow=N["ink"])
        self.ptext("MP", 24, 56, 2, N["yellow"], shadow=N["ink"])
        self.neon(*PANELS[1])
        self.ptext("TODAY", 389, 18, 2, N["cyan"], anchor="center", shadow=N["ink"])

        # комната
        self.neon(*PANELS[2])
        x1, y1, x2, y2 = ROOM
        self.rect(x1, y1, x2, 236, "#4a2b4c")
        for x in range(x1 + 6, x2, 14):
            self.rect(x, y1, x + 2, 236, "#53305a")
        self.rect(x1, 236, x2, 240, "#2e1a2e")
        self.rect(x1, 240, x2, y2, "#5a3a2e")
        for i, y in enumerate(range(246, y2, 10)):
            self.rect(x1, y, x2, y + 1, "#4a2e24")
            for x in range(x1 + (i % 3) * 22, x2, 66):
                self.rect(x, y - 9, x + 1, y, "#4a2e24")
        # ковёр
        self.rect(150, 262, 360, 306, "#ff4f8b")
        self.rect(154, 265, 356, 303, "#e8643c")
        self.rect(162, 271, 348, 297, "#7a2f8f")
        self.rect(168, 276, 342, 292, "#ff6a4a")
        for x in range(176, 340, 12):
            self.rect(x, 282, x + 6, 286, N["yellow"])
        for x in range(152, 360, 6):
            self.rect(x, 306, x + 2, 310, "#ffd0a0")
        # окно в небо
        self.rect(286, 104, 452, 200, N["wood"])
        sx1, sy1, sx2, sy2 = SKY
        for i in range(12):
            self.rect(sx1, sy1 + i * 7, sx2, sy1 + (i + 1) * 7, mix("#5b3fd1", "#8fd8ff", i / 11))
        for x in range(sx1, sx2, 4):
            h = 8 + 5 * math.sin(x * 0.05) + 3 * math.sin(x * 0.13)
            self.rect(x, sy2 - h, x + 4, sy2, "#7a7fe0")
        self.rect(280, 198, 458, 206, "#a06a46")
        # постеры
        for (a, b, c, d), col in (((24, 104, 74, 168), "#c23b6b"), ((82, 110, 136, 160), "#2f6fd9"),
                                  ((210, 104, 270, 152), "#ff8a3d")):
            self.rect(a, b, c, d, "#f4e9d8")
            self.rect(a + 3, b + 3, c - 3, d - 3, col)
            self.rect(a + 2, b - 2, a + 8, b + 3, "#d8d4e4")
            self.rect(c - 8, b - 2, c - 2, b + 3, "#d8d4e4")
        self.sprite(SKELETON, 49, 154, 3)
        for x in range(30, 70, 7):
            self.rect(x, 158, x + 3, 161, "#ff3b5c" if x % 2 else N["yellow"])
        self.sprite(STAR, 109, 144, 2)
        self.ptext("GAME", 109, 147, 1, N["yellow"], anchor="center")
        self.sprite(HEART, 240, 134, 3)
        self.ptext("1UP", 240, 139, 1, N["white"], anchor="center")
        # книжный шкаф
        self.rect(146, 120, 200, 258, "#6b3f2a")
        self.rect(150, 124, 196, 254, "#3a2218")
        books = ["#ff4f8b", "#3fe0ff", "#ffe14d", "#3ddc84", "#b98cff", "#ff8a3d", "#f4e9d8"]
        for shelf_y in (152, 186, 220, 254):
            self.rect(150, shelf_y - 2, 196, shelf_y + 2, N["wood"])
            x = 152
            while x < 192:
                bw = rnd.randint(4, 7)
                bh = rnd.randint(16, 26)
                self.rect(x, shelf_y - 2 - bh, min(x + bw, 194), shelf_y - 2, rnd.choice(books))
                x += bw + 1
        # телевизор на тумбе
        self.rect(26, 244, 140, 292, "#6b3f2a")
        self.rect(30, 262, 136, 266, "#4a2b1c")
        self.rect(40, 270, 96, 284, "#b8b4c8")
        self.rect(44, 274, 70, 276, "#6b6880")
        self.rect(104, 272, 128, 284, "#2a2838")
        self.rect(30, 176, 136, 246, "#9a98a8")
        self.rect(30, 176, 136, 180, "#c4c2d0")
        self.rect(38, 184, 116, 238, "#3a3848")
        for ky in (196, 212):
            self.rect(120, ky, 130, ky + 10, "#5a5868")
            self.rect(122, ky + 2, 128, ky + 8, "#7a7888")
        for ly in range(226, 240, 3):
            self.rect(119, ly, 131, ly + 1, "#5a5868")
        self.rect(44, 166, 104, 176, "#d8d4e4")
        self.rect(44, 170, 104, 172, "#9a98a8")
        # диван с пледом
        self.rect(296, 214, 456, 252, "#1f8a82")
        self.rect(296, 214, 456, 218, "#3fd1c4")
        self.rect(376, 218, 378, 250, "#177069")
        self.rect(292, 246, 460, 276, "#2bb3a8")
        self.rect(292, 270, 460, 280, "#1f8a82")
        self.rect(286, 232, 304, 282, "#2bb3a8")
        self.rect(286, 232, 304, 236, "#3fd1c4")
        self.rect(440, 226, 462, 282, "#ff8a3d")
        for y in range(232, 282, 8):
            self.rect(440, y, 462, y + 3, "#e0602a")
        self.rect(296, 280, 302, 290, "#3a2218")
        self.rect(450, 282, 456, 290, "#3a2218")
        # журнальный столик, кружка и картридж
        self.rect(186, 270, 280, 278, "#a06a46")
        self.rect(190, 278, 276, 284, "#7a4a30")
        self.rect(194, 284, 200, 302, "#7a4a30")
        self.rect(266, 284, 272, 302, "#7a4a30")
        self.rect(204, 258, 216, 270, "#f4f0ff")
        self.rect(216, 261, 221, 268, "#f4f0ff")
        self.rect(217, 263, 219, 266, "#a06a46")
        self.rect(236, 263, 262, 270, "#ff6f8a")
        self.rect(240, 265, 258, 268, "#ffd0e0")

        # окно таймера
        self.win_window(*PANELS[3], "TIMER.EXE")
        self.bevel(22, 356, 458, 414, fill=N["ink"], sunken=True)

        # журнал квестов
        self.neon(*PANELS[4])
        self.ptext("QUEST LOG", 26, 559, 2, N["pink"], shadow=N["ink"])

        # инвентарь
        self.neon(*PANELS[5])
        icons = [(FLOPPY, "CSV"), (PIN, "TOP"), (BUBBLE_ICON, "FX"), (BOMB, "CLR"), (SKIN_ICON, "SKIN")]
        for i, (spr, label) in enumerate(icons):
            sx = SLOT_X0 + i * SLOT_STEP
            self.rect(sx, 735, sx + SLOT_W, 779, "#ffb02e" if i % 2 == 0 else N["pink"])
            self.rect(sx + 2, 737, sx + SLOT_W - 2, 777, N["ink"])
            self.sprite(spr, sx + SLOT_W / 2, 757 + len(spr) * 2.5 / 2, 2.5)
            self.ptext(label, sx + SLOT_W / 2, 786, 1, N["cyan"], anchor="center")

        # уровень и портрет
        self.neon(*PANELS[6])
        self.rect(400, 734, 458, 804, N["cyan"])
        self.rect(402, 736, 456, 802, N["ink"])
        for y in range(739, 800, 5):
            for x in range(405 + (y // 5 % 2) * 2, 454, 5):
                self.rect(x, y, x + 1, y + 1, N["dot"])
        self.layer = "dyn"

    # ── кадр ───────────────────────────────────────────────────────────────
    def redraw(self):
        self.cv.delete("dyn")
        self.hits = []
        running = self.data["running"]
        f = self.f
        sel = self.task(self.data["selected"])
        today = self.today_total()

        # HUD
        name = sel["name"] if sel else "— нет квеста —"
        if len(name) > 30:
            name = name[:29] + "…"
        self.text(24, 24, name, N["cyan"], 12, anchor="w", shadow=N["ink"])
        hp = (self.session_elapsed() % FOCUS_SEC) / FOCUS_SEC if running else 0
        self.bar(56, 36, 288, 50, hp, N["red"])
        self.bar(56, 56, 288, 70, today / DAY_GOAL_SEC, N["blue"])
        self.pixel_digits(fmt_hms(today), 389, 40, 3, N["yellow"] if running else "#c9b450")

        self.draw_room(running, f)

        # таймер
        total = self.task_total(sel["id"]) if sel else 0
        digits = fmt_hms(total)
        if running and (f // 6) % 2:
            digits = digits.replace(":", " ")
        self.pixel_digits(digits, W / 2, 364, 6, N["cyan"] if running else "#5a5a8a", shadow="#1f2a6a")
        if running and (f // 8) % 2:
            self.rect(424, 363, 430, 369, N["red"])
            self.ptext("REC", 450, 363, 1, N["red"], anchor="e")
        label = sel["name"] if sel else "нет квеста"
        if len(label) > 26:
            label = label[:25] + "…"
        self.text(24, 427, label, N["black"], 11, anchor="w")
        self.text(456, 427, ("сессия " + fmt_hms(self.session_elapsed())) if running else "всего по квесту",
                  "#1a2a9a" if running else N["gray_d"], 11, anchor="e")

        # главная кнопка и стикеры
        if running:
            self.win_button("main", 130, 450, 350, 496, "STOP", "#d4204a", self.toggle, 3)
        else:
            self.win_button("main", 130, 450, 350, 496, "START!", N["title1"], self.toggle, 3)
        sp = 0.3 if running else 0.13
        self.sprite(FOLDER, 66, 488 + math.sin(f * sp) * 3, 3)
        self.sprite(GLOBE, 414, 490 + math.sin(f * sp + 2) * 3, 3)
        self.win_button("add", 400, 506, 468, 538, "ADD", N["black"],
                        lambda: (self.press("add"), self.add_task()), 2)

        self.draw_view_tabs()
        if self.kb_on():
            self.draw_kanban(running, f)
        else:
            self.draw_list(running, f)
        self.draw_items()
        self.draw_level(running, f, today)
        self.draw_popups(running, f)

    def pixel_digits(self, s, cx, top, scale, color, shadow=N["ink"]):
        widths = [3 if ch in ": " else 5 for ch in s]
        total = sum(w * scale for w in widths) + (len(s) - 1) * scale
        x = cx - total / 2
        for ch, w in zip(s, widths):
            if ch != " ":
                self.ptext(ch, x, top, scale, color, shadow=shadow)
            x += (w + 1) * scale

    def draw_room(self, running, f):
        # небо в окне: облака, перекладины рамы
        for cl in self.clouds:
            cl[0] -= cl[2] * (2 if running else 1)
            if cl[0] < SKY[0] - 30:
                cl[0] = SKY[2] + 30
            self.sprite(CLOUD, cl[0], cl[1], 2, clip=SKY)
        self.rect(367, SKY[1], 371, SKY[3], N["wood"])
        self.rect(SKY[0], 150, SKY[2], 154, N["wood"])

        # экран телевизора
        a, b, c, d = SCREEN
        if running:
            self.rect(a, b, c, d, "#0b1a4a")
            sy = b + (f * 2) % (d - b)
            self.rect(a, sy, c, sy + 2, "#1f3a8a")
            if (f // 5) % 2:
                self.ptext(">", a + 4, b + 4, 1, N["green"])
            self.ptext("PLAY", a + 10, b + 4, 1, N["green"])
            self.pixel_digits(fmt_hms(self.session_elapsed()), (a + c) / 2, b + 18, 1, N["cyan"], shadow=None)
            self.sprite(HEART, (a + c) / 2, d - 3 - abs(math.sin(f * 0.3)) * 6, 1.5)
            if f % 14 == 0:
                self.particles.append({"kind": "note", "x": 84, "y": 168, "vx": 0, "vy": -1.1, "life": 26,
                                       "gravity": False, "ph": random.uniform(0, 6)})
        else:
            for y in range(b, d, 5):
                for x in range(a, c, 5):
                    self.rect(x, y, min(x + 5, c), min(y + 5, d), random.choice(NOISE[:6]))
            if (f // 12) % 2:
                self.rect(a + 6, b + 18, c - 6, b + 30, N["ink"])
                self.ptext("NO SIGNAL", (a + c) / 2, b + 21, 1, N["white"], anchor="center")

        # призрак на диване
        self.draw_ghost(running, f, 362, 262)

        # пар над кружкой
        if f % 6 == 0:
            self.particles.append({"kind": "steam", "x": 210 + random.uniform(-2, 2), "y": 254, "vx": 0,
                                   "vy": -0.6, "life": 22, "gravity": False, "ph": random.uniform(0, 6)})

        # пузыри и рыбки
        if self.data["fx"]:
            for i, bub in enumerate(self.bubbles):
                bub["y"] -= bub["speed"] * (1.6 if running else 1)
                bub["x"] += math.sin(f * 0.05 + bub["ph"]) * 0.4
                if bub["y"] < ROOM[1] - 20:
                    self.bubbles[i] = bub = self.new_bubble()
                for ci, cj, col in RINGS[bub["r"]]:
                    x, y = bub["x"] + ci * 2, bub["y"] + cj * 2
                    self.rect(x, y, x + 2, y + 2, col, clip=ROOM)
                hx, hy = bub["x"] - bub["r"], bub["y"] - bub["r"]
                self.rect(hx, hy, hx + 2, hy + 2, N["white"], clip=ROOM)
            if f % (160 if running else 260) == 0:
                going_left = random.random() < 0.5
                self.fish.append({"x": ROOM[2] + 30 if going_left else ROOM[0] - 30,
                                  "y": random.uniform(118, 180), "vx": -1.6 if going_left else 1.6,
                                  "ph": random.uniform(0, 6)})
            alive = []
            for fish in self.fish:
                fish["x"] += fish["vx"] * (1.5 if running else 1)
                if ROOM[0] - 40 < fish["x"] < ROOM[2] + 40:
                    alive.append(fish)
                    self.sprite(FISH, fish["x"], fish["y"] + math.sin(f * 0.2 + fish["ph"]) * 4, 2.5,
                                flip=fish["vx"] > 0, clip=ROOM)
            self.fish = alive

        # частицы
        for p in self.particles:
            k = p["kind"]
            if k == "sparkle":
                self.sprite(pt.SPARKLE, p["x"], p["y"], 2 if p["life"] % 4 < 2 else 3)
            elif k == "heart":
                self.sprite(HEART, p["x"], p["y"], 3)
            elif k == "z":
                self.ptext("Z", p["x"], p["y"], 1 if p["life"] > 20 else 2, N["white"])
            elif k == "text":
                self.ptext(p["text"], p["x"], p["y"], 2, N["cyan"], anchor="center", shadow=N["ink"])
            elif k == "steam":
                s = 3 if p["life"] > 11 else 2
                self.rect(p["x"], p["y"], p["x"] + s, p["y"] + s, mix("#ffffff", "#4a2b4c", 1 - p["life"] / 22))
            elif k == "note":
                self.text(p["x"], p["y"], "♪", N["pink"] if p["life"] % 8 < 4 else N["cyan"], 13)
            elif k == "drop":
                self.rect(p["x"], p["y"], p["x"] + 3, p["y"] + 5, "#8fd8ff")
            elif k == "puff":
                s = 4 + (20 - p["life"]) * 0.6
                self.rect(p["x"] - s / 2, p["y"] - s / 2, p["x"] + s / 2, p["y"] + s / 2,
                          mix("#ffffff", "#4a2b4c", (20 - p["life"]) / 20))

    def scare_ghost(self):
        """Пасхалка: призрак пугается от клика и исчезает на 15 секунд."""
        if self.ghost_state is None:
            self.ghost_state = ("scared", self.f)
            for dx in (-26, -18, 18, 26):
                self.particles.append({"kind": "drop", "x": 362 + dx, "y": 214, "vx": dx / 30, "vy": -1.5,
                                       "life": 16})

    def dissolve(self, rows, cx, bottom, s, keep):
        """Рисует спрайт «рассыпанным»: видна только доля клеток keep (0…1)."""
        w, h = len(rows[0]), len(rows)
        x0, y0 = cx - w * s / 2, bottom - h * s
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != "." and ((i * 7 + j * 13) % 17) / 17 < keep:
                    self.rect(round(x0 + i * s), round(y0 + j * s), round(x0 + (i + 1) * s),
                              round(y0 + (j + 1) * s), P2[ch])

    def draw_ghost(self, running, f, gx, gb):
        st = self.ghost_state
        if st and st[0] == "gone":
            self.sprite(PAD, gx, gb, 3)  # брошенный джойстик на диване
            if time.time() >= st[1]:
                self.ghost_state = ("back", f)
                self.burst("sparkle", gx, gb - 30, 12)
            return
        if st and st[0] == "scared":
            k = f - st[1]
            self.sprite(PAD, gx, gb, 3)
            if k < 12:  # вздрогнул, подпрыгнул, «!»
                self.sprite(GHOST_SCARED, gx + (3 if k % 2 else -3), gb - min(k, 6) * 2, 3.5)
                if (k // 2) % 2 == 0:
                    self.ptext("!", gx + 34, gb - 80, 4, N["yellow"], shadow=N["red"])
            elif k < 24:  # растворяется в воздухе
                self.dissolve(GHOST_SCARED, gx, gb - 12 - (k - 12) * 3, 3.5, 1 - (k - 12) / 12)
                if k == 22:
                    for _ in range(8):
                        a = random.uniform(0, math.tau)
                        self.particles.append({"kind": "puff", "x": gx + math.cos(a) * 14,
                                               "y": gb - 60 + math.sin(a) * 14, "vx": math.cos(a) * 1.2,
                                               "vy": math.sin(a) * 1.2 - 0.5, "life": 20})
            else:
                self.ghost_state = ("gone", time.time() + GHOST_AWAY_SEC)
            return
        if st and st[0] == "back":
            k = f - st[1]
            if k < 12:  # проявляется обратно
                self.dissolve(GHOST if running else GHOST_SLEEP, gx, gb, 3.5, (k + 1) / 12)
                return
            self.ghost_state = None
        if running:
            frame = GHOST_SLEEP if f % 50 in (0, 1) else (GHOST_PRESS if (f // 3) % 2 else GHOST)
            self.sprite(frame, gx, gb + math.sin(f * 0.3) * 3, 3.5)
        else:
            self.sprite(GHOST_SLEEP, gx, gb + math.sin(f * 0.1) * 2, 3.5)
            if f % 24 == 0:
                self.particles.append({"kind": "z", "x": gx + 30, "y": gb - 60, "vx": 0, "vy": -0.9, "life": 34})
        self.hits.append((gx - 28, gb - 58, gx + 28, gb, self.scare_ghost))

    # ── режим «Канбан» (общая логика — kanban.py) ─────────────────────────
    KB_AREA = (18, 574, 462, 712)   # журнал квестов
    KB_TABS = (456, 553, 570, 84)
    KB_SKIN = "2000"

    def kb_theme(self):
        return {"cols": {"todo": N["violet"], "doing": N["pink"], "done": N["green"]}, "col_bg": N["panel"],
                "tint": 0.82, "head_text": N["ink"], "card_bg": N["row"], "card_line": N["sel"], "text": N["white"],
                "dim": N["yellow"], "run": N["green"], "mark_off": N["sel"],
                "tab_on_bg": N["sel"], "tab_on_line": N["cyan"], "tab_on_text": N["cyan"],
                "tab_off_bg": N["row"], "tab_off_line": N["sel"], "tab_off_text": N["violet"],
                "font": self.font, "tab_labels": ("☰ Список", "▦ Канбан")}

    def draw_list(self, running, f):
        tasks = self.data["tasks"]
        if not tasks:
            self.text(W / 2, 640, "пусто… добавь квест выше ↑", N["violet"], 12)
        for idx in range(self.scroll, min(len(tasks), self.scroll + self.ROWS)):
            t = tasks[idx]
            y = self.LIST_TOP + (idx - self.scroll) * self.ROW_H
            is_run = running and running["task_id"] == t["id"]
            is_sel = t["id"] == self.data["selected"]
            self.rect(22, y, 454, y + 28, N["sel"] if is_sel else N["row"])
            if is_sel:
                self.rect(22, y, 26, y + 28, N["pink"] if is_run else N["cyan"])
            name = t["name"] if len(t["name"]) <= 27 else t["name"][:26] + "…"
            name = done_prefix(self, t) + name
            marker = ("▶ " if (f // 5) % 2 else "▷ ") if is_run else ""
            self.text(34, y + 14, marker + name, N["white"], 12, anchor="w", shadow=N["ink"])
            self.text(426, y + 14, fmt_hms(self.task_total(t["id"])),
                      N["green"] if is_run else N["yellow"], 12, anchor="e", shadow=N["ink"])
            self.text(442, y + 14, "✕", N["red"], 12)
            tid = t["id"]
            self.hits.append((22, y, 430, y + 28, lambda tid=tid: self.select(tid)))
            self.hits.append((432, y, 454, y + 28, lambda tid=tid: self.delete_task(tid)))
        if len(tasks) > self.ROWS:
            bar_h = self.ROWS * self.ROW_H - 4
            knob = max(16, bar_h * self.ROWS / len(tasks))
            pos = (bar_h - knob) * self.scroll / (len(tasks) - self.ROWS)
            self.rect(457, self.LIST_TOP, 461, self.LIST_TOP + bar_h, N["row"])
            self.rect(457, self.LIST_TOP + pos, 461, self.LIST_TOP + pos + knob, N["cyan"])

    def draw_items(self):
        actions = [("csv", self.export_csv, None), ("top", self.toggle_top, self.topmost),
                   ("fx", self.toggle_fx, self.data["fx"]), ("clear", self.clear_tasks, None),
                   ("skin", self.switch_skin, None)]
        for i, (name, cb, state) in enumerate(actions):
            sx = SLOT_X0 + i * SLOT_STEP
            if state is not None:
                self.rect(sx + SLOT_W - 9, 739, sx + SLOT_W - 4, 744, N["green"] if state else "#3a3550")
            if self.pressed.get(name, -1) >= self.f:
                self.rect(sx, 735, sx + SLOT_W, 779, "", N["white"], 3)
            self.hits.append((sx, 735, sx + SLOT_W, 795, cb))

    def draw_level(self, running, f, today):
        lv, xp = self.level()
        if lv > self.last_lv and running:
            self.burst("sparkle", 240, 200, 18)
            self.show_toast(f"LEVEL UP! ★ LV {lv}", 40)
        self.last_lv = lv
        self.ptext(f"LV {lv:02d}", 274, 740, 3, N["yellow"], shadow=N["ink"])
        self.ptext(f"{int(xp * 25):02d}/25", 274, 768, 2, N["white"], shadow=N["ink"])
        self.ptext("MIN", 352, 775, 1, N["violet"])
        self.bar(274, 788, 392, 800, xp, N["red"])
        if self.ghost_state and self.ghost_state[0] in ("scared", "gone"):
            if (f // 6) % 2:
                self.ptext("?", 429, 752, 5, N["violet"], anchor="center", shadow=N["ink"])
            return
        frame = GHOST if running else (GHOST_SLEEP if (f // 30) % 3 == 0 else GHOST)
        self.sprite(frame, 429, 799 + (math.sin(f * 0.3) * 2 if running else 0), 3)

    def draw_popups(self, running, f):
        if not running and self.data["tasks"] and time.time() - self.idle_since > IDLE_SEC:
            self.win_window(100, 116, 380, 232, "HELLO!!")
            self.rect(105, 141, 375, 227, N["gray"])
            self.ptext("ARE YOU HERE??", 240, 158, 2, N["black"], anchor="center")
            self.win_button("maybe", 170, 186, 310, 218, "MAYBE...", N["black"], self.dismiss_idle, 2)
        if self.toast and self.toast[1] >= f:
            tw = max(220, len(self.toast[0]) * 8 + 40)
            x1, x2 = W / 2 - tw / 2, W / 2 + tw / 2
            self.win_window(x1, 100, x2, 160, "MESSAGE")
            self.text(W / 2, 141, self.toast[0], N["black"], 11)


def main():
    import task_quest  # единое приложение со скинами
    task_quest.main("2000")


if __name__ == "__main__":
    main()
