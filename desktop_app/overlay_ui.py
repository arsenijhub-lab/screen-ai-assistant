import ctypes
import webbrowser
import tkinter as tk

try:
    from .hotkeys import GlobalHotkeyManager
    from .sniper_selector import SniperAreaSelector
except (ImportError, ValueError):
    from hotkeys import GlobalHotkeyManager
    from sniper_selector import SniperAreaSelector

class FloatingOverlayUI:
    def __init__(self, root, engine, on_open_launcher=None):
        self.root = root
        self.engine = engine
        self.on_open_launcher = on_open_launcher

        self.root.title("Screen AI Overlay")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 0.90)
        self.root.configure(bg="#14171F")

        self.width = 420
        self.height = 575
        screen_w = self.root.winfo_screenwidth()
        start_x = screen_w - self.width - 30
        start_y = 50
        self.root.geometry(f"{self.width}x{self.height}+{start_x}+{start_y}")

        self.is_minimized = False
        self.is_stealth = True # Режим невидимки включен по умолчанию!
        self.drag_x = 0
        self.drag_y = 0

        self.setup_ui()
        self.setup_drag()

        self.engine.add_listener(self.on_engine_update)

        # Применяем защиту от записи и демонстрации экрана
        self.root.after(300, self.apply_stealth_mode)

        # Запуск глобальных горячих клавиш (Alt+X, Alt+B, Alt+Z, Alt+S, Alt+V, Alt+C, Alt+Left, Alt+Right)
        self.hotkeys = GlobalHotkeyManager(
            on_analyze=self.engine.analyze_now,
            on_clipboard=self.engine.analyze_clipboard,
            on_toggle_stealth_hide=self.toggle_stealth_hide,
            on_sniper=self.launch_sniper_mode,
            on_audio=self.launch_audio_mode,
            on_crypto=lambda: self.engine.analyze_crypto(),
            on_history_prev=self.engine.history_prev,
            on_history_next=self.engine.history_next
        )
        self.hotkeys.start()

    def apply_stealth_mode(self):
        """Делает окно полностью невидимым в Zoom, Discord, Teams, Google Meet, OBS и скриншотах!"""
        try:
            self.root.update_idletasks()
            hwnd = self.root.winfo_id()
            parent_hwnd = ctypes.windll.user32.GetParent(hwnd)

            # WDA_EXCLUDEFROMCAPTURE = 0x00000011 (Windows 10 2004+ / Windows 11)
            affinity = 0x00000011 if self.is_stealth else 0x00000000
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, affinity)
            if parent_hwnd:
                ctypes.windll.user32.SetWindowDisplayAffinity(parent_hwnd, affinity)

            if self.is_stealth:
                self.btn_stealth.config(text="👻 Невидимка: ВКЛ", fg="#00E676")
            else:
                self.btn_stealth.config(text="👁 Видно всем", fg="#FF5252")
        except Exception as e:
            print(f"Ошибка настройки DisplayAffinity: {e}")

    def toggle_stealth(self):
        self.is_stealth = not self.is_stealth
        self.apply_stealth_mode()

    def setup_ui(self):
        # 1. Шапка оверлея
        self.header_frame = tk.Frame(self.root, bg="#1E222D", height=38)
        self.header_frame.pack(fill=tk.X, side=tk.TOP)
        self.header_frame.pack_propagate(False)

        self.lbl_title = tk.Label(
            self.header_frame,
            text="● Screen AI",
            fg="#00E676",
            bg="#1E222D",
            font=("Segoe UI", 10, "bold")
        )
        self.lbl_title.pack(side=tk.LEFT, padx=10)

        # Кнопка переключения Невидимки
        self.btn_stealth = tk.Label(
            self.header_frame,
            text="👻 Невидимка: ВКЛ",
            fg="#00E676",
            bg="#1E222D",
            font=("Segoe UI", 8, "bold"),
            cursor="hand2"
        )
        self.btn_stealth.pack(side=tk.LEFT, padx=4)
        self.btn_stealth.bind("<Button-1>", lambda e: self.toggle_stealth())

        # Кнопка переключения режима Учеба / Крипта в шапке
        self.btn_mode_hdr = tk.Label(
            self.header_frame,
            text="🎓 Учёба",
            fg="#B388FF",
            bg="#1E222D",
            font=("Segoe UI", 8, "bold"),
            cursor="hand2"
        )
        self.btn_mode_hdr.pack(side=tk.LEFT, padx=6)
        self.btn_mode_hdr.bind("<Button-1>", lambda e: self.engine.toggle_app_mode())

        # Кнопка закрытия
        self.btn_close = tk.Label(
            self.header_frame,
            text="✕",
            fg="#FF5252",
            bg="#1E222D",
            font=("Segoe UI", 11, "bold"),
            cursor="hand2"
        )
        self.btn_close.pack(side=tk.RIGHT, padx=10)
        self.btn_close.bind("<Button-1>", lambda e: self.close_overlay())

        # Кнопка свернуть
        self.btn_min = tk.Label(
            self.header_frame,
            text="—",
            fg="#B0B0B0",
            bg="#1E222D",
            font=("Segoe UI", 12, "bold"),
            cursor="hand2"
        )
        self.btn_min.pack(side=tk.RIGHT, padx=8)
        self.btn_min.bind("<Button-1>", lambda e: self.toggle_minimize())

        # Кнопка открыть лаунчер
        self.btn_launcher = tk.Label(
            self.header_frame,
            text="⚙️",
            fg="#B0B0B0",
            bg="#1E222D",
            font=("Segoe UI", 10),
            cursor="hand2"
        )
        self.btn_launcher.pack(side=tk.RIGHT, padx=6)
        if self.on_open_launcher:
            self.btn_launcher.bind("<Button-1>", lambda e: self.on_open_launcher())

        # 2. Контейнер контента
        self.main_content = tk.Frame(self.root, bg="#14171F", padx=12, pady=10)
        self.main_content.pack(fill=tk.BOTH, expand=True)

        # Верхняя панель: статус и прозрачность
        meta_row = tk.Frame(self.main_content, bg="#14171F")
        meta_row.pack(fill=tk.X, pady=(0, 6))

        self.lbl_quota = tk.Label(
            meta_row,
            text="⚡ БЕЗЛИМИТ",
            fg="#00E676",
            bg="#14171F",
            font=("Segoe UI", 8, "bold")
        )
        self.lbl_quota.pack(side=tk.LEFT)

        self.scale_alpha = tk.Scale(
            meta_row,
            from_=20,
            to=100,
            orient=tk.HORIZONTAL,
            bg="#14171F",
            fg="#FFFFFF",
            highlightthickness=0,
            troughcolor="#2D3342",
            activebackground="#7C4DFF",
            showvalue=False,
            length=160,
            command=self.on_alpha_change
        )
        self.scale_alpha.set(90)
        self.scale_alpha.pack(side=tk.RIGHT)

        # Бегущая строка крипто-котировок онлайн
        self.ticker_box = tk.Frame(self.main_content, bg="#10131B", padx=6, pady=3, highlightbackground="#252B3A", highlightthickness=1)
        self.ticker_box.pack(fill=tk.X, pady=(0, 6))
        self.lbl_crypto_ticker = tk.Label(
            self.ticker_box,
            text="🪙 BTC, ETH, SOL, TON — котировки онлайн",
            fg="#64B5F6",
            bg="#10131B",
            font=("Segoe UI", 7, "bold"),
            anchor="w"
        )
        self.lbl_crypto_ticker.pack(fill=tk.X)

        # Панель листания истории ответов ИИ (Назад / Вперед)
        self.hist_bar = tk.Frame(self.main_content, bg="#14171F")
        self.hist_bar.pack(fill=tk.X, pady=(0, 4))

        self.btn_hist_prev = tk.Label(
            self.hist_bar,
            text="◀ Назад",
            fg="#C5C7D0",
            bg="#1E222D",
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=2,
            cursor="hand2"
        )
        self.btn_hist_prev.pack(side=tk.LEFT)
        self.btn_hist_prev.bind("<Button-1>", lambda e: self.engine.history_prev())

        self.lbl_hist_counter = tk.Label(
            self.hist_bar,
            text="● Ответ 0/0",
            fg="#9AA0A6",
            bg="#14171F",
            font=("Segoe UI", 8)
        )
        self.lbl_hist_counter.pack(side=tk.LEFT, padx=8)

        self.btn_hist_next = tk.Label(
            self.hist_bar,
            text="Вперед ▶",
            fg="#C5C7D0",
            bg="#1E222D",
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=2,
            cursor="hand2"
        )
        self.btn_hist_next.pack(side=tk.LEFT)
        self.btn_hist_next.bind("<Button-1>", lambda e: self.engine.history_next())

        self.btn_hist_latest = tk.Label(
            self.hist_bar,
            text="⚡ Свежий",
            fg="#00E676",
            bg="#1E222D",
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=2,
            cursor="hand2"
        )
        self.btn_hist_latest.pack(side=tk.RIGHT)
        self.btn_hist_latest.bind("<Button-1>", lambda e: self.engine.history_latest())

        # 1. КАРТОЧКА НАЙДЕННОЙ ИГРЫ / КОНТЕНТА
        self.game_frame = tk.Frame(self.main_content, bg="#211C38", padx=10, pady=8, highlightbackground="#7C4DFF", highlightthickness=1.5)
        self.lbl_game_title = tk.Label(
            self.game_frame,
            text="🎮 НАЙДЕНА ИГРА / ПРОЕКТ:",
            fg="#B388FF",
            bg="#211C38",
            font=("Segoe UI", 8, "bold")
        )
        self.lbl_game_title.pack(anchor="w")

        self.lbl_game_content = tk.Label(
            self.game_frame,
            text="—",
            fg="#FFFFFF",
            bg="#211C38",
            font=("Segoe UI", 9),
            wraplength=355,
            justify=tk.LEFT
        )
        self.lbl_game_content.pack(anchor="w", pady=(3, 0))

        # 2. БЛОК ОТВЕТА НА ТЕСТ / СУФЛЕРА / КРИПТО-СИГНАЛА
        self.answer_frame = tk.Frame(self.main_content, bg="#18382B", padx=10, pady=8, highlightbackground="#00E676", highlightthickness=1.5)
        
        ans_hdr = tk.Frame(self.answer_frame, bg="#18382B")
        ans_hdr.pack(fill=tk.X)

        self.lbl_answer_title = tk.Label(
            ans_hdr,
            text="💡 ОТВЕТ / СУФЛЕР / СИГНАЛ:",
            fg="#00E676",
            bg="#18382B",
            font=("Segoe UI", 8, "bold")
        )
        self.lbl_answer_title.pack(side=tk.LEFT)

        self.btn_copy_ans = tk.Label(
            ans_hdr,
            text="📋 Копировать",
            fg="#FFFFFF",
            bg="#25523F",
            font=("Segoe UI", 7, "bold"),
            padx=6,
            pady=1,
            cursor="hand2"
        )
        self.btn_copy_ans.pack(side=tk.RIGHT)
        self.btn_copy_ans.bind("<Button-1>", lambda e: self.copy_answer_to_clipboard())

        self.lbl_answer_text = tk.Label(
            self.answer_frame,
            text="—",
            fg="#FFFFFF",
            bg="#18382B",
            font=("Segoe UI", 9, "bold"),
            wraplength=365,
            justify=tk.LEFT
        )
        self.lbl_answer_text.pack(anchor="w", pady=(2, 0))

        # Строка статуса (прикреплена к самому низу)
        self.lbl_status = tk.Label(
            self.main_content,
            text="Готов к работе",
            fg="#9AA0A6",
            bg="#14171F",
            font=("Segoe UI", 8)
        )
        self.lbl_status.pack(side=tk.BOTTOM, fill=tk.X, pady=(4, 0))

        # 5. Нижняя панель действий (прикреплена над статусом)
        bottom_frame = tk.Frame(self.main_content, bg="#14171F")
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 0))

        # Верхняя линия кнопок: Экран, Область, Буфер
        actions_row1 = tk.Frame(bottom_frame, bg="#14171F")
        actions_row1.pack(fill=tk.X, pady=(0, 3))

        self.btn_analyze = tk.Button(
            actions_row1,
            text="⚡ Экран (Alt+X)",
            bg="#7C4DFF",
            fg="#FFFFFF",
            activebackground="#651FFF",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            font=("Segoe UI", 8, "bold"),
            pady=5,
            cursor="hand2",
            command=self.engine.analyze_now
        )
        self.btn_analyze.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.btn_sniper = tk.Button(
            actions_row1,
            text="🎯 Рамка (Alt+S)",
            bg="#211C38",
            fg="#B388FF",
            relief=tk.FLAT,
            font=("Segoe UI", 8, "bold"),
            pady=5,
            cursor="hand2",
            command=self.launch_sniper_mode
        )
        self.btn_sniper.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        self.btn_clipboard = tk.Button(
            actions_row1,
            text="📋 Буфер (Alt+B)",
            bg="#1A2733",
            fg="#64B5F6",
            relief=tk.FLAT,
            font=("Segoe UI", 8, "bold"),
            pady=5,
            cursor="hand2",
            command=self.engine.analyze_clipboard
        )
        self.btn_clipboard.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        # Вторая линия кнопок: Звук, Крипта
        actions_row2 = tk.Frame(bottom_frame, bg="#14171F")
        actions_row2.pack(fill=tk.X, pady=(0, 3))

        self.btn_audio = tk.Button(
            actions_row2,
            text="🎙️ Звук / Суфлер (Alt+V)",
            bg="#18382B",
            fg="#00E676",
            relief=tk.FLAT,
            font=("Segoe UI", 8, "bold"),
            pady=5,
            cursor="hand2",
            command=self.launch_audio_mode
        )
        self.btn_audio.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.btn_crypto = tk.Button(
            actions_row2,
            text="📈 Крипта (Alt+C)",
            bg="#10253F",
            fg="#64B5F6",
            relief=tk.FLAT,
            font=("Segoe UI", 8, "bold"),
            pady=5,
            cursor="hand2",
            command=lambda: self.engine.analyze_crypto()
        )
        self.btn_crypto.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        # Нижняя линия кнопок: Авто-режим, смена режима и сайт оплаты
        mode_row = tk.Frame(bottom_frame, bg="#14171F")
        mode_row.pack(fill=tk.X)

        self.btn_auto = tk.Button(
            mode_row,
            text="Авто: ВКЛ",
            bg="#2D3342",
            fg="#00E676",
            relief=tk.FLAT,
            font=("Segoe UI", 8, "bold"),
            pady=4,
            cursor="hand2",
            command=self.toggle_auto
        )
        self.btn_auto.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.btn_mode_switch = tk.Button(
            mode_row,
            text="🎓 Режим",
            bg="#1E222D",
            fg="#B388FF",
            relief=tk.FLAT,
            font=("Segoe UI", 8, "bold"),
            pady=4,
            cursor="hand2",
            command=self.engine.toggle_app_mode
        )
        self.btn_mode_switch.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        self.btn_clear = tk.Button(
            mode_row,
            text="🧹 Очистить",
            bg="#1E2332",
            fg="#E0E0E0",
            relief=tk.FLAT,
            font=("Segoe UI", 8, "bold"),
            pady=4,
            cursor="hand2",
            command=self.clear_display
        )
        self.btn_clear.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        # 4. ПОЛЕ БЫСТРОГО ВОПРОСА К ИИ (прикреплено над кнопками)
        quick_q_box = tk.Frame(self.main_content, bg="#1E222D", padx=6, pady=4, highlightbackground="#2D3342", highlightthickness=1)
        quick_q_box.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 0))

        self.entry_quick_q = tk.Entry(
            quick_q_box,
            bg="#14171F",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            relief=tk.FLAT,
            font=("Segoe UI", 9)
        )
        self.entry_quick_q.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 4))
        self.entry_quick_q.insert(0, "Спросить у ИИ (по экрану или любой вопрос)...")
        self.entry_quick_q.bind("<FocusIn>", self._clear_quick_q_placeholder)
        self.entry_quick_q.bind("<Return>", lambda e: self.submit_quick_question())
        self._enable_entry_paste(self.entry_quick_q)

        btn_ask = tk.Button(
            quick_q_box,
            text="Спросить",
            bg="#7C4DFF",
            fg="#FFFFFF",
            activebackground="#651FFF",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            font=("Segoe UI", 8, "bold"),
            padx=8,
            command=self.submit_quick_question
        )
        btn_ask.pack(side=tk.RIGHT)

        # 3. БЛОК ТЕЗИСОВ ВИДЕОРОЛИКА
        self.lbl_summary_header = tk.Label(
            self.main_content,
            text="📋 ТЕЗИСЫ ВИДЕОРОЛИКА / КОНСПЕКТ:",
            fg="#9AA0A6",
            bg="#14171F",
            font=("Segoe UI", 8, "bold")
        )
        self.lbl_summary_header.pack(anchor="w", pady=(6, 4))

        self.txt_summary = tk.Text(
            self.main_content,
            bg="#1E222D",
            fg="#E1E3E6",
            relief=tk.FLAT,
            wrap=tk.WORD,
            font=("Segoe UI", 9),
            padx=8,
            pady=6,
            height=4
        )
        self.txt_summary.insert(tk.END, "Запустите видео, стрим или тест...")
        self.txt_summary.config(state=tk.DISABLED)
        self.txt_summary.pack(fill=tk.BOTH, expand=True)

    def _enable_entry_paste(self, entry):
        def do_paste(event=None):
            self._clear_quick_q_placeholder(None)
            try:
                text = self.root.clipboard_get()
                try:
                    entry.delete("sel.first", "sel.last")
                except tk.TclError:
                    pass
                entry.insert(tk.INSERT, text)
            except tk.TclError:
                pass
            return "break"

        def on_ctrl_key(event):
            if event.keycode == 86:  # V / М
                return do_paste()
            elif event.keycode == 67:  # C / С
                entry.event_generate("<<Copy>>")
                return "break"
            elif event.keycode == 65:  # A / Ф
                entry.select_range(0, tk.END)
                return "break"

        entry.bind("<Control-KeyPress>", on_ctrl_key)

        menu = tk.Menu(entry, tearoff=0, bg="#1E222D", fg="#FFFFFF", activebackground="#7C4DFF")
        menu.add_command(label="📋 Вставить", command=do_paste)
        menu.add_command(label="Очистить", command=lambda: entry.delete(0, tk.END))
        entry.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    def _clear_quick_q_placeholder(self, event):
        if "Спросить" in self.entry_quick_q.get():
            self.entry_quick_q.delete(0, tk.END)

    def submit_quick_question(self):
        q = self.entry_quick_q.get().strip()
        if q and "Спросить" not in q:
            self.engine.ask_quick_question(q)
            self.entry_quick_q.delete(0, tk.END)

    def copy_answer_to_clipboard(self):
        text = self.lbl_answer_text.cget("text")
        if text and text != "—":
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.btn_copy_ans.config(text="✓ Скопировано!", fg="#00E676")
                self.root.after(1500, lambda: self.btn_copy_ans.config(text="📋 Копировать", fg="#FFFFFF"))
            except Exception:
                pass

    def setup_drag(self):
        self.header_frame.bind("<Button-1>", self.start_drag)
        self.header_frame.bind("<B1-Motion>", self.do_drag)
        self.lbl_title.bind("<Button-1>", self.start_drag)
        self.lbl_title.bind("<B1-Motion>", self.do_drag)

    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def do_drag(self, event):
        deltax = event.x - self.drag_x
        deltay = event.y - self.drag_y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def on_alpha_change(self, val):
        alpha = int(val) / 100.0
        self.root.wm_attributes("-alpha", alpha)

    def toggle_minimize(self):
        if not self.is_minimized:
            self.main_content.pack_forget()
            self.root.geometry(f"200x38+{self.root.winfo_x()}+{self.root.winfo_y()}")
            self.btn_min.config(text="□")
            self.is_minimized = True
        else:
            self.main_content.pack(fill=tk.BOTH, expand=True)
            self.root.geometry(f"{self.width}x{self.height}+{self.root.winfo_x()}+{self.root.winfo_y()}")
            self.btn_min.config(text="—")
            self.is_minimized = False

    def toggle_auto(self):
        self.engine.is_auto = not self.engine.is_auto
        if self.engine.is_auto:
            self.btn_auto.config(text="Авто: ВКЛ", fg="#00E676")
        else:
            self.btn_auto.config(text="Авто: ВЫКЛ", fg="#FF5252")

    def close_overlay(self):
        self.root.withdraw()

    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.after(100, self.apply_stealth_mode)

    def launch_sniper_mode(self):
        """Запуск режима снайперского прицела с рамкой"""
        self.root.after(0, lambda: SniperAreaSelector(
            parent_root=self.root,
            on_region_selected=self.engine.analyze_region,
            is_stealth=self.is_stealth
        ))

    def launch_audio_mode(self):
        """Запуск голосового суфлера (слух ИИ из наушников/видео)"""
        self.engine.listen_and_answer()

    def toggle_stealth_hide(self):
        """Экстренное скрытие / показ оверлея по горячей клавише Alt+Z"""
        def _toggle():
            try:
                if self.root.winfo_ismapped() and not self.root.state() == "withdrawn":
                    self.root.withdraw()
                else:
                    self.show()
            except Exception:
                self.show()
        self.root.after(0, _toggle)

    def clear_display(self):
        """Очищает экран суфлера и текущие результаты"""
        self.lbl_answer_text.config(text="—")
        if self.answer_frame.winfo_ismapped():
            self.answer_frame.pack_forget()
        if self.game_frame.winfo_ismapped():
            self.game_frame.pack_forget()
        self.txt_summary.config(state=tk.NORMAL)
        self.txt_summary.delete("1.0", tk.END)
        self.txt_summary.insert(tk.END, "Экран очищен. Нажмите Alt+X, Alt+S или Alt+B для анализа.")
        self.txt_summary.config(state=tk.DISABLED)
        self.lbl_status.config(text="Экран очищен")

    def on_engine_update(self, data):
        self.root.after(0, lambda: self._apply_update(data))

    def _apply_update(self, data):
        # 0. Статус Безлимита
        self.lbl_quota.config(text="⚡ БЕЗЛИМИТ", fg="#00E676", cursor="arrow")

        # Режим приложения (Учеба / Крипто-Радар)
        app_mode = data.get("app_mode", "study")
        if app_mode == "crypto":
            self.btn_mode_hdr.config(text="📈 Крипта", fg="#64B5F6")
            self.btn_mode_switch.config(text="📈 Режим: Крипта", fg="#64B5F6")
            self.lbl_answer_title.config(text="📈 КРИПТО-СИГНАЛ / ТРЕЙДИНГ:", fg="#64B5F6", bg="#0D2137")
            self.lbl_answer_text.config(bg="#0D2137")
            self.answer_frame.config(bg="#0D2137", highlightbackground="#1E88E5")
            self.lbl_summary_header.config(text="📊 АНАЛИЗ ГРАФИКА / СТАКАНА:")
            if "Спросить у ИИ" in self.entry_quick_q.get():
                self.entry_quick_q.delete(0, tk.END)
                self.entry_quick_q.insert(0, "Спросить по крипте (BTC, SOL, шорт/лонг?)...")
        else:
            self.btn_mode_hdr.config(text="🎓 Учёба", fg="#B388FF")
            self.btn_mode_switch.config(text="🎓 Режим: Учёба", fg="#B388FF")
            self.lbl_answer_title.config(text="💡 ОТВЕТ / СУФЛЕР К ТЕСТУ:", fg="#00E676", bg="#18382B")
            self.lbl_answer_text.config(bg="#18382B")
            self.answer_frame.config(bg="#18382B", highlightbackground="#00E676")
            self.lbl_summary_header.config(text="📋 ТЕЗИСЫ ВИДЕОРОЛИКА / КОНСПЕКТ:")
            if "Спросить по крипте" in self.entry_quick_q.get():
                self.entry_quick_q.delete(0, tk.END)
                self.entry_quick_q.insert(0, "Спросить у ИИ (по экрану или любой вопрос)...")

        # Бегущая строка крипто-котировок
        ticker = data.get("crypto_ticker", "")
        if ticker:
            self.lbl_crypto_ticker.config(text=ticker)

        # Навигация по истории ответов ИИ
        h_cnt = data.get("history_count", 0)
        h_cur = data.get("history_current", 0)
        is_latest = data.get("history_is_latest", True)
        if h_cnt > 0:
            self.lbl_hist_counter.config(text=f"● Ответ {h_cur}/{h_cnt}", fg="#00E676" if is_latest else "#FFD54F")
            if is_latest:
                self.btn_hist_latest.config(text="⚡ Свежий", fg="#00E676")
            else:
                self.btn_hist_latest.config(text="⚡ К свежему", fg="#FFD54F")
        else:
            self.lbl_hist_counter.config(text="● История пуста", fg="#9AA0A6")

        # 1. Карточка игры
        game_info = data.get("game_info", "")
        if game_info:
            self.lbl_game_content.config(text=game_info)
            if not self.game_frame.winfo_ismapped():
                self.game_frame.pack(fill=tk.X, before=self.lbl_summary_header, pady=(0, 6))
        else:
            if self.game_frame.winfo_ismapped():
                self.game_frame.pack_forget()

        # 2. Карточка ответа / криптосигнала
        ans = data.get("answer", "")
        if ans:
            self.lbl_answer_text.config(text=ans)
            if not self.answer_frame.winfo_ismapped():
                self.answer_frame.pack(fill=tk.X, before=self.lbl_summary_header, pady=(0, 6))
        else:
            if self.answer_frame.winfo_ismapped():
                self.answer_frame.pack_forget()

        # 3. Тезисы видео / анализ
        summary = data.get("summary", "")
        if summary:
            self.txt_summary.config(state=tk.NORMAL)
            self.txt_summary.delete("1.0", tk.END)
            self.txt_summary.insert(tk.END, summary)
            self.txt_summary.config(state=tk.DISABLED)

        st = data.get("status", "")
        self.lbl_status.config(text=f"{st} | Alt+Z:Скрыть Alt+X:Скан Alt+C:Крипта Alt+←/→:История")
