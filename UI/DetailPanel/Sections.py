import customtkinter as ctk
import tkinter.font as tkfont
from typing import List, Dict, Any, Optional

from UI.ViewUtils import COLORS, is_system_tag, format_tag_text
from Resources.Icons import (
    FONT_TITLE, FONT_SMALL, FONT_NORMAL,
    ICON_ADD, ICON_REMOVE, ICON_FOLDER, ICON_TAG, ICON_EDIT, ICON_INFO
)

class TagSection:
    """
    Manages the 'Tags' header, 'Edit Tag' button, and the flow-layout chip rendering.
    Features:
    - Precise text measurement for layout.
    - 'Show More' / 'Show Less' toggle for long lists.
    - Robust overflow protection.
    """
    def __init__(self, parent: ctk.CTkFrame, app, context_type: str):
        self.app = app
        self.context_type = context_type # "pack", "collection", or "sticker"
        
        # State for Show More/Less
        self.expanded = False
        
        # Container
        self.container = ctk.CTkFrame(parent, fg_color="transparent")
        self.container.pack(fill="x", padx=15, pady=10)
        
        # Header Row (Title + Line)
        header = ctk.CTkFrame(self.container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        
        # Icon + Title
        ctk.CTkLabel(header, text=f"{ICON_TAG} Tags", font=FONT_TITLE, text_color=COLORS["text_main"]).pack(side="left")
        
        # Line
        ctk.CTkFrame(header, height=2, fg_color=COLORS["card_border"]).pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # "Edit Tag" Button - Big & Centered
        ctk.CTkButton(
            self.container, 
            text=f"{ICON_EDIT} Edit Tags", 
            command=self._open_manager,
            height=32, 
            font=FONT_NORMAL, 
            corner_radius=8,
            fg_color=COLORS["card_bg"], 
            hover_color=COLORS["card_border"], 
            text_color=COLORS["text_main"]
        ).pack(fill="x", padx=30, pady=(0, 10))
        
        # List Container (Chips go here)
        self.chip_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.chip_frame.pack(fill="x", pady=5)

    def _open_manager(self):
        self.app.popup_manager.open_tag_manager_modal(self.context_type)

    def _toggle_expand(self, tags):
        self.expanded = not self.expanded
        self.render(tags)

    def render(self, tags: List[str]):
        """Renders the list of tags as flow chips with robust measurement and 3-line limit."""
        # Clear old widgets
        for w in self.chip_frame.winfo_children(): w.destroy()
        
        sorted_tags = sorted(list(set(tags))) # Dedup and sort
        
        if not sorted_tags:
            ctk.CTkLabel(self.chip_frame, text="No tags", text_color=COLORS["text_sub"], font=FONT_SMALL).pack(anchor="w")
            return
        
        # --- MEASUREMENT SETUP ---
        # Use a generic font family fallback if Segoe UI isn't available, but try Segoe UI first
        chip_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        
        # Layout Constants
        MAX_W = 190   # Conservative width to prevent horizontal scroll (Sidebar ~250px)
        PAD_X = 16    # Chip padding (8px * 2)
        GAP_X = 4     # Gap between chips
        ROW_H = 28    # Row height
        MAX_LINES = 3 # Hard limit for collapsed state
        
        # 1. GENERATE ALL LINES (Simulation)
        lines = [[]]
        current_w = 0
        
        for tag in sorted_tags:
            text = format_tag_text(tag)
            
            # Truncate super long tags to avoid single-tag overflow
            if len(text) > 25: 
                text = text[:22] + "..."
                
            w = chip_font.measure(text) + PAD_X
            
            # Safety cap for very wide text even after char truncation
            if w > MAX_W: w = MAX_W 
            
            # Wrap to new line if needed
            # We check if (current_w + w) exceeds MAX_W. 
            # We also ensure lines[-1] is not empty (so we don't wrap the very first item endlessly)
            if current_w + w > MAX_W and len(lines[-1]) > 0:
                lines.append([])
                current_w = 0
            
            lines[-1].append({"text": text, "orig": tag, "width": w})
            current_w += w + GAP_X

        # 2. APPLY "SHOW MORE" / "SHOW LESS" LOGIC
        
        def calc_line_width(item_list):
            width = 0
            for it in item_list:
                width += it["width"] + GAP_X
            return width - GAP_X if width > 0 else 0

        # COLLAPSED MODE
        if not self.expanded and len(lines) > MAX_LINES:
            # We have more lines than allowed
            total_items_count = len(sorted_tags)
            
            # Keep only the first MAX_LINES
            lines = lines[:MAX_LINES]
            last_line = lines[-1]
            
            # Create the button placeholder
            # We don't know the exact count yet, estimation loop needed
            # But roughly:
            visible_so_far = sum(len(l) for l in lines)
            remaining = total_items_count - visible_so_far # Initial estimate
            
            btn_txt = f"Show More" # Base text
            btn_w = chip_font.measure(btn_txt + " (99)") + PAD_X # Measure with margin
            
            # Remove items from the last line until the button fits
            while last_line and (calc_line_width(last_line) + btn_w + GAP_X > MAX_W):
                popped = last_line.pop()
                visible_so_far -= 1
            
            # Recalculate remaining based on what's actually left
            visible_final = sum(len(l) for l in lines)
            remaining_final = total_items_count - visible_final
            
            # Add Button
            lines[-1].append({
                "is_button": True, 
                "text": f"Show More ({remaining_final})", 
                "cmd": lambda: self._toggle_expand(sorted_tags),
                "width": btn_w
            })

        # EXPANDED MODE
        elif self.expanded:
            # Check if we need to append "Show Less"
            # It goes at the very end.
            btn_txt = "Show Less"
            btn_w = chip_font.measure(btn_txt) + PAD_X
            
            last_line = lines[-1]
            if calc_line_width(last_line) + btn_w + GAP_X > MAX_W:
                lines.append([]) # New line for button
            
            lines[-1].append({
                "is_button": True, 
                "text": btn_txt, 
                "cmd": lambda: self._toggle_expand(sorted_tags),
                "width": btn_w
            })

        # 3. RENDER FINAL LINES
        for line_items in lines:
            row = ctk.CTkFrame(self.chip_frame, fg_color="transparent", height=ROW_H)
            row.pack(fill="x", pady=2, anchor="w")
            
            for item in line_items:
                if item.get("is_button"):
                    # Render Button
                    ctk.CTkButton(
                        row, text=item["text"], 
                        width=item["width"], 
                        height=20,
                        font=("Segoe UI", 10, "bold"),
                        fg_color=COLORS["card_border"], 
                        text_color=COLORS["text_main"],
                        hover_color=COLORS["card_hover"],
                        command=item["cmd"]
                    ).pack(side="left", padx=(0, GAP_X))
                else:
                    # Render Tag Label
                    orig_tag = item["orig"]
                    disp_text = item["text"]
                    
                    is_sys = is_system_tag(orig_tag)
                    bg = COLORS["card_bg"] if is_sys else COLORS["btn_positive"]
                    fg = COLORS["text_main"] if is_sys else COLORS["text_on_positive"]
                    
                    ctk.CTkLabel(
                        row, text=disp_text, font=("Segoe UI", 10, "bold"),
                        fg_color=bg, text_color=fg, corner_radius=6, padx=8, pady=2
                    ).pack(side="left", padx=(0, GAP_X))


class StatsBlock:
    """
    Renders a grid of Key-Value pairs for metadata (e.g. Format, Date, Counts).
    """
    def __init__(self, parent: ctk.CTkFrame, keys: List[str]):
        # Container
        self.main_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.main_container.pack(fill="x", padx=15, pady=10)

        # 1. Header Row
        header = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(header, text=f"{ICON_INFO} Info", font=FONT_TITLE, text_color=COLORS["text_main"]).pack(side="left")
        ctk.CTkFrame(header, height=2, fg_color=COLORS["card_border"]).pack(side="left", fill="x", expand=True, padx=(10, 0))

        # 2. Content Container
        self.content_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_container.pack(fill="x", padx=5)
        
        self.labels = {}
        
        for key in keys:
            wrapper = ctk.CTkFrame(self.content_container, fg_color="transparent")
            wrapper.pack(fill="x", pady=(2, 5))
            
            # Key Label
            ctk.CTkLabel(wrapper, text=key, font=FONT_SMALL, text_color=COLORS["text_sub"]).pack(anchor="w")
            
            # Value Label
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
        self.header_frame.pack(fill="x", padx=15, pady=(20, 10))
        
        ctk.CTkLabel(self.header_frame, text=f"{ICON_FOLDER} Collection", font=FONT_TITLE, text_color=COLORS["text_main"]).pack(side="left")
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