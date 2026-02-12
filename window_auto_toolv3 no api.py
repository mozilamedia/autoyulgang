import tkinter as tk
from tkinter import ttk
import pyautogui
import win32gui
import win32con
import win32api
import cv2
import numpy as np
import json
import random
import string
import time
import threading
from pathlib import Path
from script_editor import ScriptEditor


class WindowAutoTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Window Auto Tool")

        self.windows_list = []
        self.minimized_windows = set()
        self.templates = []
        self.is_running = False
        self.auto_thread = None

        self.script_data = None
        self.use_script_runtime = False

        self.setup_ui()
        self.load_templates()
        self.load_script()

    # ================= UI =================
    def setup_ui(self):
        self.root.geometry("400x450")
        self.root.resizable(False, False)

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Window Auto Tool",
                  font=("Segoe UI", 14, "bold")).pack(pady=(0, 10))

        # Start / Stop
        row1 = ttk.Frame(main)
        row1.pack(fill="x", pady=5)

        self.start_btn = ttk.Button(row1, text="▶ Start", command=self.start_automation)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.stop_btn = ttk.Button(row1, text="■ Stop", command=self.stop_automation, state=tk.DISABLED)
        self.stop_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))

        # Loop delay
        delay_frame = ttk.LabelFrame(main, text="Loop Delay")
        delay_frame.pack(fill="x", pady=8)

        ttk.Label(delay_frame, text="Delay (seconds):").pack(side="left", padx=5)
        self.delay_var = tk.IntVar(value=300)
        self.delay_spinbox = ttk.Spinbox(delay_frame, from_=5, to=3600,
                                         textvariable=self.delay_var, width=8)
        self.delay_spinbox.pack(side="right", padx=5)

        # Script mode
        script_frame = ttk.LabelFrame(main, text="Script Mode")
        script_frame.pack(fill="x", pady=8)

        self.script_mode_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            script_frame,
            text="Enable Script (script.json)",
            variable=self.script_mode_var
        ).pack(anchor="w", padx=5, pady=3)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=5)

        ttk.Button(btn_frame, text="Reload Script", command=self.load_script)\
            .pack(side="left", expand=True, fill="x", padx=(0, 5))
        ttk.Button(btn_frame, text="Edit Script", command=self.open_script_editor)\
            .pack(side="left", expand=True, fill="x", padx=(5, 0))

        # Minimize
        min_frame = ttk.LabelFrame(main, text="Auto Minimize")
        min_frame.pack(fill="x", pady=8)

        self.minimize_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(min_frame, text="Minimize after",
                        variable=self.minimize_var).pack(side="left", padx=5)

        self.minimize_delay_var = tk.IntVar(value=3)
        ttk.Spinbox(min_frame, from_=1, to=10,
                    textvariable=self.minimize_delay_var,
                    width=5).pack(side="left", padx=(5, 2))

        ttk.Label(min_frame, text="seconds").pack(side="left")

        # Status
        info = ttk.LabelFrame(main, text="Status")
        info.pack(fill="both", expand=True, pady=10)

        self.script_label = ttk.Label(info, text="Script: not loaded", wraplength=360)
        self.script_label.pack(anchor="w", padx=5, pady=4)

        self.windows_count_label = ttk.Label(info, text="Windows: 0 detected")
        self.windows_count_label.pack(anchor="w", padx=5, pady=4)

    # ================= CORE =================
    def load_templates(self):
        self.templates.clear()
        d = Path("templates")
        d.mkdir(exist_ok=True)

        for f in d.iterdir():
            if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp"]:
                img = cv2.imread(str(f))
                if img is not None:
                    self.templates.append({"name": f.name, "image": img})

        self.templates.sort(key=lambda x: x["name"])

    def load_script(self):
        p = Path("script.json")
        if not p.exists():
            self.script_data = None
            self.script_label.config(text="Script: not found")
            return

        with open(p, "r", encoding="utf-8") as f:
            self.script_data = json.load(f)

        self.script_label.config(
            text=f"Script loaded ({len(self.script_data.get('steps', []))} steps)"
        )

    def open_script_editor(self):
        ScriptEditor(self.root)

    def find_and_store_windows(self):
        self.windows_list.clear()

        def cb(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                if "YB_OnlineClient" in win32gui.GetWindowText(hwnd):
                    self.windows_list.append(hwnd)

        win32gui.EnumWindows(cb, None)
        self.windows_count_label.config(
            text=f"Windows: {len(self.windows_list)} detected"
        )
        return len(self.windows_list)

    def activate_window(self, hwnd):
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.3)
            return True
        except:
            return False

    def find_image_on_screen(self, template):
        screenshot = pyautogui.screenshot()
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val >= 0.8:
            h, w = template.shape[:2]
            return max_loc[0] + w // 2, max_loc[1] + h // 2
        return None

    # ================= LOOP =================
    def automation_loop(self):
        while self.is_running:
            for hwnd in self.windows_list:
                if not self.is_running:
                    break

                if not self.activate_window(hwnd):
                    continue

                if self.use_script_runtime and self.script_data:
                    completed = set()
                    for step in self.script_data["steps"]:
                        deps = step.get("depends_on", [])
                        mode = step.get("depends_mode", "any")

                        if deps:
                            ok = all(d in completed for d in deps) if mode == "all" \
                                 else any(d in completed for d in deps)
                            if not ok:
                                continue

                        tpl = next((t for t in self.templates
                                    if t["name"] == step["template"]), None)
                        if not tpl:
                            continue

                        pos = self.find_image_on_screen(tpl["image"])
                        if pos:
                            pyautogui.click(*pos)
                            completed.add(step.get("id", step["template"]))
                            time.sleep(step.get("wait_after_click", 0))
                else:
                    for tpl in self.templates:
                        pos = self.find_image_on_screen(tpl["image"])
                        if pos:
                            pyautogui.click(*pos)
                            time.sleep(0.5)

                if self.minimize_var.get():
                    time.sleep(self.minimize_delay_var.get())
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                    self.minimized_windows.add(hwnd)

                time.sleep(0.5)

            time.sleep(self.delay_var.get())

    # ================= CONTROL =================
    def start_automation(self):
        if not self.templates:
            return
        if self.find_and_store_windows() == 0:
            return

        self.use_script_runtime = self.script_mode_var.get()
        self.is_running = True
        self.auto_thread = threading.Thread(
            target=self.automation_loop, daemon=True
        )
        self.auto_thread.start()

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

    def stop_automation(self):
        self.is_running = False

        for hwnd in list(self.minimized_windows):
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            except:
                pass
        self.minimized_windows.clear()

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    WindowAutoTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
