#!/usr/bin/env python3
"""Pixel Task Quest — ретро-пиксельный трекер времени выполнения задач.

Запуск:  python3 pixel_tracker.py
Данные:  tracker_data.json рядом со скриптом (сессии сохраняются сразу).

Управление:
  ПРОБЕЛ      — старт / стоп
  ENTER       — добавить задачу (в поле ввода)
  клик        — выбрать задачу (если таймер идёт — переключиться на неё)
  ✕           — удалить задачу
  колесо мыши — прокрутка списка
"""
import csv
import json
import math
import os
import random
import time
import tkinter as tk
import uuid
from datetime import date, datetime
from tkinter import font as tkfont
from tkinter import messagebox

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.environ.get("PIXEL_TRACKER_DATA", os.path.join(APP_DIR, "tracker_data.json"))

W, H = 480, 740
FPS_MS = 80

C = {
    "bg": "#1b1440", "sky": "#241a55", "panel": "#2e2366", "sel": "#4b3a9e",
    "ink": "#120c2b", "text": "#f4ecff", "dim": "#9d8fd6",
    "yellow": "#ffd84a", "pink": "#ff7eb6", "mint": "#6ff7c8", "red": "#ff5c7a",
    "grass": "#3fbf7f", "grass2": "#2e9a63", "dirt": "#6b3f6e", "dirt2": "#5a3360",
}

PALETTE = {
    "K": "#120c2b", "B": "#f4f0ff", "S": "#c9bff0", "P": "#ff9fcf", "R": "#ff6fa8",
    "Y": "#ffd84a", "W": "#ffffff", "p": "#ffb3d9", "O": "#ffb02e", "#": None,
    "G": "#3fbf7f", "g": "#2e9a63", "N": "#8a5a3c", "C": "#6fd8ff", "c": "#3a9ad9",
    "D": "#6b5fa8", "L": "#c9bff0", "V": "#8f7ae6",
}
LEVEL_SEC = 25 * 60  # один уровень = 25 минут работы за день

# «цифровой дождь» на фоне
RAIN_CHARS = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789★♥"
RAIN_STEP = 16      # высота «клетки» символа
RAIN_GAP = 20       # расстояние между колонками
RAIN_TRAIL = 14     # максимальная длина хвоста

# ── Спрайты (оригинальные персонажи) ─────────────────────────────────────────
# Мяу-Луна: белая кошечка с жёлтым полумесяцем на лбу
CAT_AWAKE = [
    "................",
    "..K.........K...",
    ".KPK.......KPK..",
    ".KPBK.....KBPK..",
    ".KBBBKKKKKBBBK..",
    ".KBBBBBYBBBBBK..",
    "KBBBBBYYBBBBBBK.",
    "KBBWKBBBBBWKBBK.",
    "KBBKKBBBBBKKBBK.",
    "KBRRBBBPBBBRRBK.",
    ".KBBBBKBKBBBBK..",
    "..KKBBBBBBBKK...",
    "...KBBBBBBBK.KK.",
    "...KBBSBBBBKKBK.",
    "...KBBKBKBBBBBK.",
    "....KK.K.KKKKK..",
]
CAT_SLEEP = CAT_AWAKE[:7] + [
    "KBBBBBBBBBBBBBK.",
    "KBKKKBBBBBKKKBK.",
] + CAT_AWAKE[9:]

# Моти: розовый прыгучий шарик
MOTI = [
    ".....KKKK.....",
    "...KKppppKK...",
    "..KppppppppK..",
    ".KppWppppWppK.",
    ".KppKppppKppK.",
    "KpRRppKKppRRpK",
    "KppppppppppppK",
    "KppppppppppppK",
    ".KppppppppppK.",
    "..KKppppppKK..",
    "....KKKKKK....",
]

# Звёздочка-фея
STAR = [
    "....K....",
    "...KYK...",
    "...KYK...",
    "KKKYYYKKK",
    "KYYKYKYYK",
    ".KYYYYYK.",
    "..KYYYK..",
    ".KYYKYYK.",
    ".KK...KK.",
]

HEART = [
    ".KK.KK.",
    "KRRKRRK",
    "KRRRRRK",
    ".KRRRK.",
    "..KRK..",
    "...K...",
]

SPARKLE = [
    "..W..",
    "..Y..",
    "WYWYW",
    "..Y..",
    "..W..",
]

# ── Ретро-декор сцены ────────────────────────────────────────────────────────
CLOUD = [
    "....KKKK........",
    "..KKWWWWKK.KKK..",
    ".KWWWWWWWWKWWWK.",
    "KWWWWWWWWWWWWWWK",
    "KSSWWWWWWWWWSSSK",
    ".KKKKKKKKKKKKKK.",
]

UFO = [
    ".....KKKK.....",
    "....KCCCCK....",
    "...KCWCCCCK...",
    ".KKKKKKKKKKKK.",
    "KDLDLDLDLDLDLK",
    ".KKKKKKKKKKKK.",
    "...KK....KK...",
]
UFO_BLINK = [row.replace("L", "Y") for row in UFO]

