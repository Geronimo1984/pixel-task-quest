"""Режим «Канбан» для всех скинов: колонки статусов, карточки, перетаскивание и карточка задачи.

Скин подмешивает KanbanMixin (class AppX(KanbanMixin, tq.App2)) и задаёт:
  KB_AREA  — область колонок (x1, y1, x2, y2);
  KB_TABS  — вкладки «Список / Канбан»: (правый край, y1, y2, ширина вкладки);
  KB_SKIN  — ключ скина (для стиля карточки задачи);
  kb_theme() — цвета и шрифт (см. THEME_KEYS).
В redraw скин рисует вкладки (draw_view_tabs) и, если включён канбан (kb_on()), — draw_kanban вместо списка.
"""
import os
import tkinter as tk
from tkinter import font as tkfont

from pixel_tracker import fmt_hms, mix

STATUSES = [("todo", "ЗАДАЧИ"), ("doing", "В РАБОТЕ"), ("done", "ГОТОВО")]
VIEW_KEY = "task_view"   # общий для всех скинов режим: "list" или "kanban"

THEME_KEYS = ("cols", "col_bg", "tint", "head_text", "card_bg", "card_line", "text", "dim", "run", "mark_off",
              "tab_on_bg", "tab_on_line", "tab_on_text", "tab_off_bg", "tab_off_line", "tab_off_text", "font",
              "tab_labels")


