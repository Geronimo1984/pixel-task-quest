#!/usr/bin/env python3
"""Скин «Terminal» для Task Quest.

Зелёный фосфорный экран старого терминала: командная строка, падающие символы,
буквы из вертикальных штрихов со свечением и полутоновый глаз,
который следит за твоим временем.

Запуск:  python3 task_quest.py term
"""
import math
import os
import random
import time
import tkinter as tk
from tkinter import font as tkfont

import pixel_tracker as pt
import task_quest_2000 as tq
from pixel_tracker import HEART, RAIN_CHARS, RAIN_STEP, RAIN_TRAIL, SPARKLE, fmt_hms, mix
from kanban import done_prefix
from task_quest_2000 import FONT

W, H = 480, 800

G = {
    "bg": "#000000", "scan": "#03120a", "glow": "#0a3d1a", "dim": "#11702f", "mid": "#1fae48",
    "bright": "#39ff6a", "hot": "#c4ffd2", "rain_head": "#2fa856", "rain_tail": "#0c4a22",
}

PROMPT = "C:\\QUEST>"
CMD_BTNS = [("csv", "CSV"), ("top", "TOP"), ("fx", "FX"), ("clear", "CLR"), ("skin", "SKIN")]
FOCUS_SEC = 25 * 60
DAY_GOAL_SEC = 8 * 3600

# ── Полутоновый глаз ────────────────────────────────────────────────────────
EYE_CX, EYE_CY, EYE_HW, EYE_HH, EYE_STEP = 277, 178, 176, 64, 7
EYE_PANEL = (84, 82, 470, 262)

# Заставки в окне экрана: глаз и картинки из assets/term_screens, сменяются раз в SCREEN_SEC или по щелчку
SCREEN_DIR = os.path.join(pt.APP_DIR, "assets", "term_screens")
SCREENS = [("eye", "WATCHING YOUR TIME"), ("rain", "THE RAIN PRESENTS"), ("neo", "WAKE UP, NEO..."),
           ("bullets", "THERE IS NO SPOON")]
SCREEN_SEC = 20
DEFAULT_SCREEN = "neo"   # заставка при запуске скина
SCREEN_IN = 1.6       # секунд на появление (точки загораются каждая в свой момент)
SCREEN_OUT = 1.0      # секунд на исчезновение перед сменой заставки
BREATH_TICKS = 2      # кадров скина на один кадр «дыхания»


def eye_halfheight(dx):
    t = 1 - (dx / EYE_HW) ** 2
    return EYE_HH * t ** 0.8 if t > 0 else 0


EYE_DOTS = []  # (x, y, v) — v: вертикальное положение внутри века от -1 до 1
for _row, _y in enumerate(range(EYE_CY - EYE_HH, EYE_CY + EYE_HH + 1, EYE_STEP)):
    for _x in range(EYE_CX - EYE_HW + (_row % 2) * 3, EYE_CX + EYE_HW + 1, EYE_STEP):
        _hh = eye_halfheight(_x - EYE_CX)
        if _hh > 3 and abs(_y - EYE_CY) <= _hh:
            EYE_DOTS.append((_x, _y, (_y - EYE_CY) / _hh))


def eye_brightness(x, y, v, ix, iy, pupil):
    if math.hypot(x - (ix - 12), y - (iy - 12)) < 7:
        return 1.0  # блик
    d = math.hypot(x - ix, y - iy)
    if d < pupil:
        return 0.0
    if d < 36:  # радужка с лучиками
        return 0.32 + 0.14 * math.sin(math.atan2(y - iy, x - ix) * 9) + 0.18 * d / 36
    if d < 41:
        return 0.14
    return 0.92 - 0.45 * v * v - 0.15 * ((x - EYE_CX) / EYE_HW) ** 2


