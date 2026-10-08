"""Один раз готовит кадры анимации «Готово» из GIF: полные кадры, уменьшенные, без чёрного фона.

Чёрный фон GIF превращается в прозрачность, свечение — в полупрозрачность (яркость → непрозрачность),
поэтому анимация ложится поверх любого скина. Результат — assets/done_kirby/0.png … N.png.

Запуск:  python3 tools/bake_done_gif.py путь/к/анимации.gif [высота]
"""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import disc_render as dr   # noqa: E402 — обёртки CoreGraphics/ImageIO

_sz = ctypes.c_size_t
CGImageSourceGetCount = dr._sig(dr._io, "CGImageSourceGetCount", _sz, ctypes.c_void_p)
CGImageGetWidth = dr._sig(dr._cg, "CGImageGetWidth", _sz, ctypes.c_void_p)
CGImageGetHeight = dr._sig(dr._cg, "CGImageGetHeight", _sz, ctypes.c_void_p)
CGBitmapContextGetData = dr._sig(dr._cg, "CGBitmapContextGetData", ctypes.c_void_p, ctypes.c_void_p)
CGBitmapContextGetBytesPerRow = dr._sig(dr._cg, "CGBitmapContextGetBytesPerRow", _sz, ctypes.c_void_p)


def bake(src_path, out_dir, height=170, glow=3.0):
    os.makedirs(out_dir, exist_ok=True)
    url = dr._url(src_path)
    src = dr.CGImageSourceCreateWithURL(url, None)
    count = CGImageSourceGetCount(src)
    first = dr.CGImageSourceCreateImageAtIndex(src, 0, None)
    w0, h0 = CGImageGetWidth(first), CGImageGetHeight(first)
    dr.CGImageRelease(first)
    h = height
    w = round(w0 * h / h0)
    space = dr.CGColorSpaceCreateDeviceRGB()
    png = dr.CFStringCreateWithCString(None, b"public.png", dr._UTF8)
    for i in range(count):
        frame = dr.CGImageSourceCreateImageAtIndex(src, i, None)   # ImageIO отдаёт уже собранный кадр
        ctx = dr.CGBitmapContextCreate(None, w, h, 8, 0, space, dr._PREMULT_LAST)
        dr.CGContextSetInterpolationQuality(ctx, dr._HIGH_QUALITY)
        dr.CGContextDrawImage(ctx, dr.CGRect(0, 0, w, h), frame)
        stride = CGBitmapContextGetBytesPerRow(ctx)
        buf = (ctypes.c_ubyte * (stride * h)).from_address(CGBitmapContextGetData(ctx))
        for y in range(h):
            row = y * stride
            for x in range(w):
                p = row + x * 4
                m = max(buf[p], buf[p + 1], buf[p + 2])
                # чёрный фон (почти 0) — прозрачный; уже со слабой яркостью — почти непрозрачный диск
                a = 0 if m < 6 else min(255, int(60 + m * glow))
                buf[p + 3] = a   # цвета уже не больше непрозрачности — premultiplied остаётся корректным
        out = dr.CGBitmapContextCreateImage(ctx)
        tmp = os.path.join(out_dir, f".{i}.png")
        out_url = dr._url(tmp)
        dest = dr.CGImageDestinationCreateWithURL(out_url, png, 1, None)
        dr.CGImageDestinationAddImage(dest, out, None)
        dr.CGImageDestinationFinalize(dest)
        os.replace(tmp, os.path.join(out_dir, f"{i}.png"))
        for obj in (dest, out_url):
            dr.CFRelease(obj)
        dr.CGImageRelease(out)
        dr.CGImageRelease(frame)
        dr.CGContextRelease(ctx)
    dr.CFRelease(png)
    dr.CGColorSpaceRelease(space)
    dr.CFRelease(src)
    dr.CFRelease(url)
    return count, w, h


if __name__ == "__main__":
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    n, w, h = bake(sys.argv[1], os.path.join(here, "assets", "done_kirby"),
                   int(sys.argv[2]) if len(sys.argv) > 2 else 170)
    print(f"{n} кадров {w}×{h} → assets/done_kirby")
