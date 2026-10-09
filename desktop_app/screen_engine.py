import io
import os
import sys
import json
import time
import threading
from PIL import Image, ImageGrab

try:
    from .ai_providers import MultiAIProvider
    from .auth_manager import AuthManager, get_app_dir
    from .audio_capture import record_system_audio_wav
    from .crypto_market import fetch_crypto_ticker, fetch_top_crypto_summary
except (ImportError, ValueError):
    from ai_providers import MultiAIProvider
    from auth_manager import AuthManager, get_app_dir
    try:
        from audio_capture import record_system_audio_wav
    except ImportError:
        record_system_audio_wav = None
    try:
        from crypto_market import fetch_crypto_ticker, fetch_top_crypto_summary
    except ImportError:
        fetch_crypto_ticker = None
        fetch_top_crypto_summary = None

DEFAULT_GEMINI_KEY = ""

class ScreenEngine:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(get_app_dir(), "config.json")
        self.config_path = config_path
        self.auth = AuthManager()
        
        saved_provider, saved_keys = self.load_config()
        self.ai = MultiAIProvider(provider_id=saved_provider, keys_dict=saved_keys)
        
        self.is_running = False
        self.is_auto = True
        self.interval = 4.5
        
        # Режимы работы: 'study' (учёба/тесты/игры) или 'crypto' (крипто-радар/трейдинг)
        self.app_mode = "study"
        
        # История ответов для листания (вперед / назад)
        self.history = []
        self.history_index = -1
        
        self.latest_game = ""
        self.latest_answer = ""
        self.latest_summary = "Ожидание первого анализа экрана..."
        self.latest_crypto = ""
        self.latest_ticker = "BTC, ETH, SOL, TON — мониторинг онлайн"
        self.last_update_time = "—"
        self.status = "Готов к работе"
        
        self.listeners = []
        self._thread = None
        self._analyzing_lock = threading.Lock()
        self._last_screen_thumb = None
        self._last_analysis_time = 0

        # Фоновая подгрузка котировок топ-криптовалют
        if fetch_top_crypto_summary:
            threading.Thread(target=self._fetch_top_tickers, daemon=True).start()

    def load_config(self):
        keys = {"gemini": DEFAULT_GEMINI_KEY}
        provider = "gemini"
        paths_to_check = [self.config_path, "config.json"]
        for p in paths_to_check:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        provider = data.get("current_provider", "gemini")
                        loaded_keys = data.get("keys", {})
                        if "gemini_api_key" in data and "gemini" not in loaded_keys:
                            loaded_keys["gemini"] = data["gemini_api_key"]
                        for k, v in loaded_keys.items():
                            if v and v.strip():
                                keys[k] = v.strip()
                        break
                except Exception:
                    pass
        return provider, keys

    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({
                    "current_provider": self.ai.current_provider,
                    "keys": self.ai.keys
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения config: {e}")

    def add_listener(self, callback):
        self.listeners.append(callback)

    def notify_listeners(self):
        curr_idx = len(self.history) if self.history_index == -1 else self.history_index + 1
        data = {
            "game_info": self.latest_game,
            "answer": self.latest_answer,
            "summary": self.latest_summary,
            "crypto_signal": self.latest_crypto,
            "crypto_ticker": self.latest_ticker,
            "app_mode": self.app_mode,
            "history_count": len(self.history),
            "history_current": curr_idx,
            "history_is_latest": (self.history_index == -1 or self.history_index == len(self.history) - 1),
            "status": self.status,
            "last_update": self.last_update_time,
            "is_auto": self.is_auto,
            "provider_name": self.ai.PROVIDERS[self.ai.current_provider]["name"],
            "provider_badge": self.ai.PROVIDERS[self.ai.current_provider]["badge"],
            "is_pro": self.auth.is_pro,
            "remaining_quota": self.auth.get_remaining_requests()
        }
        for cb in self.listeners:
            try:
                cb(data)
            except Exception as e:
                print(f"Ошибка вызова listener: {e}")

    def add_history_entry(self, entry_type, answer="", summary="", game_info="", crypto_info=""):
        """Добавляет ответ в историю для возможности листания назад/вперед"""
        if not answer and not summary and not crypto_info:
            return
        item = {
            "time": time.strftime("%H:%M:%S"),
            "type": entry_type,
            "answer": answer,
            "summary": summary,
            "game_info": game_info,
            "crypto_info": crypto_info
        }
        self.history.append(item)
        if len(self.history) > 60:
            self.history.pop(0)
        self.history_index = -1

    def history_prev(self):
        """Листать историю: предыдущий ответ ИИ"""
        if not self.history:
            return
        if self.history_index == -1:
            self.history_index = max(0, len(self.history) - 2)
        else:
            self.history_index = max(0, self.history_index - 1)
        self._load_history_item(self.history_index)

    def history_next(self):
        """Листать историю: следующий ответ ИИ (к свежему)"""
        if not self.history:
            return
        if self.history_index == -1 or self.history_index >= len(self.history) - 1:
            self.history_index = -1
            self._load_history_item(len(self.history) - 1)
        else:
            self.history_index += 1
            if self.history_index >= len(self.history) - 1:
                self.history_index = -1
                self._load_history_item(len(self.history) - 1)
            else:
                self._load_history_item(self.history_index)

    def history_latest(self):
        """Вернуться к самому последнему ответу"""
        if not self.history:
            return
        self.history_index = -1
        self._load_history_item(len(self.history) - 1)

    def _load_history_item(self, idx):
        if 0 <= idx < len(self.history):
            item = self.history[idx]
            self.latest_answer = item.get("answer", "")
            self.latest_summary = item.get("summary", "")
            self.latest_game = item.get("game_info", "")
            self.latest_crypto = item.get("crypto_info", "")
            self.status = f"● Ответ {idx+1} из {len(self.history)} ({item.get('time', '')})"
            self.notify_listeners()

    def toggle_app_mode(self):
        """Переключение режимов: 🎓 Учёба/Тесты <-> 📈 Крипто-Радар"""
        self.app_mode = "crypto" if self.app_mode == "study" else "study"
        if self.app_mode == "crypto":
            self.status = "📈 Режим: Крипто-Радар активирован"
            threading.Thread(target=self._fetch_top_tickers, daemon=True).start()
        else:
            self.status = "🎓 Режим: Учёба и Тесты активирован"
        self.notify_listeners()
        return self.app_mode

    def _fetch_top_tickers(self):
        if fetch_top_crypto_summary:
            top = fetch_top_crypto_summary()
            if top:
                self.latest_ticker = top
                self.notify_listeners()

    def analyze_crypto(self, user_query=""):
        """Анализ крипто-графика с экрана + биржевые котировки"""
        def _worker():
            self.status = "📈 Сканирую график крипты..."
            self.notify_listeners()

            # Если пользователь указал монету (например BTC, SOL), получаем живую котировку
            if fetch_crypto_ticker and user_query:
                t_data = fetch_crypto_ticker(user_query)
                if t_data.get("ok"):
                    self.latest_ticker = f"🪙 {t_data['pair']}: {t_data['price']} ({t_data['change']}) | 24h: {t_data['high']} / {t_data['low']}"
                    self.notify_listeners()

            try:
                jpeg_bytes = self.capture_screen_jpeg()
            except Exception:
                jpeg_bytes = None

            if jpeg_bytes:
                res = self.ai.analyze_crypto_chart(jpeg_bytes, user_notes=user_query)
                if res["ok"]:
                    text = res["text"]
                    self.latest_crypto = text
                    self.latest_answer = text
                    self._last_manual_q_time = time.time() + 15
                    self.status = "● Крипто-сигнал готов!"
                    self.add_history_entry("Крипто-сигнал", answer=text, crypto_info=text)
                else:
                    self.status = f"Ошибка: {res['error']}"

            self.last_update_time = time.strftime("%H:%M:%S")
            self.notify_listeners()

        threading.Thread(target=_worker, daemon=True).start()

    def capture_screen_jpeg(self):
        screenshot = ImageGrab.grab()
        width, height = screenshot.size
        target_width = 1280
        scale = target_width / max(width, 1)
        target_height = int(height * scale)
        resized = screenshot.resize((target_width, target_height))
        
        buffer = io.BytesIO()
        resized.save(buffer, format="JPEG", quality=75)
        return buffer.getvalue()

    def analyze_now(self):
        if self.app_mode == "crypto":
            self.analyze_crypto()
        else:
            threading.Thread(target=lambda: self._run_analysis(force=True), daemon=True).start()

    def analyze_clipboard(self):
        """Анализ изображения из буфера обмена Windows (после Win+Shift+S или копирования картинки)"""
        def _worker():
            try:
                im = ImageGrab.grabclipboard()
                if im is None:
                    self.status = "Буфер обмена пуст"
                    self.latest_answer = "⚠️ В буфере обмена нет картинки.\nСделайте снимок (Win+Shift+S) или скопируйте изображение и повторите."
                    self.notify_listeners()
                    return

                if isinstance(im, list):
                    if im and os.path.exists(im[0]):
                        im = Image.open(im[0])
                    else:
                        self.status = "Файл в буфере не найден"
                        self.notify_listeners()
                        return

                if isinstance(im, Image.Image):
                    if im.mode in ("RGBA", "P"):
                        im = im.convert("RGB")
                    buf = io.BytesIO()
                    im.save(buf, format="JPEG", quality=85)
                    self.analyze_custom_image(buf.getvalue(), label="Буфер (Win+Shift+S)")
            except Exception as e:
                self.status = f"Ошибка буфера: {str(e)[:40]}"
                self.notify_listeners()

        threading.Thread(target=_worker, daemon=True).start()

    def analyze_custom_image(self, image_bytes, user_query="", label="Изображение", mode=None):
        """Анализ произвольного изображения (из файла, буфера или веб-панели)"""
        target_mode = mode if mode else self.app_mode
        self.status = f"● Анализ ({label})..."
        self.notify_listeners()

        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            max_dim = max(img.size)
            if max_dim > 1600:
                scale = 1600.0 / max_dim
                img = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
            
            out_buf = io.BytesIO()
            img.save(out_buf, format="JPEG", quality=80)
            jpeg_bytes = out_buf.getvalue()

            if target_mode == "crypto":
                res = self.ai.analyze_crypto_chart(jpeg_bytes, user_notes=user_query)
            else:
                res = self.ai.analyze_image(jpeg_bytes)

            if res["ok"]:
                text = res["text"]
                self._process_ai_response(text)
                self.auth.use_request()
                self.status = f"● Анализ ({label}) готов!"
                self.last_update_time = time.strftime("%H:%M:%S")
                self.notify_listeners()
                return {
                    "ok": True,
                    "answer": self.latest_answer,
                    "summary": self.latest_summary,
                    "crypto_signal": self.latest_crypto,
                    "game_info": self.latest_game,
                    "status": self.status
                }
            else:
                self.status = f"Ошибка: {res['error']}"
                self.notify_listeners()
                return {"ok": False, "error": res["error"]}
        except Exception as e:
            self.status = f"Ошибка обработки: {str(e)[:40]}"
            self.notify_listeners()
            return {"ok": False, "error": str(e)}

    def analyze_uploaded_image(self, image_bytes, user_query="", mode=None):
        """Алиас для обратной совместимости с веб-сервером"""
        return self.analyze_custom_image(image_bytes, user_query=user_query, label="Загрузка", mode=mode)

    def ask_quick_question(self, question_text):
        """Быстрый вопрос к ИИ (с захватом текущего экрана для контекста)"""
        def _worker():
            self.status = "● Решаю вопрос по экрану..."
            self.notify_listeners()
            try:
                jpeg_bytes = self.capture_screen_jpeg()
            except Exception:
                jpeg_bytes = None
            res = self.ai.ask_quick_question(question_text, jpeg_bytes=jpeg_bytes)
            if res["ok"]:
                self.latest_answer = f"❓ {question_text}\n💡 {res['text']}"
                self._last_manual_q_time = time.time()
                self.status = "● Ответ готов!"
                self.add_history_entry("Вопрос", answer=self.latest_answer)
            else:
                self.status = f"Ошибка: {res['error']}"
            self.last_update_time = time.strftime("%H:%M:%S")
            self.notify_listeners()

        # Если в вопросе упомянута криптовалюта, сразу подтягиваем живую котировку
        if fetch_crypto_ticker:
            q_clean = question_text.lower().replace("курс", "").replace("цена", "").replace("прогноз", "").strip()
            for part in q_clean.split():
                if part in ["btc", "eth", "sol", "ton", "doge", "xrp", "bnb", "pepe", "not", "sui", "near", "биток", "эфир", "солана", "тон"]:
                    t_data = fetch_crypto_ticker(part)
                    if t_data.get("ok"):
                        self.latest_ticker = f"🪙 {t_data['pair']}: {t_data['price']} ({t_data['change']}) | Max: {t_data['high']} Min: {t_data['low']}"
                        self.notify_listeners()
                    break

        threading.Thread(target=_worker, daemon=True).start()

    def listen_and_answer(self, duration_sec=5.5):
        """
        Захват звука из наушников/колонок (учитель/видео) + экран
        """
        def _worker():
            if not record_system_audio_wav:
                self.status = "Ошибка: модуль звука недоступен"
                self.notify_listeners()
                return

            self.status = "🎙️ Слушаю звук (5 сек)..."
            self.notify_listeners()

            wav_bytes, src_info = record_system_audio_wav(duration_sec=duration_sec)
            if not wav_bytes:
                self.status = f"⚠️ {src_info}"
                self.latest_answer = f"🎙️ {src_info}\n(Включите звук в видеоролике или конференции Zoom/Discord)"
                self.notify_listeners()
                return

            self.status = f"● Распознаю ({src_info})..."
            self.notify_listeners()

            try:
                jpeg_bytes = self.capture_screen_jpeg()
            except Exception:
                jpeg_bytes = None

            res = self.ai.analyze_audio_and_screen(wav_bytes, jpeg_bytes)
            if res["ok"]:
                text = res["text"]
                self.latest_answer = f"🎙️ {src_info}:\n{text}"
                self._last_manual_q_time = time.time() + 15
                self.status = "● Голосовой суфлер готов!"
                self.add_history_entry("Голос", answer=self.latest_answer)
            else:
                self.status = f"Ошибка: {res['error']}"

            self.last_update_time = time.strftime("%H:%M:%S")
            self.notify_listeners()

        threading.Thread(target=_worker, daemon=True).start()

    def analyze_region(self, jpeg_bytes):
        """
        Снайперский анализ конкретно выделенной области экрана
        """
        def _worker():
            self.status = "🎯 Снайперский анализ..."
            self.notify_listeners()

            res = self.ai.analyze_sniper_region(jpeg_bytes)
            if res["ok"]:
                self.latest_answer = f"🎯 ВЫДЕЛЕННАЯ ОБЛАСТЬ:\n{res['text']}"
                self._last_manual_q_time = time.time() + 15
                self.status = "● Задача решена!"
                self.add_history_entry("Снайпер", answer=self.latest_answer)
            else:
                self.status = f"Ошибка: {res['error']}"

            self.last_update_time = time.strftime("%H:%M:%S")
            self.notify_listeners()

        threading.Thread(target=_worker, daemon=True).start()

    def _run_analysis(self, force=False):
        if not self._analyzing_lock.acquire(blocking=False):
            return

        try:
            screenshot = ImageGrab.grab()
            # Умная проверка изменения экрана (сравнение компактного 32x24 хэша)
            thumb = screenshot.resize((32, 24)).convert("L").tobytes()
            now = time.time()
            if not force and self._last_screen_thumb == thumb and (now - self._last_analysis_time < 30):
                # Экран полностью статичен, экономим трафик и токены
                return

            current_badge = self.ai.PROVIDERS[self.ai.current_provider]["badge"]
            self.status = f"● Анализ ({current_badge})..."
            self.notify_listeners()

            width, height = screenshot.size
            target_width = 1280
            scale = target_width / max(width, 1)
            target_height = int(height * scale)
            resized = screenshot.resize((target_width, target_height))
            buffer = io.BytesIO()
            resized.save(buffer, format="JPEG", quality=75)
            jpeg_bytes = buffer.getvalue()

            res = self.ai.analyze_image(jpeg_bytes)
            self._last_screen_thumb = thumb
            self._last_analysis_time = now

            if res["ok"]:
                text = res["text"]
                self._process_ai_response(text)
                self.auth.use_request()
                self.status = f"● Готово ({current_badge})"
            else:
                self.status = f"{res['error'][:60]}"

            self.last_update_time = time.strftime("%H:%M:%S")
            self.notify_listeners()
        except Exception as e:
            self.status = f"Сбой: {str(e)[:50]}"
            self.notify_listeners()
        finally:
            self._analyzing_lock.release()

    def _process_ai_response(self, text):
        if "[CRYPTO_SIGNAL]:" in text:
            crypto_chunk = text.split("[CRYPTO_SIGNAL]:")[1]
            for stop_tag in ["[GAME_INFO]:", "[TEST_ANSWER]:", "[SUMMARY]:"]:
                if stop_tag in crypto_chunk:
                    crypto_chunk = crypto_chunk.split(stop_tag)[0]
            self.latest_crypto = crypto_chunk.strip()
            self.latest_answer = self.latest_crypto

        if "[GAME_INFO]:" in text:
            game_chunk = text.split("[GAME_INFO]:")[1]
            for stop_tag in ["[TEST_ANSWER]:", "[SUMMARY]:", "[CRYPTO_SIGNAL]:"]:
                if stop_tag in game_chunk:
                    game_chunk = game_chunk.split(stop_tag)[0]
            self.latest_game = game_chunk.strip()
        else:
            self.latest_game = ""

        if "[TEST_ANSWER]:" in text:
            ans_chunk = text.split("[TEST_ANSWER]:")[1]
            for stop_tag in ["[GAME_INFO]:", "[SUMMARY]:", "[CRYPTO_SIGNAL]:"]:
                if stop_tag in ans_chunk:
                    ans_chunk = ans_chunk.split(stop_tag)[0]
            ans_clean = ans_chunk.strip()
            # Не перезаписываем свежий ответ на личный вопрос в течение 12 секунд
            recent_manual = (time.time() - getattr(self, "_last_manual_q_time", 0)) < 12
            if ans_clean and not ans_clean.startswith("<") and not recent_manual:
                self.latest_answer = ans_clean

        if "[SUMMARY]:" in text:
            sum_chunk = text.split("[SUMMARY]:")[1]
            for stop_tag in ["[GAME_INFO]:", "[TEST_ANSWER]:", "[CRYPTO_SIGNAL]:"]:
                if stop_tag in sum_chunk:
                    sum_chunk = sum_chunk.split(stop_tag)[0]
            self.latest_summary = sum_chunk.strip()
        elif not self.latest_game and "[TEST_ANSWER]:" not in text and "[CRYPTO_SIGNAL]:" not in text and text.strip():
            self.latest_summary = text.strip()

        # Сохранение в историю для листания
        self.add_history_entry(
            entry_type="Крипто" if self.latest_crypto else "Анализ",
            answer=self.latest_answer,
            summary=self.latest_summary,
            game_info=self.latest_game,
            crypto_info=self.latest_crypto
        )

    def start_loop(self):
        self.is_running = True
        self._thread = threading.Thread(target=self._loop_worker, daemon=True)
        self._thread.start()

    def _loop_worker(self):
        while self.is_running:
            if self.is_auto:
                self._run_analysis()
            time.sleep(self.interval)

    def stop(self):
        self.is_running = False
