import customtkinter as ctk
import random  # <--- Added for random selection
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
        
        # Pass relevant settings to sub-managers
        self.filters.sort_by = data.get("sort_by", "Recently Added")

    def save_settings(self):
        """Saves current config to file."""
        data = {
            "token": self.app.client.token if hasattr(self.app, 'client') else "",
            "theme_name": self.current_theme_name,
            "nsfw_enabled": self.nsfw_enabled,
            # Preserve any unknown data that might be in the file
            "custom_theme_data": load_json(SETTINGS_FILE).get("custom_theme_data", {})
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
    def get_linked_pack_collection(self, root): return self.filters.get_linked_pack_collection(root) # Note: Read-op often in Filters/Library

    # Tags
    def add_tag_manual(self, context, tag): return self.lib.add_tag_manual(context, tag)
    def confirm_remove_tag(self, context, tag): return self.lib.confirm_remove_tag(context, tag)
    
    # Covers
    def set_collection_cover(self, path): return self.lib.set_collection_cover(path)
    def open_collection_cover_selector(self): return self.lib.open_collection_cover_selector()
    def open_cover_selector(self): return self.lib.open_cover_selector() # For packs

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
        Auto-selects a random pack on startup to populate the sidebar.
        Fixes the empty/collapsed sidebar glitch.
        """
        if not self.app.library_data:
            return

        # Pick a random pack
        pack = random.choice(self.app.library_data)
        self.current_pack_data = pack
        
        # Update UI via DetailsManager
        # We use 'after' to ensure UI is fully ready if called during init chain
        self.app.after(100, lambda: self.app.details_manager.show_pack_details(pack))