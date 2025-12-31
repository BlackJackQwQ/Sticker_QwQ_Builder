import customtkinter as ctk
import os
import subprocess
import unicodedata
import time
import cv2  # ADDED: OpenCV for video decoding
from pathlib import Path
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Optional, Tuple, Union, Callable, List

# --- NEW IMPORTS FROM REFACTORED MODULES ---
from Core.Config import logger, TEMP_FOLDER, SETTINGS_FILE, BASE_DIR, load_json
from Resources.Themes import THEME_PALETTES

# ==============================================================================
#   ACTIVE APPLICATION STATE
# ==============================================================================

# This dictionary holds the CURRENTLY ACTIVE colors.
# UI components will import this to know what color to draw.
COLORS: Dict[str, str] = {}

# Initialize with default to prevent ImportErrors before init
COLORS.update(THEME_PALETTES["Classic"])

# ==============================================================================
#   THEME MANAGER
# ==============================================================================

def apply_theme_palette(theme_name: str) -> str:
    """
    Updates the global COLORS dictionary based on the selected theme.
    Returns: The appearance mode ('Dark' or 'Light').
    """
    selected_theme = {}
    
    # 1. Check for Custom Theme
    if theme_name == "Custom":
        data = load_json(SETTINGS_FILE)
        custom_data = data.get("custom_theme_data", {})
        
        if custom_data and "bg_main" in custom_data:
            selected_theme = custom_data
        else:
            theme_name = "Classic" # Fallback
            
    # 2. Load Preset from Resources
    if theme_name != "Custom":
        selected_theme = THEME_PALETTES.get(theme_name, THEME_PALETTES["Classic"])
    
    # 3. Update Global State
    COLORS.clear()
    COLORS.update(selected_theme)
    
    return selected_theme.get("mode", "Dark")

# ==============================================================================
#   IMAGE & VIDEO HANDLING (Visuals)
# ==============================================================================

_IMAGE_CACHE: Dict[Tuple[str, Tuple[int, int]], ctk.CTkImage] = {}

class AsyncImageLoader:
    """
    Loads images in a background thread to keep the UI smooth.
    """
    _executor = ThreadPoolExecutor(max_workers=4)
    
    @classmethod
    def load(cls, path: str, size: Tuple[int, int], callback_on_complete: Callable[[Optional[ctk.CTkImage]], None]):
        if not path or not os.path.exists(path):
            callback_on_complete(None)
            return

        cache_key = (path, size)
        if cache_key in _IMAGE_CACHE:
            callback_on_complete(_IMAGE_CACHE[cache_key])
            return

        def _load_task() -> Optional[ctk.CTkImage]:
            try:
                with Image.open(path) as pil_img:
                    pil_img.load()
                    pil_copy = pil_img.copy()
                    pil_copy.thumbnail(size, Image.Resampling.LANCZOS)
                    return ctk.CTkImage(light_image=pil_copy, size=size)
            except Exception as e:
                logger.error(f"Image load error ({path}): {e}")
                return None

        def _done_callback(future: Future):
            try:
                img = future.result()
                if img: _IMAGE_CACHE[cache_key] = img
                callback_on_complete(img)
            except Exception as e:
                logger.error(f"Async load callback error: {e}")
                callback_on_complete(None)

        future = cls._executor.submit(_load_task)
        future.add_done_callback(_done_callback)

def load_ctk_image(path: str, size: Tuple[int, int]) -> Optional[ctk.CTkImage]:
    """Synchronous image loader (blocks UI, use sparingly)."""
    if not path or not os.path.exists(path): return None
    
    cache_key = (path, size)
    if cache_key in _IMAGE_CACHE: return _IMAGE_CACHE[cache_key]
    
    try:
        with Image.open(path) as pil_img:
            pil_img.load()
            pil_copy = pil_img.copy()
            pil_copy.thumbnail(size, Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=pil_copy, size=size)
            _IMAGE_CACHE[cache_key] = ctk_img
            return ctk_img
    except Exception as e:
        logger.error(f"Sync load error ({path}): {e}")
        return None