# блок-сюрприз со звездой
BLOCK = [
    "KKKKKKKKKKKK",
    "KWYYYYYYYYYK",
    "KYKYYYYYYKOK",
    "KYYYYKYYYYOK",
    "KYYYKWKYYYOK",
    "KYKKWWWKKYOK",
    "KYYKWWWKYYOK",
    "KYYKWKWKYYOK",
    "KYYYKYKYYYOK",
    "KYKYYYYYYKOK",
    "KYOOOOOOOOOK",
    "KKKKKKKKKKKK",
]

COIN_FRAMES = [
    [".KKKK.", "KYYYOK", "KYWYOK", "KYWYOK", "KYWYOK", "KYWYOK", "KYYYOK", ".KKKK."],
    [".KK.", "KYOK", "KWOK", "KWOK", "KWOK", "KWOK", "KYOK", ".KK."],
    ["KK"] * 8,
]
COIN_FRAMES.append(COIN_FRAMES[1])

BUSH = [
    "...KKK.KKK..",
    "..KGGGKGGGK.",
    ".KGgGGGGgGGK",
    "KGGGGgGGGGgK",
    "KKKKKKKKKKKK",
]

FLOWER = [".PRP.", "RRYRR", ".PRP.", "..G..", ".GG..", "..G.."]
FLOWER2 = [".PRP.", "RRYRR", ".PRP.", "..G..", "..GG.", "..G.."]

# ── Стикеры вокруг интерфейса ────────────────────────────────────────────────
CONTROLLER = [
    "..KKKKKKKKKKKK..",
    ".KVVVVVVVVVVVVK.",
    "KVVKVVVVVVVVRVVK",
    "KVKKKVVVVVVRVYVK",
    "KVVKVVVKKVVVCVVK",
    "KVVVVVVVVVVVVVVK",
    ".KVVVVKKKKVVVVK.",
    "..KKKK....KKKK..",
]

POTION = [
    "..KKKK..",
    "..KNNK..",
    "...KK...",
    "..KPPK..",
    ".KPWPPK.",
    "KPWPPPPK",
    "KPPPPPPK",
    "KRPPPPRK",
    ".KRRRRK.",
    "..KKKK..",
]

GEM = [
    "..KKKKK..",
    ".KCWCCcK.",
    "KCWCCCCcK",
    "KKKKKKKKK",
    ".KCCCCcK.",
    "..KCCcK..",
    "...KcK...",
    "....K....",
]

SWORD = [
    "...KK..",
    "..KWLK.",
    "..KWLK.",
    "..KWLK.",
    "..KWLK.",
    "..KWLK.",
    "KKKWLKK",
    "KYYYYYK",
    "KKKNNKK",
    "..KNNK.",
    "..KYYK.",
    "...KK..",
]

DIGITS = {
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    ":": ["...", ".#.", ".#.", "...", ".#.", ".#.", "..."],
}


