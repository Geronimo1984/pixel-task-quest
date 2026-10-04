"""Своя панель заголовка окна вместо стандартной macOS — в стиле каждого скина.

Окно без системной рамки (overrideredirect): клавиатура и клики работают как обычно,
а панель рисуется один раз при смене скина. В каждом кадре она не перерисовывается,
только кнопки при наведении, поэтому на скорость не влияет.

Кнопки: закрыть (как крестик окна) и свернуть (прячет приложение, вернуть — кликом по иконке в Dock).
Панель перетаскивается мышью за любое место, кроме кнопок.
"""
import ctypes
import ctypes.util
import tkinter as tk

import task_quest_2000 as tq
from pixel_tracker import mix

# ── доступ к Cocoa (тень окна, «свернуть» = скрыть приложение) ─────────────
try:
    _objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
    _objc.objc_getClass.restype = ctypes.c_void_p
    _objc.objc_getClass.argtypes = [ctypes.c_char_p]
    _objc.sel_registerName.restype = ctypes.c_void_p
    _objc.sel_registerName.argtypes = [ctypes.c_char_p]
except (OSError, TypeError):
    _objc = None


def _send(obj, sel, restype=ctypes.c_void_p, argtypes=(), *args):
    fn = ctypes.cast(_objc.objc_msgSend, ctypes.CFUNCTYPE(restype, ctypes.c_void_p, ctypes.c_void_p, *argtypes))
    return fn(obj, _objc.sel_registerName(sel), *args)


def _nsapp():
    return _send(_objc.objc_getClass(b"NSApplication"), b"sharedApplication")


def mac_window_polish():
    """Окну без рамки возвращаем системную тень и делаем приложение активным."""
    if not _objc:
        return
    try:
        app = _nsapp()
        wins = _send(app, b"windows")
        for i in range(_send(wins, b"count", ctypes.c_ulong)):
            w = _send(wins, b"objectAtIndex:", ctypes.c_void_p, (ctypes.c_ulong,), i)
            _send(w, b"setHasShadow:", None, (ctypes.c_bool,), True)
        _send(app, b"activateIgnoringOtherApps:", None, (ctypes.c_bool,), True)
    except (AttributeError, OSError, ValueError):
        pass


def mac_native_drag():
    """Перетаскивание окна силами macOS: окно двигает оконный сервер, плавно и без нагрузки на Tk.

    Вызывается из обработчика нажатия кнопки мыши; возвращает False, если не получилось."""
    if not _objc:
        return False
    try:
        event = _send(_nsapp(), b"currentEvent")
        window = _send(event, b"window") if event else None
        # 1 — нажатие, 6 — движение с нажатой кнопкой (если скин был занят кадром, нажатие уже позади)
        if not window or _send(event, b"type", ctypes.c_ulong) not in (1, 6):
            return False
        _send(window, b"performWindowDragWithEvent:", None, (ctypes.c_void_p,), event)
        return True
    except (AttributeError, OSError, ValueError):
        return False


def mac_hide_app(root):
    """«Свернуть»: окно без рамки нельзя убрать в Dock, поэтому прячем приложение целиком (как ⌘H)."""
    if _objc:
        try:
            _send(_nsapp(), b"hide:", None, (ctypes.c_void_p,), None)
            return
        except (AttributeError, OSError, ValueError):
            pass
    root.withdraw()


# ── стили панелей ──────────────────────────────────────────────────────────
class Style:
    # окно выбора скина: заголовок, фон, строка под мышью, текст, подпись, галочка, шрифт
    picker = {"title": "SKINS", "bg": "#16162e", "hover": "#2a2b5a", "hover_line": "#6f74d8", "text": "#ffffff",
              "sub": "#b4b7e6", "hover_text": "#ffffff", "hover_sub": "#b4b7e6", "check": "#7dffb0",
              "border": "#6f74d8", "font": "sans"}
    height = 28
    bg = "#000000"
    buttons_left = True     # кнопки слева, как у macOS, или справа, как у Windows/DOS
    button_w = 18

    def __init__(self, bar):
        self.bar = bar

    def background(self, w, title):
        pass

    @staticmethod
    def dialog_title(title):
        """Заголовок всплывающего окна на баре (пиксельный шрифт — латиница)."""
        return title

    def button(self, name, x1, y1, x2, y2, hover, down):
        pass


