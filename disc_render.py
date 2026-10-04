"""Кадры вращения диска для скина MiniDisc — через CoreGraphics macOS (ctypes, без сторонних библиотек).

render_frames(src, outdir, size, frames) пишет outdir/0.png … outdir/{frames-1}.png:
диск, повёрнутый на k·360/frames градусов по часовой стрелке, обрезанный кругом, с прозрачным фоном.
Работает за доли секунды; вызывается из фонового потока при первом показе диска.
"""
import ctypes
import ctypes.util
import math
import os

_cf = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreFoundation"))
_cg = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreGraphics"))
_io = ctypes.cdll.LoadLibrary(ctypes.util.find_library("ImageIO"))

_vp, _sz, _b = ctypes.c_void_p, ctypes.c_size_t, ctypes.c_bool


class CGRect(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double), ("w", ctypes.c_double), ("h", ctypes.c_double)]


def _sig(lib, name, res, *args):
    f = getattr(lib, name)
    f.restype, f.argtypes = res, list(args)
    return f


CFRelease = _sig(_cf, "CFRelease", None, _vp)
CFURLCreateFromFileSystemRepresentation = _sig(_cf, "CFURLCreateFromFileSystemRepresentation", _vp,
                                               _vp, ctypes.c_char_p, ctypes.c_long, _b)
CFStringCreateWithCString = _sig(_cf, "CFStringCreateWithCString", _vp, _vp, ctypes.c_char_p, ctypes.c_uint32)
CGImageSourceCreateWithURL = _sig(_io, "CGImageSourceCreateWithURL", _vp, _vp, _vp)
CGImageSourceCreateImageAtIndex = _sig(_io, "CGImageSourceCreateImageAtIndex", _vp, _vp, _sz, _vp)
CGImageDestinationCreateWithURL = _sig(_io, "CGImageDestinationCreateWithURL", _vp, _vp, _vp, _sz, _vp)
CGImageDestinationAddImage = _sig(_io, "CGImageDestinationAddImage", None, _vp, _vp, _vp)
CGImageDestinationFinalize = _sig(_io, "CGImageDestinationFinalize", _b, _vp)
CGColorSpaceCreateDeviceRGB = _sig(_cg, "CGColorSpaceCreateDeviceRGB", _vp)
CGBitmapContextCreate = _sig(_cg, "CGBitmapContextCreate", _vp, _vp, _sz, _sz, _sz, _sz, _vp, ctypes.c_uint32)
CGBitmapContextCreateImage = _sig(_cg, "CGBitmapContextCreateImage", _vp, _vp)
CGContextSetInterpolationQuality = _sig(_cg, "CGContextSetInterpolationQuality", None, _vp, ctypes.c_int)
CGContextAddEllipseInRect = _sig(_cg, "CGContextAddEllipseInRect", None, _vp, CGRect)
CGContextClip = _sig(_cg, "CGContextClip", None, _vp)
CGContextTranslateCTM = _sig(_cg, "CGContextTranslateCTM", None, _vp, ctypes.c_double, ctypes.c_double)
CGContextRotateCTM = _sig(_cg, "CGContextRotateCTM", None, _vp, ctypes.c_double)
CGContextDrawImage = _sig(_cg, "CGContextDrawImage", None, _vp, CGRect, _vp)
CGContextRelease = _sig(_cg, "CGContextRelease", None, _vp)
CGImageRelease = _sig(_cg, "CGImageRelease", None, _vp)
CGColorSpaceRelease = _sig(_cg, "CGColorSpaceRelease", None, _vp)

_UTF8 = 0x08000100
_PREMULT_LAST = 1        # kCGImageAlphaPremultipliedLast
_HIGH_QUALITY = 3        # kCGInterpolationHigh


def _url(path):
    b = os.fsencode(os.path.abspath(path))
    return CFURLCreateFromFileSystemRepresentation(None, b, len(b), False)


def render_frames(src, outdir, size, frames):
    os.makedirs(outdir, exist_ok=True)
    src_url = _url(src)
    source = CGImageSourceCreateWithURL(src_url, None)
    image = CGImageSourceCreateImageAtIndex(source, 0, None) if source else None
    if not image:
        raise OSError(f"не удалось прочитать {src}")
    space = CGColorSpaceCreateDeviceRGB()
    png = CFStringCreateWithCString(None, b"public.png", _UTF8)
    s = float(size)
    try:
        for k in range(frames):
            ctx = CGBitmapContextCreate(None, size, size, 8, 0, space, _PREMULT_LAST)
            CGContextSetInterpolationQuality(ctx, _HIGH_QUALITY)
            CGContextAddEllipseInRect(ctx, CGRect(0.5, 0.5, s - 1, s - 1))   # круг диска
            CGContextClip(ctx)
            CGContextTranslateCTM(ctx, s / 2, s / 2)
            CGContextRotateCTM(ctx, -k * 2 * math.pi / frames)               # по часовой стрелке
            CGContextDrawImage(ctx, CGRect(-s / 2, -s / 2, s, s), image)
            frame = CGBitmapContextCreateImage(ctx)
            tmp = os.path.join(outdir, f".{k}.png")
            out_url = _url(tmp)
            dest = CGImageDestinationCreateWithURL(out_url, png, 1, None)
            CGImageDestinationAddImage(dest, frame, None)
            CGImageDestinationFinalize(dest)
            os.replace(tmp, os.path.join(outdir, f"{k}.png"))   # готовый кадр появляется целиком
            for obj in (dest, out_url):
                CFRelease(obj)
            CGImageRelease(frame)
            CGContextRelease(ctx)
    finally:
        CFRelease(png)
        CGColorSpaceRelease(space)
        CGImageRelease(image)
        CFRelease(source)
        CFRelease(src_url)


if __name__ == "__main__":
    import sys
    render_frames(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