def fmt_hms(sec):
    sec = int(sec)
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def lighten(hex_color, k=0.4):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    r, g, b = (int(v + (255 - v) * k) for v in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def moon_cells(r=6, shift=3):
    cells = []
    for j in range(2 * r + 1):
        for i in range(2 * r + 1):
            in_big = (i - r) ** 2 + (j - r) ** 2 <= r * r + r * 0.6
            in_cut = (i - r - shift) ** 2 + (j - r + 1) ** 2 <= (r - 1) ** 2
            if in_big and not in_cut:
                cells.append((i, j))
    return cells


def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{int(x + (y - x) * t):02x}" for x, y in zip(a, b))


# ── Иконка приложения (64×64 пиксельных клетки) ─────────────────────────────
def icon_grid():
    n, lo, hi, r = 64, 5, 58, 9

    def inside(x, y, pad=0):
        a, b, rr = lo + pad, hi - pad, r - pad
        if not (a <= x <= b and a <= y <= b):
            return False
        cx, cy = min(max(x, a + rr), b - rr), min(max(y, a + rr), b - rr)
        return (x - cx) ** 2 + (y - cy) ** 2 <= rr * rr

    g =[[None] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            if not inside(x, y):
                continue
            if not inside(x, y, 2):
                g[y][x] = PALETTE["K"]
            elif y < 46:
                g[y][x] = mix("#3b2d85", "#1f1650", (y - lo) / 41)
            elif y < 49:
                g[y][x] = C["grass"] if (x // 3) % 2 else C["grass2"]
            else:
                g[y][x] = C["dirt"] if (x // 3 + y // 3) % 2 else C["dirt2"]

    def put(rows, x0, y0, s=1):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != "." and PALETTE.get(ch):
                    for dy in range(s):
                        for dx in range(s):
                            g[y0 + j * s + dy][x0 + i * s + dx] = PALETTE[ch]

    for sx, sy in ((12, 14), (25, 9), (34, 13), (10, 26), (53, 30)):
        g[sy][sx] = C["yellow"]
    for sx, sy in ((19, 20), (49, 24)):
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            g[sy + dy][sx + dx] = C["yellow"]
    for i, j in moon_cells(6, 3):
        g[9 + j][42 + i] = C["yellow"]
    put(CAT_AWAKE, 16, 16, 2)
    put(HEART, 8, 37)
    put(COIN_FRAMES[0], 50, 36)
    return g


def icon_photo(size, grid_fn=None):
    """PhotoImage с иконкой нужного размера (нужен созданный tk.Tk)."""
    grid = (grid_fn or icon_grid)()
    n = len(grid)
    if size < n:
        return icon_photo(n, grid_fn).subsample(n // size)
    s = size // n
    img = tk.PhotoImage(width=size, height=size)
    for y, row in enumerate(grid):
        for x, col in enumerate(row):
            if col:
                img.put(col, to=(x * s, y * s, (x + 1) * s, (y + 1) * s))
    return img


class App:
    def __init__(self, root):
        self.root = root
        root.title("Task Quest · Pixel")
        root.resizable(False, False)
        root.configure(bg=C["bg"])

        families = set(tkfont.families())
        fam = next((f for f in ("Menlo", "Monaco", "Consolas", "Courier New", "Courier") if f in families), "TkFixedFont")
        self.font = lambda size, bold=True: (fam, size, "bold" if bold else "normal")

        self.cv = tk.Canvas(root, width=W, height=H, bg=C["bg"], highlightthickness=0)
        self.cv.pack()
        # фоновый «пиксельный» узор — рисуется один раз
        for row, y in enumerate(range(10, H, 24)):
            for x in range(12 * (row % 2), W, 24):
                self.cv.create_rectangle(x, y, x + 3, y + 3, fill="#261d57", outline="", tags="bg")
        self.on_switch = None  # задаётся оболочкой task_quest.py

        self.f = 0
        self.particles = []
        self.pressed = {}
        self.hits = []
        self.scroll = 0
        self.toast = None
        self.topmost = False
        self.stars = [(random.randint(36, 440), random.randint(64, 178), random.randint(0, 40)) for _ in range(28)]
        self.moon = moon_cells()
        self.clouds = [[140, 96, 0.5], [330, 76, 0.3], [520, 112, 0.4]]
        self.rain = [self.new_drop(x, random.uniform(-H, H)) for x in range(10, W, RAIN_GAP)]
        # голова — почти белая, хвост плавно растворяется в фоне
        self.rain_colors = ["#d8ffe9"] + [mix("#3fdc8a", C["bg"], 0.25 + 0.7 * k / RAIN_TRAIL)
                                           for k in range(1, RAIN_TRAIL)]

        self.load()
        self.last_lv = self.level()[0]
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

    # ── данные ────────────────────────────────────────────────────────────
    def load(self):
        self.data = {"tasks": [], "sessions": [], "running": None, "selected": None, "rain": True}
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, encoding="utf-8") as fh:
                    self.data.update(json.load(fh))
            except (OSError, ValueError):
                os.replace(DATA_FILE, DATA_FILE + ".broken")
        self.recompute()

    def save(self):
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, DATA_FILE)

    def recompute(self):
        self.totals = {}
        for s in self.data["sessions"]:
            self.totals[s["task_id"]] = self.totals.get(s["task_id"], 0) + s["end"] - s["start"]

    def task(self, tid):
        return next((t for t in self.data["tasks"] if t["id"] == tid), None)

    def task_total(self, tid):
        total = self.totals.get(tid, 0)
        r = self.data["running"]
        if r and r["task_id"] == tid:
            total += time.time() - r["start"]
        return total

    def today_total(self):
        sod = datetime.combine(date.today(), datetime.min.time()).timestamp()
        spans = [(s["start"], s["end"]) for s in self.data["sessions"]]
        if self.data["running"]:
            spans.append((self.data["running"]["start"], time.time()))
        return sum(max(0, end - max(start, sod)) for start, end in spans)

    def level(self):
        today = self.today_total()
        return int(today // LEVEL_SEC) + 1, (today % LEVEL_SEC) / LEVEL_SEC

    def session_elapsed(self):
        r = self.data["running"]
        return time.time() - r["start"] if r else 0

    # ── действия ──────────────────────────────────────────────────────────
    def add_task(self, _event=None):
        name = self.entry.get().strip()
        if not name or self.placeholder_on:
            self.show_toast("Введи название квеста", 25)
            return
        t = {"id": uuid.uuid4().hex[:8], "name": name, "created": time.time()}
        self.data["tasks"].insert(0, t)
        if not self.data["running"]:
            self.data["selected"] = t["id"]
        self.scroll = 0
        self.entry.delete(0, "end")
        self.save()
        self.burst("sparkle", 240, 140, 10)
        self.show_toast("Новый квест!", 20)

    def select(self, tid):
        r = self.data["running"]
        if r and r["task_id"] != tid:
            self.stop()
            self.data["selected"] = tid
            self.start()
        else:
            self.data["selected"] = tid
            self.save()

    def toggle(self):
        self.press("main")
        if self.data["running"]:
            self.stop()
        else:
            self.start()

    def start(self):
        tid = self.data["selected"]
        if not self.task(tid):
            self.show_toast("Сначала выбери квест", 25)
            return
        self.data["running"] = {"task_id": tid, "start": time.time()}
        self.save()
        self.burst("sparkle", 200, 120, 14)
        self.show_toast("Поехали! ★", 18)

    def stop(self):
        r = self.data["running"]
        if not r:
            return
        end = time.time()
        if end - r["start"] >= 1:
            self.data["sessions"].append({"task_id": r["task_id"], "start": r["start"], "end": end})
        self.data["running"] = None
        self.recompute()
        self.save()
        self.burst("heart", 240, 150, 14)
        self.particles.append({"kind": "text", "x": 240, "y": 120, "vx": 0, "vy": -0.9,
                               "life": 32, "text": "+" + fmt_hms(end - r["start"])})

    def delete_task(self, tid):
        t = self.task(tid)
        if not t:
            return
        if not messagebox.askyesno("Удалить квест", f"Удалить «{t['name']}» вместе со всей историей времени?"):
            return
        if self.data["running"] and self.data["running"]["task_id"] == tid:
            self.data["running"] = None
        self.data["tasks"] = [x for x in self.data["tasks"] if x["id"] != tid]
        self.data["sessions"] = [s for s in self.data["sessions"] if s["task_id"] != tid]
        if self.data["selected"] == tid:
            self.data["selected"] = self.data["tasks"][0]["id"] if self.data["tasks"] else None
        self.recompute()
        self.scroll_by(0)
        self.save()

    def clear_tasks(self):
        self.press("clear")
        n = len(self.data["tasks"])
        if not n:
            self.show_toast("Список и так пуст", 20)
            return
        if not messagebox.askyesno(
                "Очистить список",
                f"Удалить все квесты ({n}) вместе с историей времени?\n\n"
                "Перед очисткой я сохраню резервную копию рядом с программой."):
            return
        backup = os.path.join(os.path.dirname(DATA_FILE),
                              f"tracker_backup_{datetime.now():%Y-%m-%d_%H-%M-%S}.json")
        with open(backup, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, ensure_ascii=False, indent=1)
        self.data.update(tasks=[], sessions=[], running=None, selected=None)
        self.recompute()
        self.scroll = 0
        self.save()
        self.burst("sparkle", 240, 140, 16)
        self.show_toast("Список очищен ✓ копия сохранена", 40)

    def export_csv(self):
        self.press("csv")
        path = os.path.join(os.path.expanduser("~/Desktop"), f"pixel_tracker_{date.today():%Y-%m-%d}.csv")
        names = {t["id"]: t["name"] for t in self.data["tasks"]}
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow(["Задача", "Начало", "Конец", "Длительность", "Минуты"])
            for s in sorted(self.data["sessions"], key=lambda s: s["start"]):
                dur = s["end"] - s["start"]
                w.writerow([names.get(s["task_id"], "?"),
                            datetime.fromtimestamp(s["start"]).strftime("%d.%m.%Y %H:%M:%S"),
                            datetime.fromtimestamp(s["end"]).strftime("%d.%m.%Y %H:%M:%S"),
                            fmt_hms(dur), round(dur / 60, 1)])
            w.writerow([])
            w.writerow(["ИТОГО ПО ЗАДАЧАМ"])
            for t in self.data["tasks"]:
                w.writerow([t["name"], "", "", fmt_hms(self.totals.get(t["id"], 0)),
                            round(self.totals.get(t["id"], 0) / 60, 1)])
        self.show_toast("CSV сохранён на Рабочий стол", 35)

    def toggle_top(self):
        self.press("top")
        self.topmost = not self.topmost
        self.root.attributes("-topmost", self.topmost)
        self.show_toast("Поверх окон: " + ("ВКЛ" if self.topmost else "ВЫКЛ"), 20)

    def switch_skin(self):
        self.press("skin")
        if self.on_switch:
            self.on_switch()

    def teardown(self):
        """Убирает этот скин из окна, чтобы на его место встал другой."""
        if getattr(self, "_after", None):
            self.root.after_cancel(self._after)
        self.entry.destroy()
        self.cv.destroy()

    def toggle_rain(self):
        self.press("rain")
        self.data["rain"] = not self.data["rain"]
        self.save()
        self.show_toast("Цифровой дождь: " + ("ВКЛ" if self.data["rain"] else "ВЫКЛ"), 20)

    def on_close(self):
        if self.data["running"]:
            ans = messagebox.askyesnocancel(
                "Таймер идёт",
                "Остановить таймер и сохранить время?\n\n"
                "Да — остановить\nНет — выйти, таймер продолжит идти до следующего запуска")
            if ans is None:
                return
            if ans:
                self.stop()
        self.save()
        release_lock()
        self.root.destroy()

    # ── ввод ──────────────────────────────────────────────────────────────
    def build_entry(self):
        self.entry = tk.Entry(self.root, font=self.font(13), bg=C["ink"], fg=C["text"],
                              insertbackground=C["yellow"], relief="flat",
                              highlightthickness=3, highlightbackground=C["dim"], highlightcolor=C["yellow"])
        self.cv.create_window(26, 432, anchor="nw", window=self.entry, width=350, height=34)
        self.placeholder = "новый квест..."
        self.placeholder_on = False
        self.set_placeholder()
        self.entry.bind("<FocusIn>", self.clear_placeholder)
        self.entry.bind("<FocusOut>", lambda e: self.set_placeholder())
        self.entry.bind("<Return>", self.add_task)

    def set_placeholder(self):
        if not self.entry.get():
            self.placeholder_on = True
            self.entry.config(fg=C["dim"])
            self.entry.insert(0, self.placeholder)

    def clear_placeholder(self, _e=None):
        if self.placeholder_on:
            self.entry.delete(0, "end")
            self.entry.config(fg=C["text"])
            self.placeholder_on = False

    def on_space(self, event):
        if self.root.focus_get() is self.entry:
            return
        self.toggle()

    def on_click(self, e):
        self.cv.focus_set()  # снимаем фокус с поля ввода, чтобы работал пробел
        for x1, y1, x2, y2, cb in reversed(self.hits):
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                cb()
                return

    def on_wheel(self, e):
        if e.delta:
            self.scroll_by(-1 if e.delta > 0 else 1)

    def scroll_by(self, d):
        max_scroll = max(0, len(self.data["tasks"]) - self.ROWS)
        self.scroll = min(max(0, self.scroll + d), max_scroll)

    def press(self, name):
        self.pressed[name] = self.f + 3

    def show_toast(self, text, frames):
        self.toast = (text, self.f + frames)

    # ── частицы ───────────────────────────────────────────────────────────
    def burst(self, kind, x, y, n):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            sp = random.uniform(1.5, 4.5)
            self.particles.append({"kind": kind, "x": x, "y": y, "vx": math.cos(a) * sp,
                                   "vy": math.sin(a) * sp - 2, "life": random.randint(16, 28)})

    def update_particles(self):
        alive = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            if p["kind"] in ("heart", "sparkle", "coin") and p.get("gravity", True):
                p["vy"] += 0.18
                p["vx"] *= 0.97
            if p["kind"] == "z":
                p["vx"] = math.sin(p["life"] / 4) * 0.6
            if p["life"] > 0:
                alive.append(p)
        self.particles = alive

    # ── отрисовка ─────────────────────────────────────────────────────────
    def rect(self, x1, y1, x2, y2, fill, outline="", width=0):
        self.cv.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=width, tags="dyn")

    def text(self, x, y, s, color, size=12, anchor="center", shadow=C["ink"]):
        if shadow:
            self.cv.create_text(x + 2, y + 2, text=s, fill=shadow, font=self.font(size), anchor=anchor, tags="dyn")
        self.cv.create_text(x, y, text=s, fill=color, font=self.font(size), anchor=anchor, tags="dyn")

    def sprite(self, rows, cx, bottom, sx=4.0, sy=None, color=None):
        sy = sy or sx
        w, h = len(rows[0]), len(rows)
        x0, y0 = cx - w * sx / 2, bottom - h * sy
        for j, row in enumerate(rows):
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
                          color or PALETTE[ch])
                i = k

    def button(self, name, x1, y1, x2, y2, label, color, cb, size=14, fg=C["ink"]):
        down = self.pressed.get(name, -1) >= self.f
        o = 3 if down else 0
        if not down:
            self.rect(x1 + 4, y1 + 4, x2 + 4, y2 + 4, C["ink"])
        self.rect(x1 + o, y1 + o, x2 + o, y2 + o, color, C["ink"], 3)
        if y2 - y1 >= 30:  # на низких кнопках блики налезали бы на текст
            self.rect(x1 + o + 5, y1 + o + 5, x2 + o - 5, y1 + o + 9, lighten(color, 0.45))
            self.rect(x1 + o + 5, y2 + o - 7, x2 + o - 5, y2 + o - 4, self.darken(color))
        self.text((x1 + x2) / 2 + o, (y1 + y2) / 2 + o, label, fg, size, shadow=None)
        self.hits.append((x1, y1, x2 + 4, y2 + 4, cb))

    @staticmethod
    def darken(hex_color, k=0.25):
        r, g, b = (int(int(hex_color[i:i + 2], 16) * (1 - k)) for i in (1, 3, 5))
        return f"#{r:02x}{g:02x}{b:02x}"

    ROWS = 5
    ROW_H = 40
    LIST_TOP = 512

    @staticmethod
    def new_drop(x, y):
        return {"x": x, "y": y, "speed": random.uniform(2.5, 6), "len": random.randint(6, RAIN_TRAIL),
                "chars": [random.choice(RAIN_CHARS) for _ in range(RAIN_TRAIL)]}

    def draw_rain(self, running):
        # рисуется первым в кадре — значит, оказывается позади всего остального
        boost = 1.8 if running else 1
        for i, d in enumerate(self.rain):
            d["y"] += d["speed"] * boost
            if d["y"] - d["len"] * RAIN_STEP > H:
                self.rain[i] = d = self.new_drop(d["x"], random.uniform(-160, 0))
            if random.random() < 0.15:
                d["chars"][random.randrange(RAIN_TRAIL)] = random.choice(RAIN_CHARS)
            head = int(d["y"] // RAIN_STEP)  # символы стоят в клетках, как на старом терминале
            for k in range(d["len"]):
                row = head - k
                y = row * RAIN_STEP
                if y < -RAIN_STEP or y > H:
                    continue
                self.cv.create_text(d["x"], y, text=d["chars"][row % RAIN_TRAIL], fill=self.rain_colors[k],
                                    font=self.font(11, k == 0), tags="dyn")

    def redraw(self):
        self.cv.delete("dyn")
        self.hits = []
        running = self.data["running"]
        f = self.f

        if self.data["rain"]:
            self.draw_rain(running)

        # заголовок
        self.text(W / 2, 28, "★ PIXEL TASK QUEST ★", C["yellow"], 19, shadow=C["pink"])

        # ── сцена ──
        sx1, sy1, sx2, sy2 = 20, 52, 460, 226
        self.rect(sx1, sy1, sx2, sy2, C["sky"], C["ink"], 4)
        for x, y, ph in self.stars:
            if (f + ph) % 40 < 5:
                self.rect(x - 1, y - 5, x + 2, y + 6, C["yellow"])
                self.rect(x - 5, y - 1, x + 6, y + 2, C["yellow"])
            else:
                self.rect(x, y, x + 3, y + 3, C["dim"])
        for i, j in self.moon:
            self.rect(380 + i * 4, 64 + j * 4, 384 + i * 4, 68 + j * 4, C["yellow"])
        if f % 150 == 75:
            self.particles.append({"kind": "shoot", "x": random.randint(220, 440), "y": 58,
                                   "vx": -5, "vy": 2.5, "life": 16, "gravity": False})
        for cl in self.clouds:
            cl[0] -= cl[2] * (2 if running else 1)
            if cl[0] < sx1 - 40:
                cl[0] = sx2 + 40
            self.sprite(CLOUD, cl[0], cl[1], 3)
        ux = (f % 600) * 3 - 40
        if ux < W + 40:
            self.sprite(UFO if (f // 3) % 2 else UFO_BLINK, ux, 104 + math.sin(f * 0.2) * 5, 2.5)
        for gx in range(sx1 + 2, sx2 - 2, 10):
            k = (gx // 10) % 2
            self.rect(gx, 198, min(gx + 10, sx2 - 2), 206, C["grass"] if k else C["grass2"])
            self.rect(gx, 206, min(gx + 10, sx2 - 2), 224, C["dirt"] if k else C["dirt2"])

        ground = 198
        self.sprite(BUSH, 178, ground, 3)
        self.sprite(BUSH, 428, ground, 3)
        for i, fx in enumerate((148, 248, 268, 392)):
            self.sprite(FLOWER if (f // 8 + i) % 2 else FLOWER2, fx, ground, 3)

        # блок-сюрприз: пока идёт таймер, выбрасывает монетки
        bump = 0
        if running and f % 50 < 3:
            bump = 5
            if f % 50 == 0:
                self.particles.append({"kind": "coin", "x": 92, "y": 82, "vx": 0, "vy": -2.2, "life": 14})
        self.sprite(BLOCK, 92, 112 - bump, 2.5)

        # вращающиеся монетки над Моти
        for i, cx in enumerate((300, 330, 360)):
            frame = COIN_FRAMES[(f // 3 + i) % 4]
            self.sprite(frame, cx, 116 + math.sin(f * 0.15 + i) * 3, 2)
        # кошечка
        cat_x = 92
        if running:
            hop = abs(math.sin(f * 0.32)) * 16
            frame = CAT_SLEEP if f % 45 in (0, 1) else CAT_AWAKE
            self.rect(cat_x - 22 + hop / 3, ground - 4, cat_x + 22 - hop / 3, ground, C["grass2"])
            self.sprite(frame, cat_x, ground - hop, 4)
        else:
            breathe = math.sin(f * 0.12) * 0.12
            self.sprite(CAT_SLEEP, cat_x, ground, 4 + breathe, 4 - breathe)
            if f % 22 == 0:
                self.particles.append({"kind": "z", "x": cat_x + 26, "y": ground - 66, "vx": 0,
                                       "vy": -0.9, "life": 34})

        # моти
        moti_x = 330
        if running:
            s = abs(math.sin(f * 0.26 + 1))
            hop = s * 30
            sxm, sym = (4.7, 3.3) if s < 0.25 else (3.8, 4.3)
            self.rect(moti_x - 24 + hop / 2, ground - 4, moti_x + 24 - hop / 2, ground, C["grass2"])
            self.sprite(MOTI, moti_x, ground - hop, sxm, sym)
            if f % 18 == 0:
                self.particles.append({"kind": "heart", "x": moti_x, "y": ground - hop - 50, "vx": random.uniform(-0.6, 0.6),
                                       "vy": -1.2, "life": 26, "gravity": False})
        else:
            breathe = math.sin(f * 0.1) * 0.15
            self.sprite(MOTI, moti_x, ground, 4 + breathe, 4 - breathe)

        # звёздочка-фея
        if running:
            st_x = 210 + math.cos(f * 0.12) * 46
            st_y = 128 + math.sin(f * 0.24) * 22
            if f % 3 == 0:
                self.particles.append({"kind": "sparkle", "x": st_x, "y": st_y + 10, "vx": random.uniform(-0.5, 0.5),
                                       "vy": 0.4, "life": 14, "gravity": False})
        else:
            st_x, st_y = 212, 142 + math.sin(f * 0.15) * 6
        self.sprite(STAR, st_x, st_y + 18, 4)

        # частицы
        for p in self.particles:
            k = p["kind"]
            if k == "sparkle":
                self.sprite(SPARKLE, p["x"], p["y"], 2 if p["life"] % 4 < 2 else 3)
            elif k == "heart":
                self.sprite(HEART, p["x"], p["y"], 3)
            elif k == "z":
                self.text(p["x"], p["y"], "z" if p["life"] > 20 else "Z", C["text"], 10 if p["life"] > 20 else 14, shadow=None)
            elif k == "text":
                self.text(p["x"], p["y"], p["text"], C["mint"], 16)
            elif k == "coin":
                self.sprite(COIN_FRAMES[(p["life"] // 2) % 4], p["x"], p["y"], 2)
            elif k == "shoot":
                for t in range(5):
                    size = 4 - t * 0.6
                    x, y = p["x"] - p["vx"] * t * 0.8, p["y"] - p["vy"] * t * 0.8
                    self.rect(x, y, x + size, y + size, C["yellow"] if t < 2 else C["text"])

        # полоска опыта: 1 уровень = 25 минут работы за сегодня
        lv, xp = self.level()
        if lv > self.last_lv and running:
            self.burst("sparkle", 92, 100, 18)
            self.show_toast(f"LEVEL UP! ★ LV {lv}", 40)
        self.last_lv = lv
        self.rect(26, 58, 158, 78, C["ink"])
        self.text(32, 68, f"LV{lv:02d}", C["yellow"], 10, anchor="w", shadow=None)
        filled = int(xp * 10)
        for i in range(10):
            if i < filled:
                col = C["mint"]
            elif i == filled and running and (f // 4) % 2:  # мигает клетка, которая сейчас набирается
                col = C["dim"]
            else:
                col = C["panel"]
            self.rect(72 + i * 8, 63, 78 + i * 8, 73, col)

        # обрезаем то, что вылезло за края сцены, и обводим рамку заново
        self.rect(0, sy1 - 2, sx1, sy2 + 2, C["bg"])
        self.rect(sx2, sy1 - 2, W, sy2 + 2, C["bg"])
        self.rect(sx1, sy1, sx2, sy2, "", C["ink"], 4)

        # стикеры вокруг интерфейса
        sp = 0.3 if running else 0.13
        bob = lambda ph: math.sin(f * sp + ph) * 3
        self.sprite(CONTROLLER, 50, 42 + bob(0), 2)
        self.sprite(POTION, 432, 44 + bob(1.5), 2.5)
        self.sprite(SWORD, 56, 292 + bob(3), 3)
        self.sprite(GEM, 424, 286 + bob(4.5), 3)
        if (f + 10) % 40 < 6:
            self.sprite(SPARKLE, 436, 266 + bob(4.5), 2 if (f % 40) < 3 else 3)
        self.sprite(COIN_FRAMES[(f // 3) % 4], 70, 384 + bob(2), 3)
        pulse = abs(math.sin(f * (0.25 if running else 0.1))) * 0.6
        self.sprite(HEART, 410, 384, 3 + pulse)

        if self.toast and self.toast[1] >= f:
            tw = len(self.toast[0]) * 8 + 24
            self.rect(W / 2 - tw / 2, 60, W / 2 + tw / 2, 86, C["ink"], C["pink"], 2)
            self.text(W / 2, 73, self.toast[0], C["text"], 11, shadow=None)

        # ── таймер ──
        sel = self.task(self.data["selected"])
        total = self.task_total(sel["id"]) if sel else 0
        digits = fmt_hms(total)
        if running and (f // 6) % 2:
            digits = digits.replace(":", " ")
        color = C["yellow"] if running else C["dim"]
        self.pixel_text(digits, W / 2, 244, 6, color)

        label = sel["name"] if sel else "— нет квеста —"
        if len(label) > 34:
            label = label[:33] + "…"
        self.text(W / 2, 306, label, C["text"], 13)
        if running:
            self.text(W / 2, 326, "сессия " + fmt_hms(self.session_elapsed()), C["pink"], 11)
        else:
            self.text(W / 2, 326, "всего по квесту", C["dim"], 11)

        # главная кнопка
        if running:
            self.button("main", 130, 342, 350, 394, "■  СТОП", C["red"], self.toggle, 18)
        else:
            self.button("main", 130, 342, 350, 394, "▶  СТАРТ", C["mint"], self.toggle, 18)

        # общее время за день по всем квестам
        self.rect(120, 402, 360, 426, C["ink"], C["mint"] if running else C["yellow"], 2)
        self.text(134, 414, "ЗА ДЕНЬ", C["pink"], 11, anchor="w", shadow=None)
        self.pixel_text(fmt_hms(self.today_total()), 290, 407, 2, C["mint"] if running else C["yellow"])

        # ── добавление ──
        self.button("add", 388, 430, 454, 468, "+", C["yellow"], lambda: (self.press("add"), self.add_task()), 20)

        # ── список ──
        self.text(26, 492, "КВЕСТЫ", C["pink"], 12, anchor="w")
        self.text(410, 492, "ВРЕМЯ", C["pink"], 12, anchor="e")
        if self.data["tasks"]:
            self.button("clear", 112, 481, 222, 503, "ОЧИСТИТЬ", C["red"], self.clear_tasks, 10)
        tasks = self.data["tasks"]
        if not tasks:
            self.text(W / 2, self.LIST_TOP + 60, "пока пусто… добавь квест выше ↑", C["dim"], 12)
        for idx in range(self.scroll, min(len(tasks), self.scroll + self.ROWS)):
            t = tasks[idx]
            y = self.LIST_TOP + (idx - self.scroll) * self.ROW_H
            is_run = running and running["task_id"] == t["id"]
            is_sel = t["id"] == self.data["selected"]
            fill = C["sel"] if is_sel else C["panel"]
            self.rect(24, y, 456, y + 34, fill, C["ink"], 3)
            if is_sel:
                self.rect(27, y + 3, 33, y + 31, C["pink"] if is_run else C["yellow"])
            name = t["name"] if len(t["name"]) <= 26 else t["name"][:25] + "…"
            marker = ("▶ " if (f // 5) % 2 else "▷ ") if is_run else ""
            self.text(42, y + 17, marker + name, C["text"], 12, anchor="w")
            self.text(410, y + 17, fmt_hms(self.task_total(t["id"])),
                      C["mint"] if is_run else C["yellow"], 12, anchor="e")
            self.text(436, y + 17, "✕", C["red"], 12, shadow=None)
            tid = t["id"]
            self.hits.append((24, y, 422, y + 34, lambda tid=tid: self.select(tid)))
            self.hits.append((424, y, 456, y + 34, lambda tid=tid: self.delete_task(tid)))
        if len(tasks) > self.ROWS:
            bar_h = self.ROWS * self.ROW_H - 6
            knob = max(20, bar_h * self.ROWS / len(tasks))
            pos = (bar_h - knob) * self.scroll / (len(tasks) - self.ROWS)
            self.rect(460, self.LIST_TOP, 466, self.LIST_TOP + bar_h, C["panel"])
            self.rect(460, self.LIST_TOP + pos, 466, self.LIST_TOP + pos + knob, C["dim"])

        # ── футер ──
        fy = H - 40
        self.button("csv", 24, fy, 94, fy + 26, "CSV", C["pink"], self.export_csv, 11)
        self.button("top", 104, fy, 174, fy + 26, "TOP", C["yellow"] if self.topmost else C["dim"], self.toggle_top, 11)
        self.button("rain", 184, fy, 254, fy + 26, "RAIN", C["mint"] if self.data["rain"] else C["dim"],
                    self.toggle_rain, 11)
        self.button("skin", 264, fy, 334, fy + 26, "SKIN", C["mint"], self.switch_skin, 11)
        self.text(456, fy + 13, "ПРОБЕЛ ▶/■", C["dim"], 10, anchor="e", shadow=None)

    def pixel_text(self, s, cx, top, scale, color):
        # мигающее двоеточие заменено пробелом — рисуем его как пустой символ той же ширины
        widths = [3 if ch in ": " else 5 for ch in s]
        total = sum(w * scale for w in widths) + (len(s) - 1) * scale
        x = cx - total / 2
        shadow = max(2, round(scale * 0.67))
        for ch, w in zip(s, widths):
            if ch != " ":
                for dx, col in ((shadow, C["ink"]), (0, color)):
                    for j, row in enumerate(DIGITS[ch]):
                        for i, px in enumerate(row):
                            if px == "#":
                                self.rect(x + i * scale + dx, top + j * scale + dx,
                                          x + (i + 1) * scale + dx, top + (j + 1) * scale + dx, col)
            x += (w + 1) * scale

    def tick(self):
        self.f += 1
        self.update_particles()
        self.redraw()
        self._after = self.root.after(FPS_MS, self.tick)


# ── Защита от одновременного запуска (обе версии пишут в один файл данных) ──
LOCK_FILE = DATA_FILE + ".lock"


def acquire_lock():
    try:
        with open(LOCK_FILE, encoding="utf-8") as fh:
            pid = int(fh.read().strip() or 0)
        if pid and pid != os.getpid():
            os.kill(pid, 0)  # процесс жив — значит, трекер уже открыт
            return False
    except (OSError, ValueError):
        pass
    with open(LOCK_FILE, "w", encoding="utf-8") as fh:
        fh.write(str(os.getpid()))
    return True


def release_lock():
    try:
        with open(LOCK_FILE, encoding="utf-8") as fh:
            if fh.read().strip() == str(os.getpid()):
                os.remove(LOCK_FILE)
    except OSError:
        pass


def main():
    import task_quest  # единое приложение со скинами
    task_quest.main("pixel")


if __name__ == "__main__":
    main()
