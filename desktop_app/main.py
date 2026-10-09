import sys
import os
import io
import threading
import tkinter as tk

# Защита от ошибок вывода (print / uvicorn) в режиме --windowed PyInstaller
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from screen_engine import ScreenEngine
from launcher_window import LauncherWindow
from overlay_ui import FloatingOverlayUI
from server import run_server

def start_application():
    # 1. Инициализация движка мульти-ИИ и авторизации
    engine = ScreenEngine()

    # 2. Запуск фонового веб-хостинга
    server_thread = threading.Thread(
        target=run_server,
        args=(engine, "0.0.0.0", 8000),
        daemon=True
    )
    server_thread.start()

    # 3. Запуск фонового цикла мониторинга
    engine.start_loop()

    # 4. Создание графических окон
    root = tk.Tk()

    # Окно оверлея создается как Toplevel
    overlay_top = tk.Toplevel(root)
    overlay_top.withdraw() # Изначально скрыто до нажатия кнопки в лаунчере

    def show_overlay():
        overlay_ui.show()

    def show_launcher():
        root.deiconify()
        root.lift()

    overlay_ui = FloatingOverlayUI(overlay_top, engine, on_open_launcher=show_launcher)
    launcher = LauncherWindow(root, engine, on_launch_overlay=show_overlay)

    def on_closing():
        if hasattr(overlay_ui, "hotkeys") and overlay_ui.hotkeys:
            overlay_ui.hotkeys.stop()
        engine.stop()
        root.destroy()
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        engine.stop()

if __name__ == "__main__":
    start_application()
