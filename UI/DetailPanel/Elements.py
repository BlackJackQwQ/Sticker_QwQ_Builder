import customtkinter as ctk
import tkinter.font as tkfont
from typing import Dict, Any, Callable

from UI.ViewUtils import COLORS
from Resources.Icons import (
    FONT_TITLE, FONT_SMALL, FONT_NORMAL,
    ICON_FAV_ON, ICON_FAV_OFF
)

def create_section_header(parent: ctk.CTkFrame, text: str):
    """Creates a section header with text and a horizontal divider line."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", padx=10, pady=(20, 10))
    
    ctk.CTkLabel(frame, text=text, font=FONT_TITLE, text_color=COLORS["text_sub"]).pack(side="left")
    ctk.CTkFrame(frame, height=2, fg_color=COLORS["card_border"]).pack(side="left", fill="x", expand=True, padx=(10, 0))

def create_modern_button(parent: ctk.CTkFrame, text: str, cmd: Callable) -> ctk.CTkButton:
    """Standard small utility button (e.g., Rename, Change Cover)."""
    return ctk.CTkButton(
        parent, text=text, command=cmd,
        height=28, font=FONT_SMALL, corner_radius=8,
        fg_color=COLORS["card_bg"], hover_color=COLORS["card_border"], text_color=COLORS["text_main"]
    )

def create_action_button(parent: ctk.CTkFrame, text: str, fg: str, text_col: str, cmd: Callable) -> ctk.CTkButton:
    """Large action button (e.g., Download, Remove). Packs itself automatically."""
    btn = ctk.CTkButton(
        parent, text=text, command=cmd,
        height=32, font=FONT_NORMAL, corner_radius=8,
        fg_color=fg, hover_color=fg, text_color=text_col
    )
    btn.pack(fill="x", pady=6, padx=30)
    return btn

def update_fav_btn(btn: ctk.CTkButton, is_fav: bool, colors_dict: Dict[str, str]):
    """Updates the visual state of a favorite button."""
    if is_fav:
        btn.configure(text=f"{ICON_FAV_ON} Favorited", fg_color=colors_dict["gold"], text_color=colors_dict["black"])
    else:
        btn.configure(text=f"{ICON_FAV_OFF} Favorite", fg_color=colors_dict["card_bg"], text_color=colors_dict["text_main"])

def update_smart_text(label: ctk.CTkLabel, text: str, container_width: int, base_size: int = 22, max_lines: int = 2):
    """
    Intelligently resizes text to fit within a container width using Word-Aware Simulation.
    """
    if not text:
        label.configure(text="")
        return

    # 1. Set text immediately so it's visible
    label.configure(text=text)

    # 2. Define Constraints
    # INCREASED SAFETY MARGIN: 40px to absolutely guarantee no edge clipping
    safe_width = max(50, container_width - 40)
    
    # Always set wraplength to the safe width so Tkinter knows where to wrap visualy
    label.configure(wraplength=safe_width)

    # 3. The Solver Loop (Start Big -> Go Small)
    current_size = base_size
    min_size = 12
    final_size = min_size # Default fallback

    words = text.split()
    
    while current_size >= min_size:
        # Create a temporary font object for measurement
        # Note: We assume "Segoe UI" bold as defined in Layouts.py
        font = tkfont.Font(family="Segoe UI", size=current_size, weight="bold")
        space_width = font.measure(" ")
        
        # --- SIMULATION START ---
        lines_needed = 1
        current_line_width = 0
        fits_horizontally = True
        
        for word in words:
            word_width = font.measure(word)
            
            # Critical Check: Is a single word wider than the entire container?
            if word_width > safe_width:
                fits_horizontally = False
                break # This font size is definitely too big
            
            # Logic: Can we add this word to the current line?
            # Note: We add space_width only if it's not the first word on line
            width_to_add = word_width + (space_width if current_line_width > 0 else 0)
            
            if current_line_width + width_to_add <= safe_width:
                # Fits on current line
                current_line_width += width_to_add
            else:
                # Must wrap to next line
                lines_needed += 1
                current_line_width = word_width # Start new line with this word
        
        # --- SIMULATION END ---
        
        # Decision
        if fits_horizontally and lines_needed <= max_lines:
            final_size = current_size
            break # We found the largest size that fits!
            
        current_size -= 2

    # 4. Apply the calculated font
    label.configure(font=("Segoe UI", final_size, "bold"))

def adjust_text_size(event, label: ctk.CTkLabel, base_size: int):
    """
    Legacy wrapper for backward compatibility.
    Redirects old calls to the new robust logic.
    """
    update_smart_text(label, label.cget("text"), event.width, base_size)