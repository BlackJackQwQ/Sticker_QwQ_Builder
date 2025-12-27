import customtkinter as ctk
import threading
import cv2
from typing import Tuple, Optional, Callable
from pathlib import Path
from PIL import Image, ImageSequence, ImageDraw

from UI.ViewUtils import COLORS, AsyncImageLoader
from Resources.Icons import CARD_PADDING

# Constants for render sizes
SIZE_LARGE = (320, 320)
SIZE_SMALL = (180, 180)
SIZE_LIST  = (48, 48)

class CardUtils:
    """
    Shared mechanics for all card types:
    - Base Frame Factory
    - Hover/Click Binding
    - Animation & Image Loading Engine
    """
    def __init__(self, app):
        self.app = app
        self.refresh_theme_colors()

    def refresh_theme_colors(self):
        self.COL_BG = COLORS["card_bg"] 
        self.COL_BORDER = COLORS["card_border"]
        self.COL_HOVER = COLORS["card_hover"]

    def highlight_selected_cards(self):
        """Updates border color for selected stickers."""
        sel_list = getattr(self.app.logic, 'selected_stickers', [])
        selected_ids = {id(s[0]) for s in sel_list}
        
        for card in self.app.cards:
            if not card.winfo_exists(): continue
            if hasattr(card, 'sticker_data'):
                if id(card.sticker_data) in selected_ids:
                    card.configure(border_color=COLORS["accent"], border_width=3)
                else:
                    card.configure(border_color=self.COL_BORDER, border_width=2)

    # ==========================================================================
    #   BASE FRAME CONSTRUCTION
    # ==========================================================================

    def _get_grid_position(self, index: int) -> Tuple[int, int]:
        if self.app.current_layout_mode == "List": 
            return index, 0
        else: 
            return index // self.app.content_columns, index % self.app.content_columns

    def create_base_frame(self, index: int) -> ctk.CTkFrame:
        """Creates the outer frame for any card type."""
        row, col = self._get_grid_position(index)
        
        card = ctk.CTkFrame(
            self.app.content_area, 
            corner_radius=10, 
            border_width=2, 
            border_color=self.COL_BORDER, 
            fg_color=self.COL_BG
        )
        
        # State placeholders
        card.image_label = None
        card.image_path = None
        card.placeholder_text = ""
        card.last_size_request = None 
        card.anim_loop = None 
        card.is_animated_content = False 
        
        if self.app.current_layout_mode == "List":
            # List Layout
            card.grid(row=row, column=col, sticky="ew", padx=15, pady=4)
            card.configure(height=68) 
            card.grid_propagate(False)
            card.grid_columnconfigure(1, weight=1)
            card.grid_rowconfigure(0, weight=1)
        else:
            # Grid Layout
            card.grid(row=row, column=col, sticky="nsew", padx=CARD_PADDING, pady=CARD_PADDING)
            card.grid_propagate(False) 
            card.grid_columnconfigure(0, weight=1)
            card.grid_rowconfigure(0, weight=1) 
            card.grid_rowconfigure(1, weight=0)
            
        return card

    def bind_hover_effects(self, card_frame: ctk.CTkFrame, on_click_cmd: Callable, on_double_click_cmd: Optional[Callable] = None):
        """Attaches hover/click events to card and children."""
        def on_enter(e):
            if not card_frame.winfo_exists(): return
            is_selected = False
            if hasattr(card_frame, 'sticker_data'):
                sel_list = getattr(self.app.logic, 'selected_stickers', [])
                sel_ids = [id(x[0]) for x in sel_list]
                if id(card_frame.sticker_data) in sel_ids: is_selected = True
            
            if not is_selected:
                card_frame.configure(border_color=self.COL_HOVER, fg_color=self.COL_HOVER)

        def on_leave(e):
            if not card_frame.winfo_exists(): return
            is_selected = False
            if hasattr(card_frame, 'sticker_data'):
                sel_list = getattr(self.app.logic, 'selected_stickers', [])
                sel_ids = [id(x[0]) for x in sel_list]
                if id(card_frame.sticker_data) in sel_ids: is_selected = True
            
            target_border = COLORS["accent"] if is_selected else self.COL_BORDER
            card_frame.configure(border_color=target_border, fg_color=self.COL_BG)

        def recursive_bind(widget):
            try:
                if not widget.winfo_exists(): return
                widget.bind("<Button-1>", lambda e: on_click_cmd(e), add="+")
                if on_double_click_cmd: widget.bind("<Double-Button-1>", lambda e: on_double_click_cmd(), add="+")
                widget.bind("<Enter>", on_enter, add="+")
                widget.bind("<Leave>", on_leave, add="+")
                try: widget.configure(cursor="hand2")
                except: pass 
                for child in widget.winfo_children(): recursive_bind(child)
            except: pass

        self.app.after(50, lambda: recursive_bind(card_frame) if card_frame.winfo_exists() else None)

    # ==========================================================================
    #   ANIMATION ENGINE
    # ==========================================================================

    def is_file_animated(self, path: str) -> bool:
        if not path or not Path(path).exists(): return False
        if path.lower().endswith((".gif", ".tgs", ".webm", ".mp4", ".mkv")): return True
        try:
            with Image.open(path) as img:
                if getattr(img, "is_animated", False): return True
                if img.format == "GIF": return True
            return False
        except: return False

    def _apply_play_overlay(self, pil_img: Image.Image) -> Image.Image:
        """Draws a play button overlay on the PIL image."""
        if pil_img.mode != 'RGBA': pil_img = pil_img.convert('RGBA')
        draw = ImageDraw.Draw(pil_img)
        w, h = pil_img.size
        
        icon_size = int(min(w, h) * 0.15)
        if icon_size < 20: icon_size = 20
        if icon_size > 48: icon_size = 48
        
        margin = int(icon_size * 0.5)
        cx, cy = w - margin - (icon_size // 2), h - margin - (icon_size // 2)
        radius = icon_size // 2
        
        # Circle
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill="#000000AA", outline=None)
        
        # Triangle
        tri_r = radius * 0.5
        draw.polygon([(cx-tri_r+2, cy-tri_r), (cx-tri_r+2, cy+tri_r), (cx+tri_r+2, cy)], fill=COLORS["accent"])
        
        return pil_img

    def load_image_to_label(self, label_widget: ctk.CTkLabel, image_path: Optional[str], size: Tuple[int, int], placeholder_text: str = "", add_overlay: bool = False):
        if not image_path:
            if placeholder_text and label_widget.winfo_exists(): 
                try:
                    label_widget.configure(image=None, text=placeholder_text, text_color=COLORS["text_sub"])
                except Exception:
                    try: label_widget.configure(text=placeholder_text)
                    except: pass
            return

        if image_path.lower().endswith(('.webm', '.mp4', '.mkv')):
             if label_widget.winfo_exists(): 
                 try:
                    label_widget.configure(image=None, text="VIDEO", text_color=COLORS["text_sub"])
                 except: pass
             return

        if add_overlay:
            threading.Thread(target=self._load_image_with_overlay_thread, args=(label_widget, image_path, size), daemon=True).start()
        else:
            def on_ready(ctk_img):
                try:
                    if label_widget.winfo_exists():
                        if ctk_img: 
                            label_widget.configure(image=ctk_img, text="")
                        else:
                            label_widget.configure(image=None, text="⚠️", text_color=COLORS["btn_negative"])
                except: pass
            AsyncImageLoader.load(image_path, size, on_ready)

    def _load_image_with_overlay_thread(self, label_widget, path, size):
        try:
            # 1. Background: Heavy PIL Operations (Safe)
            pil_img = Image.open(path)
            pil_img.thumbnail(size, Image.Resampling.LANCZOS)
            pil_img = self._apply_play_overlay(pil_img)
            
            # 2. Main Thread: Create CTkImage and Update UI (Safe)
            def on_main_thread():
                if label_widget.winfo_exists():
                    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
                    label_widget.configure(image=ctk_img, text="")

            self.app.after(0, on_main_thread)
            
        except Exception:
            self.app.after(0, lambda: label_widget.configure(image=None, text="⚠️", text_color=COLORS["btn_negative"]) if label_widget.winfo_exists() else None)

    def animate_card(self, card: ctk.CTkFrame, path: str, size: Tuple[int, int], label: ctk.CTkLabel):
        """Dispatches animation task."""
        if path.lower().endswith(('.webm', '.mp4', '.mkv')):
            threading.Thread(target=self._load_video_frames, args=(card, path, size, label), daemon=True).start()
            return

        try:
            frames = []
            duration = 100
            with Image.open(path) as im:
                is_anim = getattr(im, "is_animated", False) or im.format == "GIF"
                if not is_anim: raise ValueError("Not animated")
                duration = im.info.get('duration', 100) or 100
                if duration < 20: duration = 100

                iterator = ImageSequence.Iterator(im)
                for i, frame in enumerate(iterator):
                    if i > 40: break 
                    f = frame.copy()
                    f.thumbnail(size, Image.Resampling.LANCZOS)
                    f = self._apply_play_overlay(f)
                    frames.append(ctk.CTkImage(light_image=f, size=size))
            
            if not frames: raise ValueError("No frames")
            self._start_animation_loop(card, frames, duration, label)
        except:
            self.load_image_to_label(label, path, size, add_overlay=True)

    def _load_video_frames(self, card, path, size, label):
        pil_frames = [] # Use raw PIL images in thread
        try:
            cap = cv2.VideoCapture(path)
            i = 0
            while True:
                ret, frame = cap.read()
                if not ret or i > 30: break 
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb)
                pil_img.thumbnail(size, Image.Resampling.LANCZOS)
                pil_img = self._apply_play_overlay(pil_img)
                pil_frames.append(pil_img)
                i += 1
            cap.release()
        except: pass

        if pil_frames:
            # Transfer to Main Thread for CTkImage creation
            def on_main_thread():
                if not card.winfo_exists(): return
                # Create CTkImages safely on main thread
                ctk_frames = [ctk.CTkImage(light_image=f, size=size) for f in pil_frames]
                self._start_animation_loop(card, ctk_frames, 50, label)

            self.app.after(0, on_main_thread)
        else:
            self.app.after(0, lambda: label.configure(image=None, text="⚠️", text_color=COLORS["btn_negative"]))

    def _start_animation_loop(self, card, frames, duration, label):
        def loop(idx):
            if not card.winfo_exists(): return
            try:
                label.configure(image=frames[idx], text="")
                card.anim_loop = card.after(duration, lambda: loop((idx + 1) % len(frames)))
            except: pass
        loop(0)

    def update_card_image(self, card: ctk.CTkFrame, new_size: Tuple[int, int]):
        """Refreshes content on resize."""
        if not card.winfo_exists(): return
        if not hasattr(card, 'image_label') or not card.image_label: return
        if not hasattr(card, 'image_path') or not card.image_path: return
            
        if card.last_size_request:
            diff_w = abs(card.last_size_request[0] - new_size[0])
            if diff_w < 5: return 
            
        card.last_size_request = new_size
        
        if getattr(card, 'is_animated_content', False):
            if card.anim_loop: card.after_cancel(card.anim_loop)
            self.animate_card(card, card.image_path, new_size, card.image_label)
        else:
            is_anim_flag = getattr(card, 'is_animated_content', False)
            self.load_image_to_label(card.image_label, card.image_path, new_size, card.placeholder_text, add_overlay=is_anim_flag)