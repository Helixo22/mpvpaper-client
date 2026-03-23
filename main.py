import customtkinter as ctk
import os
import signal
import subprocess
import json
import shutil
from tkinter.filedialog import askdirectory
import webbrowser

# ── App Init ──────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
app = ctk.CTk()
app.geometry("1020x680")
app.minsize(820, 560)
app.title("Mpvpaper Client")

# ── Palette (GitHub dark style) ───────────────────────────────────────────────
SIDEBAR_BG   = "#161b22"
CONTENT_BG   = "#0d1117"
CARD_BG      = "#21262d"
CARD_BORDER  = "#30363d"
GREEN        = "#238636"
GREEN_HOVER  = "#2ea043"
DANGER       = "#da3633"
DANGER_HOVER = "#f85149"
TEXT_PRI     = "#e6edf3"
TEXT_SEC     = "#8b949e"
TEXT_MUT     = "#484f58"
LIVE_FG      = "#79c0ff"
LIVE_BG      = "#0c2d6b"

# ── State ─────────────────────────────────────────────────────────────────────
config_file       = "mpvpaper_config.json"
current_directory = None
# filename → {"applied": bool, "size": str, "path": str}
all_wallpapers    = {}
status_label      = None
stats_label       = None
dir_name_label    = None
dir_path_label    = None
mpv_dot_label     = None
switch_var        = None

print("\nRequires mpvpaper — https://github.com/GhostNaN/mpvpaper\n")

# ── Config ────────────────────────────────────────────────────────────────────
def load_config():
    global current_directory
    try:
        if os.path.exists(config_file):
            with open(config_file) as f:
                current_directory = json.load(f).get("wallpaper_directory")
    except Exception as e:
        print(f"Config load error: {e}")

def save_config():
    try:
        with open(config_file, "w") as f:
            json.dump({"wallpaper_directory": current_directory}, f, indent=2)
    except Exception as e:
        print(f"Config save error: {e}")

# ── Helpers ───────────────────────────────────────────────────────────────────
def format_size(path):
    try:
        s = os.path.getsize(path)
        for u in ["B", "KB", "MB", "GB"]:
            if s < 1024:
                return f"{s:.0f} {u}"
            s /= 1024
        return f"{s:.1f} GB"
    except Exception:
        return ""

def set_status(msg):
    if status_label:
        status_label.configure(text=msg)

def update_stats():
    if stats_label:
        total   = len(all_wallpapers)
        applied = sum(1 for w in all_wallpapers.values() if w["applied"])
        stats_label.configure(text=f"{total} wallpapers  •  {applied} applied")

def check_mpvpaper_running():
    result = subprocess.run(["pgrep", "mpvpaper"], capture_output=True, text=True)
    return bool(result.stdout.strip())

# ── mpvpaper control ──────────────────────────────────────────────────────────
def on_off():
    if switch_var.get() == "off":
        result = subprocess.run(["pgrep", "mpvpaper"], capture_output=True, text=True)
        for pid in result.stdout.strip().split("\n"):
            if pid.strip().isdigit():
                try:
                    os.kill(int(pid), signal.SIGTERM)
                except Exception:
                    pass
        set_status("mpvpaper stopped")
        mpv_dot_label.configure(text="● OFF", text_color=DANGER)
    else:
        if not current_directory:
            set_status("Select a directory first!")
            switch_var.set("off")
            return
        apply_dir = os.path.join(current_directory, "Apply")
        wdir = apply_dir if os.path.exists(apply_dir) else current_directory
        if not os.path.exists(wdir):
            set_status("Directory not found!")
            switch_var.set("off")
            return
        try:
            subprocess.Popen(["mpvpaper", "-o", "no-audio --loop-playlist --hwdec=vaapi --really-quiet", "*", wdir])
            set_status(f"mpvpaper started → {os.path.basename(wdir)}/")
            mpv_dot_label.configure(text="● ON", text_color=GREEN_HOVER)
        except Exception as e:
            set_status(f"Error: {e}")
            switch_var.set("off")

# ── Directory ─────────────────────────────────────────────────────────────────
def set_directory():
    global current_directory
    path = askdirectory(title="Select Wallpaper Directory")
    if path:
        current_directory = path
        save_config()
        refresh_dir_labels()
        fetch_wallpapers()

def refresh_dir_labels():
    if not dir_name_label:
        return
    if current_directory:
        dir_name_label.configure(text=os.path.basename(current_directory))
        dir_path_label.configure(text=current_directory)
    else:
        dir_name_label.configure(text="Not selected")
        dir_path_label.configure(text="")