class MoonStyle(Style):
    """Индиго с розовой рамкой, пиксельные звёздочки и круглые кнопки-«конфеты»."""
    height = 28
    bg = "#2f2180"
    picker = {"title": "SKINS", "bg": "#221f62", "hover": "#3a2f8f", "hover_line": "#ff7fcf", "text": "#ffffff",
              "sub": "#c9bfff", "hover_text": "#ffffff", "hover_sub": "#ffd6f0", "check": "#3fe8ac",
              "border": "#ff7fcf", "font": "sans"}

    def background(self, w, title):
        b = self.bar
        for i in range(self.height):
            b.rect(0, i, w, i + 1, mix("#4a34ac", "#2f2180", i / (self.height - 1)))
        b.rect(0, self.height - 3, w, self.height - 1, "#ff7fcf")
        b.rect(0, self.height - 1, w, self.height, "#8a76f7")
        for x, y in ((90, 6), (150, 17), (330, 7), (396, 16), (446, 8)):
            b.rect(x, y, x + 2, y + 2, "#ffd23a")
            b.rect(x - 2, y, x, y + 2, "#ffffff")
        cx = w / 2
        if title:
            b.ptext(title, cx, 7, 2, "#ff62b4", anchor="center", shadow="#12123a")
            return
        b.ptext("TASK QUEST", cx - 6, 7, 2, "#ff62b4", anchor="e", shadow="#12123a")
        b.heart(cx + 4, 8, "#ff2f8c")
        b.ptext("MOON", cx + 22, 7, 2, "#b296ff", shadow="#12123a")

    def button(self, name, x1, y1, x2, y2, hover, down):
        b = self.bar
        color = {"close": "#ff2f8c", "min": "#ffd23a"}[name]
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        b.disk(cx, cy, 7, "#12123a")
        b.disk(cx, cy + (1 if down else 0), 6, mix(color, "#ffffff", 0.35) if hover else color)
        if not down:
            b.rect(cx - 4, cy - 4, cx - 2, cy - 2, "#ffffff")
        if hover:   # значок появляется при наведении, как у светофора macOS
            glyph = tq.FONT["X"] if name == "close" else ["#####"]
            b.sprite(glyph, cx - 2, cy - (3 if name == "close" else 0) + (1 if down else 0), 1, "#12123a",
                     scale_x=0.8)


class Win2000Style(Style):
    """Заголовок окна Windows 98: градиент синего и серые объёмные кнопки справа."""
    height = 26
    bg = "#1a2a9a"
    buttons_left = False
    button_w = 18
    picker = {"title": "SKINS.EXE", "bg": "#c0c0c8", "hover": "#1a2a9a", "hover_line": "#1a2a9a", "text": "#000000",
              "sub": "#404048", "hover_text": "#ffffff", "hover_sub": "#dfe6ff", "check": "#1a2a9a",
              "border": "#808088", "font": "sans", "danger": "#c0203a"}

    def background(self, w, title):
        b = self.bar
        bands = 24
        for i in range(bands):
            b.rect(w * i / bands, 0, w * (i + 1) / bands + 1, self.height,
                   mix(tq.N["title1"], tq.N["title2"], i / (bands - 1)))
        b.sprite(tq.GHOST, 14, 3, 1.25, None, pal=tq.P2)
        b.ptext(title or "TASK QUEST 2000", 36, 7, 2, "#ffffff", shadow="#0b0820")

    def button(self, name, x1, y1, x2, y2, hover, down):
        b = self.bar
        y1, y2 = y1 + 4, y2 - 4
        light, dark = ("#808088", "#ffffff") if down else ("#ffffff", "#000000")
        b.rect(x1, y1, x2, y2, dark)
        b.rect(x1, y1, x2 - 1, y2 - 1, light)
        b.rect(x1 + 1, y1 + 1, x2 - 1, y2 - 1, "#808088" if not down else "#c0c0c8")
        b.rect(x1 + 1, y1 + 1, x2 - 2, y2 - 2, "#e4e4ec" if hover else "#c0c0c8")
        o = 1 if down else 0
        ink = "#ff4fa3" if hover else "#000000"
        if name == "close":
            b.ptext("X", x1 + 6 + o, y1 + 2 + o, 1, ink)
        else:
            b.rect(x1 + 4 + o, y2 - 5 + o, x1 + 10 + o, y2 - 3 + o, ink)


