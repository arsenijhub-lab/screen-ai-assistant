# ⚡ Screen AI Assistant (PC Edition)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?logo=windows" alt="Platform Windows">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/FastAPI-v0.100%2B-009688?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/AI%20Models-Gemini%20%7C%20GPT--4o%20%7C%20Claude-7C4DFF" alt="AI Models">
</p>

**Screen AI Assistant** — мощный персональный ИИ-ассистент реального времени для Windows. Приложение работает в виде плавающего полупрозрачного оверлея поверх всех окон, моментально анализирует происходящее на экране (тесты, код, видео, графики) или звук из наушников, и выдает структурированные подсказки и решения.

> 🚀 **100% Open Source & Free**: Все функции, горячие клавиши и модели полностью разблокированы без каких-либо подписок, лимитов или скрытых платежей.

---

## 🌟 Ключевые возможности

### 1. 👻 Аппаратный режим «Невидимки» (Stealth Mode)
- Использует нативный вызов Windows API: `SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)`.
- Окно ассистента и область прицела **полностью невидимы** при демонстрации экрана в **Zoom, Discord, Microsoft Teams, Google Meet, OBS Studio** и на скриншотах рабочего стола.

### 2. ⚡ Мгновенный мультимодальный анализ экрана (Alt + X / Alt + B)
- **Alt + X**: Мгновенный снимок экрана и анализ текущего окна.
- **Alt + B**: Мгновенное решение скриншота прямо из буфера обмена (идеально в связке с `Win + Shift + S`).
- Интеллектуальный диффинг кадров (отсекает статичные повторы и экономит сетевой трафик).

### 3. 🎯 Снайперский прицел (Alt + S)
- Полноэкранный полупрозрачный режим выделения области экрана мышью.
- Позволяет направить ИИ только на нужную формулу, отдельный вопрос теста или блок кода.

### 4. 🎙️ Аудио-суфлер из наушников (WASAPI Loopback, Alt + V)
- Захватывает внутренний системный звук из наушников/динамиков без задержек (с автоматическим фоллбэком на микрофон).
- ИИ слушает устный вопрос преподавателя или спикера на конференции и формулирует четкий ответ.

### 5. 📈 Режим «Крипто-Радар» (Alt + C)
- Анализирует свечные графики (TradingView, Binance, Bybit).
- Вычисляет паттерны тех. анализа, уровни поддержки/сопротивления и генерирует сигналы (`LONG / SHORT / СТОП`).
- Встроенная бегущая строка котировок в реальном времени (BTC, ETH, SOL, TON).

### 6. 🌐 Локальный FastAPI сервер и веб-панель (`http://localhost:8000`)
- Встроенный сервер на FastAPI + Uvicorn предоставляет веб-дашборд и REST API для интеграции со сторонними скриптами и браузером.

---

## ⌨️ Горячие клавиши (Global Hotkeys)

Все комбинации клавиш зарегистрированы на уровне операционной системы через Windows API `RegisterHotKey` и работают в любых играх и программах поверх всех окон:

| Комбинация | Действие | Описание |
| :--- | :--- | :--- |
| **Alt + X** | ⚡ Снимок экрана | Анализирует весь рабочий стол через выбранную нейросеть |
| **Alt + S** | 🎯 Снайперский прицел | Открывает рамку для выделения конкретной задачи мышью |
| **Alt + B** | 📋 Анализ буфера | Анализирует изображение из буфера обмена (`Win+Shift+S`) |
| **Alt + V** | 🎙️ Аудио-суфлер | Захват 5.5 сек звука из наушников или микрофона |
| **Alt + C** | 📈 Крипто-Радар | Сканирование биржевого графика и генерация торгового плана |
| **Alt + Z** | 👻 Паник-кнопка | Мгновенно скрыть / показать оверлей при посторонних |
| **Alt + ← / →** | ⏮️ История | Навигация по истории предыдущих ответов нейросети |

---

## 🏗️ Архитектура проекта

