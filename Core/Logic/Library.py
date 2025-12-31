import customtkinter as ctk
from datetime import datetime
from typing import List, Dict, Any, Optional

from Core.Config import save_json, load_json, SETTINGS_FILE, logger
from UI.ViewUtils import COLORS, is_system_tag, ToastNotification
from UI.DetailPanel.Elements import update_fav_btn

class LibraryManager:
    """
    The Data Handler.
    Responsible for all WRITE operations to the library_data list.
    Includes Renaming, Merging, Tagging, and Deletion logic.
    """
    
    def __init__(self, app):
        self.app = app
        
        # UI State flags for renaming
        self.is_renaming_sticker: bool = False
        self.is_renaming_pack: bool = False 
        self.is_renaming_collection: bool = False

    # ==========================================================================
    #   DATA LOADING & CACHE MANAGEMENT (The Fix)
    # ==========================================================================

    def load_library_data(self):
        """Initial load of data from JSON."""
        self.app.library_data = self.app.client.load_library() or []
        
        # Ensure defaults structure first
        for pack in self.app.library_data:
            pack.setdefault('tags', [])
            pack.setdefault('is_favorite', False)
            pack.setdefault('linked_packs', [])
            pack.setdefault('custom_collection_name', "") 
            pack.setdefault('custom_collection_cover', "") 
            pack.setdefault('custom_collection_tags', [])
            
            for s in pack.get('stickers', []):
                s.setdefault('tags', [])
                s.setdefault('is_favorite', False)
                s.setdefault('usage_count', 0)

        # Build the initial tag cache
        self._rebuild_tag_cache()

    def _rebuild_tag_cache(self):
        """
        GHOST BUSTER: Completely wipes and rebuilds the global tag lists 
        based on what actually exists in the library.
        """
        if not hasattr(self.app, 'logic'): return

        # 1. Clear existing global lists
        self.app.logic.sticker_tags_ac.clear()
        self.app.logic.pack_tags_ac.clear()
        
        # 2. Add System defaults
        self.app.logic.sticker_tags_ac.add("NSFW")

        # 3. Scan Library
        for pack in self.app.library_data:
            # Add Pack Tags
            for t in pack['tags']: 
                self.app.logic.pack_tags_ac.add(t)
            
            # Add Collection Tags (if it's a root of a collection)
            for t in pack.get('custom_collection_tags', []): 
                self.app.logic.pack_tags_ac.add(t)
            
            # Add Sticker Tags
            for s in pack.get('stickers', []):
                for t in s['tags']: 
                    if not is_system_tag(t): 
                        self.app.logic.sticker_tags_ac.add(t)
        
        logger.info("Tag cache rebuilt. Ghosts busted.")

    def _save(self):
        """Helper to save library state."""
        self.app.client.save_library(self.app.library_data)

    # ==========================================================================
    #   RENAMING LOGIC
    # ==========================================================================

    def rename_pack_local(self, new_name: str):
        if not self.app.logic.current_pack_data: return
        
        name_str = new_name.strip()
        self.app.logic.current_pack_data['name'] = name_str
        self._save()
        
        # Update UI directly
        layout = self.app.details_manager.pack_layout
        layout.title_lbl.configure(text=name_str)
        
        self.is_renaming_pack = False
        layout.rename_btn.configure(text="Rename")
        layout.title_entry.pack_forget()
        layout.title_lbl.pack(fill="x")
        self.app.refresh_view()
        
        ToastNotification(self.app, "Renamed", f"Pack renamed to '{name_str}'")

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

    def rename_collection_from_detail(self, new_name: str):
        sel_col = self.app.logic.selected_collection_data
        if not sel_col: return
        
        packs = sel_col['packs']
        cleaned_name = new_name.strip()
        
        for p in packs:
            p['custom_collection_name'] = cleaned_name
            
        self._save()
        sel_col['name'] = cleaned_name or f"{packs[0]['name']} Collection"
        
        layout = self.app.details_manager.collection_layout
        layout.title_lbl.configure(text=sel_col['name'])
        
        self.is_renaming_collection = False
        layout.rename_btn.configure(text="Rename")
        layout.title_entry.pack_forget() 
        layout.title_lbl.pack(fill="x")
        
        # Update current view context if we are looking at this collection
        curr_col = self.app.logic.current_collection_data
        if curr_col and curr_col['packs'][0]['t_name'] == packs[0]['t_name']:
             curr_col['name'] = sel_col['name']
             self.app.header_title_label.configure(text=sel_col['name'])
             
        self.app.logic.apply_filters()
        self.app.refresh_view()
        
        ToastNotification(self.app, "Renamed", f"Collection renamed to '{cleaned_name}'")

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

    def toggle_rename_sticker(self):
        # Only support single selection renaming
        if len(self.app.logic.selected_stickers) != 1: return
        
        layout = self.app.details_manager.sticker_layout
        sticker_data = self.app.logic.selected_stickers[0][0]
        
        if self.is_renaming_sticker:
            new_name = layout.name_entry.get().strip()
            sticker_data['custom_name'] = new_name
            self._save()
            
            layout.name_lbl.configure(text=new_name or "Sticker")
            layout.name_entry.pack_forget()
            layout.name_lbl.pack(fill="x")
            layout.rename_btn.configure(text="Rename")
            
            self.app.refresh_view()
            self.is_renaming_sticker = False
            
            ToastNotification(self.app, "Renamed", f"Sticker renamed to '{new_name}'")
        else:
            layout.name_entry.delete(0, "end")
            layout.name_entry.insert(0, layout.name_lbl.cget("text"))
            layout.name_lbl.pack_forget()
            layout.name_entry.pack(fill="x")
            layout.name_entry.focus()
            layout.rename_btn.configure(text="Save")
            self.is_renaming_sticker = True

    # ==========================================================================
    #   STRUCTURE LOGIC (Merging/Collections)
    # ==========================================================================

    def merge_packs(self, pack_a_tname: str, pack_b_tname: str):
        """Merges two packs into a collection by linking them together."""
        lib = self.app.library_data
        pa = next((p for p in lib if p['t_name'] == pack_a_tname), None)
        pb = next((p for p in lib if p['t_name'] == pack_b_tname), None)
        
        if pa and pb:
            # Bi-directional linking
            if pack_b_tname not in pa['linked_packs']: pa['linked_packs'].append(pack_b_tname)
            if pack_a_tname not in pb['linked_packs']: pb['linked_packs'].append(pack_a_tname)
            
            # Sync name
            name = pa.get('custom_collection_name') or pb.get('custom_collection_name')
            if name:
                pa['custom_collection_name'] = name
                pb['custom_collection_name'] = name
            
            self._save()
            self.app.logic.apply_filters() 
            self.app.refresh_view()
            
            if self.app.logic.current_pack_data:
                self.app.details_manager.show_pack_details(self.app.logic.current_pack_data)
                
            ToastNotification(self.app, "Collection Updated", "Packs linked successfully.")

    def link_pack(self, target_tname: str):
        """Links current pack to target."""
        if not self.app.logic.current_pack_data: return
        self.merge_packs(self.app.logic.current_pack_data['t_name'], target_tname)
        self.app.details_manager.show_pack_details(self.app.logic.current_pack_data)

    def unlink_pack(self, target_tname: str):
        current = self.app.logic.current_pack_data
        target = next((p for p in self.app.library_data if p['t_name'] == target_tname), None)
        
        if current and target_tname in current['linked_packs']:
            current['linked_packs'].remove(target_tname)
        
        if target and current['t_name'] in target['linked_packs']:
            target['linked_packs'].remove(current['t_name'])
            
        self._save()
        self.app.logic.apply_filters() 
        self.app.refresh_view()
        self.app.details_manager.show_pack_details(current)

    def add_packs_to_collection_by_tname(self, pack_tnames: List[str]):
        if not self.app.logic.selected_collection_data or not pack_tnames: return
        
        current_members = self.app.logic.selected_collection_data['packs']
        root_tname = current_members[0]['t_name']
        
        for new_tname in pack_tnames:
            self.merge_packs(root_tname, new_tname)
            
        # Refresh Collection View
        new_folder = self.app.logic._create_virtual_folder(
            self.app.logic.get_linked_pack_collection({'t_name':root_tname, 'linked_packs': []})
        )
        self.app.logic.show_collection_details(new_folder)

    def remove_pack_from_collection(self, tname_to_remove: str):
        sel_col = self.app.logic.selected_collection_data
        if not sel_col: return

        target_pack = next((p for p in self.app.library_data if p['t_name'] == tname_to_remove), None)
        if not target_pack: return

        current_pack_tnames = [p['t_name'] for p in sel_col['packs']]
        
        # Remove links from all other members
        for p_tname in current_pack_tnames:
            if p_tname == tname_to_remove: continue
            
            p_obj = next((p for p in self.app.library_data if p['t_name'] == p_tname), None)
            if p_obj and tname_to_remove in p_obj['linked_packs']:
                p_obj['linked_packs'].remove(tname_to_remove)

        # Clear target
        target_pack['linked_packs'] = []
        target_pack['custom_collection_name'] = ""
        target_pack['custom_collection_cover'] = ""
        target_pack['custom_collection_tags'] = []
        
        # Rebuild tags because a collection tag might have become orphaned
        self._rebuild_tag_cache()
        self._save()

        # Update Runtime Memory
        sel_col['packs'] = [p for p in sel_col['packs'] if p['t_name'] != tname_to_remove]
        sel_col['count'] -= target_pack.get('count', 0)
        sel_col['pack_count'] -= 1
        
        if sel_col['pack_count'] <= 1:
            self.app.logic.selected_collection_data = None
            self.app.details_manager.collection_layout.hide()
            ToastNotification(self.app, "Collection Dissolved", "Only one pack remained.")
        else:
            self.app.details_manager.show_collection_details(sel_col)

        self.app.logic.apply_filters()
        self.app.refresh_view()

    def disband_collection(self):
        sel_col = self.app.logic.selected_collection_data
        if not sel_col: return
        
        for p in sel_col['packs']:
            p['linked_packs'] = []
            p['custom_collection_name'] = ""
            p['custom_collection_cover'] = "" 
        
        # Rebuild tags immediately
        self._rebuild_tag_cache()
        self._save()
        
        self.app.logic.selected_collection_data = None
        self.app.logic.apply_filters()
        self.app.refresh_view()
        
        self.app.details_manager.collection_layout.hide()
        ToastNotification(self.app, "Success", "Collection Disbanded Successfully.")

    # ==========================================================================
    #   TAGS & COVERS
    # ==========================================================================

    def add_tag_manual(self, context_type: str, tag_text: str):
        val = tag_text.strip()
        if not val or is_system_tag(val): return
        
        if context_type == "pack":
             if self.app.logic.current_pack_data:
                 if val not in self.app.logic.current_pack_data['tags']:
                     self.app.logic.current_pack_data['tags'].append(val)
                     self.app.logic.pack_tags_ac.add(val)
                     
        elif context_type == "collection":
             if self.app.logic.selected_collection_data:
                 root = self.app.logic.selected_collection_data['packs'][0]
                 if 'custom_collection_tags' not in root: root['custom_collection_tags'] = []
                 if val not in root['custom_collection_tags']:
                     root['custom_collection_tags'].append(val)
                     self.app.logic.pack_tags_ac.add(val)
                     
        elif context_type == "sticker":
             for s in self.app.logic.selected_stickers:
                if val not in s[0]['tags']: s[0]['tags'].append(val)
             self.app.logic.sticker_tags_ac.add(val)
            
        self._save()
        
        # Update UI
        if context_type == "pack":
            self.app.details_manager.pack_layout.tags.render(self.app.logic.current_pack_data['tags'])
        elif context_type == "collection":
            root = self.app.logic.selected_collection_data['packs'][0]
            self.app.details_manager.collection_layout.tags.render(root.get('custom_collection_tags', []))
        elif context_type == "sticker":
             self.app.details_manager.update_details_panel()
             
        ToastNotification(self.app, "Tag Added", f"Added tag: {val}")

    def confirm_remove_tag(self, prefix, tag):
        # 1. Remove the tag from the specific item
        if prefix == "pack":
            if self.app.logic.current_pack_data and tag in self.app.logic.current_pack_data['tags']:
                self.app.logic.current_pack_data['tags'].remove(tag)
        elif prefix == "collection":
            if self.app.logic.selected_collection_data:
                root = self.app.logic.selected_collection_data['packs'][0]
                if tag in root.get('custom_collection_tags', []):
                    root['custom_collection_tags'].remove(tag)
        else:
            for s in self.app.logic.selected_stickers:
                if tag in s[0]['tags']: s[0]['tags'].remove(tag)
                
        # 2. TRIGGER REBUILD (The specific fix)
        self._rebuild_tag_cache()

        # 3. Save and Refresh
        self._save()
        
        # Update UI
        if prefix == "pack":
            self.app.details_manager.pack_layout.tags.render(self.app.logic.current_pack_data['tags'])
        elif prefix == "collection":
            root = self.app.logic.selected_collection_data['packs'][0]
            self.app.details_manager.collection_layout.tags.render(root.get('custom_collection_tags', []))
        else:
            self.app.details_manager.update_details_panel()

    def set_collection_cover(self, path_str: Optional[str]):
        sel_col = self.app.logic.selected_collection_data
        if not sel_col: return
        
        val = path_str if path_str else ""
        for p in sel_col['packs']:
            p['custom_collection_cover'] = val
        self._save() 
        
        col_id = f"collection_{sel_col['name']}"
        self.set_system_cover(col_id, val)

        sel_col['thumbnail_path'] = val
        
        self.app.details_manager.show_collection_details(sel_col)
        self.app.refresh_view()
        
        ToastNotification(self.app, "Cover Updated", "Collection cover changed.")

    def set_system_cover(self, key: str, path_str: Optional[str]):
        settings = load_json(SETTINGS_FILE)
        if "custom_covers" not in settings:
            settings["custom_covers"] = {}
            
        if path_str:
            settings["custom_covers"][key] = path_str
        else:
            if key in settings["custom_covers"]:
                del settings["custom_covers"][key]
                
        save_json(settings, SETTINGS_FILE)
        self.app.refresh_view()

    def open_collection_cover_selector(self):
        self.app.popup_manager.open_cover_selector_modal(
            "Collection Cover", 
            lambda path: self.set_collection_cover(path)
        )

    def open_cover_selector(self):
        def update_pack_cover(path):
            if not self.app.logic.current_pack_data: return
            if path is None:
                self.app.logic.current_pack_data['thumbnail_path'] = "" 
                if 'temp_thumbnail' in self.app.logic.current_pack_data:
                    del self.app.logic.current_pack_data['temp_thumbnail']
            else:
                self.app.logic.current_pack_data['thumbnail_path'] = path
            
            self._save()
            self.app.details_manager.show_pack_details(self.app.logic.current_pack_data)
            self.app.refresh_view()
            
            ToastNotification(self.app, "Cover Updated", "Pack cover changed.")

        self.app.popup_manager.open_cover_selector_modal("Pack Cover", update_pack_cover)

    # ==========================================================================
    #   DELETION
    # ==========================================================================

    def confirm_remove_pack(self):
        win = ctk.CTkToplevel(self.app)
        win.title("Confirm")
        win.geometry("300x150")
        
        from UI.ViewUtils import center_window, set_window_icon 
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
        if self.app.logic.current_pack_data in self.app.library_data:
            self.app.library_data.remove(self.app.logic.current_pack_data)
            
            # TRIGGER REBUILD: Ensure tags from this deleted pack are removed from global list
            self._rebuild_tag_cache()
            
            self._save()
            self.app.logic.current_pack_data = None
            self.app.logic.apply_filters()
            self.app.refresh_view()
            self.app.details_manager.pack_layout.hide()
            
            ToastNotification(self.app, "Success", "Pack Deleted Successfully.")

    # ==========================================================================
    #   FAVORITES
    # ==========================================================================

    def toggle_favorite(self, type_):
        if type_ == "pack":
            if self.app.logic.current_pack_data:
                state = not self.app.logic.current_pack_data.get('is_favorite')
                self.app.logic.current_pack_data['is_favorite'] = state
                self._save()
                
                layout = self.app.details_manager.pack_layout
                update_fav_btn(layout.fav_btn, state, COLORS)
                
        elif type_ == "collection":
            sel_col = self.app.logic.selected_collection_data
            if sel_col:
                state = not sel_col.get('is_favorite', False)
                sel_col['is_favorite'] = state
                for p in sel_col['packs']: p['is_favorite'] = state
                self._save()
                
                layout = self.app.details_manager.collection_layout
                update_fav_btn(layout.fav_btn, state, COLORS)
                
                self.app.logic.apply_filters()
                self.app.refresh_view()
        else:
            sel = self.app.logic.selected_stickers
            if not sel: return
            target_state = any(not s[0].get('is_favorite') for s in sel)
            for s in sel: s[0]['is_favorite'] = target_state
            self._save()
            self.app.details_manager.update_details_panel()
            
        self.app.refresh_view()