# ── Wallpaper management ──────────────────────────────────────────────────────
def fetch_wallpapers():
    global all_wallpapers
    if not current_directory or not os.path.exists(current_directory):
        set_status("Invalid directory")
        return
    all_wallpapers = {}
    apply_dir = os.path.join(current_directory, "Apply")
    for f in os.listdir(current_directory):
        if f.lower().endswith(".mp4"):
            p = os.path.join(current_directory, f)
            all_wallpapers[f] = {"applied": False, "size": format_size(p), "path": p}
    if os.path.exists(apply_dir):
        for f in os.listdir(apply_dir):
            if f.lower().endswith(".mp4"):
                p = os.path.join(apply_dir, f)
                all_wallpapers[f] = {"applied": True, "size": format_size(p), "path": p}
    update_stats()
    applied = sum(1 for w in all_wallpapers.values() if w["applied"])
    set_status(f"Loaded {len(all_wallpapers)} wallpapers  ({applied} applied)")
    render_list()

def toggle_wallpaper(filename):
    """Move a wallpaper into/out of the Apply folder."""
    if not current_directory:
        return
    info = all_wallpapers.get(filename)
    if not info:
        return
    apply_dir = os.path.join(current_directory, "Apply")
    if info["applied"]:
        src = os.path.join(apply_dir, filename)
        dst = os.path.join(current_directory, filename)
        if os.path.exists(src) and not os.path.exists(dst):
            try:
                shutil.move(src, dst)
                info["applied"] = False
                info["path"]    = dst
                set_status(f"Removed from Apply: {filename}")
            except Exception as e:
                set_status(f"Error: {e}")
                return
    else:
        if not os.path.exists(apply_dir):
            os.makedirs(apply_dir)
        src = os.path.join(current_directory, filename)
        dst = os.path.join(apply_dir, filename)
        if os.path.exists(src) and not os.path.exists(dst):
            try:
                shutil.move(src, dst)
                info["applied"] = True
                info["path"]    = dst
                set_status(f"Applied: {filename}")
            except Exception as e:
                set_status(f"Error: {e}")
                return
    update_stats()
    render_list()

def remove_all_applied():
    if not current_directory:
        set_status("No directory selected")
        return
    apply_dir = os.path.join(current_directory, "Apply")
    if not os.path.exists(apply_dir):
        set_status("No applied wallpapers")
        return
    count = 0
    for f, info in all_wallpapers.items():
        if info["applied"]:
            src = os.path.join(apply_dir, f)
            dst = os.path.join(current_directory, f)
            if os.path.exists(src) and not os.path.exists(dst):
                try:
                    shutil.move(src, dst)
                    info["applied"] = False
                    info["path"]    = dst
                    count += 1
                except Exception as e:
                    set_status(f"Error: {e}")
    update_stats()
    set_status(f"Removed {count} wallpaper(s) from Apply")
    render_list()

def find_wallpapers():
    webbrowser.open("https://www.desktophut.com/", new=2)

# ── List rendering ────────────────────────────────────────────────────────────
def render_list():
    for w in list_frame.winfo_children():
        w.destroy()

    if not all_wallpapers:
        ctk.CTkLabel(
            list_frame,
            text="No wallpapers found\nSelect a directory and press Refresh",
            font=ctk.CTkFont(size=15),
            text_color=TEXT_SEC,
            justify="center",
        ).pack(expand=True, pady=100)
        return

    # Applied first, then alphabetical
    sorted_items = sorted(
        all_wallpapers.items(),
        key=lambda x: (not x[1]["applied"], x[0].lower()),
    )
    for filename, info in sorted_items:
        _make_item(filename, info)

def _make_item(filename, info):
    applied = info["applied"]
    card = ctk.CTkFrame(
        list_frame,
        fg_color=CARD_BG,
        corner_radius=10,
        border_width=1,
        border_color="#1f6feb" if applied else CARD_BORDER,
    )
    card.pack(fill="x", pady=4)

    var = ctk.BooleanVar(value=applied)

    ctk.CTkCheckBox(
        card,
        text="",
        variable=var,
        command=lambda fn=filename: toggle_wallpaper(fn),
        width=20,
        fg_color=GREEN,
        hover_color=GREEN_HOVER,
        border_color=CARD_BORDER,
    ).pack(side="left", padx=(15, 12), pady=16)

    ctk.CTkLabel(
        card,
        text=filename,
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color=TEXT_PRI,
        anchor="w",
    ).pack(side="left", fill="x", expand=True, pady=16)

    right = ctk.CTkFrame(card, fg_color="transparent")
    right.pack(side="right", padx=15, pady=10)

    if applied:
        ctk.CTkLabel(
            right,
            text=" LIVE ",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=LIVE_FG,
            fg_color=LIVE_BG,
            corner_radius=5,
        ).pack(side="right", padx=(8, 0))

    if info["size"]:
        ctk.CTkLabel(
            right,
            text=info["size"],
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SEC,
        ).pack(side="right")