def load_video_frames(path: str, size: Tuple[int, int], max_frames: int = 120) -> List[ctk.CTkImage]:
    """
    ADDED: Decodes video files (WebM, MP4) into a list of CTkImages using OpenCV.
    This creates a pre-buffered list of frames for smooth playback.
    """
    if not path or not os.path.exists(path): return []
    
    frames = []
    try:
        # Open video file
        cap = cv2.VideoCapture(path)
        if not cap.isOpened(): return []
        
        count = 0
        while True:
            ret, frame = cap.read()
            # Stop if no frame or limit reached (prevent memory overflow)
            if not ret or count >= max_frames: 
                break
                
            # 1. Resize Frame (OpenCV uses width, height)
            # Use INTER_AREA for shrinking (better quality), INTER_LINEAR for zooming
            frame = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
            
            # 2. Color Convert (OpenCV is BGR, we need RGB)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 3. Convert to Pillow -> CTkImage
            pil_img = Image.fromarray(frame)
            ctk_img = ctk.CTkImage(light_image=pil_img, size=size)
            
            frames.append(ctk_img)
            count += 1
            
        cap.release()
        
    except Exception as e:
        logger.error(f"Video decode error ({path}): {e}")
        return []
        
    return frames

def resize_image_to_temp(path: str, size_name: str) -> Optional[str]:
    """Resizes image/converts WebP for clipboard usage."""
    if not path or not os.path.exists(path): return None
    
    size_map = {"Large": 1024, "Big": 512, "Normal": 256, "Small": 128, "Tiny": 64}
    target_dim = size_map.get(size_name.split(" ")[0])
    is_webp = path.lower().endswith(".webp")
    
    if not target_dim and not is_webp: return path
    
    try:
        with Image.open(path) as img:
            # Determine new size if scaling needed
            if target_dim:
                ratio = min(target_dim / img.width, target_dim / img.height)
                new_w = int(img.width * ratio)
                new_h = int(img.height * ratio)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
            timestamp = int(time.time() * 1000)
            
            # Convert if necessary (WebP -> PNG for better compatibility)
            ext = ".png"
            if img.format == 'GIF' and not target_dim: ext = ".gif"
            
            temp_path = os.path.join(TEMP_FOLDER, f"temp_{timestamp}_{os.path.basename(path).split('.')[0]}{ext}")
            
            img.save(temp_path)
            return temp_path
    except Exception as e:
        logger.error(f"Resize error: {e}")
        return path

# ==============================================================================
#   WINDOW & OS HELPERS
# ==============================================================================

def center_window(window: ctk.CTkToplevel, width: int, height: int):
    window.update_idletasks()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

def set_window_icon(window: Union[ctk.CTk, ctk.CTkToplevel]):
    """
    Sets the window icon. 
    CRITICAL: Includes a Windows-specific fix to ensure the Taskbar Icon updates.
    """
    try:
        ico_path = BASE_DIR / "Assets" / "Purple_Rose.ico"
        
        # 1. Windows Taskbar Fix
        # Without this, Windows groups the app under the generic 'Python' process icon
        if os.name == 'nt':
            import ctypes
            # Unique ID for this app
            app_id = 'StickerQwQ.Manager.App.1.0' 
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            except Exception:
                pass

        # 2. Set the actual bitmap
        if ico_path.exists():
            # Small delay ensures window handle is ready
            window.after(200, lambda: window.iconbitmap(str(ico_path)))
            
    except Exception as e:
        logger.warning(f"Could not set icon: {e}")

def open_file_location(target_path: str, is_file: bool = False):
    if not os.path.exists(target_path): return
    try:
        if os.name == 'nt':
            path = os.path.normpath(target_path)
            if is_file: subprocess.run(['explorer', '/select,', path])
            else: os.startfile(path)
        elif os.name == 'posix':
            subprocess.run(['xdg-open' if os.sys.platform != 'darwin' else 'open', target_path])
    except Exception as e:
        logger.error(f"Error opening file: {e}")

def copy_to_clipboard(path: str):
    if os.name != 'nt': return
    try:
        # Use PowerShell to set the clipboard to the FILE object (allowing paste into Discord/Telegram)
        subprocess.run(f'powershell -command "Get-Item \'{path}\' | Set-Clipboard"', shell=True, check=True)
    except Exception as e: 
        logger.error(f"Clipboard copy failed: {e}")

# ==============================================================================
#   TEXT FORMATTERS
# ==============================================================================

def is_system_tag(tag: str) -> bool:
    if tag in ["Static", "Animated", "Local", "NSFW"]: return True
    if not tag: return False
    try:
        # Detect Emoji or Symbols
        if unicodedata.category(tag[0]).startswith('S') or ord(tag[0]) > 0x2000: return True
    except: pass
    return False

