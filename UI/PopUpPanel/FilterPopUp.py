import customtkinter as ctk
from typing import Optional, List

from UI.PopUpPanel.Base import BasePopUp
from UI.ViewUtils import COLORS, is_system_tag, format_tag_text, logger
from Resources.Icons import (
    FONT_HEADER, FONT_TITLE, FONT_NORMAL, FONT_SMALL,
    ICON_ADD, ICON_REMOVE, ICON_SEARCH
)

class FilterPopUp(BasePopUp):
    """
    Handles popups related to the Left Filter Panel (Tag Management).
    Methods:
    - open_tag_manager_modal: Edit tags for specific item(s).
    - open_all_tags_modal: View global tag statistics.
    """
    def __init__(self, app):
        super().__init__(app)

    # ==========================================================================
    #   TAG MANAGER (Contextual)
    # ==========================================================================

    def open_tag_manager_modal(self, context_type: str):
        """
        Manages tags for Pack, Collection, or Sticker.
        Replaces the inline search bar in Details panel.
        """
        # 1. Determine Context & Data from the new Controller (self.app.logic)
        target_name = ""
        current_tags = []
        all_known_tags = []
        
        if context_type == "pack":
            if not self.app.logic.current_pack_data: return
            target_name = self.app.logic.current_pack_data.get('name', 'Pack')
            current_tags = self.app.logic.current_pack_data.get('tags', [])
            all_known_tags = self.app.logic.pack_tags_ac
            
        elif context_type == "collection":
            if not self.app.logic.selected_collection_data: return
            target_name = self.app.logic.selected_collection_data.get('name', 'Collection')
            # Collection tags are stored in the root pack's 'custom_collection_tags'
            root = self.app.logic.selected_collection_data['packs'][0]
            current_tags = root.get('custom_collection_tags', [])
            all_known_tags = self.app.logic.pack_tags_ac
            
        elif context_type == "sticker":
            if not self.app.logic.selected_stickers: return
            # Use the first selected sticker for name display
            target_name = self.app.logic.current_sticker_data.get('custom_name', 'Sticker')
            current_tags = self.app.logic.current_sticker_data.get('tags', [])
            all_known_tags = self.app.logic.sticker_tags_ac

        # 2. Window Setup
        win = self._create_base_window(f"Manage Tags: {target_name}", 500, 600)
        
        # Header
        header = ctk.CTkFrame(win, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(header, text="Manage Tags", font=FONT_HEADER, text_color=COLORS["text_main"]).pack(anchor="center")
        ctk.CTkLabel(header, text=target_name, font=FONT_NORMAL, text_color=COLORS["accent"]).pack(anchor="center")

        # ==========================
        # TOP: CURRENT TAGS
        # ==========================
        top_frame = ctk.CTkFrame(win, fg_color=COLORS["bg_sidebar"], corner_radius=10)
        top_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        ctk.CTkLabel(top_frame, text="Current Tags", font=FONT_TITLE, text_color=COLORS["text_sub"]).pack(pady=(10,5), padx=10, anchor="w")
        
        current_scroll = ctk.CTkScrollableFrame(top_frame, fg_color="transparent")
        current_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        def refresh_current_list():
            for w in current_scroll.winfo_children(): w.destroy()
            
            # Re-fetch fresh list from logic
            fresh_tags = []
            if context_type == "pack": 
                fresh_tags = self.app.logic.current_pack_data.get('tags', [])
            elif context_type == "collection": 
                r = self.app.logic.selected_collection_data['packs'][0]
                fresh_tags = r.get('custom_collection_tags', [])
            elif context_type == "sticker":
                # For stickers, we check the main selection. 
                # (Logic.add_tag_manual handles batch updates, but we display the primary one here)
                if self.app.logic.selected_stickers:
                    fresh_tags = self.app.logic.current_sticker_data.get('tags', [])
            
            if not fresh_tags:
                ctk.CTkLabel(current_scroll, text="No tags assigned.", text_color=COLORS["text_sub"]).pack(pady=20)
                return

            for tag in fresh_tags:
                row = ctk.CTkFrame(current_scroll, fg_color=COLORS["card_bg"], corner_radius=6)
                row.pack(fill="x", pady=3)
                
                disp = format_tag_text(tag)
                is_sys = is_system_tag(tag)
                col = COLORS["text_sub"] if is_sys else COLORS["text_main"]
                
                ctk.CTkLabel(row, text=disp, font=FONT_NORMAL, text_color=col).pack(side="left", padx=10, pady=5)
                
                if not is_sys:
                    # UPDATED: Added "Remove" text and increased width
                    ctk.CTkButton(
                        row, text=f"{ICON_REMOVE} Remove", width=80, height=24,
                        fg_color=COLORS["btn_negative"], hover_color=COLORS["btn_negative_hover"], text_color=COLORS["text_on_negative"],
                        # Call logic to remove, then refresh both lists in this modal
                        command=lambda t=tag: [
                            self.app.logic.confirm_remove_tag(context_type, t), 
                            refresh_current_list(), 
                            refresh_add_list(search_entry.get())
                        ]
                    ).pack(side="right", padx=10)

        # ==========================
        # BOTTOM: ADD TAGS
        # ==========================
        bottom_frame = ctk.CTkFrame(win, fg_color="transparent")
        bottom_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        ctk.CTkLabel(bottom_frame, text="Add Tags", font=FONT_TITLE, text_color=COLORS["accent"]).pack(pady=(10, 5), anchor="w")
        
        # Search/Add Bar
        search_fr = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        search_fr.pack(fill="x", pady=(0, 5))
        
        search_entry = ctk.CTkEntry(search_fr, placeholder_text=f"{ICON_SEARCH} Search or create tag...", height=30, fg_color=COLORS["entry_bg"], text_color=COLORS["entry_text"])
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        def add_typed_tag():
            txt = search_entry.get().strip()
            if txt:
                # Use new manual add method in Logic
                if hasattr(self.app.logic, 'add_tag_manual'):
                     self.app.logic.add_tag_manual(context_type, txt)
                else:
                    logger.warning("add_tag_manual not found in Logic")
                
                search_entry.delete(0, "end")
                refresh_current_list()
                refresh_add_list()

        ctk.CTkButton(
            search_fr, text=f"{ICON_ADD} Add", width=60, height=30,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["text_on_accent"],
            command=add_typed_tag
        ).pack(side="right")
        
        # List of Available Tags
        add_scroll = ctk.CTkScrollableFrame(bottom_frame, fg_color="transparent", border_width=1, border_color=COLORS["card_border"])
        add_scroll.pack(fill="both", expand=True)

        def refresh_add_list(query=""):
            for w in add_scroll.winfo_children(): w.destroy()
            query = query.lower()
            
            # Re-read current set to exclude already added tags
            current_set = set()
            if context_type == "pack": 
                current_set = set(self.app.logic.current_pack_data.get('tags', []))
            elif context_type == "collection":
                r = self.app.logic.selected_collection_data['packs'][0]
                current_set = set(r.get('custom_collection_tags', []))
            elif context_type == "sticker":
                if self.app.logic.current_sticker_data:
                    current_set = set(self.app.logic.current_sticker_data.get('tags', []))

            # Filter Available
            candidates = [t for t in all_known_tags if not is_system_tag(t) and t not in current_set]
            candidates.sort()
            
            count = 0
            for tag in candidates:
                if query and query not in tag.lower(): continue
                
                row = ctk.CTkFrame(add_scroll, fg_color=COLORS["card_bg"], corner_radius=6)
                row.pack(fill="x", pady=2)
                
                ctk.CTkLabel(row, text=tag, font=FONT_NORMAL, text_color=COLORS["text_main"]).pack(side="left", padx=10, pady=5)
                
                # UPDATED: Added "Add" text and increased width
                ctk.CTkButton(
                    row, text=f"{ICON_ADD} Add", width=70, height=24,
                    fg_color=COLORS["btn_positive"], hover_color=COLORS["btn_positive_hover"], text_color=COLORS["text_on_positive"],
                    command=lambda t=tag: [
                        getattr(self.app.logic, 'add_tag_manual', lambda a,b: None)(context_type, t), 
                        refresh_current_list(), 
                        refresh_add_list(search_entry.get())
                    ]
                ).pack(side="right", padx=10)
                
                count += 1
                if count > 50 and not query: break

        search_entry.bind("<KeyRelease>", lambda e: refresh_add_list(search_entry.get()))
        search_entry.bind("<Return>", lambda e: add_typed_tag())

        refresh_current_list()
        refresh_add_list()

    # ==========================================================================
    #   GLOBAL TAG VIEW
    # ==========================================================================

    def open_all_tags_modal(self):
        win = self._create_base_window("All Tags", 480, 680)
        
        ctrl = ctk.CTkFrame(win, fg_color=COLORS["transparent"])
        ctrl.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(ctrl, text="Manage Tags", font=FONT_HEADER, text_color=COLORS["text_main"]).pack(anchor="center", pady=(0, 10))

        search_var = ctk.StringVar()
        ctk.CTkEntry(
            ctrl, textvariable=search_var, placeholder_text=f"{ICON_SEARCH} Search...", height=32, 
            fg_color=COLORS["entry_bg"], text_color=COLORS["entry_text"]
        ).pack(fill="x", pady=(0, 10))
        
        filter_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        filter_row.pack(fill="x")
        
        sort_var = ctk.StringVar(value="Frequency")
        ctk.CTkOptionMenu(filter_row, variable=sort_var, values=["Frequency", "A-Z"], width=110, fg_color=COLORS["dropdown_bg"]).pack(side="left")
        
        show_sys = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(filter_row, text="Show System", variable=show_sys, text_color=COLORS["text_sub"], progress_color=COLORS["accent"]).pack(side="right")
        
        scroll = ctk.CTkScrollableFrame(win, fg_color=COLORS["transparent"])
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        def rebuild(*args):
            if not win.winfo_exists(): return
            for w in scroll.winfo_children(): w.destroy()
            
            # Delegate to Controller -> Filters.get_tag_usage()
            usage = self.app.logic.get_tag_usage()
            q = search_var.get().lower()
            
            final = []
            for tag, count in usage.items():
                is_sys = is_system_tag(tag)
                if not show_sys.get() and (is_sys or tag in ["Static", "Animated", "Local"]): continue
                if q and q not in tag.lower(): continue
                final.append((tag, count))

            if sort_var.get() == "Frequency": final.sort(key=lambda x: x[1], reverse=True)
            else: final.sort(key=lambda x: x[0].lower())

            for tag, count in final:
                row = ctk.CTkFrame(scroll, fg_color=COLORS["card_bg"])
                row.pack(fill="x", pady=3)
                
                txt_col = COLORS["text_sub"] if is_system_tag(tag) else COLORS["text_main"]
                ctk.CTkLabel(row, text=f"{format_tag_text(tag)} ({count})", font=("Segoe UI", 12, "bold"), text_color=txt_col).pack(side="left", padx=10, pady=8)
                
                btns = ctk.CTkFrame(row, fg_color="transparent")
                btns.pack(side="right", padx=5)
                
                # Filter Include
                ctk.CTkButton(
                    btns, text=f"{ICON_ADD}", width=28, fg_color=COLORS["btn_positive"], 
                    command=lambda t=tag: [self.app.logic.add_filter_tag_direct(t, "Include"), win.destroy()]
                ).pack(side="left", padx=2)
                
                # Filter Exclude
                ctk.CTkButton(
                    btns, text="-", width=28, fg_color=COLORS["btn_negative"], 
                    command=lambda t=tag: [self.app.logic.add_filter_tag_direct(t, "Exclude"), win.destroy()]
                ).pack(side="left", padx=2)

        rebuild()
        search_var.trace_add("write", rebuild)
        sort_var.trace_add("write", rebuild)
        show_sys.trace_add("write", rebuild)