import subprocess
import threading
import tkinter as tk
from tkinter import ttk
import re
import pygetwindow as gw
import pyautogui
import time
import os
import requests
import zipfile
import io
from pynput import mouse
from tkinter import messagebox
from pystray import Icon, MenuItem as item
from PIL import Image, ImageDraw

BIN_DIR = os.path.join(os.getcwd(), 'bin')

device_name = None
device_info_full = None
click_global_x, click_global_y = None, None
click_relative_x, click_relative_y = None, None
scrcpy_window = None
scrcpy_process = None
listener = None
tray_icon = None

usb_info = "Unknown"
renderer_info = "Unknown"
audio_info_combined = "Unknown"
texture_info = "Unknown"

def download_and_extract_scrcpy(version):
    url_64bit = "https://github.com/Genymobile/scrcpy/releases/download/v2.7/scrcpy-win64-v2.7.zip"
    url_32bit = "https://github.com/Genymobile/scrcpy/releases/download/v2.7/scrcpy-win32-v2.7.zip"
    url = url_64bit if version == '64-bit' else url_32bit
    print(f"Downloading {version} version of Scrcpy...")
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(BIN_DIR)
    print(f"{version} version of Scrcpy downloaded and extracted.")

def find_scrcpy_executable():
    for root, dirs, files in os.walk(BIN_DIR):
        if 'scrcpy.exe' in files:
            return os.path.join(root, 'scrcpy.exe')
    return None

def ask_version_choice():
    version_window = tk.Toplevel()
    version_window.title("Scrcpy Version")
    label = ttk.Label(version_window, text="Which Scrcpy version would you like to install?")
    label.pack(pady=10)

    version_choice = tk.StringVar(value="")
    def select_64bit():
        version_choice.set("64-bit")
        version_window.destroy()
    def select_32bit():
        version_choice.set("32-bit")
        version_window.destroy()

    btn_64bit = ttk.Button(version_window, text="64-bit", command=select_64bit)
    btn_64bit.pack(side=tk.LEFT, padx=20, pady=10)
    btn_32bit = ttk.Button(version_window, text="32-bit", command=select_32bit)
    btn_32bit.pack(side=tk.RIGHT, padx=20, pady=10)

    version_window.wait_window()
    return version_choice.get()

def check_and_download_scrcpy():
    if not os.path.exists(BIN_DIR):
        os.makedirs(BIN_DIR)
    scrcpy_exe = find_scrcpy_executable()
    if not scrcpy_exe:
        version = ask_version_choice()
        if version:
            download_and_extract_scrcpy(version)
        else:
            messagebox.showwarning("Cancelled", "No version selected.")
            return
        scrcpy_exe = find_scrcpy_executable()
    if not scrcpy_exe:
        messagebox.showerror("Error", "scrcpy.exe not found! Please try again.")
    else:
        print(f"Scrcpy found at {scrcpy_exe}")
        return scrcpy_exe

