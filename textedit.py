"""Копирование и вставка в полях ввода — в любой раскладке и через меню правой кнопки.

В Tk сочетания ⌘C / ⌘V / ⌘X / ⌘A / ⌘Z привязаны к латинским клавишам: при русской раскладке та же
клавиша даёт «с», «м», «ч», «ф», «я», и Tk сочетание не узнаёт — копирование молча не работает.
Добавляем к стандартным событиям Tk их русские варианты и контекстное меню для всех Entry и Text.
"""
import tkinter as tk

# клавиша на месте латинской буквы в русской раскладке (ЙЦУКЕН)
CYRILLIC = {"<<Copy>>": "Cyrillic_es", "<<Paste>>": "Cyrillic_em", "<<Cut>>": "Cyrillic_che",
            "<<SelectAll>>": "Cyrillic_ef", "<<Undo>>": "Cyrillic_ya"}
MENU = [("Вырезать", "<<Cut>>"), ("Копировать", "<<Copy>>"), ("Вставить", "<<Paste>>"), (None, None),
        ("Выделить всё", "<<SelectAll>>")]


def install(root):
    for event, keysym in CYRILLIC.items():
        for sequence in (f"<Command-{keysym}>", f"<Command-Shift-{keysym}>"):
            try:
                root.event_add(event, sequence)
            except tk.TclError:
                pass
    # у Entry нет «Выделить всё» по ⌘A — добавляем, как в Text
    root.bind_class("Entry", "<<SelectAll>>", lambda e: (e.widget.select_range(0, "end"),
                                                         e.widget.icursor("end"), "break")[2])
    menu = tk.Menu(root, tearoff=0)

    def popup(e):
        w = e.widget
        w.focus_set()
        menu.delete(0, "end")
        for label, event in MENU:
            if label is None:
                menu.add_separator()
            else:
                menu.add_command(label=label, command=lambda ev=event: w.event_generate(ev))
        menu.tk_popup(e.x_root, e.y_root)
        return "break"

    for cls in ("Entry", "Text"):
        root.bind_class(cls, "<Button-2>", popup, add="+")          # правая кнопка мыши на macOS
        root.bind_class(cls, "<Control-Button-1>", popup, add="+")  # ⌃-щелчок