class AppTerminal(tq.App2):
    ROWS = 8
    ROW_H = 30
    LIST_TOP = 498

    def __init__(self, root):  # noqa: своя сцена, как у остальных скинов
        self.root = root
        root.title("Task Quest · Terminal")
        root.resizable(False, False)
        root.configure(bg=G["bg"])
        families = set(tkfont.families())
        fam = next((f for f in ("Menlo", "Monaco", "Courier New", "Courier") if f in families), "TkFixedFont")
        self.font = lambda size, bold=True: (fam, size, "bold" if bold else "normal")

        self.cv = tk.Canvas(root, width=W, height=H, bg=G["bg"], highlightthickness=0)
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
        self.glitch_until = -1
        self.screen_i = 0
        self.screen_since = time.time()
        # кадры заставок (tools/bake_term_screens.py): появление in_NN и «дыхание» breath_NN; грузятся при первом показе
        self.screen_frames = {}
        self.screen_names = [n for n, _ in SCREENS
                             if n == "eye" or os.path.exists(os.path.join(SCREEN_DIR, n, "breath_00.png"))]
        if DEFAULT_SCREEN in self.screen_names:   # первой показывается Нео
            self.screen_i = [n for n, _ in SCREENS].index(DEFAULT_SCREEN)
        self.typed = ("", 0)
        self.rain = [pt.App.new_drop(x, random.uniform(-H, H)) for x in range(90, W, 14)]
        self.rain_colors = [G["rain_head"]] + [mix(G["rain_tail"], G["bg"], 0.6 * k / RAIN_TRAIL)
                                               for k in range(1, RAIN_TRAIL)]

        self.load()
        self.data.setdefault("fx", True)
        self.last_lv = self.level()[0]

        self.draw_static()
        self.build_entry()

        self.cv.bind("<Button-1>", self.on_click)
        self.kb_init()   # режим «Канбан» вместо вывода dir
        self.cv.bind("<MouseWheel>", self.on_wheel)
        self.cv.bind("<Button-4>", lambda e: self.scroll_by(-1))
        self.cv.bind("<Button-5>", lambda e: self.scroll_by(1))
        root.bind("<space>", self.on_space)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        if not self.data["tasks"]:
            self.show_toast("Добавь первый квест ↓", 60)
        elif self.data["running"]:
            self.show_toast("С возвращением! Таймер шёл", 50)
        self.tick()

    # ── ввод ──────────────────────────────────────────────────────────────
    def build_entry(self):
        self.entry = tk.Entry(self.root, font=self.font(13, False), bg=G["bg"], fg=G["bright"],
                              insertbackground=G["bright"], relief="flat",
                              highlightthickness=1, highlightbackground=G["dim"], highlightcolor=G["bright"])
        self.cv.create_window(170, 434, anchor="nw", window=self.entry, width=240, height=26)
        self.placeholder = "новый квест..."
        self.placeholder_on = False
        self.set_placeholder()
        self.entry.bind("<FocusIn>", self.clear_placeholder)
        self.entry.bind("<FocusOut>", lambda e: self.set_placeholder())
        self.entry.bind("<Return>", self.add_task)

    def set_placeholder(self):
        if not self.entry.get():
            self.placeholder_on = True
            self.entry.config(fg=G["dim"])
            self.entry.insert(0, self.placeholder)

    def clear_placeholder(self, _e=None):
        if self.placeholder_on:
            self.entry.delete(0, "end")
            self.entry.config(fg=G["bright"])
            self.placeholder_on = False

    def toggle_fx(self):
        self.press("fx")
        self.data["fx"] = not self.data["fx"]
        self.save()
        self.show_toast("Падающие символы: " + ("ВКЛ" if self.data["fx"] else "ВЫКЛ"), 20)

    def frames_of(self, name):
        if name not in self.screen_frames:
            folder = os.path.join(SCREEN_DIR, name)
            files = sorted(os.listdir(folder))
            self.screen_frames[name] = {
                kind: [tk.PhotoImage(file=os.path.join(folder, fn)) for fn in files if fn.startswith(kind)]
                for kind in ("in_", "breath_")}
        return self.screen_frames[name]

    def next_screen(self):
        """Следующая заставка (сама — раз в SCREEN_SEC, или щелчок по экрану с картинкой)."""
        names = self.screen_names
        cur = SCREENS[self.screen_i][0]
        nxt = names[(names.index(cur) + 1) % len(names)] if cur in names else names[0]
        self.screen_i = [n for n, _ in SCREENS].index(nxt)
        self.screen_since = time.time()

    def draw_screen(self, name, label, f):
        """Заставка: точки загораются каждая в свой момент, потом вся картинка «дышит» — каждая точка
        мерцает в своей фазе; перед сменой точки гаснут в обратном порядке."""
        x1, y1, x2, y2 = EYE_PANEL
        frames = self.frames_of(name)
        appear, breath = frames["in_"], frames["breath_"]
        t = time.time() - self.screen_since
        if t > SCREEN_SEC - SCREEN_OUT:     # исчезновение — появление наоборот
            k = (SCREEN_SEC - t) / SCREEN_OUT
            img = appear[max(0, min(len(appear) - 1, int(k * len(appear))))]
        elif t < SCREEN_IN:                  # появление
            img = appear[min(len(appear) - 1, int(t / SCREEN_IN * len(appear)))]
        else:                                # «дыхание» по кругу
            img = breath[(f // BREATH_TICKS) % len(breath)]
        self.rect(x1, y1, x2, y2, G["bg"])
        self.cv.create_image(x1 + 1, y1 + 1, image=img, anchor="nw", tags=self.layer)
        sy = y1 + 1 + (f * 5) % img.height()   # бегущая полоса развёртки, как на ЭЛТ
        self.cv.create_rectangle(x1 + 1, sy, x2 - 1, sy + 3, fill=G["bright"], outline="", stipple="gray25",
                                 tags=self.layer)
        for x in range(x1, x2, 6):   # пунктирная рамка, как у глаза
            self.rect(x, y1, x + 3, y1 + 1, G["mid"])
            self.rect(x, y2 - 1, x + 3, y2, G["mid"])
        self.gtext(x1 + 4, y1 + 12, label, G["bright"], 10)
        self.gtext(x2 - 6, y1 + 12, f"[{self.screen_i + 1}/{len(SCREENS)}]", G["mid"], 9, anchor="e")
        self.hits.append((x1, y1, x2, y2, self.next_screen))

    def poke_eye(self):
        """Пасхалка: ткнуть в глаз — экран глючит."""
        self.glitch_until = self.f + 24

    # ── примитивы ─────────────────────────────────────────────────────────
    def gtext(self, x, y, s, color=G["bright"], size=12, anchor="w", bold=False):
        """Текст с лёгким фосфорным свечением."""
        for dx, dy in ((1, 1), (-1, 0)):
            self.cv.create_text(x + dx, y + dy, text=s, fill=G["glow"], font=self.font(size, bold),
                                anchor=anchor, tags=self.layer)
        self.cv.create_text(x, y, text=s, fill=color, font=self.font(size, bold), anchor=anchor, tags=self.layer)

    def stext(self, s, x, top, scale, color, anchor="w", vertical=False):
        """Пиксельные буквы из вертикальных штрихов со свечением, как на экране ЭЛТ."""
        glyphs = [FONT.get(ch, FONT["?"]) for ch in s.upper()]
        widths = [len(g[0]) for g in glyphs]
        if vertical:
            positions = [(x - w * scale / 2, top + i * (7 + 2) * scale) for i, w in enumerate(widths)]
        else:
            total = sum(widths) * scale + (len(glyphs) - 1) * scale
            x0 = x - total / 2 if anchor == "center" else x
            positions, cx = [], x0
            for w in widths:
                positions.append((cx, top))
                cx += (w + 1) * scale
        cells = [(gx + i * scale, gy + j * scale)
                 for g, (gx, gy) in zip(glyphs, positions)
                 for j, row in enumerate(g) for i, px in enumerate(row) if px == "#"]
        if not cells:
            return
        # надпись собирается в картинку один раз (свечение + штрихи) и дальше выводится одним элементом
        ox, oy = round(min(c[0] for c in cells)) - 2, round(min(c[1] for c in cells)) - 2
        w = round(max(c[0] for c in cells)) + scale + 2 - ox
        h = round(max(c[1] for c in cells)) + scale + 2 - oy
        bar = max(1, scale // 3)

        def paint(img):
            for cx, cy in cells:
                img.put(G["glow"], to=(round(cx) - 2 - ox, round(cy) - 2 - oy, round(cx) + scale + 2 - ox,
                                       round(cy) + scale + 2 - oy))
            for cx, cy in cells:
                for k in range(0, scale, bar + 1):
                    img.put(color, to=(round(cx) + k - ox, round(cy) - oy, round(cx) + k + bar - ox,
                                       round(cy) + scale - oy))
        key = ("stext", s.upper(), scale, color, vertical, round(x - ox) if not vertical else 0, anchor)
        self.place(ox, oy, self.cached(key + (w, h), w, h, paint))

    def term_button(self, name, x1, y1, x2, y2, label, cb, size=12, active=False):
        down = self.pressed.get(name, -1) >= self.f
        fill = G["bright"] if down else (G["glow"] if active else G["bg"])
        self.rect(x1, y1, x2, y2, G["bright"] if not down else G["hot"])
        self.rect(x1 + 2, y1 + 2, x2 - 2, y2 - 2, fill)
        self.cv.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=label, fill=G["bg"] if down else G["bright"],
                            font=self.font(size), tags=self.layer)
        self.hits.append((x1, y1, x2, y2, cb))

    # ── статичный слой ────────────────────────────────────────────────────
    def draw_static(self):
        self.begin_static()
        for y in range(0, H, 3):  # строки развёртки
            self.rect(0, y, W, y + 1, G["scan"])
        self.stext("QUEST", 40, 22, 8, G["bright"], vertical=True)
        self.rect(76, 10, 77, 790, G["dim"])
        self.ptext("DAY", 40, 772, 2, G["dim"], anchor="center")
        self.layer = "dyn"

    # ── кадр ───────────────────────────────────────────────────────────────
    def redraw(self):
        self.cv.delete("dyn")
        self.hits = []
        running = self.data["running"]
        f = self.f
        sel = self.task(self.data["selected"])
        today = self.today_total()
        glitch = f < self.glitch_until

        if self.data["fx"]:
            self.draw_rain(running)
        self.draw_day_bar(today, f)
        self.draw_prompt(running, sel, f, glitch)
        if time.time() - self.screen_since > SCREEN_SEC:
            self.next_screen()
        name, label = SCREENS[self.screen_i]
        if name == "eye" or name not in self.screen_names:
            self.draw_eye(running, f, glitch)
        else:
            self.draw_screen(name, label, f)

        # большой таймер — общее время за день
        total = self.task_total(sel["id"]) if sel else 0
        digits = fmt_hms(today)
        if running and (f // 6) % 2:
            digits = digits.replace(":", " ")
        self.stext(digits, 277, 276, 6, G["bright"] if running else G["mid"], anchor="center")
        self.gtext(470, 274, "за день", G["mid"], 10, anchor="e")

        # «Loading..» — прогресс фокус-сессии
        focus = (self.session_elapsed() % FOCUS_SEC) / FOCUS_SEC if running else 0
        dots = "." * (1 + (f // 5) % 3) if running else ".."
        self.gtext(84, 344, ("Loading" if running else "Paused") + dots, G["bright"], 12)
        self.rect(168, 336, 412, 352, G["bright"])
        self.rect(170, 338, 410, 350, G["bg"])
        for i in range(int(focus * 24)):
            self.rect(172 + i * 10, 340, 172 + i * 10 + 7, 348, G["bright"])
        if running and int(focus * 24) < 24 and (f // 4) % 2:
            i = int(focus * 24)
            self.rect(172 + i * 10, 340, 172 + i * 10 + 7, 348, G["dim"])
        self.gtext(470, 344, "FOCUS", G["bright"], 12, anchor="e")

        lv, xp = self.level()
        if lv > self.last_lv and running:
            self.burst("sparkle", 277, 180, 18)
            self.show_toast(f"LEVEL UP ★ LV {lv}", 40)
        self.last_lv = lv
        self.gtext(84, 368, f"> квест {fmt_hms(total)} | сессия {fmt_hms(self.session_elapsed())} | LV {lv:02d}",
                   G["mid"], 11)

        # кнопки-команды
        self.term_button("main", 84, 384, 226, 420, "[ STOP ]" if running else "[ START ]", self.toggle, 16)
        actions = {"csv": self.export_csv, "top": self.toggle_top, "fx": self.toggle_fx,
                   "clear": self.clear_tasks, "skin": self.switch_skin}
        active = {"top": self.topmost, "fx": self.data["fx"]}
        for i, (name, label) in enumerate(CMD_BTNS):
            x1 = 234 + i * 48
            self.term_button(name, x1, 384, x1 + 44, 420, label, actions[name], 10, active.get(name, False))

        # строка ввода
        self.gtext(84, 447, PROMPT, G["bright"], 12)
        self.term_button("add", 418, 434, 470, 460, "ADD", lambda: (self.press("add"), self.add_task()), 11)

        self.gtext(84, 482, f"> dir /quests · {len(self.data['tasks'])} шт.", G["bright"], 12)
        self.draw_view_tabs()
        if self.kb_on():
            self.draw_kanban(running, f)
        else:
            self.draw_list(running, f)

        # подвал
        self.gtext(84, 778, "> TAKE BACK YOUR TIME" + ("_" if (f // 6) % 2 else ""), G["dim"], 11)
        self.gtext(470, 778, f"FX:{'ON' if self.data['fx'] else 'OFF'} TOP:{'ON' if self.topmost else 'OFF'}",
                   G["dim"], 10, anchor="e")

        self.draw_particles()
        if self.toast and self.toast[1] >= f:
            tw = max(220, len(self.toast[0]) * 8 + 40)
            x1, x2 = EYE_CX - tw / 2, EYE_CX + tw / 2
            self.rect(x1, 152, x2, 204, G["bright"])
            self.rect(x1 + 2, 154, x2 - 2, 202, G["bg"])
            self.gtext(EYE_CX, 178, "> " + self.toast[0], G["bright"], 12, anchor="center", bold=True)

    def draw_rain(self, running):
        boost = 1.8 if running else 1
        for i, d in enumerate(self.rain):
            d["y"] += d["speed"] * boost
            if d["y"] - d["len"] * RAIN_STEP > H:
                self.rain[i] = d = pt.App.new_drop(d["x"], random.uniform(-160, 0))
            if random.random() < 0.15:
                d["chars"][random.randrange(RAIN_TRAIL)] = random.choice(RAIN_CHARS)
            head = int(d["y"] // RAIN_STEP)
            for k in range(d["len"]):
                row = head - k
                y = row * RAIN_STEP
                if -RAIN_STEP < y < H:
                    self.cv.create_text(d["x"], y, text=d["chars"][row % RAIN_TRAIL], fill=self.rain_colors[k],
                                        font=self.font(11, False), tags=self.layer)

    def draw_day_bar(self, today, f):
        pct = min(1.0, today / DAY_GOAL_SEC)
        segs = 26
        self.gtext(40, 366, f"{int(pct * 100)}%", G["bright"], 10, anchor="center")
        self.rect(24, 378, 56, 762, G["dim"])
        self.rect(25, 379, 55, 761, G["bg"])
        filled = int(pct * segs)
        for i in range(segs):
            y2 = 758 - i * 14.6
            col = G["bright"] if i < filled else (G["glow"] if i > filled or (f // 4) % 2 else G["dim"])
            self.rect(28, y2 - 11, 52, y2, col)

    def draw_prompt(self, running, sel, f, glitch):
        self.rect(84, 10, 470, 74, G["bg"])
        self.gtext(90, 24, f"{PROMPT} run focus.exe", G["bright"], 12)
        name = (sel["name"] if len(sel["name"]) <= 22 else sel["name"][:21] + "…") if sel else ""
        if glitch:
            line = "> ВНИМАНИЕ: глаз тебя заметил"
        elif not self.data["tasks"]:
            line = "> добавь квест: введи название ниже"
        elif running and sel:
            line = f"> квест «{name}» выполняется..."
        elif sel:
            line = f"Войти в квест «{name}»? Y/N .."
        else:
            line = "> выбери квест в списке"
        if line != self.typed[0]:
            self.typed = (line, f)
        shown = line[:(f - self.typed[1]) * 2 + 1]
        self.gtext(90, 46, shown, G["bright"], 12)
        if (f // 5) % 2:
            cw = 7.3
            x = 90 + len(shown) * cw + 3
            self.rect(x, 39, x + 8, 54, G["bright"])

    def eye_color(self, b):
        cache = self.__dict__.setdefault("_eye_colors", {})
        k = round(b * 32)
        if k not in cache:
            cache[k] = mix(G["dim"], G["hot"], k / 32)
        return cache[k]

    def draw_eye(self, running, f, glitch):
        x1, y1, x2, y2 = EYE_PANEL
        self.rect(x1, y1, x2, y2, G["bg"])
        if getattr(self, "eye_img", None) is None:
            self.eye_img = tk.PhotoImage(width=x2 - x1, height=y2 - y1)
        img = self.eye_img
        img.blank()

        def put(ax, ay, bx, by, col):
            ax, ay = max(0, round(ax) - x1), max(0, round(ay) - y1)
            bx, by = min(x2 - x1, round(bx) - x1), min(y2 - y1, round(by) - y1)
            if bx > ax and by > ay:
                img.put(col, to=(ax, ay, bx, by))
        for x in range(x1, x2, 6):  # пунктирная рамка, как у плаката
            put(x, y1, x + 3, y1 + 1, G["mid"])
            put(x, y2 - 1, x + 3, y2, G["mid"])
        self.gtext(x1 + 4, y1 + 12, "WATCHING YOUR TIME", G["mid"], 10)
        for k in range(3):
            cx = x2 - 14 - k * 18
            for i, j in ((0, -4), (-4, 0), (4, 0), (0, 4), (0, 0)):
                put(cx + i - 1, y1 + 12 + j - 1, cx + i + 2, y1 + 12 + j + 2, G["mid"])

        # насколько открыт глаз и куда смотрит
        pupil = 15
        if glitch:
            o, ix, iy, pupil = 1.0, EYE_CX + random.uniform(-6, 6), EYE_CY, 6
        elif running:
            k = f % 70
            o = abs(k - 3) / 3 if k < 6 else 1.0
            ix, iy = EYE_CX + math.sin(f * 0.04) * 60, EYE_CY + math.sin(f * 0.07) * 8
        else:
            k = f % 140
            o = 0.38 if 70 <= k < 96 else 0.07  # дремлет, иногда приоткрывает глаз
            ix, iy = EYE_CX + (math.sin(f * 0.2) * 40 if o > 0.1 else 0), EYE_CY

        # полутоновые точки, рамка и веки рисуются в одну картинку: тысяча точек — один элемент холста
        bands = {}
        for x, y, v in EYE_DOTS:
            if abs(v) > o:
                continue
            if glitch:
                band = y // 14
                if band not in bands:
                    bands[band] = random.choice((0, 0, -12, 9, 16))
                x += bands[band]
            b = eye_brightness(x, y, v, ix, iy, pupil)
            s = EYE_STEP * b * 0.95
            if s >= 1:
                ax, ay = round(x - s / 2) - x1, round(y - s / 2) - y1
                bx, by = round(x + s / 2) - x1, round(y + s / 2) - y1
                if bx > ax and by > ay and ax >= 0 and ay >= 0 and bx <= x2 - x1 and by <= y2 - y1:
                    img.put(self.eye_color(b), to=(ax, ay, bx, by))
        for x in range(EYE_CX - EYE_HW, EYE_CX + EYE_HW, 4):  # веки
            hh = eye_halfheight(x - EYE_CX + 2)
            put(x, EYE_CY - o * hh - 2, x + 4, EYE_CY - o * hh + 1, G["bright"])
            put(x, EYE_CY + o * hh, x + 4, EYE_CY + o * hh + 2, G["mid"])
            if o < 0.2 and x % 16 == 0 and abs(x - EYE_CX) < EYE_HW - 30:
                put(x, EYE_CY + 3, x + 2, EYE_CY + 10, G["mid"])  # ресницы спящего глаза
        if not running and not glitch and f % 30 == 0:
            self.particles.append({"kind": "z", "x": EYE_CX + 120, "y": EYE_CY - 20, "vx": 0, "vy": -0.8,
                                   "life": 26})
        if glitch:
            for _ in range(3):
                gy = random.randint(y1 + 20, y2 - 20)
                put(x1, gy, x2, gy + random.randint(3, 9), G["bright"])
            self.gtext(random.randint(x1 + 10, x2 - 140), random.randint(y1 + 30, y2 - 20),
                       random.choice(("ERR0R", "S1GNAL L0ST", "WHO'S THERE?", "0x00FF")), G["hot"], 12, bold=True)
        self.cv.create_image(x1, y1, image=img, anchor="nw", tags=self.layer)
        self.hits.append((EYE_CX - EYE_HW, EYE_CY - EYE_HH, EYE_CX + EYE_HW, EYE_CY + EYE_HH, self.poke_eye))

    # ── режим «Канбан» (общая логика — kanban.py) ─────────────────────────
    KB_AREA = (84, 496, 470, 748)
    KB_TABS = (470, 473, 491, 84)
    KB_SKIN = "term"

    def kb_theme(self):
        return {"cols": {"todo": G["mid"], "doing": G["bright"], "done": G["hot"]}, "col_bg": G["bg"], "tint": 0.86,
                "head_text": G["bg"], "card_bg": G["bg"], "card_line": G["dim"], "text": G["bright"], "dim": G["mid"],
                "run": G["hot"], "mark_off": G["dim"],
                "tab_on_bg": G["bright"], "tab_on_line": G["bright"], "tab_on_text": G["bg"],
                "tab_off_bg": G["bg"], "tab_off_line": G["dim"], "tab_off_text": G["mid"],
                "font": self.font, "tab_labels": ("[список]", "[канбан]")}

    def draw_list(self, running, f):
        tasks = self.data["tasks"]
        if not tasks:
            self.gtext(84, 520, "  пусто. введи название квеста выше_", G["dim"], 12)
        for idx in range(self.scroll, min(len(tasks), self.scroll + self.ROWS)):
            t = tasks[idx]
            y = self.LIST_TOP + (idx - self.scroll) * self.ROW_H
            is_run = running and running["task_id"] == t["id"]
            is_sel = t["id"] == self.data["selected"]
            if is_sel:
                self.rect(84, y, 470, y + 26, G["mid"])
            ink = G["bg"] if is_sel else G["bright"]
            name = t["name"] if len(t["name"]) <= 24 else t["name"][:23] + "…"
            name = done_prefix(self, t) + name
            leader = " " + "." * max(2, 24 - len(name))
            self.cv.create_text(90, y + 13, text=f"{idx + 1:02d}", fill=G["bg"] if is_sel else G["dim"],
                                font=self.font(12), anchor="w", tags=self.layer)
            if is_run and (f // 5) % 2:
                self.cv.create_text(112, y + 13, text="▶", fill=ink, font=self.font(11), anchor="w",
                                    tags=self.layer)
            self.cv.create_text(126, y + 13, text=name + leader, fill=ink, font=self.font(12), anchor="w",
                                tags=self.layer)
            self.cv.create_text(432, y + 13, text=fmt_hms(self.task_total(t["id"])),
                                fill=G["bg"] if is_sel else (G["hot"] if is_run else G["mid"]),
                                font=self.font(12), anchor="e", tags=self.layer)
            self.cv.create_text(454, y + 13, text="[x]", fill=G["bg"] if is_sel else G["dim"],
                                font=self.font(11), tags=self.layer)
            tid = t["id"]
            self.hits.append((84, y, 438, y + 26, lambda tid=tid: self.select(tid)))
            self.hits.append((440, y, 470, y + 26, lambda tid=tid: self.delete_task(tid)))
        if len(tasks) > self.ROWS:
            bar_h = self.ROWS * self.ROW_H - 4
            knob = max(16, bar_h * self.ROWS / len(tasks))
            pos = (bar_h - knob) * self.scroll / (len(tasks) - self.ROWS)
            self.rect(473, self.LIST_TOP, 476, self.LIST_TOP + bar_h, G["glow"])
            self.rect(473, self.LIST_TOP + pos, 476, self.LIST_TOP + pos + knob, G["bright"])

    def draw_particles(self):
        for p in self.particles:
            k = p["kind"]
            if k == "sparkle":
                self.sprite(SPARKLE, p["x"], p["y"], 2 if p["life"] % 4 < 2 else 3, color=G["hot"])
            elif k == "heart":
                self.sprite(HEART, p["x"], p["y"], 3, color=G["bright"])
            elif k == "z":
                self.gtext(p["x"], p["y"], "z" if p["life"] > 16 else "Z", G["mid"], 11 if p["life"] > 16 else 14)
            elif k == "text":
                self.gtext(p["x"], p["y"], p["text"], G["hot"], 16, anchor="center", bold=True)


def main():
    import task_quest  # единое приложение со скинами
    task_quest.main("term")


if __name__ == "__main__":
    main()