class KanbanMixin:
    KB_GAP, KB_HEAD, KB_CARD, KB_STEP = 6, 20, 36, 40

    # ── состояние ─────────────────────────────────────────────────────────
    def kb_init(self):
        self.kb_scroll = {key: 0 for key, _ in STATUSES}
        self.kb_cards = []
        self.kb_drag = None
        self.details = None
        if VIEW_KEY not in self.data and "moon_view" in self.data:   # режим из первой версии (только Moon)
            self.data[VIEW_KEY] = self.data["moon_view"]
        self.cv.bind("<B1-Motion>", self.kb_motion)
        self.cv.bind("<ButtonRelease-1>", self.kb_release)
        self.cv.bind("<Double-Button-1>", self.kb_double)

    def kb_on(self):
        return self.data.get(VIEW_KEY) == "kanban"

    def status_of(self, t):
        r = self.data["running"]
        return t.get("status") or ("doing" if r and r["task_id"] == t["id"] else "todo")

    def set_view(self, view):
        self.data[VIEW_KEY] = view
        self.kb_drag = None
        self.cv.delete("kbghost")
        self.save()

    # ── рисование ─────────────────────────────────────────────────────────
    def kb_text(self, x, y, s, color, size, bold=True, anchor="w"):
        self.cv.create_text(x, y, text=s, fill=color, font=self.kb_theme()["font"](size, bold), anchor=anchor,
                            tags=self.layer)

    def draw_view_tabs(self):
        th = self.kb_theme()
        right, y1, y2, tw = self.KB_TABS
        kanban = self.kb_on()
        for i, (view, label) in enumerate(zip(("list", "kanban"), th["tab_labels"])):
            x2 = right - (1 - i) * (tw + 4)
            x1 = x2 - tw
            on = (view == "kanban") == kanban
            self.rect(x1, y1, x2, y2, th["tab_on_line"] if on else th["tab_off_line"])
            self.rect(x1 + 1, y1 + 1, x2 - 1, y2 - 1, th["tab_on_bg"] if on else th["tab_off_bg"])
            self.kb_text((x1 + x2) / 2, (y1 + y2) / 2, label, th["tab_on_text"] if on else th["tab_off_text"], 10,
                         anchor="center")
            self.hits.append((x1, y1, x2, y2, lambda view=view: self.set_view(view)))

    def kb_columns(self):
        x1, y1, x2, y2 = self.KB_AREA
        w = (x2 - x1 - self.KB_GAP * (len(STATUSES) - 1)) / len(STATUSES)
        cols = self.kb_theme()["cols"]
        return [(key, label, cols[key], x1 + i * (w + self.KB_GAP), y1, x1 + i * (w + self.KB_GAP) + w, y2)
                for i, (key, label) in enumerate(STATUSES)]

    def kb_visible(self):
        return max(1, int((self.KB_AREA[3] - self.KB_AREA[1] - self.KB_HEAD - 4) // self.KB_STEP))

    def kb_state(self, running, f):
        """Всё, от чего зависит вид канбана, — скины с кэшем частей перерисовывают его только при изменениях."""
        tasks = tuple((t["id"], t["name"], self.status_of(t), int(self.task_total(t["id"])),
                       t["id"] == self.data["selected"], bool(running and running["task_id"] == t["id"]),
                       bool(t.get("comment", "").strip())) for t in self.data["tasks"])
        drag = (self.kb_drag["id"], self.kb_drag.get("over")) if self.kb_drag and self.kb_drag.get("active") else None
        return tasks, tuple(self.kb_scroll.values()), drag, (f // 4) % 3 if running else 0

    def draw_kanban(self, running, f):
        th = self.kb_theme()
        tasks = self.data["tasks"]
        self.kb_cards = []
        drag_id = self.kb_drag["id"] if self.kb_drag and self.kb_drag.get("active") else None
        hover_col = self.kb_drag.get("over") if drag_id else None
        vis = self.kb_visible()
        for key, label, color, x1, y1, x2, y2 in self.kb_columns():
            col_tasks = [t for t in tasks if self.status_of(t) == key]
            self.rect(x1, y1, x2, y2, mix(color, th["col_bg"], th["tint"] - (0.1 if hover_col == key else 0)))
            self.rect(x1, y1, x2, y1 + self.KB_HEAD, color)
            self.kb_text((x1 + x2) / 2, y1 + self.KB_HEAD / 2, f"{label} · {len(col_tasks)}", th["head_text"], 9,
                         anchor="center")
            top = self.kb_scroll[key] = max(0, min(self.kb_scroll[key], len(col_tasks) - vis))
            for n, t in enumerate(col_tasks[top:top + vis]):
                cy = y1 + self.KB_HEAD + 4 + n * self.KB_STEP
                self.draw_card(t, x1 + 3, cy, x2 - 3, cy + self.KB_CARD, color, running, f, ghost=t["id"] == drag_id)
            if len(col_tasks) > vis:   # тонкая полоса прокрутки колонки
                bar = y2 - y1 - self.KB_HEAD - 4
                knob = max(12, bar * vis / len(col_tasks))
                pos = (bar - knob) * top / (len(col_tasks) - vis)
                self.rect(x2 - 3, y1 + self.KB_HEAD + 2 + pos, x2 - 1, y1 + self.KB_HEAD + 2 + pos + knob, color)
            if not tasks and key == "todo":
                self.kb_text((x1 + x2) / 2, (y1 + y2) / 2, "добавь квест ↑", th["dim"], 10, anchor="center")

    def draw_card(self, t, x1, y1, x2, y2, color, running, f, ghost=False):
        th = self.kb_theme()
        is_run = running and running["task_id"] == t["id"]
        is_sel = t["id"] == self.data["selected"]
        if ghost:   # карточку тащат — на месте остаётся пунктирный контур
            self.cv.create_rectangle(x1, y1, x2, y2, outline=color, dash=(3, 2), tags=self.layer)
            return
        k = 3 if is_run else (2 if is_sel else 1)
        # текущая задача: толстая пульсирующая рамка цвета «идёт»
        line = (th["run"] if (f // 4) % 2 else color) if is_run else (color if is_sel else th["card_line"])
        self.rect(x1, y1, x2, y2, line)
        self.rect(x1 + k, y1 + k, x2 - k, y2 - k, th["card_bg"])
        self.rect(x1, y1, x1 + 3, y2, color)   # цветная кромка статуса
        name = self.fit_text(t["name"], x2 - x1 - 22, 10)
        self.kb_text(x1 + 8, y1 + 11, name, th["run"] if is_run else th["text"], 10)
        self.kb_text(x1 + 8, y1 + 26, fmt_hms(self.task_total(t["id"])), th["run"] if is_run else th["dim"], 9)
        if is_run:
            self.kb_run_mark(x2 - 19, y1 + 26, f)
        has_comment = bool(t.get("comment", "").strip())
        self.kb_text(x2 - 10, y1 + 26, "✎", color if has_comment else th["mark_off"], 11, anchor="center")
        tid = t["id"]
        self.kb_cards.append((x1, y1, x2, y2, tid))
        self.hits.append((x1, y1, x2, y2, lambda tid=tid: self.kb_press(tid)))
        self.hits.append((x2 - 18, y1 + 18, x2, y2, lambda tid=tid: self.open_details(tid)))

    def kb_run_mark(self, x, y, f):
        """Отметка идущего квеста: крупная мигающая точка (Moon — крупное сердечко).
        x — правый край отметки, y — середина строки времени."""
        th = self.kb_theme()
        self.kb_text(x - 9, y - 1, "●", th["run"] if (f // 4) % 2 else th["dim"], 17, anchor="center")

    def fit_text(self, text, width, size):
        fonts = self.__dict__.setdefault("_kb_fonts", {})
        if size not in fonts:
            fonts[size] = tkfont.Font(font=self.kb_theme()["font"](size, True))
        font = fonts[size]
        if font.measure(text) <= width:
            return text
        while text and font.measure(text + "…") > width:
            text = text[:-1]
        return text.rstrip() + "…"

    # ── мышь: выбор, перетаскивание, двойной клик ────────────────────────
    def kb_press(self, tid):
        """Нажатие на карточку: если её не потащат, по отпусканию она выбирается (как клик в списке)."""
        x, y = getattr(self, "kb_press_xy", (0, 0))   # точка нажатия из самого события, а не где мышь сейчас
        self.kb_drag = {"id": tid, "x0": x, "y0": y, "active": False}

    def on_click(self, e):
        self.kb_press_xy = (e.x, e.y)
        super().on_click(e)

    def kb_column_at(self, x, y):
        for key, _, _, x1, y1, x2, y2 in self.kb_columns():
            if x1 - self.KB_GAP / 2 <= x <= x2 + self.KB_GAP / 2 and y1 - 30 <= y <= y2 + 30:
                return key
        return None

    def kb_motion(self, e):
        d = self.kb_drag
        if not d or not self.kb_on():
            return
        th = self.kb_theme()
        if not d["active"]:
            if abs(e.x - d["x0"]) + abs(e.y - d["y0"]) < 6:
                return
            d["active"] = True
            t = self.task(d["id"])
            col = th["cols"][self.status_of(t)]
            w = (self.KB_AREA[2] - self.KB_AREA[0]) / 3 - 10
            # «призрак» карточки следует за мышью сразу, не дожидаясь кадра
            self.cv.create_rectangle(0, 0, w, self.KB_CARD, fill=th["card_bg"], outline=col, width=2,
                                     tags=("kbghost", "kbg_box"))
            self.cv.create_rectangle(0, 0, 3, self.KB_CARD, fill=col, outline="", tags=("kbghost", "kbg_edge"))
            self.cv.create_text(8, self.KB_CARD / 2, text=self.fit_text(t["name"], w - 14, 10), fill=th["text"],
                                font=th["font"](10, True), anchor="w", tags=("kbghost", "kbg_text"))
            d["w"] = w
        w = d["w"]
        x, y = e.x - w / 2, e.y - self.KB_CARD / 2
        self.cv.coords("kbg_box", x, y, x + w, y + self.KB_CARD)
        self.cv.coords("kbg_edge", x, y, x + 3, y + self.KB_CARD)
        self.cv.coords("kbg_text", x + 8, y + self.KB_CARD / 2)
        self.cv.tag_raise("kbghost")
        d["over"] = self.kb_column_at(e.x, e.y)

    def kb_release(self, e):
        d, self.kb_drag = self.kb_drag, None
        self.cv.delete("kbghost")
        if d and d.get("active"):
            target = self.kb_column_at(e.x, e.y)
            if target:
                self.set_status(d["id"], target)
        elif d and d["id"] != self.data["selected"]:
            self.select(d["id"])   # простой клик — выбрать квест (во время работы таймер переключится на него)

    def kb_double(self, e):
        if not self.kb_on():
            return
        for x1, y1, x2, y2, tid in self.kb_cards:
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                self.open_details(tid)
                return

    def tick(self):
        r = self.data["running"]
        if r:   # счёт времени по задаче, которая уже «Готово», не идёт — таймер останавливается сам
            t = self.task(r["task_id"])
            if t and t.get("status") == "done":
                self.stop()
                self.show_toast(f"Готово: {t['name'][:22]} — таймер остановлен", 30)
        super().tick()
        if self.kb_drag and self.kb_drag.get("active"):
            self.cv.tag_raise("kbghost")   # призрак всегда поверх свежего кадра
        if self.cv.find_withtag("doneanim"):
            self.cv.tag_raise("doneanim")

    def on_wheel(self, e):
        x1, y1, x2, y2 = self.KB_AREA
        if self.kb_on() and y1 <= e.y <= y2:
            key = self.kb_column_at(e.x, e.y)
            if key and e.delta:
                self.kb_scroll[key] += -1 if e.delta > 0 else 1
            return
        super().on_wheel(e)

    # ── статусы и таймер ──────────────────────────────────────────────────
    def set_status(self, tid, status):
        t = self.task(tid)
        if not t or self.status_of(t) == status:
            return
        t["status"] = status
        r = self.data["running"]
        if status == "done":
            if r and r["task_id"] == tid:
                self.stop()   # готово — таймер останавливается, время сохраняется
            self.kb_done_fx()
            self.play_done_anim()   # анимация «Готово» в правом нижнем углу
            self.show_toast(f"Готово: {t['name'][:22]} ★", 30)
        else:
            self.show_toast(f"{dict(STATUSES)[status].capitalize()}: {t['name'][:22]}", 22)
        self.save()

    # ── анимация «Готово»: диск Kirby Air Ride в правом нижнем углу (assets/done_kirby, 30 кадров по 100 мс) ──
    DONE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "done_kirby")
    DONE_MS = 100

    def done_frames(self):
        """Кадры загружаются один раз на окно (картинки Tk живут вместе со своим окном)."""
        frames = getattr(self.root, "_done_frames", None)
        if frames is None:
            frames = []
            i = 0
            while os.path.exists(os.path.join(self.DONE_DIR, f"{i}.png")):
                frames.append(tk.PhotoImage(master=self.root, file=os.path.join(self.DONE_DIR, f"{i}.png")))
                i += 1
            self.root._done_frames = frames
        return frames

    def play_done_anim(self):
        """Проигрывает анимацию один раз поверх скина; повторное «Готово» начинает её заново."""
        try:
            frames = self.done_frames()
        except tk.TclError:
            return
        if not frames:
            return
        if getattr(self, "_done_after", None):
            self.root.after_cancel(self._done_after)
        self.cv.delete("doneanim")
        w, h = frames[0].width(), frames[0].height()
        x = int(self.cv["width"]) - w - 6
        y = int(self.cv["height"]) - h - 6
        item = self.cv.create_image(x, y, image=frames[0], anchor="nw", tags="doneanim")

        def step(k=1):
            self._done_after = None
            if not self.cv.winfo_exists():
                return
            if k >= len(frames):
                self.cv.delete("doneanim")
                return
            self.cv.itemconfigure(item, image=frames[k])
            self.cv.tag_raise("doneanim")   # поверх свежего кадра скина
            self._done_after = self.root.after(self.DONE_MS, lambda: step(k + 1))
        self.cv.tag_raise("doneanim")
        self._done_after = self.root.after(self.DONE_MS, step)

    def kb_done_fx(self):
        x1, y1, x2, y2 = self.KB_AREA
        self.burst("sparkle", x2 - 60, (y1 + y2) / 2, 10)

    def start(self):
        super().start()
        r = self.data["running"]
        t = self.task(r["task_id"]) if r else None
        if t and self.status_of(t) != "doing":
            t["status"] = "doing"   # взяли в работу — карточка переезжает в «В работе»
            self.save()

    # ── карточка задачи ───────────────────────────────────────────────────
    def open_details(self, tid):
        t = self.task(tid)
        if not t or self.details:
            return
        self.kb_drag = None
        import task_details
        cols = self.kb_theme()["cols"]
        statuses = [(key, label, cols[key]) for key, label in STATUSES]
        if hasattr(self, "overlay_changed"):
            self.overlay_changed(True)
        self.details = task_details.TaskDetails(self, t, statuses, self.save_details, skin=self.KB_SKIN)

    def save_details(self, tid, name, status, comment, new_total=None):
        t = self.task(tid)
        if not t:
            return
        changed = (name, comment, status) != (t["name"], t.get("comment", ""), self.status_of(t))
        t["name"], t["comment"] = name, comment
        if new_total is not None:
            self.set_task_total(tid, new_total)
            changed = True
        self.save()
        if status != self.status_of(t):
            self.set_status(tid, status)   # «Готово» — с остановкой таймера и своим оповещением
        else:
            self.show_toast("Изменения сохранены ✓" if changed else "Без изменений", 22)

    def details_closed(self):
        if hasattr(self, "overlay_changed"):
            self.overlay_changed(False)

    def teardown(self):
        if getattr(self, "_done_after", None):
            self.root.after_cancel(self._done_after)
            self._done_after = None
        if self.details:
            self.details.close()
        super().teardown()


def done_prefix(app, t):
    """В режиме списка у готовых квестов — галочка перед названием."""
    return "✓ " if hasattr(app, "status_of") and app.status_of(t) == "done" else ""

