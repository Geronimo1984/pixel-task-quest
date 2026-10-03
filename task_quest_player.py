#!/usr/bin/env python3
"""Скин «Player» для Task Quest.

Фон — точная копия плеера K-Jofol (assets/player.png). Поверх него живые данные:
таймер и квест на LCD, танцующий эквалайзер, дуга громкости = прогресс фокус-сессии,
плейлист = список квестов. В круглых «приводах» вращаются диски Kirby Air Ride,
Bratz Rock Angelz и Resident Evil 4 (assets/disc_*.png, по 24 кадра поворота).

Запуск:  python3 task_quest.py player
"""
import json
import math
import os
import random
import time
import tkinter as tk
import uuid
from tkinter import font as tkfont
from tkinter import simpledialog

import pixel_tracker as pt
import task_quest_2000 as tq
from pixel_tracker import fmt_hms

W, H = 480, 740
TILE = 160
ASSETS = os.path.join(pt.APP_DIR, "assets")
FOCUS_SEC = 25 * 60
DAY_GOAL_SEC = 8 * 3600

DISC_TITLES = {  # имя файла assets/disc_<имя>.png → название для LCD
    "kirby": "Kirby Air Ride", "bratz": "Bratz Rock Angelz", "re4": "Resident Evil 4",
    "gow": "God of War", "sonic98": "Sonic · Hardcore 98", "nirvana": "Nirvana · Nevermind",
    "evilwithin": "The Evil Within", "dmc3": "Devil May Cry 3", "dmc": "Devil May Cry",
    "sh2": "Silent Hill 2", "matrix": "Matrix: Path of Neo", "re4ps3": "Resident Evil 4 PS3",
    "manhunt": "Manhunt", "mk": "MK: Deception", "sonicadv": "Sonic Adventure",
    "outlast": "Outlast Trinity", "sims2": "The Sims 2", "sh3": "Silent Hill 3",
}
DISCS = list(DISC_TITLES)
DISC_FRAMES, DISC_BIG, DISC_SMALL = 24, 168, 112  # блоки с дисками в 2 раза больше родных приводов
DRIVE_TOP = (350, 238)     # верхний привод — текущий диск
DRIVE_BOTTOM = (62, 675)   # нижний привод — следующий диск

# стиль Xbox-плеера: тёмный глянцевый металл и светящиеся лаймовые экраны (assets/player_xbox.png)
LCD_INK = "#031000"        # почти чёрный зелёный — максимальный контраст на лаймовом экране
LCD_SOFT = "#0b2c00"
LIST_INK = "#041200"       # текст плейлиста
LIST_SEL_INK = "#dcff9e"   # выделенная строка — светлый лайм на тёмно-зелёной полосе
LIST_SEL_BG = "#123d00"
LIST_RUN_INK = "#003d00"
EQ_BAR = "#0d3a00"
ARC_DIM = "#0f2a05"        # погасшие деления дуги громкости
GREEN = "#a6ff3c"
GREEN_DIM = "#5bb81e"
BEZEL = ("#1c201e", "#4a514c", "#9aa39d", "#f2f6f3", "#8b938e", "#3a3f3c", "#0e100f")

# места для текста (старый текст стёрт с фона заранее — assets/player_clean.png)
LCD_TIME = (150, 66, 262, 88)
LCD_LINE2 = (138, 90, 272, 105)
LCD_LINE3 = (128, 110, 280, 124)
LCD_LINE4 = (130, 125, 278, 139)
EQ_BARS = (148, 158, 251, 209)
LIST_AREA = (38, 349, 362, 577)
LIST_TOP, LIST_ROW = 349, 19
INFO_AREA = (40, 582, 398, 623)

# зелёные текстовые кнопки справа от плейлиста и кнопки плеера (центр, полуширина, полувысота)
SIDE_BTNS = [("add", 399, "добавить"), ("del", 418, "удалить"), ("select", 437, "дальше"),
             ("csv", 456, "в CSV"), ("clear", 475, "очистить"), ("fx", 494, "эффекты"),
             ("top", 515, "поверх"), ("skin", 535, "скины")]
