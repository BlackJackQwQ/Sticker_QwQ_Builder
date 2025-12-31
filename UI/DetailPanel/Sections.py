import customtkinter as ctk
from typing import List, Dict, Any, Optional

from UI.ViewUtils import COLORS, is_system_tag, format_tag_text
from Resources.Icons import (
    FONT_TITLE, FONT_SMALL, FONT_NORMAL,
    ICON_ADD, ICON_REMOVE, ICON_FOLDER
)

class TagSection:
    """
    Manages the 'Tags' header, 'Manage' button, and the flow-layout chip rendering.
    """
    def __init__(self, parent: ctk.CTkFrame, app, context_type: str):
        self.app = app
        self.context_type = context_type # "pack", "collection", or "sticker"
        
        # Container
        self.container = ctk.CTkFrame(parent, fg_color="transparent")
        self.container.pack(fill="x", padx=15, pady=10)
        
        # Header Row
        header = ctk.CTkFrame(self.container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(header, text="Tags", font=FONT_TITLE, text_color=COLORS["text_main"]).pack(side="left")
        
        ctk.CTkButton(
            header, text=f"{ICON_ADD} Manage", width=80, height=22, font=FONT_SMALL,
            fg_color=COLORS["card_bg"], hover_color=COLORS["card_border"], text_color=COLORS["text_main"],
            command=self._open_manager
        ).pack(side="right")
        
        # List Container (Chips go here)
        self.chip_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.chip_frame.pack(fill="x", pady=5)

    def _open_manager(self):
        self.app.popup_manager.open_tag_manager_modal(self.context_type)

    def render(self, tags: List[str]):
        """Renders the list of tags as flow chips."""
        # Clear old
        for w in self.chip_frame.winfo_children(): w.destroy()
        
        sorted_tags = sorted(list(set(tags))) # Dedup and sort
        
        if not sorted_tags:
            ctk.CTkLabel(self.chip_frame, text="No tags", text_color=COLORS["text_sub"], font=FONT_SMALL).pack(anchor="w")
            return
        
        # Flow Layout Logic
        current_row = ctk.CTkFrame(self.chip_frame, fg_color="transparent")
        current_row.pack(fill="x", pady=2, anchor="w")
        current_x = 0
        MAX_W = 220 # Approximate width breakpoint for sidebar
        
        for tag in sorted_tags[:15]: # Soft limit to prevent overflow
            is_sys = is_system_tag(tag)
            bg = COLORS["card_bg"] if is_sys else COLORS["btn_positive"]
            fg = COLORS["text_main"] if is_sys else COLORS["text_on_positive"]
            text = format_tag_text(tag)
            
            # Rough width estimation (char width * 8px + padding)
            est_w = len(text) * 8 + 20
            
            if current_x + est_w > MAX_W:
                current_row = ctk.CTkFrame(self.chip_frame, fg_color="transparent")
                current_row.pack(fill="x", pady=2, anchor="w")
                current_x = 0
            
            ctk.CTkLabel(
                current_row, text=text, font=("Segoe UI", 10, "bold"),
                fg_color=bg, text_color=fg, corner_radius=6, padx=8, pady=2
            ).pack(side="left", padx=2)
            current_x += est_w + 4


class StatsBlock:
    """
    Renders a grid of Key-Value pairs for metadata (e.g. Format, Date, Counts).
    """
    def __init__(self, parent: ctk.CTkFrame, keys: List[str]):
        self.container = ctk.CTkFrame(parent, fg_color="transparent")
        self.container.pack(fill="x", padx=20, pady=5)
        
        self.labels = {}
        
        for key in keys:
            wrapper = ctk.CTkFrame(self.container, fg_color="transparent")
            wrapper.pack(fill="x", pady=(5, 8), padx=5)
            
            # Key Label (Small, Sub text)
            ctk.CTkLabel(wrapper, text=key, font=FONT_SMALL, text_color=COLORS["text_sub"]).pack(anchor="w")
            
            # Value Label (Normal, Main text)
            val_lbl = ctk.CTkLabel(wrapper, text="--", font=FONT_NORMAL, text_color=COLORS["text_main"])
            val_lbl.pack(anchor="w")
            
            self.labels[key] = val_lbl

    def update(self, data: Dict[str, Any]):
        """Updates the value labels based on the provided dictionary."""
        for key, val_lbl in self.labels.items():
            if key in data:
                val_lbl.configure(text=str(data[key]))
            else:
                val_lbl.configure(text="--")


class LinkStatusSection:
    """
    Specific to Pack View. 
    Shows either a 'Make Collection' button OR 'Part of Collection: Name' label.
    """
    def __init__(self, parent: ctk.CTkFrame, app):
        self.app = app
        
        # Header
        self.header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(20, 10))
        ctk.CTkLabel(self.header_frame, text=f"Collection {ICON_FOLDER}", font=FONT_TITLE, text_color=COLORS["text_sub"]).pack(side="left")
        ctk.CTkFrame(self.header_frame, height=2, fg_color=COLORS["card_border"]).pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        self.content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.content_frame.pack(fill="x", padx=0, pady=0)
        
        # Button
        self.create_btn = ctk.CTkButton(
            self.content_frame, text=f"{ICON_ADD} Make Collection", 
            command=self.app.popup_manager.open_link_pack_modal,
            height=32, font=FONT_NORMAL, corner_radius=8,
            fg_color=COLORS["btn_primary"], hover_color=COLORS["btn_primary_hover"], text_color=COLORS["text_on_primary"]
        )
        self.create_btn.pack(fill="x", padx=30, pady=(5, 10))
        
        # Status Label (Hidden initially)
        self.status_lbl = ctk.CTkLabel(self.content_frame, text="", font=FONT_SMALL, text_color=COLORS["text_sub"])

    def update(self, pack_data: Dict[str, Any]):
        links = self.app.logic.get_linked_pack_collection(pack_data)
        
        if len(links) > 1:
            # It is inside a collection
            coll_name = pack_data.get('custom_collection_name') or f"{links[0]['name']} Collection"
            self.create_btn.pack_forget()
            
            self.status_lbl.configure(text=f"Part of: {coll_name}")
            self.status_lbl.pack(pady=10)
        else:
            # Standalone pack
            self.status_lbl.pack_forget()
            self.create_btn.pack(fill="x", padx=30, pady=(5, 10))