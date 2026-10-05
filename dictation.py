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


def stop_only():
    """Выключить диктовку (черновик подтверждает тот, кто знает поле, — см. TaskDetails.commit_draft)."""
    if AVAILABLE:
        try:
            _action(b"stopDictation:")
        except (AttributeError, OSError, ValueError, ctypes.ArgumentError):
            pass


def stop():
    stop_only()
    reset_input()


def reset_input():
    """Возвращает клавиатуру полю ввода после диктовки.

    Пока диктовка распознаёт речь, в поле стоит «черновой» (ещё не подтверждённый) текст. Если диктовку
    остановили посреди фразы или она отключилась сама, черновик может остаться, и обычные нажатия клавиш
    перестают доходить до поля. Здесь черновик подтверждается, а окно снова получает ввод с клавиатуры."""
    if not AVAILABLE:
        return
    try:
        _tb.mac_make_key()
        app = _tb._nsapp()
        win = _tb._send(app, b"keyWindow")
        if not win:
            return
        view = _tb._send(win, b"contentView")
        responds = lambda obj, sel: _tb._send(obj, b"respondsToSelector:", ctypes.c_bool, (ctypes.c_void_p,),
                                              _tb._objc.sel_registerName(sel))
        if view and responds(view, b"unmarkText"):
            _tb._send(view, b"unmarkText")
        ctx = _tb._send(view, b"inputContext") if view else None
        if ctx:
            _tb._send(ctx, b"discardMarkedText")
        if view:
            _tb._send(win, b"makeFirstResponder:", ctypes.c_bool, (ctypes.c_void_p,), view)
    except (AttributeError, OSError, ValueError, ctypes.ArgumentError):
        pass


def has_draft():
    """Есть ли в окне неподтверждённый текст диктовки (или другого системного ввода)."""
    if not AVAILABLE:
        return False
    try:
        win = _tb._send(_tb._nsapp(), b"keyWindow")
        view = _tb._send(win, b"contentView") if win else None
        return bool(view) and _tb._send(view, b"hasMarkedText", ctypes.c_bool)
    except (AttributeError, OSError, ValueError, ctypes.ArgumentError):
        return False
