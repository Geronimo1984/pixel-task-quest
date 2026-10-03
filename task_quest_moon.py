#!/usr/bin/env python3
"""Скин «Moon» для Task Quest.

Волшебный аркадный автомат с крылатым сердцем и падающими блоками-сердечками,
окно мессенджера в духе Windows XP со списком квестов и ночное небо с луной.

Запуск:  python3 task_quest.py moon
"""
import math
import os
import random
import time
import tkinter as tk
from tkinter import font as tkfont

import pixel_tracker as pt
import task_quest_2000 as tq
from pixel_tracker import HEART, SPARKLE, STAR, fmt_hms, lighten, mix, moon_cells

W, H = 480, 800

M = {  # пастельная ночь — в тон автомату, Кирби, Синнамоли и Сейлор Мун
    "bg": "#141640", "body": "#4b4296", "body_d": "#322b70", "frame": "#f6a3d6", "line": "#9a92ec",
    "panel": "#23245a", "well": "#181a46", "grid": "#24275e", "pink": "#ff8cc6", "hot": "#ff5fa2",
    "lilac": "#c7b6ff", "yellow": "#ffdf7a", "mint": "#8fe3c4", "white": "#ffffff", "ink": "#12123a",
    "ctrl": "#c99cf0", "ctrl_l": "#e9cbff", "ctrl_d": "#9a72d6",
    # окно мессенджера — тот же индиго, только светлее
    "xp1": "#7b97f2", "xp2": "#5874e0", "xp3": "#4660c8", "xp_hi": "#aebfff", "xp_red": "#f06a8a",
    "xp_body": "#eef0ff", "xp_body2": "#dde2fb", "xp_border": "#4660c8", "xp_list": "#ffffff",
    "xp_line": "#a9b6ec", "xp_sel": "#dbe2ff", "xp_sel_line": "#8b9cec", "xp_text": "#26306e",
    "xp_dim": "#6d76b4", "xp_status": "#e3e7fb",
}

P3 = dict(tq.P2)
P3.update({"K": "#2a2466", "L": "#c7b6ff", "l": "#9a92ec", "P": "#ff8cc6", "R": "#ff5fa2", "W": "#ffffff",
           "Y": "#ffdf7a", "O": "#ffbf6b", "V": "#8a7fd6", "G": "#8fe3c4", "B": "#8f9cff", "w": "#f6efff"})

# ── Спрайты (оригинальные) ──────────────────────────────────────────────────
BIG_HEART = [
    "..KKK...KKK..",
    ".KPPPK.KPPPK.",
    "KPWWPPKPPPPPK",
    "KPWPPPPPPPPPK",
    "KPPPPPPPPPPPK",
    ".KPPPPPPPPPK.",
    "..KPPPPPPPK..",
    "...KPPPPPK...",
    "....KPPPK....",
    ".....KPK.....",
    "......K......",
]

WING = [
    "V.........",
    "wV..V.....",
    "wwVVwV.V..",
    "wwwwwwVwV.",
    "wwwwwwwwwV",
    ".wwwwwwwwV",
    "..VVVVVVV.",
]


# Кирби на звезде — точная копия присланной картинки (64×64, фон вырезан)
KIRBY_PAL = {"a": "#690322", "b": "#da7591", "c": "#dd9baa", "d": "#9b0238", "e": "#dfd0c4", "f": "#da2261", "g": "#db9a04", "h": "#ddd702", "i": "#4b9c15", "j": "#026fc5", "k": "#6a3175", "z": "#010200"}
KIRBY = [
    "...............aabbbbbaa.........",
    ".............abbcccccccbba.......",
    "............abcccccccccccbd......",
    "...........abcccccccccccccba.....",
    ".......aabbbbccccccccccccccb.....",
    "......abcccbbcccccccabccabcca....",
    "......acccccbcccccccezccezccbb...",
    "......bcccccbcccccccdzccdzccbca..",
    "......acccccbccccccczzcczzccbcb..",
    ".......bbbbbbccbbbbcbaccbaccbcb..",
    "........abbbbccffffcbbccbbffbcb..",
    "..........abbcccccccccccccccba...",
    "..........abbccccccccccaccbba....",
    ".........aabbcccccccccccccbb.....",
    ".........afdbbbcccccccccbbba.....",
    "........aeffdbbbbbbbbbbbbba......",
    "........affffdbbbbbbbbbbbaa......",
    "..aaaaa.afffddaddbbbbbdddddaa....",
    ".aggggggaaaaaaaaaaaaaddddffdaa...",
    "agghhhhgggggggggggggaddddfffdaa..",
    "agghhhhhhhgggggggggggaddddffdaga.",
    "hagghhhhhhhhggggggggggaddddddggga",
    "hhaagghhhhhhhhggggggggggaadagggga",
    "iiiiaagggghhhhhhhhhhhhhggggggggga",
    "iiiiiiaggghhhheehhhhhhhhhhhhhhga.",
    "jjjjjjjagghhhheehhhgghhhhhhhhhhga",
    "jjjjjjjagghhhhhhhhggggghhhhhhhhga",
    "kkkkkkkkagghhhggggaaaaagggghhhhga",
    "kkkkkkkkkaaaaaaaaakkkkkaaaaaaaaa.",
]
KIRBY_BLINK = KIRBY[:6] + [
    "......acccccbcccccccccccccccbb...",
    "......bcccccbcccccccdcccdcccbca..",
    "......acccccbcccccccaaccaaccbcb..",
] + KIRBY[9:]
KIRBY_TRAIL = {21: "#ddd702", 22: "#ddd702", 23: "#4b9c15", 24: "#4b9c15", 25: "#026fc5", 26: "#026fc5", 27: "#6a3175", 28: "#6a3175"}  # ряды радуги
RIDER_SCALE = 2
CINNA_PAUSE = 36  # кадров между пролётами Синнаморола (≈ 3 секунды)
CINNA_LANE = 740  # высота полёта — в подвале экрана, над строкой статуса и ночным городом
CINNA_LOOP = (16, 0.13)  # радиус петли и скорость вращения: петля, пока вращение быстрее полёта вперёд
KIRBY_CENTER = (424, 316)  # Кирби мчится на звезде в правой нижней панели
KIRBY_HOP = 18  # кадров прыжка по клику

# волшебная пудреница с сердцем
COMPACT = [
    ".....KKKKKK.....",
    "...KKYYYYYYKK...",
    "..KYYOOOOOOYYK..",
    ".KYOOPPPPPPOOYK.",
    ".KYOPPPPPPPPOYK.",
    "KYOPPRRPPRRPPOYK",
    "KYOPRWRRRRRRPOYK",
    "KYOPRRRRRRRRPOYK",
    "KYOPPRRRRRRPPOYK",
    "KYOPPPRRRRPPPOYK",
    ".KYOPPPRRPPPOYK.",
    ".KYOOPPPPPPOOYK.",
    "..KYYOOOOOOYYK..",
    "...KKYYYYYYKK...",
    ".....KKKKKK.....",
]

