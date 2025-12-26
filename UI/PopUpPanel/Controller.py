import customtkinter as ctk
from typing import Optional, Callable, List

# Sub-Popup Modules
from UI.PopUpPanel.MainWindowPopUp import MainWindowPopUp
from UI.PopUpPanel.DetailPopUp import DetailPopUp
from UI.PopUpPanel.FilterPopUp import FilterPopUp

class PopUpManager:
    """
    The Facade Controller for all application modals.
    Replaces the old monolithic PopUp.py.
    
    It routes requests to specialized handlers based on where the popup originates:
    1. MainWindowPopUp (Header/Global)
    2. DetailPopUp (Right Sidebar)
    3. FilterPopUp (Left Sidebar)
    """

    def __init__(self, app):
        self.app = app
        
        # Initialize Sub-Managers
        self.main_popup = MainWindowPopUp(app)
        self.detail_popup = DetailPopUp(app)
        self.filter_popup = FilterPopUp(app)

    # ==========================================================================
    #   ROUTE TO: MainWindowPopUp (Global/Header Actions)
    # ==========================================================================

    def open_settings_modal(self):
        self.main_popup.open_settings_modal()

    def open_token_tutorial_modal(self):
        self.main_popup.open_token_tutorial_modal()

    def open_add_pack_modal(self):
        self.main_popup.open_add_pack_modal()

    def open_update_modal(self, run_func: Callable):
        self.main_popup.open_update_modal(run_func)
        
    def show_search_history(self, history_list: List[str]):
        self.main_popup.show_search_history(history_list)

    def open_usage_stats_modal(self):
        self.main_popup.open_usage_stats_modal()

    # ==========================================================================
    #   ROUTE TO: DetailPopUp (Right Sidebar Actions)
    # ==========================================================================

    def open_cover_selector_modal(self, title: str, callback: Callable):
        self.detail_popup.open_cover_selector_modal(title, callback)

    def open_collection_edit_modal(self):
        self.detail_popup.open_collection_edit_modal()
        
    def open_link_pack_modal(self):
        self.detail_popup.open_link_pack_modal()

    # ==========================================================================
    #   ROUTE TO: FilterPopUp (Left Sidebar Actions)
    # ==========================================================================

    def open_tag_manager_modal(self, context_type: str):
        self.filter_popup.open_tag_manager_modal(context_type)

    def open_all_tags_modal(self):
        self.filter_popup.open_all_tags_modal()