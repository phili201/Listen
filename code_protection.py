import os
import sys
import hashlib
import shutil
import datetime
import threading
import time
import tkinter as tk
from tkinter import simpledialog
from unittest import result

pin_verified = False

MARKER = "\u200B\u200C\u200D\u200B\u200B\u200D\u200C\u200B\u200D\u200B\u200C\u200D\u200C\u200B\u200D\u200C\u200B\u200C\u200D\u200D\u200B\u200C\u200D"
USB_KEY_PATH = "/media/philipp/UNTITLED/code.key"
project_folder = "/home/philipp/Downloads/Listen APP"

PI_USER = "philipp"
PI_IP = "192.168.178.81"
PI_FOLDER = "/home/philipp/backups"

def verify_usb():
    return os.path.exists(USB_KEY_PATH)

def verify_Marker(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return MARKER in content
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False
    
def send_backup_to_pi(project_folder):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"backup_{timestamp}.zip"
    password = "Hase2012"
    result_zip = os.system(f"zip -P {password} -r {zip_name} {project_folder}")
    if result_zip != 0:
        print("Error creating password-protected zip archive.")
        return
    result_scp = os.system(f"scp {zip_name} {PI_USER}@{PI_IP}:{PI_FOLDER}/{zip_name}")
    if result_scp == 0:
        print("Backup successfully sent to Raspberry Pi.")
        os.remove(zip_name)
    else:
        print("Error sending backup to Raspberry Pi.")

def self_destruct(project_folder):
    print("Starting self-destruction sequence...")
    for i in range(5, 0, -1):
        print(f"Self-destruction in {i} seconds...")
        time.sleep(1)
    shutil.rmtree(project_folder)
    sys.exit(1)

def stick_removed():
    return not os.path.exists(USB_KEY_PATH)

def ask_for_pin_gui():
    def get_pin():
        global pin_verified
        pin = simpledialog.askstring("PIN Required", "Enter PIN to abort self-destruction:")
        if pin == "2012":
            pin_verified = True
            print("Self-destruction aborted.")
        if verify_usb():
            pin_verified = True
            print("Self-destruction aborted.")
        else:
            print("Incorrect Pin. Self-destruction will proceed.")
    root = tk.Tk()
    root.withdraw()
    threading.Thread(target=get_pin).start()

def pin_timer_gui(project_folder):
    global pin_verified
    pin_verified = False
    ask_for_pin_gui()
    print("You have 20 seconds to enter the correct PIN...")
    start = time.time()
    while time.time() - start < 20:
        if pin_verified:
            print("Self-destruction aborted.")
            return
        time.sleep(1)
    print("Time expired. Initiating self-destruction.")
    send_backup_to_pi(project_folder)
    self_destruct(project_folder)


def code_check(file_path="main.py", project_folder="/home/philipp/Downloads/Listen APP"):
    if stick_removed():
        print("X USB key removed during execution. Initiating self-destruction.")
        pin_timer_gui(project_folder)
    if not verify_usb():
        print("X USB key not found. Initiating self-destruction.")
        send_backup_to_pi(project_folder)
        self_destruct(project_folder)
    if not verify_Marker(file_path):
        print("X Marker not found in code. Initiating self-destruction.")
        send_backup_to_pi(project_folder)
        self_destruct(project_folder)
    print("✔ Code protection check passed.")