BUDDY = [
    "..GG..BB..",
    ".GGGGBBBB.",
    ".GGGGBBBB.",
    "..GG..BB..",
    ".GGGGBBBB.",
    "GGGGGBBBBB",
    "GGGGGBBBBB",
    "GGGGGBBBBB",
]
PERSON = ["..XX..", ".XXXX.", ".XXXX.", "..XX..", ".XXXX.", "XXXXXX", "XXXXXX"]

# ── «Тетрис» из сердечек, который играет сам ────────────────────────────────
SHAPES = {
    "I": [(0, 0), (1, 0), (2, 0), (3, 0)],
    "O": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "T": [(0, 0), (1, 0), (2, 0), (1, 1)],
    "S": [(1, 0), (2, 0), (0, 1), (1, 1)],
    "Z": [(0, 0), (1, 0), (1, 1), (2, 1)],
    "J": [(0, 0), (0, 1), (1, 1), (2, 1)],
    "L": [(2, 0), (0, 1), (1, 1), (2, 1)],
}
PIECE_COLORS = {"I": "#8fd3ff", "O": "#ffd98a", "T": "#b9a0ff", "S": "#95e6c4",
                "Z": "#ff9cc9", "J": "#8f9cff", "L": "#ffb38f"}


def _rotations(cells):
    out, cur = [], cells
    for _ in range(4):
        mx, my = min(x for x, _ in cur), min(y for _, y in cur)
        norm = tuple(sorted((x - mx, y - my) for x, y in cur))
        if norm not in out:
            out.append(norm)
        cur = [(y, -x) for x, y in cur]
    return out


ROTS = {k: _rotations(v) for k, v in SHAPES.items()}


class HeartStack:
    COLS, ROWS = 10, 17

    def __init__(self):
        self.board = [[None] * self.COLS for _ in range(self.ROWS)]
        for r in range(self.ROWS - 4, self.ROWS):  # стартовый «завал», чтобы стакан не был пустым
            for c in range(self.COLS):
                if random.random() < 0.7:
                    self.board[r][c] = random.choice(list(PIECE_COLORS.values()))
            self.board[r][random.randrange(self.COLS)] = None
        self.queue = [random.choice(list(SHAPES)) for _ in range(3)]
        self.piece = None
        self.clearing = []
        self.clear_t = 0
        self.spawn()

    def fits(self, cells, x, y):
        for cx, cy in cells:
            bx, by = x + cx, y + cy
            if bx < 0 or bx >= self.COLS or by >= self.ROWS:
                return False
            if by >= 0 and self.board[by][bx] is not None:
                return False
        return True

    def landing(self, cells, x):
        y = -4
        if not self.fits(cells, x, y):
            return None
        while self.fits(cells, x, y + 1):
            y += 1
        return y

    def rate(self, cells, x, y):
        """Чем меньше — тем лучше ход: невысокий ровный стакан без дырок."""
        b = [row[:] for row in self.board]
        for cx, cy in cells:
            if y + cy < 0:
                return math.inf
            b[y + cy][x + cx] = "#"
        lines = sum(all(v is not None for v in row) for row in b)
        heights, holes = [], 0
        for c in range(self.COLS):
            top = next((r for r in range(self.ROWS) if b[r][c] is not None), self.ROWS)
            heights.append(self.ROWS - top)
            holes += sum(1 for r in range(top, self.ROWS) if b[r][c] is None)
        bump = sum(abs(heights[i] - heights[i + 1]) for i in range(self.COLS - 1))
        return sum(heights) * 0.5 + holes * 3.5 + bump * 0.35 - lines * 6 + random.uniform(0, 1.5)

    def spawn(self):
        kind = self.queue.pop(0)
        self.queue.append(random.choice(list(SHAPES)))
        best = None
        for cells in ROTS[kind]:
            width = max(cx for cx, _ in cells) + 1
            for x in range(self.COLS - width + 1):
                y = self.landing(cells, x)
                if y is not None:
                    score = self.rate(cells, x, y)
                    if best is None or score < best[0]:
                        best = (score, cells, x)
        if best is None or best[0] == math.inf:
            self.board = [[None] * self.COLS for _ in range(self.ROWS)]
            return self.spawn()
        _, cells, x = best
        self.piece = {"kind": kind, "cells": cells, "x": x, "y": -max(cy for _, cy in cells) - 1}

    def step(self):
        """Один шаг падения. Возвращает число собранных линий, -1 если стакан переполнился."""
        if self.clear_t:
            self.clear_t -= 1
            if not self.clear_t:
                for r in sorted(self.clearing):
                    del self.board[r]
                    self.board.insert(0, [None] * self.COLS)
                self.clearing = []
                self.spawn()
            return 0
        p = self.piece
        if self.fits(p["cells"], p["x"], p["y"] + 1):
            p["y"] += 1
            return 0
        overflow = False
        for cx, cy in p["cells"]:
            if p["y"] + cy < 0:
                overflow = True
            else:
                self.board[p["y"] + cy][p["x"] + cx] = PIECE_COLORS[p["kind"]]
        self.piece = None
        if overflow:
            self.board = [[None] * self.COLS for _ in range(self.ROWS)]
            self.spawn()
            return -1
        full = [r for r, row in enumerate(self.board) if all(v is not None for v in row)]
        if full:
            self.clearing, self.clear_t = full, 4
            return len(full)
        self.spawn()
        return 0


ASSETS = os.path.join(pt.APP_DIR, "assets")

# Hello Kitty — портрет 100×120 в левой нижней панели (точная копия кадра из картинки)
KITTY_AT = (22, 272)
KITTY_EYES = [(36, 56), (38, 56), (35, 57), (36, 57), (38, 57), (39, 57), (36, 58), (37, 58), (38, 58), (39, 58),
              (36, 59), (37, 59), (38, 59), (39, 59), (35, 60), (36, 60), (37, 60), (39, 60), (36, 61), (38, 61),
              (64, 53), (65, 53), (66, 53), (65, 54), (66, 54), (63, 55), (64, 55), (65, 55), (66, 55), (67, 55),
              (63, 56), (64, 56), (65, 56), (66, 56), (67, 56), (64, 57), (65, 57), (67, 57), (64, 58), (65, 58),
              (66, 58)]
