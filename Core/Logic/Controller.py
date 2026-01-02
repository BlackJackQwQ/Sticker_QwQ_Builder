import customtkinter as ctk
import random
from Core.Config import SETTINGS_FILE, save_json, load_json
from UI.ViewUtils import apply_theme_palette

# --- Import New Sub-Managers ---
from .Library import LibraryManager
from .Filters import FilterManager
from .Actions import ActionManager
from .Updater import UpdateManager

class AppLogic:
    """
    Central Coordinator.
    Directs traffic between the UI and the specialized Logic modules.
    Reduces the monolithic Logic.py by delegating responsibilities.
    """

    def __init__(self, app):
        self.app = app
        
        # --- Initialize Sub-Services ---
        self.lib = LibraryManager(app)       # Handles Data (Renaming, Merging, Deleting, Tags)
        self.filters = FilterManager(app)    # Handles Search, Sort, and Pagination
        self.actions = ActionManager(app)    # Handles OS Actions (Copy, Open File)
        self.updater = UpdateManager(app)    # Handles Network/Downloads
        
        # --- Shared State ---
        # These are kept here as they are fundamental app configurations
        self.current_theme_name: str = "Classic"
        self.nsfw_enabled: bool = False
        self.app_token: str = ""
        
        # Transient UI State (Selection)
        # We keep this here because it's shared across Actions, Library, and Filters
        self.selected_stickers = [] 
        self.current_pack_data = None
        self.current_sticker_data = None
        self.current_sticker_path = None
        self.current_collection_data = None
        
        # Selection state for collection views
        self.selected_collection_data = None

        # Custom Covers (Memory Cache)
        self.custom_covers = {}

        # Autocomplete sets (Populated by LibraryManager)
        self.pack_tags_ac = set()
        self.sticker_tags_ac = set()
        
        # History
        self.pack_search_history = []
        
        # Ensure library list exists on app
        if not hasattr(self.app, 'library_data'):
            self.app.library_data = []

    # ==========================================================================
    #   SETTINGS & SETUP
    # ==========================================================================

    def load_settings(self):
        """Loads basic app configuration."""
        data = load_json(SETTINGS_FILE)
        self.app_token = data.get("token", "")
        if hasattr(self.app, 'client'): 
            self.app.client.set_token(self.app_token)
            
        self.current_theme_name = data.get("theme_name", "Classic")
        apply_theme_palette(self.current_theme_name) 
        
        self.nsfw_enabled = data.get("nsfw_enabled", False)
        
        # Load Custom Covers into memory
        self.custom_covers = data.get("custom_covers", {})
        
        # Pass relevant settings to sub-managers
        self.filters.sort_by = data.get("sort_by", "Recently Added")

    def save_settings(self):
        """Saves current config to file."""
        data = {
            "token": self.app.client.token if hasattr(self.app, 'client') else "",
            "theme_name": self.current_theme_name,
            "nsfw_enabled": self.nsfw_enabled,
            # Preserve any unknown data that might be in the file
            "custom_theme_data": load_json(SETTINGS_FILE).get("custom_theme_data", {}),
            # Save memory cache back to file
            "custom_covers": self.custom_covers
        }
        save_json(data, SETTINGS_FILE)

    def save_new_theme_and_restart(self, new_theme: str):
        self.current_theme_name = new_theme
        self.save_settings()
        self.app.restart_app()

    def load_library_data(self):
        """Delegates loading to Library Manager, then refreshes filters."""
        self.lib.load_library_data()
        self.filters.apply_filters()

    # ==========================================================================
    #   DELEGATES: LIBRARY MANAGEMENT (Write Operations)
    # ==========================================================================
    
    # Renaming
    def rename_pack_local(self, new_name): return self.lib.rename_pack_local(new_name)
    def toggle_rename_pack_ui(self): return self.lib.toggle_rename_pack_ui()
    def rename_collection_from_detail(self, new_name): return self.lib.rename_collection_from_detail(new_name)
    def toggle_rename_collection_ui(self): return self.lib.toggle_rename_collection_ui()
    def toggle_rename(self): return self.lib.toggle_rename_sticker() # Logic for sticker renaming

    # Structure (Merging/Linking)
    def merge_packs(self, a, b): return self.lib.merge_packs(a, b)
    def link_pack(self, target): return self.lib.link_pack(target)
    def unlink_pack(self, target): return self.lib.unlink_pack(target)
    def add_packs_to_collection_by_tname(self, names): return self.lib.add_packs_to_collection_by_tname(names)
    def remove_pack_from_collection(self, tname): return self.lib.remove_pack_from_collection(tname)
    def disband_collection(self): return self.lib.disband_collection()
    def get_linked_pack_collection(self, root): return self.filters.get_linked_pack_collection(root) 

    # Tags
    def add_tag_manual(self, context, tag): return self.lib.add_tag_manual(context, tag)
    def confirm_remove_tag(self, context, tag): return self.lib.confirm_remove_tag(context, tag)
    
    # Covers
    def set_collection_cover(self, path): return self.lib.set_collection_cover(path)
    def open_collection_cover_selector(self): return self.lib.open_collection_cover_selector()
    def open_cover_selector(self): return self.lib.open_cover_selector() # For packs
    
    # System Covers (All Stickers/Collections)
    def set_system_cover(self, key, path): 
        # Update memory cache instantly
        if path:
            self.custom_covers[key] = path
        elif key in self.custom_covers:
            del self.custom_covers[key]
            
        return self.lib.set_system_cover(key, path)

    # Deletion
    def confirm_remove_pack(self): return self.lib.confirm_remove_pack()
    def perform_remove(self): return self.lib.perform_remove()

    # Favorites
    def toggle_favorite(self, type_): return self.lib.toggle_favorite(type_)

    # ==========================================================================
    #   DELEGATES: FILTERS & VIEW (Read Operations)
    # ==========================================================================

    def apply_filters(self): return self.filters.apply_filters()
    def reset_filters(self): return self.filters.reset_filters()
    def on_filter_change(self, val=None): return self.filters.on_filter_change(val)
    
    # Pagination
    def change_page(self, direction): return self.filters.change_page(direction)
    def set_items_per_page(self, value): return self.filters.set_items_per_page(value)
    def get_current_page_items(self): return self.filters.get_current_page_items()
    
    # Stats properties (delegated to filter manager)
    @property
    def total_items(self): return self.filters.total_items
    @property
    def total_pages(self): return self.filters.total_pages
    @property
    def current_page(self): 
        return self.filters.current_page
    @current_page.setter
    def current_page(self, value):
        self.filters.current_page = value

    # Search
    def on_search(self, e=None): return self.filters.on_search(e)
    def clear_search(self): return self.filters.clear_search()
    def show_search_history(self): return self.filters.show_search_history()
    
    # Filter Tags
    def add_filter_tag_direct(self, tag, mode): return self.filters.add_filter_tag_direct(tag, mode)
    def remove_filter_tag(self, tag, mode): return self.filters.remove_filter_tag(tag, mode)
    def get_tag_usage(self): return self.filters.get_tag_usage()
    def get_most_used_stickers(self, limit=10): return self.filters.get_most_used_stickers(limit)
    def open_usage_stats(self): return self.filters.open_usage_stats()
    
    # Properties needed by UI for state reading
    @property
    def sort_by(self): return self.filters.sort_by
    @sort_by.setter
    def sort_by(self, val): self.filters.sort_by = val
    
    @property
    def sort_order(self): return self.filters.sort_order
    @sort_order.setter
    def sort_order(self, val): self.filters.sort_order = val

    @property
    def only_favorites(self): return self.filters.only_favorites
    @only_favorites.setter
    def only_favorites(self, val): self.filters.only_favorites = val
    
    @property
    def include_tags(self): return self.filters.include_tags
    @property
    def exclude_tags(self): return self.filters.exclude_tags
    
    @property
    def filter_file_type(self): return self.filters.filter_file_type
    @property
    def filter_tag_mode(self): return self.filters.filter_tag_mode

    # Helpers
    def _create_virtual_folder(self, packs): return self.filters._create_virtual_folder(packs)

    # ==========================================================================
    #   DELEGATES: ACTIONS (OS Interactions)
    # ==========================================================================

    def copy_sticker(self): return self.actions.copy_sticker()
    def show_file(self): return self.actions.show_file()
    def open_url(self, e=None): return self.actions.open_url(e)
    def select_random_sticker(self): return self.actions.select_random_sticker()

    # ==========================================================================
    #   DELEGATES: UPDATER (Network)
    # ==========================================================================

    def add_pack_from_url(self, urls): return self.updater.add_pack_from_url(urls)
    def trigger_redownload(self): return self.updater.trigger_redownload()
    def update_all_packs(self): return self.updater.update_all_packs()

    # ==========================================================================
    #   UI NAVIGATION (Handled directly here or routed)
    # ==========================================================================

    def on_sticker_click(self, sticker_data, idx, path, pack_tname, event=None):
        """
        Handles selection logic. 
        Kept in Controller because it touches shared selection state heavily.
        """
        is_ctrl = event and (event.state & 4 or event.state & 0x20000)
        item = (sticker_data, idx, path, pack_tname)
        
        if is_ctrl:
            # Toggle selection if Ctrl is held
            exists = next((i for i, s in enumerate(self.selected_stickers) if s[0] is sticker_data), -1)
            if exists != -1: 
                self.selected_stickers.pop(exists)
            else: 
                self.selected_stickers.append(item)
        else:
            # Single selection
            self.selected_stickers = [item]

        # Update pointers for Detail Panel
        if self.selected_stickers:
            last = self.selected_stickers[-1]
            self.current_sticker_data = last[0]
            self.current_sticker_path = last[2]
        else:
            self.current_sticker_data = None
            
        # Refresh UI components
        if hasattr(self.app, 'card_manager'): 
            self.app.card_manager.highlight_selected_cards()
        if hasattr(self.app, 'details_manager'): 
            self.app.details_manager.update_details_panel()

    def open_collection(self, folder_data):
        self.current_collection_data = folder_data
        self.app.show_collection_view()

    def show_collection_details(self, folder_data):
        self.selected_collection_data = folder_data
        self.app.details_manager.show_collection_details(folder_data)

    def select_startup_item(self):
        """
        Auto-selects a random Pack or Collection on startup to populate the sidebar.
        This mirrors the 'Library View' logic:
        - It includes standalone Packs.
        - It includes Virtual Collections (as one item).
        - It EXCLUDES packs that are inside a collection.
        - It EXCLUDES the virtual 'All Stickers' card.
        """
        if not self.app.library_data:
            return

        candidates = []
        processed_tnames = set()
        
        # 1. Build the list of valid Top-Level items (Packs & Collections)
        for p in self.app.library_data:
            tname = p['t_name']
            if tname in processed_tnames: continue
            
            # Check relationships using FilterManager logic
            links = self.filters.get_linked_pack_collection(p)
            
            if len(links) > 1:
                # IT IS A COLLECTION
                # Create the virtual folder object exactly like the view does
                folder_obj = self.filters._create_virtual_folder(links)
                candidates.append({"type": "collection", "data": folder_obj})
                
                # Mark all packs inside this collection as processed so they don't appear individually
                for lp in links: processed_tnames.add(lp['t_name'])
            else:
                # IT IS A SINGLE PACK
                candidates.append({"type": "pack", "data": p})
                processed_tnames.add(tname)
        
        if not candidates: return

        # 2. Pick one at random
        choice = random.choice(candidates)
        
        # 3. Route to the correct Detail View
        # INCREASED DELAY to 600ms to allow Main Window to stabilize geometry
        if choice["type"] == "collection":
            self.selected_collection_data = choice["data"]
            self.app.after(600, lambda: self.app.details_manager.show_collection_details(choice["data"]))
        else:
            self.current_pack_data = choice["data"]
            self.app.after(600, lambda: self.app.details_manager.show_pack_details(choice["data"]))