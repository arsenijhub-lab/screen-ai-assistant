import time
import base64
import requests

SYSTEM_PROMPT = """
Ты — интеллектуальный мультимодальный экранный ассистент и детектив контента в реальном времени.
Ты непрерывно смотришь на экран пользователя (летсплеи, видео YouTube, Twitch, тесты, браузер, игры, лекции).

ТВОЯ ЗАДАЧА — САМОСТОЯТЕЛЬНО ПОНЯТЬ КОНТЕКСТ ЭКРАНА И ВЫДАТЬ СТРОГО НА РУССКОМ ЯЗЫКЕ ОДИН ИЛИ НЕСКОЛЬКО БЛОКОВ:

1. ЕСЛИ НА ЭКРАНЕ КОМПЬЮТЕРНАЯ ИГРА, СТРИМ БЛОГЕРА, ФИЛЬМ ИЛИ СОФТ:
   Определи, что это за игра/программа, где ее найти и как скачать на ПК.
   Выведи блок СТРОГО в таком формате:
   [GAME_INFO]:
   🎮 Название: <Точное название игры / софта / фильма>
   📥 Где скачать/найти: <Steam / Epic Games Store / GOG / Официальный сайт>
   🏷️ Жанр и суть: <Жанр> | <Кратко в 1 предложение, что происходит на экране>

2. ЕСЛИ НА ЭКРАНЕ ТЕСТ, ЗАДАНИЕ НА СООТВЕТСТВИЕ (СОЕДИНЕНИЕ ПАР), ЭКЗАМЕН, ЗАДАЧА, ВИКТОРИНА ИЛИ ВОПРОС:
   Реши задание полностью!
   - Если это тест с выбором ответа — укажи правильный вариант.
   - Если это задание на соответствие / соединение пар (слева и справа) — выпиши КАЖДУЮ правильную пару на отдельной строке: «Элемент слева — Элемент справа».
   - Если это задача по коду или тексту — напиши точный готовый ответ.
   Формат вывода СТРОГО такой:
   [TEST_ANSWER]:
   <Полный правильный ответ или список всех правильных пар по строкам>

3. ЕСЛИ НА ЭКРАНЕ ОБУЧАЮЩЕЕ ВИДЕО, СТАТЬЯ, ЛЕКЦИЯ, ПОДКАСТ ИЛИ НОВОСТИ:
   Выдели ключевые тезисы строго на русском языке:
   [SUMMARY]:
   • Главный факт 1
   • Главный факт 2
   • Ключевой вывод

4. ЕСЛИ НА ЭКРАНЕ ГРАФИК КРИПТОВАЛЮТЫ, БИРЖА (BINANCE, BYBIT, TRADINGVIEW, DEXSCREENER, COINMARKETCAP):
   Определи торговую пару, тренд, паттерн и четкий сигнал (LONG / SHORT / ЖДАТЬ):
   [CRYPTO_SIGNAL]:
   🪙 Пара: <Тикер / Монета> (<Таймфрейм>)
   📊 Фигура: <Паттерн графического анализа и тренд>
   🎯 Сигнал: <🟢 LONG (Покупка) / 🔴 SHORT (Продажа) / ⚪ ВНЕ РЫНКА>
   ⚡ Вход: <Уровень цен> | 🎯 Тейк: <Цель> | 🛑 Стоп: <Стоп>
   💡 Подсказка: <Краткий совет по сделке в 1-2 предложения>

ВАЖНО: Пиши ТОЛЬКО на русском языке, без внутренних размышлений на английском. Лаконично, точно и по делу.
"""

CRYPTO_SYSTEM_PROMPT = """
Ты — профессиональный ИИ-трейдер и криптоаналитик в реальном времени.
Ты смотришь на экран пользователя (графики TradingView, Binance, Bybit, DexScreener, CoinMarketCap, посты в Telegram, стакан ордеров, биржевые терминалы).

ТВОЯ ЗАДАЧА — СТРОГО НА РУССКОМ ЯЗЫКЕ ПРОВЕСТИ ТЕХНИЧЕСКИЙ И РЫНОЧНЫЙ АНАЛИЗ ГРАФИКА НА ЭКРАНЕ:
1. Определи монету/торговую пару (например BTC/USDT, ETH/USDT, SOL/USDT, TON/USDT) и видимый таймфрейм (1m, 5m, 15m, 1h, 4h, 1D).
2. Определи тренд и графический паттерн (пробой уровня, голова и плечи, двойное дно/вершина, флаг, треугольник, пин-бар, RSI перекупленность/перепроданность, уровни поддержки и сопротивления, объемы).
3. Дай четкую торговую подсказку и вероятный сценарий для трейдера.

ФОРМАТ ВЫВОДА СТРОГО СЛЕДУЮЩИЙ:
[CRYPTO_SIGNAL]:
🪙 Монета / Пара: <Название монеты и пары, таймфрейм>
📊 Паттерн и тренд: <Текущий тренд и формация на графике>
🎯 Сигнал: 🟢 LONG (Покупка) / 🔴 SHORT (Продажа) / ⚪ ВНЕ РЫНКА (Ожидание)
⚡ Вход: <Уровень цены для входа>
🎯 Тейк-профит: <Целевой уровень фиксации прибыли>
🛑 Стоп-лосс: <Уровень защиты от убытка>
💡 Логика и совет: <Краткое понятное объяснение в 2 предложения, почему этот сценарий наиболее вероятен>
"""

