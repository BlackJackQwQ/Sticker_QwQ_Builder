import customtkinter as ctk
from typing import Dict, Any

# Import sibling modules (we will create these next)
import UI.CardsPanel.Builders as Builders
from UI.CardsPanel.Utils import CardUtils

class CardManager:
    """
    The Traffic Controller for Card Generation.
    
    Responsibilities:
    1. Acts as the public interface for MainWindow.
    2. Initializes the Shared Utils engine (animations, hover effects).
    3. Routes specific card creation requests to the Builders module.
    """

    def __init__(self, app):
        self.app = app
        # Initialize the core mechanics engine
        self.utils = CardUtils(app)

    def refresh_theme_colors(self):
        """Pass-through to Utils to update color references."""
        self.utils.refresh_theme_colors()

    def highlight_selected_cards(self):
        """Updates border colors based on selection state."""
        self.utils.highlight_selected_cards()

    def update_card_image(self, card, new_size):
        """Called by MainWindow during resize events."""
        self.utils.update_card_image(card, new_size)

    # ==========================================================================
    #   BUILDER ROUTING
    #   (MainWindow calls these -> Controller routes to Builders.py)
    # ==========================================================================

    def create_add_card(self, index: int, is_sticker: bool = False):
        Builders.create_add_card(self.app, self.utils, index, is_sticker)

    def create_all_stickers_card(self, index: int):
        Builders.create_all_stickers_card(self.app, self.utils, index)

    def create_all_stickers_in_collection_card(self, index: int):
        Builders.create_all_stickers_in_collection_card(self.app, self.utils, index)

    def create_folder_card(self, index: int, folder_data: Dict[str, Any]):
        Builders.create_folder_card(self.app, self.utils, index, folder_data)

    def create_pack_card(self, index: int, pack_data: Dict[str, Any]):
        Builders.create_pack_card(self.app, self.utils, index, pack_data)

    def create_sticker_card(self, index: int, sticker_data: Dict[str, Any], pack_tname: str, idx_in_pack: int):
        Builders.create_sticker_card(self.app, self.utils, index, sticker_data, pack_tname, idx_in_pack)