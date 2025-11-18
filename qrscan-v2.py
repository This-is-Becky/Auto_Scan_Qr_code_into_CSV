
import cv2
from pyzbar.pyzbar import decode
import openpyxl
from datetime import datetime
import time
import os

# Step 1: Detect available cameras
# print("Checking available cameras...")
# available_cameras = []
# for i in range(5):
#     cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
#     if cap.isOpened():
#         print(f"✅ Camera found at index {i}")
#         available_cameras.append(i)
#         cap.release()
#     else:
#         print(f"❌ No camera at index {i}")
#
# if not available_cameras:
#     print("No cameras detected. Exiting.")
#     exit()

# Step 3: Prepare Excel file
excel_file = "qrcode.xlsx"
try:
    wb = openpyxl.load_workbook(excel_file)
    sheet = wb.active
except FileNotFoundError:
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.append(["Product", "Price", "Timestamp"])

#Save the file
wb.save(excel_file)
print("Excel file will be saved at:", os.path.abspath(excel_file))

# Step 4: Open webcam
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("Error: Could not open selected webcam.")
    exit()

print("Scanning QR codes... Press 'q' to quit.")

# Track scanned codes to avoid duplicates
# scanned_codes = set()
# pre_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break

    # Decode QR codes
    for barcode in decode(frame):
        x, y, w, h = barcode.rect
        # Draw bounding box
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        data = barcode.data.decode('utf-8')
        # print(product)
        product = data.split(",")[0]
        price=data.split(",")[1]
        # print(price)

        # Display product text above the box
        cv2.putText(frame, data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255,0), 2)

        # Save on 'Enter' (ASCII 13)
        if cv2.waitKey(1) & 0xFF == ord('s'):  # 13 is the ASCII value for Carriage Return/Enter

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append([product, price, timestamp])
            wb.save(excel_file)
            time.sleep(0.2)
            cv2.putText(frame, "saved", (x-20, y + h + 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 10)
            print(f"✅ Recorded: {data} at {timestamp}")


    # Show video feed
    cv2.imshow('QR Scanner', frame)

    # Quit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- Cleanup ---
cap.release()
cv2.destroyAllWindows()
print("Scanner closed.")