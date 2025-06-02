import customtkinter as ctk
import tkinter as tk
import os
import signal
import subprocess
import json
import shutil
from tkinter.filedialog import askdirectory
from tkinter import messagebox

# Ctk settings
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")
app = ctk.CTk()
app.geometry("750x650")
app.title("Mpvpaper-client")

# ----------------------------------------

# Allerts
print("\nTo use the app you need to have mpvpaper installed (https://github.com/GhostNaN/mpvpaper).")
print("Please DO NOT force close the app with ctrl+c this may require a restart of the session.\n")

# Global variables
wallpaper_frame = None
mp4_files = []
config_file = "mpvpaper_config.json"
current_directory = None
checkbox_vars = {}

# Load and save JSON
def load_config():
    global current_directory
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                current_directory = config.get('wallpaper_directory', None)
                print(f"Loaded directory: {current_directory}")
        else:
            current_directory = None
    except Exception as e:
        print(f"Error loading configuration: {e}")
        current_directory = None

def save_config():
    try:
        config = {
            'wallpaper_directory': current_directory
        }
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Configuration saved: {current_directory}")
    except Exception as e:
        print(f"Error saving configuration: {e}")

# ----------------------------------------

# On/Off
switch_var = ctk.StringVar(value="on")

def on_off():
    state = switch_var.get()
    if state == "off":
        result = subprocess.run(['pgrep', 'mpvpaper'], capture_output=True, text=True)
        pids = result.stdout.strip().split('\n')
        for pid in pids:
            if pid.strip().isdigit():
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"Terminated process with PID: {pid}")
                except ProcessLookupError:
                    print(f"Process with PID {pid} not found.")
                except Exception as e:
                    print(f"Error terminating process with PID {pid}: {e}")
    else:
        apply_folder = os.path.join(current_directory, "Apply") if current_directory else None
        wallpaper_dir = apply_folder if apply_folder and os.path.exists(apply_folder) else current_directory

        if wallpaper_dir and os.path.exists(wallpaper_dir):
            try:
                subprocess.Popen([
                    "mpvpaper",
                    "-o", "no-audio --loop-playlist",
                    "*",
                    wallpaper_dir
                ])
                print(f"mpvpaper started successfully with directory: {wallpaper_dir}")
            except Exception as e:
                print(f"Error starting mpvpaper: {e}")
        else:
            messagebox.showwarning("Warning", "Please select a directory for wallpapers first!")
            switch_var.set("off")

# Close and hide
def hide_window():
    app.withdraw()

def close_app():
    app.destroy()

# Set Directory
def set_directory():
    global current_directory
    path = askdirectory(title="Select Wallpaper Directory")
    if path:
        current_directory = path
        save_config()

        directory_name = os.path.basename(path) if path else "Not selected"
        set_directory_button.configure(text=f"🗂️ {directory_name}")
        print(f"Directory set: {path}")

# Fetch wallpapers
def fetch_wallpaper():
    global mp4_files, checkbox_vars

    if not current_directory:
        messagebox.showwarning("Warning", "Please select a directory first with 'Set Directory'!")
        return

    if not os.path.exists(current_directory):
        messagebox.showerror("Error", f"The directory {current_directory} no longer exists!")
        return

    try:
        files = os.listdir(current_directory)
        mp4_files = [f for f in files if f.lower().endswith('.mp4')]
        print(f"Found {len(mp4_files)} MP4 files in {current_directory}")

        checkbox_vars.clear()

        frame_wallpaper()
    except Exception as e:
        messagebox.showerror("Error", f"Error reading directory: {e}")

