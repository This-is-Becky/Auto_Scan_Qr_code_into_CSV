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
        self.geometry("1200x650")  # Widened to fit the history panel
        self.configure(fg_color="#1a1a1a")

        # --- Data & Camera Setup ---
        self.cap = None
        self.current_data = None
        self.message_lock_until = 0
        self.available_cameras = self.detect_cameras()

        # --- Layout Grid ---
        # Col 0: Sidebar | Col 1: Camera (Weight 1) | Col 2: History
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- 1. Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#212121")
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(self.sidebar, text="SCANNER v2", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=30)
        self.label_format = ctk.CTkLabel(self.sidebar, text="Define Format (comma separated):",
                                         text_color="gray", font=("Arial", 10))
        self.label_format.pack(pady=(10, 0))
        self.format_entry = ctk.CTkEntry(self.sidebar, placeholder_text="e.g. ID, Name, Price")
        self.format_entry.insert(0, "Product, Price")
        self.format_entry.pack(pady=5, padx=20)

        # Camera Menu
        self.camera_menu = ctk.CTkOptionMenu(self.sidebar, values=[f"Camera {i}" for i in self.available_cameras])
        self.camera_menu.pack(pady=10, padx=20)

        self.btn_save = ctk.CTkButton(self.sidebar, text="SAVE (S)", command=self.save_data)
        self.btn_save.pack(pady=20, padx=20)

        self.switch_var = ctk.StringVar(value="on")
        self.active_switch = ctk.CTkSwitch(self.sidebar, text="Camera Active", variable=self.switch_var,
                                           onvalue="on", offvalue="off", command=self.toggle_camera)
        self.active_switch.pack(pady=20)

        # --- 2. Main Camera View ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#2b2b2b")
        self.main_frame.grid(row=0, column=1, padx=10, pady=20, sticky="nsew")

        self.video_label = ctk.CTkLabel(self.main_frame, text="Camera Loading...")
        self.video_label.pack(expand=True, fill="both", padx=10, pady=10)

        self.data_label = ctk.CTkLabel(self.main_frame, text="Ready to scan", font=("Arial", 14), text_color="gray")
        self.data_label.pack(pady=10)

        # --- 3. History Panel (The New Part) ---
        self.history_frame = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#212121")
        self.history_frame.grid(row=0, column=2, sticky="nsew")

        self.history_title = ctk.CTkLabel(self.history_frame, text="RECENT SCANS", font=ctk.CTkFont(weight="bold"))
        self.history_title.pack(pady=20)

        self.history_list = ctk.CTkScrollableFrame(self.history_frame, fg_color="transparent")
        self.history_list.pack(expand=True, fill="both", padx=5, pady=5)

        # --- Initialization ---
        self.init_excel()  # Setup CSV
        self.change_camera(self.camera_menu.get())

        self.bind('<KeyPress-s>', lambda e: self.save_data())
        self.bind('<KeyPress-S>', lambda e: self.save_data())
        self.update_camera()

    # --- HELPER METHODS ---

    def detect_cameras(self):
        index = 0
        arr = []
        while index < 3:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.read()[0]:
                arr.append(index)
                cap.release()
            index += 1
        return arr if arr else [0]

    def change_camera(self, choice):
        try:
            cam_index = int(choice.split(" ")[1])
            if self.cap: self.cap.release()
            self.cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
        except:
            pass

    def toggle_camera(self):
        if self.switch_var.get() == "on":
            self.change_camera(self.camera_menu.get())
        else:
            if self.cap:
                self.cap.release()
                self.cap = None
            self.current_data = None

    def init_excel(self):
        filename = datetime.now().strftime("%Y%m%d") + ".csv"
        if not os.path.exists(filename):
            # Grab headers from the UI entry
            user_headers = self.format_entry.get()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"{user_headers},Timestamp\n")

    def save_data(self):
        if self.current_data:
            try:
                # 1. Get the current format defined by the user
                headers = [h.strip() for h in self.format_entry.get().split(",")]
                num_expected = len(headers)

                # 2. Split the QR data
                qr_values = [v.strip() for v in self.current_data.split(",")]

                if len(qr_values) != num_expected:
                    self.show_status(f"❌ Match Error: Expected {num_expected} items", "#e74c3c")
                    return

                # 3. Prepare row data
                timestamp = datetime.now().strftime("%H:%M:%S")
                filename = datetime.now().strftime("%Y%m%d") + ".csv"

                # Ensure file exists (in case user changed format mid-day)
                if not os.path.exists(filename): self.init_excel()

                # 4. Save to CSV
                row_string = ",".join(qr_values)
                with open(filename, 'a', encoding='utf-8') as f:
                    f.write(f"{row_string},{timestamp}\n")

                # Update UI History (Show the first item from the QR as the name)
                display_name = qr_values[0]
                history_item = ctk.CTkLabel(self.history_list, text=f"• {display_name} - {timestamp}",
                                            anchor="w", font=("Arial", 11))
                history_item.pack(fill="x", pady=2)

                self.show_status(f"✅ Saved: {display_name}", "#2ecc71")
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
            self.current_data = None
            self.video_label.configure(image="", text="Camera Paused")

        self.after(15, self.update_camera)


if __name__ == "__main__":
    app = ModernQRScanner()
    app.mainloop()