def format_tag_text(tag: str) -> str:
    return tag

# ==============================================================================
#   UI HELPER CLASSES (Tooltips, Notifications)
# ==============================================================================

class Tooltip:
    """
    A lightweight, themed hover tooltip.
    Displays text in a small floating window after a delay.
    """
    def __init__(self, widget, text: str = ""):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        
        # Bind events
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave) # Hide on click

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        # Delay 500ms before showing
        self.id = self.widget.after(500, self.showtip)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def showtip(self, event=None):
        if not self.text: return
        
        # 1. FIXED GLITCH: Get Mouse Position (Screen relative)
        # We offset +20px so the tooltip window does NOT spawn under the cursor.
        # This prevents the widget from receiving a <Leave> event immediately.
        x = self.widget.winfo_pointerx() + 20
        y = self.widget.winfo_pointery() + 20
        
        # Create Floating Window
        self.tip_window = ctk.CTkToplevel(self.widget)
        self.tip_window.wm_overrideredirect(True) # Remove OS title bar
        self.tip_window.wm_geometry(f"+{x}+{y}")
        self.tip_window.attributes('-topmost', True) # Keep on top
        
        # 2. IMPROVED STYLING
        # Background: Use 'card_hover' for nice contrast (lighter than sidebar)
        # Border: Use 'text_sub' for a subtle but distinct edge
        bg_color = COLORS.get("card_hover", "#333333")
        border_col = COLORS.get("text_sub", "#888888")
        text_color = COLORS.get("text_main", "#FFFFFF")

        # --- TRANSPARENCY FIX (The Fix for Round Corners) ---
        # We set the window background to a specific "chroma key" color and 
        # tell the OS to render that color as fully transparent.
        # This allows the rounded corners of the inner frame to be visible
        # without the rectangular window background showing through.
        if os.name == 'nt':
            # Use a near-black color that is unlikely to be the actual border color
            self.tip_window.configure(fg_color="#000001")
            self.tip_window.attributes("-transparentcolor", "#000001")
        else:
            # Fallback for MacOS/Linux (usually handles transparency better natively)
            self.tip_window.configure(fg_color="transparent")

        frame = ctk.CTkFrame(
            self.tip_window, 
            fg_color=bg_color,
            corner_radius=6, 
            border_width=1, 
            border_color=border_col
        )
        frame.pack(fill="both", expand=True)
        
        # Text Label (Smaller font, nice padding)
        label = ctk.CTkLabel(
            frame, 
            text=self.text, 
            text_color=text_color, 
            font=("Segoe UI", 11), 
            justify='left'
        )
        label.pack(padx=10, pady=5)

    def hidetip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

class ToastNotification:
    def __init__(self, master_window: ctk.CTk, title: str, message: str, duration: int = 3000):
        try:
            self.top = ctk.CTkToplevel(master_window)
            self.top.overrideredirect(True)
            self.top.attributes('-topmost', True)
            self.top.configure(fg_color=COLORS["card_bg"])
            
            self.frame = ctk.CTkFrame(self.top, fg_color=COLORS["bg_sidebar"], border_width=2, border_color=COLORS["accent"], corner_radius=10)
            self.frame.pack(fill="both", expand=True)
            
            ctk.CTkLabel(self.frame, text=title, font=("Segoe UI", 14, "bold"), text_color=COLORS["accent"]).pack(anchor="w", padx=15, pady=(10, 2))
            ctk.CTkLabel(self.frame, text=message, font=("Segoe UI", 12), text_color=COLORS["text_main"]).pack(anchor="w", padx=15, pady=(0, 10))
            
            master_window.update_idletasks()
            try:
                x = master_window.winfo_x() + master_window.winfo_width() - 260
                y = master_window.winfo_y() + master_window.winfo_height() - 90
                self.top.geometry(f"250x70+{x}+{y}")
            except: self.top.geometry("250x70")
            
            self.top.after(duration, self.fade_out)
        except Exception as e:
            logger.error(f"Toast Error: {e}")
        
    def fade_out(self):
        try:
            alpha = self.top.attributes("-alpha")
            if alpha > 0:
                self.top.attributes("-alpha", alpha - 0.1)
                self.top.after(50, self.fade_out)
            else: self.top.destroy()
        except: self.top.destroy()