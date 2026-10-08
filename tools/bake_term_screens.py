"""Готовит заставки Terminal: картинка → палитра фосфорного экрана скина, с фактурой ЭЛТ.

Яркость каждой точки (после растяжения контраста) переводится в зелёную шкалу скина
(чёрный → glow → dim → mid → bright → hot), поверх — вертикальные штрихи и строки развёртки,
как у большого таймера Terminal. Исходники лежат в tools/term_src, результат — assets/term_screens.

Запуск:  python3 tools/bake_term_screens.py
"""
import os
import subprocess
import sys
import tkinter as tk

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "tools", "term_src")
OUT = os.path.join(HERE, "assets", "term_screens")
WIDTH = 384   # ширина окна экрана Terminal (без рамки)

# шкала фосфора скина Terminal (task_quest_terminal.G): положение 0..1 → цвет
RAMP = [(0.00, "#000000"), (0.18, "#0a3d1a"), (0.42, "#11702f"), (0.66, "#1fae48"), (0.86, "#39ff6a"),
        (1.00, "#c4ffd2")]
# кадрирование источника (x, y, ширина, высота) — у «пуль» берём основной кадр без миниатюр снизу
CROP = {"bullets": (0, 0, 649, 438)}


def hex2rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


RAMP_RGB = [(p, hex2rgb(c)) for p, c in RAMP]


def ramp(v):
    for (p0, c0), (p1, c1) in zip(RAMP_RGB, RAMP_RGB[1:]):
        if v <= p1:
            t = (v - p0) / (p1 - p0)
            return tuple(round(a + (b - a) * t) for a, b in zip(c0, c1))
    return RAMP_RGB[-1][1]


def prepare(name, tmp, root):
    """Исходник → PNG нужной ширины (через sips, с кадрированием)."""
    src = os.path.join(SRC, f"{name}.jpg")
    subprocess.run(["sips", "-s", "format", "png", src, "--out", tmp], capture_output=True, check=True)
    if name in CROP:   # кадрируем сами: sips игнорирует смещение и режет из середины
        x, y, w, h = CROP[name]
        full = tk.PhotoImage(master=root, file=tmp)
        part = tk.PhotoImage(master=root, width=w, height=h)
        part.tk.call(part, "copy", full, "-from", x, y, x + w, y + h)
        part.write(tmp, format="png")
    subprocess.run(["sips", "--resampleWidth", str(WIDTH), tmp], capture_output=True, check=True)


def bake(name, root):
    tmp = os.path.join(OUT, f".{name}_src.png")
    prepare(name, tmp, root)
    src = tk.PhotoImage(master=root, file=tmp)
    w, h = src.width(), src.height()
    lum = [[0.0] * w for _ in range(h)]
    hist = []
    for y in range(h):
        for x in range(w):
            r, g, b = src.get(x, y)
            v = 0.3 * r + 0.59 * g + 0.11 * b
            lum[y][x] = v
            hist.append(v)
    hist.sort()
    lo, hi = hist[int(len(hist) * 0.02)], hist[int(len(hist) * 0.995)]   # растяжение контраста
    out = tk.PhotoImage(master=root, width=w, height=h)
    for y in range(h):
        row = []
        scan = 0.78 if y % 3 == 2 else 1.0                       # строки развёртки
        for x in range(w):
            v = max(0.0, min(1.0, (lum[y][x] - lo) / max(1.0, hi - lo)))
            v = v ** 0.85
            stroke = 0.62 if x % 3 == 2 else 1.0                  # вертикальные штрихи фосфора
            r, g, b = ramp(v * stroke * scan)
            row.append(f"#{r:02x}{g:02x}{b:02x}")
        out.put("{" + " ".join(row) + "}", to=(0, y))
    out.write(os.path.join(OUT, f"{name}.png"), format="png")
    os.remove(tmp)
    return w, h


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    root = tk.Tk()
    root.withdraw()
    for name in sys.argv[1:] or ("rain", "neo", "bullets"):
        print(name, "%d×%d" % bake(name, root))
    root.destroy()
