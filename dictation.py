"""Голосовой ввод: включает встроенную диктовку macOS в поле, где стоит курсор.

Распознанный текст система сама вставляет в поле Tk (окно Tk принимает системный текстовый ввод).
Язык — из настроек диктовки macOS («Системные настройки → Клавиатура → Диктовка»); если диктовка
ещё не включена, macOS при первом нажатии предложит её включить. Сторонние библиотеки и ключи не нужны.
"""
import ctypes
import sys

try:
    import titlebar as _tb
    AVAILABLE = sys.platform == "darwin" and _tb._objc is not None
except ImportError:
    AVAILABLE = False


def _action(name):
    sel = _tb._objc.sel_registerName(name)
    return bool(_tb._send(_tb._nsapp(), b"sendAction:to:from:", ctypes.c_bool,
                          (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p), sel, None, None))


def start(widget):
    """Поставить курсор в конец поля и включить диктовку. Возвращает True, если система её приняла."""
    if not AVAILABLE:
        return False
    widget.focus_force()
    try:
        widget.mark_set("insert", "end-1c")
        if widget.get("end-2c", "end-1c") not in ("", " ", "\n"):
            widget.insert("end-1c", " ")   # чтобы надиктованное не слиплось с уже написанным
    except Exception:   # noqa: BLE001 — Entry вместо Text
        pass
    widget.update_idletasks()
    try:
        return _action(b"startDictation:")
    except (AttributeError, OSError, ValueError, ctypes.ArgumentError):
        return False


def stop():
    if AVAILABLE:
        try:
            _action(b"stopDictation:")
        except (AttributeError, OSError, ValueError, ctypes.ArgumentError):
            pass
