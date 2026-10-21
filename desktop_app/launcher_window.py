import socket
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

# Очищено от мобильных зависимостей

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def enable_paste_helpers(entry, root):
    """Обеспечивает безотказную вставку текста из буфера:
    - по кнопке мыши (ПКМ -> Вставить)
    - по комбинациям Ctrl+V и Shift+Insert
    - работает даже при русской раскладке клавиатуры!
    """
    def paste_clipboard():
        try:
            text = root.clipboard_get().strip()
            if text:
                entry.delete(0, tk.END)
                entry.insert(0, text)
        except Exception:
            pass

    def on_key(event):
        if event.state & 4: # Нажат Control
            # Обработка 'v'/'V' и русской буквы 'м'/'М' (та же клавиша на русской раскладке)
            if event.keysym.lower() in ('v', 'cyrillic_em', 'm', 'ntilde'):
                paste_clipboard()
                return "break"
            elif event.keysym.lower() in ('a', 'cyrillic_ef'):
                entry.select_range(0, tk.END)
                return "break"

    entry.bind("<Control-KeyPress>", on_key)
    entry.bind("<Shift-Insert>", lambda e: paste_clipboard())

    # Контекстное меню по правой кнопке мыши
    menu = tk.Menu(entry, tearoff=0, bg="#1E222D", fg="#FFFFFF", activebackground="#7C4DFF")
    menu.add_command(label="Вставить из буфера", command=paste_clipboard)
    menu.add_command(label="Очистить", command=lambda: entry.delete(0, tk.END))
    
    def popup(e):
        menu.tk_popup(e.x_root, e.y_root)

    entry.bind("<Button-3>", popup)