def frame_wallpaper():
    global wallpaper_frame

    if wallpaper_frame is None:
        wallpaper_frame = ctk.CTkScrollableFrame(
            master=app,
            width=550,
            height=250,
            corner_radius=15
        )
        wallpaper_frame.pack(pady=(20, 20), padx=30, fill="both", expand=True)

    for widget in wallpaper_frame.winfo_children():
        widget.destroy()

    if not mp4_files:
        no_files_label = ctk.CTkLabel(
            master=wallpaper_frame,
            text="No MP4 files found in the selected directory",
            font=ctk.CTkFont(size=14)
        )
        no_files_label.pack(pady=20)
        return

    for filename in mp4_files:
        file_frame = ctk.CTkFrame(
            master=wallpaper_frame,
            width=500,
            height=50,
            corner_radius=12
        )
        file_frame.pack(pady=8, padx=15, fill="x")
        file_frame.pack_propagate(False)


        checkbox_vars[filename] = ctk.BooleanVar()


        checkbox = ctk.CTkCheckBox(
            master=file_frame,
            text="",
            variable=checkbox_vars[filename],
            width=20,
            command=apply_wallpapers
        )
        checkbox.pack(side="left", padx=(15, 10), pady=10)


        file_label = ctk.CTkLabel(
            master=file_frame,
            text=f"🎬 {filename}",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        file_label.pack(side="left", padx=(0, 15), pady=10, fill="x", expand=True)

def apply_wallpapers():

    # Create Apply
    apply_folder = os.path.join(current_directory, "Apply")
    if not os.path.exists(apply_folder):
        try:
            os.makedirs(apply_folder)
            print(f"Created Apply folder: {apply_folder}")
        except Exception as e:
            print("Error creating Apply folder:", e)
            return

    # Move Apply
    for filename, var in checkbox_vars.items():
        if var.get():
            source_path = os.path.join(current_directory, filename)
            dest_path = os.path.join(apply_folder, filename)

            if os.path.exists(source_path) and not os.path.exists(dest_path):
                try:
                    shutil.move(source_path, dest_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Could not move {filename}: {e}")


    fetch_wallpaper()


# UI
load_config()

# Skibidi Text
title_label_1 = ctk.CTkLabel(
    master=app,
    text="Mpvpaper-client",
    font=ctk.CTkFont(size=30, weight="bold")
)
title_label_1.pack(pady=(30, 5))

# Description
subtitle_label_1 = ctk.CTkLabel(
    master=app,
    text="By Helixo22",
    font=ctk.CTkFont(size=15)
)
subtitle_label_1.pack(pady=(0, 25))

# Switch
switch_1 = ctk.CTkSwitch(
    master=app,
    text="🌿 On/Off Wallpaper",
    command=on_off,
    variable=switch_var,
    onvalue="on",
    offvalue="off"
)
switch_1.pack(pady=(0, 15))

# Directory button
directory_text = "🗂️Set Directory"
if current_directory:
    directory_name = os.path.basename(current_directory)
    directory_text = f"🗂️ {directory_name}"

set_directory_button = ctk.CTkButton(
    master=app,
    text=directory_text,
    command=set_directory,
    width=220,
    height=45,
    corner_radius=15,
    font=ctk.CTkFont(size=16, weight="bold"),
    fg_color=["#2d7a2d", "#4caf50"],
    hover_color=["#4caf50", "#66bb6a"]
)
set_directory_button.pack(pady=(0, 15))

# Fetch wallpapers
fetch_wallpaper_button = ctk.CTkButton(
    master=app,
    text="📂Fetch Wallpapers",
    command=fetch_wallpaper,
    width=220,
    height=45,
    corner_radius=15,
    font=ctk.CTkFont(size=16, weight="bold"),
    fg_color=["#2d7a2d", "#4caf50"],
    hover_color=["#4caf50", "#66bb6a"]
)
fetch_wallpaper_button.pack(pady=(15, 10))

# Hide button
hide_button = ctk.CTkButton(
    master=app,
    text="🫣",
    width=35,
    height=35,
    fg_color="#2d7a2d",
    hover_color="#4caf50",
    command=hide_window,
    corner_radius=15,
    font=ctk.CTkFont(size=20)
)

# Close button
close_button = ctk.CTkButton(
    master=app,
    text="❌",
    width=35,
    height=35,
    fg_color="#a83232",
    hover_color="#e74c3c",
    command=close_app,
    corner_radius=15,
    font=ctk.CTkFont(size=20, weight="bold")
)

close_button.place(relx=1.0, y=10, anchor="ne")
hide_button.place(relx=0.95, y=10, anchor="ne")

app.mainloop()
