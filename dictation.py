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


def _app_window():
    """Окно приложения (Tk), а не «активное окно»: во время диктовки активным может быть её же
    системное окошко с микрофоном, и команды уходили бы ему."""
    for w in _tb._tk_windows():
        if _tb._send(w, b"isVisible", ctypes.c_bool):
            return w
    return _tb._send(_tb._nsapp(), b"keyWindow")


def _input_context():
    win = _app_window()
    view = _tb._send(win, b"contentView") if win else None
    return _tb._send(view, b"inputContext") if view else None


def _responds(obj, sel):
    return bool(obj) and _tb._send(obj, b"respondsToSelector:", ctypes.c_bool, (ctypes.c_void_p,),
                                   _tb._objc.sel_registerName(sel))


def stop_only():
    """Выключить диктовку и спрятать системный значок микрофона
    (черновик подтверждает тот, кто знает поле, — см. TaskDetails.commit_draft).

    Общая команда приложения stopDictation: диктовку в поле Tk не останавливает, поэтому сначала
    останавливаем её у самого поля ввода (контекст ввода), а общую команду посылаем вдогонку."""
    if not AVAILABLE:
        return
    try:
        ctx = _input_context()
        if _responds(ctx, b"_stopDictation:"):
            _tb._send(ctx, b"_stopDictation:", None, (ctypes.c_void_p,), None)
        _action(b"stopDictation:")
        ctx = _input_context()
        if _responds(ctx, b"hideDictationIndicator"):
            _tb._send(ctx, b"hideDictationIndicator")
    except (AttributeError, OSError, ValueError, ctypes.ArgumentError):
        pass


def end_session(widget, then=None):
    """Надёжно закончить диктовку: команды остановки диктовка в поле Tk выполняет не всегда, а вот
    уход фокуса из приложения заканчивает её всегда. На долю секунды отдаём фокус Finder и сразу
    возвращаем полю (окно остаётся на месте, курсор — в поле). then() — после возврата."""
    stop_only()
    if not AVAILABLE:
        if then:
            then()
        return
    try:
        ws = _tb._send(_tb._objc.objc_getClass(b"NSWorkspace"), b"sharedWorkspace")
        apps = _tb._send(ws, b"runningApplications")
        for i in range(_tb._send(apps, b"count", ctypes.c_ulong)):
            a = _tb._send(apps, b"objectAtIndex:", ctypes.c_void_p, (ctypes.c_ulong,), i)
            bid = _tb._send(a, b"bundleIdentifier")
            if bid and ctypes.cast(_tb._send(bid, b"UTF8String"), ctypes.c_char_p).value == b"com.apple.finder":
                _tb._send(a, b"activateWithOptions:", ctypes.c_bool, (ctypes.c_ulong,), 0)
                break
    except (AttributeError, OSError, ValueError, ctypes.ArgumentError):
        pass

    def back():
        try:
            _tb._send(_tb._nsapp(), b"activateIgnoringOtherApps:", None, (ctypes.c_bool,), True)
            win = _app_window()
            if win:
                _tb._send(win, b"makeKeyAndOrderFront:", None, (ctypes.c_void_p,), None)
        except (AttributeError, OSError, ValueError, ctypes.ArgumentError):
            pass
        try:
            widget.focus_force()
        except Exception:   # noqa: BLE001 — карточку уже закрыли
            pass
        if then:
            then()
    widget.after(350, back)


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
        win = _app_window()
        if not win:
            return
        view = _tb._send(win, b"contentView")
        if not view:
            return
        # трогаем ввод только если черновик действительно есть: лишние сбросы и смена получателя ввода
        # заставляют macOS снова запускать диктовку при каждом щелчке
        if _tb._send(view, b"hasMarkedText", ctypes.c_bool):
            responds = lambda obj, sel: _tb._send(obj, b"respondsToSelector:", ctypes.c_bool, (ctypes.c_void_p,),
                                                  _tb._objc.sel_registerName(sel))
            if responds(view, b"unmarkText"):
                _tb._send(view, b"unmarkText")
            ctx = _tb._send(view, b"inputContext")
            if ctx:
                _tb._send(ctx, b"discardMarkedText")
        if _tb._send(win, b"firstResponder") != view:
            _tb._send(win, b"makeFirstResponder:", ctypes.c_bool, (ctypes.c_void_p,), view)
    except (AttributeError, OSError, ValueError, ctypes.ArgumentError):
        pass


def has_draft():
    """Есть ли в окне неподтверждённый текст диктовки (или другого системного ввода)."""
    if not AVAILABLE:
        return False
    try:
        win = _app_window()
        view = _tb._send(win, b"contentView") if win else None
        return bool(view) and _tb._send(view, b"hasMarkedText", ctypes.c_bool)
    except (AttributeError, OSError, ValueError, ctypes.ArgumentError):
        return False


def active():
    """Идёт ли диктовка: виден ли системный значок микрофона (окошко TUINSWindow)."""
    if not AVAILABLE:
        return False
    try:
        wins = _tb._send(_tb._nsapp(), b"windows")
        for i in range(_tb._send(wins, b"count", ctypes.c_ulong)):
            w = _tb._send(wins, b"objectAtIndex:", ctypes.c_void_p, (ctypes.c_ulong,), i)
            if _tb._class_name(w) == b"TUINSWindow" and _tb._send(w, b"isVisible", ctypes.c_bool):
                return True
    except (AttributeError, OSError, ValueError, ctypes.ArgumentError):
        pass
    return False
