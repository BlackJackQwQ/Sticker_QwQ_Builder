import customtkinter as ctk
from typing import List, Dict, Any, Optional

from UI.ViewUtils import COLORS, is_system_tag, format_tag_text, Tooltip
from UI.DetailPanel.Elements import create_section_header
from Resources.Icons import (
    FONT_TITLE, FONT_SMALL, FONT_NORMAL,
    ICON_ADD, ICON_REMOVE, ICON_FOLDER,
    ICON_TAG, ICON_SETTINGS, ICON_INFO
)

class TagSection:
    """
    Manages the 'Tags' header, 'Edit' button, and the flow-layout chip rendering.
    Includes 'Show More / Show Less' logic for overflow using clickable labels.
    """
    def __init__(self, parent: ctk.CTkFrame, app, context_type: str):
        self.app = app
        self.context_type = context_type # "pack", "collection", or "sticker"
        self.is_expanded = False # State for tracking Show More/Less
        self.current_tags = []
        
        # Container (Holds Header + Button + Chips)
        self.container = ctk.CTkFrame(parent, fg_color="transparent")
        self.container.pack(fill="x", padx=0, pady=0)
        
        # 1. Standard Header with Icon
        create_section_header(self.container, f"{ICON_TAG} Tags")
        
        # 2. Edit Button (Full Width, below header)
        self.edit_btn = ctk.CTkButton(
            self.container, 
            text=f"{ICON_SETTINGS} Edit Tags", 
            command=self._open_manager,
            height=32, 
            font=FONT_NORMAL, 
            corner_radius=8,
            fg_color=COLORS["card_bg"], 
            hover_color=COLORS["card_border"], 
            text_color=COLORS["text_main"]
        )
        self.edit_btn.pack(fill="x", padx=30, pady=(0, 10))
        self.tooltip_edit = Tooltip(self.edit_btn, "Manage tags for this item")
        
        # 3. List Container (Chips go here)
        self.chip_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.chip_frame.pack(fill="x", pady=5, padx=15)

    def _open_manager(self):
        self.app.popup_manager.open_tag_manager_modal(self.context_type)

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.render(self.current_tags)

    def render(self, tags: List[str]):
        """Renders the list of tags as flow chips with smart overflow logic."""
        self.current_tags = tags
        
        # Clear old widgets
        for w in self.chip_frame.winfo_children(): w.destroy()
        
        sorted_tags = sorted(list(set(tags))) # Dedup and sort
        
        if not sorted_tags:
            ctk.CTkLabel(self.chip_frame, text="No tags", text_color=COLORS["text_sub"], font=FONT_SMALL).pack(anchor="w")
            return
        
        # --- 1. PRE-CALCULATE LINES ---
        MAX_W = 220
        lines = [[]]
        current_w = 0
        
        # Helper to estimate width (char width * 8px + padding)
        def get_tag_width(t_text):
            return len(t_text) * 8 + 20
            
        formatted_tags = []
        for t in sorted_tags:
            formatted_tags.append({
                "raw": t,
                "text": format_tag_text(t),
                "sys": is_system_tag(t),
                "width": get_tag_width(format_tag_text(t))
            })

        # Organize tags into lines based on width
        for tag_obj in formatted_tags:
            w = tag_obj["width"]
            if current_w + w > MAX_W and len(lines[-1]) > 0:
                 lines.append([])
                 current_w = 0
            
            lines[-1].append(tag_obj)
            current_w += w + 4 # 4px padding/gap

        # --- 2. RENDER HELPERS ---
        
        def make_action_chip(text, cmd, parent):
            """Creates a clickable label that looks like a tag."""
            lbl = ctk.CTkLabel(
                parent, text=text, font=("Segoe UI", 10, "bold"),
                fg_color=COLORS["card_border"], text_color=COLORS["text_main"],
                corner_radius=6, padx=8, pady=2, cursor="hand2"
            )
            lbl.pack(side="left", padx=2)
            
            # Interactions
            lbl.bind("<Button-1>", lambda e: cmd())
            lbl.bind("<Enter>", lambda e: lbl.configure(fg_color=COLORS["card_hover"]))
            lbl.bind("<Leave>", lambda e: lbl.configure(fg_color=COLORS["card_border"]))
            
            # Dynamic Tooltip
            tip_text = "Expand tag list" if text == "Show More" else "Collapse tag list"
            Tooltip(lbl, tip_text)

        def make_tag(tag_obj, parent):
            bg = COLORS["card_bg"] if tag_obj["sys"] else COLORS["btn_positive"]
            fg = COLORS["text_main"] if tag_obj["sys"] else COLORS["text_on_positive"]
            ctk.CTkLabel(
                parent, text=tag_obj["text"], font=("Segoe UI", 10, "bold"),
                fg_color=bg, text_color=fg, corner_radius=6, padx=8, pady=2
            ).pack(side="left", padx=2)

        # --- 3. RENDER LOGIC ---
        total_lines = len(lines)
        limit = 3
        
        # Case A: Fits in limit -> Render All, No Buttons
        if total_lines <= limit:
            for line in lines:
                row = ctk.CTkFrame(self.chip_frame, fg_color="transparent")
                row.pack(fill="x", pady=2, anchor="w")
                for tag in line: make_tag(tag, row)
                
        # Case B: Expanded -> Render All + Show Less
        elif self.is_expanded:
            for i, line in enumerate(lines):
                row = ctk.CTkFrame(self.chip_frame, fg_color="transparent")
                row.pack(fill="x", pady=2, anchor="w")
                for tag in line: make_tag(tag, row)
                
                # Append 'Show Less' at the end of last line (if space) or new line
                if i == len(lines) - 1:
                     lw = sum(t["width"] + 4 for t in line)
                     btn_w = 60
                     if lw + btn_w > MAX_W:
                         # New row for button
                         btn_row = ctk.CTkFrame(self.chip_frame, fg_color="transparent")
                         btn_row.pack(fill="x", pady=2, anchor="w")
                         make_action_chip("Show Less", self.toggle_expand, btn_row)
                     else:
                         make_action_chip("Show Less", self.toggle_expand, row)

        # Case C: Collapsed -> Render limit-1 lines, then smart render last line with button
        else:
            # Render first 2 lines normally
            for i in range(limit - 1):
                row = ctk.CTkFrame(self.chip_frame, fg_color="transparent")
                row.pack(fill="x", pady=2, anchor="w")
                for tag in lines[i]: make_tag(tag, row)
            
            # Render 3rd line with cutoff for button
            row = ctk.CTkFrame(self.chip_frame, fg_color="transparent")
            row.pack(fill="x", pady=2, anchor="w")
            
            line_3 = lines[limit - 1]
            current_w = 0
            btn_w = 60 # approx width for "Show More"
            
            for tag in line_3:
                # Can we fit this tag AND the button?
                if current_w + tag["width"] + 4 + btn_w <= MAX_W:
                    make_tag(tag, row)
                    current_w += tag["width"] + 4
                else:
                    break # Stop adding tags, place button
            
            make_action_chip("Show More", self.toggle_expand, row)


