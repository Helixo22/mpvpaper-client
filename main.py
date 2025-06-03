import customtkinter as ctk
import tkinter as tk
import os
import signal
import subprocess
import json
import shutil
from tkinter.filedialog import askdirectory
from tkinter import messagebox

# Ctk
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")
app = ctk.CTk()
app.geometry("900x750")
app.title("Mpvpaper Client")
app.resizable(False, False)

# Color
PRIMARY_COLOR = ["#1e5631", "#2d7a2d"]
PRIMARY_HOVER = ["#2d7a2d", "#4caf50"]
ACCENT_COLOR = ["#0d7377", "#14a085"]
ACCENT_HOVER = ["#14a085", "#17c3b2"]
DANGER_COLOR = ["#a83232", "#e74c3c"]
NAVBAR_COLOR = ["#1a1a1a", "#0d1117"]

# Allerts
print("\nTo use the app you need to have mpvpaper installed (https://github.com/GhostNaN/mpvpaper).")
print("Please DO NOT force close the app with ctrl+c this may require a restart of the session.\n")

# Global variables
wallpaper_frame = None
mp4_files = []
config_file = "mpvpaper_config.json"
current_directory = None
checkbox_vars = {}
main_content_frame = None

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
        set_directory_button.configure(text=f"📁 {directory_name}")
        status_label.configure(text=f"Current Directory: {directory_name}")
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
        file_count_label.configure(text=f"Files Found: {len(mp4_files)} MP4s")
    except Exception as e:
        messagebox.showerror("Error", f"Error reading directory: {e}")

