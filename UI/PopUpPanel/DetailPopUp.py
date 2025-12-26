import customtkinter as ctk
from typing import Optional, Callable, Any
from pathlib import Path
import random

from UI.PopUpPanel.Base import BasePopUp
from UI.ViewUtils import COLORS, load_ctk_image
from Core.Config import BASE_DIR, LIBRARY_FOLDER
from Resources.Icons import (
    FONT_HEADER, FONT_TITLE, FONT_NORMAL, FONT_SMALL,
    ICON_ADD, ICON_REMOVE, ICON_RANDOM, ICON_FOLDER, ICON_SEARCH, ICON_LEFT
)

class DetailPopUp(BasePopUp):
    """
    Handles popups related to the Right Detail Panel (Covers, Collections).
    """
    def __init__(self, app):
        super().__init__(app)
        # State for the cover selector navigation
        self.cover_selector_win: Optional[ctk.CTkToplevel] = None
        self.current_view_mode = "packs" # "packs" or "stickers"
        self.current_pack_context = None

    # ==========================================================================
    #   COVER SELECTOR (MINI LIBRARY)
    # ==========================================================================

    def open_cover_selector_modal(self, target_name: str, on_select_callback: Callable[[Optional[str]], None]):
        """
        Opens a Mini-Library browser to select a cover image.
        
        Args:
            target_name: Title to display (e.g., "Pack Cover", "All Stickers Cover")
            on_select_callback: Function to call with the selected file path (or None for random).
        """
        if self.cover_selector_win and self.cover_selector_win.winfo_exists():
            self.cover_selector_win.focus()
            return

        self.cover_selector_win = self._create_base_window(f"Select {target_name}", 700, 650)
        self.current_view_mode = "packs"
        self.current_pack_context = None
        
        # --- HEADER CONTROLS ---
        header = ctk.CTkFrame(self.cover_selector_win, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=10)
        
        # Back Button (Hidden initially)
        self.back_btn = ctk.CTkButton(
            header, text=f"{ICON_LEFT} Back", width=80, height=30,
            fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"], text_color=COLORS["text_main"],
            command=self._go_back_to_packs
        )
        # We pack it, but might hide it in _render_pack_list
        self.back_btn.pack(side="left", padx=(0, 10))
        
        # Search Bar
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            header, textvariable=self.search_var, placeholder_text=f"{ICON_SEARCH} Search...", 
            height=35, fg_color=COLORS["entry_bg"], text_color=COLORS["entry_text"]
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search())

        # Options Menu
        def show_options():
            self._show_cover_options_menu(on_select_callback)

        opt_btn = ctk.CTkButton(
            header, text="Options", width=80, height=30,
            fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"], text_color=COLORS["text_main"],
            command=show_options
        )
        opt_btn.pack(side="right", padx=(10, 0))

        # --- CONTENT AREA ---
        self.scroll_frame = ctk.CTkScrollableFrame(self.cover_selector_win, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Initial Render
        self._render_pack_list(on_select_callback)

    def _show_cover_options_menu(self, callback):
        """Shows a small popup for 'Reset to Random' or 'Remove Cover'."""
        menu = ctk.CTkToplevel(self.cover_selector_win)
        menu.title("Options")
        menu.geometry("300x180")
        menu.transient(self.cover_selector_win)
        menu.configure(fg_color=COLORS["card_bg"])
        
        # Center over parent
        try:
            x = self.cover_selector_win.winfo_x() + (self.cover_selector_win.winfo_width() // 2) - 150
            y = self.cover_selector_win.winfo_y() + (self.cover_selector_win.winfo_height() // 2) - 90
            menu.geometry(f"+{x}+{y}")
        except: pass
        
        ctk.CTkLabel(menu, text="Cover Options", font=FONT_TITLE, text_color=COLORS["text_main"]).pack(pady=15)
        
        ctk.CTkButton(
            menu, text=f"{ICON_RANDOM} Reset to Random", 
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["text_on_accent"],
            command=lambda: [callback(None), menu.destroy(), self.cover_selector_win.destroy()]
        ).pack(fill="x", padx=20, pady=5)
        
        ctk.CTkButton(
            menu, text=f"{ICON_REMOVE} Remove Cover", 
            fg_color=COLORS["btn_neutral"], hover_color=COLORS["card_border"], text_color=COLORS["text_main"],
            command=lambda: [callback(""), menu.destroy(), self.cover_selector_win.destroy()]
        ).pack(fill="x", padx=20, pady=5)

    def _on_search(self):
        query = self.search_var.get().lower()
        if not hasattr(self, '_active_callback'): return
        
        if self.current_view_mode == "packs":
            self._render_pack_list(self._active_callback, query)
        elif self.current_view_mode == "stickers":
            self._render_sticker_grid(self.current_pack_context, self._active_callback, query)

    def _go_back_to_packs(self):
        self.search_entry.delete(0, "end")
        self._render_pack_list(self._active_callback)

    def _render_pack_list(self, callback, query=""):
        self.current_view_mode = "packs"
        self._active_callback = callback # Store for search events
        self.back_btn.pack_forget() # Hide Back button
        
        # Clear
        for w in self.scroll_frame.winfo_children(): w.destroy()
        
        # Grid setup
        grid = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        cols = 4
        for i in range(cols): grid.grid_columnconfigure(i, weight=1)
        
        # Filter Packs
        packs = [p for p in self.app.library_data if query in p['name'].lower()]
        
        if not packs:
            ctk.CTkLabel(self.scroll_frame, text="No packs found.", text_color=COLORS["text_sub"]).pack(pady=50)
            return

        for i, pack in enumerate(packs):
            if i > 50: break # Limit rendering
            
            # Mini Card
            card = ctk.CTkFrame(grid, fg_color=COLORS["card_bg"], corner_radius=8, border_width=1, border_color=COLORS["card_border"])
            card.grid(row=i//cols, column=i%cols, padx=5, pady=5, sticky="nsew")
            
            # Thumbnail Logic
            thumb_path = pack.get('thumbnail_path')
            if not thumb_path:
                # Try find one
                tname = pack['t_name']
                base = BASE_DIR / LIBRARY_FOLDER / tname
                if base.exists():
                    for ext in ['.png', '.webp']:
                        attempt = base / f"sticker_0{ext}"
                        if attempt.exists(): 
                            thumb_path = str(attempt)
                            break
            
            # Image
            img_lbl = ctk.CTkLabel(card, text=ICON_FOLDER, font=("Arial", 32), text_color=COLORS["text_sub"])
            img_lbl.pack(pady=(10, 5), padx=10, expand=True)
            
            if thumb_path:
                try:
                    img = load_ctk_image(thumb_path, (64, 64))
                    if img: img_lbl.configure(image=img, text="")
                except: pass
            
            # Title
            title = pack['name']
            if len(title) > 15: title = title[:12] + "..."
            ctk.CTkLabel(card, text=title, font=FONT_SMALL, text_color=COLORS["text_main"]).pack(pady=(0, 5))
            
            # Interaction
            cmd = lambda p=pack: self._render_sticker_grid(p, callback)
            
            card.bind("<Button-1>", lambda e, c=cmd: c())
            img_lbl.bind("<Button-1>", lambda e, c=cmd: c())
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, c=cmd: c())
                
            card.bind("<Enter>", lambda e, c=card: c.configure(border_color=COLORS["accent"], fg_color=COLORS["card_hover"]))
            card.bind("<Leave>", lambda e, c=card: c.configure(border_color=COLORS["card_border"], fg_color=COLORS["card_bg"]))

    def _render_sticker_grid(self, pack_data, callback, query=""):
        self.current_view_mode = "stickers"
        self.current_pack_context = pack_data
        self.back_btn.pack(side="left", padx=(0, 10)) # Show Back button
        
        # Clear
        for w in self.scroll_frame.winfo_children(): w.destroy()
        
        ctk.CTkLabel(self.scroll_frame, text=f"Stickers in: {pack_data['name']}", font=FONT_TITLE, text_color=COLORS["text_main"]).pack(pady=(0, 10))
        
        grid = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        grid.pack(fill="both")
        cols = 5
        for i in range(cols): grid.grid_columnconfigure(i, weight=1)
        
        base_path = BASE_DIR / LIBRARY_FOLDER / pack_data['t_name']
        sticker_files = []
        
        # Scan folder for valid images
        if base_path.exists():
            all_files = sorted(list(base_path.iterdir()), key=lambda x: x.name)
            for f in all_files:
                if f.suffix.lower() in {'.png', '.webp', '.gif'}:
                    if query and query not in f.name.lower(): continue
                    sticker_files.append(str(f))
        
        if not sticker_files:
            ctk.CTkLabel(self.scroll_frame, text="No images found.", text_color=COLORS["text_sub"]).pack(pady=50)
            return

        for i, path in enumerate(sticker_files):
            if i > 100: break
            
            frame = ctk.CTkFrame(grid, fg_color=COLORS["card_bg"], corner_radius=6)
            frame.grid(row=i//cols, column=i%cols, padx=4, pady=4)
            
            img_lbl = ctk.CTkLabel(frame, text="", width=80, height=80)
            img_lbl.pack(padx=2, pady=2)
            
            # Load
            img = load_ctk_image(path, (80, 80))
            if img: img_lbl.configure(image=img)
            
            # Select Action
            def on_click(p=path):
                callback(p)
                if self.cover_selector_win.winfo_exists():
                    self.cover_selector_win.destroy()
            
            img_lbl.bind("<Button-1>", lambda e, c=on_click: c())
            frame.bind("<Button-1>", lambda e, c=on_click: c())
            frame.bind("<Enter>", lambda e, f=frame: f.configure(fg_color=COLORS["accent"]))
            frame.bind("<Leave>", lambda e, f=frame: f.configure(fg_color=COLORS["card_bg"]))


    # ==========================================================================
    #   COLLECTION MANAGEMENT
    # ==========================================================================

    def open_collection_edit_modal(self):
        """
        Unified Modal for Managing a Collection (View contents, Remove, Add).
        """
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
        
        add_scroll = ctk.CTkScrollableFrame(bottom_frame, fg_color="transparent", border_width=1, border_color=COLORS["card_border"])
        add_scroll.pack(fill="both", expand=True)
        
        def refresh_add_list(query=""):
            for w in add_scroll.winfo_children(): w.destroy()
            query = query.lower()
            
            # Identify what is already in the collection to exclude it
            current_tnames = {p['t_name'] for p in collection_data.get('packs', [])}
            
            count = 0
            for pack in self.app.library_data:
                if pack['t_name'] in current_tnames: continue
                if query and query not in pack['name'].lower(): continue
                
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
        """
        Modal to link the CURRENT STANDALONE PACK to another pack/collection.
        """
        win = self._create_base_window("Add to Collection", 500, 650)
        
        header = ctk.CTkFrame(win, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))
        
        current_pack = self.app.logic.current_pack_data
        pack_name = current_pack.get('name', 'Pack') if current_pack else "Current Pack"
        
        ctk.CTkLabel(header, text="Add to Collection", font=FONT_HEADER, text_color=COLORS["text_main"]).pack(anchor="center")
        ctk.CTkLabel(header, text=f"Moving: {pack_name}", font=FONT_NORMAL, text_color=COLORS["accent"]).pack(anchor="center")
        
        self._build_link_ui(win, current_pack=current_pack)

    def _build_link_ui(self, win, current_pack=None, target_collection=None):
        """Shared UI builder for linking."""
        ctrl_frame = ctk.CTkFrame(win, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=15, pady=(5, 10))
        
        entry = ctk.CTkEntry(ctrl_frame, placeholder_text=f"{ICON_SEARCH} Search packs...", height=35, fg_color=COLORS["entry_bg"], text_color=COLORS["entry_text"])
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        filter_var = ctk.StringVar(value="All")
        filter_seg = ctk.CTkSegmentedButton(
            ctrl_frame, values=["All", "Collections", "Packs"], variable=filter_var,
            selected_color=COLORS["seg_selected"], selected_hover_color=COLORS["seg_selected"],
            unselected_color=COLORS["card_bg"], text_color=COLORS["seg_text"],
            height=30
        )
        filter_seg.pack(side="left")
        
        scroll = ctk.CTkScrollableFrame(win, fg_color=COLORS["transparent"])
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        def populate(query="", mode="All"):
            for w in scroll.winfo_children(): w.destroy()
            query = query.lower()
            
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

            # 2. Render Collections
            if not target_collection and mode in ["All", "Collections"] and collections:
                ctk.CTkLabel(scroll, text="EXISTING COLLECTIONS", font=("Segoe UI", 12, "bold"), text_color=COLORS["accent"]).pack(anchor="w", pady=(5,2))
                
                for col_id, info in collections.items():
                    if query and query not in info['name'].lower(): continue
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
            if mode in ["All", "Packs"]:
                header_txt = "AVAILABLE PACKS" if not target_collection else "SELECT PACK TO ADD"
                ctk.CTkLabel(scroll, text=header_txt, font=("Segoe UI", 12, "bold"), text_color=COLORS["accent"]).pack(anchor="w", pady=(15,2))
                
                count = 0
                for pack in self.app.library_data:
                    if pack['t_name'] in excluded_tnames: continue
                    if query and query not in pack['name'].lower(): continue
                    
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

        populate(mode="All")
        entry.bind("<KeyRelease>", lambda e: populate(entry.get(), filter_var.get()))
        filter_seg.configure(command=lambda m: populate(entry.get(), m))