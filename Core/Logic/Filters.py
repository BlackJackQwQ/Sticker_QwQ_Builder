import random
from typing import List, Dict, Any, Optional

from UI.ViewUtils import is_system_tag

class FilterManager:
    """
    The Search Engine.
    Responsible for Filtering, Sorting, Pagination, and View Logic.
    Does NOT modify the data structure.
    """
    
    def __init__(self, app):
        self.app = app
        
        # Filter State
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

    # ==========================================================================
    #   CORE LOGIC
    # ==========================================================================

    def apply_filters(self):
        """The main loop that determines what items are shown in the grid."""
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
                
                # Check for Virtual Collections (Links)
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
                    
                    # Tag filtering on collections is based on the root pack's custom tags
                    if not check_tags(links[0].get('custom_collection_tags', [])): continue

                    # Mark all inside as processed
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
                
                def get_sort_key(x):
                    val = x.get(key, 0)
                    if isinstance(val, str): return val.lower()
                    return val

                display_items.sort(key=get_sort_key, reverse=is_desc)

            self.app.filtered_library = display_items

        elif self.app.view_mode == "collection":
            # Inside a collection, we show the packs it contains
            if self.app.logic.current_collection_data:
                raw_packs = self.app.logic.current_collection_data['packs'] 
                
                # Filter packs within collection
                filtered_packs = []
                for p in raw_packs:
                    if self.search_query and self.search_query not in p.get('name','').lower(): continue
                    if self.only_favorites and not p.get('is_favorite'): continue
                    if not check_tags(p.get('tags', [])): continue
                    filtered_packs.append(p)

                self.app.filtered_library = sorted(filtered_packs, key=lambda x: x.get('name',''), reverse=is_desc)
            else:
                self.app.filtered_library = []

        else:
            # Gallery Mode (Stickers)
            self._apply_sticker_filters()

    def _create_virtual_folder(self, packs: List[Dict]) -> Dict:
        """Creates a temporary object representing a folder of packs."""
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
        """Filters individual stickers when in Gallery View."""
        is_desc = (self.sort_order == "Descending")
        raw = []
        pool = []
        
        if self.app.view_mode == "gallery_collection":
            if self.app.logic.current_collection_data:
                pool = self.app.logic.current_collection_data['packs']
        elif self.app.logic.current_pack_data:
            pool = [self.app.logic.current_pack_data]
        else:
            pool = self.app.library_data
            
        # Flatten structure into a list of tuples: (sticker_dict, pack_tname, index_in_pack)
        for p in pool:
            if not self.app.logic.nsfw_enabled and "NSFW" in p.get('tags', []): continue
            for i, s in enumerate(p.get('stickers', [])):
                raw.append((s, p['t_name'], i))

        results = []
        for item in raw:
            s, pack_tname, idx = item
            tags = s.get('tags', [])
            
            # Apply Filters
            if self.only_favorites and not s.get('is_favorite'): continue
            if not self.app.logic.nsfw_enabled and "NSFW" in tags: continue
            
            if self.filter_file_type != "All":
                if self.filter_file_type == "Animated" and "Animated" not in tags: continue
                if self.filter_file_type == "Static" and "Static" not in tags: continue
            
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

        # Apply Sort
        if self.sort_by == "Usage":
            results.sort(key=lambda x: x[0].get('usage_count', 0), reverse=is_desc)
        elif self.sort_by == "Random":
            random.shuffle(results)
        else:
            # Sort by Pack Name then Index (Index Logic)
            results.sort(key=lambda x: (x[1], x[2]), reverse=is_desc)
            
        self.app.filtered_stickers = results

    def get_linked_pack_collection(self, root_pack: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Helper to recursively find all packs linked to a root pack."""
        # This uses the app's library_data source of truth
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
    #   PAGINATION
    # ==========================================================================

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

    # ==========================================================================
    #   SEARCH & TAG CONTROLS
    # ==========================================================================

    def on_search(self, e=None):
        self.search_query = self.app.search_entry.get().lower()
        if self.search_query and self.search_query not in self.app.logic.pack_search_history:
             self.app.logic.pack_search_history.append(self.search_query)
        self.current_page = 1
        self.apply_filters()
        self.app.refresh_view()
    
    def clear_search(self):
        self.app.search_entry.delete(0, "end")
        self.on_search()
        
    def show_search_history(self):
        h = self.app.logic.pack_search_history 
        self.app.popup_manager.show_search_history(h)

    def reset_filters(self):
        self.sort_by = "Recently Added"
        self.sort_order = "Descending"
        self.only_favorites = False
        self.filter_file_type = "All"
        self.search_query = ""
        self.include_tags.clear()
        self.exclude_tags.clear()
        
        # Reset UI elements
        self.app.filter_manager.refresh_ui()
        self.app.search_entry.delete(0, "end")
        
        self.apply_filters()
        self.app.refresh_view()

    def on_filter_change(self, val=None):
        mgr = self.app.filter_manager
        self.sort_by = mgr.sort_opt.get()
        self.sort_order = mgr.order_opt.get()
        self.app.logic.nsfw_enabled = bool(mgr.nsfw_switch.get()) # Update logic state
        self.only_favorites = bool(mgr.fav_switch.get())
        self.filter_file_type = mgr.file_type_seg.get()
        self.filter_tag_mode = mgr.tag_match_seg.get()
        
        self.app.logic.save_settings()
        self.current_page = 1 
        self.apply_filters()
        self.app.refresh_view()

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

    # ==========================================================================
    #   STATISTICS
    # ==========================================================================

    def get_tag_usage(self):
        """
        Calculates tag frequency for the current view context.
        FIX: Explicitly differentiate between Pack Tags and Sticker Tags based on view mode.
        """
        usage = {}
        view_mode = self.app.view_mode
        
        # Case A: Sticker View (Gallery)
        if view_mode in ["gallery_pack", "gallery_collection"]:
            # Decide pool of stickers
            if view_mode == "gallery_pack" and self.app.logic.current_pack_data:
                # View: Single Pack Stickers
                pool = [self.app.logic.current_pack_data]
            elif view_mode == "gallery_collection" and self.app.logic.current_collection_data:
                # View: All Stickers in Collection
                pool = self.app.logic.current_collection_data.get('packs', [])
            else:
                # View: All Library Stickers (fallback)
                pool = self.app.library_data
                
            for p in pool:
                for s in p.get('stickers', []):
                    for t in s.get('tags', []): 
                        usage[t] = usage.get(t, 0) + 1

        # Case B: Pack/Collection View (Library)
        else:
            # Decide pool of packs
            if view_mode == "collection" and self.app.logic.current_collection_data:
                # View: Packs inside a Collection -> Show PACK tags
                pool = self.app.logic.current_collection_data.get('packs', [])
            else:
                # View: Library -> Show PACK tags from all packs
                # Note: We iterate ALL packs in library to show global pack tag frequency
                pool = self.app.library_data
            
            for p in pool:
                # Add Pack Tags
                for t in p.get('tags', []): 
                    usage[t] = usage.get(t, 0) + 1
                
                # Add Collection Tags (if applicable)
                # Usually collection tags are stored on the root pack
                for t in p.get('custom_collection_tags', []):
                    usage[t] = usage.get(t, 0) + 1

        return usage
        
    def get_most_used_stickers(self, limit=10):
        # Scan entire library for usage stats
        from Core.Config import BASE_DIR, LIBRARY_FOLDER # Import here to avoid cycle
        
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