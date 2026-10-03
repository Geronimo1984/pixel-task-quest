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
from moon_art import LUNA_ALPH, LUNA_BLINK, LUNA_BLINK_AT, LUNA_BODY, LUNA_COLORS, LUNA_TAIL, LUNA_TAIL_AT
import task_quest_2000 as tq
from pixel_tracker import HEART, SPARKLE, STAR, fmt_hms, lighten, mix, moon_cells

W, H = 480, 800

M = {
    "bg": "#0b1033", "body": "#5a2f8f", "body_d": "#3a1a66", "frame": "#ff8ad8", "line": "#8a5ad0",
    "panel": "#2a1446", "well": "#170b2e", "grid": "#26164a", "pink": "#ff6fb5", "hot": "#ff3d8b",
    "lilac": "#c9a8ff", "yellow": "#ffd84a", "mint": "#5fe0a0", "white": "#ffffff", "ink": "#1a0a33",
    "ctrl": "#d98ae8", "ctrl_l": "#f2b8ff", "ctrl_d": "#a85ac8",
    # окно мессенджера
    "xp1": "#2b6fe6", "xp2": "#0a4fd6", "xp3": "#0841b8", "xp_hi": "#5d9bff", "xp_red": "#e5482f",
    "xp_body": "#e9edff", "xp_body2": "#d3dcfb", "xp_border": "#0a4ec4", "xp_list": "#ffffff",
    "xp_line": "#9aaee8", "xp_sel": "#cfdcff", "xp_sel_line": "#7a96e8", "xp_text": "#1a2a6a",
    "xp_dim": "#5a6ab0", "xp_status": "#dfe5fb",
}

P3 = dict(tq.P2)
P3.update({"K": "#2a1446", "L": "#b48cf0", "l": "#8a64d0", "P": "#ff6fb5", "R": "#ff3d8b", "W": "#ffffff",
           "Y": "#ffd84a", "O": "#ffb02e", "V": "#7a4aa8", "G": "#3ddc84", "B": "#2f6fd9", "w": "#f4e8ff"})

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

PURR_FRAMES = 45  # ≈ 3.5 секунды мурчания

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
RIDER_EVERY = 320  # кадров между пролётами (≈ 25 секунд)

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
PIECE_COLORS = {"I": "#4fc3ff", "O": "#ffc94a", "T": "#b06bff", "S": "#5fe0a0",
                "Z": "#ff5fa8", "J": "#6f7bff", "L": "#ff8a5c"}


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


def art_image(rows, alph=LUNA_ALPH, colors=LUNA_COLORS):
    """Собирает PhotoImage из строк пиксель-арта (прозрачные клетки — «.»)."""
    lut = {ch: colors[k] for k, ch in enumerate(alph)}
    img = tk.PhotoImage(width=len(rows[0]), height=len(rows))
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            ch = row[x]
            if ch == ".":
                x += 1
                continue
            k = x
            while k < len(row) and row[k] == ch:
                k += 1
            img.put(lut[ch], to=(x, y, k, y + 1))
            x = k
    return img


CRANE_FILE = os.path.join(pt.APP_DIR, "assets", "crane.png")  # автомат Kirby Crane Fever, 130×215
CRANE_AT = (175, 62)  # левый верхний угол картинки в стакане
CRANE_STARS = [(32, 172), (45, 170), (57, 175), (74, 180), (95, 172), (109, 171), (16, 186), (113, 40)]

LUNA_TOP = 252  # кошка стоит на дне правой нижней панели (y 392)


def disk_cells(r):
    return [(i, j) for j in range(-r, r + 1) for i in range(-r, r + 1) if math.hypot(i, j) <= r + 0.3]


DISKS = {r: disk_cells(r) for r in (4, 5, 7, 9)}

