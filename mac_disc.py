"""Диск MiniDisc, который вращает сама macOS (Core Animation) — плавно, 60 кадров в секунду, без нагрузки на Tk.

Диск — отдельный слой поверх окна Tk. Python только меняет скорость (разгон и выбег),
кадры рисует видеокарта. Шторка картриджа «вырезана» из слоя маской, поэтому она и надписи
в окошке ярлыка (их рисует Tk) остаются видны поверх диска; втулка — свой слой над диском.

Если что-то недоступно (не macOS, другая версия Tk), attach() возвращает None и скин
крутит диск по-старому, кадрами Tk.
"""
import ctypes
import ctypes.util
import math

try:
    import disc_render as dr
    _objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
    _qc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("QuartzCore"))
    _objc.objc_getClass.restype = ctypes.c_void_p
    _objc.objc_getClass.argtypes = [ctypes.c_char_p]
    _objc.sel_registerName.restype = ctypes.c_void_p
    _objc.sel_registerName.argtypes = [ctypes.c_char_p]
    _qc.CACurrentMediaTime.restype = ctypes.c_double
    _cg = dr._cg
    CGContextSetBlendMode = dr._sig(_cg, "CGContextSetBlendMode", None, ctypes.c_void_p, ctypes.c_int)
    CGContextSetRGBFillColor = dr._sig(_cg, "CGContextSetRGBFillColor", None, ctypes.c_void_p, ctypes.c_double,
                                       ctypes.c_double, ctypes.c_double, ctypes.c_double)
    CGContextFillEllipseInRect = dr._sig(_cg, "CGContextFillEllipseInRect", None, ctypes.c_void_p, dr.CGRect)
    AVAILABLE = True
except (OSError, TypeError, AttributeError):
    AVAILABLE = False

_D, _F, _B, _V = ctypes.c_double, ctypes.c_float, ctypes.c_bool, ctypes.c_void_p
_BLEND_DEST_OUT = 23   # kCGBlendModeDestinationOut


def _send(obj, sel, restype=_V, argtypes=(), *args):
    fn = ctypes.cast(_objc.objc_msgSend, ctypes.CFUNCTYPE(restype, _V, _V, *argtypes))
    return fn(obj, _objc.sel_registerName(sel), *args)


def _cls(name):
    return _objc.objc_getClass(name)


def _nsstring(s):
    return dr.CFStringCreateWithCString(None, s.encode(), dr._UTF8)


def _load_image(path):
    url = dr._url(path)
    src = dr.CGImageSourceCreateWithURL(url, None)
    img = dr.CGImageSourceCreateImageAtIndex(src, 0, None) if src else None
    dr.CFRelease(url)
    if src:
        dr.CFRelease(src)
    return img


def _mask_image(size, cutout_path, cut_x, cut_y):
    """Маска слоя диска: круг минус непрозрачная часть шторки (cut_x, cut_y — от левого верхнего угла)."""
    space = dr.CGColorSpaceCreateDeviceRGB()
    ctx = dr.CGBitmapContextCreate(None, size, size, 8, 0, space, dr._PREMULT_LAST)
    CGContextSetRGBFillColor(ctx, 1, 1, 1, 1)
    CGContextFillEllipseInRect(ctx, dr.CGRect(0, 0, size, size))
    cut = _load_image(cutout_path)
    if cut:
        w = dr._sig(_cg, "CGImageGetWidth", ctypes.c_size_t, _V)(cut)
        h = dr._sig(_cg, "CGImageGetHeight", ctypes.c_size_t, _V)(cut)
        CGContextSetBlendMode(ctx, _BLEND_DEST_OUT)
        dr.CGContextDrawImage(ctx, dr.CGRect(cut_x, size - cut_y - h, w, h), cut)   # ось y у CoreGraphics — вверх
        dr.CGImageRelease(cut)
    img = dr.CGBitmapContextCreateImage(ctx)
    dr.CGContextRelease(ctx)
    dr.CGColorSpaceRelease(space)
    return img


def _main_window():
    app = _send(_cls(b"NSApplication"), b"sharedApplication")
    wins = _send(app, b"windows")
    for i in range(_send(wins, b"count", ctypes.c_ulong)):
        w = _send(wins, b"objectAtIndex:", _V, (ctypes.c_ulong,), i)
        name = ctypes.cast(_send(_send(w, b"className"), b"UTF8String"), ctypes.c_char_p).value
        if name == b"TKWindow" and _send(w, b"isVisible", _B):
            return w
    return None


class _Tx:
    """CATransaction без неявных анимаций (чтобы слои вставали на место мгновенно)."""
    def __enter__(self):
        _send(_cls(b"CATransaction"), b"begin")
        _send(_cls(b"CATransaction"), b"setDisableActions:", None, (_B,), True)

    def __exit__(self, *exc):
        _send(_cls(b"CATransaction"), b"commit")


