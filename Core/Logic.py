import random
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set, Union
import customtkinter as ctk 

from Core.Config import SETTINGS_FILE, LIBRARY_FOLDER, BASE_DIR, save_json, load_json, logger
from Core.Downloader import DownloadManager
from UI.ViewUtils import resize_image_to_temp, is_system_tag, copy_to_clipboard, open_file_location, ToastNotification, COLORS
# NEW IMPORT: Needed to manually update favorited state on buttons without full refresh
from UI.DetailPanel.Elements import update_fav_btn

# Type Aliases
StickerData = Dict[str, Any]
PackData = Dict[str, Any]
SelectionItem = Tuple[StickerData, int, Optional[str], str] 

class AppLogic:
    """
    Central Controller with Folder/Collection support.
    Refactored to work with modular DetailPanel architecture.
    """

    def __init__(self, app):
        self.app = app
        self.downloader = DownloadManager(app)
        
        # --- STATE ---
        self.nsfw_enabled: bool = False
        self.current_theme_name: str = "Classic"
        self.app_token: str = ""
        
        # Filters
        self.only_favorites: bool = False
        self.filter_file_type: str = "All"
        self.filter_tag_mode: str = "Match All"
        self.sort_by: str = "Recently Added"
        self.sort_order: str = "Descending"
        self.search_query: str = ""
        self.include_tags: List[str] = []
        self.exclude_tags: List[str] = []
        
        # Pagination
        self.current_page: int = 1
        self.items_per_page: int = 50
        self.total_items: int = 0
        self.total_pages: int = 1
        
        # History & Autocomplete
        self.pack_search_history: List[str] = []
        self.sticker_search_history: List[str] = []
        self.pack_tags_ac: Set[str] = set()
        self.sticker_tags_ac: Set[str] = set()
        
        # Selection
        self.selected_stickers: List[SelectionItem] = [] 
        self.current_pack_data: Optional[PackData] = None 
        self.current_sticker_data: Optional[StickerData] = None 
        self.current_sticker_path: Optional[str] = None
        
        # UI State
        self.expanded_tag_containers: List[str] = [] 
        
        # --- NEW: Folder/Collection Logic ---
        self.current_collection_data: Optional[Dict] = None 
        self.selected_collection_data: Optional[Dict] = None 
        self.current_gallery_pack: Optional[Dict] = None 
        
        self.is_renaming_sticker: bool = False
        self.is_renaming_pack: bool = False 
        self.is_renaming_collection: bool = False
        
        # Ensure library_data exists on app immediately
        if not hasattr(self.app, 'library_data'):
            self.app.library_data = []

    # ==========================================================================
    #   INIT & SETTINGS
    # ==========================================================================

    def load_settings(self):
        data = load_json(SETTINGS_FILE)
        self.app_token = data.get("token", "")
        if hasattr(self.app, 'client'): self.app.client.set_token(self.app_token)
        self.current_theme_name = data.get("theme_name", "Classic")
        
        from UI.ViewUtils import apply_theme_palette
        apply_theme_palette(self.current_theme_name) 
        
        self.nsfw_enabled = data.get("nsfw_enabled", False)

    def load_library_data(self):
        self.app.library_data = self.app.client.load_library() or []
        self.sticker_tags_ac.add("NSFW") 
            
        for pack in self.app.library_data:
            pack.setdefault('tags', [])
            pack.setdefault('is_favorite', False)
            pack.setdefault('linked_packs', [])
            pack.setdefault('custom_collection_name', "") 
            pack.setdefault('custom_collection_cover', "") 
            pack.setdefault('custom_collection_tags', [])
            
            for t in pack['tags']: self.pack_tags_ac.add(t)
            for t in pack.get('custom_collection_tags', []): self.pack_tags_ac.add(t)
            
            for s in pack.get('stickers', []):
                s.setdefault('tags', [])
                s.setdefault('is_favorite', False)
                s.setdefault('usage_count', 0)
                for t in s['tags']: 
                    if not is_system_tag(t): self.sticker_tags_ac.add(t)
        
        self.apply_filters()

    def save_settings(self):
        data = {
            "token": self.app.client.token,
            "theme_name": self.current_theme_name,
            "nsfw_enabled": self.nsfw_enabled,
            "custom_theme_data": load_json(SETTINGS_FILE).get("custom_theme_data", {})
        }
        save_json(data, SETTINGS_FILE)

    def save_new_theme_and_restart(self, new_theme: str):
        self.current_theme_name = new_theme
        self.save_settings()
        self.app.restart_app()

    # ==========================================================================
    #   CORE LOGIC: FILTERING & HIERARCHY
    # ==========================================================================

    def apply_filters(self):
        is_desc = (self.sort_order == "Descending")
        
        def check_tags(tags):
            if self.exclude_tags and any(t in tags for t in self.exclude_tags): return False
            if not self.include_tags: return True
            if self.filter_tag_mode == "Match Any": return any(t in tags for t in self.include_tags)
            return all(t in tags for t in self.include_tags)

        if self.app.view_mode == "library":
            processed_tnames = set()
            display_items = []
            
            for p in self.app.library_data:
                tname = p['t_name']
                if tname in processed_tnames: continue
                
                # Preliminary check for searching (optimization)
                if self.search_query and self.search_query not in p.get('name','').lower():
                    # We still need to check if it's inside a collection that matches
                    pass

                links = self.get_linked_pack_collection(p)
                
                if len(links) > 1:
                    # It is a Virtual Collection
                    folder_obj = self._create_virtual_folder(links)
                    
                    # Apply filters to the collection object
                    if self.only_favorites:
                        if not any(lp.get('is_favorite') for lp in links): continue
                        
                    if self.search_query:
                         match_name = self.search_query in folder_obj['name'].lower()
                         match_pack = any(self.search_query in lp.get('name','').lower() for lp in links)
                         if not (match_name or match_pack): continue

                    # Mark all inside as processed so we don't duplicate
                    for lp in links: processed_tnames.add(lp['t_name'])
                    display_items.append(folder_obj)
                    
                else:
                    # It is a Single Pack
                    if self.search_query and self.search_query not in p.get('name','').lower(): continue
                    if self.only_favorites and not p.get('is_favorite'): continue
                    if not check_tags(p.get('tags', [])): continue
                    
                    processed_tnames.add(tname)
                    display_items.append(p)

            # Sort items
            if self.sort_by == "Random":
                random.shuffle(display_items)
            else:
                key = 'added'
                if self.sort_by == "Alphabetical": key = 'name'
                elif self.sort_by == "Sticker Count": key = 'count'
                
                # Robust sort key getter
                def get_sort_key(x):
                    val = x.get(key, 0)
                    if isinstance(val, str): return val.lower()
                    return val

                display_items.sort(key=get_sort_key, reverse=is_desc)

            self.app.filtered_library = display_items

        elif self.app.view_mode == "collection":
            if self.current_collection_data:
                raw_packs = self.current_collection_data['packs'] 
                self.app.filtered_library = sorted(raw_packs, key=lambda x: x.get('name',''), reverse=is_desc)
            else:
                self.app.filtered_library = []

        else:
            self._apply_sticker_filters()

    def _create_virtual_folder(self, packs: List[Dict]) -> Dict:
        root_pack = packs[0] 
        custom_name = next((p.get('custom_collection_name') for p in packs if p.get('custom_collection_name')), "")
        custom_cover = next((p.get('custom_collection_cover') for p in packs if p.get('custom_collection_cover')), "")
        
        display_name = custom_name if custom_name else f"{root_pack['name']} Collection"
        total_count = sum(p.get('count', 0) for p in packs)
        
        thumb = custom_cover or ""
        
        return {
            "type": "folder",
            "name": display_name,
            "count": total_count,
            "pack_count": len(packs),
            "thumbnail_path": thumb,
            "packs": packs, 
            "is_favorite": any(p.get('is_favorite') for p in packs), 
            "added": root_pack.get('added', ''),
            "updated": root_pack.get('updated', '')
        }

    def _apply_sticker_filters(self):
        is_desc = (self.sort_order == "Descending")
        raw = []
        pool = []
        
        if self.app.view_mode == "gallery_collection":
            if self.current_collection_data:
                pool = self.current_collection_data['packs']
        elif self.current_pack_data:
            pool = [self.current_pack_data]
        else:
            pool = self.app.library_data
            
        for p in pool:
            if not self.nsfw_enabled and "NSFW" in p.get('tags', []): continue
            for i, s in enumerate(p.get('stickers', [])):
                raw.append((s, p['t_name'], i))

        results = []
        for item in raw:
            s, pack_tname, idx = item
            tags = s.get('tags', [])
            
            if self.only_favorites and not s.get('is_favorite'): continue
            if not self.nsfw_enabled and "NSFW" in tags: continue
            
            if self.exclude_tags and any(t in tags for t in self.exclude_tags): continue
            if self.include_tags:
                match = any(t in tags for t in self.include_tags) if self.filter_tag_mode == "Match Any" else all(t in tags for t in self.include_tags)
                if not match: continue

            if self.search_query:
                q = self.search_query
                name_match = q in s.get('custom_name','').lower()
                tag_match = q in " ".join(tags).lower()
                if not (name_match or tag_match): continue
            
            results.append(item)

        if self.sort_by == "Usage":
            results.sort(key=lambda x: x[0].get('usage_count', 0), reverse=is_desc)
        elif self.sort_by == "Random":
            random.shuffle(results)
        else:
            # Sort by Pack Name then Index
            results.sort(key=lambda x: (x[1], x[2]), reverse=is_desc)
            
        self.app.filtered_stickers = results

    # ==========================================================================
    #   RENAMING & MANAGEMENT (UPDATED FOR NEW LAYOUT)
    # ==========================================================================

    def rename_collection_from_detail(self, new_name: str):
        if not self.selected_collection_data: return
        
        packs = self.selected_collection_data['packs']
        cleaned_name = new_name.strip()
        
        for p in packs:
            p['custom_collection_name'] = cleaned_name
            
        self.app.client.save_library(self.app.library_data)
        self.selected_collection_data['name'] = cleaned_name or f"{packs[0]['name']} Collection"
        
        # --- UPDATE UI: Target CollectionLayout ---
        layout = self.app.details_manager.collection_layout
        layout.title_lbl.configure(text=self.selected_collection_data['name'])
        
        self.is_renaming_collection = False
        layout.rename_btn.configure(text="Rename")
        layout.title_entry.pack_forget() 
        layout.title_lbl.pack(fill="x")
        
        if self.current_collection_data and self.current_collection_data['packs'][0]['t_name'] == packs[0]['t_name']:
             self.current_collection_data['name'] = self.selected_collection_data['name']
             self.app.header_title_label.configure(text=self.selected_collection_data['name'])
             
        self.apply_filters()
        self.app.refresh_view()

    def set_collection_cover(self, path_str: Optional[str]):
        if not self.selected_collection_data: return
        
        packs = self.selected_collection_data['packs']
        # If None, clear it to enable random logic
        val = path_str if path_str else ""
        
        for p in packs:
            p['custom_collection_cover'] = val
            
        self.app.client.save_library(self.app.library_data)
        self.selected_collection_data['thumbnail_path'] = val
        self.app.details_manager.show_collection_details(self.selected_collection_data)
        self.apply_filters()
        self.app.refresh_view()

    def open_collection_cover_selector(self):
        self.app.popup_manager.open_cover_selector_modal(is_collection=True)

    def disband_collection(self):
        if not self.selected_collection_data: return
        
        packs = self.selected_collection_data['packs']
        for p in packs:
            p['linked_packs'] = []
            p['custom_collection_name'] = ""
            p['custom_collection_cover'] = "" 
            
        self.app.client.save_library(self.app.library_data)
        self.selected_collection_data = None
        self.apply_filters()
        self.app.refresh_view()
        
        # --- UPDATE UI: Hide Collection Layout ---
        self.app.details_manager.collection_layout.hide()
            
        ToastNotification(self.app, "Success", "Collection disbanded.")

    def rename_pack_local(self, new_name: str):
        if not self.current_pack_data: return
        
        self.current_pack_data['name'] = new_name.strip()
        self.app.client.save_library(self.app.library_data)
        
        # --- UPDATE UI: Target PackLayout ---
        layout = self.app.details_manager.pack_layout
        layout.title_lbl.configure(text=new_name)
        
        self.is_renaming_pack = False
        layout.rename_btn.configure(text="Rename")
        layout.title_entry.pack_forget()
        layout.title_lbl.pack(fill="x")
        self.app.refresh_view()

    def toggle_rename_pack_ui(self):
        layout = self.app.details_manager.pack_layout
        
        if self.is_renaming_pack:
            new_name = layout.title_entry.get()
            self.rename_pack_local(new_name)
        else:
            self.is_renaming_pack = True
            layout.title_lbl.pack_forget()
            layout.title_entry.pack(fill="x")
            layout.title_entry.delete(0, "end")
            layout.title_entry.insert(0, layout.title_lbl.cget("text"))
            layout.title_entry.focus()
            layout.rename_btn.configure(text="Save")

    def toggle_rename_collection_ui(self):
        layout = self.app.details_manager.collection_layout
        
        if self.is_renaming_collection:
            new_name = layout.title_entry.get()
            self.rename_collection_from_detail(new_name)
        else:
            self.is_renaming_collection = True
            layout.title_lbl.pack_forget()
            layout.title_entry.pack(fill="x")
            layout.title_entry.delete(0, "end")
            layout.title_entry.insert(0, layout.title_lbl.cget("text"))
            layout.title_entry.focus()
            layout.rename_btn.configure(text="Save")

    def merge_packs(self, pack_a_tname: str, pack_b_tname: str):
        """Merges two packs into a collection by linking them together."""
        pa = next((p for p in self.app.library_data if p['t_name'] == pack_a_tname), None)
        pb = next((p for p in self.app.library_data if p['t_name'] == pack_b_tname), None)
        
        if pa and pb:
            # Ensure both packs link to each other
            if pack_b_tname not in pa['linked_packs']: pa['linked_packs'].append(pack_b_tname)
            if pack_a_tname not in pb['linked_packs']: pb['linked_packs'].append(pack_a_tname)
            
            # Sync any custom name if one exists
            name = pa.get('custom_collection_name') or pb.get('custom_collection_name')
            if name:
                pa['custom_collection_name'] = name
                pb['custom_collection_name'] = name
            
            # Save and Refresh
            self.app.client.save_library(self.app.library_data)
            self.apply_filters() 
            self.app.refresh_view()
            
            # If viewing details, update them
            if self.current_pack_data:
                self.app.details_manager.show_pack_details(self.current_pack_data)

    def add_packs_to_collection_by_tname(self, pack_tnames: List[str]):
        """
        Adds a list of packs to the currently selected collection.
        Used by the new Edit Collection modal.
        """
        if not self.selected_collection_data or not pack_tnames: return
        
        # Get current members
        current_members = self.selected_collection_data['packs']
        root_tname = current_members[0]['t_name']
        
        for new_tname in pack_tnames:
            self.merge_packs(root_tname, new_tname)
            
        # Refresh the current collection view
        new_folder = self._create_virtual_folder(self.get_linked_pack_collection({'t_name':root_tname, 'linked_packs': []})) # Re-fetch full object
        self.show_collection_details(new_folder)

    def link_pack(self, target_tname: str):
        """Links the current single pack to a target pack/collection."""
        self.merge_packs(self.current_pack_data['t_name'], target_tname)
        self.app.details_manager.show_pack_details(self.current_pack_data)

    def remove_pack_from_collection(self, tname_to_remove: str):
        """
        Removes a specific pack from the currently selected collection.
        """
        if not self.selected_collection_data: return

        target_pack = next((p for p in self.app.library_data if p['t_name'] == tname_to_remove), None)
        if not target_pack: return

        current_pack_tnames = [p['t_name'] for p in self.selected_collection_data['packs']]
        
        for p_tname in current_pack_tnames:
            if p_tname == tname_to_remove: continue
            
            p_obj = next((p for p in self.app.library_data if p['t_name'] == p_tname), None)
            if p_obj and tname_to_remove in p_obj['linked_packs']:
                p_obj['linked_packs'].remove(tname_to_remove)

        target_pack['linked_packs'] = []
        target_pack['custom_collection_name'] = ""
        target_pack['custom_collection_cover'] = ""
        target_pack['custom_collection_tags'] = []

        self.app.client.save_library(self.app.library_data)

        # Update Runtime Memory (UI Cache)
        self.selected_collection_data['packs'] = [p for p in self.selected_collection_data['packs'] if p['t_name'] != tname_to_remove]
        self.selected_collection_data['count'] -= target_pack.get('count', 0)
        self.selected_collection_data['pack_count'] -= 1
        
        if self.selected_collection_data['pack_count'] <= 1:
            self.selected_collection_data = None
            self.app.details_manager.collection_layout.hide()
            ToastNotification(self.app, "Collection Dissolved", "Only one pack remained.")
        else:
            self.app.details_manager.show_collection_details(self.selected_collection_data)

        self.apply_filters()
        self.app.refresh_view()

    def get_linked_pack_collection(self, root_pack: Dict[str, Any]) -> List[Dict[str, Any]]:
        collection = {root_pack['t_name']: root_pack}
        to_process = list(root_pack['linked_packs'])
        
        processed = set()
        processed.add(root_pack['t_name'])
        
        while to_process:
            curr_tname = to_process.pop()
            if curr_tname in processed: continue
            processed.add(curr_tname)
            
            found = next((p for p in self.app.library_data if p['t_name'] == curr_tname), None)
            if found:
                collection[curr_tname] = found
                for link in found['linked_packs']:
                    if link not in processed: to_process.append(link)
                    
        return sorted(list(collection.values()), key=lambda x: x.get('added', ''))

    # ==========================================================================
    #   NAVIGATION DELEGATES
    # ==========================================================================
    
    def open_collection(self, folder_data):
        self.current_collection_data = folder_data
        self.app.show_collection_view()

    def show_collection_details(self, folder_data):
        self.selected_collection_data = folder_data
        self.app.details_manager.show_collection_details(folder_data)

    def select_random_sticker(self):
        source = self.app.filtered_stickers
        if not source: return
        choice = random.choice(source)
        base = BASE_DIR / LIBRARY_FOLDER / choice[1]
        final_path = None
        for ext in [".png", ".gif", ".webp"]:
            p = base / f"sticker_{choice[2]}{ext}"
            if p.exists(): 
                final_path = str(p); break
        
        self.selected_stickers = [(choice[0], choice[2], final_path, choice[1])]
        self.current_sticker_data = choice[0]
        self.current_sticker_path = final_path
        self.app.details_manager.update_details_panel()

    # ==========================================================================
    #   STANDARD DELEGATES
    # ==========================================================================
    
    def on_sticker_click(self, sticker_data, idx, path, pack_tname, event=None):
        is_ctrl = event and (event.state & 4 or event.state & 0x20000)
        item = (sticker_data, idx, path, pack_tname)
        if is_ctrl:
            exists = next((i for i, s in enumerate(self.selected_stickers) if s[0] is sticker_data), -1)
            if exists != -1: self.selected_stickers.pop(exists)
            else: self.selected_stickers.append(item)
        else: self.selected_stickers = [item]

        if self.selected_stickers:
            last = self.selected_stickers[-1]
            self.current_sticker_data = last[0]
            self.current_sticker_path = last[2]
        else: self.current_sticker_data = None
            
        if hasattr(self.app, 'card_manager'): self.app.card_manager.highlight_selected_cards()
        if hasattr(self.app, 'details_manager'): self.app.details_manager.update_details_panel()

    def add_pack_from_url(self, urls: Union[str, List[str]]):
        if not self.app.client.token:
            self.app.popup_manager.open_settings_modal(); return
        if isinstance(urls, str): urls = [urls]
        
        for url in urls:
            clean_url = url.strip()
            if not clean_url: continue
            
            potential_name = clean_url.split('/')[-1]
            existing = next((p for p in self.app.library_data if p['t_name'] == potential_name), None)
            
            if existing:
                self.downloader.add_to_queue(existing, "update")
                ToastNotification(self.app, "Duplicate", f"Updating existing pack: {existing['name']}")
            else:
                self.downloader.add_to_queue(clean_url, "new")
        
        if not existing:
            ToastNotification(self.app, "Queue Started", f"Processing {len(urls)} packs")

    def trigger_redownload(self):
        if self.current_pack_data:
            self.downloader.add_to_queue(self.current_pack_data, "update")
            ToastNotification(self.app, "Queued", "Re-downloading...")
            
    def update_all_packs(self):
        self.app.popup_manager.open_update_modal(self._run_update_check)

    def _run_update_check(self, progress_callback, status_callback, finish_callback):
        import threading
        def _check():
            total = len(self.app.library_data)
            updates_found = 0
            for i, pack in enumerate(self.app.library_data):
                if status_callback: status_callback(f"Checking: {pack.get('name')}")
                if progress_callback: progress_callback(i / total)
                try:
                    remote = self.app.client.get_pack_by_name(pack.get('t_name'))
                    if remote and len(remote.get('stickers',[])) != pack.get('count', 0):
                        pack['stickers'] = remote['stickers']
                        pack['count'] = len(remote['stickers'])
                        self.downloader.add_to_queue(pack, "update")
                        updates_found += 1
                except Exception: pass
            if progress_callback: progress_callback(1.0)
            if status_callback: status_callback(f"Queued {updates_found} updates.")
            self.app.after(1500, finish_callback)
        threading.Thread(target=_check, daemon=True).start()

    def reset_filters(self):
        self.sort_by = "Recently Added"
        self.sort_order = "Descending"
        self.only_favorites = False
        self.filter_file_type = "All"
        self.search_query = ""
        self.include_tags.clear()
        self.exclude_tags.clear()
        self.app.filter_manager.refresh_ui()
        self.app.search_entry.delete(0, "end")
        self.apply_filters()
        self.app.refresh_view()

    def on_filter_change(self, val=None):
        mgr = self.app.filter_manager
        self.sort_by = mgr.sort_opt.get()
        self.sort_order = mgr.order_opt.get()
        self.nsfw_enabled = bool(mgr.nsfw_switch.get())
        self.only_favorites = bool(mgr.fav_switch.get())
        self.filter_file_type = mgr.file_type_seg.get()
        self.filter_tag_mode = mgr.tag_match_seg.get()
        self.save_settings()
        self.current_page = 1 
        self.apply_filters()
        self.app.refresh_view()

    def change_page(self, direction: str):
        if direction == "next" and self.current_page < self.total_pages:
            self.current_page += 1
            self.app.refresh_view()
        elif direction == "prev" and self.current_page > 1:
            self.current_page -= 1
            self.app.refresh_view()

    def set_items_per_page(self, value: str):
        self.items_per_page = 999999 if value == "All" else int(value)
        self.current_page = 1
        self.app.refresh_view()

    def get_current_page_items(self):
        source = self.app.filtered_library if self.app.view_mode in ["library", "collection"] else self.app.filtered_stickers
        self.total_items = len(source)
        self.total_pages = (self.total_items + self.items_per_page - 1) // self.items_per_page or 1
        self.current_page = max(1, min(self.current_page, self.total_pages))
        start = (self.current_page - 1) * self.items_per_page
        return source[start : start + self.items_per_page]

    def toggle_favorite(self, type_):
        # --- UPDATE UI: Specific Layouts ---
        
        if type_ == "pack":
            if self.current_pack_data:
                state = not self.current_pack_data.get('is_favorite')
                self.current_pack_data['is_favorite'] = state
                self.app.client.save_library(self.app.library_data)
                
                # Update UI
                layout = self.app.details_manager.pack_layout
                update_fav_btn(layout.fav_btn, state, COLORS)
                
        elif type_ == "collection":
            if self.selected_collection_data:
                state = not self.selected_collection_data.get('is_favorite', False)
                self.selected_collection_data['is_favorite'] = state
                
                for p in self.selected_collection_data['packs']:
                    p['is_favorite'] = state
                
                self.app.client.save_library(self.app.library_data)
                
                # Update UI
                layout = self.app.details_manager.collection_layout
                update_fav_btn(layout.fav_btn, state, COLORS)
                
                self.apply_filters()
                self.app.refresh_view()
        else:
            if not self.selected_stickers: return
            target_state = any(not s[0].get('is_favorite') for s in self.selected_stickers)
            for s in self.selected_stickers: s[0]['is_favorite'] = target_state
            self.app.client.save_library(self.app.library_data)
            
            # Refresh Sticker Panel
            self.app.details_manager.update_details_panel()
            
        self.app.refresh_view()

    def copy_sticker(self):
        if not self.selected_stickers: return
        data, _, path, _ = self.selected_stickers[-1]
        if not path: return
        
        # --- UPDATE UI: Target StickerLayout for size ---
        size = self.app.details_manager.sticker_layout.size_var.get()
        
        final_path = resize_image_to_temp(path, size)
        if final_path:
            copy_to_clipboard(final_path)
            data['usage_count'] += 1
            data['last_used'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.app.client.save_library(self.app.library_data)
            if len(self.selected_stickers) == 1: 
                self.app.details_manager.update_details_panel()

    def show_file(self):
        if self.selected_stickers: open_file_location(self.selected_stickers[-1][2], True)

    def open_url(self, e=None):
        if self.current_pack_data: webbrowser.open(self.current_pack_data['url'])
        
    def on_search(self, e=None):
        self.search_query = self.app.search_entry.get().lower()
        if self.search_query and self.search_query not in self.pack_search_history:
             self.pack_search_history.append(self.search_query)
        self.current_page = 1
        self.apply_filters()
        self.app.refresh_view()
    
    def clear_search(self):
        self.app.search_entry.delete(0, "end")
        self.on_search()
        
    def show_search_history(self):
        h = self.pack_search_history 
        self.app.popup_manager.show_search_history(h)

    def add_tag(self, prefix):
        pass

    def add_tag_manual(self, context_type: str, tag_text: str):
        val = tag_text.strip()
        if not val or is_system_tag(val): return
        
        if context_type == "pack":
             if self.current_pack_data:
                 if val not in self.current_pack_data['tags']:
                     self.current_pack_data['tags'].append(val)
                     self.pack_tags_ac.add(val)
                     
        elif context_type == "collection":
             if self.selected_collection_data:
                 root = self.selected_collection_data['packs'][0]
                 if 'custom_collection_tags' not in root: root['custom_collection_tags'] = []
                 if val not in root['custom_collection_tags']:
                     root['custom_collection_tags'].append(val)
                     self.pack_tags_ac.add(val)
                     
        elif context_type == "sticker":
             for s in self.selected_stickers:
                if val not in s[0]['tags']: s[0]['tags'].append(val)
             self.sticker_tags_ac.add(val)
            
        self.app.client.save_library(self.app.library_data)
        
        # --- UPDATE UI: Target specific layout tag section ---
        if context_type == "pack":
            self.app.details_manager.pack_layout.tags.render(self.current_pack_data['tags'])
        elif context_type == "collection":
            root = self.selected_collection_data['packs'][0]
            self.app.details_manager.collection_layout.tags.render(root.get('custom_collection_tags', []))
        elif context_type == "sticker":
            # Refresh the whole sticker panel to be safe (single or batch)
             self.app.details_manager.update_details_panel()

    def confirm_remove_tag(self, prefix, tag):
        # prefix maps to context_type (pack, collection, sticker)
        if prefix == "pack":
            if self.current_pack_data and tag in self.current_pack_data['tags']:
                self.current_pack_data['tags'].remove(tag)
        elif prefix == "collection":
            if self.selected_collection_data:
                root = self.selected_collection_data['packs'][0]
                if tag in root.get('custom_collection_tags', []):
                    root['custom_collection_tags'].remove(tag)
        else:
            for s in self.selected_stickers:
                if tag in s[0]['tags']: s[0]['tags'].remove(tag)
                
        self.app.client.save_library(self.app.library_data)
        
        # --- UPDATE UI ---
        if prefix == "pack":
            self.app.details_manager.pack_layout.tags.render(self.current_pack_data['tags'])
        elif prefix == "collection":
            root = self.selected_collection_data['packs'][0]
            self.app.details_manager.collection_layout.tags.render(root.get('custom_collection_tags', []))
        else:
            self.app.details_manager.update_details_panel()

    def add_filter_tag_direct(self, tag, mode):
        target = self.include_tags if mode == "Include" else self.exclude_tags
        if tag not in target:
            target.append(tag)
            self.app.filter_manager.refresh_ui()
            self.apply_filters()
            self.app.refresh_view()
            
    def remove_filter_tag(self, tag, mode):
        target = self.include_tags if mode == "Include" else self.exclude_tags
        if tag in target:
            target.remove(tag)
            self.app.filter_manager.refresh_ui()
            self.apply_filters()
            self.app.refresh_view()

    def get_tag_usage(self):
        usage = {}
        pool = getattr(self.app, 'library_data', [])
        mode = getattr(self.app, 'view_mode', 'library')
        
        if mode == "gallery_pack" and self.current_pack_data:
            pool = [self.current_pack_data]
        elif mode in ["collection", "gallery_collection"] and self.current_collection_data:
            pool = self.current_collection_data.get('packs', [])
            
        for p in pool:
            for s in p.get('stickers', []):
                for t in s.get('tags', []): usage[t] = usage.get(t, 0) + 1
        return usage
        
    def expand_tags(self, type_):
        # This feature might need re-implementation in Sections.py if strictly required, 
        # but for now we just refresh the render.
        # self.app.details_manager.render_tags(type_) -> 
        # mapped to:
        if type_ == "pack":
             self.app.details_manager.pack_layout.tags.render(self.current_pack_data['tags'])
        elif type_ == "collection":
             # ...
             pass
        # Kept generic as the UI logic is now handled inside Sections.py
        pass
        
    def get_most_used_stickers(self, limit=10):
        all_s = []
        for p in self.app.library_data:
            for i, s in enumerate(p.get('stickers', [])):
                if s.get('usage_count', 0) > 0: 
                    all_s.append((s, p['t_name'], p.get('name'), i))
        
        all_s.sort(key=lambda x: x[0].get('usage_count'), reverse=True)
        
        results = []
        for s, tname, pname, idx in all_s[:limit]:
            base = BASE_DIR / LIBRARY_FOLDER / tname
            path_str = None
            for ext in [".png", ".gif", ".webp"]:
                p_check = base / f"sticker_{idx}{ext}"
                if p_check.exists(): 
                    path_str = str(p_check)
                    break
                    
            results.append({
                "name": s.get('custom_name', "Sticker"), 
                "usage": s['usage_count'], 
                "tags": s.get('tags', []), 
                "pack_tname": tname, 
                "pack_display_name": pname,
                "image_path": path_str
            })
        return results

    def open_usage_stats(self):
        self.app.popup_manager.open_usage_stats_modal()

    def link_pack(self, target_tname: str):
        self.merge_packs(self.current_pack_data['t_name'], target_tname)
        self.app.details_manager.show_pack_details(self.current_pack_data)

    def unlink_pack(self, target_tname: str):
        current = self.current_pack_data
        target = next((p for p in self.app.library_data if p['t_name'] == target_tname), None)
        
        if current and target_tname in current['linked_packs']:
            current['linked_packs'].remove(target_tname)
        
        if target and current['t_name'] in target['linked_packs']:
            target['linked_packs'].remove(current['t_name'])
            
        self.app.client.save_library(self.app.library_data)
        self.apply_filters() 
        self.app.refresh_view()
        self.app.details_manager.show_pack_details(current)
            
    def open_cover_selector(self):
        self.app.popup_manager.open_cover_selector_modal()
    
    def toggle_rename(self):
        # Sticker Rename
        if len(self.selected_stickers) != 1: return
        
        layout = self.app.details_manager.sticker_layout
        sticker_data = self.selected_stickers[0][0]
        
        if self.is_renaming_sticker:
            new_name = layout.name_entry.get()
            sticker_data['custom_name'] = new_name
            self.app.client.save_library(self.app.library_data)
            
            layout.name_lbl.configure(text=new_name or "Sticker")
            layout.name_entry.pack_forget()
            layout.name_lbl.pack(fill="x")
            layout.rename_btn.configure(text="Rename")
            
            self.app.refresh_view()
            self.is_renaming_sticker = False
        else:
            layout.name_entry.delete(0, "end")
            layout.name_entry.insert(0, layout.name_lbl.cget("text"))
            layout.name_lbl.pack_forget()
            layout.name_entry.pack(fill="x")
            layout.name_entry.focus()
            layout.rename_btn.configure(text="Save")
            self.is_renaming_sticker = True
            
    def confirm_remove_pack(self):
        win = ctk.CTkToplevel(self.app)
        win.title("Confirm")
        win.geometry("300x150")
        
        from UI.ViewUtils import center_window, set_window_icon, COLORS
        center_window(win, 300, 150)
        set_window_icon(win)
        win.attributes('-topmost', True)
        win.configure(fg_color=COLORS["bg_main"])
        
        ctk.CTkLabel(win, text="Delete Pack?", font=("Segoe UI", 16, "bold"), text_color=COLORS["text_main"]).pack(pady=20)
        ctk.CTkButton(
            win, text="Delete", 
            fg_color=COLORS["btn_negative"], hover_color=COLORS["btn_negative_hover"], text_color=COLORS["text_on_negative"], 
            command=lambda: [self.perform_remove(), win.destroy()]
        ).pack(pady=10)

    def perform_remove(self):
        if self.current_pack_data in self.app.library_data:
            self.app.library_data.remove(self.current_pack_data)
            self.app.client.save_library(self.app.library_data)
            self.current_pack_data = None
            self.apply_filters()
            self.app.refresh_view()
            
            # --- UPDATE UI: Hide Pack Layout ---
            self.app.details_manager.pack_layout.hide()