KITTY_LIDS = [(35, 59, 40, 60), (63, 56, 68, 57)]  # закрытые глазки — тонкие чёрточки
KITTY_SPARKS = [(11, 25), (89, 34)]

# Синнаморол — круглый кадр (радиус 30, в 1,5 раза меньше исходного) с облачком;
# края растворяются в мыльных пузырях
CINNA_R = 30
CINNA_EYES = [(37, 21), (38, 21), (37, 22), (38, 22), (25, 23), (26, 23), (37, 23), (38, 23), (24, 24), (25, 24),
              (26, 24)]
CINNA_LIDS = [(24, 24, 27, 25), (36, 23, 39, 24)]
CINNA_BUBBLES = 16  # пузырей по контуру

# Сейлор Мун — появляется в стакане, когда сессия завершена или новый уровень
SAILOR_FRAMES = 64  # ≈ 5 секунд
CRANE_AT = (175, 62)  # левый верхний угол картинки в стакане
CLAW_AT = (61, 75)    # где клешня висит на картинке автомата
CLAW_SPLIT = (88, 9)  # с какого ряда начинаются зубцы и где середина клешни
CLAW_CYCLE = 90       # кадров на «попытку достать игрушку» (≈ 7 секунд)
CRANE_STARS = [(32, 172), (45, 170), (57, 175), (74, 180), (95, 172), (109, 171), (16, 186), (113, 40)]



def disk_cells(r):
    return [(i, j) for j in range(-r, r + 1) for i in range(-r, r + 1) if math.hypot(i, j) <= r + 0.3]


DISKS = {r: disk_cells(r) for r in (4, 5, 7, 9)}

WELL_X, WELL_Y, CELL = 140, 50, 20       # стакан 10×17 клеток
PANEL_L, PANEL_R = (18, 126), (354, 462)  # колонки автомата
XP = (36, 478, 444, 796)                  # окно мессенджера
ROUND_BTNS = [("csv", "CSV", "#ff9cc9"), ("top", "TOP", "#8fd3ff"), ("fx", "FX", "#b9a0ff"),
              ("clear", "CLR", "#ffb38f"), ("skin", "SKIN", "#95e6c4")]


