import time
import ctypes
import threading


class GlobalHotkeyManager:
    """
    Глобальный перехватчик горячих клавиш Windows (без сторонних библиотек).
    Работает поверх любых окон (игры, браузеры, Zoom, Word) независимо от раскладки RU/EN/UA.
    Горячие клавиши:
      Alt + X — Мгновенный анализ всего экрана
      Alt + Z — Экстренно скрыть / показать оверлей (паник-кнопка)
      Alt + S — Снайперский режим (выделение задачи рамкой)
      Alt + V — Захват звука из наушников/колонок (слух ИИ)
    """

    VK_MENU = 0x12  # Alt
    VK_X = 0x58     # Alt + X: Анализ экрана
    VK_B = 0x42     # Alt + B: Анализ буфера обмена (Win+Shift+S)
    VK_Z = 0x5A     # Alt + Z: Экстренно спрятать/показать
    VK_S = 0x53     # Alt + S: Снайперская рамка
    VK_V = 0x56     # Alt + V: Голосовой суфлер
    VK_C = 0x43     # Alt + C: Крипто-Радар
    VK_LEFT = 0x25  # Alt + Left: Листать назад в истории
    VK_RIGHT = 0x27 # Alt + Right: Листать вперед в истории

    def __init__(self, on_analyze=None, on_clipboard=None, on_toggle_stealth_hide=None, on_sniper=None, on_audio=None, on_crypto=None, on_history_prev=None, on_history_next=None):
        self.on_analyze = on_analyze
        self.on_clipboard = on_clipboard
        self.on_toggle_stealth_hide = on_toggle_stealth_hide
        self.on_sniper = on_sniper
        self.on_audio = on_audio
        self.on_crypto = on_crypto
        self.on_history_prev = on_history_prev
        self.on_history_next = on_history_next

        self._running = False
        self._thread = None
        self._last_trigger = {
            self.VK_X: 0,
            self.VK_B: 0,
            self.VK_Z: 0,
            self.VK_S: 0,
            self.VK_V: 0,
            self.VK_C: 0,
            self.VK_LEFT: 0,
            self.VK_RIGHT: 0
        }

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _is_pressed(self, vk):
        # Старший бит установлен (0x8000), если клавиша нажата в данный момент
        return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)

    def _loop(self):
        debounce = 0.45

        while self._running:
            try:
                alt_down = self._is_pressed(self.VK_MENU)
                now = time.time()

                if alt_down:
                    if self._is_pressed(self.VK_X) and (now - self._last_trigger[self.VK_X] > debounce):
                        self._last_trigger[self.VK_X] = now
                        if self.on_analyze:
                            self.on_analyze()

                    elif self._is_pressed(self.VK_B) and (now - self._last_trigger[self.VK_B] > debounce):
                        self._last_trigger[self.VK_B] = now
                        if self.on_clipboard:
                            self.on_clipboard()

                    elif self._is_pressed(self.VK_Z) and (now - self._last_trigger[self.VK_Z] > debounce):
                        self._last_trigger[self.VK_Z] = now
                        if self.on_toggle_stealth_hide:
                            self.on_toggle_stealth_hide()

                    elif self._is_pressed(self.VK_S) and (now - self._last_trigger[self.VK_S] > debounce):
                        self._last_trigger[self.VK_S] = now
                        if self.on_sniper:
                            self.on_sniper()

                    elif self._is_pressed(self.VK_V) and (now - self._last_trigger[self.VK_V] > debounce):
                        self._last_trigger[self.VK_V] = now
                        if self.on_audio:
                            self.on_audio()

                    elif self._is_pressed(self.VK_C) and (now - self._last_trigger[self.VK_C] > debounce):
                        self._last_trigger[self.VK_C] = now
                        if self.on_crypto:
                            self.on_crypto()

                    elif self._is_pressed(self.VK_LEFT) and (now - self._last_trigger[self.VK_LEFT] > 0.28):
                        self._last_trigger[self.VK_LEFT] = now
                        if self.on_history_prev:
                            self.on_history_prev()

                    elif self._is_pressed(self.VK_RIGHT) and (now - self._last_trigger[self.VK_RIGHT] > 0.28):
                        self._last_trigger[self.VK_RIGHT] = now
                        if self.on_history_next:
                            self.on_history_next()

                time.sleep(0.04)
            except Exception:
                time.sleep(0.1)
