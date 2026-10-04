#!/usr/bin/env python3
"""Скин «MiniDisc» для Task Quest.

Картридж MiniDisc (assets/md.png), а внутри вместо родного диска крутится диск из нашей коллекции
(assets/discs/*.png). Поверх диска — металлическая втулка и шторка; в окошке ярлыка, где было
«60 LAPISIA», — время квеста. Снизу — серебристые кнопки и список квестов в стиле трек-листа.

Кадры вращения рисует CoreGraphics (disc_render.py) в фоне при первом показе диска и кладёт
в кэш ~/Library/Caches/TaskQuest/md — в репозитории лежат только исходники дисков.

Окно обычное, не прозрачное: прозрачные окна macOS перерисовываются целиком и тормозят.

Запуск:  python3 task_quest.py md
"""
import math
import os
import random
import shutil
import threading
import time
import tkinter as tk
from tkinter import font as tkfont

import disc_render
import mac_disc
import pixel_tracker as pt
import task_quest_2000 as tq
from pixel_tracker import fmt_hms

W, H = 480, 770
ASSETS = os.path.join(pt.APP_DIR, "assets")
CACHE = os.path.expanduser("~/Library/Caches/TaskQuest/md")

DISC_TITLES = {   # assets/discs/<имя>.png → название
    "kirby": "Kirby Air Ride", "bratz": "Bratz Rock Angelz", "re4": "Resident Evil 4",
    "gow": "God of War", "sonic98": "Sonic · Hardcore 98", "nirvana": "Nirvana · Nevermind",
    "evilwithin": "The Evil Within", "dmc3": "Devil May Cry 3", "dmc": "Devil May Cry",
    "sh2": "Silent Hill 2", "matrix": "Matrix: Path of Neo", "re4ps3": "Resident Evil 4 PS3",
    "manhunt": "Manhunt", "mk": "MK: Deception", "sonicadv": "Sonic Adventure",
    "outlast": "Outlast Trinity", "sims2": "The Sims 2", "sh3": "Silent Hill 3",
}
DISCS = list(DISC_TITLES)
DISC_CENTER, DISC_SIZE, DISC_FRAMES = (222, 220), 420, 48   # центр и диаметр диска, кадров на оборот (по 7,5°)
# вращение как у CD-проигрывателя: разгон при старте и долгий выбег до остановки
DISC_MS = 50              # свой цикл диска — 20 кадров в секунду, работает только пока диск крутится
DISC_SPEED = 150          # градусов в секунду на полном ходу (оборот за 2,4 с)
DISC_SPINUP = 1.2         # секунд на разгон
DISC_COAST = (0.15, 0.55)  # выбег: постоянное трение + трение от скорости — остановка ≈ 3 с
HUB_AT, SHUTTER_AT = (222, 220), (282, 150)
LABEL = (300, 171, 468, 276)                                 # чёрное окошко ярлыка на шторке
PANEL_Y = 466                                                # нижняя панель — под картриджем
DISC_EVERY_SEC = 20                                          # пока идёт таймер, диск меняется сам

C = {
    "panel": "#08141b", "panel2": "#0d1d26", "line": "#2f6f86", "cyan": "#8ff0ff", "cyan_dim": "#4fa8bd",
    "text": "#e6fbff", "label": "#b9bec3", "label_dim": "#8d9399", "black": "#000000",
    "silver1": "#e3e6e9", "silver2": "#9aa1a7", "silver_edge": "#3a4045", "ink": "#0b1014",
    "sel": "#8ff0ff", "run": "#ffd166",
}
BUTTONS = [   # имя, подпись, x1, x2 — серебристые кнопки как металлический ярлык
    ("main", "▶ START", 12, 150), ("add", "+ ДОБАВИТЬ", 156, 262), ("del", "− УДАЛИТЬ", 268, 362),
    ("csv", "CSV", 368, 400), ("top", "TOP", 404, 436), ("skin", "SKIN", 440, 470),
]
BTN_Y = (PANEL_Y + 10, PANEL_Y + 40)
LIST_TOP, ROW_H, ROWS = PANEL_Y + 104, 26, 6


