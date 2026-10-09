import os
import sys
import json
import time

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class AuthManager:
    """
    Менеджер сессии и статистики запросов Screen AI Assistant.
    Полностью открытая (Open Source) версия:
    - Без искусственных ограничений и лимитов
    - Все функции (Снайпер, Голос, Анализ экрана, Крипто-радар) разблокированы навсегда
    """
    def __init__(self, session_path=None):
        if session_path is None:
            session_path = os.path.join(get_app_dir(), "user_session.json")
        self.session_path = session_path
        self.is_pro = True
        self.is_unlimited = True
        self.pro_plan_name = "Open Source • Полный безлимит"
        self.total_requests = 0
        self.requests_used_today = 0
        self.last_reset_date = time.strftime("%Y-%m-%d")

        self.load_session()

    def get_current_date(self):
        return time.strftime("%Y-%m-%d")

    def check_and_reset_daily(self):
        current_date = self.get_current_date()
        if self.last_reset_date != current_date:
            self.last_reset_date = current_date
            self.requests_used_today = 0
            self.save_session()

    def get_remaining_requests(self):
        return "∞ (Безлимит)"

    def can_make_request(self):
        return True, "Безлимитный доступ"

    def use_request(self):
        self.check_and_reset_daily()
        self.total_requests += 1
        self.requests_used_today += 1
        self.save_session()

    def load_session(self):
        if os.path.exists(self.session_path):
            try:
                with open(self.session_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.total_requests = data.get("total_requests", 0)
                    self.requests_used_today = data.get("requests_used_today", 0)
                    self.last_reset_date = data.get("last_reset_date", time.strftime("%Y-%m-%d"))
            except Exception:
                pass

    def save_session(self):
        try:
            with open(self.session_path, "w", encoding="utf-8") as f:
                json.dump({
                    "edition": "Open Source Community Edition",
                    "license": "MIT (Free & Unlimited)",
                    "total_requests": self.total_requests,
                    "requests_used_today": self.requests_used_today,
                    "last_reset_date": self.last_reset_date
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