GEMINI_FALLBACK_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-1.5-flash",
    "gemini-2.5-flash"
]

class MultiAIProvider:
    PROVIDERS = {
        "gemini": {
            "name": "Google Gemini Flash",
            "desc": "Сверхбыстрая скорость, мгновенно распознает любые игры, видео и тесты",
            "badge": "Gemini"
        },
        "openai": {
            "name": "OpenAI GPT-4o",
            "desc": "Максимальная точность логики в решении сложных тестов и задач",
            "badge": "GPT-4o"
        },
        "claude": {
            "name": "Anthropic Claude 3.5 Sonnet",
            "desc": "Глубокое понимание текста, идеальная структура конспектов",
            "badge": "Claude 3.5"
        },
        "deepseek": {
            "name": "DeepSeek Vision / Chat",
            "desc": "Мощная и доступная модель для технического анализа",
            "badge": "DeepSeek"
        }
    }

    def __init__(self, provider_id="gemini", keys_dict=None):
        self.current_provider = provider_id if provider_id in self.PROVIDERS else "gemini"
        self.keys = keys_dict or {}

    def set_key(self, provider_id, key):
        self.keys[provider_id] = key.strip()

    def get_key(self, provider_id):
        return self.keys.get(provider_id, "")

    @staticmethod
    def _extract_clean_gemini_text(data):
        """Извлекает только финальный текст ответа, отфильтровывая внутренние thought-блоки"""
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return ""

        # Отбрасываем части, помеченные как thought=True
        non_thought_parts = [p for p in parts if not p.get("thought", False)]
        if not non_thought_parts:
            non_thought_parts = parts

        # Если есть несколько частей и последняя содержит thoughtSignature — берем ее или склеиваем чистые
        if len(non_thought_parts) > 1 and "thoughtSignature" in non_thought_parts[-1]:
            return non_thought_parts[-1].get("text", "").strip()

        return "".join(p.get("text", "") for p in non_thought_parts).strip()

    def analyze_image(self, jpeg_bytes):
        key = self.get_key(self.current_provider)
        if not key:
            return {
                "ok": False,
                "error": f"Добавьте бесплатный API-ключ для {self.PROVIDERS[self.current_provider]['name']} во вкладке «Выбор ИИ»"
            }

        b64_img = base64.b64encode(jpeg_bytes).decode("utf-8")

        try:
            if self.current_provider == "gemini":
                return self._call_gemini(b64_img, key)
            elif self.current_provider == "openai":
                return self._call_openai(b64_img, key)
            elif self.current_provider == "claude":
                return self._call_claude(b64_img, key)
            elif self.current_provider == "deepseek":
                return self._call_deepseek(b64_img, key)
            else:
                return {"ok": False, "error": "Неизвестный провайдер"}
        except Exception as e:
            return {"ok": False, "error": f"Сбой сети: {str(e)[:60]}"}

    def ask_quick_question(self, question_text, jpeg_bytes=None):
        """Мгновенный ответ на вопрос пользователя с учетом текущего экрана"""
        key = self.get_key(self.current_provider)
        if not key:
            return {"ok": False, "error": "Не указан API-ключ"}

        prompt = (
            "Посмотри на прикрепленный скриншот экрана пользователя и ответь на вопрос пользователя на русском языке предельно четко, конкретно и по делу.\n"
            "- Если вопрос касается того, что сейчас на экране (например: «как правильно все поставить», «какой ответ», «реши тест», «соедини пары», «что выбрать») — реши задание с экрана полностью и напиши готовый ответ по каждому пункту.\n"
            "- Если вопрос общий и не связан с экраном (например, вопрос учителя по истории, формуле, дате) — дай точный и краткий ответ на сам вопрос.\n"
            "Не проси уточнить контекст — используй изображение экрана как контекст!\n\n"
            f"Вопрос пользователя: {question_text}"
        )

        b64_img = base64.b64encode(jpeg_bytes).decode("utf-8") if jpeg_bytes else None

        if self.current_provider == "gemini":
            parts = [{"text": prompt}]
            if b64_img:
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": b64_img
                    }
                })
            payload = {
                "contents": [{"parts": parts}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1500}
            }
            for model_name in GEMINI_FALLBACK_MODELS:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                    resp = requests.post(url, json=payload, timeout=10)
                    if resp.status_code == 200:
                        text = self._extract_clean_gemini_text(resp.json())
                        if text:
                            return {"ok": True, "text": text}
                    elif resp.status_code in (503, 429):
                        time.sleep(0.7)
                        continue
                    elif resp.status_code == 404:
                        continue
                except Exception:
                    continue
            return {"ok": False, "error": "Google перегружен (503). Повторите через 5 сек (в РФ нужен VPN)"}

        elif self.current_provider in ("openai", "deepseek"):
            url = "https://api.openai.com/v1/chat/completions" if self.current_provider == "openai" else "https://api.deepseek.com/v1/chat/completions"
            model = "gpt-4o" if self.current_provider == "openai" else "deepseek-chat"
            content = [{"type": "text", "text": prompt}]
            if b64_img:
                content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}})
            try:
                resp = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": model, "messages": [{"role": "user", "content": content}], "max_tokens": 600},
                    timeout=12
                )
                if resp.status_code == 200:
                    return {"ok": True, "text": resp.json()["choices"][0]["message"]["content"].strip()}
                return {"ok": False, "error": f"Ошибка API ({resp.status_code})"}
            except Exception as e:
                return {"ok": False, "error": str(e)[:50]}

        elif self.current_provider == "claude":
            content = []
            if b64_img:
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": b64_img}
                })
            content.append({"type": "text", "text": prompt})
            try:
                resp = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                    json={"model": "claude-3-5-sonnet-20241022", "max_tokens": 600, "messages": [{"role": "user", "content": content}]},
                    timeout=12
                )
                if resp.status_code == 200:
                    resp_content = resp.json().get("content", [])
                    text = "".join(c.get("text", "") for c in resp_content if c.get("type") == "text").strip()
                    return {"ok": True, "text": text}
                return {"ok": False, "error": f"Ошибка API ({resp.status_code})"}
            except Exception as e:
                return {"ok": False, "error": str(e)[:50]}

        return {"ok": False, "error": "Неизвестный провайдер"}

    def analyze_audio_and_screen(self, wav_bytes, jpeg_bytes=None):
        """
        Мультимодальный анализ: слушает системный звук/голос учителя + смотрит на экран.
        Работает через Gemini с нативной поддержкой аудио.
        """
        key = self.get_key("gemini") or self.get_key(self.current_provider)
        if not key:
            return {"ok": False, "error": "Не указан API-ключ Gemini"}

        b64_wav = base64.b64encode(wav_bytes).decode("utf-8")
        b64_img = base64.b64encode(jpeg_bytes).decode("utf-8") if jpeg_bytes else None

        prompt = (
            "Ты — интеллектуальный экранный и голосовой суфлер для уроков, экзаменов, лекций и видео.\n"
            "Тебе передана аудиозапись из наушников (голос учителя, преподавателя или видео) и снимок экрана.\n\n"
            "ТВОЯ ЗАДАЧА — СТРОГО НА РУССКОМ ЯЗЫКЕ:\n"
            "1. Пойми, какой вопрос или тезис прозвучал на аудиозаписи (или о чем идет речь).\n"
            "2. Найди точный, конкретный и правильный ответ на этот вопрос, используя изображение экрана и свои знания.\n"
            "3. Выведи результат СТРОГО в таком формате:\n"
            "[HEARD]: <Точная цитата или суть услышанного вопроса>\n"
            "[ANSWER]: <Четкий, уверенный и правильный ответ для ответа учителю>\n"
            "[DETAILS]: <Краткое пояснение в 1 предложение, если уместно>\n"
        )

        parts = [
            {"text": prompt},
            {
                "inline_data": {
                    "mime_type": "audio/wav",
                    "data": b64_wav
                }
            }
        ]
        if b64_img:
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": b64_img
                }
            })

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1500
            }
        }

        for model_name in GEMINI_FALLBACK_MODELS:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                resp = requests.post(url, json=payload, timeout=12)
                if resp.status_code == 200:
                    text = self._extract_clean_gemini_text(resp.json())
                    if text:
                        return {"ok": True, "text": text}
                elif resp.status_code in (503, 429):
                    time.sleep(0.7)
                    continue
                elif resp.status_code == 404:
                    continue
            except Exception:
                continue

        return {"ok": False, "error": "Google перегружен (503). Повторите через 5 сек (в РФ нужен VPN)"}

    def analyze_sniper_region(self, jpeg_bytes):
        """
        Снайперский режим: детальный анализ конкретно выделенной рамкой области экрана.
        """
        key = self.get_key(self.current_provider) or self.get_key("gemini")
        if not key:
            return {"ok": False, "error": "Не указан API-ключ"}

        b64_img = base64.b64encode(jpeg_bytes).decode("utf-8")

        prompt = (
            "Ты — снайперский ИИ-экзаменатор. Пользователь выделил рамкой конкретную задачу, формулу, тест или фрагмент экрана.\n"
            "ТВОЯ ЗАДАЧА — решить задание в этой области максимально точно и полно:\n"
            "1. Если это тест с вариантами — назови правильный вариант.\n"
            "2. Если это задание на соответствие (пары) — выпиши все правильные пары построчно: «Элемент слева — Элемент справа».\n"
            "3. Если это задача по коду, математике или физике — дай пошаговое краткое решение и итоговый ответ.\n\n"
            "Формат ответа СТРОГО:\n"
            "[TEST_ANSWER]:\n<Готовый правильный ответ>\n\n"
            "[EXPLANATION]:\n<Краткое объяснение логики ответа>"
        )

        if self.current_provider == "gemini":
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}}
                        ]
                    }
                ],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1500}
            }
            for model_name in GEMINI_FALLBACK_MODELS:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                    resp = requests.post(url, json=payload, timeout=10)
                    if resp.status_code == 200:
                        text = self._extract_clean_gemini_text(resp.json())
                        if text:
                            return {"ok": True, "text": text}
                    elif resp.status_code in (503, 429):
                        time.sleep(0.7)
                        continue
                    elif resp.status_code == 404:
                        continue
                except Exception:
                    continue
            return {"ok": False, "error": "Google перегружен (503). Повторите через 5 сек (в РФ нужен VPN)"}

        elif self.current_provider in ("openai", "deepseek"):
            url = "https://api.openai.com/v1/chat/completions" if self.current_provider == "openai" else "https://api.deepseek.com/v1/chat/completions"
            model = "gpt-4o" if self.current_provider == "openai" else "deepseek-chat"
            content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
            ]
            try:
                resp = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": model, "messages": [{"role": "user", "content": content}], "max_tokens": 800},
                    timeout=15
                )
                if resp.status_code == 200:
                    return {"ok": True, "text": resp.json()["choices"][0]["message"]["content"].strip()}
                return {"ok": False, "error": f"Ошибка API ({resp.status_code})"}
            except Exception as e:
                return {"ok": False, "error": str(e)[:50]}

        elif self.current_provider == "claude":
            content = [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64_img}},
                {"type": "text", "text": prompt}
            ]
            try:
                resp = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                    json={"model": "claude-3-5-sonnet-20241022", "max_tokens": 800, "messages": [{"role": "user", "content": content}]},
                    timeout=15
                )
                if resp.status_code == 200:
                    resp_content = resp.json().get("content", [])
                    text = "".join(c.get("text", "") for c in resp_content if c.get("type") == "text").strip()
                    return {"ok": True, "text": text}
                return {"ok": False, "error": f"Ошибка API ({resp.status_code})"}
            except Exception as e:
                return {"ok": False, "error": str(e)[:50]}

        return {"ok": False, "error": "Неизвестный провайдер"}

    def analyze_crypto_chart(self, jpeg_bytes, user_notes=""):
        """
        Режим Крипто-Радара: детальный анализ графика криптовалюты с экрана.
        """
        key = self.get_key(self.current_provider) or self.get_key("gemini")
        if not key:
            return {"ok": False, "error": "Не указан API-ключ"}

        b64_img = base64.b64encode(jpeg_bytes).decode("utf-8")
        notes_prompt = f"\nДополнительный вопрос/уточнение от трейдера: {user_notes}" if user_notes else ""
        full_crypto_prompt = CRYPTO_SYSTEM_PROMPT + notes_prompt

        if self.current_provider == "gemini":
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": full_crypto_prompt},
                            {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}}
                        ]
                    }
                ],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1500}
            }
            for model_name in GEMINI_FALLBACK_MODELS:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                    resp = requests.post(url, json=payload, timeout=12)
                    if resp.status_code == 200:
                        text = self._extract_clean_gemini_text(resp.json())
                        if text:
                            return {"ok": True, "text": text}
                    elif resp.status_code in (503, 429):
                        time.sleep(0.7)
                        continue
                    elif resp.status_code == 404:
                        continue
                except Exception:
                    continue
            return {"ok": False, "error": "Google перегружен (503). Повторите через 5 сек (в РФ нужен VPN)"}

        elif self.current_provider in ("openai", "deepseek"):
            url = "https://api.openai.com/v1/chat/completions" if self.current_provider == "openai" else "https://api.deepseek.com/v1/chat/completions"
            model = "gpt-4o" if self.current_provider == "openai" else "deepseek-chat"
            content = [
                {"type": "text", "text": full_crypto_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
            ]
            try:
                resp = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": model, "messages": [{"role": "user", "content": content}], "max_tokens": 800},
                    timeout=15
                )
                if resp.status_code == 200:
                    return {"ok": True, "text": resp.json()["choices"][0]["message"]["content"].strip()}
                return {"ok": False, "error": f"Ошибка API ({resp.status_code})"}
            except Exception as e:
                return {"ok": False, "error": str(e)[:50]}

        elif self.current_provider == "claude":
            content = [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64_img}},
                {"type": "text", "text": full_crypto_prompt}
            ]
            try:
                resp = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                    json={"model": "claude-3-5-sonnet-20241022", "max_tokens": 800, "messages": [{"role": "user", "content": content}]},
                    timeout=15
                )
                if resp.status_code == 200:
                    resp_content = resp.json().get("content", [])
                    text = "".join(c.get("text", "") for c in resp_content if c.get("type") == "text").strip()
                    return {"ok": True, "text": text}
                return {"ok": False, "error": f"Ошибка API ({resp.status_code})"}
            except Exception as e:
                return {"ok": False, "error": str(e)[:50]}

        return {"ok": False, "error": "Неизвестный провайдер"}

    def _call_gemini(self, b64_img, api_key):
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": SYSTEM_PROMPT},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": b64_img
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1500
            }
        }

        last_err = "Серверы Google временно недоступны (503)"
        for model_name in GEMINI_FALLBACK_MODELS:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                resp = requests.post(url, json=payload, timeout=10)
                if resp.status_code == 200:
                    text = self._extract_clean_gemini_text(resp.json())
                    if text:
                        return {"ok": True, "text": text}
                elif resp.status_code in (503, 429):
                    last_err = "Google перегружен (503). Повторите через 5 сек (в РФ/РБ нужен VPN)"
                    time.sleep(0.7)
                    continue
                elif resp.status_code == 404:
                    continue
                elif resp.status_code == 400:
                    try:
                        err_msg = resp.json().get("error", {}).get("message", "")
                        if "location" in err_msg.lower():
                            return {"ok": False, "error": "Регион не поддерживается Google. Включите VPN"}
                    except Exception:
                        err_msg = resp.text[:50]
                    return {"ok": False, "error": f"Ошибка 400: {err_msg[:45]}"}
                else:
                    try:
                        err_msg = resp.json().get("error", {}).get("message", "")
                    except Exception:
                        err_msg = resp.text[:50]
                    return {"ok": False, "error": f"Код {resp.status_code}: {err_msg[:50]}"}
            except requests.exceptions.Timeout:
                last_err = "Таймаут ожидания, повтор..."
                continue
            except Exception as e:
                last_err = str(e)[:50]
                continue

        return {"ok": False, "error": last_err}

    def _call_openai(self, b64_img, api_key):
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": SYSTEM_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_img}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 600,
            "temperature": 0.2
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return {"ok": True, "text": text}
        return {"ok": False, "error": f"OpenAI ({resp.status_code})"}

    def _call_claude(self, b64_img, api_key):
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 600,
            "temperature": 0.2,
            "system": SYSTEM_PROMPT,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": b64_img
                            }
                        },
                        {
                            "type": "text",
                            "text": "Проанализируй этот экран согласно инструкции."
                        }
                    ]
                }
            ]
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("content", [])
            text = "".join(c.get("text", "") for c in content if c.get("type") == "text")
            return {"ok": True, "text": text}
        return {"ok": False, "error": f"Claude ({resp.status_code})"}

    def _call_deepseek(self, b64_img, api_key):
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": SYSTEM_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_img}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500,
            "temperature": 0.2
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return {"ok": True, "text": text}
        return {"ok": False, "error": f"DeepSeek ({resp.status_code})"}
