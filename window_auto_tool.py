import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pyautogui
import win32gui
import win32con
import win32api
import win32process
import cv2
import numpy as np
import json
import random
import string
import time
import threading
import requests
import psutil
from pathlib import Path
from datetime import datetime
from script_editor import ScriptEditor


class CombinedTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Window Auto & Monitor Tool")
        self.root.geometry("400x650")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Auto Tool vars
        self.windows_list = []
        self.minimized_windows = set()
        self.templates = []
        self.is_auto_running = False
        self.auto_thread = None
        self.script_data = None
        self.use_script_runtime = False

        # Monitor vars
        self.is_monitor_running = False
        self.monitor_thread = None
        self.monitor_stop_event = threading.Event()
        self.config_file = "config.json"
        self.window_keyword = "YB_OnlineClient"  # Default window name
        
        # Step counting vars
        self.step_counters = {}  # {window_number: count}
        self.step_last_time = {}  # {window_number: timestamp}
        self.track_step_enabled = False
        self.milestone_enabled = False
        self.auto_reset_enabled = False
        self.reset_checker_thread = None
        self.reset_checker_stop = threading.Event()

        # Setup UI first (fast)
        self.setup_ui()
        
        # Load config (fast)
        self.load_monitor_config()
        
        # Load heavy stuff in background
        threading.Thread(target=self.load_heavy_resources, daemon=True).start()

    # ================= UI SETUP =================
    def setup_ui(self):
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab 1: Auto Tool
        self.tab_auto = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_auto, text="Auto Tool")
        self.setup_auto_tab()

        # Tab 2: Monitor
        self.tab_monitor = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_monitor, text="Monitor")
        self.setup_monitor_tab()

    def setup_auto_tab(self):
        main = ttk.Frame(self.tab_auto, padding=12)
        main.pack(fill="both", expand=True)

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

        # Dời 2 nút vào đây
        btn_frame = ttk.Frame(script_frame)
        btn_frame.pack(fill="x", padx=5, pady=(0, 5))

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

        self.script_label = ttk.Label(info, text="Script: not loaded", wraplength=400)
        self.script_label.pack(anchor="w", padx=5, pady=4)

        self.windows_count_label = ttk.Label(info, text="Windows: 0 detected")
        self.windows_count_label.pack(anchor="w", padx=5, pady=4)

        # Monitor status
        monitor_status_frame = ttk.Frame(info)
        monitor_status_frame.pack(anchor="w", padx=5, pady=4)

        ttk.Label(monitor_status_frame, text="Monitor:").pack(side="left")
        
        self.monitor_status_var = tk.StringVar(value="🔴 Đã dừng")
        self.lbl_monitor_status = ttk.Label(
            monitor_status_frame,
            textvariable=self.monitor_status_var,
            foreground="red"
        )
        self.lbl_monitor_status.pack(side="left", padx=5)

        self.status_canvas = tk.Canvas(monitor_status_frame, width=16, height=16, highlightthickness=0)
        self.status_canvas.pack(side="left")
        self.status_dot = self.status_canvas.create_oval(2, 2, 14, 14, fill="red", outline="")

        self.lbl_count = ttk.Label(info, text="Cửa sổ đang chạy: 0", foreground="blue")
        self.lbl_count.pack(anchor="w", padx=5, pady=4)

        # Log
        ttk.Label(main, text="Log Monitor").pack(anchor="w", pady=(10, 2))
        self.txt_log = scrolledtext.ScrolledText(main, height=8)
        self.txt_log.pack(fill="both", expand=True, pady=5)

    def setup_monitor_tab(self):
        main = ttk.Frame(self.tab_monitor, padding=12)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Monitor Settings",
                  font=("Segoe UI", 12, "bold")).pack(pady=(0, 10))

        # Window name
        ttk.Label(main, text="Tên cửa sổ cần quét:").pack(anchor="w", pady=(5, 0))
        self.entry_window_name = ttk.Entry(main)
        self.entry_window_name.insert(0, "YB_OnlineClient")
        self.entry_window_name.pack(fill="x", pady=2)

        # Machine name
        ttk.Label(main, text="Tên máy (mặc định: PC):").pack(anchor="w", pady=(10, 0))
        self.entry_machine = ttk.Entry(main)
        self.entry_machine.pack(fill="x", pady=2)

        # Discord
        ttk.Label(main, text="Discord Webhook:").pack(anchor="w", pady=(10, 0))
        self.entry_discord = ttk.Entry(main)
        self.entry_discord.pack(fill="x", pady=2)

        # Telegram
        ttk.Label(main, text="Telegram Bot Token:").pack(anchor="w", pady=(10, 0))
        self.entry_tg_token = ttk.Entry(main)
        self.entry_tg_token.pack(fill="x", pady=2)

        ttk.Label(main, text="Telegram Chat ID:").pack(anchor="w", pady=(5, 0))
        self.entry_tg_chat = ttk.Entry(main)
        self.entry_tg_chat.pack(fill="x", pady=2)

        # Step tracking options
        track_frame = ttk.LabelFrame(main, text="Thông báo Step", padding=8)
        track_frame.pack(fill="x", pady=(15, 0))

        # Checkbox 1: Track each step
        self.track_step_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(track_frame, text="Thông báo mỗi lần hoàn thành step",
                       variable=self.track_step_var).pack(anchor="w", pady=2)

        ttk.Label(track_frame, text="Template (.png):").pack(anchor="w", pady=(5, 0))
        self.entry_track_template = ttk.Entry(track_frame)
        self.entry_track_template.pack(fill="x", pady=2)

        ttk.Label(track_frame, text="Nội dung thông báo:").pack(anchor="w", pady=(5, 0))
        self.entry_track_message = ttk.Entry(track_frame)
        self.entry_track_message.insert(0, "đã hoàn thành nhiệm vụ")
        self.entry_track_message.pack(fill="x", pady=2)

        # Checkbox 2 & 3: Milestone and Auto reset (same row)
        milestone_check_row = ttk.Frame(track_frame)
        milestone_check_row.pack(fill="x", pady=(10, 2))
        
        self.milestone_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(milestone_check_row, text="Thông báo khi đạt mốc",
                       variable=self.milestone_var).pack(side="left")
        
        self.auto_reset_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(milestone_check_row, text="Auto reset sau",
                       variable=self.auto_reset_var).pack(side="left", padx=(20, 0))

        # Milestone settings
        milestone_row = ttk.Frame(track_frame)
        milestone_row.pack(fill="x", pady=2)

        ttk.Label(milestone_row, text="Số lần:").pack(side="left", padx=(0, 5))
        self.entry_milestone_count = ttk.Spinbox(milestone_row, from_=1, to=1000, width=8)
        self.entry_milestone_count.set(10)
        self.entry_milestone_count.pack(side="left")
        
        ttk.Label(milestone_row, text="| Reset sau:").pack(side="left", padx=(20, 5))
        self.entry_reset_minutes = ttk.Spinbox(milestone_row, from_=1, to=1440, width=8)
        self.entry_reset_minutes.set(30)
        self.entry_reset_minutes.pack(side="left")
        ttk.Label(milestone_row, text="phút").pack(side="left", padx=(5, 0))

        ttk.Label(track_frame, text="Nội dung thông báo mốc:").pack(anchor="w", pady=(5, 0))
        self.entry_milestone_message = ttk.Entry(track_frame)
        self.entry_milestone_message.insert(0, "đã đạt mốc")
        self.entry_milestone_message.pack(fill="x", pady=2)

    # ================= AUTO TOOL CORE =================
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
        
        # Update display if UI is ready (thread-safe)
        if hasattr(self, 'script_label'):
            self.root.after(0, self.update_template_count)

    def load_script(self):
        p = Path("script.json")
        if not p.exists():
            self.script_data = None
            if hasattr(self, 'script_label'):
                self.root.after(0, lambda: self.script_label.config(
                    text=f"Script: not found | Templates: {len(self.templates)}"
                ))
            return

        with open(p, "r", encoding="utf-8") as f:
            self.script_data = json.load(f)

        if hasattr(self, 'script_label'):
            self.root.after(0, lambda: self.script_label.config(
                text=f"Script: {len(self.script_data.get('steps', []))} steps | Templates: {len(self.templates)}"
            ))

    def update_template_count(self):
        """Update template count in script label"""
        if self.script_data:
            self.script_label.config(
                text=f"Script: {len(self.script_data.get('steps', []))} steps | Templates: {len(self.templates)}"
            )
        else:
            self.script_label.config(text=f"Script: not found | Templates: {len(self.templates)}")

    def initial_scan(self):
        """Scan windows and update count when tool opens"""
        count = self.find_and_store_windows()
        text = f"Windows: {count} detected" if count > 0 else "Windows: 0 detected"
        self.root.after(0, lambda: self.windows_count_label.config(text=text))

    def load_heavy_resources(self):
        """Load templates and scan windows in background thread"""
        # Load templates (heavy - OpenCV)
        self.load_templates()
        
        # Load script (light)
        self.load_script()
        
        # Scan windows (medium)
        self.initial_scan()

    def open_script_editor(self):
        ScriptEditor(self.root)

    def find_and_store_windows(self):
        self.windows_list.clear()

        def cb(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                if self.window_keyword in win32gui.GetWindowText(hwnd):
                    self.windows_list.append(hwnd)

        win32gui.EnumWindows(cb, None)
        
        # Only update label if called from main thread (not from initial scan)
        if hasattr(self, 'windows_count_label') and threading.current_thread() == threading.main_thread():
            self.windows_count_label.config(
                text=f"Windows: {len(self.windows_list)} detected"
            )
        
        return len(self.windows_list)

    def activate_window(self, hwnd):
        try:
            # Check if minimized first
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(2)  # Tăng lên 2s để window restore hoàn toàn
            
            # Make sure window is visible
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            time.sleep(0.3)
            
            # Force window to front
            win32gui.SetForegroundWindow(hwnd)
            
            # Force refresh/redraw window
            win32gui.UpdateWindow(hwnd)
            
            time.sleep(0.5)
            return True
        except Exception as e:
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

    def automation_loop(self):
        hwnd_to_number = {}  # Map hwnd to window number for step tracking
        window_counter = 0
        
        while self.is_auto_running:
            for hwnd in self.windows_list:
                if not self.is_auto_running:
                    break

                # Assign window number if new
                if hwnd not in hwnd_to_number:
                    window_counter += 1
                    hwnd_to_number[hwnd] = window_counter
                    self.step_counters[window_counter] = 0

                window_num = hwnd_to_number[hwnd]

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
                            
                            # Check if this is the tracked template
                            if self.track_step_enabled and step["template"] == self.entry_track_template.get().strip():
                                self.handle_step_tracking(window_num)
                            
                            time.sleep(step.get("wait_after_click", 0))
                else:
                    for tpl in self.templates:
                        pos = self.find_image_on_screen(tpl["image"])
                        if pos:
                            pyautogui.click(*pos)
                            
                            # Check if this is the tracked template
                            if self.track_step_enabled and tpl["name"] == self.entry_track_template.get().strip():
                                self.handle_step_tracking(window_num)
                            
                            time.sleep(0.5)

                if self.minimize_var.get():
                    time.sleep(self.minimize_delay_var.get())
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                    self.minimized_windows.add(hwnd)

                time.sleep(0.5)

            time.sleep(self.delay_var.get())

    # ================= MONITOR CORE =================
    def load_monitor_config(self):
        if Path(self.config_file).exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if "window_name" in cfg:
                    self.entry_window_name.delete(0, tk.END)
                    self.entry_window_name.insert(0, cfg.get("window_name", "YB_OnlineClient"))
                
                self.entry_machine.insert(0, cfg.get("machine", ""))
                self.entry_discord.insert(0, cfg.get("discord", ""))
                self.entry_tg_token.insert(0, cfg.get("tg_token", ""))
                self.entry_tg_chat.insert(0, cfg.get("tg_chat", ""))
                
                # Load step tracking settings
                if "track_template" in cfg:
                    self.entry_track_template.delete(0, tk.END)
                    self.entry_track_template.insert(0, cfg.get("track_template", ""))
                
                if "track_message" in cfg:
                    self.entry_track_message.delete(0, tk.END)
                    self.entry_track_message.insert(0, cfg.get("track_message", "đã hoàn thành nhiệm vụ"))
                
                if "milestone_count" in cfg:
                    self.entry_milestone_count.set(cfg.get("milestone_count", 10))
                
                if "milestone_message" in cfg:
                    self.entry_milestone_message.delete(0, tk.END)
                    self.entry_milestone_message.insert(0, cfg.get("milestone_message", "đã đạt mốc"))
                
                if "reset_minutes" in cfg:
                    self.entry_reset_minutes.set(cfg.get("reset_minutes", 30))
                
                # Load checkbox states (Monitor tab)
                self.track_step_var.set(cfg.get("track_step_enabled", False))
                self.milestone_var.set(cfg.get("milestone_enabled", False))
                self.auto_reset_var.set(cfg.get("auto_reset_enabled", False))
                
                # Load checkbox states (Auto tab)
                self.script_mode_var.set(cfg.get("script_mode_enabled", True))
                self.minimize_var.set(cfg.get("auto_minimize_enabled", False))
                
                # Load delay settings
                if "loop_delay" in cfg:
                    self.delay_var.set(cfg.get("loop_delay", 300))
                if "minimize_delay" in cfg:
                    self.minimize_delay_var.set(cfg.get("minimize_delay", 3))

    def save_monitor_config(self, cfg):
        cfg["window_name"] = self.window_keyword  # Save current window name
        
        # Save step tracking settings
        cfg["track_template"] = self.entry_track_template.get().strip()
        cfg["track_message"] = self.entry_track_message.get().strip()
        cfg["milestone_count"] = int(self.entry_milestone_count.get())
        cfg["milestone_message"] = self.entry_milestone_message.get().strip()
        cfg["reset_minutes"] = int(self.entry_reset_minutes.get())
        
        # Save checkbox states (Monitor tab)
        cfg["track_step_enabled"] = self.track_step_var.get()
        cfg["milestone_enabled"] = self.milestone_var.get()
        cfg["auto_reset_enabled"] = self.auto_reset_var.get()
        
        # Save checkbox states (Auto tab)
        cfg["script_mode_enabled"] = self.script_mode_var.get()
        cfg["auto_minimize_enabled"] = self.minimize_var.get()
        
        # Save delay settings
        cfg["loop_delay"] = self.delay_var.get()
        cfg["minimize_delay"] = self.minimize_delay_var.get()
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)

    def send_discord(self, webhook, msg):
        if webhook.strip():
            try:
                requests.post(webhook, json={"content": msg}, timeout=5)
            except:
                pass

    def send_telegram(self, token, chat_id, msg):
        if token.strip() and chat_id.strip():
            try:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url, data={
                    "chat_id": chat_id,
                    "text": msg
                }, timeout=5)
            except:
                pass

    def notify(self, cfg, msg):
        self.send_discord(cfg.get("discord", ""), msg)
        self.send_telegram(cfg.get("tg_token", ""), cfg.get("tg_chat", ""), msg)

    def log_monitor(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.txt_log.insert(tk.END, f"[{ts}] {msg}\n")
        self.txt_log.see(tk.END)

    def handle_step_tracking(self, window_num):
        """Handle step tracking and milestone notifications"""
        from datetime import datetime
        
        current_time = time.time()
        
        # Update counter and timestamp
        self.step_counters[window_num] = self.step_counters.get(window_num, 0) + 1
        self.step_last_time[window_num] = current_time
        count = self.step_counters[window_num]
        
        machine_name = self.entry_machine.get().strip() or "PC"
        now = datetime.now()
        
        cfg = {
            "machine": machine_name,
            "discord": self.entry_discord.get().strip(),
            "tg_token": self.entry_tg_token.get().strip(),
            "tg_chat": self.entry_tg_chat.get().strip()
        }
        
        # Check if reached milestone
        reached_milestone = False
        if self.milestone_var.get():
            try:
                milestone = int(self.entry_milestone_count.get())
                if count >= milestone:
                    reached_milestone = True
                    milestone_msg = self.entry_milestone_message.get().strip()
                    msg = f"🎯 Máy {machine_name}: Cửa sổ {window_num} {milestone_msg} ({count}/{milestone}) - {now.strftime('%d/%m %H:%M')}"
                    self.notify(cfg, msg)
                    self.log_monitor(f"Cửa sổ {window_num}: Đạt mốc {milestone} lần - Reset counter")
                    # Reset counter
                    self.step_counters[window_num] = 0
                    self.step_last_time[window_num] = current_time
            except:
                pass
        
        # Send notification for each step completion (only if NOT reached milestone)
        if self.track_step_var.get() and not reached_milestone:
            message = self.entry_track_message.get().strip()
            msg = f"✅ Máy {machine_name}: Cửa sổ {window_num} {message} (lần {count}) - {now.strftime('%d/%m %H:%M')}"
            self.notify(cfg, msg)
            self.log_monitor(f"Cửa sổ {window_num}: {message} (lần {count})")

    def reset_checker_loop(self):
        """Background thread to check and reset counters based on time"""
        while not self.reset_checker_stop.is_set():
            if self.auto_reset_enabled:
                try:
                    reset_minutes = int(self.entry_reset_minutes.get())
                    current_time = time.time()
                    
                    for window_num in list(self.step_last_time.keys()):
                        if window_num in self.step_counters and self.step_counters[window_num] > 0:
                            time_diff = (current_time - self.step_last_time[window_num]) / 60
                            
                            if time_diff >= reset_minutes:
                                self.log_monitor(f"Cửa sổ {window_num}: Auto reset (không hoàn thành trong {reset_minutes} phút)")
                                self.step_counters[window_num] = 0
                                # Keep last_time to avoid repeated resets
                                self.step_last_time[window_num] = current_time
                except:
                    pass
            
            # Check every 30 seconds
            time.sleep(30)

    def find_monitor_pids(self):
        pids = set()

        def cb(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if self.window_keyword in title:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    pids.add(pid)

        win32gui.EnumWindows(cb, None)
        return pids

    def monitor_loop(self, cfg):
        tracked = set()
        notified = set()
        pid_to_number = {}  # Map PID to window number
        window_counter = 0

        self.log_monitor("Bắt đầu theo dõi")

        while not self.monitor_stop_event.is_set():
            current = self.find_monitor_pids()
            self.lbl_count.config(text=f"Cửa sổ đang chạy: {len(current)}")

            for pid in current:
                if pid not in tracked:
                    window_counter += 1
                    pid_to_number[pid] = window_counter
                tracked.add(pid)

            for pid in list(tracked):
                if not psutil.pid_exists(pid):
                    if pid not in notified:
                        now = datetime.now()
                        window_num = pid_to_number.get(pid, "?")
                        msg = f"🚨 Máy {cfg['machine']}: Cửa sổ {window_num} đóng ({now.strftime('%d/%m %H:%M')})"
                        
                        self.notify(cfg, msg)
                        self.log_monitor(f"Cửa sổ {window_num} (PID {pid}) đã đóng – gửi cảnh báo")
                        notified.add(pid)
                    tracked.remove(pid)

            time.sleep(2)

        self.log_monitor("Đã dừng theo dõi")

    def set_monitor_inputs_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.entry_machine.config(state=state)
        self.entry_discord.config(state=state)
        self.entry_tg_token.config(state=state)
        self.entry_tg_chat.config(state=state)

    def set_monitor_status_icon(self, color):
        self.status_canvas.itemconfig(self.status_dot, fill=color)

    def start_monitor(self):
        if self.is_monitor_running:
            return

        machine_name = self.entry_machine.get().strip()
        if not machine_name:
            machine_name = "PC"

        cfg = {
            "machine": machine_name,
            "discord": self.entry_discord.get().strip(),
            "tg_token": self.entry_tg_token.get().strip(),
            "tg_chat": self.entry_tg_chat.get().strip()
        }

        self.save_monitor_config(cfg)

        self.monitor_stop_event.clear()
        self.monitor_thread = threading.Thread(
            target=self.monitor_loop,
            args=(cfg,),
            daemon=True
        )
        self.monitor_thread.start()

        self.monitor_status_var.set("🟢 Đang chạy")
        self.lbl_monitor_status.config(foreground="green")
        self.set_monitor_status_icon("green")
        self.set_monitor_inputs_state(False)

        self.is_monitor_running = True

    def stop_monitor(self):
        if not self.is_monitor_running:
            return

        self.monitor_stop_event.set()

        self.monitor_status_var.set("🔴 Đã dừng")
        self.lbl_monitor_status.config(foreground="red")
        self.set_monitor_status_icon("red")
        self.set_monitor_inputs_state(True)

        self.is_monitor_running = False

    # ================= CONTROL =================
    def start_automation(self):
        # Update window keyword from input
        self.window_keyword = self.entry_window_name.get().strip() or "YB_OnlineClient"
        
        # Update tracking settings
        self.track_step_enabled = self.track_step_var.get()
        self.milestone_enabled = self.milestone_var.get()
        self.auto_reset_enabled = self.auto_reset_var.get()
        
        if not self.templates:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy template nào!")
            return
        if self.find_and_store_windows() == 0:
            messagebox.showwarning("Cảnh báo", f"Không tìm thấy cửa sổ '{self.window_keyword}'!")
            return

        # Reset counters
        self.step_counters.clear()
        self.step_last_time.clear()

        # Start Auto Tool
        self.use_script_runtime = self.script_mode_var.get()
        self.is_auto_running = True
        self.auto_thread = threading.Thread(
            target=self.automation_loop, daemon=True
        )
        self.auto_thread.start()

        # Start reset checker thread if auto reset is enabled
        if self.auto_reset_enabled:
            self.reset_checker_stop.clear()
            self.reset_checker_thread = threading.Thread(
                target=self.reset_checker_loop, daemon=True
            )
            self.reset_checker_thread.start()

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        # Auto start Monitor
        self.start_monitor()

    def stop_automation(self):
        # Stop Auto Tool
        self.is_auto_running = False

        # Stop reset checker
        if self.reset_checker_thread and self.reset_checker_thread.is_alive():
            self.reset_checker_stop.set()

        for hwnd in list(self.minimized_windows):
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            except:
                pass
        self.minimized_windows.clear()

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

        # Auto stop Monitor
        self.stop_monitor()

    def on_close(self):
        if self.is_auto_running:
            self.is_auto_running = False
        if self.is_monitor_running:
            self.monitor_stop_event.set()
        if self.reset_checker_thread and self.reset_checker_thread.is_alive():
            self.reset_checker_stop.set()
        self.root.destroy()


def main():
    root = tk.Tk()
    CombinedTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
