import customtkinter as ctk
from typing import Dict, Any

from UI.ViewUtils import COLORS
from UI.DetailPanel.AsyncLoader import AsyncLoader
from UI.DetailPanel.Layouts import PackLayout, CollectionLayout, StickerLayout

class DetailsController:
    """
    The "Brain" of the Detail Panel.
    
    Responsibilities:
    1. Initializes the shared AsyncLoader (Image Engine).
    2. Instantiates the three main View Layouts (Pack, Collection, Sticker).
    3. Handles the routing/switching logic between these views.
    4. Acts as the public interface for MainWindow to call.
    """

    def __init__(self, app, container: ctk.CTkFrame):
        self.app = app
        self.container = container
        
        # --- 1. SHARED ENGINE ---
        # Handles background image/video loading for all child layouts.
        self.loader = AsyncLoader(app)
        
        # --- 2. LAYOUTS (THE SKELETON) ---
        # We pass 'self.app' and 'self.loader' so layouts can use the engine.
        # Layouts are instantiated here but kept hidden until needed.
        self.pack_layout = PackLayout(self.app, self.container, self.loader)
        self.collection_layout = CollectionLayout(self.app, self.container, self.loader)
        self.sticker_layout = StickerLayout(self.app, self.container, self.loader)

        # Ensure everything is hidden initially
        self.pack_layout.hide()
        self.collection_layout.hide()
        self.sticker_layout.hide()

    # ==========================================================================
    #   PUBLIC ROUTING METHODS (Called by MainWindow/Logic)
    # ==========================================================================

    def show_pack_details(self, pack_data: Dict[str, Any]):
        """
        Route: Pack View
        Hides others, Shows Pack, Triggers Data Refresh.
        """
        # Ensure Logic state is synced (redundant safety)
        self.app.logic.current_pack_data = pack_data
        
        # 1. Switch Visibility
        self.collection_layout.hide()
        self.sticker_layout.hide()
        self.pack_layout.show()
        
        # 2. Populate Data
        # We generate a new 'load_id' in the loader to invalidate old image requests
        load_id = self.loader.get_new_load_id()
        self.pack_layout.refresh(pack_data, load_id)

    def show_collection_details(self, folder_data: Dict[str, Any]):
        """
        Route: Collection View
        Hides others, Shows Collection, Triggers Data Refresh.
        """
        self.app.logic.selected_collection_data = folder_data
        
        # 1. Switch Visibility
        self.pack_layout.hide()
        self.sticker_layout.hide()
        self.collection_layout.show()
        
        # 2. Populate Data
        load_id = self.loader.get_new_load_id()
        self.collection_layout.refresh(folder_data, load_id)

    def update_details_panel(self):
        """
        Route: Sticker View
        Hides others, Shows Sticker (Single or Batch), Triggers Data Refresh.
        """
        # 1. Switch Visibility
        self.pack_layout.hide()
        self.collection_layout.hide()
        self.sticker_layout.show()
        
        # 2. Populate Data
        load_id = self.loader.get_new_load_id()
        self.sticker_layout.refresh(load_id)