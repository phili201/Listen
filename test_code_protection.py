import os
import shutil
import sys
import datetime
import time
import tkinter as tk
from tkinter import simpledialog


def ask_for_pin_gui():
    root = tk.Tk()
    root.withdraw()
    pin = simpledialog.askstring("PIN Required", "Enter PIN to abort self-destruction:")
    if pin == "2012":
        print("Self-destruction aborted.")
        return True
    else:
        print("Incorrect Pin. Self-destruction will proceed.")
        return False

ask_for_pin_gui()