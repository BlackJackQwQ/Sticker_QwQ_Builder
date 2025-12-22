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

def adjust_text_size(event, label: ctk.CTkLabel, base_size: int):
    """
    Auto-shrinks text font size to fit within the container width.
    Requires tkinter.font for measurement.
    """
    width = event.width - 20
    if width < 50: return
    
    text = label.cget("text") or ""
    if not text: return

    target_size = base_size
    while target_size > 14:
        # Use a temporary font object to measure width
        font = tkfont.Font(family="Segoe UI", size=target_size, weight="bold")
        if font.measure(text) <= width: 
            break
        target_size -= 2
    
    label.configure(font=("Segoe UI", target_size, "bold"))