class LauncherWindow:
    def __init__(self, root, engine, on_launch_overlay):
        self.root = root
        self.engine = engine
        self.on_launch_overlay = on_launch_overlay

        self.root.title("Screen AI Assistant - Панель управления")
        self.root.geometry("860x650")
        self.root.minsize(780, 580)
        self.root.configure(bg="#0F1117")

        self.setup_styles()
        self.setup_layout()

        self.engine.add_listener(self.on_engine_update)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("TNotebook", background="#0F1117", borderwidth=0)
        style.configure("TNotebook.Tab", 
            background="#1E222D", 
            foreground="#9AA0A6", 
            padding=[16, 10], 
            font=("Segoe UI", 10, "bold"),
            borderwidth=0
        )
        style.map("TNotebook.Tab", 
            background=[("selected", "#7C4DFF")], 
            foreground=[("selected", "#FFFFFF")]
        )

    def setup_layout(self):
        # Верхний Header
        header = tk.Frame(self.root, bg="#161922", height=60, padx=20)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        lbl_logo = tk.Label(
            header, 
            text="⚡ SCREEN AI ASSISTANT", 
            fg="#FFFFFF", 
            bg="#161922", 
            font=("Segoe UI", 13, "bold")
        )
        lbl_logo.pack(side=tk.LEFT, pady=16)

        self.lbl_header_status = tk.Label(
            header,
            text=self.get_account_badge_text(),
            fg="#00E676" if self.engine.auth.is_pro else "#9AA0A6",
            bg="#212634",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=4
        )
        self.lbl_header_status.pack(side=tk.RIGHT, pady=16)

        # Контейнер вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        self.tab_home = tk.Frame(self.notebook, bg="#0F1117", padx=16, pady=16)
        self.tab_models = tk.Frame(self.notebook, bg="#0F1117", padx=16, pady=16)
        self.tab_hotkeys = tk.Frame(self.notebook, bg="#0F1117", padx=16, pady=16)
        self.tab_settings = tk.Frame(self.notebook, bg="#0F1117", padx=16, pady=16)

        self.notebook.add(self.tab_home, text="  Главная  ")
        self.notebook.add(self.tab_models, text="  Выбор ИИ  ")
        self.notebook.add(self.tab_hotkeys, text="  ⌨️ Горячие клавиши  ")
        self.notebook.add(self.tab_settings, text="  О проекте  ")

        self.build_tab_home()
        self.build_tab_models()
        self.build_tab_hotkeys()
        self.build_tab_settings()

    def get_account_badge_text(self):
        return "⚡ Open Source • Безлимит"

    # --- Вкладка 1: Главная ---
    def build_tab_home(self):
        btn_start_overlay = tk.Button(
            self.tab_home,
            text="▶  ЗАПУСТИТЬ ЭКРАННЫЙ ОВЕРЛЕЙ",
            bg="#7C4DFF",
            fg="#FFFFFF",
            activebackground="#651FFF",
            activeforeground="#FFFFFF",
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            pady=14,
            command=self.on_launch_overlay
        )
        btn_start_overlay.pack(fill=tk.X, pady=(0, 16))

        card_info = tk.Frame(self.tab_home, bg="#1A1D26", padx=16, pady=14, highlightbackground="#2D3342", highlightthickness=1)
        card_info.pack(fill=tk.X, pady=(0, 16))

        self.lbl_home_model = tk.Label(
            card_info,
            text=f"Текущая модель: {self.engine.ai.PROVIDERS[self.engine.ai.current_provider]['name']}",
            fg="#FFFFFF",
            bg="#1A1D26",
            font=("Segoe UI", 10, "bold")
        )
        self.lbl_home_model.pack(anchor="w")

        self.lbl_home_quota = tk.Label(
            card_info,
            text=f"Статус: {self.get_account_badge_text()}",
            fg="#00E676",
            bg="#1A1D26",
            font=("Segoe UI", 9)
        )
        self.lbl_home_quota.pack(anchor="w", pady=(4, 0))

        # Быстрый ввод / статус API-ключа прямо на главной вкладке
        home_key_box = tk.Frame(card_info, bg="#12151D", padx=10, pady=8, highlightbackground="#3D4558", highlightthickness=1)
        home_key_box.pack(fill=tk.X, pady=(10, 0))

        lbl_hk_hdr = tk.Label(
            home_key_box,
            text="🔑 API-ключ Gemini (Google AI Studio):",
            fg="#64B5F6",
            bg="#12151D",
            font=("Segoe UI", 8, "bold")
        )
        lbl_hk_hdr.pack(anchor="w")

        home_key_row = tk.Frame(home_key_box, bg="#12151D")
        home_key_row.pack(fill=tk.X, pady=(4, 0))

        self.entry_home_key = tk.Entry(
            home_key_row,
            bg="#0B0D13",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            relief=tk.FLAT,
            font=("Segoe UI", 9)
        )
        self.entry_home_key.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 6))
        current_k = self.engine.ai.get_key(self.engine.ai.current_provider)
        if current_k:
            self.entry_home_key.insert(0, current_k)
        enable_paste_helpers(self.entry_home_key, self.root)
        self.entry_home_key.bind("<KeyRelease>", lambda e: self.on_home_key_changed())
        self.entry_home_key.bind("<Return>", lambda e: self.on_save_home_key())

        btn_save_hk = tk.Button(
            home_key_row,
            text="Сохранить",
            bg="#7C4DFF",
            fg="#FFFFFF",
            activebackground="#651FFF",
            activeforeground="#FFFFFF",
            font=("Segoe UI", 8, "bold"),
            relief=tk.FLAT,
            padx=10,
            command=self.on_save_home_key
        )
        btn_save_hk.pack(side=tk.RIGHT)

        self.lbl_home_key_status = tk.Label(
            home_key_box,
            text="✓ Ключ подключен" if current_k else "⚠️ Вставьте API-ключ и нажмите «Сохранить»",
            fg="#00E676" if current_k else "#FFB74D",
            bg="#12151D",
            font=("Segoe UI", 8)
        )
        self.lbl_home_key_status.pack(anchor="w", pady=(3, 0))

        card_guide = tk.Frame(self.tab_home, bg="#1A1D26", padx=16, pady=14, highlightbackground="#2D3342", highlightthickness=1)
        card_guide.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            card_guide,
            text="💡 КАК ЭТО РАБОТАЕТ В ДЕЙСТВИИ:",
            fg="#7C4DFF",
            bg="#1A1D26",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(0, 8))

        guide_text = (
            "1. Нажмите «Запустить экранный оверлей» — появится полупрозрачный суфлер поверх всех окон.\n\n"
            "2. Горячие клавиши (работают в любых программах поверх всех окон):\n"
            "   • Alt + X — Мгновенный анализ экрана / видео\n"
            "   • Alt + S — Снайперский режим (выделение задачи или графика рамкой)\n"
            "   • Alt + B — Мгновенный анализ скриншота из буфера обмена (Win+Shift+S)\n"
            "   • Alt + V — Захват системного звука из наушников или микрофона (5.5 сек)\n"
            "   • Alt + C — Крипто-Радар (сканирование графика TradingView/биржи, сигнал LONG/SHORT)\n"
            "   • Alt + ← / → — Листание истории предыдущих ответов нейросети\n"
            "   • Alt + Z — Паник-кнопка: мгновенно спрятать/показать суфлер\n\n"
            "3. Режимы работы: переключайте «🎓 Учёба» и «📈 Крипта» кнопкой в шапке суфлера.\n"
            "4. В оверлее доступно поле быстрого вопроса и бегущая строка котировок BTC, ETH, SOL, TON.\n"
            "5. Полный Open-Source безлимит: все функции и модели открыты без ограничений."
        )

        lbl_guide = tk.Label(
            card_guide,
            text=guide_text,
            fg="#C5C7D0",
            bg="#1A1D26",
            font=("Segoe UI", 9),
            justify=tk.LEFT,
            wraplength=680
        )
        lbl_guide.pack(anchor="w")

    # --- Вкладка 2: Выбор нейросети ---
    def build_tab_models(self):
        tk.Label(
            self.tab_models,
            text="ВЫБЕРИТЕ НЕЙРОСЕТЬ ДЛЯ АНАЛИЗА ЭКРАНА:",
            fg="#9AA0A6",
            bg="#0F1117",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(0, 10))

        self.model_var = tk.StringVar(value=self.engine.ai.current_provider)

        for pid, pdata in self.engine.ai.PROVIDERS.items():
            card = tk.Frame(self.tab_models, bg="#1A1D26", padx=12, pady=10, highlightbackground="#2D3342", highlightthickness=1)
            card.pack(fill=tk.X, pady=4)

            rb = tk.Radiobutton(
                card,
                text=pdata["name"],
                variable=self.model_var,
                value=pid,
                bg="#1A1D26",
                fg="#FFFFFF",
                selectcolor="#7C4DFF",
                activebackground="#1A1D26",
                activeforeground="#FFFFFF",
                font=("Segoe UI", 10, "bold"),
                command=self.on_provider_selected
            )
            rb.pack(anchor="w")

            tk.Label(
                card,
                text=pdata["desc"],
                fg="#9AA0A6",
                bg="#1A1D26",
                font=("Segoe UI", 8)
            ).pack(anchor="w", padx=24)

        # Поле ввода API ключа для выбранной модели
        key_box = tk.Frame(self.tab_models, bg="#161922", padx=14, pady=12, highlightbackground="#7C4DFF", highlightthickness=1)
        key_box.pack(fill=tk.X, pady=(16, 0))

        self.lbl_key_prompt = tk.Label(
            key_box,
            text=f"API-ключ для {self.engine.ai.PROVIDERS[self.engine.ai.current_provider]['name']}:",
            fg="#FFFFFF",
            bg="#161922",
            font=("Segoe UI", 9, "bold")
        )
        self.lbl_key_prompt.pack(anchor="w")

        key_input_row = tk.Frame(key_box, bg="#161922")
        key_input_row.pack(fill=tk.X, pady=(6, 0))

        self.entry_api_key = tk.Entry(
            key_input_row,
            bg="#0F1117",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            relief=tk.FLAT,
            font=("Segoe UI", 10)
        )
        self.entry_api_key.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 6))
        self.entry_api_key.insert(0, self.engine.ai.get_key(self.engine.ai.current_provider))

        # Активируем ПКМ и Ctrl+V поддержку
        enable_paste_helpers(self.entry_api_key, self.root)
        self.entry_api_key.bind("<KeyRelease>", lambda e: self.on_models_key_changed())
        self.entry_api_key.bind("<Return>", lambda e: self.on_save_key())

        # Кнопка быстрой вставки из буфера обмена
        btn_paste_key = tk.Button(
            key_input_row,
            text="📋 Вставить",
            bg="#2D3342",
            fg="#FFFFFF",
            activebackground="#3D4558",
            activeforeground="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            command=self.paste_to_api_key
        )
        btn_paste_key.pack(side=tk.LEFT, padx=(0, 6))

        btn_save_key = tk.Button(
            key_input_row,
            text="Сохранить",
            bg="#7C4DFF",
            fg="#FFFFFF",
            activebackground="#651FFF",
            activeforeground="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=14,
            command=self.on_save_key
        )
        btn_save_key.pack(side=tk.RIGHT)

        # Кнопка перехода на Google AI Studio
        btn_get_gemini = tk.Button(
            key_box,
            text="🔑 Получить бесплатный API-ключ Gemini (Google AI Studio) ↗",
            bg="#18382B",
            fg="#00E676",
            activebackground="#00E676",
            activeforeground="#000000",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=7,
            cursor="hand2",
            command=lambda: webbrowser.open("https://aistudio.google.com/app/apikey")
        )
        btn_get_gemini.pack(fill=tk.X, pady=(10, 8))

        # Двуязычный блок инструкций (RU / EN)
        guide_box = tk.Frame(key_box, bg="#11141C", padx=12, pady=10, highlightbackground="#252B3A", highlightthickness=1)
        guide_box.pack(fill=tk.X)

        lbl_ru_guide = tk.Label(
            guide_box,
            text=(
                "🇷🇺 КАК ДОБАВИТЬ СВОЙ БЕСПЛАТНЫЙ КЛЮЧ GEMINI:\n"
                "1. Нажмите зеленую кнопку выше (или откройте https://aistudio.google.com/app/apikey).\n"
                "2. Войдите через аккаунт Google и нажмите «Create API key» (Создать ключ API).\n"
                "3. Скопируйте ключ, вставьте в поле выше и нажмите «Сохранить».\n"
                "• Сервис полностью бесплатен (щедрый лимит Google без привязки банковских карт)."
            ),
            fg="#E0E2EC",
            bg="#11141C",
            font=("Segoe UI", 8),
            justify=tk.LEFT
        )
        lbl_ru_guide.pack(anchor="w", pady=(0, 6))

        lbl_en_guide = tk.Label(
            guide_box,
            text=(
                "🇬🇧 HOW TO ADD YOUR OWN FREE GEMINI API KEY:\n"
                "1. Click the green button above (or open https://aistudio.google.com/app/apikey).\n"
                "2. Sign in with your Google account and click \"Create API key\".\n"
                "3. Copy the key, paste it into the field above and click \"Save\".\n"
                "• Completely free via Google AI Studio tier (no credit card required)."
            ),
            fg="#9AA0A6",
            bg="#11141C",
            font=("Segoe UI", 8),
            justify=tk.LEFT
        )
        lbl_en_guide.pack(anchor="w")

    def on_home_key_changed(self):
        val = self.entry_home_key.get().strip()
        self.engine.ai.set_key("gemini", val)
        self.engine.save_config()
        if hasattr(self, "entry_api_key") and self.engine.ai.current_provider == "gemini":
            cur_tab_val = self.entry_api_key.get().strip()
            if cur_tab_val != val:
                self.entry_api_key.delete(0, tk.END)
                self.entry_api_key.insert(0, val)
        if hasattr(self, "lbl_home_key_status"):
            self.lbl_home_key_status.config(
                text="✓ Ключ сохранен и активен!" if val else "⚠️ Вставьте API-ключ",
                fg="#00E676" if val else "#FFB74D"
            )

    def on_save_home_key(self):
        val = self.entry_home_key.get().strip()
        self.engine.ai.set_key("gemini", val)
        self.engine.save_config()
        self.on_home_key_changed()
        messagebox.showinfo("Успешно", "API-ключ Gemini сохранен и готов к работе!")

    def on_models_key_changed(self):
        val = self.entry_api_key.get().strip()
        self.engine.ai.set_key(self.engine.ai.current_provider, val)
        self.engine.save_config()
        if self.engine.ai.current_provider == "gemini" and hasattr(self, "entry_home_key"):
            cur_home_val = self.entry_home_key.get().strip()
            if cur_home_val != val:
                self.entry_home_key.delete(0, tk.END)
                self.entry_home_key.insert(0, val)
            if hasattr(self, "lbl_home_key_status"):
                self.lbl_home_key_status.config(
                    text="✓ Ключ сохранен и активен!" if val else "⚠️ Вставьте API-ключ",
                    fg="#00E676" if val else "#FFB74D"
                )

    def paste_to_api_key(self):
        try:
            val = self.root.clipboard_get().strip()
            if val:
                self.entry_api_key.delete(0, tk.END)
                self.entry_api_key.insert(0, val)
                self.on_models_key_changed()
                messagebox.showinfo("Буфер обмена", "Ключ успешно вставлен и сохранен!")
            else:
                messagebox.showwarning("Буфер обмена", "Буфер обмена пуст.")
        except Exception:
            messagebox.showwarning("Буфер обмена", "Не удалось прочитать буфер обмена.")

    def on_provider_selected(self):
        new_provider = self.model_var.get()
        self.engine.ai.current_provider = new_provider
        self.engine.save_config()
        self.lbl_key_prompt.config(text=f"API-ключ для {self.engine.ai.PROVIDERS[new_provider]['name']}:")
        self.entry_api_key.delete(0, tk.END)
        self.entry_api_key.insert(0, self.engine.ai.get_key(new_provider))
        self.lbl_home_model.config(text=f"Текущая модель: {self.engine.ai.PROVIDERS[new_provider]['name']}")
        self.engine.notify_listeners()

    def on_save_key(self):
        val = self.entry_api_key.get().strip()
        self.engine.ai.set_key(self.engine.ai.current_provider, val)
        self.engine.save_config()
        self.on_models_key_changed()
        messagebox.showinfo("Успешно", f"Ключ для {self.engine.ai.PROVIDERS[self.engine.ai.current_provider]['name']} сохранен!")

    # --- Вкладка 3: Горячие клавиши и управление ---
    def build_tab_hotkeys(self):
        tk.Label(
            self.tab_hotkeys,
            text="⌨️ БЫСТРЫЕ ГОРЯЧИЕ КЛАВИШИ WINDOWS (РАБОТАЮТ ПОВЕРХ ВСЕХ ОКОН):",
            fg="#64B5F6",
            bg="#0F1117",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 10))

        scroll_container = tk.Frame(self.tab_hotkeys, bg="#0F1117")
        scroll_container.pack(fill=tk.BOTH, expand=True)

        hotkeys_list = [
            ("Alt + X", "⚡ Анализ всего экрана", "Мгновенно делает снимок всего рабочего стола и передает в ИИ для распознавания тестов, видео или кода.", lambda: self.engine.analyze_now()),
            ("Alt + S", "🎯 Снайперский прицел", "Открывает затемнение с рамкой: выделите мышкой конкретную задачу, формулу или график.", lambda: self.on_launch_overlay()),
            ("Alt + B", "📋 Анализ буфера обмена", "Мгновенно решает снимок экрана, сделанный через Win+Shift+S или скопированный в буфер обмена.", lambda: self.engine.analyze_clipboard()),
            ("Alt + V", "🎙️ Устный суфлер (Аудио)", "Захватывает системный звук из наушников/видео или голос преподавателя через микрофон (5.5 сек).", lambda: self.engine.listen_and_answer()),
            ("Alt + Z", "👻 Стелс-кнопка (Паника)", "Мгновенно прячет или восстанавливает плавающее окно ассистента при приближении посторонних.", None),
            ("Alt + C", "📈 Крипто-Радар", "Анализирует биржевые графики (Binance, TradingView) и выдает сигналы LONG / SHORT / СТОП.", lambda: self.engine.analyze_crypto()),
            ("Alt + ◄ / ►", "⏮️ Листание истории", "Перемещение по предыдущим ответам нейросети назад и вперед.", lambda: self.engine.history_prev())
        ]

        for keys, title, desc, action_fn in hotkeys_list:
            card = tk.Frame(scroll_container, bg="#161922", padx=10, pady=6, highlightbackground="#252B3A", highlightthickness=1)
            card.pack(fill=tk.X, pady=3)

            left = tk.Frame(card, bg="#161922", width=115)
            left.pack(side=tk.LEFT)
            left.pack_propagate(False)

            tk.Label(
                left,
                text=keys,
                fg="#00E676",
                bg="#1E2332",
                font=("Consolas", 9, "bold"),
                padx=6,
                pady=3
            ).pack(anchor="w")

            mid = tk.Frame(card, bg="#161922")
            mid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

            tk.Label(
                mid,
                text=title,
                fg="#FFFFFF",
                bg="#161922",
                font=("Segoe UI", 9, "bold")
            ).pack(anchor="w")

            tk.Label(
                mid,
                text=desc,
                fg="#9AA0A6",
                bg="#161922",
                font=("Segoe UI", 8),
                wraplength=480,
                justify=tk.LEFT
            ).pack(anchor="w")

            if action_fn:
                btn_test = tk.Button(
                    card,
                    text="Тест",
                    bg="#2D3342",
                    fg="#C5C7D0",
                    activebackground="#7C4DFF",
                    activeforeground="#FFFFFF",
                    font=("Segoe UI", 8, "bold"),
                    relief=tk.FLAT,
                    padx=10,
                    pady=2,
                    cursor="hand2",
                    command=action_fn
                )
                btn_test.pack(side=tk.RIGHT, pady=2)

    # --- Вкладка 4: Настройки и О проекте ---
    def build_tab_settings(self):
        box_about = tk.Frame(self.tab_settings, bg="#1A1D26", padx=16, pady=14, highlightbackground="#2D3342", highlightthickness=1)
        box_about.pack(fill=tk.X, pady=(0, 14))

        tk.Label(box_about, text="О ПРОЕКТЕ (SCREEN AI ASSISTANT):", fg="#FFFFFF", bg="#1A1D26", font=("Segoe UI", 9, "bold")).pack(anchor="w")

        about_text = (
            "Screen AI Assistant — интеллектуальный персональный ассистент реального времени для Windows.\n\n"
            "• Лицензия: MIT (Open Source, свободное коммерческое и личное использование)\n"
            "• Версия: 2.5.0 Production Ready\n"
            "• Поддерживаемые модели: Google Gemini (2.5 Flash, 2.0 Flash, 1.5 Pro), OpenAI GPT-4o, Claude 3.5\n"
            "• Режим невидимости: Windows API SetWindowDisplayAffinity (WDA_EXCLUDEFROMCAPTURE)\n"
            "• Аудио-захват: WASAPI Loopback (наушники/динамики) + микрофон\n"
            "• Конфигурация: локально в config.json (ключи хранятся только на вашем компьютере)"
        )
        tk.Label(
            box_about,
            text=about_text,
            fg="#C5C7D0",
            bg="#1A1D26",
            font=("Segoe UI", 8),
            justify=tk.LEFT
        ).pack(anchor="w", pady=(6, 0))

        # Локальный хостинг
        box_host = tk.Frame(self.tab_settings, bg="#1A1D26", padx=16, pady=14, highlightbackground="#2D3342", highlightthickness=1)
        box_host.pack(fill=tk.X)

        tk.Label(box_host, text="ЛОКАЛЬНЫЙ СЕРВЕР И ВЕБ-МОНИТОРИНГ:", fg="#FFFFFF", bg="#1A1D26", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(
            box_host,
            text="Встроенный FastAPI сервер активен: http://localhost:8000\nВы можете открыть веб-дашборд в любом браузере для мониторинга или API-интеграций.",
            fg="#9AA0A6",
            bg="#1A1D26",
            font=("Segoe UI", 9),
            justify=tk.LEFT
        ).pack(anchor="w", pady=(4, 8))

        btn_open_web = tk.Button(
            box_host,
            text="🌐 Открыть дашборд в браузере (localhost:8000)",
            bg="#7C4DFF",
            fg="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
            command=lambda: webbrowser.open("http://localhost:8000")
        )
        btn_open_web.pack(anchor="w")

    def on_engine_update(self, data):
        self.root.after(0, lambda: self._apply_update(data))

    def _apply_update(self, data):
        self.lbl_header_status.config(text=self.get_account_badge_text())
        self.lbl_home_quota.config(text=f"Статус: {self.get_account_badge_text()}")