class AppMD(tq.App2):
    ROWS = ROWS
    ROW_H = ROW_H
    LIST_TOP = LIST_TOP

    def __init__(self, root):  # noqa: своя сцена, как у остальных скинов
        self.root = root
        root.title("Task Quest · MiniDisc")
        root.resizable(False, False)
        root.configure(bg=C["panel"])
        families = set(tkfont.families())
        sans = next((f for f in ("Helvetica Neue", "Helvetica", "Arial") if f in families), "TkDefaultFont")
        mono = next((f for f in ("Menlo", "Monaco", "Courier") if f in families), "TkFixedFont")
        self.sans = lambda size, bold=True: (sans, size, "bold" if bold else "normal")
        self.font = lambda size, bold=True: (mono, size, "bold" if bold else "normal")

        self.cv = tk.Canvas(root, width=W, height=H, bg=C["panel"], highlightthickness=0)
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
        self.hover = None
        self.keys, self.sec_hits = {}, {}
        self.frames = {}          # имя диска → список PhotoImage (заполняется по мере загрузки)
        self.rendering = set()    # диски, кадры которых сейчас рисуются в фоне
        self.disc_angle = 0.0
        self.disc_speed = 0.0
        self.disc_last = time.perf_counter()
        self._disc_after = None
        self.native = None        # диск на слое Core Animation (macOS) — если получилось подключить
        self.native_tried = 0.0
        self.disc_switch_at = time.time() + DISC_EVERY_SEC

        self.load()
        self.data["md_disc"] = self.data.get("md_disc", 0) % len(DISCS)
        self.last_lv = self.level()[0]

        self.bg = tk.PhotoImage(file=os.path.join(ASSETS, "md.png"))
        self.hub = tk.PhotoImage(file=os.path.join(ASSETS, "md_hub.png"))
        self.shutter = tk.PhotoImage(file=os.path.join(ASSETS, "md_shutter.png"))
        self.draw_static()
        self.build_entry()

        self.cv.bind("<Button-1>", self.on_click)
        self.cv.bind("<Motion>", self.on_motion)
        self.cv.bind("<Leave>", lambda e: setattr(self, "hover", None))
        self.cv.bind("<MouseWheel>", self.on_wheel)
        root.bind("<space>", self.on_space)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        if not mac_disc.AVAILABLE:   # на macOS диск крутит Core Animation, кадры Tk — только запасной вариант
            self.want_disc(self.current_disc())
        if not self.data["tasks"]:
            self.show_toast("ДОБАВЬ ПЕРВЫЙ ТРЕК", 60)
        self.tick()

    # ── диски ─────────────────────────────────────────────────────────────
    def current_disc(self):
        return DISCS[self.data["md_disc"]]

    def want_disc(self, name):
        """Кадры диска: из кэша, а если их нет — рисуем в фоне (CoreGraphics, доли секунды)."""
        if name in self.frames or name in self.rendering:
            return
        folder = os.path.join(CACHE, f"{name}_{DISC_SIZE}_{DISC_FRAMES}")
        if os.path.exists(os.path.join(folder, f"{DISC_FRAMES - 1}.png")):
            self.frames[name] = []
            return
        self.rendering.add(name)

        def work():
            try:
                disc_render.render_frames(os.path.join(ASSETS, "discs", f"{name}.png"), folder, DISC_SIZE,
                                          DISC_FRAMES)
            finally:
                self.rendering.discard(name)
                self.frames.setdefault(name, [])
        threading.Thread(target=work, daemon=True).start()

    def load_frames_step(self):
        if self.native:
            return
        self._load_frames_step()

    def _load_frames_step(self):
        """Подгружаем по паре кадров за тик, чтобы окно не замирало: сначала текущий диск, потом следующий,
        чтобы смена диска была мгновенной."""
        name = self.current_disc()
        nxt = DISCS[(self.data["md_disc"] + 1) % len(DISCS)]
        if len(self.frames.get(name) or []) >= DISC_FRAMES:
            for other in list(self.frames):
                if other not in (name, nxt):
                    del self.frames[other]
            if nxt not in self.frames:
                self.want_disc(nxt)
                self.prune_cache({name, nxt})
            name = nxt
        frames = self.frames.get(name)
        if frames is None or len(frames) >= DISC_FRAMES:
            return
        folder = os.path.join(CACHE, f"{name}_{DISC_SIZE}_{DISC_FRAMES}")
        for _ in range(2):
            path = os.path.join(folder, f"{len(frames)}.png")
            if len(frames) >= DISC_FRAMES or not os.path.exists(path):
                break
            frames.append(tk.PhotoImage(file=path))

    @staticmethod
    def prune_cache(keep):
        """В кэше — кадры только текущего и следующего диска (остальные легко нарисовать заново)."""
        keep = {f"{n}_{DISC_SIZE}_{DISC_FRAMES}" for n in keep}
        try:
            for entry in os.listdir(CACHE):
                if entry not in keep:
                    shutil.rmtree(os.path.join(CACHE, entry), ignore_errors=True)
        except OSError:
            pass

    def next_disc(self):
        self.data["md_disc"] = (self.data["md_disc"] + 1) % len(DISCS)
        self.save()
        if self.native:
            self.native.set_image(self.disc_path(self.current_disc()))
        elif not mac_disc.AVAILABLE or self.native_tried == float("inf"):
            self.want_disc(self.current_disc())
        self.show_toast(DISC_TITLES[self.current_disc()].upper(), 30)

    def scratch(self):
        """Клик по диску — «скретч» назад и смена диска (отсчёт 20 секунд начинается заново)."""
        self.disc_speed = -260
        self.spin()
        self.next_disc()
        self.disc_switch_at = time.time() + DISC_EVERY_SEC

    @staticmethod
    def disc_path(name):
        return os.path.join(ASSETS, "discs", f"{name}.png")

    def attach_native(self):
        """Пробуем отдать вращение диска macOS (слой Core Animation над окном): плавно и без нагрузки на Tk."""
        if self.native or not mac_disc.AVAILABLE or time.time() - self.native_tried < 1:
            return
        self.native_tried = time.time()
        if not self.root.winfo_ismapped():
            return
        x0, y0 = DISC_CENTER[0] - DISC_SIZE // 2, DISC_CENTER[1] - DISC_SIZE // 2
        self.native = mac_disc.attach(*self.disc_origin(), DISC_SIZE,
                                      self.disc_path(self.current_disc()), os.path.join(ASSETS, "md_shutter.png"),
                                      SHUTTER_AT[0] - x0, SHUTTER_AT[1] - y0, os.path.join(ASSETS, "md_hub.png"),
                                      360 / DISC_SPEED)
        if not self.native:
            self.native_fails = getattr(self, "native_fails", 0) + 1
            if self.native_fails >= 3:   # не получилось за три попытки — крутим по-старому, кадрами Tk
                self.native_tried = float("inf")
                self.want_disc(self.current_disc())
        if self.native:
            self.frames.clear()   # кадры Tk больше не нужны
            self.native.set_speed(self.disc_speed / DISC_SPEED)
            self.overlay_changed(getattr(self, "overlay_open", False))

    def disc_origin(self):
        """Левый верхний угол квадрата диска в координатах окна (над холстом — панель заголовка)."""
        ox = self.cv.winfo_rootx() - self.root.winfo_rootx()
        oy = self.cv.winfo_rooty() - self.root.winfo_rooty()
        return ox + DISC_CENTER[0] - DISC_SIZE // 2, oy + DISC_CENTER[1] - DISC_SIZE // 2

    def overlay_changed(self, shown):
        """Панель выбора скина поверх окна: слой диска на это время прячем, чтобы он её не закрывал."""
        self.overlay_open = shown
        if self.native:
            self.native.set_hidden(shown)

    def spin(self):
        """Запускает цикл вращения, если он ещё не идёт."""
        if self._disc_after is None:
            self.disc_last = time.perf_counter()
            self._disc_after = self.root.after(DISC_MS, self.disc_step)

    def disc_step(self):
        """Кадр вращения: разгон до полного хода, пока идёт таймер, и долгий плавный выбег после стопа."""
        self._disc_after = None
        now = time.perf_counter()
        dt, self.disc_last = min(0.2, now - self.disc_last), now
        v = self.disc_speed
        if self.data["running"]:
            if v < DISC_SPEED:
                v = min(DISC_SPEED, v + DISC_SPEED / DISC_SPINUP * dt * (2.5 if v < 0 else 1))
        elif v > 0:
            v = max(0.0, v - (DISC_SPEED * DISC_COAST[0] + v * DISC_COAST[1]) * dt)
        elif v < 0:   # после «скретча» на паузе — диск просто останавливается
            v = min(0.0, v + DISC_SPEED * 2 * dt)
        self.disc_speed = v
        self.disc_angle = (self.disc_angle + v * dt) % 360
        self.show_disc()
        if v or self.data["running"]:
            self._disc_after = self.root.after(DISC_MS, self.disc_step)

    def show_disc(self):
        if self.native:
            self.native.set_speed(self.disc_speed / DISC_SPEED)
            return
        frames = self.frames.get(self.current_disc()) or []
        if not frames:
            return
        k = round(self.disc_angle / (360 / DISC_FRAMES)) % DISC_FRAMES
        img = frames[k] if len(frames) == DISC_FRAMES else frames[0]
        if self.keys.get("disc") != str(img):
            self.cv.itemconfigure(self.disc_item, image=img)
            self.keys["disc"] = str(img)

    def teardown(self):
        if self.native:
            self.native.remove()
            self.native = None
        if self._disc_after:
            self.root.after_cancel(self._disc_after)
            self._disc_after = None
        super().teardown()

    def start(self):
        super().start()
        if self.data["running"]:
            self.next_disc()   # на каждом старте — следующий диск коллекции
            self.disc_switch_at = time.time() + DISC_EVERY_SEC

    # ── статичный слой ────────────────────────────────────────────────────
    def draw_static(self):
        cv = self.cv
        self.begin_static()   # картридж и градиент панели — одна картинка фона
        self.place(0, 0, self.bg)
        for i in range(H - PANEL_Y):   # нижняя панель — тёмный прозрачный пластик с голубым отблеском
            self.rect(0, PANEL_Y + i, W, PANEL_Y + i + 1, pt.mix(C["panel2"], C["panel"], i / (H - PANEL_Y)))
        self.rect(0, PANEL_Y, W, PANEL_Y + 1, C["cyan_dim"])
        self.disc_item = cv.create_image(*DISC_CENTER, tags="static")
        cv.create_image(*HUB_AT, image=self.hub, tags="static")
        cv.create_image(*SHUTTER_AT, image=self.shutter, anchor="nw", tags="static")
        x1, y1, x2, y2 = 12, LIST_TOP - 22, 468, LIST_TOP + ROWS * ROW_H + 4
        cv.create_rectangle(x1, y1, x2, y2, outline=C["line"], tags="static")
        cv.create_text(20, y1 + 11, text="TRACK LIST", fill=C["cyan"], font=self.sans(10), anchor="w", tags="static")
        cv.create_text(460, y1 + 11, text="TIME", fill=C["cyan"], font=self.sans(10), anchor="e", tags="static")
        self.layer = "dyn"

    def build_entry(self):
        self.entry = tk.Entry(self.root, font=self.sans(13, False), bg=C["ink"], fg=C["text"],
                              insertbackground=C["cyan"], relief="flat",
                              highlightthickness=1, highlightbackground=C["line"], highlightcolor=C["cyan"])
        self.cv.create_window(12, PANEL_Y + 48, anchor="nw", window=self.entry, width=456, height=26)
        self.placeholder = "новый трек… (Enter — добавить)"
        self.placeholder_on = False
        self.set_placeholder()
        self.entry.bind("<FocusIn>", self.clear_placeholder)
        self.entry.bind("<FocusOut>", lambda e: self.set_placeholder())
        self.entry.bind("<Return>", self.add_task)

    def set_placeholder(self):
        if not self.entry.get():
            self.placeholder_on = True
            self.entry.config(fg=C["cyan_dim"])
            self.entry.insert(0, self.placeholder)

    def clear_placeholder(self, _e=None):
        if self.placeholder_on:
            self.entry.delete(0, "end")
            self.entry.config(fg=C["text"])
            self.placeholder_on = False

    def toggle_fx(self):
        pass

    def delete_selected(self):
        self.press("del")
        if self.data["selected"]:
            self.delete_task(self.data["selected"])

    def on_motion(self, e):
        self.hover = None
        for name, _, x1, x2 in BUTTONS:
            if x1 <= e.x <= x2 and BTN_Y[0] <= e.y <= BTN_Y[1]:
                self.hover = name

    # ── кадр: части перерисовываются, только когда изменилось их содержимое ─
    ORDER = ("label", "buttons", "list", "status", "fx")

    def section(self, name, key, draw):
        if self.keys.get(name) == key:
            return
        self.cv.delete(name)
        saved, self.hits, self.layer = self.hits, [], name
        draw()
        self.sec_hits[name], self.hits, self.layer = self.hits, saved, "dyn"
        self.keys[name] = key
        for upper in self.ORDER[self.ORDER.index(name) + 1:]:
            if self.cv.find_withtag(upper):
                self.cv.tag_lower(name, upper)
                break

    def redraw(self):
        running = self.data["running"]
        f = self.f
        sel = self.task(self.data["selected"])
        today = self.today_total()
        lv, xp = self.level()
        if lv > self.last_lv and running:
            self.show_toast(f"LEVEL UP · LV {lv}", 40)
        self.last_lv = lv

        # диск: кадры подгружаются понемногу; крутится, пока идёт работа
        if running and time.time() >= self.disc_switch_at:   # смена диска каждые 20 секунд работы
            self.next_disc()
            self.disc_switch_at = time.time() + DISC_EVERY_SEC
        self.load_frames_step()
        self.attach_native()
        if self.native:
            self.native.follow(*self.disc_origin())
        if running or self.disc_speed:
            self.spin()
        self.show_disc()

        # окошко ярлыка: статус, время, название трека (как «60 LAPISIA»)
        shown = self.session_elapsed() if running else (self.task_total(sel["id"]) if sel else 0)
        if self.toast and self.toast[1] >= f:
            caption = self.toast[0]
        else:
            caption = (sel["name"] if sel else "НЕТ ТРЕКА").upper()
        caption = caption if len(caption) <= 16 else caption[:15] + "…"
        status = ("● REC" if (f // 6) % 2 else "○ REC") if running else "❚❚ PAUSE"
        self.section("label", (fmt_hms(shown), caption, status), lambda: self.draw_label(fmt_hms(shown), caption,
                                                                                         status, running))

        btn_key = (running, self.hover, self.topmost, tuple(self.pressed.get(n, -1) >= f for n, *_ in BUTTONS),
                   (f // 5) % 2 if self.hover else 0)
        self.section("buttons", btn_key, lambda: self.draw_buttons(running, f))

        tasks = self.data["tasks"]
        rows = tuple((t["id"], t["name"], int(self.task_total(t["id"])), t["id"] == self.data["selected"],
                      bool(running and running["task_id"] == t["id"]))
                     for t in tasks[self.scroll:self.scroll + ROWS])
        self.section("list", (self.scroll, rows, (f // 8) % 2 if running else 0), lambda: self.draw_list(running, f))

        status_line = f"TODAY {fmt_hms(today)}  ·  LV {lv:02d}  ·  DISC: {DISC_TITLES[self.current_disc()].upper()}"
        self.section("status", status_line, lambda: self.cv.create_text(
            14, H - 14, text=status_line, fill=C["cyan_dim"], font=self.sans(9), anchor="w", tags=self.layer))

        self.section("fx", f if self.particles else None, self.draw_particles)
        self.hits = [h for tag in self.ORDER for h in self.sec_hits.get(tag, [])]
        r = DISC_SIZE // 2
        self.hits.insert(0, (DISC_CENTER[0] - r, DISC_CENTER[1] - r, SHUTTER_AT[0], DISC_CENTER[1] + r, self.scratch))

    def draw_label(self, time_text, caption, status, running):
        x1, y1, x2, y2 = LABEL
        cv = self.cv
        cv.create_text(x1 + 10, y1 + 16, text=status, fill=C["run"] if running else C["label_dim"],
                       font=self.sans(10), anchor="w", tags=self.layer)
        cv.create_text(x2 - 8, y1 + 54, text=time_text, fill=C["label"], font=self.sans(28), anchor="e",
                       tags=self.layer)
        spaced = " ".join(caption)   # разрядка, как «L A P I S I A»
        size = 11
        while size > 7 and tkfont.Font(family=self.sans(size)[0], size=size, weight="bold").measure(spaced) > x2 - x1 - 16:
            size -= 1
        cv.create_text(x2 - 8, y1 + 88, text=spaced, fill=C["label_dim"], font=self.sans(size), anchor="e",
                       tags=self.layer)

    def draw_buttons(self, running, f):
        cv = self.cv
        y1, y2 = BTN_Y
        acts = {"main": self.toggle, "add": lambda: (self.press("add"), self.add_task()), "del": self.delete_selected,
                "csv": self.export_csv, "top": self.toggle_top, "skin": self.switch_skin}
        for name, label, x1, x2 in BUTTONS:
            if name == "main":
                label = "■ STOP" if running else "▶ START"
            down = self.pressed.get(name, -1) >= f
            hover = self.hover == name
            if hover:   # подсветка в стиле старых меню: инверсия и мигающий курсор
                cv.create_rectangle(x1, y1, x2, y2, fill=C["ink"], outline=C["cyan"], width=2, tags=self.layer)
                cv.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=label, fill=C["cyan"], font=self.sans(11),
                               tags=self.layer)
                if (f // 5) % 2 and x2 - x1 > 60:
                    cv.create_text(x1 + 4, (y1 + y2) / 2, text="►", fill=C["cyan"], font=self.sans(8), anchor="w",
                                   tags=self.layer)
            else:       # брашированный металл, как рамка ярлыка
                def paint(img, w=x2 - x1 + 1, h=y2 - y1 + 1):
                    for i in range(h):
                        t = i / (h - 1)
                        col = pt.mix(C["silver2"], C["silver1"], t) if down else pt.mix(C["silver1"], C["silver2"], t)
                        img.put(col, to=(0, i, w, i + 1))
                    for edge in ((0, 0, w, 1), (0, h - 1, w, h), (0, 0, 1, h), (w - 1, 0, w, h)):
                        img.put(C["silver_edge"], to=edge)
                self.place(x1, y1, self.cached(("btn", x2 - x1, y2 - y1, down), x2 - x1 + 1, y2 - y1 + 1, paint))
                on = (name == "top" and self.topmost)
                cv.create_text((x1 + x2) / 2, (y1 + y2) / 2 + (1 if down else 0), text=label,
                               fill="#0a5a70" if on else C["ink"], font=self.sans(11), tags=self.layer)
            self.hits.append((x1, y1, x2, y2, acts[name]))

    def draw_list(self, running, f):
        cv = self.cv
        tasks = self.data["tasks"]
        if not tasks:
            cv.create_text(W / 2, LIST_TOP + 60, text="пусто — впиши название трека выше", fill=C["cyan_dim"],
                           font=self.sans(12, False), tags=self.layer)
        for idx in range(self.scroll, min(len(tasks), self.scroll + ROWS)):
            t = tasks[idx]
            y = LIST_TOP + (idx - self.scroll) * ROW_H
            is_sel = t["id"] == self.data["selected"]
            is_run = running and running["task_id"] == t["id"]
            if is_sel:
                cv.create_rectangle(14, y + 1, 466, y + ROW_H - 1, fill=C["sel"], outline="", tags=self.layer)
            ink = C["ink"] if is_sel else (C["run"] if is_run else C["text"])
            dim = C["ink"] if is_sel else C["cyan_dim"]
            cv.create_text(22, y + ROW_H / 2, text=f"{idx + 1:02d}", fill=dim, font=self.font(11), anchor="w",
                           tags=self.layer)
            name = t["name"] if len(t["name"]) <= 34 else t["name"][:33] + "…"
            mark = ("▶ " if (f // 8) % 2 else "▷ ") if is_run else ""
            cv.create_text(52, y + ROW_H / 2, text=mark + name, fill=ink, font=self.sans(12), anchor="w",
                           tags=self.layer)
            cv.create_text(430, y + ROW_H / 2, text=fmt_hms(self.task_total(t["id"])), fill=ink, font=self.font(11),
                           anchor="e", tags=self.layer)
            cv.create_text(452, y + ROW_H / 2, text="✕", fill=C["ink"] if is_sel else "#ff7a8a", font=self.sans(11),
                           tags=self.layer)
            tid = t["id"]
            self.hits.append((14, y, 438, y + ROW_H, lambda tid=tid: self.select(tid)))
            self.hits.append((440, y, 466, y + ROW_H, lambda tid=tid: self.delete_task(tid)))

    def draw_particles(self):
        for p in self.particles:
            if p["kind"] == "text":
                self.cv.create_text(p["x"], p["y"], text=p["text"], fill=C["cyan"], font=self.sans(16),
                                    tags=self.layer)
            elif p["kind"] in ("sparkle", "heart"):
                self.cv.create_text(p["x"], p["y"], text="✦" if p["kind"] == "sparkle" else "♥", fill=C["cyan"],
                                    font=self.sans(10), tags=self.layer)


def main():
    import task_quest  # единое приложение со скинами
    task_quest.main("md")


if __name__ == "__main__":
    main()