HINTS = {
    "play": "▶ старт", "b_play": "▶ старт", "pause": "❚❚ пауза", "b_pause": "❚❚ пауза",
    "stop": "■ стоп", "b_stop": "■ стоп", "eject": "⏏ экспорт в CSV", "b_eject": "⏏ экспорт в CSV",
    "prev": "⏮ предыдущий квест", "b_prev": "⏮ предыдущий квест", "next": "⏭ следующий квест",
    "b_next": "⏭ следующий квест", "green": "эквалайзер вкл/выкл", "dock": "поверх окон", "disc": "сменить диск",
    "close": "✕ закрыть", "close2": "✕ закрыть",
}
ROUND_BTNS = {
    "play": ((62, 62), 17), "pause": ((28, 48), 13), "eject": ((62, 22), 13), "stop": ((96, 48), 13),
    "prev": ((38, 90), 13), "next": ((86, 90), 13),
    "b_prev": ((283, 693), 18), "b_play": ((325, 693), 18), "b_next": ((375, 693), 18),
    "b_eject": ((443, 592), 17), "b_stop": ((443, 632), 17), "b_pause": ((422, 670), 17),
    "green": ((343, 135), 22), "dock": ((350, 47), 12),
    "close": ((432, 170), 9), "close2": ((392, 332), 9),
}


