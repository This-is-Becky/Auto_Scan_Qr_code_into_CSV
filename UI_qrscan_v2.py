import cv2
from pyzbar.pyzbar import decode
import openpyxl
from datetime import datetime
import os
import customtkinter as ctk
from PIL import Image
import time
# Force Dark Mode
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class ModernQRScanner(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Modern Inventory Scanner")
        self.geometry("1000x650")
        self.configure(fg_color="#1a1a1a")  # True dark background

        # --- Excel Setup ---
        self.excel_file = "qrcode.xlsx"
        self.init_excel()

        # --- Camera Setup ---
        self.cap = None
        self.available_cameras = self.detect_cameras()
        self.current_data = None

        # --- Layout Grid ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#212121")
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(self.sidebar, text="SCANNER v2", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=30, padx=20)

        # Camera Selection Dropdown (Replacing Categories)
        self.label_mode = ctk.CTkLabel(self.sidebar, text="Select Device:", text_color="gray")
        self.label_mode.pack(pady=(10, 0))

        self.camera_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=[f"Camera {i}" for i in self.available_cameras],
            command=self.change_camera
        )
        self.camera_menu.pack(pady=10, padx=20)

        # Save Button
        self.btn_save = ctk.CTkButton(self.sidebar, text="SAVE (S)", command=self.save_data,
                                      fg_color="#1f6aa5", hover_color="#144870")
        self.btn_save.pack(pady=20, padx=20)

        # Status Switch
        self.switch_var = ctk.StringVar(value="on")
        self.active_switch = ctk.CTkSwitch(self.sidebar, text="Camera Active", variable=self.switch_var, onvalue="on",
                                           offvalue="off", command=self.toggle_camera)
        self.active_switch.pack(pady=20)

        # --- Main View ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#2b2b2b")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.video_label = ctk.CTkLabel(self.main_frame, text="Camera Loading...")
        self.video_label.pack(expand=True, fill="both", padx=10, pady=10)

        self.data_label = ctk.CTkLabel(self.main_frame, text="Ready to scan", font=ctk.CTkFont(size=14),
                                       text_color="gray")
        self.data_label.pack(pady=10)

        # --- Initialization ---
        self.change_camera(self.camera_menu.get())
        # Message showing time set
        self.message_lock_until = 0

        # Keyboard Binding
        self.bind('<KeyPress-s>', lambda e: self.save_data())
        self.bind('<KeyPress-S>', lambda e: self.save_data())
        self.focus_set()  # Ensure the window captures key presses

        self.update_camera()

    def detect_cameras(self):
        """Checks for available camera indices."""
        index = 0
        arr = []
        while index < 4:  # Checking first 4 slots
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.read()[0]:
                arr.append(index)
                cap.release()
            index += 1
        return arr if arr else [0]

    def change_camera(self, choice):
        """Switches the video capture source."""
        # Extract the number from "Camera 0"
        try:
            cam_index = int(choice.split(" ")[1])
            if self.cap:
                self.cap.release()

            # Re-initialize the capture object
            self.cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)

            # Optional: Set resolution for stability
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        except Exception as e:
            print(f"Error switching camera: {e}")

    def toggle_camera(self):
        """Handles the hardware state when the switch is flipped."""
        if self.switch_var.get() == "on":
            # Start the camera if it's not already running
            if self.cap is None or not self.cap.isOpened():
                self.change_camera(self.camera_menu.get())
        else:
            # Release hardware so other apps can use it and save power
            if self.cap:
                self.cap.release()
                self.cap = None
            # Wipe data so you can't save while paused
            self.current_data = None

    def get_daily_filename(self):
        """Generates a filename based on the current date: YYYYMMDD.csv"""
        date_str = datetime.now().strftime("%Y%m%d")
        return f"{date_str}.csv"

    def init_excel(self):
        """Ensures the CSV for the current day exists with headers."""
        filename = self.get_daily_filename()
        if not os.path.exists(filename):
            with open(filename, mode='w', encoding='utf-8') as f:
                # Writing the header row
                f.write("Product,Price,Timestamp\n")

    def save_data(self):
        if self.current_data:
            try:
                # 1. Get the specific file for today
                filename = self.get_daily_filename()

                # 2. Ensure the file and headers exist
                if not os.path.exists(filename):
                    self.init_csv()

                # 3. Basic parsing logic (Name,Price)
                product, price = self.current_data.split(",")
                timestamp = datetime.now().strftime("%H:%M:%S")  # Time only, date is in filename

                # 4. Append to the CSV
                with open(filename, mode='a', encoding='utf-8') as f:
                    f.write(f"{product},{price},{timestamp}\n")

                self.data_label.configure(text=f"✅ Saved to {filename}: {product}", text_color="#2ecc71")
                print(f"Recorded in {filename}: {product}")

                # Optional: Clear current_data so you don't save the same scan twice by accident
                self.current_data = None
                # keep the message for 3 seconds
                self.show_status(f"✅ Saved: {product}", "#2ecc71", duration=3)
                self.current_data = None  # Clear data after saving

            except ValueError:
                self.data_label.configure(text="❌ Error: Format must be 'Name,Price'", text_color="#e74c3c")
            except Exception as e:
                self.show_status(f"❌ Error: {e}", "#e74c3c", duration=4)
        else:
            self.show_status("⚠️ No code detected to save!", "#f1c40f", duration=2)

    def show_status(self, text, color="white", duration=3):
        """Displays a message and locks it for 'duration' seconds."""
        self.data_label.configure(text=text, text_color=color)
        self.message_lock_until = time.time() + duration

    def update_camera(self):
        current_time = time.time()

        # Only attempt to read if switch is ON and hardware is ready
        if self.switch_var.get() == "on" and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                found_qr = False
                for barcode in decode(frame):
                    found_qr = True
                    self.current_data = barcode.data.decode('utf-8')

                    # Update label only if not showing a "Saved" message
                    if current_time > self.message_lock_until:
                        self.data_label.configure(text=f"Detected: {self.current_data}", text_color="white")

                    # Draw overlay
                    x, y, w, h = barcode.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (31, 106, 165), 3)

                # --- CRITICAL FIX: IF NO QR IS FOUND, WIPE MEMORY ---
                if not found_qr:
                    self.current_data = None
                    if current_time > self.message_lock_until:
                        self.data_label.configure(text="Ready to scan", text_color="gray")

                # Render frame to UI
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                img_tk = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 480))
                self.video_label.configure(image=img_tk, text="")
                self.video_label._image_ref = img_tk  # Prevents the 'image doesn't exist' error
        else:
            # If camera is OFF or Paused
            self.current_data = None
            self.video_label.configure(image="", text="Camera Paused")
            if current_time > self.message_lock_until:
                self.data_label.configure(text="Camera Paused", text_color="gray")

        # Repeat the loop
        self.after(15, self.update_camera)

if __name__ == "__main__":
    app = ModernQRScanner()
    app.mainloop()