WELL_X, WELL_Y, CELL = 140, 50, 20       # стакан 10×17 клеток
PANEL_L, PANEL_R = (18, 126), (354, 462)  # колонки автомата
XP = (36, 478, 444, 796)                  # окно мессенджера
ROUND_BTNS = [("csv", "CSV", "#ff6fb5"), ("top", "TOP", "#4fa8ff"), ("fx", "FX", "#b06bff"),
              ("clear", "CLR", "#ff8a5c"), ("skin", "SKIN", "#3fd8c0")]


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
        self.purr_until = -1
        self.luna_body, self.luna_blink = art_image(LUNA_BODY), art_image(LUNA_BLINK)
        # хвост по рядам: каждый ряд сдвигается отдельно, чтобы хвост изгибался, а не съезжал целиком
        self.luna_tail = [(r, len(row) - len(row.lstrip(".")), art_image([row.strip(".")]))
                          for r, row in enumerate(LUNA_TAIL) if row.strip(".")]
        try:
            self.crane = tk.PhotoImage(file=CRANE_FILE)
        except tk.TclError:
            self.crane = None  # без картинки на паузе остаётся сияющее сердце
        self.rider = None

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
        self.cv.create_text(x1 + 27, y1 + h / 2 + 1, text=title, fill="#0a2a7a", font=self.ui(11, True),
                            anchor="w", tags=self.layer)
        self.cv.create_text(x1 + 26, y1 + h / 2, text=title, fill=M["white"], font=self.ui(11, True),
                            anchor="w", tags=self.layer)
        self.msprite(BUDDY, x1 + 14, y1 + h / 2 + 8, 2 if h > 20 else 1.5)
        if buttons:
            for k, col in enumerate(("#3c82f6", "#3c82f6", M["xp_red"])):
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
            self.rect(0, 470 + i * 14, W, 470 + (i + 1) * 14, mix("#0b1033", "#22307a", i / 23))
        for _ in range(40):
            x, y = rnd.randrange(0, W), rnd.randrange(474, 790)
            self.rect(x, y, x + 2, y + 2, rnd.choice(("#dfe6ff", "#ffd84a", "#c9a8ff")))
        for i, j in DISKS[9]:
            self.rect(460 + i * 2, 520 + j * 2, 462 + i * 2, 522 + j * 2,
                      "#e8ecff" if i * 0.8 + j < 4 else "#c4cbe8")
        for cx, cy in ((456, 514), (464, 526)):
            self.rect(cx, cy, cx + 4, cy + 4, "#b4bce0")
        x = 0
        while x < W:
            bw, bh = rnd.randint(18, 40), rnd.randint(30, 90)
            self.rect(x, 800 - bh, x + bw, 800, "#0a0f2a")
            for wy in range(800 - bh + 6, 796, 10):
                for wx in range(x + 4, x + bw - 4, 8):
                    if rnd.random() < 0.3:
                        self.rect(wx, wy, wx + 3, wy + 4, "#ffd84a")
            x += bw + rnd.randint(0, 6)

        # корпус автомата
        self.rect(6, 6, 474, 470, M["frame"])
        self.rect(9, 9, 471, 467, M["body"])
        for y in range(9, 467, 6):  # мягкая диагональная штриховка
            self.rect(9, y, 471, y + 1, "#5f3496")
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
        self.last_lv = lv
        self.ptext(f"LV {lv:02d}", cx, 226, 2, M["lilac"], anchor="center", shadow=M["ink"])
        filled = int(xp * 5)
        for i in range(5):
            on = i < filled or (i == filled and running and (f // 4) % 2)
            self.sprite(HEART, 36 + i * 18, 256, 2, color=None if on else M["line"], pal=P3)
        # пудреница с крыльями
        bob = math.sin(f * (0.2 if running else 0.08)) * 3
        self.msprite(WING, 38, 336 + bob, 2.5, flip=True)
        self.msprite(WING, 106, 336 + bob, 2.5)
        self.msprite(COMPACT, cx, 356 + bob, 3)
        if running and f % 10 == 0:
            self.particles.append({"kind": "sparkle", "x": cx + random.uniform(-30, 30), "y": 300,
                                   "vx": 0, "vy": -0.6, "life": 14, "gravity": False})

        rx = sum(PANEL_R) / 2
        self.draw_next(rx)
        if running:
            if (f // 6) % 2:
                self.ptext("PLAY", rx, 200, 3, M["mint"], anchor="center", shadow=M["ink"])
        else:
            self.ptext("PAUSE", rx, 200, 3, M["pink"], anchor="center", shadow=M["ink"])
        self.draw_luna(rx, running, f)
        self.draw_well(running, f)

        # бегущая строка с именем квеста
        name = sel["name"] if sel else "выбери квест"
        if len(name) > 40:
            name = name[:39] + "…"
        self.text(W / 2, 413, f"♥ {name} ♥", M["pink"], 12)

        self.draw_controls(running, f)
        self.draw_messenger(running, f, today)
        self.draw_particles()
        self.draw_rider(running, f)
        if self.toast and self.toast[1] >= f:
            tw = max(220, len(self.toast[0]) * 8 + 40)
            x1, x2 = W / 2 - tw / 2, W / 2 + tw / 2
            self.rect(x1 - 1, 179, x2 + 1, 241, M["xp_border"])
            self.xp_titlebar(x1, 180, x2, 200, "Quest Messenger", buttons=False)
            self.rect(x1, 200, x2, 240, M["xp_body"])
            self.uitext(W / 2, 220, self.toast[0], M["xp_text"], 12, True, anchor="center")

    def draw_luna(self, rx, running, f):
        """Чёрная кошка: машет хвостом, моргает, дремлет на паузе, мурлычет по клику."""
        purring = f < self.purr_until
        lively = running or purring
        dx = (1 if f % 2 else -1) if purring else 0
        dy = -1 if (running and (f // 10) % 2) else 0
        x0, y0 = rx - len(LUNA_BODY[0]) / 2 + dx, LUNA_TOP + dy
        # хвост изгибается: кончик качается сильнее всего, основание неподвижно
        amp = 3 if lively else 1.5
        phase = f * (0.3 if lively else 0.1)
        last = len(LUNA_TAIL) - 1
        for r, lead, img in self.luna_tail:
            k = ((last - r) / last) ** 1.5
            off = round(math.sin(phase - k * 1.2) * amp * k)
            self.cv.create_image(x0 + LUNA_TAIL_AT[0] + lead + off, y0 + LUNA_TAIL_AT[1] + r, image=img,
                                 anchor="nw", tags=self.layer)
        self.cv.create_image(x0, y0, image=self.luna_body, anchor="nw", tags=self.layer)
        # глаз: во время работы иногда моргает, на паузе дремлет и изредка открывает глаз
        if purring:
            closed = True
        elif running:
            closed = f % 55 in (0, 1, 2)
        else:
            closed = not (60 <= f % 130 < 84)
        if closed:
            self.cv.create_image(x0 + LUNA_BLINK_AT[0], y0 + LUNA_BLINK_AT[1], image=self.luna_blink,
                                 anchor="nw", tags=self.layer)
        if purring:  # пасхалка: мурлычет, вокруг парят сердечки
            if f % 4 == 0:
                self.particles.append({"kind": "float", "x": rx + random.uniform(-40, 30), "y": 280,
                                       "vx": 0, "vy": -1.3, "life": 32, "gravity": False,
                                       "ph": random.uniform(0, 6)})
            if f % 15 == 0:
                self.particles.append({"kind": "purr", "x": rx + random.choice((-30, 30)), "y": 268,
                                       "vx": 0, "vy": -0.8, "life": 22, "gravity": False})
        elif not running and f % 26 == 0:
            self.particles.append({"kind": "z", "x": rx + 30, "y": 262, "vx": 0, "vy": -0.7, "life": 30})
        self.hits.append((rx - 57, LUNA_TOP, rx + 57, 392, self.pet_kitty))

    def start(self):
        super().start()
        if self.data["running"]:
            self.launch_rider()  # на старте Кирби пролетает по экрану

    def launch_rider(self):
        if self.rider is None and self.data["fx"]:
            self.rider = {"x": -70.0, "base": random.choice((26, 474)), "trail": [], "loop": None}

    def rider_loop(self):
        """Клик по Кирби — мёртвая петля с сердечками."""
        if self.rider and self.rider["loop"] is None:
            self.rider["loop"] = self.f
            self.burst("heart", self.rider["x"], self.rider["base"], 8)

    def draw_rider(self, running, f):
        if self.rider is None:
            if f % RIDER_EVERY == RIDER_EVERY // 2:
                self.launch_rider()
            return
        r = self.rider
        r["x"] += 3.2 * (1.3 if running else 1)
        x, y = r["x"], r["base"] + math.sin(r["x"] * 0.035) * 8
        if r["loop"] is not None:
            k = f - r["loop"]
            if k < 24:
                a = k / 24 * math.tau
                x, y = x + math.sin(a) * 30, y - (1 - math.cos(a)) * 30
            else:
                r["loop"] = None
        r["trail"].append((x, y))
        del r["trail"][:-48]
        w, h = len(KIRBY[0]) * RIDER_SCALE, len(KIRBY) * RIDER_SCALE
        bob = math.sin(f * 0.5) * 2
        # радужный хвост тянется от левого края картинки, с пиксельной «волной»
        for i in range(1, len(r["trail"])):
            (x1, y1), (x2, _) = r["trail"][i - 1], r["trail"][i]
            wave = RIDER_SCALE if ((len(r["trail"]) - i + f // 2) // 4) % 2 else 0
            left, right = min(x1, x2) - w / 2, max(x1, x2) - w / 2 + 1
            top = y1 + h / 2 - h + wave
            for row, col in KIRBY_TRAIL.items():
                self.rect(left, top + row * RIDER_SCALE, right, top + (row + 1) * RIDER_SCALE, col)
        if f % 5 == 0:
            self.particles.append({"kind": "sparkle", "x": x - w / 2, "y": y + random.uniform(-6, 20),
                                   "vx": -0.5, "vy": 0, "life": 10, "gravity": False})
        self.sprite(KIRBY_BLINK if f % 40 in (0, 1) else KIRBY, x, y + h / 2 + bob, RIDER_SCALE, pal=KIRBY_PAL)
        self.hits.append((x - w / 2, y - h / 2, x + w / 2, y + h / 2, self.rider_loop))
        if x > W + 90:
            self.rider = None

    def pet_kitty(self):
        """Пасхалка: погладить кошечку."""
        self.purr_until = self.f + PURR_FRAMES

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
        if not running and self.crane:
            # на паузе в стакане стоит автомат Kirby Crane Fever, звёздочки мерцают
            x0, y0 = CRANE_AT
            w, h = self.crane.width(), self.crane.height()
            self.rect(x0 - 4, y0 - 4, x0 + w + 4, y0 + h + 4, M["frame"])
            self.rect(x0 - 2, y0 - 2, x0 + w + 2, y0 + h + 2, M["line"])
            self.cv.create_image(x0, y0, image=self.crane, anchor="nw", tags=self.layer)
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
            self.rect(381, 513 + i, 433, 514 + i, mix("#ffffff", "#c8d4f6", (1 - i / 25) if down else i / 25))
        self.uitext(407 + (1 if down else 0), 526, "Add", M["xp_text"], 12, True, anchor="center")
        self.hits.append((380, 512, 434, 540, lambda: (self.press("add"), self.add_task())))

        tasks = self.data["tasks"]
        self.uitext(56, 561, f"▾ Квесты ({len(tasks)})", "#1a3a9a", 11, True)
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
                col = "#3ddc84" if idx % 2 else "#2f6fd9"
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
            elif k == "purr":
                self.text(p["x"], p["y"], "мрр~", M["pink"] if p["life"] % 6 < 3 else M["lilac"], 11)


def main():
    import task_quest  # единое приложение со скинами
    task_quest.main("moon")


if __name__ == "__main__":
    main()
