import cv2
from pyzbar.pyzbar import decode
import os
import customtkinter as ctk
from PIL import Image
import time
from datetime import datetime

class ModernQRScanner(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Modern Inventory Scanner")
        self.geometry("1250x700")
        self.configure(fg_color="#1a1a1a")

        # --- Data & Camera Setup ---
        self.cap = None
        self.current_data = None
        self.message_lock_until = 0
        self.available_cameras = self.detect_cameras()

        # --- Layout Grid ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- 1. Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#212121")
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(self.sidebar, text="SCANNER v2", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.pack(pady=20)

        # BOLD Format Label
        self.label_format = ctk.CTkLabel(
            self.sidebar,
            text="Define Format (comma separated):",
            text_color="#3498db",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.label_format.pack(pady=(10, 0), padx=10)

        self.format_entry = ctk.CTkEntry(self.sidebar, placeholder_text="e.g. ID, Name, Price")
        self.format_entry.insert(0, "Product, Price")
        self.format_entry.pack(pady=5, padx=20)

        self.camera_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=[f"Camera {i}" for i in self.available_cameras],
            command=self.change_camera
        )
        self.camera_menu.pack(pady=10, padx=20)

        self.btn_save = ctk.CTkButton(self.sidebar, text="SAVE (S)", command=self.save_data, font=ctk.CTkFont(weight="bold"))
        self.btn_save.pack(pady=15, padx=20)

        self.switch_var = ctk.StringVar(value="on")
        self.active_switch = ctk.CTkSwitch(self.sidebar, text="Camera Active", variable=self.switch_var,
                                           onvalue="on", offvalue="off", command=self.toggle_camera)
        self.active_switch.pack(pady=10)

        # --- CONTINUOUS MANUAL TEXT BOX ---
        self.manual_frame = ctk.CTkFrame(self.sidebar, fg_color="#2b2b2b", corner_radius=10)
        self.manual_frame.pack(pady=20, padx=15, fill="both", expand=True)

        manual_text = (
            "🚀 INSTRUCTIONS\n\n"
            "1. TYPE format in the\n"
            "blue BOLD box first.\n"
            "e.g: Apple, 150\n\n"
            "2. Match QR code to\n"
            "that format.\n\n"
            "3. Scan & press 'S'\n"
            "to save.\n\n"
            "⚠️ REMINDER:\n"
            "Set format BEFORE\n"
            "scanning!"
        )
        self.manual_label = ctk.CTkLabel(
            self.manual_frame,
            text=manual_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            justify="left",
            text_color="#bdc3c7"
        )
        self.manual_label.pack(pady=15, padx=10)

        # --- 2. Main Camera View ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#2b2b2b")
        self.main_frame.grid(row=0, column=1, padx=10, pady=20, sticky="nsew")

        self.video_label = ctk.CTkLabel(self.main_frame, text="Camera Loading...")
        self.video_label.pack(expand=True, fill="both", padx=10, pady=10)

        self.data_label = ctk.CTkLabel(self.main_frame, text="Ready to scan", font=ctk.CTkFont(size=14), text_color="gray")
        self.data_label.pack(pady=10)

        # --- 3. History Panel ---
        self.history_frame = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color="#212121")
        self.history_frame.grid(row=0, column=2, sticky="nsew")

        self.history_title = ctk.CTkLabel(self.history_frame, text="RECENT SCANS", font=ctk.CTkFont(size=14, weight="bold"))
        self.history_title.pack(pady=20)

        self.history_list = ctk.CTkScrollableFrame(self.history_frame, fg_color="transparent")
        self.history_list.pack(expand=True, fill="both", padx=5, pady=5)

        # --- Initialization ---
        self.change_camera(self.camera_menu.get())
        self.bind('<KeyPress-s>', lambda e: self.save_data())
        self.bind('<KeyPress-S>', lambda e: self.save_data())
        self.update_camera()

    def detect_cameras(self):
        index, arr = 0, []
        while index < 3:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.isOpened():
                arr.append(index)
                cap.release()
            index += 1
        return arr if arr else [0]

    def change_camera(self, choice):
        try:
            cam_index = int(choice.split(" ")[1])
            if self.cap: self.cap.release()
            self.cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
        except: pass

    def toggle_camera(self):
        if self.switch_var.get() == "on":
            self.change_camera(self.camera_menu.get())
        else:
            if self.cap: self.cap.release(); self.cap = None
            self.current_data = None

    def init_excel(self):
        filename = datetime.now().strftime("%Y%m%d") + ".csv"
        if not os.path.exists(filename):
            user_headers = self.format_entry.get().strip()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"{user_headers},Timestamp\n")

    def save_data(self):
        if self.current_data:
            try:
                headers = [h.strip() for h in self.format_entry.get().split(",")]
                qr_values = [v.strip() for v in self.current_data.split(",")]

                if len(qr_values) != len(headers):
                    self.show_status(f"❌ Match Error: Expected {len(headers)} items", "#e74c3c")
                    return

                filename = datetime.now().strftime("%Y%m%d") + ".csv"
                self.init_excel()

                timestamp = datetime.now().strftime("%H:%M:%S")
                with open(filename, 'a', encoding='utf-8') as f:
                    f.write(",".join(qr_values) + f",{timestamp}\n")

                # --- SHOW FIRST 2 COLUMNS + TIMESTAMP IN BOLD ---
                col1 = qr_values[0]
                col2 = qr_values[1] if len(qr_values) > 1 else ""

                # Format: • ID | Product [14:30:05]
                if col2:
                    display_text = f"• {col1} | {col2} [{timestamp}]"
                else:
                    display_text = f"• {col1} [{timestamp}]"

                history_item = ctk.CTkLabel(
                    self.history_list,
                    text=display_text,
                    anchor="w",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#ecf0f1"
                )
                history_item.pack(fill="x", pady=2, padx=5)

                self.show_status(f"✅ Saved: {col1}", "#2ecc71")
                self.current_data = None
            except Exception as e:
                self.show_status(f"❌ Error: {str(e)}", "#e74c3c")
        else:
            self.show_status("⚠️ No code detected!", "#f1c40f")

    def show_status(self, text, color, duration=2):
        self.data_label.configure(text=text, text_color=color)
        self.message_lock_until = time.time() + duration

    def update_camera(self):
        current_time = time.time()
        if self.switch_var.get() == "on" and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                found_qr = False
                for barcode in decode(frame):
                    found_qr = True
                    self.current_data = barcode.data.decode('utf-8')
                    if current_time > self.message_lock_until:
                        self.data_label.configure(text=f"Detected: {self.current_data}", text_color="white")
                    x, y, w, h = barcode.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (31, 106, 165), 3)
                if not found_qr:
                    self.current_data = None
                    if current_time > self.message_lock_until:
                        self.data_label.configure(text="Ready to scan", text_color="gray")
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                img_tk = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 480))
                self.video_label.configure(image=img_tk, text="")
                self.video_label._image_ref = img_tk
        else:
            self.video_label.configure(image="", text="Camera Paused")
        self.after(15, self.update_camera)

if __name__ == "__main__":
    app = ModernQRScanner()
    app.mainloop()