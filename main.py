from pathlib import Path
import sys
import traceback

def _eula_accepted():
    # Applies to Windows only; the marker is written by scripts/Install.ps1 or by the prompt below.
    if sys.platform != "win32":
        return True
    mark = Path(__file__).with_name(".eula-accepted-1.0")
    if mark.exists():
        return True
    import ctypes
    text = ("Nostalgia RTX содержит проприетарные компоненты NVIDIA RTX Video SDK и распространяется на условиях "
            "лицензионного соглашения (файл EULA.md в папке программы).\n\n"
            "Вы прочитали соглашение и принимаете его условия?")
    if ctypes.windll.user32.MessageBoxW(None, text, "Nostalgia RTX — лицензионное соглашение", 0x24) != 6:
        return False
    mark.write_text("EULA 1.0 accepted\n", encoding="ascii")
    return True


try:
    if not _eula_accepted():
        raise SystemExit(0)
    from nostalgia.gui import main
    code = main()
except Exception:
    error = traceback.format_exc()
    Path(__file__).with_name("startup.log").write_text(error, encoding="utf-8")
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, "Не удалось запустить интерфейс. Ошибка записана в startup.log. Запустите INSTALL.cmd повторно.", "Nostalgia RTX", 0x10)
    else:
        print(error, file=sys.stderr)
    code = 1
raise SystemExit(code)