class TerminalStyle(Style):
    """Чёрная строка терминала с зелёным текстом; кнопки [_] [X] при наведении инвертируются."""
    height = 24
    bg = "#000000"
    buttons_left = False
    button_w = 34

    @staticmethod
    def dialog_title(title):
        return title.lower().replace(" ", "_").rstrip("?") + ".exe"   # «C:\QUEST> delete.exe»
    picker = {"title": "skins.exe", "bg": "#000000", "hover": "#39ff6a", "hover_line": "#39ff6a", "text": "#39ff6a",
              "sub": "#1fae48", "hover_text": "#000000", "hover_sub": "#03120a", "check": "#c4ffd2",
              "border": "#1fae48", "font": "mono"}

    def background(self, w, title):
        b = self.bar
        b.rect(0, 0, w, self.height, "#000000")
        for y in range(1, self.height, 3):
            b.rect(0, y, w, y + 1, "#03120a")
        b.rect(0, self.height - 1, w, self.height, "#11702f")
        b.text(10, self.height / 2, "C:\\QUEST> " + (title or "task_quest.exe"), "#39ff6a", 11, anchor="w")

    def button(self, name, x1, y1, x2, y2, hover, down):
        b = self.bar
        label = "[X]" if name == "close" else "[_]"
        if hover or down:
            b.rect(x1, y1 + 3, x2, y2 - 4, "#39ff6a" if not down else "#1fae48")
            b.text((x1 + x2) / 2, self.height / 2 - 0.5, label, "#000000", 11)
        else:
            b.text((x1 + x2) / 2, self.height / 2 - 0.5, label, "#1fae48", 11)


class MiniDiscStyle(Style):
    """Брашированный металл, как ярлык картриджа; кнопки — круглые индикаторы с голубой подсветкой."""
    height = 28
    bg = "#9aa1a7"
    picker = {"title": "SKIN SELECT", "bg": "#08141b", "hover": "#8ff0ff", "hover_line": "#8ff0ff", "text": "#e6fbff",
              "sub": "#4fa8bd", "hover_text": "#0b1014", "hover_sub": "#08303c", "check": "#8ff0ff",
              "border": "#4fa8bd", "font": "sans"}

    def background(self, w, title):
        b = self.bar
        for i in range(self.height):
            b.rect(0, i, w, i + 1, mix("#e3e6e9", "#9aa1a7", i / (self.height - 1)))
        b.rect(0, self.height - 1, w, self.height, "#3a4045")
        b.rect(0, self.height - 2, w, self.height - 1, "#4fa8bd")
        label = " ".join(title or "TASK QUEST · MINIDISC").replace("   ", "  ").replace(" ·", "  ·")
        b.text(w / 2, self.height / 2, label, "#0b1014", 10, font="sans", anchor="center")

    def button(self, name, x1, y1, x2, y2, hover, down):
        b = self.bar
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        r = 6
        b.cv.create_oval(cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1, fill="#3a4045", outline="", tags=b.tag)
        fill = ("#8ff0ff" if hover else "#08141b") if not down else "#4fa8bd"
        b.cv.create_oval(cx - r, cy - r, cx + r, cy + r, fill=fill, outline="#4fa8bd", tags=b.tag)
        glyph = "×" if name == "close" else "–"
        b.text(cx, cy - 0.5, glyph, "#08141b" if hover else "#8ff0ff", 10, font="sans", anchor="center")


STYLES = {"moon": MoonStyle, "2000": Win2000Style, "term": TerminalStyle, "md": MiniDiscStyle}


