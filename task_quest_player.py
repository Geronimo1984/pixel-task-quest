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
ASSETS = os.path.join(pt.APP_DIR, "assets")
FOCUS_SEC = 25 * 60
DAY_GOAL_SEC = 8 * 3600

DISCS = ["kirby", "bratz", "re4"]
DISC_FRAMES, DISC_BIG, DISC_SMALL = 24, 84, 56
DRIVE_TOP = (350, 238)     # верхний привод — текущий диск
DRIVE_BOTTOM = (62, 675)   # нижний привод — следующий диск

LCD_INK = "#2c352c"        # тёмный текст на LCD
LIST_INK = "#5d6a5a"       # текст плейлиста
LIST_SEL_INK = "#8a9286"   # выделенная строка (как пятая строка на картинке)
LIST_SEL_BG = "#a4a99d"
EQ_BAR = "#3e4f42"
ARC_DIM = "#1d3320"        # погасшие деления дуги громкости
GREEN = "#38f04a"

# где на картинке стоит старый текст — его закрашиваем цветом LCD и пишем своё
LCD_TIME = (150, 66, 262, 88)
LCD_LINE2 = (138, 90, 272, 105)
LCD_LINE3 = (128, 110, 280, 124)
LCD_LINE4 = (130, 125, 278, 139)
EQ_BARS = (148, 158, 251, 209)
LIST_AREA = (38, 349, 362, 577)
LIST_TOP, LIST_ROW = 349, 19
INFO_AREA = (40, 582, 398, 623)

# зелёные текстовые кнопки справа от плейлиста и кнопки плеера (центр, полуширина, полувысота)
SIDE_BTNS = [("add", 399), ("del", 418), ("select", 437), ("csv", 456), ("clear", 475), ("fx", 494),
             ("top", 515), ("skin", 535)]
