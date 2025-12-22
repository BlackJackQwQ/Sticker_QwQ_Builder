import customtkinter as ctk
from typing import Optional
from pathlib import Path

from UI.PopUpPanel.Base import BasePopUp
from UI.ViewUtils import COLORS, load_ctk_image
from Core.Config import BASE_DIR, LIBRARY_FOLDER
from Resources.Icons import (
    FONT_HEADER, FONT_TITLE, FONT_NORMAL, FONT_SMALL,
    ICON_ADD, ICON_REMOVE, ICON_RANDOM, ICON_FOLDER, ICON_SEARCH
)

class DetailPopUp(BasePopUp):
    """
    Handles popups related to the Right Detail Panel (Covers, Collections).
    """
    def __init__(self, app):
        super().__init__(app)

    # ==========================================================================
    #   COVER SELECTOR
    # ==========================================================================

    def open_cover_selector_modal(self, is_collection=False):
        """
        Refined Cover Selector with Tabs: Gallery & Options.
        """
        target_name = ""
        if is_collection:
            if not self.app.logic.selected_collection_data: return
            target_name = "Collection Cover"
            packs_to_scan = self.app.logic.selected_collection_data['packs']
        else:
            if not self.app.logic.current_pack_data: return
            packs_to_scan = [self.app.logic.current_pack_data]
            target_name = "Pack Cover"
            
        win = self._create_base_window(f"Select {target_name}", 650, 650)
        
        # TABVIEW Structure
        tabs = ctk.CTkTabview(win, fg_color="transparent")
        tabs.pack(fill="both", expand=True, padx=10, pady=5)
        
        tab_gallery = tabs.add("Gallery")
        tab_opts = tabs.add("Options")
        
        # --- TAB 1: GALLERY ---
        ctk.CTkLabel(tab_gallery, text="Click an image to set it as cover", font=FONT_NORMAL, text_color=COLORS["text_sub"]).pack(pady=(5, 10))
        
        scroll = ctk.CTkScrollableFrame(tab_gallery, fg_color=COLORS["transparent"])
        scroll.pack(fill="both", expand=True)
        
        def set_cover(p_str: Optional[str]):
            if is_collection:
                self.app.logic.set_collection_cover(p_str)
            else:
                if p_str is None:
                    # Reset logic
                    self.app.logic.current_pack_data['thumbnail_path'] = "" 
                    if 'temp_thumbnail' in self.app.logic.current_pack_data:
                        del self.app.logic.current_pack_data['temp_thumbnail']
                else:
                    self.app.logic.current_pack_data['thumbnail_path'] = p_str
                
                self.app.client.save_library(self.app.library_data)
                self.app.details_manager.show_pack_details(self.app.logic.current_pack_data)
                self.app.refresh_view()
                
            if win.winfo_exists(): win.destroy()

        # Grid Builder for Gallery
        grid = ctk.CTkFrame(scroll, fg_color=COLORS["transparent"])
        grid.pack(fill="both")
        for i in range(5): grid.grid_columnconfigure(i, weight=1)
        
        # Populate images
        image_list = []
        MAX_IMAGES = 150 
        
        for p in packs_to_scan:
            tname = p['t_name']
            pack_path = BASE_DIR / LIBRARY_FOLDER / tname
            if pack_path.exists():
                imgs = [str(pack_path / f.name) for f in pack_path.iterdir() if f.suffix.lower() in {'.png','.gif','.webp'}]
                image_list.extend(imgs[:30]) 
                if len(image_list) > MAX_IMAGES: break 
        
        if not image_list:
            ctk.CTkLabel(scroll, text="No images found.", text_color=COLORS["text_sub"]).pack(pady=50)
        
        for i, path_str in enumerate(image_list):
            card = ctk.CTkFrame(grid, fg_color=COLORS["card_bg"], corner_radius=8)
            card.grid(row=i//5, column=i%5, padx=4, pady=4)
            
            preview = load_ctk_image(path_str, size=(80, 80))
            
            btn = ctk.CTkButton(
                card, text="", image=preview, width=90, height=90, 
                fg_color=COLORS["transparent"], hover_color=COLORS["card_hover"], 
                command=lambda p=path_str: set_cover(p)
            )
            btn.pack(padx=2, pady=2)

        # --- TAB 2: OPTIONS ---
        opt_frame = ctk.CTkFrame(tab_opts, fg_color=COLORS["transparent"])
        opt_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(opt_frame, text="Cover Settings", font=FONT_HEADER, text_color=COLORS["text_main"]).pack(pady=(0, 20))
        
        ctk.CTkButton(
            opt_frame, text=f"{ICON_RANDOM} Reset to Random Image", height=40, font=FONT_NORMAL,
            fg_color=COLORS["accent"], text_color=COLORS["text_on_accent"], hover_color=COLORS["accent_hover"],
            command=lambda: set_cover(None)
        ).pack(fill="x", pady=10)
        
        ctk.CTkButton(
            opt_frame, text=f"{ICON_REMOVE} Remove Cover (Use Default Icon)", height=40, font=FONT_NORMAL,
            fg_color=COLORS["btn_neutral"], text_color=COLORS["text_on_neutral"], hover_color=COLORS["card_hover"],
            command=lambda: set_cover("") 
        ).pack(fill="x", pady=10)
        
        ctk.CTkLabel(opt_frame, text="Note: 'Reset to Random' picks a random sticker each time the details are viewed.", 
                     font=FONT_SMALL, text_color=COLORS["text_sub"]).pack(pady=20)

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