class TitleBar:
    """Холст-заголовок над холстом скина; умеет перекрашиваться под новый скин."""
    BUTTONS = ("close", "min")

    def __init__(self, root, on_close, parent=None, buttons=("close", "min"), draggable=True):
        self.root = root
        self.on_close = on_close
        self.BUTTONS = buttons
        self.draggable = draggable
        self.cv = tk.Canvas(parent or root, height=28, highlightthickness=0, bd=0)
        self.cv.pack(side="top", fill="x")
        self.tag = "bg"
        self.style = None
        self.hover = self.down = None
        self.drag = None
        self.cv.bind("<Motion>", self.on_motion)
        self.cv.bind("<Leave>", lambda e: self.set_state(None, None))
        self.cv.bind("<ButtonPress-1>", self.on_press)
        self.cv.bind("<B1-Motion>", self.on_drag)
        self.cv.bind("<ButtonRelease-1>", self.on_release)

    # примитивы рисования
    def rect(self, x1, y1, x2, y2, fill):
        self.cv.create_rectangle(x1, y1, x2, y2, fill=fill, outline="", tags=self.tag)

    def text(self, x, y, s, color, size, font="mono", anchor="center"):
        family = ("Menlo" if font == "mono" else "Helvetica Neue")
        self.cv.create_text(x, y, text=s, fill=color, font=(family, size, "bold"), anchor=anchor, tags=self.tag)

    def sprite(self, rows, x0, y0, s, color, pal=None, scale_x=1.0):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in ".":
                    continue
                col = color or (pal or {}).get(ch)
                if col:
                    self.rect(x0 + i * s * scale_x, y0 + j * s, x0 + (i + 1) * s * scale_x, y0 + (j + 1) * s, col)

    def ptext(self, s, x, y, scale, color, anchor="w", shadow=None):
        glyphs = [tq.FONT.get(ch, tq.FONT["?"]) for ch in s.upper()]
        total = sum(len(g[0]) + 1 for g in glyphs) * scale - scale
        x -= total / 2 if anchor == "center" else total if anchor == "e" else 0
        for off, col in ([(1, shadow)] if shadow else []) + [(0, color)]:
            cx = x
            for g in glyphs:
                self.sprite(g, cx + off, y + off, scale, col)
                cx += (len(g[0]) + 1) * scale

    def disk(self, cx, cy, r, color):
        for j in range(-r, r + 1):
            half = int(((r + 0.4) ** 2 - j * j) ** 0.5)
            self.rect(cx - half, cy + j, cx + half + 1, cy + j + 1, color)

    def heart(self, x, y, color):
        self.sprite([".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."], x, y, 2, color,
                    scale_x=0.75)

    # раскладка
    def apply(self, skin, width, title=None):
        self.style = STYLES.get(skin, MoonStyle)(self)
        st = self.style
        self.width = width
        self.cv.config(width=width, height=st.height, bg=st.bg)
        self.cv.delete("all")
        self.tag = "bg"
        st.background(width, title)
        self.slots = {}
        gap, y1, y2 = 6, 0, st.height
        for k, name in enumerate(self.BUTTONS if st.buttons_left else reversed(self.BUTTONS)):
            if st.buttons_left:
                x1 = 8 + k * (st.button_w + gap)
            else:
                x1 = width - 8 - (len(self.BUTTONS) - k) * (st.button_w + gap) + gap
            self.slots[name] = (x1, y1, x1 + st.button_w, y2)
        self.hover = self.down = None
        self.draw_buttons()

    def draw_buttons(self):
        self.cv.delete("btn")
        self.tag = "btn"
        for name, (x1, y1, x2, y2) in self.slots.items():
            self.style.button(name, x1, y1, x2, y2, self.hover == name, self.down == name)
        self.tag = "bg"

    def button_at(self, x, y):
        for name, (x1, y1, x2, y2) in self.slots.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                return name
        return None

    def set_state(self, hover, down):
        if (hover, down) != (self.hover, self.down):   # перерисовываем только кнопки и только при изменении
            self.hover, self.down = hover, down
            self.draw_buttons()

    # мышь
    def on_motion(self, e):
        if self.drag is None:
            self.set_state(self.button_at(e.x, e.y), self.down)

    def on_press(self, e):
        name = self.button_at(e.x, e.y)
        if name:
            self.set_state(name, name)
        elif self.draggable and not mac_native_drag():
            self.drag = (e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y())

    def on_drag(self, e):
        if self.drag:
            self.root.geometry(f"+{e.x_root - self.drag[0]}+{e.y_root - self.drag[1]}")

    def on_release(self, e):
        name = self.down
        self.drag = None
        self.set_state(self.button_at(e.x, e.y), None)
        if name and name == self.button_at(e.x, e.y):
            if name == "close":
                self.on_close()
            else:
                mac_hide_app(self.root)
