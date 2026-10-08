"""Готовит исходники заставок Terminal: кадрирует картинку и уменьшает её до размера окна экрана.

Сама заставка рисуется в скине из этого исходника символами (task_quest_terminal.AsciiScreen):
картинка тут не перекрашивается и кадры анимации не готовятся. Исходники — tools/term_src/*.jpg,
результат — assets/term_screens/<имя>.png.

Запуск:  python3 tools/prep_term_sources.py
"""
import os
import subprocess
import sys
import tkinter as tk

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "tools", "term_src")
OUT = os.path.join(HERE, "assets", "term_screens")
WIDTH, HEIGHT = 384, 176                       # окно экрана Terminal (без рамки)
CROP = {"bullets": (0, 0, 649, 438)}           # у «пуль» — основной кадр без миниатюр снизу
TOP = {"rain": 16, "neo": 18, "bullets": 40}   # какая часть уменьшенной картинки попадает в окно (отступ сверху)


def prepare(name, root):
    tmp = os.path.join(OUT, f".{name}.png")
    subprocess.run(["sips", "-s", "format", "png", os.path.join(SRC, f"{name}.jpg"), "--out", tmp],
                   capture_output=True, check=True)
    if name in CROP:   # кадрируем сами: sips игнорирует смещение и режет из середины
        x, y, w, h = CROP[name]
        full = tk.PhotoImage(master=root, file=tmp)
        part = tk.PhotoImage(master=root, width=w, height=h)
        part.tk.call(part, "copy", full, "-from", x, y, x + w, y + h)
        part.write(tmp, format="png")
    subprocess.run(["sips", "--resampleWidth", str(WIDTH), tmp], capture_output=True, check=True)
    img = tk.PhotoImage(master=root, file=tmp)
    top = min(TOP.get(name, 0), max(0, img.height() - HEIGHT))
    out = tk.PhotoImage(master=root, width=WIDTH, height=HEIGHT)
    out.tk.call(out, "copy", img, "-from", 0, top, WIDTH, top + HEIGHT)
    out.write(os.path.join(OUT, f"{name}.png"), format="png")
    os.remove(tmp)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    root = tk.Tk()
    root.withdraw()
    for name in sys.argv[1:] or ("rain", "neo", "bullets"):
        prepare(name, root)
        print(name, "→ assets/term_screens/%s.png" % name)
    root.destroy()