def start_scrcpy():
    global scrcpy_process
    scrcpy_exe = check_and_download_scrcpy()
    if not scrcpy_exe:
        return
    scrcpy_cmd = [
        scrcpy_exe,
        "--max-size=1024",
        "--video-codec=h264",
        "--video-bit-rate=6M",
        "--audio-bit-rate=128K",
        "--max-fps=30",
        "--audio-encoder=aac"
    ]
    try:
        scrcpy_process = subprocess.Popen(
            scrcpy_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        threading.Thread(target=read_output, args=(scrcpy_process,)).start()
        threading.Thread(target=monitor_mouse_position).start()
    except FileNotFoundError as e:
        messagebox.showerror("Error", f"Scrcpy could not be started: {e}")

def stop_scrcpy():
    global scrcpy_process, listener
    if scrcpy_process:
        scrcpy_process.terminate()
        scrcpy_process = None
    if listener:
        listener.stop()
        listener = None

def read_output(process):
    global device_name, device_info_full, audio_info_combined
    audio_info_combined = ""

    for line in process.stdout:
        usb_match = re.search(r'INFO:\s+-->\s+\(usb\)\s+(\w+)', line)
        if usb_match:
            usb_info = usb_match.group(1)
            update_usb_info(usb_info)
            update_tray_tooltip()

        renderer_match = re.search(r'INFO:\s+Renderer:\s+(\w+)', line)
        if renderer_match:
            renderer_info = renderer_match.group(1)
            update_renderer_info(renderer_info)
            update_tray_tooltip()

        if "Audio disabled" in line:
            audio_info_combined = "Audio disabled, not supported before Android 11."
        elif "Demuxer 'audio': stream explicitly disabled by the device" in line:
            audio_info_combined += " WARN: stream explicitly disabled by the device."

        update_audio_info(audio_info_combined)
        update_tray_tooltip()

        texture_match = re.search(r'Texture: (\d+)x(\d+)', line)
        if texture_match:
            width = texture_match.group(1)
            height = texture_match.group(2)
            update_texture_info(f"{width}x{height}")
            update_tray_tooltip()

        full_device_match = re.search(r'Device:.*', line)
        if full_device_match:
            device_info_full = full_device_match.group(0).strip()
            update_device_info(device_info_full)

        window_match = re.search(r'Device:.*?\[.*?\]\s.*?\s(\w+)\s?\(', line)
        if window_match:
            device_name = window_match.group(1).strip()
            update_program_window_info(device_name)

def monitor_mouse_position():
    global device_name, click_global_x, click_global_y, click_relative_x, click_relative_y, scrcpy_window, listener
    scrcpy_window = None
    while scrcpy_window is None:
        if device_name:
            windows = gw.getWindowsWithTitle(device_name)
            for window in windows:
                if device_name in window.title and window.visible:
                    scrcpy_window = window
                    break
        time.sleep(1)

    listener = mouse.Listener(on_click=on_click)
    listener.start()

    while scrcpy_window:
        try:
            window_x, window_y = scrcpy_window.left, scrcpy_window.top
            window_width, window_height = scrcpy_window.width, scrcpy_window.height
            mouse_x, mouse_y = pyautogui.position()
            if window_x <= mouse_x <= window_x + window_width and window_y <= mouse_y <= window_y + window_height:
                relative_x = mouse_x - window_x
                relative_y = mouse_y - window_y
                update_mouse_position(relative_x, relative_y, window_width, window_height)
            time.sleep(0.1)
        except gw.PyGetWindowException:
            break

def on_click(x, y, button, pressed):
    global click_global_x, click_global_y, click_relative_x, click_relative_y, scrcpy_window
    if pressed and scrcpy_window:
        try:
            click_global_x, click_global_y = x, y
            window_x, window_y = scrcpy_window.left, scrcpy_window.top
            click_relative_x = click_global_x - window_x
            click_relative_y = click_global_y - window_y
            update_click_position(click_global_x, click_global_y, click_relative_x, click_relative_y)
        except gw.PyGetWindowException:
            pass

def update_usb_info(info):
    global usb_info
    usb_info = info
    usb_label.config(text=f"USB: {usb_info}")
    update_tray_tooltip()

def update_renderer_info(info):
    global renderer_info
    renderer_info = info
    renderer_label.config(text=f"Renderer: {renderer_info}")
    update_tray_tooltip()

def update_audio_info(info):
    global audio_info_combined
    audio_info_combined = info
    audio_label.config(text=f"Audio: {audio_info_combined}")
    update_tray_tooltip()

def update_texture_info(info):
    global texture_info
    texture_info = info
    texture_label.config(text=f"Texture Size: {texture_info}")
    update_tray_tooltip()

def update_device_info(device_info):
    window_label.config(text=f"Device Info: {device_info}")

def update_program_window_info(window_name):
    program_window_label.config(text=f"Program Window: {window_name}")

def update_mouse_position(x, y, width, height):
    mouse_position_label.config(text=f"Mouse Position: {x}x{y} (Window Size: {width}x{height})")

def update_click_position(global_x, global_y, relative_x, relative_y):
    click_global_label.config(text=f"Click Position Global: {global_x}x{global_y}")
    click_relative_label.config(text=f"Click Position Relative: {relative_x}x{relative_y}")

def quit_application():
    stop_scrcpy()
    tray_icon.stop()
    root.quit()

def on_closing():
    root.withdraw()

def create_tray_icon():
    global tray_icon
    image = Image.new('RGB', (64, 64), (255, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 64, 64), fill="blue")
    tray_icon = Icon("scrcpy_bot", image, menu=(
        item('Start Scrcpy', lambda icon, item: start_scrcpy()),
        item('Stop Scrcpy', lambda icon, item: stop_scrcpy()),
        item('Show GUI', show_gui_from_tray),
        item('Quit', lambda icon, item: quit_application())
    ))
    threading.Thread(target=tray_icon.run).start()

def show_gui_from_tray(icon, item):
    root.deiconify()
    root.lift()

def update_tray_tooltip():
    if tray_icon:
        tooltip_text = f"USB: {usb_info}\nRenderer: {renderer_info}\nAudio: {audio_info_combined}\nTexture: {texture_info}"
        tray_icon.title = tooltip_text

root = tk.Tk()
root.title("Scrcpy Tray-Tool")

texture_label = ttk.Label(root, text="Texture Size: ", font=("Arial", 12))
texture_label.pack(pady=10)
window_label = ttk.Label(root, text="Device Info: ", font=("Arial", 12))
window_label.pack(pady=10)
program_window_label = ttk.Label(root, text="Program Window: ", font=("Arial", 12))
program_window_label.pack(pady=10)
usb_label = ttk.Label(root, text="USB: ", font=("Arial", 12))
usb_label.pack(pady=10)
renderer_label = ttk.Label(root, text="Renderer: ", font=("Arial", 12))
renderer_label.pack(pady=10)
audio_label = ttk.Label(root, text="Audio: ", font=("Arial", 12))
audio_label.pack(pady=10)
mouse_position_label = ttk.Label(root, text="Mouse Position: ", font=("Arial", 12))
mouse_position_label.pack(pady=10)
click_global_label = ttk.Label(root, text="Click Position Global: ", font=("Arial", 12))
click_global_label.pack(pady=10)
click_relative_label = ttk.Label(root, text="Click Position Relative: ", font=("Arial", 12))
click_relative_label.pack(pady=10)

root.withdraw()

start_button = ttk.Button(root, text="Start Scrcpy", command=start_scrcpy)
start_button.pack(pady=20)
stop_button = ttk.Button(root, text="Stop Scrcpy", command=stop_scrcpy)
stop_button.pack(pady=20)

root.protocol("WM_DELETE_WINDOW", on_closing)

create_tray_icon()

root.mainloop()