# ═══════════════════════════════════════════════════════════════════════════════
# BUILD UI
# ═══════════════════════════════════════════════════════════════════════════════
load_config()
app.configure(fg_color=CONTENT_BG)

# ── Navbar ────────────────────────────────────────────────────────────────────
navbar = ctk.CTkFrame(app, height=62, corner_radius=0, fg_color=SIDEBAR_BG)
navbar.pack(fill="x")
navbar.pack_propagate(False)

nav_l = ctk.CTkFrame(navbar, fg_color="transparent")
nav_l.pack(side="left", fill="y", padx=24)

ctk.CTkLabel(nav_l, text="mpvpaper",
             font=ctk.CTkFont(size=21, weight="bold"),
             text_color=TEXT_PRI).pack(side="left", pady=18)
ctk.CTkLabel(nav_l, text=" client",
             font=ctk.CTkFont(size=21),
             text_color=GREEN_HOVER).pack(side="left", pady=18)
ctk.CTkLabel(nav_l, text=" v2.1",
             font=ctk.CTkFont(size=10),
             text_color=TEXT_MUT).pack(side="left", pady=(22, 0))

nav_r = ctk.CTkFrame(navbar, fg_color="transparent")
nav_r.pack(side="right", fill="y", padx=20)

# Close / hide buttons
ctk.CTkButton(
    nav_r, text="×", width=30, height=30,
    fg_color=DANGER, hover_color=DANGER_HOVER,
    command=lambda: app.destroy(),
    corner_radius=7, font=ctk.CTkFont(size=15, weight="bold"),
).pack(side="right", pady=16)

ctk.CTkButton(
    nav_r, text="−", width=30, height=30,
    fg_color=CARD_BG, hover_color=CARD_BORDER,
    command=lambda: app.withdraw(),
    corner_radius=7, font=ctk.CTkFont(size=15, weight="bold"),
    text_color=TEXT_SEC,
).pack(side="right", padx=(0, 8), pady=16)

# Active switch + status dot
_running = check_mpvpaper_running()
switch_var = ctk.StringVar(value="on" if _running else "off")

mpv_dot_label = ctk.CTkLabel(
    nav_r,
    text="● ON" if _running else "● OFF",
    font=ctk.CTkFont(size=12, weight="bold"),
    text_color=GREEN_HOVER if _running else DANGER,
)
mpv_dot_label.pack(side="right", padx=(6, 14), pady=16)

ctk.CTkSwitch(
    nav_r, text="Active",
    command=on_off,
    variable=switch_var, onvalue="on", offvalue="off",
    font=ctk.CTkFont(size=13), text_color=TEXT_SEC,
    fg_color=TEXT_MUT, progress_color=GREEN,
    button_color=TEXT_PRI, button_hover_color="#c9d1d9",
).pack(side="right", pady=16)

# Navbar divider
ctk.CTkFrame(app, height=1, corner_radius=0, fg_color=CARD_BORDER).pack(fill="x")

# ── Body ──────────────────────────────────────────────────────────────────────
body = ctk.CTkFrame(app, fg_color="transparent", corner_radius=0)
body.pack(fill="both", expand=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
sidebar = ctk.CTkFrame(body, width=230, corner_radius=0, fg_color=SIDEBAR_BG)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

ctk.CTkFrame(body, width=1, corner_radius=0, fg_color=CARD_BORDER).pack(side="left", fill="y")

def _section_title(parent, text):
    ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(size=10, weight="bold"),
        text_color=TEXT_MUT, anchor="w",
    ).pack(fill="x", pady=(0, 7))

def _divider(parent):
    ctk.CTkFrame(parent, height=1, fg_color=CARD_BORDER).pack(
        fill="x", padx=0, pady=14
    )