def frame_wallpaper():
    global wallpaper_frame

    if wallpaper_frame is None:
        wallpaper_frame = ctk.CTkScrollableFrame(
            master=main_content_frame,
            width=580,
            height=350,
            corner_radius=15,
            fg_color=["#f0f0f0", "#1e1e1e"]
        )
        wallpaper_frame.pack(pady=(20, 20), padx=20, fill="both", expand=True)

    for widget in wallpaper_frame.winfo_children():
        widget.destroy()

    if not mp4_files:
        no_files_label = ctk.CTkLabel(
            master=wallpaper_frame,
            text="No MP4 files found in the selected directory",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=["#666666", "#888888"]
        )
        no_files_label.pack(pady=50)
        return

    for i, filename in enumerate(mp4_files):
        file_frame = ctk.CTkFrame(
            master=wallpaper_frame,
            width=550,
            height=60,
            corner_radius=12,
            fg_color=["#ffffff", "#2a2a2a"],
            border_width=1,
            border_color=["#e0e0e0", "#3a3a3a"]
        )
        file_frame.pack(pady=8, padx=15, fill="x")
        file_frame.pack_propagate(False)

        checkbox_vars[filename] = ctk.BooleanVar()

        checkbox = ctk.CTkCheckBox(
            master=file_frame,
            text="",
            variable=checkbox_vars[filename],
            width=24,
            height=24,
            command=apply_wallpapers,
            fg_color=PRIMARY_COLOR,
            hover_color=PRIMARY_HOVER
        )
        checkbox.pack(side="left", padx=(20, 15), pady=18)

        # File info
        file_info_frame = ctk.CTkFrame(master=file_frame, fg_color="transparent")
        file_info_frame.pack(side="left", fill="x", expand=True, pady=10)

        file_label = ctk.CTkLabel(
            master=file_info_frame,
            text=f"🎬 {filename}",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        file_label.pack(anchor="w", padx=(0, 15))

        # File number
        number_label = ctk.CTkLabel(
            master=file_frame,
            text=f"#{i+1}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=["#666666", "#888888"],
            width=40
        )
        number_label.pack(side="right", padx=(0, 20), pady=18)

# Apply wallpapers
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

# Remove wallpapers
def remove_from_apply():
    if not current_directory:
        messagebox.showwarning("Warning", "Select a directory first!")
        return

    apply_folder = os.path.join(current_directory, "Apply")
    if not os.path.exists(apply_folder):
        messagebox.showinfo("Info", "No wallpapers to remove.")
        return

    for filename in os.listdir(apply_folder):
        src = os.path.join(apply_folder, filename)
        dst = os.path.join(current_directory, filename)
        if os.path.exists(src) and not os.path.exists(dst):
            try:
                shutil.move(src, dst)
            except Exception as e:
                messagebox.showerror("Error", f"{filename}: {e}")

    fetch_wallpaper()

# UI
load_config()

# Navbar Frame
navbar_frame = ctk.CTkFrame(
    master=app,
    height=80,
    corner_radius=0,
    fg_color=NAVBAR_COLOR
)
navbar_frame.pack(fill="x", side="top")
navbar_frame.pack_propagate(False)

# Navbar Left
navbar_left = ctk.CTkFrame(master=navbar_frame, fg_color="transparent")
navbar_left.pack(side="left", fill="y", padx=30, pady=15)

title_label = ctk.CTkLabel(
    master=navbar_left,
    text="🎬 Mpvpaper Client",
    font=ctk.CTkFont(size=28, weight="bold"),
    text_color=["#ffffff", "#ffffff"]
)
title_label.pack(side="left")

subtitle_label = ctk.CTkLabel(
    master=navbar_left,
    text="v2.0 • By Helixo22",
    font=ctk.CTkFont(size=12),
    text_color=["#cccccc", "#888888"]
)
subtitle_label.pack(side="left", padx=(15, 0), pady=(5, 0))

# Navbar Right
navbar_right = ctk.CTkFrame(master=navbar_frame, fg_color="transparent")
navbar_right.pack(side="right", fill="y", padx=20, pady=15)


switch_1 = ctk.CTkSwitch(
    master=navbar_right,
    text="Wallpaper Active",
    command=on_off,
    variable=switch_var,
    onvalue="on",
    offvalue="off",
    font=ctk.CTkFont(size=14, weight="bold"),
    text_color=["#ffffff", "#ffffff"],
    fg_color=PRIMARY_COLOR,
    progress_color=PRIMARY_HOVER
)
switch_1.pack(side="right", padx=(20, 0))

# Window controls
controls_frame = ctk.CTkFrame(master=navbar_right, fg_color="transparent")
controls_frame.pack(side="right")

hide_button = ctk.CTkButton(
    master=controls_frame,
    text="−",
    width=35,
    height=35,
    fg_color=ACCENT_COLOR,
    hover_color=ACCENT_HOVER,
    command=hide_window,
    corner_radius=8,
    font=ctk.CTkFont(size=20, weight="bold")
)
hide_button.pack(side="right", padx=(0, 8))

close_button = ctk.CTkButton(
    master=controls_frame,
    text="×",
    width=35,
    height=35,
    fg_color=DANGER_COLOR,
    hover_color=["#c44752", "#ff5757"],
    command=close_app,
    corner_radius=8,
    font=ctk.CTkFont(size=20, weight="bold")
)
close_button.pack(side="right")

# Main
main_content_frame = ctk.CTkFrame(
    master=app,
    corner_radius=0,
    fg_color=["#f8f9fa", "#0d1117"]
)
main_content_frame.pack(fill="both", expand=True)

# Control Panel
control_panel = ctk.CTkFrame(
    master=main_content_frame,
    height=140,
    corner_radius=15,
    fg_color=["#ffffff", "#1a1a1a"],
    border_width=1,
    border_color=["#e0e0e0", "#3a3a3a"]
)
control_panel.pack(fill="x", padx=20, pady=(20, 10))
control_panel.pack_propagate(False)

# Status Section
status_frame = ctk.CTkFrame(master=control_panel, fg_color="transparent")
status_frame.pack(fill="x", padx=20, pady=(15, 10))

status_label = ctk.CTkLabel(
    master=status_frame,
    text="Current Directory: Not selected",
    font=ctk.CTkFont(size=14, weight="bold"),
    anchor="w"
)
status_label.pack(side="left")

file_count_label = ctk.CTkLabel(
    master=status_frame,
    text="Files Found: 0 MP4s",
    font=ctk.CTkFont(size=12),
    text_color=["#666666", "#888888"],
    anchor="e"
)
file_count_label.pack(side="right")

# Button
button_panel = ctk.CTkFrame(master=control_panel, fg_color="transparent")
button_panel.pack(fill="x", padx=20, pady=(0, 15))


directory_text = "📁 Set Directory"
if current_directory:
    directory_name = os.path.basename(current_directory)
    directory_text = f"📁 {directory_name}"

set_directory_button = ctk.CTkButton(
    master=button_panel,
    text=directory_text,
    command=set_directory,
    width=180,
    height=45,
    corner_radius=12,
    font=ctk.CTkFont(size=14, weight="bold"),
    fg_color=PRIMARY_COLOR,
    hover_color=PRIMARY_HOVER
)
set_directory_button.pack(side="left", padx=(0, 10))


fetch_wallpaper_button = ctk.CTkButton(
    master=button_panel,
    text="🔄 Fetch Wallpapers",
    command=fetch_wallpaper,
    width=160,
    height=45,
    corner_radius=12,
    font=ctk.CTkFont(size=14, weight="bold"),
    fg_color=ACCENT_COLOR,
    hover_color=ACCENT_HOVER
)
fetch_wallpaper_button.pack(side="left", padx=(0, 10))


remove_wallpapers_button = ctk.CTkButton(
    master=button_panel,
    text="↩️ Remove from Apply",
    command=remove_from_apply,
    width=160,
    height=45,
    corner_radius=12,
    font=ctk.CTkFont(size=14, weight="bold"),
    fg_color=["#6c757d", "#495057"],
    hover_color=["#5a6268", "#6c757d"]
)
remove_wallpapers_button.pack(side="left")

# Load directory
if current_directory:
    directory_name = os.path.basename(current_directory)
    status_label.configure(text=f"Current Directory: {directory_name}")

app.mainloop()