class NativeDisc:
    def __init__(self, host, container, disc, hub, period, x, y, size):
        self.host, self.container, self.disc, self.hub = host, container, disc, hub
        self.period = period
        self.x, self.y, self.size = x, y, size
        self.host_h = None
        self.follow()
        self.images = {}
        self.speed = 0.0

    def follow(self, x=None, y=None):
        """Держит слой на месте диска. У слоя окна ось y снизу, поэтому позиция зависит от высоты окна;
        к тому же при запуске окно и панель заголовка встают на место не сразу — пересчитываем при изменениях."""
        if x is not None:
            self.x, self.y = x, y
        h = _send(self.host, b"bounds", dr.CGRect).h
        key = (h, self.x, self.y)
        if key != self.host_h:
            self.host_h = key
            with _Tx():
                _send(self.container, b"setFrame:", None, (dr.CGRect,),
                      dr.CGRect(self.x, h - self.y - self.size, self.size, self.size))

    def set_image(self, path):
        """Сменить диск — с мягкой сменой картинки (неявная анимация contents)."""
        img = self.images.get(path)
        if img is None:
            img = self.images[path] = _load_image(path)
        if img:
            _send(self.disc, b"setContents:", None, (_V,), img)

    def set_speed(self, k):
        """k — доля полного хода (1 — оборот за period секунд, 0 — стоит, < 0 — назад)."""
        if abs(k - self.speed) < 1e-4:
            return
        now = _qc.CACurrentMediaTime()
        local = _send(self.disc, b"convertTime:fromLayer:", _D, (_D, _V), now, None)
        with _Tx():
            _send(self.disc, b"setTimeOffset:", None, (_D,), local)
            _send(self.disc, b"setBeginTime:", None, (_D,), now)
            _send(self.disc, b"setSpeed:", None, (_F,), k)
        self.speed = k

    def set_hidden(self, hidden):
        with _Tx():
            _send(self.container, b"setHidden:", None, (_B,), hidden)

    def remove(self):
        with _Tx():
            _send(self.container, b"removeFromSuperlayer")


def attach(x, y, size, disc_path, cutout_path, cut_x, cut_y, hub_path, period):
    """Слой диска в окне: (x, y) — левый верхний угол квадрата диска в координатах окна Tk."""
    if not AVAILABLE:
        return None
    try:
        win = _main_window()
        if not win:
            return None
        host = _send(_send(win, b"contentView"), b"layer")
        if not host:
            return None
        with _Tx():
            container = _send(_send(_cls(b"CALayer"), b"layer"), b"retain")
            mask = _send(_send(_cls(b"CALayer"), b"layer"), b"retain")
            _send(mask, b"setFrame:", None, (dr.CGRect,), dr.CGRect(0, 0, size, size))
            _send(mask, b"setContents:", None, (_V,), _mask_image(size, cutout_path, cut_x, cut_y))
            _send(container, b"setMask:", None, (_V,), mask)

            disc = _send(_send(_cls(b"CALayer"), b"layer"), b"retain")
            _send(disc, b"setFrame:", None, (dr.CGRect,), dr.CGRect(0, 0, size, size))
            _send(disc, b"setCornerRadius:", None, (_D,), size / 2)
            _send(disc, b"setMasksToBounds:", None, (_B,), True)
            _send(container, b"addSublayer:", None, (_V,), disc)

            hub_img = _load_image(hub_path)
            hub = None
            if hub_img:
                hw = dr._sig(_cg, "CGImageGetWidth", ctypes.c_size_t, _V)(hub_img)
                hub = _send(_send(_cls(b"CALayer"), b"layer"), b"retain")
                _send(hub, b"setFrame:", None, (dr.CGRect,), dr.CGRect((size - hw) / 2, (size - hw) / 2, hw, hw))
                _send(hub, b"setContents:", None, (_V,), hub_img)
                _send(container, b"addSublayer:", None, (_V,), hub)
            _send(host, b"addSublayer:", None, (_V,), container)

            # бесконечный оборот по часовой стрелке; скоростью управляет speed слоя
            anim = _send(_cls(b"CABasicAnimation"), b"animationWithKeyPath:", _V, (_V,),
                         _nsstring("transform.rotation.z"))
            num = lambda v: _send(_cls(b"NSNumber"), b"numberWithDouble:", _V, (_D,), v)
            _send(anim, b"setFromValue:", None, (_V,), num(0.0))
            _send(anim, b"setToValue:", None, (_V,), num(-2 * math.pi))
            _send(anim, b"setDuration:", None, (_D,), period)
            _send(anim, b"setRepeatCount:", None, (_F,), 1e9)
            _send(anim, b"setRemovedOnCompletion:", None, (_B,), False)
            _send(disc, b"addAnimation:forKey:", None, (_V, _V), anim, _nsstring("spin"))
            _send(disc, b"setSpeed:", None, (_F,), 0.0)
        nd = NativeDisc(host, container, disc, hub, period, x, y, size)
        nd.set_image(disc_path)
        return nd
    except (AttributeError, OSError, ValueError, ctypes.ArgumentError):
        return None
