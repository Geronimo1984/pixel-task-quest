"""Всплывающие окна в стиле текущего скина — вместо системных окон macOS.

Окно рисуется внутри приложения поверх скина (как выбор скина): сверху бар в стиле скина,
ниже заголовок, текст и кнопки с подсветкой в стиле старых меню. Enter — кнопка по умолчанию,
Esc и крестик в баре — отмена, ← → и Tab — переход между кнопками.

ask() возвращает значение нажатой кнопки (None — отмена) и ждёт ответа, не останавливая анимацию.
"""
import tkinter as tk
from tkinter import font as tkfont

import titlebar

WIDTH = 360
PAD = 18
BTN_H = 30


class Dialog:
    def __init__(self, root, parent_cv, skin, title, heading, text, buttons, default=0):
        """buttons — список (подпись, значение); default — индекс кнопки для Enter."""
        self.root = root
        self.buttons = buttons
        self.focus = default
        self.hover = None
        self.result = tk.StringVar(root, "")
        self.value = None
        style = titlebar.STYLES.get(skin, titlebar.MoonStyle)
        self.pal = style.picker
        family = "Menlo" if self.pal["font"] == "mono" else "Helvetica Neue"
        self.font = lambda size, bold=True: (family, size, "bold" if bold else "normal")

        self.frame = tk.Frame(parent_cv.master, bg=self.pal["border"], bd=0, highlightthickness=0)
        self.bar = titlebar.TitleBar(root, self.cancel, parent=self.frame, buttons=("close",), draggable=False)
        self.bar.cv.pack_configure(padx=2, pady=(2, 0))
        self.bar.apply(skin, WIDTH, style.dialog_title(title))

        # раскладка: заголовок, текст с переносом, ряд кнопок справа
        measure = tkfont.Font(family=family, size=12, weight="bold")
        self.btn_w = [max(84, measure.measure(label) + 28) for label, _ in buttons]
        probe = tk.Canvas(self.frame)
        tid = probe.create_text(0, 0, text=text, font=self.font(11, False), width=WIDTH - 2 * PAD, anchor="nw")
        text_h = probe.bbox(tid)[3] if text else 0
        probe.destroy()
        self.text_top = PAD + 26
        self.btn_top = self.text_top + text_h + PAD
        height = self.btn_top + BTN_H + PAD
        self.cv = tk.Canvas(self.frame, width=WIDTH, height=height, bg=self.pal["bg"], highlightthickness=0)
        self.cv.pack(padx=2, pady=(0, 2))
        self.cv.create_text(PAD, PAD + 6, text=heading, fill=self.pal["text"], font=self.font(14), anchor="w")
        self.cv.create_text(PAD, self.text_top, text=text, fill=self.pal["sub"], font=self.font(11, False),
                            width=WIDTH - 2 * PAD, anchor="nw")
        x = WIDTH - PAD
        self.slots = []
        for w in reversed(self.btn_w):
            self.slots.insert(0, (x - w, self.btn_top, x, self.btn_top + BTN_H))
            x -= w + 8
        self.draw_buttons()

        self.cv.bind("<Motion>", self.on_motion)
        self.cv.bind("<Leave>", lambda e: self.set_hover(None))
        self.cv.bind("<Button-1>", self.on_click)
        for w in (self.cv, self.bar.cv):
            w.bind("<Return>", lambda e: self.choose(self.focus))
            w.bind("<KP_Enter>", lambda e: self.choose(self.focus))
            w.bind("<Escape>", lambda e: self.cancel())
            w.bind("<Left>", lambda e: self.move(-1))
            w.bind("<Right>", lambda e: self.move(1))
            w.bind("<Tab>", lambda e: (self.move(1), "break")[1])
            w.bind("<space>", lambda e: "break")   # пробел не запускает таймер под окном
        self.frame.place(in_=parent_cv, relx=0.5, rely=0.42, anchor="center")
        self.frame.lift()
        self.cv.focus_set()

    def draw_buttons(self):
        cv, p = self.cv, self.pal
        cv.delete("btn")
        for i, ((label, _), (x1, y1, x2, y2)) in enumerate(zip(self.buttons, self.slots)):
            on = self.hover == i
            focus = self.focus == i
            # подсветка как в старых меню: под мышью — заливка, кнопка по умолчанию — яркая рамка
            cv.create_rectangle(x1, y1, x2, y2, fill=p["hover"] if on else p["bg"],
                                outline=p["hover_line"] if (on or focus) else p["border"],
                                width=2 if focus else 1, tags="btn")
            cv.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=label, fill=p["hover_text"] if on else p["text"],
                           font=self.font(12), tags="btn")
            if focus and not on:
                cv.create_text(x1 + 9, (y1 + y2) / 2, text="►", fill=p["hover_line"], font=self.font(8), tags="btn")

    def button_at(self, x, y):
        for i, (x1, y1, x2, y2) in enumerate(self.slots):
            if x1 <= x <= x2 and y1 <= y <= y2:
                return i
        return None

    def set_hover(self, i):
        if i != self.hover:
            self.hover = i
            self.draw_buttons()

    def on_motion(self, e):
        self.set_hover(self.button_at(e.x, e.y))

    def on_click(self, e):
        i = self.button_at(e.x, e.y)
        if i is not None:
            self.choose(i)

    def move(self, d):
        self.focus = (self.focus + d) % len(self.buttons)
        self.draw_buttons()

    def choose(self, i):
        self.value = self.buttons[i][1]
        self.close()

    def cancel(self):
        self.value = None
        self.close()

    def close(self):
        if self.frame.winfo_exists():
            self.frame.destroy()
        self.result.set("done")


def ask(app, title, heading, text, buttons, default=0):
    """Окно поверх скина app; возвращает значение кнопки или None. Анимация скина при этом идёт."""
    root = app.root
    skin = app.data.get("skin") or getattr(app, "SKIN", "moon")
    # клики мимо окна и пробел скину на это время не достаются
    app.cv.bind("<Button-1>", lambda e: "break")
    space = root.bind("<space>")
    root.bind("<space>", lambda e: "break")
    if hasattr(app, "overlay_changed"):
        app.overlay_changed(True)
    dlg = Dialog(root, app.cv, skin, title, heading, text, buttons, default)
    try:
        root.wait_variable(dlg.result)
    except tk.TclError:   # окно программы закрыли, пока ждали ответа
        return None
    if app.cv.winfo_exists():
        app.cv.bind("<Button-1>", app.on_click)
        root.bind("<space>", app.on_space if space else "")
        if hasattr(app, "overlay_changed"):
            app.overlay_changed(False)
    return dlg.value


def info_window(root, skin, title, heading, text):
    """Отдельное маленькое окно в стиле скина — для сообщения до запуска основного окна."""
    root.overrideredirect(True)
    root.configure(bg="#000000")
    holder = tk.Canvas(root, width=WIDTH + 4, height=1, highlightthickness=0, bd=0)
    holder.pack()
    dlg = Dialog(root, holder, skin, title, heading, text, [("OK", True)])
    dlg.frame.place_forget()
    dlg.frame.pack()
    holder.destroy()
    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    root.geometry(f"+{(root.winfo_screenwidth() - w) // 2}+{(root.winfo_screenheight() - h) // 3}")
    root.deiconify()
    root.lift()
    titlebar.mac_window_polish()
    dlg.cv.focus_force()
    root.wait_variable(dlg.result)
