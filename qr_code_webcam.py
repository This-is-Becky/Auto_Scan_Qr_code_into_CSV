# -*- coding: utf-8 -*-
"""
Created on Mon Nov  3 17:08:38 2025

@author: beckylin
"""

import cv2
from pyzbar.pyzbar import decode
import openpyxl
from datetime import datetime
import time

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

# if not available_cameras:
#     print("No cameras detected. Exiting.")
#     exit()

# Step 2: Choose camera
# print("\nAvailable cameras:", available_cameras)
# cam_index = int(input(f"Select camera index from {available_cameras}: "))

# Step 3: Prepare Excel file
excel_file = "test.xlsx"
try:
    wb = openpyxl.load_workbook(excel_file)
    sheet = wb.active
except FileNotFoundError:
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.append(["Product", "Timestamp"])

# Step 4: Open webcam
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("Error: Could not open selected webcam.")
    exit()

print("Scanning QR codes... Press 'q' to quit.")

# Track scanned codes to avoid duplicates
scanned_codes = set()
pre_time =time.time()

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

        product = barcode.data.decode('utf-8')

        # Display product text above the box
        cv2.putText(frame, product, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # Scan only if not scanned before
        if product not in scanned_codes:
            scanned_codes.add(product)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append([product, timestamp])
            wb.save(excel_file)
            print(f"✅ Recorded: {product} at {timestamp}")

        else:
            current_time= time.time()
            if current_time - pre_time >= 5:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.append([product, timestamp])
                wb.save(excel_file)
                print(f"✅ Recorded: {product} at {timestamp}")
                pre_time = current_time

                

    # Show video feed
    cv2.imshow('QR Scanner', frame)

    # Quit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()