# Directory section
d_sec = ctk.CTkFrame(sidebar, fg_color="transparent")
d_sec.pack(fill="x", padx=16, pady=(22, 0))

_section_title(d_sec, "DIRECTORY")

dir_name_label = ctk.CTkLabel(
    d_sec, text="Not selected",
    font=ctk.CTkFont(size=14, weight="bold"),
    text_color=TEXT_PRI, anchor="w", wraplength=196,
)
dir_name_label.pack(fill="x")

dir_path_label = ctk.CTkLabel(
    d_sec, text="",
    font=ctk.CTkFont(size=10), text_color=TEXT_MUT,
    anchor="w", wraplength=196, justify="left",
)
dir_path_label.pack(fill="x", pady=(2, 10))

ctk.CTkButton(
    d_sec, text="📁  Set Directory",
    command=set_directory, height=38, corner_radius=8,
    font=ctk.CTkFont(size=13, weight="bold"),
    fg_color=GREEN, hover_color=GREEN_HOVER, anchor="w",
).pack(fill="x")

_divider(sidebar)

# Stats section
s_sec = ctk.CTkFrame(sidebar, fg_color="transparent")
s_sec.pack(fill="x", padx=16)
_section_title(s_sec, "STATS")
stats_label = ctk.CTkLabel(
    s_sec, text="0 wallpapers  •  0 applied",
    font=ctk.CTkFont(size=12), text_color=TEXT_SEC, anchor="w",
)
stats_label.pack(fill="x")

_divider(sidebar)

# Actions section
a_sec = ctk.CTkFrame(sidebar, fg_color="transparent")
a_sec.pack(fill="x", padx=16)
_section_title(a_sec, "ACTIONS")

def _action_btn(parent, text, cmd):
    ctk.CTkButton(
        parent, text=text, command=cmd,
        height=36, corner_radius=8,
        font=ctk.CTkFont(size=13),
        fg_color=CARD_BG, hover_color=CARD_BORDER,
        text_color=TEXT_PRI, anchor="w",
    ).pack(fill="x", pady=(0, 6))

_action_btn(a_sec, "🔄  Refresh",           fetch_wallpapers)
_action_btn(a_sec, "↩  Remove All Applied", remove_all_applied)
_action_btn(a_sec, "🔍  Find Wallpapers",   find_wallpapers)

# Sidebar footer
ctk.CTkLabel(
    sidebar, text="By Helixo22",
    font=ctk.CTkFont(size=10), text_color=TEXT_MUT,
).pack(side="bottom", pady=12)

# ── Main content area ─────────────────────────────────────────────────────────
main_area = ctk.CTkFrame(body, fg_color=CONTENT_BG, corner_radius=0)
main_area.pack(side="left", fill="both", expand=True)

hdr = ctk.CTkFrame(main_area, fg_color="transparent")
hdr.pack(fill="x", padx=24, pady=(22, 8))

ctk.CTkLabel(
    hdr, text="Wallpapers",
    font=ctk.CTkFont(size=20, weight="bold"),
    text_color=TEXT_PRI, anchor="w",
).pack(side="left")

ctk.CTkLabel(
    hdr, text="Check to apply  •  Uncheck to remove",
    font=ctk.CTkFont(size=11), text_color=TEXT_MUT, anchor="e",
).pack(side="right")

ctk.CTkFrame(main_area, height=1, fg_color=CARD_BORDER).pack(fill="x", padx=24)

list_frame = ctk.CTkScrollableFrame(
    main_area,
    fg_color="transparent",
    scrollbar_button_color=CARD_BG,
    scrollbar_button_hover_color=CARD_BORDER,
)
list_frame.pack(fill="both", expand=True, padx=24, pady=12)

# ── Status bar ────────────────────────────────────────────────────────────────
ctk.CTkFrame(app, height=1, corner_radius=0, fg_color=CARD_BORDER).pack(fill="x")

sbar = ctk.CTkFrame(app, height=28, corner_radius=0, fg_color=SIDEBAR_BG)
sbar.pack(fill="x")
sbar.pack_propagate(False)

status_label = ctk.CTkLabel(
    sbar, text="Ready",
    font=ctk.CTkFont(size=11), text_color=TEXT_MUT, anchor="w",
)
status_label.pack(side="left", padx=16, fill="y")

# ── Startup ───────────────────────────────────────────────────────────────────
refresh_dir_labels()
if current_directory and os.path.exists(current_directory):
    fetch_wallpapers()
else:
    render_list()

app.mainloop()
