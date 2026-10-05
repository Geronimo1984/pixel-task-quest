"""Карточка задачи для канбана: название, статус, время и комментарий — окно поверх скина в его стиле.

Открывается двойным кликом по карточке (или по значку ✎). Сохранить — Enter (или кнопка),
новая строка в комментарии — Shift+Enter, отмена — Esc или крестик в баре. Пока карточка открыта, клики мимо неё скину не достаются.
"""
import tkinter as tk

import dictation
import titlebar
from pixel_tracker import fmt_hms

WIDTH = 392
PAD = 16


class TaskDetails:
    def __init__(self, app, task, statuses, on_save, skin="moon"):
        """statuses — список (ключ, подпись, цвет); on_save(task_id, name, status, comment)."""
        self.app, self.task, self.statuses, self.on_save = app, task, statuses, on_save
        root = app.root
        style = titlebar.STYLES.get(skin, titlebar.MoonStyle)
        p = self.pal = style.picker
        family = "Menlo" if p["font"] == "mono" else "Tahoma"
        self.font = lambda size, bold=True: (family, size, "bold" if bold else "normal")
        self.status = task.get("status") or statuses[0][0]
        self.hover = None

        self.frame = tk.Frame(root, bg=p["border"], bd=0, highlightthickness=0)
        self.bar = titlebar.TitleBar(root, self.cancel, parent=self.frame, buttons=("close",), draggable=False)
        self.bar.cv.pack_configure(padx=2, pady=(2, 0))
        self.bar.apply(skin, WIDTH, style.dialog_title("QUEST CARD"))
        h = 372
        cv = self.cv = tk.Canvas(self.frame, width=WIDTH, height=h, bg=p["bg"], highlightthickness=0)
        cv.pack(padx=2, pady=(0, 2))

        # название
        cv.create_text(PAD, 16, text="Название", fill=p["sub"], font=self.font(10), anchor="w")
        self.name = tk.Entry(cv, font=self.font(13), bg="#ffffff", fg="#26306e", relief="flat",
                             insertbackground=p["hover_line"], highlightthickness=2,
                             highlightbackground=p["border"], highlightcolor=p["hover_line"])
        self.name.insert(0, task["name"])
        cv.create_window(PAD, 28, anchor="nw", window=self.name, width=WIDTH - 2 * PAD, height=30)

        # статус — три переключателя
        cv.create_text(PAD, 76, text="Статус", fill=p["sub"], font=self.font(10), anchor="w")
        gap = 8
        bw = (WIDTH - 2 * PAD - gap * (len(statuses) - 1)) / len(statuses)
        self.status_slots = [(key, PAD + i * (bw + gap), 88, PAD + i * (bw + gap) + bw, 116)
                             for i, (key, _, _) in enumerate(statuses)]

        # время
        total = app.task_total(task["id"])
        today = app.task_today(task["id"]) if hasattr(app, "task_today") else 0
        cv.create_text(PAD, 138, text=f"Время: всего {fmt_hms(total)} · сегодня {fmt_hms(today)}",
                       fill=p["text"], font=self.font(11), anchor="w")

        # комментарий
        cv.create_text(PAD, 164, text="Комментарий", fill=p["sub"], font=self.font(10), anchor="w")
        cv.create_text(WIDTH - PAD, 164, text="↩ сохранить · ⇧↩ строка", fill=p["sub"],
                       font=self.font(9, False), anchor="e")
        # голосовой ввод комментария (диктовка macOS) — кнопка рядом с подписью, ⌘D
        self.listening = False
        self.mic = (PAD + 92, 154, PAD + 196, 174) if dictation.AVAILABLE else None
        self.comment = tk.Text(cv, font=self.font(12, False), bg="#ffffff", fg="#26306e", relief="flat", wrap="word",
                               insertbackground=p["hover_line"], highlightthickness=2, padx=6, pady=4,
                               highlightbackground=p["border"], highlightcolor=p["hover_line"], undo=True)
        self.comment.insert("1.0", task.get("comment", ""))
        cv.create_window(PAD, 176, anchor="nw", window=self.comment, width=WIDTH - 2 * PAD, height=136)

        # кнопки
        self.btns = [("delete", "Удалить", PAD, 326, PAD + 96, 356),
                     ("save", "Сохранить", WIDTH - PAD - 230, 326, WIDTH - PAD - 120, 356),
                     ("cancel", "Отмена", WIDTH - PAD - 110, 326, WIDTH - PAD, 356)]
        self.draw_controls()

        cv.bind("<Motion>", self.on_motion)
        cv.bind("<Leave>", lambda e: self.set_hover(None))
        cv.bind("<Button-1>", self.on_click)
        for w in (cv, self.bar.cv, self.name, self.comment):
            w.bind("<Escape>", lambda e: self.cancel())
            w.bind("<Command-Return>", lambda e: (self.save(), "break")[1])
            w.bind("<Control-Return>", lambda e: (self.save(), "break")[1])
        for w in (cv, self.bar.cv, self.name, self.comment):
            w.bind("<Return>", lambda e: (self.save(), "break")[1])
            w.bind("<KP_Enter>", lambda e: (self.save(), "break")[1])
        # новая строка в комментарии — Shift+Enter (или ⌥+Enter)
        self.comment.bind("<Shift-Return>", lambda e: (self.comment.insert("insert", "\n"), "break")[1])
        self.comment.bind("<Option-Return>", lambda e: (self.comment.insert("insert", "\n"), "break")[1])
        cv.bind("<space>", lambda e: "break")
        # ввод с клавиатуры всегда возвращается в поле: щелчок по нему подтверждает «черновик» диктовки
        for w in (self.name, self.comment):
            w.bind("<Button-1>", self.ensure_input, add="+")
        for w in (cv, self.bar.cv, self.name, self.comment):
            w.bind("<Command-d>", lambda e: (self.toggle_mic(), "break")[1])

        # клики мимо карточки скину не достаются
        app.cv.bind("<Button-1>", lambda e: "break")
        self.frame.place(in_=app.cv, relx=0.5, rely=0.5, anchor="center")
        self.frame.lift()
        self.draw_mic()
        self.commit_draft()
        self.draft_seen = None
        self.frame.after(700, self.watch_draft)
        self.comment.focus_force()
        self.comment.mark_set("insert", "end")

    def draw_controls(self):
        cv, p = self.cv, self.pal
        cv.delete("ctl")
        for (key, label, color), (_, x1, y1, x2, y2) in zip(self.statuses, self.status_slots):
            on = self.status == key
            hov = self.hover == ("st", key)
            cv.create_rectangle(x1, y1, x2, y2, fill=color if on else (p["hover"] if hov else p["bg"]),
                                outline=color if (on or hov) else p["border"], width=2, tags="ctl")
            cv.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=("✓ " if on else "") + label,
                           fill="#ffffff" if on else p["text"], font=self.font(11), tags="ctl")
        for key, label, x1, y1, x2, y2 in self.btns:
            hov = self.hover == ("btn", key)
            default = key == "save"
            cv.create_rectangle(x1, y1, x2, y2, fill=p["hover"] if hov else p["bg"],
                                outline=p["hover_line"] if (hov or default) else p["border"],
                                width=2 if default else 1, tags="ctl")
            ink = p.get("danger", "#ff6f8f") if key == "delete" and not hov else (p["hover_text"] if hov else p["text"])
            cv.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=label, fill=ink, font=self.font(12), tags="ctl")

    def draw_mic(self):
        if not self.mic:
            return
        cv, p = self.cv, self.pal
        cv.delete("mic")
        x1, y1, x2, y2 = self.mic
        hov = self.hover == ("btn", "mic")
        rec = "#ff3b5c"
        if self.listening:   # идёт диктовка: красная рамка и мигающая точка
            blink = getattr(self, "mic_blink", 0)
            cv.create_rectangle(x1, y1, x2, y2, fill=p["bg"], outline=rec, width=2, tags="mic")
            cv.create_oval(x1 + 7, y1 + 6, x1 + 15, y1 + 14, fill=rec if blink else p["bg"], outline=rec, tags="mic")
            cv.create_text(x1 + 21, (y1 + y2) / 2, text="Слушаю… стоп", fill=rec, font=self.font(9), anchor="w",
                           tags="mic")
        else:
            cv.create_rectangle(x1, y1, x2, y2, fill=p["hover"] if hov else p["bg"],
                                outline=p["hover_line"] if hov else p["border"], tags="mic")
            cv.create_oval(x1 + 7, y1 + 6, x1 + 15, y1 + 14, fill=rec, outline="", tags="mic")
            cv.create_text(x1 + 21, (y1 + y2) / 2, text="Голосом", fill=p["hover_text"] if hov else p["text"],
                           font=self.font(9), anchor="w", tags="mic")

    def watch_draft(self):
        """Сторож: если черновик диктовки завис (диктовку выключили не нашей кнопкой или она оборвалась),
        через 3 секунды без изменений подтверждаем его — иначе клавиатура не печатает в поле."""
        if not self.frame.winfo_exists():
            return
        if not self.listening and dictation.has_draft():
            snapshot = self.comment.get("1.0", "end-1c")
            if self.draft_seen and self.draft_seen[0] == snapshot:
                if self.frame.tk.call("clock", "milliseconds") - self.draft_seen[1] > 3000:
                    self.commit_draft()
                    self.draft_seen = None
            else:
                self.draft_seen = (snapshot, self.frame.tk.call("clock", "milliseconds"))
        else:
            self.draft_seen = None
        self.frame.after(700, self.watch_draft)

    def ensure_input(self, _e=None):
        if not self.listening:
            self.commit_draft()

    def commit_draft(self):
        """Подтверждает «черновик» диктовки: надиктованное остаётся в поле обычным текстом,
        а клавиатура снова печатает в поле (иначе нажатия съедаются).

        Tk помечает черновик тегом IMEmarkedtext и при сбросе удаляет помеченное — снимаем метку заранее,
        а для поля названия (Entry) возвращаем текст, если Tk его всё-таки убрал."""
        name_before = self.name.get()
        self.comment.tag_remove("IMEmarkedtext", "1.0", "end")
        dictation.reset_input()

        def restore():
            if self.frame.winfo_exists() and self.name.get() != name_before:
                self.name.delete(0, "end")
                self.name.insert(0, name_before)
        self.frame.after_idle(restore)

    def toggle_mic(self):
        if not self.mic:
            return
        if self.listening:
            dictation.stop_only()
            self.listening = False
            self.commit_draft()
        else:
            self.listening = dictation.start(self.comment)
            if self.listening:
                self.blink_mic()
            else:
                self.app.show_toast("Диктовка недоступна — включи её в настройках macOS", 40)
        self.draw_mic()

    def blink_mic(self):
        if not self.listening or not self.frame.winfo_exists():
            return
        self.mic_blink = 1 - getattr(self, "mic_blink", 0)
        self.draw_mic()
        self.frame.after(450, self.blink_mic)

    def target(self, x, y):
        if self.mic and self.mic[0] <= x <= self.mic[2] and self.mic[1] <= y <= self.mic[3]:
            return ("btn", "mic")
        for key, x1, y1, x2, y2 in self.status_slots:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return ("st", key)
        for key, _, x1, y1, x2, y2 in self.btns:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return ("btn", key)
        return None

    def set_hover(self, t):
        if t != self.hover:
            self.hover = t
            self.draw_controls()
            self.draw_mic()

    def on_motion(self, e):
        self.set_hover(self.target(e.x, e.y))

    def on_click(self, e):
        t = self.target(e.x, e.y)
        if not t:
            return
        kind, key = t
        if kind == "st":
            self.status = key
            self.draw_controls()
        elif key == "mic":
            self.toggle_mic()
        elif key == "save":
            self.save()
        elif key == "delete":
            self.close()
            self.app.delete_task(self.task["id"])   # спросит подтверждение в стиле скина
        else:
            self.cancel()

    def save(self):
        if self.listening:   # сохраняем во время диктовки — сначала остановить и подтвердить надиктованное
            dictation.stop_only()
            self.listening = False
        self.commit_draft()
        name = self.name.get().strip() or self.task["name"]
        comment = self.comment.get("1.0", "end").rstrip()
        self.close()
        self.on_save(self.task["id"], name, self.status, comment)

    def cancel(self):
        self.close()

    def close(self):
        if self.listening:
            dictation.stop_only()
            self.listening = False
        app = self.app
        if app.cv.winfo_exists():
            app.cv.bind("<Button-1>", app.on_click)
            app.cv.focus_set()
        if self.frame.winfo_exists():
            self.frame.destroy()
        if getattr(app, "details", None) is self:
            app.details = None
            if hasattr(app, "details_closed"):
                app.details_closed()