```
мгновеный ии/
│
├── desktop_app/                  # Исходный код приложения
│   ├── main.py                   # Точка входа: инициализация потоков и UI
│   ├── screen_engine.py          # Центральный оркестратор (захват, кэш, обработка)
│   ├── ai_providers.py           # Мультимодельный клиент (Gemini, OpenAI, Claude)
│   ├── hotkeys.py                # Низкоуровневый перехватчик клавиш (Win32 API)
│   ├── audio_capture.py          # WASAPI Loopback захват звука (pyaudiowpatch)
│   ├── sniper_selector.py        # Снайперский интерфейс выделения области
│   ├── overlay_ui.py             # Плавающий оверлей суфлера (Tkinter Topmost)
│   ├── launcher_window.py        # Панель настроек, выбора ИИ и горячих клавиш
│   ├── server.py                 # Локальный REST API сервер (FastAPI / Uvicorn)
│   ├── crypto_market.py          # Модуль крипто-котировок и технического анализа
│   └── auth_manager.py           # Менеджер сессии и локального профиля
│
├── ScreenAIAssistant.spec        # Спецификация сборки PyInstaller
├── requirements.txt              # Зависимости Python
├── run_app.bat                   # Быстрый скрипт запуска для Windows
├── LICENSE                       # Лицензия MIT
└── README.md                     # Документация проекта
```

---

## 🚀 Быстрый старт

### Вариант 1: Запуск готового `.exe` (Без установки Python)
1. Скачайте репозиторий или релиз.
2. Запустите `ScreenAIAssistant.exe` (или `run_app.bat`).
3. В открывшемся окне введите свой бесплатный API-ключ (по умолчанию Google Gemini) и нажмите **«Запустить экранный оверлей»**.

### Вариант 2: Запуск из исходного кода Python
Требуется Python 3.10 – 3.13 (Windows 10 / 11).

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/your-username/screen-ai-assistant.git
   cd screen-ai-assistant
   ```

2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Запустите приложение:
   ```bash
   python desktop_app/main.py
   ```

---

## 🛠️ Сборка в один исполняемый файл `.exe`

Для пересборки автономного исполняемого файла с помощью PyInstaller:

```bash
python -m PyInstaller --noconfirm ScreenAIAssistant.spec
```

Готовый файл будет создан в папке `dist/ScreenAIAssistant.exe`.

---

## 🔑 Настройка API-ключа Gemini / Gemini API Key Setup

> [!NOTE]
> 🇷🇺 **Каждый пользователь использует свой собственный бесплатный ключ.** Личные ключи никогда не передаются на сторонние серверы и сохраняются исключительно локально на вашем компьютере в файле `config.json`.
>
> 🇬🇧 **Each user uses their own free API key.** Personal keys are never sent to third-party servers and are stored strictly locally on your machine in `config.json`.

### 🇷🇺 Инструкция на русском: Как бесплатно подключить Google Gemini за 1 минуту

1. **Получите бесплатный ключ API:**
   - Откройте официальный портал: [**Google AI Studio (API Keys)**](https://aistudio.google.com/app/apikey).
   - Войдите в свой обычный аккаунт Google.
   - Нажмите кнопку **«Create API key»** (Создать ключ API).
   - Скопируйте полученную строку ключа (начинается с `AIzaSy...`).
   *Это на 100% бесплатно и не требует привязки банковской карты.*

2. **Вставьте ключ в приложение:**
   - Запустите `ScreenAIAssistant.exe` (или `run_app.bat`).
   - Откройте вкладку **«Выбор ИИ»**.
   - Нажмите кнопку **«📋 Вставить»** (или комбинацию `Ctrl+V`).
   - Нажмите кнопку **«Сохранить»**.

3. **Готово!**
   - Нажмите **«Запустить экранный оверлей»** на главной вкладке и пользуйтесь всеми функциями без ограничений.

---

### 🇬🇧 English Guide: How to add your free Google Gemini API key in 1 minute

1. **Get your free Gemini API key:**
   - Visit the official portal: [**Google AI Studio (API Keys)**](https://aistudio.google.com/app/apikey).
   - Sign in with your standard Google account.
   - Click **"Create API key"**.
   - Copy the generated API key string (starts with `AIzaSy...`).
   *It is 100% free with a generous tier and requires no credit card.*

2. **Paste the key into the application:**
   - Launch `ScreenAIAssistant.exe` (or `run_app.bat`).
   - Go to the **"Выбор ИИ"** (AI Models) tab.
   - Click **"📋 Вставить"** (Paste) or press `Ctrl+V`.
   - Click **"Сохранить"** (Save).

3. **You are ready to go!**
   - Switch back to the **Главная** (Home) tab, click **"ЗАПУСТИТЬ ЭКРАННЫЙ ОВЕРЛЕЙ"**, and enjoy instant AI analysis.

---

## 📄 Лицензия

Проект распространяется под открытой лицензией [MIT](LICENSE). Вы можете свободно использовать, модифицировать и внедрять данный код в коммерческих и некоммерческих целях.