class StatsBlock:
    """
    Renders a grid of Key-Value pairs for metadata (e.g. Format, Date, Counts).
    """
    def __init__(self, parent: ctk.CTkFrame, keys: List[str]):
        # Container
        self.container = ctk.CTkFrame(parent, fg_color="transparent")
        self.container.pack(fill="x", padx=0, pady=5)
        
        # Header with Icon
        create_section_header(self.container, f"{ICON_INFO} Info")

        # Content Box
        self.content_box = ctk.CTkFrame(self.container, fg_color="transparent")
        self.content_box.pack(fill="x", padx=20, pady=5)
        
        self.labels = {}
        
        for key in keys:
            wrapper = ctk.CTkFrame(self.content_box, fg_color="transparent")
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
        
        # Main Container (Allows entire section to be hidden)
        self.container = ctk.CTkFrame(parent, fg_color="transparent")
        self.container.pack(fill="x", padx=0, pady=0)
        
        # Standardized Header
        create_section_header(self.container, f"{ICON_FOLDER} Collection")
        
        self.content_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.content_frame.pack(fill="x", padx=0, pady=0)
        
        # Button
        self.create_btn = ctk.CTkButton(
            self.content_frame, text=f"{ICON_ADD} Make Collection", 
            command=self.app.popup_manager.open_link_pack_modal,
            height=32, font=FONT_NORMAL, corner_radius=8,
            fg_color=COLORS["btn_primary"], hover_color=COLORS["btn_primary_hover"], text_color=COLORS["text_on_primary"]
        )
        self.create_btn.pack(fill="x", padx=30, pady=(5, 10))
        self.tooltip_create = Tooltip(self.create_btn, "Create a collection from this pack")
        
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