import io
import socket
import base64
import json
import uvicorn
from fastapi import FastAPI, Response, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Screen AI Assistant Desktop Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine_instance = None

def set_engine(engine):
    global engine_instance
    engine_instance = engine

class KeyRequest(BaseModel):
    api_key: str

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Screen AI Assistant - Панель мониторинга ПК</title>
    <style>
        :root {
            --bg: #0b0d13;
            --card-bg: #151822;
            --card-border: #242938;
            --accent-green: #00e676;
            --accent-purple: #7c4dff;
            --accent-purple-hover: #651fff;
            --accent-blue: #64b5f6;
            --text-primary: #ffffff;
            --text-secondary: #9aa0a6;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        body { background: var(--bg); color: var(--text-primary); padding: 24px 20px; min-height: 100vh; }
        .container { max-width: 900px; margin: 0 auto; }
        
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid var(--card-border); flex-wrap: wrap; gap: 10px; }
        h1 { font-size: 22px; display: flex; align-items: center; gap: 8px; }
        .badges-row { display: flex; gap: 8px; align-items: center; }
        .badge { font-size: 12px; padding: 4px 10px; border-radius: 20px; font-weight: bold; }
        .badge-green { background: rgba(0, 230, 118, 0.15); color: var(--accent-green); border: 1px solid var(--accent-green); }
        .badge-purple { background: rgba(124, 77, 255, 0.2); color: #b388ff; border: 1px solid #7c4dff; }

        /* Бегущая строка крипты */
        .ticker-bar { background: #10131b; border: 1px solid var(--card-border); border-radius: 10px; padding: 8px 14px; margin-bottom: 18px; font-size: 13px; color: var(--accent-blue); font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

        /* Карточки */
        .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 14px; padding: 18px; margin-bottom: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .card-title { font-size: 13px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--text-secondary); font-weight: bold; }
        .btn-copy { background: #1e2332; border: 1px solid #363e54; color: #cfd3dc; padding: 4px 10px; border-radius: 6px; font-size: 12px; cursor: pointer; transition: 0.2s; }
        .btn-copy:hover { background: var(--accent-purple); color: #fff; border-color: var(--accent-purple); }

        .answer-box { background: rgba(0, 230, 118, 0.1); border-left: 4px solid var(--accent-green); padding: 14px; border-radius: 8px; font-size: 17px; font-weight: bold; color: var(--accent-green); word-break: break-word; line-height: 1.5; white-space: pre-wrap; }
        .game-box { background: rgba(124, 77, 255, 0.12); border-left: 4px solid var(--accent-purple); padding: 12px; border-radius: 8px; font-size: 14px; color: #e1e3e6; line-height: 1.5; white-space: pre-wrap; }
        .summary-box { font-size: 15px; line-height: 1.6; color: #e1e3e6; white-space: pre-wrap; }

        /* Панель истории */
        .history-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; background: #161922; border: 1px solid var(--card-border); border-radius: 10px; padding: 8px 14px; }
        .hist-btn { background: #252b3a; border: none; color: #fff; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: bold; cursor: pointer; transition: 0.2s; }
        .hist-btn:hover { background: var(--accent-purple); }
        .hist-counter { font-size: 13px; color: var(--text-secondary); }

        /* Кнопки действий */
        .controls-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin-bottom: 18px; }
        .btn-action { padding: 12px; border: none; border-radius: 10px; font-size: 13px; font-weight: bold; cursor: pointer; transition: 0.2s; color: #fff; text-align: center; }
        .btn-purple { background: var(--accent-purple); }
        .btn-purple:hover { background: #651fff; }
        .btn-green { background: #18382b; color: #00e676; border: 1px solid #00e676; }
        .btn-green:hover { background: #00e676; color: #000; }
        .btn-blue { background: #1a2733; color: #64b5f6; border: 1px solid #64b5f6; }
        .btn-blue:hover { background: #64b5f6; color: #000; }
        .btn-dark { background: #1e222d; border: 1px solid var(--card-border); }
        .btn-dark:hover { background: #2d3342; }

        /* Быстрый вопрос */
        .ask-row { display: flex; gap: 8px; margin-top: 10px; }
        .ask-input { flex: 1; padding: 12px 14px; background: #11141c; border: 1px solid var(--card-border); border-radius: 8px; color: #fff; font-size: 14px; outline: none; }
        .ask-input:focus { border-color: var(--accent-purple); }

        .screen-preview { width: 100%; border-radius: 10px; border: 1px solid var(--card-border); margin-top: 10px; display: block; }
        .footer-info { font-size: 12px; color: var(--text-secondary); text-align: center; margin-top: 24px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>⚡ Screen AI Assistant</h1>
                <p style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;">Интеллектуальный экранный аналитик и суфлер (ПК)</p>
            </div>
            <div class="badges-row">
                <div id="modelBadge" class="badge badge-purple">Gemini</div>
                <div id="quotaBadge" class="badge badge-green">PRO Безлимит</div>
                <div id="statusBadge" class="badge badge-green">Готов</div>
            </div>
        </header>

        <!-- Бегущая строка крипты -->
        <div id="tickerBar" class="ticker-bar">🪙 BTC, ETH, SOL, TON — мониторинг онлайн</div>

        <!-- Навигация по истории -->
        <div class="history-bar">
            <button class="hist-btn" onclick="histPrev()">◀ Назад</button>
            <span id="histCounter" class="hist-counter">● Ответ 0 из 0</span>
            <button class="hist-btn" onclick="histNext()">Вперед ▶</button>
            <button class="hist-btn" style="background:#00e676; color:#0b0d13;" onclick="histLatest()">⚡ Свежий</button>
        </div>

        <!-- Блок ответа к тестам / суфлера -->
        <div id="answerCard" class="card" style="display: none;">
            <div class="card-header">
                <div class="card-title">💡 Распознанный ответ / Суфлер</div>
                <button class="btn-copy" onclick="copyText('answerText')">📋 Копировать ответ</button>
            </div>
            <div id="answerText" class="answer-box">—</div>
        </div>

        <!-- Блок распознанной игры / софта -->
        <div id="gameCard" class="card" style="display: none;">
            <div class="card-header">
                <div class="card-title">🎮 Игра / Проект на экране</div>
            </div>
            <div id="gameText" class="game-box">—</div>
        </div>

        <!-- Блок тезисов / конспекта -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">📋 Тезисы видеоролика / Конспект</div>
                <button class="btn-copy" onclick="copyText('summaryText')">📋 Копировать тезисы</button>
            </div>
            <div id="summaryText" class="summary-box">Ожидание первого анализа экрана...</div>
        </div>

        <!-- Быстрый вопрос к текущему экрану -->
        <div class="card">
            <div class="card-title">❓ Задать быстрый вопрос по экрану</div>
            <div class="ask-row">
                <input id="inpQuickQ" class="ask-input" type="text" placeholder="Например: какой ответ в тесте? или объясни этот код..." onkeydown="if(event.key==='Enter') submitQuickQ()">
                <button class="btn-action btn-purple" style="min-width: 120px;" onclick="submitQuickQ()">Спросить</button>
            </div>
        </div>

        <!-- Кнопки управления -->
        <div class="controls-grid">
            <button class="btn-action btn-purple" onclick="triggerAnalyze()">⚡ Экран (Alt+X)</button>
            <button class="btn-action btn-blue" onclick="triggerClipboard()">📋 Буфер (Alt+B)</button>
            <button class="btn-action btn-green" onclick="triggerAudio()">🎙️ Звук (Alt+V)</button>
            <button id="btnMode" class="btn-action btn-dark" onclick="toggleMode()">🎓 Режим: Учёба</button>
            <button id="btnAuto" class="btn-action btn-dark" onclick="toggleAuto()">Авто: ВКЛ</button>
        </div>

        <!-- Скриншот экрана -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">🖥️ Текущий снимок экрана</div>
                <button class="btn-copy" onclick="refreshScreenshot()">🔄 Обновить снимок</button>
            </div>
            <img id="screenImg" class="screen-preview" src="/api/screenshot" alt="Скриншот экрана">
        </div>

        <div class="footer-info">
            Screen AI Assistant PC Edition | Локальный порт: 8000 | Горячие клавиши: Alt+X, Alt+B, Alt+S, Alt+V, Alt+Z, Alt+C
        </div>
    </div>

    <script>
        async function fetchState() {
            try {
                const res = await fetch('/api/latest');
                const data = await res.json();
                document.getElementById('statusBadge').innerText = data.status || "Готов";
                document.getElementById('modelBadge').innerText = data.provider_badge || "AI";
                document.getElementById('quotaBadge').innerText = "⚡ Безлимит";
                
                if (data.crypto_ticker) {
                    document.getElementById('tickerBar').innerText = data.crypto_ticker;
                }

                // История
                document.getElementById('histCounter').innerText = `● Ответ ${data.history_current} из ${data.history_count}`;

                // Ответ
                const ansCard = document.getElementById('answerCard');
                if (data.answer && data.answer.trim().length > 0 && data.answer !== "—") {
                    ansCard.style.display = 'block';
                    document.getElementById('answerText').innerText = data.answer;
                } else {
                    ansCard.style.display = 'none';
                }

                // Игра
                const gameCard = document.getElementById('gameCard');
                if (data.game_info && data.game_info.trim().length > 0) {
                    gameCard.style.display = 'block';
                    document.getElementById('gameText').innerText = data.game_info;
                } else {
                    gameCard.style.display = 'none';
                }

                // Тезисы
                if (data.summary) {
                    document.getElementById('summaryText').innerText = data.summary;
                }

                // Режим
                const btnMode = document.getElementById('btnMode');
                if (data.app_mode === 'crypto') {
                    btnMode.innerText = "📈 Режим: Крипта";
                    btnMode.style.borderColor = "#64b5f6";
                } else {
                    btnMode.innerText = "🎓 Режим: Учёба";
                    btnMode.style.borderColor = "#7c4dff";
                }

                // Авто
                const btnAuto = document.getElementById('btnAuto');
                btnAuto.innerText = data.is_auto ? "Авто: ВКЛ" : "Авто: ВЫКЛ";
                btnAuto.style.color = data.is_auto ? "#00e676" : "#ff5252";
            } catch(e) {}
        }

        async function triggerAnalyze() {
            document.getElementById('statusBadge').innerText = "● Анализирую...";
            await fetch('/api/analyze', { method: 'POST' });
            setTimeout(fetchState, 1500);
            setTimeout(refreshScreenshot, 1000);
        }

        async function triggerClipboard() {
            document.getElementById('statusBadge').innerText = "● Читаю буфер...";
            await fetch('/api/analyze_clipboard', { method: 'POST' });
            setTimeout(fetchState, 1500);
        }

        async function triggerAudio() {
            document.getElementById('statusBadge').innerText = "🎙️ Слушаю звук...";
            await fetch('/api/listen', { method: 'POST' });
            setTimeout(fetchState, 2000);
        }

        async function toggleMode() {
            await fetch('/api/toggle_mode', { method: 'POST' });
            fetchState();
        }

        async function toggleAuto() {
            await fetch('/api/toggle_auto', { method: 'POST' });
            fetchState();
        }

        async function histPrev() {
            await fetch('/api/history_prev', { method: 'POST' });
            fetchState();
        }

        async function histNext() {
            await fetch('/api/history_next', { method: 'POST' });
            fetchState();
        }

        async function histLatest() {
            await fetch('/api/history_latest', { method: 'POST' });
            fetchState();
        }

        async function submitQuickQ() {
            const inp = document.getElementById('inpQuickQ');
            const q = inp.value.trim();
            if (!q) return;
            inp.value = "";
            document.getElementById('statusBadge').innerText = "● Думаю...";
            await fetch('/api/ask_quick', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: q })
            });
            setTimeout(fetchState, 1800);
        }

        function refreshScreenshot() {
            document.getElementById('screenImg').src = '/api/screenshot?t=' + Date.now();
        }

        function copyText(elemId) {
            const text = document.getElementById(elemId).innerText;
            if (text && text !== "—") {
                navigator.clipboard.writeText(text);
                alert("✓ Скопировано в буфер обмена!");
            }
        }

        setInterval(fetchState, 2500);
        setInterval(refreshScreenshot, 5000);
        fetchState();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def get_dashboard(request: Request):
    return HTML_DASHBOARD

@app.get("/api/latest")
def get_latest():
    if not engine_instance:
        return {"status": "Сервис не инициализирован"}
    curr_idx = len(engine_instance.history) if engine_instance.history_index == -1 else engine_instance.history_index + 1
    return {
        "status": engine_instance.status,
        "game_info": getattr(engine_instance, "latest_game", ""),
        "answer": engine_instance.latest_answer,
        "summary": engine_instance.latest_summary,
        "crypto_signal": getattr(engine_instance, "latest_crypto", ""),
        "crypto_ticker": getattr(engine_instance, "latest_ticker", ""),
        "app_mode": getattr(engine_instance, "app_mode", "study"),
        "history_count": len(engine_instance.history),
        "history_current": curr_idx,
        "history_is_latest": (engine_instance.history_index == -1 or engine_instance.history_index == len(engine_instance.history) - 1),
        "last_update": engine_instance.last_update_time,
        "is_auto": engine_instance.is_auto,
        "provider_name": engine_instance.ai.PROVIDERS[engine_instance.ai.current_provider]["name"],
        "provider_badge": engine_instance.ai.PROVIDERS[engine_instance.ai.current_provider]["badge"],
        "is_pro": True,
        "remaining_quota": "Безлимит"
    }

@app.post("/api/upload_image")
async def handle_upload_image(
    request: Request,
    image_file: UploadFile = File(None),
    mode: str = Form("study"),
    notes: str = Form("")
):
    if not engine_instance:
        return {"ok": False, "error": "Сервер приложения не инициализирован"}

    img_bytes = None
    if image_file and image_file.filename:
        img_bytes = await image_file.read()
    else:
        try:
            body = await request.json()
            if body and "image" in body:
                b64_str = body["image"]
                if "," in b64_str:
                    b64_str = b64_str.split(",")[1]
                img_bytes = base64.b64decode(b64_str)
                mode = body.get("mode", mode)
                notes = body.get("notes", notes)
        except Exception:
            pass

    if not img_bytes:
        return {"ok": False, "error": "Изображение не получено"}

    res = engine_instance.analyze_custom_image(img_bytes, user_query=notes, label="Загрузка", mode=mode)
    return res

class QuickQuestionPayload(BaseModel):
    question: str

@app.post("/api/ask_quick")
def handle_ask_quick(payload: QuickQuestionPayload):
    if engine_instance and payload.question:
        engine_instance.ask_quick_question(payload.question)
        return {"ok": True}
    return {"ok": False, "error": "Пустой вопрос"}

@app.post("/api/analyze_clipboard")
def handle_analyze_clipboard():
    if engine_instance:
        engine_instance.analyze_clipboard()
        return {"ok": True}
    return {"ok": False}

@app.post("/api/listen")
def handle_listen():
    if engine_instance:
        engine_instance.listen_and_answer()
        return {"ok": True}
    return {"ok": False}

@app.post("/api/history_prev")
def handle_history_prev():
    if engine_instance:
        engine_instance.history_prev()
        return {"ok": True}
    return {"ok": False}

@app.post("/api/history_next")
def handle_history_next():
    if engine_instance:
        engine_instance.history_next()
        return {"ok": True}
    return {"ok": False}

@app.post("/api/history_latest")
def handle_history_latest():
    if engine_instance:
        engine_instance.history_latest()
        return {"ok": True}
    return {"ok": False}

@app.post("/api/toggle_mode")
def handle_toggle_mode():
    if engine_instance:
        new_mode = engine_instance.toggle_app_mode()
        return {"ok": True, "mode": new_mode}
    return {"ok": False}

@app.post("/api/crypto_scan")
def handle_crypto_scan():
    if engine_instance:
        engine_instance.analyze_crypto()
        return {"ok": True}
    return {"ok": False}

@app.post("/api/analyze")
def trigger_analysis():
    if engine_instance:
        engine_instance.analyze_now()
        return {"ok": True, "message": "Анализ запущен"}
    return {"ok": False, "error": "Движок не запущен"}

@app.post("/api/toggle_auto")
def toggle_auto():
    if engine_instance:
        engine_instance.is_auto = not engine_instance.is_auto
        engine_instance.notify_listeners()
        return {"ok": True, "is_auto": engine_instance.is_auto}
    return {"ok": False}

@app.post("/api/set_key")
def set_key(req: KeyRequest):
    if engine_instance:
        engine_instance.save_api_key(req.api_key)
        return {"ok": True}
    return {"ok": False}

@app.get("/api/screenshot")
def get_screenshot():
    if engine_instance:
        try:
            jpeg = engine_instance.capture_screen_jpeg()
            return Response(content=jpeg, media_type="image/jpeg")
        except Exception:
            pass
    return Response(status_code=404)

def run_server(engine, host="0.0.0.0", port=8000):
    import asyncio
    set_engine(engine)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for p in [port, port + 1, port + 2]:
        try:
            config = uvicorn.Config(app, host=host, port=p, log_level="warning", log_config=None)
            server = uvicorn.Server(config)
            loop.run_until_complete(server.serve())
            break
        except Exception as e:
            continue

if __name__ == "__main__":
    from screen_engine import ScreenEngine
    eng = ScreenEngine()
    eng.start_loop()
    print("Локальный веб-хостинг запущен: http://localhost:8000")
    run_server(eng, host="0.0.0.0", port=8000)
