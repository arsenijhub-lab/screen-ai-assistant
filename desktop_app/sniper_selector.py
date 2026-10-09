import io
import ctypes
import tkinter as tk
from PIL import ImageGrab


class SniperAreaSelector:
    """
    Полноэкранный снайперский прицел для выделения конкретной задачи, чертежа или теста рамкой.
    Полностью скрыт от демонстрации экрана (Stealth Mode).
    """

    def __init__(self, parent_root, on_region_selected, is_stealth=True):
        self.parent_root = parent_root
        self.on_region_selected = on_region_selected
        self.is_stealth = is_stealth

        self.top = tk.Toplevel(parent_root)
        self.top.withdraw()
        self.top.overrideredirect(True)
        self.top.wm_attributes("-topmost", True)
        self.top.wm_attributes("-alpha", 0.35)
        self.top.configure(bg="#0B0D13", cursor="crosshair")

        sw = self.top.winfo_screenwidth()
        sh = self.top.winfo_screenheight()
        self.top.geometry(f"{sw}x{sh}+0+0")

        self.canvas = tk.Canvas(self.top, bg="#0B0D13", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Подсказка сверху экрана
        self.canvas.create_rectangle(
            sw // 2 - 260, 20, sw // 2 + 260, 62,
            fill="#1E222D", outline="#00E676", width=2
        )
        self.canvas.create_text(
            sw // 2, 41,
            text="🎯 Выделите задачу или область мышкой (Esc / ПКМ — отмена)",
            fill="#00E676",
            font=("Segoe UI", 11, "bold")
        )

        self.start_x = 0
        self.start_y = 0
        self.rect_id = None

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<ButtonPress-3>", lambda e: self.cancel())
        self.top.bind("<Escape>", lambda e: self.cancel())

        self.top.deiconify()
        self.top.lift()
        self.top.focus_force()
        self._apply_stealth()

    def _apply_stealth(self):
        if not self.is_stealth:
            return
        try:
            self.top.update_idletasks()
            hwnd = self.top.winfo_id()
            parent_hwnd = ctypes.windll.user32.GetParent(hwnd)
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000011)
            if parent_hwnd:
                ctypes.windll.user32.SetWindowDisplayAffinity(parent_hwnd, 0x00000011)
        except Exception:
            pass

    def on_press(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="#00E676", width=3, fill="#211C38"
        )

    def on_drag(self, event):
        if self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x_root, event.y_root)

    def on_release(self, event):
        end_x = event.x_root
        end_y = event.y_root
        self.top.destroy()

        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        if (x2 - x1) < 15 or (y2 - y1) < 15:
            return

        # Небольшая пауза, чтобы окно прицела исчезло перед снимком
        self.parent_root.after(80, lambda: self._capture_and_send(x1, y1, x2, y2))

    def _capture_and_send(self, x1, y1, x2, y2):
        try:
            cropped = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            buf = io.BytesIO()
            cropped.save(buf, format="JPEG", quality=92)
            if self.on_region_selected:
                self.on_region_selected(buf.getvalue())
        except Exception as e:
            print(f"Ошибка захвата области: {e}")

    def cancel(self):
        try:
            self.top.destroy()
        except Exception:
            pass