ROUND_BTNS = {
    "play": ((62, 62), 17), "pause": ((28, 48), 13), "eject": ((62, 22), 13), "stop": ((96, 48), 13),
    "prev": ((38, 90), 13), "next": ((86, 90), 13),
    "b_prev": ((283, 693), 18), "b_play": ((325, 693), 18), "b_next": ((375, 693), 18),
    "b_eject": ((443, 592), 17), "b_stop": ((443, 632), 17), "b_pause": ((422, 670), 17),
    "green": ((343, 135), 22), "dock": ((350, 47), 12),
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
        arial = next((f for f in ("Arial", "Helvetica", "Verdana") if f in families), fam)
        self.font = lambda size, bold=True: (fam, size, "bold" if bold else "normal")
        self.lcd_font = lambda size: (rounded, size)
        self.list_font = lambda size: (arial, size)

        self.cv = tk.Canvas(root, width=W, height=H, bg="#000000", highlightthickness=0)
        self.cv.pack()
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

        self.bg = tk.PhotoImage(file=os.path.join(ASSETS, "player.png"))
        self.discs = {}
        for name in DISCS:
            strip = tk.PhotoImage(file=os.path.join(ASSETS, f"disc_{name}.png"))
            frames = []
            for k in range(DISC_FRAMES):
                fr = tk.PhotoImage(width=DISC_BIG, height=DISC_BIG)
                fr.tk.call(fr, "copy", strip, "-from", k * DISC_BIG, 0, (k + 1) * DISC_BIG, DISC_BIG)
                frames.append(fr)
            small = tk.PhotoImage(file=os.path.join(ASSETS, f"disc_{name}_small.png"))
            self.discs[name] = (frames, small)
        with open(os.path.join(ASSETS, "player_arc.json"), encoding="utf-8") as fh:
            self.arc = json.load(fh)

        self.load()
        self.data.setdefault("fx", True)
        self.data.setdefault("disc", 0)
        self.last_lv = self.level()[0]

        self.layer = "static"
        self.cv.create_image(0, 0, image=self.bg, anchor="nw", tags="static")
        self.layer = "dyn"
        # цвета LCD, снятые с картинки посередине экранов (по углам — тёмный ободок)
        self.blank = {"time": "#91a28f", "l2": "#92a390", "l3": "#96a995", "l4": "#96a995", "eq": "#8fa08c",
                      "info": "#96a794"}
        self.row_bg = [self.sample((40, LIST_TOP + i * LIST_ROW + 2, 44, LIST_TOP + i * LIST_ROW + 17))
                       for i in range(self.ROWS)]

        self.cv.bind("<Button-1>", self.on_click)
        self.cv.bind("<MouseWheel>", self.on_wheel)
        self.cv.bind("<Button-4>", lambda e: self.scroll_by(-1))
        self.cv.bind("<Button-5>", lambda e: self.scroll_by(1))
        root.bind("<space>", self.on_space)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        if not self.data["tasks"]:
            self.show_toast("add track — новый квест", 80)
        elif self.data["running"]:
            self.show_toast("с возвращением ♥", 50)
        self.tick()

    def teardown(self):
        if getattr(self, "_after", None):
            self.root.after_cancel(self._after)
        self.cv.destroy()

    def sample(self, rect):
        x1, y1, x2, y2 = rect
        pts = [(x1, y1), (x2 - 1, y1), (x1, y2 - 1), (x2 - 1, y2 - 1)]
        cols = [self.bg.get(x, y) for x, y in pts]
        return "#%02x%02x%02x" % tuple(sum(c[k] for c in cols) // 4 for k in range(3))

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
            self.save()

    def scratch(self):
        """Клик по диску — «скретч» назад и смена диска."""
        self.scratch_until = self.f + 12
        self.data["disc"] = (self.data["disc"] + 1) % len(DISCS)
        self.save()
        self.show_toast("диск: " + ("Kirby Air Ride", "Bratz Rock Angelz", "Resident Evil 4")[self.data["disc"]], 25)

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
            "skin": self.switch_skin,
        }
        return lambda: (self.press(name), acts[name]())

    def start_if_stopped(self):
        if not self.data["running"]:
            self.start()

    # ── отрисовка ─────────────────────────────────────────────────────────
    def lcd(self, key, rect, text, size, anchor="center", color=LCD_INK):
        x1, y1, x2, y2 = rect
        self.rect(x1, y1, x2, y2, self.blank[key])
        x = {"center": (x1 + x2) / 2, "w": x1 + 2, "e": x2 - 2}[anchor]
        self.cv.create_text(x, (y1 + y2) / 2, text=text, fill=color, font=self.lcd_font(size), anchor=anchor,
                            tags=self.layer)

    def redraw(self):
        self.cv.delete("dyn")
        self.hits = []
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
        self.lcd("time", LCD_TIME, fmt_hms(shown), 15)
        self.lcd("l2", LCD_LINE2, ("▶ play" if (f // 8) % 2 else "▶") if running else "■ pause"
                 if sel else "- - -", 9)
        if self.toast and self.toast[1] >= f:
            line3 = self.toast[0]
        else:
            line3 = sel["name"] if sel else "no track"
        if len(line3) > 26:
            line3 = line3[:25] + "…"
        self.lcd("l3", LCD_LINE3, line3, 10)
        self.lcd("l4", LCD_LINE4, f"lv {lv:02d}  ·  {fmt_hms(today)} today", 8)

        self.draw_eq(running, f)
        self.draw_arc(running, today)
        self.draw_discs(running, f)
        self.draw_playlist(running, f)

        x1, y1, x2, y2 = INFO_AREA
        self.rect(x1, y1, x2, y2, self.blank["info"])
        info = [f"time/total : {fmt_hms(self.session_elapsed())}/{fmt_hms(today)}+",
                f"track info : lv {lv:02d} · {int(xp * 25):02d}/25 min · квестов {len(self.data['tasks'])}",
                "nowplaying: " + ((sel["name"] if running and sel else "—")[:34])]
        for k, line in enumerate(info):
            self.cv.create_text(45, y1 + 7 + k * 13.5, text=line, fill=LCD_INK, font=self.lcd_font(8), anchor="w",
                                tags=self.layer)

        for name, y in SIDE_BTNS:
            if self.pressed.get(name, -1) >= f:
                self.rect(398, y - 8, 468, y + 8, "", GREEN, 1)
            self.hits.append((398, y - 9, 468, y + 9, self.action(name)))
        for name, ((cx, cy), r) in ROUND_BTNS.items():
            if self.pressed.get(name, -1) >= f:
                self.cv.create_oval(cx - r, cy - r, cx + r, cy + r, outline=GREEN, width=2, tags=self.layer)
            self.hits.append((cx - r, cy - r, cx + r, cy + r, self.action(name)))
        self.draw_particles()

    def draw_eq(self, running, f):
        x1, y1, x2, y2 = EQ_BARS
        self.rect(x1, y1, x2, y2, self.blank["eq"])
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
        frames, _ = self.discs[cur]
        cx, cy = DRIVE_TOP
        self.cv.create_image(cx, cy, image=frames[self.disc_frame], tags=self.layer)
        self.hits.append((cx - 42, cy - 42, cx + 42, cy + 42, self.scratch))
        _, small = self.discs[nxt]
        self.cv.create_image(*DRIVE_BOTTOM, image=small, tags=self.layer)

    def draw_playlist(self, running, f):
        x1, y1, x2, y2 = LIST_AREA
        tasks = self.data["tasks"]
        for i in range(self.ROWS):
            ry = LIST_TOP + i * LIST_ROW
            self.rect(x1, ry, x2, ry + LIST_ROW, self.row_bg[i])
        if not tasks:
            self.cv.create_text(45, LIST_TOP + 10, text="плейлист пуст — нажми add track", fill=LIST_INK,
                                font=self.list_font(12), anchor="w", tags=self.layer)
        for idx in range(self.scroll, min(len(tasks), self.scroll + self.ROWS)):
            t = tasks[idx]
            ry = LIST_TOP + (idx - self.scroll) * LIST_ROW
            is_sel = t["id"] == self.data["selected"]
            is_run = running and running["task_id"] == t["id"]
            if is_sel:
                self.rect(x1 + 2, ry + 1, x2 - 8, ry + LIST_ROW - 1, LIST_SEL_BG)
            ink = LIST_SEL_INK if is_sel else LIST_INK
            name = t["name"] if len(t["name"]) <= 30 else t["name"][:29] + "…"
            prefix = ("▶ " if (f // 6) % 2 else "▷ ") if is_run else ""
            self.cv.create_text(45, ry + LIST_ROW / 2, text=f"{idx + 1}. {prefix}{name}", fill=ink,
                                font=self.list_font(12), anchor="w", tags=self.layer)
            total = self.task_total(t["id"])
            self.cv.create_text(352, ry + LIST_ROW / 2, text=fmt_hms(total)[1:] if total < 36000 else fmt_hms(total),
                                fill=ink, font=self.list_font(12), anchor="e", tags=self.layer)
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