class AppMoon(tq.App2):
    ROWS = 6
    ROW_H = 30
    LIST_TOP = 574

    def __init__(self, root):  # noqa: своя сцена, как и у скина 2000
        self.root = root
        root.title("Task Quest · Moon")
        root.resizable(False, False)
        root.configure(bg=M["bg"])
        families = set(tkfont.families())
        fam = next((f for f in ("Menlo", "Monaco", "Courier New", "Courier") if f in families), "TkFixedFont")
        ui = next((f for f in ("Tahoma", "Verdana") if f in families), fam)
        self.font = lambda size, bold=True: (fam, size, "bold" if bold else "normal")
        self.ui = lambda size, bold=False: (ui, size, "bold" if bold else "normal")

        self.cv = tk.Canvas(root, width=W, height=H, bg=M["bg"], highlightthickness=0)
        self.cv.pack()
        self.on_switch = None

        self.f = 0
        self.layer = "dyn"
        self.particles = []
        self.pressed = {}
        self.hits = []
        self.scroll = 0
        self.toast = None
        self.topmost = False
        self.idle_since = time.time()
        self.stack = HeartStack()
        self.kirby_hop = -KIRBY_HOP
        self.crane = self.load_asset("crane_empty.png") or self.load_asset("crane.png")
        claw = self.load_asset("crane_claw.png")
        self.claw_parts = None
        if claw and self.crane:
            # голова и два зубца отдельно — чтобы зубцы сжимались
            w, h = claw.width(), claw.height()
            top = CLAW_SPLIT[0] - CLAW_AT[1]
            parts = []
            for (x1, y1, x2, y2) in ((0, 0, w, top), (0, top, CLAW_SPLIT[1], h), (CLAW_SPLIT[1], top, w, h)):
                part = tk.PhotoImage(width=x2 - x1, height=y2 - y1)
                part.tk.call(part, "copy", claw, "-from", x1, y1, x2, y2)
                parts.append((part, x1, y1))
            self.claw_parts = parts
        self.kitty = self.load_asset("kitty.png")
        self.cinna_img = self.load_asset("cinna.png")
        self.sailor = self.load_asset("sailor.png")
        if self.sailor:
            self.sailor_part = tk.PhotoImage(width=self.sailor.width(), height=self.sailor.height())
        self.cinna = None
        self.sailor_show = None
        self.kitty_love = -1

        self.load()
        self.data.setdefault("fx", True)
        self.last_lv = self.level()[0]

        self.draw_static()
        self.build_entry()

        self.cv.bind("<Button-1>", self.on_click)
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

    # ── поле ввода в стиле мессенджера ─────────────────────────────────────
    def build_entry(self):
        self.entry = tk.Entry(self.root, font=self.ui(13), bg=M["xp_list"], fg=M["xp_text"],
                              insertbackground=M["hot"], relief="flat",
                              highlightthickness=2, highlightbackground=M["xp_line"], highlightcolor=M["pink"])
        self.cv.create_window(46, 512, anchor="nw", window=self.entry, width=326, height=28)
        self.placeholder = "новый квест..."
        self.placeholder_on = False
        self.set_placeholder()
        self.entry.bind("<FocusIn>", self.clear_placeholder)
        self.entry.bind("<FocusOut>", lambda e: self.set_placeholder())
        self.entry.bind("<Return>", self.add_task)

    def set_placeholder(self):
        if not self.entry.get():
            self.placeholder_on = True
            self.entry.config(fg=M["xp_dim"])
            self.entry.insert(0, self.placeholder)

    def clear_placeholder(self, _e=None):
        if self.placeholder_on:
            self.entry.delete(0, "end")
            self.entry.config(fg=M["xp_text"])
            self.placeholder_on = False

    def toggle_fx(self):
        self.press("fx")
        self.data["fx"] = not self.data["fx"]
        self.save()
        self.show_toast("Анимации: " + ("ВКЛ" if self.data["fx"] else "ВЫКЛ"), 20)

    # ── примитивы ─────────────────────────────────────────────────────────
    def msprite(self, rows, cx, bottom, s, flip=False, clip=None):
        self.sprite(rows, cx, bottom, s, flip=flip, clip=clip, pal=P3)

    def uitext(self, x, y, s, color, size=11, bold=False, anchor="w"):
        self.cv.create_text(x, y, text=s, fill=color, font=self.ui(size, bold), anchor=anchor, tags=self.layer)

    def disk(self, cx, cy, r, s, color):
        for i, j in DISKS[r]:
            self.rect(cx + i * s - s / 2, cy + j * s - s / 2, cx + i * s + s / 2, cy + j * s + s / 2, color)

    def round_button(self, cx, cy, color, down=False):
        self.disk(cx, cy, 5, 2, pt.App.darken(color, 0.4))
        self.disk(cx, cy + (1 if down else 0), 4, 2, pt.App.darken(color, 0.15) if down else color)
        if not down:
            self.rect(cx - 5, cy - 6, cx - 1, cy - 2, lighten(color, 0.6))

    def block(self, x, y, color, s=CELL):
        self.rect(x, y, x + s, y + s, pt.App.darken(color, 0.4))
        self.rect(x + 2, y + 2, x + s - 2, y + s - 2, color)
        self.rect(x + 2, y + 2, x + s - 2, y + 4, lighten(color, 0.45))
        k = s / 20  # сердечко 5×4 внутри блока
        hx, hy, lc = x + 5 * k, y + 6 * k, lighten(color, 0.3)
        for x1, y1, x2, y2 in ((2, 0, 4, 2), (6, 0, 8, 2), (0, 2, 10, 4), (2, 4, 8, 6), (4, 6, 6, 8)):
            self.rect(hx + x1 * k, hy + y1 * k, hx + x2 * k, hy + y2 * k, lc)

    def cab_panel(self, x1, y1, x2, y2, label=None):
        self.rect(x1, y1, x2, y2, M["frame"])
        self.rect(x1 + 2, y1 + 2, x2 - 2, y2 - 2, M["line"])
        self.rect(x1 + 4, y1 + 4, x2 - 4, y2 - 4, M["panel"])
        if label:
            self.ptext(label, (x1 + x2) / 2, y1 + 8, 2, M["frame"], anchor="center", shadow=M["ink"])

    def xp_titlebar(self, x1, y1, x2, y2, title, buttons=True):
        h = y2 - y1
        for i in range(h):
            t = i / max(1, h - 1)
            col = mix(M["xp1"], M["xp2"], t * 2) if t < 0.5 else mix(M["xp2"], M["xp3"], (t - 0.5) * 2)
            self.rect(x1, y1 + i, x2, y1 + i + 1, col)
        self.rect(x1 + 2, y1 + 1, x2 - 2, y1 + 2, M["xp_hi"])
        self.cv.create_text(x1 + 27, y1 + h / 2 + 1, text=title, fill="#26306e", font=self.ui(11, True),
                            anchor="w", tags=self.layer)
        self.cv.create_text(x1 + 26, y1 + h / 2, text=title, fill=M["white"], font=self.ui(11, True),
                            anchor="w", tags=self.layer)
        self.msprite(BUDDY, x1 + 14, y1 + h / 2 + 8, 2 if h > 20 else 1.5)
        if buttons:
            for k, col in enumerate((M["xp2"], M["xp2"], M["xp_red"])):
                bx2 = x2 - 6 - (2 - k) * 24
                bx1, by1, by2 = bx2 - 20, y1 + 3, y2 - 3
                self.rect(bx1, by1, bx2, by2, M["white"])
                self.rect(bx1 + 1, by1 + 1, bx2 - 1, by2 - 1, col)
                if k == 0:
                    self.rect(bx1 + 5, by2 - 7, bx1 + 12, by2 - 5, M["white"])
                elif k == 1:
                    self.rect(bx1 + 5, by1 + 4, bx2 - 5, by2 - 4, M["white"])
                    self.rect(bx1 + 6, by1 + 7, bx2 - 6, by2 - 5, col)
                else:
                    self.ptext("X", (bx1 + bx2) / 2, by1 + 3, 2 if h > 20 else 1, M["white"], anchor="center")

    # ── статичный слой ────────────────────────────────────────────────────
    def draw_static(self):
        self.layer = "static"
        rnd = random.Random(1999)

        # ночное небо, звёзды, луна, город
        for i in range(24):
            self.rect(0, 470 + i * 14, W, 470 + (i + 1) * 14, mix("#141640", "#2c3478", i / 23))
        for _ in range(40):
            x, y = rnd.randrange(0, W), rnd.randrange(474, 790)
            self.rect(x, y, x + 2, y + 2, rnd.choice(("#e3e7ff", "#ffdf7a", "#c7b6ff")))
        for i, j in DISKS[9]:
            self.rect(460 + i * 2, 520 + j * 2, 462 + i * 2, 522 + j * 2,
                      "#e8ecff" if i * 0.8 + j < 4 else "#c4cbe8")
        for cx, cy in ((456, 514), (464, 526)):
            self.rect(cx, cy, cx + 4, cy + 4, "#b4bce0")
        x = 0
        while x < W:
            bw, bh = rnd.randint(18, 40), rnd.randint(30, 90)
            self.rect(x, 800 - bh, x + bw, 800, "#10122e")
            for wy in range(800 - bh + 6, 796, 10):
                for wx in range(x + 4, x + bw - 4, 8):
                    if rnd.random() < 0.3:
                        self.rect(wx, wy, wx + 3, wy + 4, "#ffdf7a")
            x += bw + rnd.randint(0, 6)

        # корпус автомата
        self.rect(6, 6, 474, 470, M["frame"])
        self.rect(9, 9, 471, 467, M["body"])
        for y in range(9, 467, 6):  # мягкая диагональная штриховка
            self.rect(9, y, 471, y + 1, "#5249a2")
        # полумесяцы и звёздочки по углам
        for i, j in moon_cells(5, 3):
            self.rect(16 + i * 3, 10 + j * 3, 19 + i * 3, 13 + j * 3, M["yellow"])
            self.rect(431 + (10 - i) * 3, 10 + j * 3, 434 + (10 - i) * 3, 13 + j * 3, M["yellow"])
        for sx, sy in ((62, 20), (412, 20), (90, 34), (386, 34)):
            self.msprite(SPARKLE, sx, sy, 2)

        # колонки
        l1, l2 = PANEL_L
        self.cab_panel(l1, 48, l2, 96, "TIME")
        self.cab_panel(l1, 100, l2, 148, "SESSION")
        self.cab_panel(l1, 152, l2, 200, "TODAY")
        self.cab_panel(l1, 204, l2, 262, "LEVEL")
        self.cab_panel(l1, 268, l2, 396)
        r1, r2 = PANEL_R
        self.cab_panel(r1, 48, r2, 170, "NEXT")
        self.cab_panel(r1, 174, r2, 226, "STATUS")
        self.cab_panel(r1, 230, r2, 396)

        # стакан
        self.rect(WELL_X - 6, WELL_Y - 6, WELL_X + 10 * CELL + 6, WELL_Y + 17 * CELL + 6, M["frame"])
        self.rect(WELL_X - 3, WELL_Y - 3, WELL_X + 10 * CELL + 3, WELL_Y + 17 * CELL + 3, M["line"])
        self.rect(WELL_X, WELL_Y, WELL_X + 10 * CELL, WELL_Y + 17 * CELL, M["well"])
        for c in range(1, 10):
            self.rect(WELL_X + c * CELL, WELL_Y, WELL_X + c * CELL + 1, WELL_Y + 17 * CELL, M["grid"])
        for r in range(1, 17):
            self.rect(WELL_X, WELL_Y + r * CELL, WELL_X + 10 * CELL, WELL_Y + r * CELL + 1, M["grid"])

        # бегущая строка и пульт
        self.rect(14, 402, 466, 424, M["frame"])
        self.rect(16, 404, 464, 422, M["ink"])
        self.rect(14, 428, 466, 466, M["ctrl_d"])
        self.rect(14, 428, 466, 463, M["ctrl"])
        self.rect(14, 428, 466, 431, M["ctrl_l"])
        self.rect(28, 448, 64, 458, M["body_d"])
        self.msprite(STAR, 106, 454, 2)
        self.msprite(WING, 87, 452, 1.5, flip=True)
        self.msprite(WING, 125, 452, 1.5)
        for i, (_, label, _) in enumerate(ROUND_BTNS):
            self.ptext(label, 352 + i * 25, 456, 1, M["body_d"], anchor="center")

        # окно мессенджера
        x1, y1, x2, y2 = XP
        self.rect(x1, y1, x2, y2, M["xp_border"])
        for i in range(12):
            yy = y1 + 26 + i * (y2 - y1 - 29) / 12
            self.rect(x1 + 3, yy, x2 - 3, yy + (y2 - y1 - 29) / 12 + 1, mix(M["xp_body"], M["xp_body2"], i / 11))
        self.xp_titlebar(x1, y1, x2, y1 + 26, "Quest Messenger")
        self.rect(46, 548, 434, 756, M["xp_line"])
        self.rect(47, 549, 433, 755, M["xp_list"])
        self.rect(x1 + 3, 762, x2 - 3, 763, M["xp_line"])
        self.layer = "dyn"

    # ── кадр ───────────────────────────────────────────────────────────────
    def redraw(self):
        self.cv.delete("dyn")
        self.hits = []
        running = self.data["running"]
        f = self.f
        sel = self.task(self.data["selected"])
        today = self.today_total()

        # корона: крылатое сердце
        glow = abs(math.sin(f * (0.25 if running else 0.08)))
        self.msprite(WING, 207, 36 - glow * 2, 3, flip=True)
        self.msprite(WING, 273, 36 - glow * 2, 3)
        self.msprite(BIG_HEART, 240, 42, 3)
        if glow > 0.85:
            self.msprite(SPARKLE, 252, 18, 2)

        # колонки
        cx = sum(PANEL_L) / 2
        total = self.task_total(sel["id"]) if sel else 0
        self.pixel_digits(fmt_hms(total), cx, 72, 2, M["pink"], shadow=M["ink"])
        self.pixel_digits(fmt_hms(self.session_elapsed()), cx, 124, 2,
                          M["mint"] if running else M["line"], shadow=M["ink"])
        self.pixel_digits(fmt_hms(today), cx, 176, 2, M["yellow"], shadow=M["ink"])
        lv, xp = self.level()
        if lv > self.last_lv and running:
            self.burst("sparkle", 240, 200, 18)
            self.show_toast(f"LEVEL UP! ★ LV {lv}", 40)
            self.sailor_show = f
        self.last_lv = lv
        self.ptext(f"LV {lv:02d}", cx, 226, 2, M["lilac"], anchor="center", shadow=M["ink"])
        filled = int(xp * 5)
        for i in range(5):
            on = i < filled or (i == filled and running and (f // 4) % 2)
            self.sprite(HEART, 36 + i * 18, 256, 2, color=None if on else M["line"], pal=P3)
        if self.kitty:
            self.draw_kitty(running, f)
        else:  # без картинки — прежняя крылатая пудреница
            bob = math.sin(f * (0.2 if running else 0.08)) * 3
            self.msprite(WING, 38, 336 + bob, 2.5, flip=True)
            self.msprite(WING, 106, 336 + bob, 2.5)
            self.msprite(COMPACT, cx, 356 + bob, 3)

        rx = sum(PANEL_R) / 2
        self.draw_next(rx)
        if running:
            if (f // 6) % 2:
                self.ptext("PLAY", rx, 200, 3, M["mint"], anchor="center", shadow=M["ink"])
        else:
            self.ptext("PAUSE", rx, 200, 3, M["pink"], anchor="center", shadow=M["ink"])
        self.draw_kirby(running, f)
        self.draw_well(running, f)

        # бегущая строка с именем квеста
        name = sel["name"] if sel else "выбери квест"
        if len(name) > 40:
            name = name[:39] + "…"
        self.text(W / 2, 413, f"♥ {name} ♥", M["pink"], 12)

        self.draw_controls(running, f)
        self.draw_messenger(running, f, today)
        self.draw_particles()
        self.draw_cinna(running, f)
        if self.toast and self.toast[1] >= f:
            tw = max(220, len(self.toast[0]) * 8 + 40)
            x1, x2 = W / 2 - tw / 2, W / 2 + tw / 2
            self.rect(x1 - 1, 179, x2 + 1, 241, M["xp_border"])
            self.xp_titlebar(x1, 180, x2, 200, "Quest Messenger", buttons=False)
            self.rect(x1, 200, x2, 240, M["xp_body"])
            self.uitext(W / 2, 220, self.toast[0], M["xp_text"], 12, True, anchor="center")

    def kirby_happy(self):
        """Клик по Кирби — подпрыгивает на звезде, жмурится, сердечки."""
        self.kirby_hop = self.f
        self.burst("heart", KIRBY_CENTER[0], KIRBY_CENTER[1] - 20, 8)

    def draw_kirby(self, running, f):
        """Кирби мчится на звезде на месте: радуга струится назад, звезда покачивается, мимо летят искры."""
        s = RIDER_SCALE
        w, h = len(KIRBY[0]) * s, len(KIRBY) * s
        hop = f - self.kirby_hop
        lively = running or hop < KIRBY_HOP
        bob = math.sin(f * (0.45 if lively else 0.15)) * (3 if lively else 2)
        jump = -math.sin(hop / KIRBY_HOP * math.pi) * 22 if hop < KIRBY_HOP else 0
        cx, cy = KIRBY_CENTER[0], KIRBY_CENTER[1] + bob + jump
        top, left = cy - h / 2, cx - w / 2
        x1, y1, x2, y2 = PANEL_R[0] + 4, 234, PANEL_R[1] - 4, 392
        # радужный хвост от левого края панели до звезды, волна бежит назад
        trail_top = KIRBY_CENTER[1] + bob - h / 2
        speed = 3 if lively else 1
        for x in range(x1, int(left) + 4, 4):
            wave = s if ((x + f * speed) // 10) % 2 else 0
            for row, col in KIRBY_TRAIL.items():
                ty = trail_top + row * s + wave
                self.rect(x, ty, min(x + 4, left + 4), ty + s, col)
        if f % (3 if lively else 7) == 0:  # встречные искры — ощущение скорости
            self.particles.append({"kind": "sparkle", "x": x2, "y": random.uniform(y1 + 8, y2 - 8),
                                   "vx": -3.5 if lively else -2, "vy": 0, "life": 26 if lively else 44,
                                   "gravity": False})
        closed = hop < KIRBY_HOP or f % 40 in (0, 1)
        self.sprite(KIRBY_BLINK if closed else KIRBY, cx, cy + h / 2, s, pal=KIRBY_PAL)
        self.hits.append((left, top, left + w, top + h, self.kirby_happy))

    def draw_claw(self, x0, y0, f):
        """Клешня опускается на тросе к игрушкам, сжимает зубцы и поднимается обратно."""
        k = f % CLAW_CYCLE
        if k < 20:
            drop, grip = 0, 0                       # висит, чуть покачиваясь
        elif k < 40:
            drop, grip = (k - 20) * 0.7, 0           # опускается
        elif k < 52:
            drop, grip = 14, min(2, (k - 40) // 3)   # сжимает зубцы
        elif k < 72:
            drop, grip = 14 - (k - 52) * 0.7, 2      # поднимается с добычей
        else:
            drop, grip = 0, 2 if k < 80 else 1       # отпускает
        sway = round(math.sin(f * 0.15)) if k < 20 else 0
        cx, cy = x0 + CLAW_AT[0] + sway, y0 + CLAW_AT[1] + round(drop)
        if drop >= 1:  # трос тянется от крепления до клешни
            self.rect(x0 + CLAW_AT[0] + 8, y0 + CLAW_AT[1], x0 + CLAW_AT[0] + 10, cy + 1, "#9a96b8")
        (head, hx, hy), (left, lx, ly), (right, rx, ry) = self.claw_parts
        self.cv.create_image(cx + hx, cy + hy, image=head, anchor="nw", tags=self.layer)
        self.cv.create_image(cx + lx + grip, cy + ly, image=left, anchor="nw", tags=self.layer)
        self.cv.create_image(cx + rx - grip, cy + ry, image=right, anchor="nw", tags=self.layer)
        if k == 46:
            self.particles.append({"kind": "sparkle", "x": cx + 9, "y": cy + 26, "vx": 0, "vy": -0.5,
                                   "life": 12, "gravity": False})

    def load_asset(self, name):
        try:
            return tk.PhotoImage(file=os.path.join(ASSETS, name))
        except tk.TclError:
            return None

    def stop(self):
        was_running = bool(self.data["running"])
        super().stop()
        if was_running:
            self.sailor_show = self.f  # сессия завершена — появляется Сейлор Мун

    def love_kitty(self):
        """Клик по Hello Kitty — вокруг неё взлетают сердечки."""
        self.kitty_love = self.f + 30
        self.burst("heart", KITTY_AT[0] + 50, KITTY_AT[1] + 60, 6)

    def draw_kitty(self, running, f):
        x0, y0 = KITTY_AT
        self.cv.create_image(x0, y0, image=self.kitty, anchor="nw", tags=self.layer)
        # моргает раз в несколько секунд (и жмурится, когда её любят)
        if f % 47 in (0, 1, 2) or f < self.kitty_love:
            for i, j in KITTY_EYES:
                self.rect(x0 + i, y0 + j, x0 + i + 1, y0 + j + 1, "#f7ede3")
            for a, b, c, d in KITTY_LIDS:
                self.rect(x0 + a, y0 + b, x0 + c, y0 + d, "#3b2622")
        for k, (sx, sy) in enumerate(KITTY_SPARKS):  # искорки на листьях мерцают
            if (f // 3 + k * 9) % 18 < 4:
                self.msprite(SPARKLE, x0 + sx, y0 + sy + 3, 2)
        if f < self.kitty_love and f % 4 == 0:
            self.particles.append({"kind": "float", "x": x0 + random.uniform(20, 80), "y": y0 + 40,
                                   "vx": 0, "vy": -1.2, "life": 28, "gravity": False, "ph": random.uniform(0, 6)})
        self.hits.append((x0, y0, x0 + 100, y0 + 120, self.love_kitty))

    def launch_cinna(self):
        if self.cinna is None and self.cinna_img and self.data["fx"]:
            self.cinna_dir = -getattr(self, "cinna_dir", 1)  # туда-обратно по очереди
            self.cinna = {"x": W + 60.0 if self.cinna_dir < 0 else -60.0, "base": CINNA_LANE, "hearts": -1,
                          "phase": 0.0, "pos": (0, CINNA_LANE),
                          "bubbles": [{"a": k / CINNA_BUBBLES * math.tau + random.uniform(-0.12, 0.12),
                                       "d": random.uniform(CINNA_R - 6, CINNA_R + 1),
                                       "r": random.choice((2, 2, 3, 3, 3, 4, 4, 5)),
                                       "ph": random.uniform(0, math.tau)} for k in range(CINNA_BUBBLES)]}

    def poke_cinna(self):
        if self.cinna:
            self.cinna["hearts"] = self.f + 16
            self.burst("heart", *self.cinna["pos"], 10)

    def draw_cinna(self, running, f):
        """Синнаморол в пузыре летает петлями по подвалу экрана — туда и обратно, моргая."""
        if self.cinna is None:
            self.cinna_wait = getattr(self, "cinna_wait", 0) + 1
            if self.cinna_wait > CINNA_PAUSE:
                self.cinna_wait = 0
                self.launch_cinna()
            return
        c = self.cinna
        boost = 1.3 if running else 1
        c["x"] += 1.35 * boost * self.cinna_dir
        c["phase"] += CINNA_LOOP[1] * boost
        # петля: вращение по кругу поверх движения вперёд (в сторону полёта)
        r = CINNA_LOOP[0]
        x = round(c["x"] - math.sin(c["phase"]) * r * self.cinna_dir)
        y = round(c["base"] - (1 - math.cos(c["phase"])) * r)
        c["pos"] = (x, y)
        x0, y0 = x - CINNA_R, y - CINNA_R
        self.cv.create_image(x0, y0, image=self.cinna_img, anchor="nw", tags=self.layer)
        if f % 50 in (0, 1, 2) or f < c["hearts"]:
            for i, j in CINNA_EYES:
                self.rect(x0 + i, y0 + j, x0 + i + 1, y0 + j + 1, "#cbd3f7")
            for a, b, cc, d in CINNA_LIDS:
                self.rect(x0 + a, y0 + b, x0 + cc, y0 + d, "#3b4fb5")
        # мыльные пузыри по растворённому краю: кружат, дышат, иногда отрываются и улетают
        for b in c["bubbles"]:
            a = b["a"] + f * 0.012
            d = b["d"] + math.sin(f * 0.11 + b["ph"]) * 1.7
            r = max(2, min(5, b["r"] + round(math.sin(f * 0.08 + b["ph"]))))
            bx, by = round(x + math.cos(a) * d), round(y + math.sin(a) * d)
            for i, j, col in tq.RINGS[r]:
                self.rect(bx + i, by + j, bx + i + 1, by + j + 1, col)
            self.rect(bx - r // 2, by - r // 2, bx - r // 2 + 1, by - r // 2 + 1, M["white"])
        if f % 7 == 0:
            a = random.uniform(0, math.tau)
            self.particles.append({"kind": "bubble", "x": round(x + math.cos(a) * CINNA_R),
                                   "y": round(y + math.sin(a) * CINNA_R), "vx": 0.5, "vy": -0.7,
                                   "r": random.choice((2, 2, 3)), "life": 30, "gravity": False})
        self.hits.append((x - CINNA_R, y - CINNA_R, x + CINNA_R, y + CINNA_R, self.poke_cinna))
        if (self.cinna_dir < 0 and c["x"] < -70) or (self.cinna_dir > 0 and c["x"] > W + 70):
            self.cinna = None

    def draw_sailor(self, f):
        """Сейлор Мун поднимается в стакане на фоне луны, стоит в позе и уходит обратно."""
        k = f - self.sailor_show
        if k >= SAILOR_FRAMES:
            self.sailor_show = None
            return
        w, h = self.sailor.width(), self.sailor.height()
        vis = h if 10 <= k < SAILOR_FRAMES - 10 else int(h * (k / 10 if k < 10 else (SAILOR_FRAMES - k) / 10))
        x0, bottom = 240 - w / 2, WELL_Y + 17 * CELL - 2
        glow = min(1, k / 10, (SAILOR_FRAMES - k) / 10)
        for i, j in moon_cells(11, 6):  # большая луна за спиной, как на картинке
            self.rect(166 + i * 6, 120 + j * 6, 172 + i * 6, 126 + j * 6, mix("#f6f1d8", M["well"], 1 - glow))
        if vis > 0:
            self.sailor_part.blank()
            self.sailor_part.tk.call(self.sailor_part, "copy", self.sailor, "-from", 0, h - vis, w, h,
                                     "-to", 0, h - vis)
            bob = round(math.sin(k * 0.3)) if 10 <= k < SAILOR_FRAMES - 10 else 0
            self.cv.create_image(x0, bottom - h + bob, image=self.sailor_part, anchor="nw", tags=self.layer)
        if k % 3 == 0:
            self.particles.append({"kind": "sparkle", "x": 240 + random.uniform(-90, 90),
                                   "y": bottom - random.uniform(20, h), "vx": 0, "vy": -0.4, "life": 12,
                                   "gravity": False})

    def draw_next(self, rx):
        for n, kind in enumerate(self.stack.queue[:2]):
            cells = ROTS[kind][0]
            s = 14 if n == 0 else 10
            w = (max(c for c, _ in cells) + 1) * s
            h = (max(r for _, r in cells) + 1) * s
            top = 74 if n == 0 else 128
            for c, r in cells:
                self.block(rx - w / 2 + c * s, top + (30 - h) / 2 + r * s, PIECE_COLORS[kind], s)

    def draw_well(self, running, f):
        st = self.stack
        if running and self.data["fx"] and f % 2 == 0:
            res = st.step()
            if res > 0:
                for r in st.clearing:
                    self.burst("sparkle", WELL_X + 100, WELL_Y + r * CELL + 10, 6)
            elif res < 0:
                self.burst("heart", 240, 200, 14)
        flash = st.clear_t and (st.clear_t % 2 == 0)
        for r, row in enumerate(st.board):
            for c, col in enumerate(row):
                if col:
                    self.block(WELL_X + c * CELL, WELL_Y + r * CELL,
                               M["white"] if flash and r in st.clearing else col)
        if st.piece and running:
            p = st.piece
            for cx, cy in p["cells"]:
                if p["y"] + cy >= 0:
                    self.block(WELL_X + (p["x"] + cx) * CELL, WELL_Y + (p["y"] + cy) * CELL,
                               PIECE_COLORS[p["kind"]])
        if self.sailor and self.sailor_show is not None:
            self.draw_sailor(f)
        elif not running and self.crane:
            # на паузе в стакане стоит автомат Kirby Crane Fever, звёздочки мерцают
            x0, y0 = CRANE_AT
            w, h = self.crane.width(), self.crane.height()
            self.rect(x0 - 4, y0 - 4, x0 + w + 4, y0 + h + 4, M["frame"])
            self.rect(x0 - 2, y0 - 2, x0 + w + 2, y0 + h + 2, M["line"])
            self.cv.create_image(x0, y0, image=self.crane, anchor="nw", tags=self.layer)
            if self.claw_parts:
                self.draw_claw(x0, y0, f)
            for k, (sx, sy) in enumerate(CRANE_STARS):
                if (f // 3 + k * 5) % 24 < 3:
                    self.msprite(SPARKLE, x0 + sx, y0 + sy + 3, 2)
            if (f // 8) % 2:
                self.rect(150, y0 + h + 10, 330, y0 + h + 30, M["well"])
                self.ptext("PRESS START", 240, y0 + h + 13, 2, M["white"], anchor="center", shadow=M["hot"])
        elif not running:
            # большое сияющее сердце с лучами, как на экране «PRESS START»
            pulse = abs(math.sin(f * 0.1))
            for i in range(9):
                bx = 196 + i * 11
                col = mix(M["pink"], M["well"], 0.35 + 0.5 * abs(math.sin(f * 0.12 + i)))
                self.rect(bx, WELL_Y + 6, bx + 2, 150, col)
            self.msprite(BIG_HEART, 240, 214 + pulse * 3, 6)
            if (f // 8) % 2:
                self.ptext("PRESS START", 240, 236, 2, M["white"], anchor="center", shadow=M["hot"])

    def draw_controls(self, running, f):
        tilt = math.sin(f * 0.6) * 5 if running else 0
        self.rect(44 + tilt / 2, 436, 48 + tilt / 2, 452, M["ink"])
        self.disk(46 + tilt, 436, 5, 2, M["hot"])
        self.rect(42 + tilt, 432, 45 + tilt, 435, lighten(M["hot"], 0.6))

        down = self.pressed.get("main", -1) >= self.f
        col = M["hot"] if running else M["pink"]
        if down:
            col = pt.App.darken(col, 0.2)
        o = 2 if down else 0
        self.disk(166, 447 + o, 7, 2, pt.App.darken(col, 0.35))
        self.disk(314, 447 + o, 7, 2, pt.App.darken(col, 0.35))
        self.rect(166, 433 + o, 314, 462 + o, pt.App.darken(col, 0.35))
        self.rect(166, 435 + o, 314, 459 + o, col)
        self.disk(167, 447 + o, 5, 2, col)
        self.disk(313, 447 + o, 5, 2, col)
        self.rect(170, 437 + o, 310, 440 + o, lighten(col, 0.5))
        self.ptext("STOP" if running else "START", 240, 440 + o, 2, M["white"], anchor="center", shadow=M["ink"])
        self.hits.append((152, 430, 328, 466, self.toggle))

        actions = {"csv": self.export_csv, "top": self.toggle_top, "fx": self.toggle_fx,
                   "clear": self.clear_tasks, "skin": self.switch_skin}
        states = {"top": self.topmost, "fx": self.data["fx"]}
        for i, (name, _, color) in enumerate(ROUND_BTNS):
            bx = 352 + i * 25
            self.round_button(bx, 442, color, self.pressed.get(name, -1) >= self.f)
            if name in states:
                self.rect(bx + 6, 431, bx + 10, 435, M["mint"] if states[name] else M["body_d"])
            self.hits.append((bx - 12, 430, bx + 12, 464, actions[name]))

    def draw_messenger(self, running, f, today):
        # кнопка «Добавить» в стиле XP
        down = self.pressed.get("add", -1) >= self.f
        self.rect(380, 512, 434, 540, M["xp_sel_line"])
        for i in range(26):
            self.rect(381, 513 + i, 433, 514 + i, mix("#ffffff", "#d3dbf8", (1 - i / 25) if down else i / 25))
        self.uitext(407 + (1 if down else 0), 526, "Add", M["xp_text"], 12, True, anchor="center")
        self.hits.append((380, 512, 434, 540, lambda: (self.press("add"), self.add_task())))

        tasks = self.data["tasks"]
        self.uitext(56, 561, f"▾ Квесты ({len(tasks)})", "#3a48a8", 11, True)
        if not tasks:
            self.uitext(240, 650, "пока пусто… добавь квест ↑", M["xp_dim"], 12, anchor="center")
        for idx in range(self.scroll, min(len(tasks), self.scroll + self.ROWS)):
            t = tasks[idx]
            y = self.LIST_TOP + (idx - self.scroll) * self.ROW_H
            is_run = running and running["task_id"] == t["id"]
            is_sel = t["id"] == self.data["selected"]
            if is_sel:
                self.rect(50, y, 430, y + 28, M["xp_sel_line"])
                self.rect(51, y + 1, 429, y + 27, M["xp_sel"])
            if is_run:
                self.sprite(HEART, 64, y + 21, 2 + 0.4 * abs(math.sin(f * 0.3)), pal=P3)
            elif is_sel:
                self.msprite(STAR, 64, y + 23, 2)
            else:
                col = "#7fd6b4" if idx % 2 else "#8f9cff"
                self.sprite(PERSON, 64, y + 22, 2, color=col)
            name = t["name"] if len(t["name"]) <= 30 else t["name"][:29] + "…"
            self.uitext(80, y + 14, name, M["hot"] if is_run else M["xp_text"], 12, is_run)
            self.uitext(404, y + 14, fmt_hms(self.task_total(t["id"])),
                        M["hot"] if is_run else M["xp_dim"], 11, is_run, anchor="e")
            self.uitext(420, y + 14, "✕", M["xp_red"], 11, True, anchor="center")
            tid = t["id"]
            self.hits.append((50, y, 410, y + 28, lambda tid=tid: self.select(tid)))
            self.hits.append((411, y, 430, y + 28, lambda tid=tid: self.delete_task(tid)))
        if len(tasks) > self.ROWS:
            bar_h = self.ROWS * self.ROW_H - 4
            knob = max(16, bar_h * self.ROWS / len(tasks))
            pos = (bar_h - knob) * self.scroll / (len(tasks) - self.ROWS)
            self.rect(428, self.LIST_TOP, 432, self.LIST_TOP + bar_h, M["xp_status"])
            self.rect(428, self.LIST_TOP + pos, 432, self.LIST_TOP + pos + knob, M["xp_sel_line"])

        # строка статуса, как «в сети / отошёл»
        sel = self.task(self.data["selected"])
        if running and sel:
            self.disk(52, 779, 4, 1.5, M["mint"])
            status = f"В работе: {sel['name'][:24]}"
        else:
            self.disk(52, 779, 4, 1.5, "#a0a8c8")
            status = "Пауза"
        self.uitext(62, 779, status, M["xp_text"], 11)
        self.uitext(434, 779, f"сегодня {fmt_hms(today)}", M["xp_dim"], 11, anchor="e")

    def draw_particles(self):
        for p in self.particles:
            k = p["kind"]
            if k == "sparkle":
                self.msprite(SPARKLE, p["x"], p["y"], 2 if p["life"] % 4 < 2 else 3)
            elif k == "heart":
                self.msprite(HEART, p["x"], p["y"], 3)
            elif k == "z":
                self.ptext("Z", p["x"], p["y"], 1 if p["life"] > 18 else 2, M["lilac"])
            elif k == "text":
                self.ptext(p["text"], p["x"], p["y"], 2, M["mint"], anchor="center", shadow=M["ink"])
            elif k == "float":
                self.msprite(HEART, p["x"], p["y"], 2 if p["life"] > 8 else 1.5)
            elif k == "bubble":
                for i, j, col in tq.RINGS[p["r"]]:
                    self.rect(p["x"] + i, p["y"] + j, p["x"] + i + 1, p["y"] + j + 1, col)
                self.rect(p["x"] - p["r"] // 2, p["y"] - p["r"] // 2, p["x"] - p["r"] // 2 + 1,
                          p["y"] - p["r"] // 2 + 1, M["white"])


def main():
    import task_quest  # единое приложение со скинами
    task_quest.main("moon")


if __name__ == "__main__":
    main()
