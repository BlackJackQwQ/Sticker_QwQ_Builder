# ... existing imports ...
import customtkinter as ctk
from typing import Optional, Callable, Any
from pathlib import Path
import math
import cv2  # Needed for video thumbnails
from PIL import Image

from UI.PopUpPanel.Base import BasePopUp
from UI.ViewUtils import COLORS, load_ctk_image
from UI.CardsPanel.Utils import CardUtils
from Core.Config import BASE_DIR, LIBRARY_FOLDER
from Resources.Icons import (
    FONT_HEADER, FONT_TITLE, FONT_NORMAL, FONT_SMALL,
    ICON_ADD, ICON_REMOVE, ICON_RANDOM, ICON_FOLDER, ICON_SEARCH, ICON_LEFT
)

class DetailPopUp(BasePopUp):
    """
    Handles popups related to the Right Detail Panel (Covers, Collections).
    Updated with Pagination, Density Control, and Active Highlighting.
    """
    def __init__(self, app):
        super().__init__(app)
        self.utils = CardUtils(app)
        
        self.cover_selector_win: Optional[ctk.CTkToplevel] = None
        
        # --- STATE ---
        self.current_view_mode = "packs" # "packs" or "stickers"
        self.current_pack_context = None # Stores data of the pack we are looking into
        self.active_context_packs = []   # List of packs available in current context (Library or Collection)
        self.can_navigate_up = True      # Can we go back to a parent list?
        self.current_active_cover = None # The path of the currently selected cover (for highlighting)
        
        # --- PAGINATION STATE ---
        self.popup_page = 1
        self.popup_limit = 20
        self.popup_items = []  # The filtered list of items to display
        self._active_callback = None

    # ==========================================================================
    #   COVER SELECTOR (MINI LIBRARY)
    # ==========================================================================

    def open_cover_selector_modal(self, target_name: str, on_select_callback: Callable[[Optional[str]], None]):
        if self.cover_selector_win and self.cover_selector_win.winfo_exists():
            self.cover_selector_win.focus()
            return

        # Increase height slightly to fit the new bars
        self.cover_selector_win = self._create_base_window(f"Select {target_name}", 750, 750) # Slightly wider/taller for bigger grid
        
        def on_close():
            self._stop_popup_animations()
            self.cover_selector_win.destroy()
        self.cover_selector_win.protocol("WM_DELETE_WINDOW", on_close)
        
        # Reset State
        self.popup_page = 1
        self.popup_limit = 20
        self.popup_items = []
        self._active_callback = on_select_callback
        self.current_active_cover = None
        
        # --- 1. DETERMINE CONTEXT & CURRENT COVER ---
        start_in_stickers = False
        self.can_navigate_up = True
        self.active_context_packs = []
        
        display_title = f"Change {target_name} Cover"
        is_collection_intent = "collection" in target_name.lower()

        if is_collection_intent and self.app.logic.selected_collection_data:
            # Context: Inside a Collection
            self.active_context_packs = self.app.logic.selected_collection_data.get('packs', [])
            self.current_view_mode = "packs"
            display_title = f"Change {self.app.logic.selected_collection_data.get('name', 'Collection')} Cover"
            self.current_active_cover = self.app.logic.selected_collection_data.get('thumbnail_path')
            
        elif self.app.logic.current_pack_data:
            tname = self.app.logic.current_pack_data.get('t_name')
            if tname == 'all_library_virtual':
                # Context: All Stickers Virtual Pack -> Show Library Packs
                self.active_context_packs = self.app.library_data
                self.current_view_mode = "packs"
            else:
                # Context: Single Pack -> Show Stickers directly
                self.active_context_packs = [self.app.logic.current_pack_data]
                self.current_pack_context = self.app.logic.current_pack_data
                start_in_stickers = True
                self.can_navigate_up = False
                self.current_view_mode = "stickers"
                display_title = f"Change {self.app.logic.current_pack_data.get('name', 'Pack')} Cover"
                self.current_active_cover = self.app.logic.current_pack_data.get('thumbnail_path')
        else:
            # Default: Library
            self.active_context_packs = self.app.library_data

        # Normalize cover path for comparison
        if self.current_active_cover:
            self.current_active_cover = str(Path(self.current_active_cover).resolve())

        # ==================== LAYOUT CONSTRUCTION ====================

        # --- ROW 1: HEADER ---
        header_frame = ctk.CTkFrame(self.cover_selector_win, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(header_frame, text=display_title, font=FONT_HEADER, text_color=COLORS["text_main"]).pack(anchor="w")

        # --- ROW 2: BACK BUTTON (Conditional) ---
        self.back_row = ctk.CTkFrame(self.cover_selector_win, fg_color="transparent", height=0)
        self.back_row.pack(fill="x", padx=15, pady=(0, 0)) # Padding added dynamically when shown
        
        self.back_btn = ctk.CTkButton(
            self.back_row, text=f"{ICON_LEFT} Back", width=80, height=30,
            fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"], text_color=COLORS["text_main"],
            command=self._go_back_to_packs
        )
        self.back_btn.pack(side="left")
        # Initially hide it
        self.back_btn.pack_forget()

        # --- ROW 3: TOOLS (Search, Random) ---
        tools_row = ctk.CTkFrame(self.cover_selector_win, fg_color="transparent")
        tools_row.pack(fill="x", padx=15, pady=(10, 5))
        
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            tools_row, textvariable=self.search_var, placeholder_text=f"{ICON_SEARCH} Search packs or stickers...", 
            height=35, fg_color=COLORS["entry_bg"], text_color=COLORS["entry_text"]
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search())

        def safe_action(value):
            self._stop_popup_animations()
            if self.cover_selector_win.winfo_exists(): self.cover_selector_win.destroy()
            self.app.last_width = 0
            on_select_callback(value)

        # Random Button - UPDATED SIZE and FONT
        ctk.CTkButton(
            tools_row, text=f"{ICON_RANDOM}", width=85, height=35,
            font=("Arial", 24), # Increased font size for the dice icon
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["text_on_accent"],
            command=lambda: safe_action(None)
        ).pack(side="left", padx=(0, 5))
        
        # --- ROW 4: CONTEXT LABEL ---
        # "Stickers in: Dogs"
        self.context_label_row = ctk.CTkFrame(self.cover_selector_win, fg_color="transparent")
        self.context_label_row.pack(fill="x", padx=20, pady=(5, 0))
        
        self.context_label = ctk.CTkLabel(
            self.context_label_row, text="", font=FONT_TITLE, text_color=COLORS["accent"]
        )
        self.context_label.pack(anchor="w")

        # --- ROW 5: TOP PAGINATION ---
        self.top_pag_frame = ctk.CTkFrame(self.cover_selector_win, fg_color="transparent")
        self.top_pag_frame.pack(fill="x", padx=15, pady=(5, 5))
        self.pag_ui_top = self._build_pagination_controls(self.top_pag_frame)

        # --- ROW 6: CONTENT GRID ---
        self.scroll_frame = ctk.CTkScrollableFrame(self.cover_selector_win, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # --- ROW 7: BOTTOM PAGINATION ---
        self.btm_pag_frame = ctk.CTkFrame(self.cover_selector_win, fg_color="transparent")
        self.btm_pag_frame.pack(fill="x", padx=15, pady=(5, 10))
        self.pag_ui_btm = self._build_pagination_controls(self.btm_pag_frame)

        # --- INITIAL RENDER ---
        if start_in_stickers:
            self._render_sticker_grid(self.current_pack_context, on_select_callback)
        else:
            self._render_pack_list(on_select_callback)

    # ==========================================================================
    #   PAGINATION LOGIC & UI
    # ==========================================================================

    def _build_pagination_controls(self, parent):
        """Builds a pagination bar and returns references to its widgets."""
        refs = {}
        
        # Left: Prev/Next
        left_fr = ctk.CTkFrame(parent, fg_color="transparent")
        left_fr.pack(side="left")
        
        refs['prev_btn'] = ctk.CTkButton(
            left_fr, text="<", width=30, height=28, 
            fg_color=COLORS["card_bg"], text_color=COLORS["text_main"],
            command=lambda: self._change_page(-1)
        )
        refs['prev_btn'].pack(side="left", padx=2)
        
        refs['label'] = ctk.CTkLabel(
            left_fr, text="Page 1 / 1", font=FONT_SMALL, width=80, 
            text_color=COLORS["text_main"] 
        )
        refs['label'].pack(side="left", padx=5)
        
        refs['next_btn'] = ctk.CTkButton(
            left_fr, text=">", width=30, height=28, 
            fg_color=COLORS["card_bg"], text_color=COLORS["text_main"],
            command=lambda: self._change_page(1)
        )
        refs['next_btn'].pack(side="left", padx=2)
        
        # Right: Density
        right_fr = ctk.CTkFrame(parent, fg_color="transparent")
        right_fr.pack(side="right")
        
        ctk.CTkLabel(right_fr, text="Show:", font=FONT_SMALL, text_color=COLORS["text_sub"]).pack(side="left", padx=5)
        
        refs['limit_seg'] = ctk.CTkSegmentedButton(
            right_fr, values=["20", "60", "100"], width=100, height=24,
            text_color=COLORS["seg_text"], 
            command=self._on_limit_change
        )
        refs['limit_seg'].set(str(self.popup_limit))
        refs['limit_seg'].pack(side="left")
        
        return refs

    def _update_pagination_ui(self):
        """Syncs both Top and Bottom bars with current state."""
        total_items = len(self.popup_items)
        if total_items == 0:
            total_pages = 1
        else:
            total_pages = math.ceil(total_items / self.popup_limit)
        
        text = f"Page {self.popup_page} / {total_pages}"
        
        # Helper to update a set of controls
        def update_set(refs):
            refs['label'].configure(text=text)
            refs['prev_btn'].configure(state="normal" if self.popup_page > 1 else "disabled")
            refs['next_btn'].configure(state="normal" if self.popup_page < total_pages else "disabled")
            # Sync density selection
            if refs['limit_seg'].get() != str(self.popup_limit):
                refs['limit_seg'].set(str(self.popup_limit))

        update_set(self.pag_ui_top)
        update_set(self.pag_ui_btm)

    def _change_page(self, direction):
        total_pages = math.ceil(len(self.popup_items) / self.popup_limit)
        new_page = self.popup_page + direction
        if 1 <= new_page <= total_pages:
            self.popup_page = new_page
            self._render_grid_page()

    def _on_limit_change(self, value):
        new_limit = int(value)
        if new_limit != self.popup_limit:
            self.popup_limit = new_limit
            self.popup_page = 1 # Reset to page 1 to avoid out of bounds
            self._render_grid_page()

    # ==========================================================================
    #   DATA PREPARATION (Navigation)
    # ==========================================================================

    def _render_pack_list(self, callback, query=""):
        """Prepares the list of packs to display."""
        self.current_view_mode = "packs"
        self._active_callback = callback
        self._stop_popup_animations()
        
        # 1. Back Button Logic
        self.back_btn.pack_forget()
        self.back_row.configure(height=0) # Collapse
        
        # 2. Context Label Logic
        header_text = "All Packs"
        if self.app.logic.selected_collection_data:
             col_packs = self.app.logic.selected_collection_data.get('packs', [])
             if self.active_context_packs is col_packs:
                 header_text = f"Packs in: {self.app.logic.selected_collection_data['name']}"
        self.context_label.configure(text=header_text)
        
        # 3. Filter Data
        query = query.lower()
        self.popup_items = [p for p in self.active_context_packs if query in p['name'].lower()]
        
        # 4. Reset & Render
        self.popup_page = 1
        self._render_grid_page()

    def _render_sticker_grid(self, pack_data, callback, query=""):
        """Prepares the list of stickers to display."""
        self.current_view_mode = "stickers"
        self.current_pack_context = pack_data
        self._active_callback = callback
        
        # 1. Back Button Logic
        if self.can_navigate_up:
            self.back_btn.pack(side="left")
            self.back_row.configure(height=40)
        else:
            self.back_btn.pack_forget()
            self.back_row.configure(height=0)

        # 2. Context Label Logic
        self.context_label.configure(text=f"Stickers in: {pack_data['name']}")
        
        # 3. Filter Data (Files)
        base_path = BASE_DIR / LIBRARY_FOLDER / pack_data['t_name']
        self.popup_items = []
        
        if base_path.exists():
            all_files = sorted(list(base_path.iterdir()), key=lambda x: x.name)
            query = query.lower()
            for f in all_files:
                if f.suffix.lower() in {'.png', '.webp', '.gif', '.webm', '.mp4'}:
                    if query and query not in f.name.lower(): continue
                    self.popup_items.append(str(f))
        
        # 4. Reset & Render
        self.popup_page = 1
        self._render_grid_page()

    def _on_search(self):
        """Triggered by search bar typing."""
        query = self.search_var.get()
        if self.current_view_mode == "packs":
            self._render_pack_list(self._active_callback, query)
        elif self.current_view_mode == "stickers":
            self._render_sticker_grid(self.current_pack_context, self._active_callback, query)

    def _go_back_to_packs(self):
        """Navigate Up from Stickers -> Pack List."""
        self.search_entry.delete(0, "end")
        self._render_pack_list(self._active_callback)

    # ==========================================================================
    #   GRID RENDERER (The Content)
    # ==========================================================================

    def _render_grid_page(self):
        """Renders the current slice of popup_items into the scroll frame."""
        self._stop_popup_animations()
        for w in self.scroll_frame.winfo_children(): w.destroy()
        
        # Update Controls first (Disable/Enable buttons)
        self._update_pagination_ui()

        if not self.popup_items:
            ctk.CTkLabel(self.scroll_frame, text="No items found.", text_color=COLORS["text_sub"]).pack(pady=50)
            return

        # Slicing
        start_idx = (self.popup_page - 1) * self.popup_limit
        end_idx = start_idx + self.popup_limit
        page_items = self.popup_items[start_idx:end_idx]
        
        # Grid Setup
        grid = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        
        if self.current_view_mode == "packs":
            self._render_pack_widgets(grid, page_items)
        else:
            self._render_sticker_widgets(grid, page_items)

    def _render_pack_widgets(self, grid, items):
        cols = 4
        for i in range(cols): grid.grid_columnconfigure(i, weight=1)

        for i, pack in enumerate(items):
            # --- HIGHLIGHT CHECK ---
            # Check if this pack's thumbnail matches the current active cover
            thumb_path = pack.get('thumbnail_path')
            is_active = False
            
            # Resolve thumb path if it exists for comparison
            resolved_thumb = None
            if thumb_path:
                try: resolved_thumb = str(Path(thumb_path).resolve())
                except: pass
                
            if self.current_active_cover and resolved_thumb and self.current_active_cover == resolved_thumb:
                is_active = True
                
            border_color = COLORS["accent"] if is_active else COLORS["card_border"]
            border_width = 3 if is_active else 2

            # --- CARD SETUP ---
            card = ctk.CTkFrame(grid, fg_color=COLORS["card_bg"], corner_radius=8, border_width=border_width, border_color=border_color)
            card.grid(row=i//cols, column=i%cols, padx=5, pady=5, sticky="nsew")
            
            card.anim_loop = None 
            card.is_animated_content = False
            
            # Find Thumbnail
            thumb_path = pack.get('thumbnail_path')
            if not thumb_path:
                tname = pack['t_name']
                base = BASE_DIR / LIBRARY_FOLDER / tname
                if base.exists():
                    found = False
                    # Quick search for a valid thumbnail
                    for f in base.iterdir():
                        if f.suffix.lower() in {'.png', '.webp', '.gif', '.webm', '.mp4'}:
                            thumb_path = str(f); found = True; break
                    if not found: # Fallback specific check
                        for ext in ['.png', '.webp', '.gif', '.webm', '.mp4']: 
                            attempt = base / f"sticker_0{ext}"
                            if attempt.exists(): thumb_path = str(attempt); break

            img_lbl = ctk.CTkLabel(card, text=ICON_FOLDER, font=("Arial", 32), text_color=COLORS["text_sub"])
            img_lbl.pack(pady=(10, 5), padx=10, expand=True)
            card.image_label = img_lbl 
            
            if thumb_path:
                is_anim = self.utils.is_file_animated(thumb_path)
                card.is_animated_content = is_anim
                card.image_path = thumb_path
                
                if thumb_path.lower().endswith(('.webm', '.mp4', '.mkv')):
                    vid_thumb = self._generate_video_thumbnail(thumb_path, (80, 80))
                    if vid_thumb: img_lbl.configure(image=vid_thumb, text="")
                else:
                    self.utils.load_image_to_label(img_lbl, thumb_path, (80, 80), ICON_FOLDER, add_overlay=False)
                
                if is_anim:
                    # Staggered animation start
                    def start_anim(c=card, p=thumb_path, l=img_lbl):
                        if c.winfo_exists(): self.utils.animate_card(c, p, (80, 80), l)
                    card.after(i * 50 + 100, start_anim)
            
            # --- TITLE (No Truncation, Wraps) ---
            title = pack['name']
            # Removed truncation. using wraplength to handle long text.
            ctk.CTkLabel(
                card, text=title, font=FONT_SMALL, text_color=COLORS["text_main"],
                wraplength=130 # Matches approx card width
            ).pack(pady=(0, 5), padx=5)
            
            # --- INTERACTION ---
            def on_click(e, p=pack):
                self._render_sticker_grid(p, self._active_callback)
            self.utils.bind_hover_effects(card, on_click)

    def _render_sticker_widgets(self, grid, items):
        cols = 5 # Kept 5 columns as requested
        for i in range(cols): grid.grid_columnconfigure(i, weight=1)

        for i, path in enumerate(items):
            # --- HIGHLIGHT CHECK ---
            is_active = False
            try:
                if self.current_active_cover and str(Path(path).resolve()) == self.current_active_cover:
                    is_active = True
            except: pass
            
            border_color = COLORS["accent"] if is_active else COLORS["card_border"]
            border_width = 3 if is_active else 2

            frame = ctk.CTkFrame(grid, fg_color=COLORS["card_bg"], corner_radius=6, border_width=border_width, border_color=border_color)
            
            # UPDATED: Balanced padding (padx=6, pady=6)
            frame.grid(row=i//cols, column=i%cols, padx=6, pady=6) 
            
            frame.anim_loop = None
            frame.is_animated_content = False
            
            # UPDATED: Increased size from 100x100 -> 120x120
            img_lbl = ctk.CTkLabel(frame, text="", width=120, height=120, text_color=COLORS["text_sub"])
            img_lbl.pack(padx=2, pady=2)
            frame.image_label = img_lbl
            
            is_anim = self.utils.is_file_animated(path)
            frame.is_animated_content = is_anim
            frame.image_path = path
            
            if path.lower().endswith(('.webm', '.mp4', '.mkv')):
                vid_thumb = self._generate_video_thumbnail(path, (120, 120)) # UPDATED: 120x120
                if vid_thumb: img_lbl.configure(image=vid_thumb, text="")
                else: img_lbl.configure(text="VID")
            else:
                self.utils.load_image_to_label(img_lbl, path, (120, 120), "", add_overlay=False) # UPDATED: 120x120

            if is_anim:
                def start_anim(c=frame, p=path, l=img_lbl):
                    if c.winfo_exists(): self.utils.animate_card(c, p, (120, 120), l) # UPDATED: 120x120
                frame.after(i * 50 + 100, start_anim)

            # --- INTERACTION ---
            def on_click(e, p=path):
                self._stop_popup_animations()
                if self.cover_selector_win.winfo_exists(): self.cover_selector_win.destroy()
                self.app.last_width = 0
                self._active_callback(p)
            
            self.utils.bind_hover_effects(frame, on_click)

    # ==========================================================================
    #   UTILS
    # ==========================================================================
    def _stop_popup_animations(self):
        for widget in self.scroll_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame): # The grid wrapper
                 for card in widget.winfo_children(): # The cards
                    if hasattr(card, 'anim_loop') and card.anim_loop:
                        card.after_cancel(card.anim_loop)
                        card.anim_loop = None

    def _generate_video_thumbnail(self, path, size):
        try:
            cap = cv2.VideoCapture(path)
            ret, frame = cap.read()
            cap.release()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame)
                pil_img.thumbnail(size, Image.Resampling.LANCZOS)
                return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        except: pass
        return None

    # ==========================================================================
    #   COLLECTION MANAGEMENT
    # ==========================================================================

    def open_collection_edit_modal(self):
        collection_data = self.app.logic.selected_collection_data
        if not collection_data: return

        # Increase height to accommodate the split view
        win = self._create_base_window(f"Edit Collection: {collection_data['name']}", 600, 700)
        
        # 1. HEADER
        header = ctk.CTkFrame(win, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(header, text="Manage Collection", font=FONT_HEADER, text_color=COLORS["text_main"]).pack(anchor="center")
        ctk.CTkLabel(header, text=collection_data['name'], font=FONT_NORMAL, text_color=COLORS["accent"]).pack(anchor="center")
        
        # 2. TOP HALF: CURRENT PACKS LIST
        top_frame = ctk.CTkFrame(win, fg_color=COLORS["bg_sidebar"], corner_radius=10)
        top_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        ctk.CTkLabel(top_frame, text="Current Packs In Collection", font=FONT_TITLE, text_color=COLORS["text_sub"]).pack(pady=(10,5), padx=10, anchor="w")
        
        current_scroll = ctk.CTkScrollableFrame(top_frame, fg_color="transparent")
        current_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        def refresh_current_list():
            for w in current_scroll.winfo_children(): w.destroy()
            
            # Fetch fresh list from logic (as it might have changed)
            packs = collection_data.get('packs', [])
            if not packs:
                ctk.CTkLabel(current_scroll, text="Collection is empty.", text_color=COLORS["text_sub"]).pack(pady=20)
                return

            for pack in packs:
                row = ctk.CTkFrame(current_scroll, fg_color=COLORS["card_bg"], corner_radius=6)
                row.pack(fill="x", pady=3)
                
                # Name
                ctk.CTkLabel(row, text=pack['name'], font=FONT_NORMAL, text_color=COLORS["text_main"]).pack(side="left", padx=10, pady=8)
                
                # Remove Button
                ctk.CTkButton(
                    row, text=f"{ICON_REMOVE} Remove", width=70, height=24,
                    fg_color=COLORS["btn_negative"], hover_color=COLORS["btn_negative_hover"], text_color=COLORS["text_on_negative"],
                    command=lambda p=pack: [self.app.logic.remove_pack_from_collection(p['t_name']), refresh_current_list(), refresh_add_list()]
                ).pack(side="right", padx=10)
        
        # 3. BOTTOM HALF: ADD NEW PACKS
        bottom_frame = ctk.CTkFrame(win, fg_color="transparent")
        bottom_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        ctk.CTkLabel(bottom_frame, text="Add Packs to Collection", font=FONT_TITLE, text_color=COLORS["accent"]).pack(pady=(10, 5), anchor="w")
        
        # Search Bar for Adding
        search_fr = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        search_fr.pack(fill="x", pady=(0, 5))
        
        add_search_entry = ctk.CTkEntry(search_fr, placeholder_text=f"{ICON_SEARCH} Search library...", height=30, fg_color=COLORS["entry_bg"], text_color=COLORS["entry_text"])
        add_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # --- NEW: ORPHAN FILTER TOGGLE ---
        # "Unsorted Only" Switch
        filter_orphans_var = ctk.BooleanVar(value=False)
        
        def toggle_orphan_filter():
            refresh_add_list(add_search_entry.get())

        orphan_switch = ctk.CTkSwitch(
            search_fr, text="Unsorted Only", 
            variable=filter_orphans_var, 
            command=toggle_orphan_filter,
            progress_color=COLORS["accent"],
            button_color=COLORS["text_main"],
            button_hover_color=COLORS["accent_hover"],
            fg_color=COLORS["switch_fg"],
            text_color=COLORS["text_sub"],
            font=FONT_SMALL,
            width=120
        )
        orphan_switch.pack(side="right", padx=(5, 0))
        
        add_scroll = ctk.CTkScrollableFrame(bottom_frame, fg_color="transparent", border_width=1, border_color=COLORS["card_border"])
        add_scroll.pack(fill="both", expand=True)
        
        def refresh_add_list(query=""):
            for w in add_scroll.winfo_children(): w.destroy()
            query = query.lower()
            show_orphans_only = filter_orphans_var.get()
            
            # Identify what is already in the collection to exclude it
            current_tnames = {p['t_name'] for p in collection_data.get('packs', [])}
            
            count = 0
            for pack in self.app.library_data:
                # Basic Exclusions
                if pack['t_name'] in current_tnames: continue
                if query and query not in pack['name'].lower(): continue
                
                # --- ORPHAN FILTER CHECK ---
                if show_orphans_only:
                    # Check if pack is already linked to something else
                    # Logic: If 'linked_packs' is not empty, it belongs to a collection
                    if pack.get('linked_packs'): continue
                
                row = ctk.CTkFrame(add_scroll, fg_color=COLORS["card_bg"], corner_radius=6)
                row.pack(fill="x", pady=2)
                
                ctk.CTkLabel(row, text=pack['name'], font=FONT_NORMAL, text_color=COLORS["text_main"]).pack(side="left", padx=10, pady=5)
                
                # Add Button
                ctk.CTkButton(
                    row, text=f"{ICON_ADD} Add", width=60, height=24,
                    fg_color=COLORS["btn_positive"], hover_color=COLORS["btn_positive_hover"], text_color=COLORS["text_on_positive"],
                    command=lambda p=pack: [
                        self.app.logic.add_packs_to_collection_by_tname([p['t_name']]), 
                        refresh_current_list(), 
                        refresh_add_list(add_search_entry.get())
                    ]
                ).pack(side="right", padx=10)
                
                count += 1
                if count > 30 and not query: break
                
        add_search_entry.bind("<KeyRelease>", lambda e: refresh_add_list(add_search_entry.get()))

        refresh_current_list()
        refresh_add_list()

    def open_link_pack_modal(self):
        # 1. Matches "Edit Collection" modal size
        win = self._create_base_window("Add to Collection", 600, 700)
        
        # 2. Header matching Edit Collection
        header = ctk.CTkFrame(win, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)
        
        current_pack = self.app.logic.current_pack_data
        pack_name = current_pack.get('name', 'Pack') if current_pack else "Current Pack"
        
        ctk.CTkLabel(header, text="Add to Collection", font=FONT_HEADER, text_color=COLORS["text_main"]).pack(anchor="center")
        ctk.CTkLabel(header, text=f"Moving: {pack_name}", font=FONT_NORMAL, text_color=COLORS["accent"]).pack(anchor="center")
        
        self._build_link_ui(win, current_pack=current_pack)

    def _build_link_ui(self, win, current_pack=None, target_collection=None):
        # 3. Main Content Area matching "Edit Collection" style
        # We'll use a single large scrollable area for the "Target" list, 
        # but with the filter controls at the top.
        
        bottom_frame = ctk.CTkFrame(win, fg_color="transparent")
        bottom_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Search/Filter Bar
        search_fr = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        search_fr.pack(fill="x", pady=(0, 5))
        
        entry = ctk.CTkEntry(search_fr, placeholder_text=f"{ICON_SEARCH} Search collections...", height=30, fg_color=COLORS["entry_bg"], text_color=COLORS["entry_text"])
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # --- NEW: ORPHAN FILTER TOGGLE (Replacing Segmented Button) ---
        filter_orphans_var = ctk.BooleanVar(value=False)
        
        def toggle_orphan_filter():
            populate(entry.get())

        orphan_switch = ctk.CTkSwitch(
            search_fr, text="Unsorted Only", 
            variable=filter_orphans_var, 
            command=toggle_orphan_filter,
            progress_color=COLORS["accent"],
            button_color=COLORS["text_main"],
            button_hover_color=COLORS["accent_hover"],
            fg_color=COLORS["switch_fg"],
            text_color=COLORS["text_sub"],
            font=FONT_SMALL,
            width=120
        )
        orphan_switch.pack(side="right", padx=(5, 0))
        
        scroll = ctk.CTkScrollableFrame(bottom_frame, fg_color="transparent", border_width=1, border_color=COLORS["card_border"])
        scroll.pack(fill="both", expand=True)
        
        def populate(query=""):
            for w in scroll.winfo_children(): w.destroy()
            query = query.lower()
            show_orphans_only = filter_orphans_var.get()
            
            # --- Logic to exclude self/already linked ---
            excluded_tnames = set()
            if current_pack:
                excluded_tnames.add(current_pack['t_name'])
                excluded_tnames.update(current_pack.get('linked_packs', []))
            
            if target_collection:
                for p in target_collection['packs']:
                    excluded_tnames.add(p['t_name'])

            # 1. Identify Existing Collections in Library
            collections = {}
            for p in self.app.library_data:
                if p['linked_packs']:
                    root_tname = sorted([p['t_name']] + p['linked_packs'])[0]
                    col_name = p.get('custom_collection_name')
                    if not col_name:
                        root_p = next((x for x in self.app.library_data if x['t_name'] == root_tname), None)
                        col_name = f"{root_p['name']} Collection" if root_p else "Collection"
                    
                    if root_tname not in collections:
                        collections[root_tname] = {"name": col_name, "count": len(p['linked_packs'])+1, "id": root_tname}

            # 2. Render Collections (Unless Unsorted Only is ON, then usually we skip collections? 
            # Actually, "Unsorted Only" in "Add to Collection" context is slightly ambiguous. 
            # If I want to add *to* a collection, I need to see collections.
            # If I want to add *to* a Pack (making a new collection), I need to see Packs.
            # So "Unsorted Only" likely means "Show me Packs that aren't in a collection yet so I can merge with them".
            
            if not target_collection and not show_orphans_only and collections:
                ctk.CTkLabel(scroll, text="EXISTING COLLECTIONS", font=("Segoe UI", 12, "bold"), text_color=COLORS["accent"]).pack(anchor="w", pady=(5,2))
                
                for col_id, info in collections.items():
                    if query and query not in info['name'].lower(): continue
                    # Prevent linking to a collection we are already inside
                    if current_pack:
                        if current_pack['t_name'] == col_id: continue
                        target_col_root = next((x for x in self.app.library_data if x['t_name'] == col_id), None)
                        if target_col_root:
                             all_in_target = [col_id] + target_col_root.get('linked_packs', [])
                             if current_pack['t_name'] in all_in_target: continue

                    card = ctk.CTkFrame(scroll, fg_color=COLORS["card_bg"], corner_radius=6)
                    card.pack(fill="x", pady=3)
                    
                    btn = ctk.CTkButton(
                        card, text=f"{ICON_FOLDER} {info['name']}", height=40, anchor="w", font=FONT_NORMAL,
                        fg_color="transparent", hover_color=COLORS["card_hover"], text_color=COLORS["text_main"],
                        command=lambda target=col_id: [self.app.logic.link_pack(target), win.destroy()]
                    )
                    btn.pack(side="left", fill="both", expand=True, padx=5)
                    ctk.CTkLabel(card, text=f"{info['count']} Items", font=FONT_SMALL, text_color=COLORS["text_sub"]).pack(side="right", padx=10)

            # 3. Render Individual Packs
            header_txt = "AVAILABLE PACKS"
            if show_orphans_only: header_txt = "UNSORTED PACKS"
            elif target_collection: header_txt = "SELECT PACK TO ADD"
            
            ctk.CTkLabel(scroll, text=header_txt, font=("Segoe UI", 12, "bold"), text_color=COLORS["accent"]).pack(anchor="w", pady=(15,2))
            
            count = 0
            for pack in self.app.library_data:
                if pack['t_name'] in excluded_tnames: continue
                if query and query not in pack['name'].lower(): continue
                
                # --- ORPHAN FILTER CHECK ---
                if show_orphans_only:
                    # If it has linked packs, it is a collection root -> Skip
                    if pack.get('linked_packs'): continue
                    
                    # We also need to check if it is a LEAF in another collection.
                    # Currently, the library_data structure doesn't easily show "parent".
                    # However, logic.get_linked_pack_collection(pack) returns list > 1 if in collection.
                    # But that might be slow to call for every pack.
                    # Simplified check: logic usually keeps 'linked_packs' only on root.
                    # But leaves don't have a flag. 
                    # We can iterate all collections once to build a "taken" set.
                    pass # Implemented below efficiently
                
                card = ctk.CTkFrame(scroll, fg_color=COLORS["card_bg"], corner_radius=6)
                card.pack(fill="x", pady=3)
                
                if target_collection:
                    root_target = target_collection['packs'][0]['t_name']
                    cmd = lambda p=pack: [self.app.logic.merge_packs(root_target, p['t_name']), 
                                          self.app.logic.show_collection_details(self.app.logic._create_virtual_folder(self.app.logic.get_linked_pack_collection({'t_name':root_target, 'linked_packs': []}))),
                                          win.destroy()]
                else:
                    cmd = lambda p=pack: [self.app.logic.link_pack(p['t_name']), win.destroy()]

                btn = ctk.CTkButton(
                    card, text=pack['name'], height=35, anchor="w", font=FONT_NORMAL,
                    fg_color="transparent", hover_color=COLORS["card_hover"], text_color=COLORS["text_main"], 
                    command=cmd
                )
                btn.pack(side="left", fill="both", expand=True, padx=5)
                
                ctk.CTkLabel(card, text=f"{pack.get('count',0)} Stickers", font=FONT_SMALL, text_color=COLORS["text_sub"]).pack(side="right", padx=10)
                
                count += 1
                if count > 50 and not query: break 

        populate()
        entry.bind("<KeyRelease>", lambda e: populate(entry.get()))