class AppPlayer(tq.App2):
    ROWS = 12
    ROW_H = LIST_ROW
    LIST_TOP = LIST_TOP

    def __init__(self, root):  # noqa: своя сцена, как у остальных скинов
        self.root = root
        root.title("Task Quest · Player")
        root.resizable(False, False)
        root.configure(bg="#000000")
        families = set(tkfont.families())
        fam = next((f for f in ("Menlo", "Monaco", "Courier") if f in families), "TkFixedFont")
        rounded = next((f for f in ("Arial Rounded MT Bold", "Verdana", "Arial") if f in families), fam)
        self.font = lambda size, bold=True: (fam, size, "bold" if bold else "normal")
        self.lcd_font = lambda size: (rounded, size)

        # окно принимает форму плеера: без рамки и заголовка, всё вокруг плеера прозрачное
        root.withdraw()
        root.overrideredirect(True)
        root.wm_attributes("-transparent", True)
        root.configure(bg="systemTransparent")
        root.deiconify()
        self.cv = tk.Canvas(root, width=W, height=H, bg="systemTransparent", highlightthickness=0)
        self.cv.pack()
        self.drag = None
        self.cv.focus_set()  # чтобы пробел сразу работал
        self.on_switch = None
        self.entry = None  # задачи добавляются через «add track»

        self.f = 0
        self.layer = "dyn"
        self.particles = []
        self.pressed = {}
        self.hits = []
        self.scroll = 0
        self.toast = None
        self.topmost = False
        self.idle_since = time.time()
        self.disc_frame = 0
        self.scratch_until = -1
        self.eq = [0.2] * 14

        self.bg = tk.PhotoImage(file=os.path.join(ASSETS, "player_xbox.png"))
        # фон режем на плитки 160×160 (размер как у дисков)
        self.bg_tiles = []
        for ty in range(0, H, TILE):
            for tx in range(0, W, TILE):
                w, h = min(TILE, W - tx), min(TILE, H - ty)
                if all(self.bg.transparency_get(tx + i, ty + j) for j in range(0, h, 4) for i in range(0, w, 4)):
                    continue  # плитка целиком из прозрачного фона — не нужна
                tile = tk.PhotoImage(width=w, height=h)
                tile.tk.call(tile, "copy", self.bg, "-from", tx, ty, tx + w, ty + h)
                self.bg_tiles.append((tx, ty, tile))
        self.hint = None
        bold = next((f for f in ("Verdana", "Tahoma", "Arial") if f in families), fam)
        self.bold = lambda size: (bold, size, "bold")
        self.bold_family = bold
        self.fit_cache = {}
        # один общий размер для всех подписей капсулы — самый крупный, при котором влезает каждая
        size = 12
        while size > 8 and any(tkfont.Font(family=bold, size=size, weight="bold").measure(label) > 66
                               for _, _, label in SIDE_BTNS):
            size -= 1
        self.side_size = size
        self.discs = {}  # диски грузятся по требованию — нужны только текущий и следующий
        with open(os.path.join(ASSETS, "player_arc.json"), encoding="utf-8") as fh:
            self.arc = json.load(fh)
        # силуэт плеера фигурами: на прозрачном окне macOS картинка видна только поверх
        # непрозрачной подложки (как диски поверх тёмных кругов приводов)
        with open(os.path.join(ASSETS, "player_silhouette.json"), encoding="utf-8") as fh:
            for x1, y1, x2, y2 in json.load(fh):
                self.cv.create_rectangle(x1, y1, x2, y2, fill="#000000", outline="", tags="static")

        self.load()
        self.data.setdefault("fx", True)
        self.data["disc"] = self.data.get("disc", 0) % len(DISCS)
        self.last_lv = self.level()[0]


        self.cv.bind("<Button-1>", self.on_click)
        self.cv.bind("<B1-Motion>", self.on_drag)
        self.cv.bind("<ButtonRelease-1>", lambda e: setattr(self, "drag", None))
        self.cv.bind("<Motion>", self.on_motion)
        self.cv.bind("<Leave>", lambda e: setattr(self, "hint", None))
        self.cv.bind("<MouseWheel>", self.on_wheel)
        self.cv.bind("<Button-4>", lambda e: self.scroll_by(-1))
        self.cv.bind("<Button-5>", lambda e: self.scroll_by(1))
        root.bind("<space>", self.on_space)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        if not self.data["tasks"]:
            self.show_toast("«добавить» — новый квест", 80)
        elif self.data["running"]:
            self.show_toast("с возвращением ♥", 50)
        self.tick()

    def teardown(self):
        if getattr(self, "_after", None):
            self.root.after_cancel(self._after)
        self.cv.destroy()
        # возвращаем обычное окно для других скинов
        root = self.root
        root.withdraw()
        root.wm_attributes("-transparent", False)
        root.overrideredirect(False)
        root.deiconify()

    def on_click(self, e):
        """Клик по кнопке — действие, по корпусу плеера — начать перетаскивание окна."""
        self.root.focus_force()
        self.cv.focus_set()
        for x1, y1, x2, y2, cb in reversed(self.hits):
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                cb()
                return
        self.drag = (e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y())

    def on_drag(self, e):
        if self.drag:
            self.root.geometry(f"+{e.x_root - self.drag[0]}+{e.y_root - self.drag[1]}")

    def on_motion(self, e):
        """Подсказка на LCD: что делает кнопка под мышкой."""
        self.hint = None
        for name, ((cx, cy), r) in ROUND_BTNS.items():
            if abs(e.x - cx) <= r and abs(e.y - cy) <= r:
                self.hint = HINTS.get(name)
        dx, dy = DRIVE_TOP
        if math.hypot(e.x - dx, e.y - dy) <= DISC_BIG / 2:
            self.hint = HINTS["disc"]

    # ── действия ──────────────────────────────────────────────────────────
    def add_task(self, _event=None):
        self.press("add")
        name = simpledialog.askstring("add track", "Название нового квеста:", parent=self.root)
        if not name or not name.strip():
            return
        t = {"id": uuid.uuid4().hex[:8], "name": name.strip(), "created": time.time()}
        self.data["tasks"].insert(0, t)
        if not self.data["running"]:
            self.data["selected"] = t["id"]
        self.scroll = 0
        self.save()
        self.show_toast("квест добавлен", 25)

    def delete_selected(self):
        self.press("del")
        if self.data["selected"]:
            self.delete_task(self.data["selected"])

    def select_step(self, d):
        tasks = self.data["tasks"]
        if not tasks:
            return
        ids = [t["id"] for t in tasks]
        cur = ids.index(self.data["selected"]) if self.data["selected"] in ids else -1
        nxt = ids[(cur + d) % len(ids)]
        self.select(nxt)
        idx = ids.index(nxt)
        if idx < self.scroll or idx >= self.scroll + self.ROWS:
            self.scroll = max(0, min(idx, len(ids) - self.ROWS))

    def start(self):
        super().start()
        if self.data["running"]:
            self.data["disc"] = (self.data["disc"] + 1) % len(DISCS)  # на старте — следующий диск
            self.show_toast("диск: " + DISC_TITLES[DISCS[self.data["disc"]]], 25)
            self.save()

    def scratch(self):
        """Клик по диску — «скретч» назад и смена диска."""
        self.scratch_until = self.f + 12
        self.data["disc"] = (self.data["disc"] + 1) % len(DISCS)
        self.save()
        self.show_toast("диск: " + DISC_TITLES[DISCS[self.data["disc"]]], 25)

    def toggle_fx(self):
        self.press("fx")
        self.data["fx"] = not self.data["fx"]
        self.save()
        self.show_toast("эквалайзер: " + ("вкл" if self.data["fx"] else "выкл"), 20)

    def action(self, name):
        acts = {
            "play": self.start_if_stopped, "b_play": self.start_if_stopped,
            "pause": self.stop, "stop": self.stop, "b_pause": self.stop, "b_stop": self.stop,
            "prev": lambda: self.select_step(-1), "b_prev": lambda: self.select_step(-1),
            "next": lambda: self.select_step(1), "b_next": lambda: self.select_step(1),
            "eject": self.export_csv, "b_eject": self.export_csv, "green": self.toggle_fx,
            "dock": self.toggle_top,
            "add": self.add_task, "del": self.delete_selected, "select": lambda: self.select_step(1),
            "csv": self.export_csv, "clear": self.clear_tasks, "fx": self.toggle_fx, "top": self.toggle_top,
            "skin": self.switch_skin, "close": self.on_close, "close2": self.on_close,
        }
        return lambda: (self.press(name), acts[name]())

    def start_if_stopped(self):
        if not self.data["running"]:
            self.start()

    # ── отрисовка ─────────────────────────────────────────────────────────
    def fit(self, text, size, width, rounded=False):
        """Самый крупный шрифт (не больше size), которым text влезает в width."""
        key = (text, size, width, rounded)
        if key not in self.fit_cache:
            fam = self.lcd_font(size)[0] if rounded else self.bold_family
            while size > 8 and tkfont.Font(family=fam, size=size, weight="normal" if rounded else "bold"
                                           ).measure(text) > width:
                size -= 1
            self.fit_cache[key] = (fam, size) if rounded else (fam, size, "bold")
            if len(self.fit_cache) > 400:
                self.fit_cache.clear()
        return self.fit_cache[key]

    def lcd(self, rect, text, size, color=LCD_INK, rounded=False):
        x1, y1, x2, y2 = rect
        font = self.fit(text, size, x2 - x1 - 6, rounded)
        self.cv.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, fill=color, font=font, tags=self.layer)

    def redraw(self):
        self.cv.delete("dyn")
        self.hits = []
        # фон плеера поверх силуэта — маленькими плитками каждый кадр, как диски
        for tx, ty, tile in self.bg_tiles:
            self.cv.create_image(tx, ty, image=tile, anchor="nw", tags=self.layer)
        running = self.data["running"]
        f = self.f
        sel = self.task(self.data["selected"])
        today = self.today_total()
        lv, xp = self.level()
        if lv > self.last_lv and running:
            self.show_toast(f"LEVEL UP ★ LV {lv}", 40)
        self.last_lv = lv

        # LCD: время, статус, квест (или сообщение), время за день
        shown = self.session_elapsed() if running else (self.task_total(sel["id"]) if sel else 0)
        self.lcd(LCD_TIME, fmt_hms(shown), 19, rounded=True)
        status = ("▶ идёт работа" if (f // 8) % 2 else "▶") if running else ("❚❚ пауза" if sel else "нет квеста")
        self.lcd(LCD_LINE2, status, 11, LCD_SOFT)
        if self.hint:
            line3 = self.hint
        elif self.toast and self.toast[1] >= f:
            line3 = self.toast[0]
        else:
            line3 = sel["name"] if sel else "добавь квест →"
        if len(line3) > 24:
            line3 = line3[:23] + "…"
        self.lcd(LCD_LINE3, line3, 12)
        self.lcd(LCD_LINE4, f"LV {lv:02d} · день {fmt_hms(today)}", 10, LCD_SOFT)

        self.draw_eq(running, f)
        self.draw_arc(running, today)
        self.draw_discs(running, f)
        self.draw_playlist(running, f)

        x1, y1, x2, y2 = INFO_AREA
        info = [f"сессия {fmt_hms(self.session_elapsed())} · день {fmt_hms(today)}",
                f"уровень {lv:02d} · ещё {25 - int(xp * 25)} мин · квестов {len(self.data['tasks'])}",
                "сейчас: " + ((sel["name"] if running and sel else "пауза")[:28])]
        for k, line in enumerate(info):
            x = 44 if k < 2 else 132   # третья строка начинается правее большого нижнего диска
            self.cv.create_text(x, y1 + 7 + k * 13.5, text=line, fill=LCD_INK, font=self.bold(10), anchor="w",
                                tags=self.layer)

        states = {"fx": self.data["fx"], "top": self.topmost}
        for name, y, label in SIDE_BTNS:
            on = states.get(name, True)
            down = self.pressed.get(name, -1) >= f
            self.cv.create_text(433, y, text=label, fill="#ffffff" if down else (GREEN if on else GREEN_DIM),
                                font=self.bold(self.side_size), tags=self.layer)
            self.hits.append((398, y - 9, 468, y + 9, self.action(name)))
        for name, ((cx, cy), r) in ROUND_BTNS.items():
            if self.pressed.get(name, -1) >= f:
                self.cv.create_oval(cx - r, cy - r, cx + r, cy + r, outline=GREEN, width=2, tags=self.layer)
            self.hits.append((cx - r, cy - r, cx + r, cy + r, self.action(name)))
        self.draw_particles()

    def draw_eq(self, running, f):
        x1, y1, x2, y2 = EQ_BARS
        live = running and self.data["fx"]
        for i in range(len(self.eq)):
            target = (0.35 + 0.6 * random.random() * (0.6 + 0.4 * math.sin(f * 0.3 + i))) if live else 0.08
            self.eq[i] += (target - self.eq[i]) * 0.45
            bx = x1 + 3 + i * 7
            top = y2 - 2 - (y2 - y1 - 4) * self.eq[i]
            for yy in range(int(y2) - 2, int(top), -3):   # полоски из сегментов, как на картинке
                self.rect(bx, yy - 2, bx + 5, yy, EQ_BAR)

    def draw_arc(self, running, today):
        progress = (self.session_elapsed() % FOCUS_SEC) / FOCUS_SEC if running else min(1, today / DAY_GOAL_SEC)
        lit = int(progress * len(self.arc))
        for b in self.arc[lit:]:   # гасим деления дальше текущего прогресса
            for x1, y, x2 in b:
                self.rect(x1, y, x2, y + 1, ARC_DIM)

    def draw_discs(self, running, f):
        cur = DISCS[self.data["disc"]]
        nxt = DISCS[(self.data["disc"] + 1) % len(DISCS)]
        if f < self.scratch_until:
            self.disc_frame = (self.disc_frame - 3) % DISC_FRAMES   # скретч назад
        elif running:
            self.disc_frame = (self.disc_frame + 1) % DISC_FRAMES
        frames, _ = self.disc(cur)
        cx, cy = DRIVE_TOP
        self.drive_bezel(cx, cy, DISC_BIG // 2)
        self.cv.create_image(cx, cy, image=frames[self.disc_frame], tags=self.layer)
        r = DISC_BIG // 2
        self.hits.append((cx - r, cy - r, cx + r, cy + r, self.scratch))
        _, small = self.disc(nxt)
        self.drive_bezel(*DRIVE_BOTTOM, DISC_SMALL // 2)
        self.cv.create_image(*DRIVE_BOTTOM, image=small, tags=self.layer)

    def disc(self, name):
        """Кадры вращения и маленькая картинка диска (загружаются при первом обращении)."""
        if name not in self.discs:
            strip = tk.PhotoImage(file=os.path.join(ASSETS, f"disc_{name}.png"))
            frames = []
            for k in range(DISC_FRAMES):
                fr = tk.PhotoImage(width=DISC_BIG, height=DISC_BIG)
                fr.tk.call(fr, "copy", strip, "-from", k * DISC_BIG, 0, (k + 1) * DISC_BIG, DISC_BIG)
                frames.append(fr)
            self.discs[name] = (frames, tk.PhotoImage(file=os.path.join(ASSETS, f"disc_{name}_small.png")))
        return self.discs[name]

    def drive_bezel(self, cx, cy, r):
        """Хромированный ободок привода вокруг диска — в стиле корпуса плеера."""
        self.cv.create_oval(cx - r - 9, cy - r - 9, cx + r + 9, cy + r + 9, fill="#0b0c0b", outline="",
                            tags=self.layer)
        for k, col in enumerate(BEZEL):
            rr = r + 8 - k
            self.cv.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=col, width=1.4, tags=self.layer)
        self.cv.create_oval(cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1, fill="#050605", outline="",
                            tags=self.layer)

    def draw_playlist(self, running, f):
        x1, y1, x2, y2 = LIST_AREA
        tasks = self.data["tasks"]
        if not tasks:
            self.cv.create_text(45, LIST_TOP + 10, text="пусто — нажми «добавить»", fill=LIST_INK,
                                font=self.bold(12), anchor="w", tags=self.layer)
        for idx in range(self.scroll, min(len(tasks), self.scroll + self.ROWS)):
            t = tasks[idx]
            ry = LIST_TOP + (idx - self.scroll) * LIST_ROW
            is_sel = t["id"] == self.data["selected"]
            is_run = running and running["task_id"] == t["id"]
            if is_sel:
                self.rect(x1 + 2, ry + 1, x2 - 8, ry + LIST_ROW - 1, LIST_SEL_BG)
            ink = LIST_SEL_INK if is_sel else (LIST_RUN_INK if is_run else LIST_INK)
            name = t["name"] if len(t["name"]) <= 24 else t["name"][:23] + "…"
            prefix = ("▶ " if (f // 6) % 2 else "▷ ") if is_run else ""
            self.cv.create_text(45, ry + LIST_ROW / 2, text=f"{idx + 1}. {prefix}{name}", fill=ink,
                                font=self.bold(12), anchor="w", tags=self.layer)
            total = self.task_total(t["id"])
            self.cv.create_text(352, ry + LIST_ROW / 2, text=fmt_hms(total)[1:] if total < 36000 else fmt_hms(total),
                                fill=ink, font=self.bold(12), anchor="e", tags=self.layer)
            tid = t["id"]
            self.hits.append((x1, ry, x2 - 8, ry + LIST_ROW, lambda tid=tid: self.select(tid)))

    def draw_particles(self):
        for p in self.particles:
            if p["kind"] == "text":
                self.cv.create_text(p["x"], p["y"], text=p["text"], fill=GREEN, font=self.lcd_font(13),
                                    tags=self.layer)
            elif p["kind"] in ("sparkle", "heart"):
                self.rect(p["x"] - 1, p["y"] - 1, p["x"] + 2, p["y"] + 2, GREEN)


def main():
    import task_quest  # единое приложение со скинами
    task_quest.main("player")


if __name__ == "__main__":
    main()
