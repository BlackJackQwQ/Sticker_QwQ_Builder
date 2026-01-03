import customtkinter as ctk
import sys
import os
import threading
from pathlib import Path
from typing import Optional

# Core Imports
from Core.Backend import StickerClient
from Core.Logic.Controller import AppLogic
from Core.Config import initialize_system_files, logger, BASE_DIR

# Resource Imports
from Resources.Icons import (
    FONT_BIG_HEADER, FONT_NORMAL, FONT_SMALL, FONT_TITLE,
    ICON_LEFT, ICON_RIGHT, ICON_SETTINGS, 
    ICON_UPDATE, ICON_CLEAR, ICON_HISTORY,
    ICON_RANDOM, ICON_STATS,
    CARD_PADDING
)
from Resources.Themes import THEME_PALETTES

# UI Component Imports
from UI.ViewUtils import COLORS, set_window_icon
from UI.CardsPanel.Controller import CardManager
from UI.Filters import FilterManager
from UI.PopUpPanel.Controller import PopUpManager
from UI.DetailPanel.Controller import DetailsController

class StickerBotApp(ctk.CTk):
    """
    Main Application with 3-Row Header Layout and Navigation Stack.
    """

    def __init__(self):
        super().__init__()
        
        logger.info("Starting Application...")
        initialize_system_files()
        
        # 1. Initialize Core Engines
        self.client = StickerClient(token="") 
        self.logic = AppLogic(self)
        self.logic.load_settings() 
        
        # 2. Window Setup
        self.title("Sticker QwQ Manager")
        self.geometry("1100x750")
        self.minsize(800, 600)
        
        # 3. Theme Setup
        self.current_theme = "Classic" 
        self.configure(fg_color=COLORS.get("bg_main", "#202020")) 
        
        self.after(200, lambda: set_window_icon(self))
        
        self.grid_columnconfigure(0, minsize=0) 
        self.grid_columnconfigure(1, weight=1)  
        self.grid_columnconfigure(2, minsize=0) 
        self.grid_rowconfigure(0, weight=1)

        # --- VIEW STATE ---
        self.view_mode = "library" 
        self.view_stack = []
        # Default to Normal, but allow persistence if needed later
        self.current_layout_mode = "Normal"
        
        self.left_sidebar_visible = True
        self.right_sidebar_visible = True
        self.content_columns = 1 
        self.cards = [] 
        self.resize_timer = None
        self.last_width = 0

        # --- MANAGERS ---
        self.popup_manager = PopUpManager(self)
        self.card_manager = CardManager(self)
        
        # 4. Build UI
        self._build_filter_sidebar()
        self._build_main_display()
        self._build_detail_sidebar()
        
        # 5. ASYNC BOOTSTRAP (Performance Fix)
        # Instead of blocking the UI to load data, we schedule it.
        self.after(100, self._start_background_loading)

    def _start_background_loading(self):
        """Starts the library loading in a separate thread to prevent UI freeze."""
        self.update_status_bar("Loading Library...", 0.1)
        
        # Show a temporary loading spinner/text in the canvas
        self.loading_label = ctk.CTkLabel(self.main_frame, text="Loading Library...", font=FONT_BIG_HEADER, text_color=COLORS["text_sub"])
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
        
        def load_task():
            # Heavy IO operation
            self.logic.load_library_data()
            # Once done, schedule UI update on main thread
            self.after(0, self._on_loading_complete)
            
        threading.Thread(target=load_task, daemon=True).start()

    def _on_loading_complete(self):
        """Called when data is ready."""
        if hasattr(self, 'loading_label'):
            self.loading_label.destroy()
            
        self.update_status_bar("Ready")
        
        if not self.client.token:
            self.after(500, lambda: self.popup_manager.open_settings_modal())
            
        # Use existing mode if set, otherwise default.
        target_mode = self.current_layout_mode if self.current_layout_mode else "Normal"
        
        # Sync the segmented button visual state
        if hasattr(self, 'view_options'):
            self.view_options.set(target_mode)
            
        # FIX: Directly call refresh_view if mode hasn't changed.
        # Calling change_layout_mode would reset self.last_width = 0 and force a resize calculation.
        if self.current_layout_mode == target_mode:
            self.refresh_view()
        else:
            self.change_layout_mode(target_mode)
        
        # FIX 2: Explicitly refresh the filter sidebar tags now that data is loaded
        if hasattr(self.filter_manager, 'refresh_tag_buttons'):
            self.filter_manager.refresh_tag_buttons()
        # Fallback if method name is different in older versions, usually it's handled by reset/apply
        elif hasattr(self.filter_manager, 'reset_all'):
             self.filter_manager.reset_all()

        # FIX: Auto-select a random pack to populate the sidebar
        self.logic.select_startup_item()

    # ==========================================================================
    #   LAYOUT CONSTRUCTION
    # ==========================================================================

    def _build_filter_sidebar(self):
        self.filter_frame = ctk.CTkFrame(self, corner_radius=0, width=240, fg_color=COLORS["bg_sidebar"])
        self.filter_frame.grid(row=0, column=0, sticky="nsew")
        self.filter_frame.grid_columnconfigure(0, weight=1)
        self.filter_frame.grid_rowconfigure(0, weight=1)
        self.filter_manager = FilterManager(self, self.filter_frame)

    def _build_detail_sidebar(self):
        """Right Sidebar: Detail Views."""
        self.sidebar_container = ctk.CTkFrame(self, corner_radius=0, width=320, fg_color=COLORS["bg_sidebar"])
        self.sidebar_container.grid(row=0, column=2, sticky="nsew")
        self.sidebar_container.grid_columnconfigure(0, weight=1)
        self.sidebar_container.grid_rowconfigure(0, weight=1)
        
        self.details_manager = DetailsController(self, self.sidebar_container)

    def _build_main_display(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1) # Canvas expands

        # --- ROW 1: GLOBAL ACTIONS (Top Bar) ---
        self.header_actions = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=45)
        self.header_actions.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.header_actions.grid_columnconfigure(2, weight=1) # Spacer

        # Left Toggle
        self.toggle_left_btn = ctk.CTkButton(self.header_actions, text=ICON_LEFT, width=35, height=35, fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"], text_color=COLORS["text_main"], command=self.toggle_left_sidebar)
        self.toggle_left_btn.pack(side="left", padx=5)

        # Back Button (Initially Hidden, packed dynamically)
        self.back_btn = ctk.CTkButton(self.header_actions, text="< Back", width=80, height=35, fg_color=COLORS["btn_neutral"], hover_color=COLORS["card_hover"], text_color=COLORS["text_main"], command=self.go_back)

        # Global Tools (Right Side)
        self.toggle_right_btn = ctk.CTkButton(self.header_actions, text=ICON_RIGHT, width=35, height=35, fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"], text_color=COLORS["text_main"], command=self.toggle_right_sidebar)
        self.toggle_right_btn.pack(side="right", padx=5)
        
        # Action Buttons (Right to Left)
        ctk.CTkButton(self.header_actions, text=ICON_UPDATE, width=35, height=35, fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"], text_color=COLORS["text_main"], command=self.logic.update_all_packs).pack(side="right", padx=5)
        ctk.CTkButton(self.header_actions, text=ICON_SETTINGS, width=35, height=35, fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"], text_color=COLORS["text_main"], command=self.popup_manager.open_settings_modal).pack(side="right", padx=5)
        ctk.CTkButton(self.header_actions, text=ICON_RANDOM, width=35, height=35, fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"], text_color=COLORS["text_main"], command=self.logic.select_random_sticker).pack(side="right", padx=5)
        ctk.CTkButton(self.header_actions, text=ICON_STATS, width=35, height=35, fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"], text_color=COLORS["text_main"], command=self.logic.open_usage_stats).pack(side="right", padx=5)


        # --- ROW 2: CONTEXT TITLE (Middle Bar) ---
        self.header_title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=50)
        self.header_title_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        self.header_title_label = ctk.CTkLabel(self.header_title_frame, text="Packs Library", font=FONT_BIG_HEADER, text_color=COLORS["text_main"])
        self.header_title_label.pack(side="left", padx=15)
        
        self.header_subtitle_label = ctk.CTkLabel(self.header_title_frame, text="", font=FONT_NORMAL, text_color=COLORS["text_sub"])
        self.header_subtitle_label.pack(side="left", padx=10, pady=(10, 0))


        # --- ROW 3: CONTROLS (Bottom Bar - Search, Page, View) ---
        self.controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.controls_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.controls_frame.grid_columnconfigure(0, weight=1)

        # Search Group
        search_group = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        search_group.grid(row=0, column=0, sticky="ew")
        
        self.search_entry = ctk.CTkEntry(search_group, placeholder_text="Search...", height=35, font=FONT_NORMAL, corner_radius=10, fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], text_color=COLORS["entry_text"])
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", self.logic.on_search)
        
        ctk.CTkButton(search_group, text=ICON_CLEAR, width=35, height=35, fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"], text_color=COLORS["text_main"], command=self.logic.clear_search).pack(side="left", padx=2)
        ctk.CTkButton(search_group, text=ICON_HISTORY, width=35, height=35, fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"], text_color=COLORS["text_main"], command=self.logic.show_search_history).pack(side="left")

        # View Controls Group
        view_ctrl_group = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        view_ctrl_group.grid(row=0, column=1, sticky="e")
        
        self.page_prev_btn = ctk.CTkButton(view_ctrl_group, text="<", width=30, height=35, fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"], text_color=COLORS["text_main"], command=lambda: self.logic.change_page("prev"))
        self.page_prev_btn.pack(side="left", padx=2)
        
        self.page_label = ctk.CTkLabel(view_ctrl_group, text="1 / 1", font=FONT_SMALL, text_color=COLORS["text_sub"], width=50)
        self.page_label.pack(side="left", padx=2)
        
        self.page_next_btn = ctk.CTkButton(view_ctrl_group, text=">", width=30, height=35, fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"], text_color=COLORS["text_main"], command=lambda: self.logic.change_page("next"))
        self.page_next_btn.pack(side="left", padx=(2, 15))

        # View Mode Segmented Button
        self.view_options = ctk.CTkSegmentedButton(view_ctrl_group, values=["Large", "Normal", "Small", "List"], command=self.change_layout_mode, height=35, corner_radius=10, selected_color=COLORS["seg_selected"], selected_hover_color=COLORS["seg_selected"], unselected_color=COLORS["seg_fg"], unselected_hover_color=COLORS["card_hover"], text_color=COLORS["seg_text"])
        self.view_options.set(self.current_layout_mode) # Set initial state correctly
        self.view_options.pack(side="left")

        # --- CONTENT AREA (Canvas) ---
        self.scroll_wrapper = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.scroll_wrapper.grid(row=3, column=0, sticky="nsew")
        self.scroll_wrapper.grid_columnconfigure(0, weight=1)
        self.scroll_wrapper.grid_rowconfigure(0, weight=1)

        self.canvas = ctk.CTkCanvas(self.scroll_wrapper, bg=COLORS["bg_main"], highlightthickness=0, bd=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = ctk.CTkScrollbar(self.scroll_wrapper, orientation="vertical", command=self.canvas.yview, fg_color="transparent", button_color=COLORS["scrollbar_fg"], button_hover_color=COLORS["scrollbar_hover"])
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.content_area = ctk.CTkFrame(self.canvas, fg_color="transparent")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_area, anchor="nw")

        self.content_area.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.scroll_wrapper.bind("<Enter>", self._bind_mouse_wheel)
        self.scroll_wrapper.bind("<Leave>", self._unbind_mouse_wheel)

        # --- STATUS BAR ---
        self.status_bar = ctk.CTkFrame(self.main_frame, height=30, fg_color=COLORS["card_bg"], corner_radius=5)
        self.status_bar.grid(row=4, column=0, sticky="ew", pady=(5, 0))
        self.status_bar.grid_columnconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready", font=FONT_SMALL, text_color=COLORS["text_sub"])
        self.status_label.grid(row=0, column=0, padx=15, sticky="w")
        self.status_prog = ctk.CTkProgressBar(self.status_bar, width=150, height=10, progress_color=COLORS["accent"])
        self.status_prog.grid(row=0, column=2, padx=15, sticky="e")
        self.status_prog.grid_remove() 

    # ==========================================================================
    #   NAVIGATION & VIEW LOGIC
    # ==========================================================================

    def navigate_to(self, mode: str, title: str = ""):
        """Central Navigation Handler."""
        if self.view_mode != mode:
            # Push current state to stack before changing
            current_title = self.header_title_label.cget("text")
            self.view_stack.append((self.view_mode, current_title))
        
        self.view_mode = mode
        self.logic.current_page = 1
        self.logic.apply_filters() # Re-calc items for new mode
        self.refresh_view()
        
        # UI Updates
        if mode == "library":
            self.back_btn.pack_forget()
            self.header_title_label.configure(text="Packs Library")
        else:
            self.back_btn.pack(side="left", padx=5) # Show Back button
            self.header_title_label.configure(text=title)

    def show_library(self):
        """Resets to Root View."""
        self.view_stack.clear()
        self.logic.current_collection_data = None
        self.logic.current_pack_data = None
        self.navigate_to("library", "Packs Library")

    def show_collection_view(self):
        """Displays content of a Virtual Folder."""
        data = self.logic.current_collection_data
        if data:
            self.navigate_to("collection", data['name'])

    def show_gallery(self, pack_data=None):
        """Displays Stickers (Level 3)."""
        # Gallery can be standalone pack OR collection aggregation
        if self.logic.current_collection_data and not pack_data:
            # Viewing All Stickers in Collection (Aggregated)
            self.navigate_to("gallery_collection", f"All Stickers: {self.logic.current_collection_data['name']}")
        else:
            # Viewing Single Pack
            self.logic.current_pack_data = pack_data
            name = pack_data['name'] if pack_data else "All Stickers"
            self.navigate_to("gallery_pack", name)

    def go_back(self):
        """Pops previous state from stack."""
        if not self.view_stack:
            self.show_library()
            return
            
        prev_mode, prev_title = self.view_stack.pop()
        
        # Restore context data based on mode we are returning TO
        if prev_mode == "library":
            self.logic.current_collection_data = None
            self.logic.current_pack_data = None
        elif prev_mode == "collection":
             # We assume current_collection_data is still valid in logic
             self.logic.current_pack_data = None
             
        self.view_mode = prev_mode
        self.logic.current_page = 1
        self.logic.apply_filters()
        self.refresh_view()
        
        if self.view_mode == "library":
            self.back_btn.pack_forget()
            
        self.header_title_label.configure(text=prev_title)

    def refresh_view(self):
        """Refreshes the grid content based on current view mode and data."""
        # Clear Cards
        for card in self.cards: card.destroy()
        self.cards.clear()
        
        # Pagination Control
        self.page_label.configure(text=f"{self.logic.current_page} / {self.logic.total_pages}")
        self.page_prev_btn.configure(state="normal" if self.logic.current_page > 1 else "disabled")
        self.page_next_btn.configure(state="normal" if self.logic.current_page < self.logic.total_pages else "disabled")
        
        self.header_subtitle_label.configure(text=f"{self.logic.total_items} Items")

        items = self.logic.get_current_page_items()
        
        # --- RENDER STRATEGY ---
        if self.view_mode in ["library", "collection"]:
            # Logic for grid indexing
            start_idx = 0
            
            # 1. LIBRARY HEADER CARDS (Page 1 only)
            if self.view_mode == "library" and self.logic.current_page == 1:
                self.card_manager.create_add_card(0)
                self.card_manager.create_all_stickers_card(1)
                start_idx = 2
            
            # 2. COLLECTION HEADER CARD (Page 1 only)
            elif self.view_mode == "collection" and self.logic.current_page == 1:
                self.card_manager.create_all_stickers_in_collection_card(0)
                start_idx = 1
            
            # 3. RENDER CONTENT
            for idx, item in enumerate(items, start=start_idx):
                if item.get("type") == "folder":
                    self.card_manager.create_folder_card(idx, item)
                else:
                    self.card_manager.create_pack_card(idx, item)
                    
        else:
            # Rendering Stickers
            for idx, item in enumerate(items):
                # item = (sticker_data, pack_tname, index_in_pack)
                self.card_manager.create_sticker_card(idx, item[0], item[1], item[2])

        self.canvas.yview_moveto(0.0)
        self.update_idletasks()
        
        # FIX: Remove the forced layout update from here.
        # We rely on the natural resize event or initial resize logic.
        # If we force it with a possibly wrong width, it resets everything.
        # self.after(50, self._force_layout_update) 
        
        # Instead, manually trigger sizing ONCE using current valid state if available
        if self.last_width > 50:
             self.on_content_resize(type('Event', (object,), {'width': self.last_width})())
        else:
             # Only fallback if we have no history
             current_w = self.canvas.winfo_width()
             if current_w > 50:
                 self.on_content_resize(type('Event', (object,), {'width': current_w})())

    def _force_layout_update(self):
        """Forces a layout calculation using the current window width."""
        current_w = self.canvas.winfo_width()
        # Fallback if canvas is not yet mapped or too small
        if current_w < 100: current_w = max(800, self.winfo_width()) - 300 
        self.on_content_resize(type('Event', (object,), {'width': current_w})())

    # ==========================================================================
    #   MISC / BOILERPLATE (Standard Methods)
    # ==========================================================================
    def update_status_bar(self, text: str, progress: float = None):
        self.status_label.configure(text=text)
        if progress is not None:
            self.status_prog.grid()
            self.status_prog.set(progress)
        else: self.status_prog.grid_remove()

    def restart_app(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def toggle_left_sidebar(self):
        if self.left_sidebar_visible:
            self.filter_frame.grid_remove()
            self.toggle_left_btn.configure(text=ICON_RIGHT)
            self.left_sidebar_visible = False
        else:
            self.filter_frame.grid()
            self.toggle_left_btn.configure(text=ICON_LEFT)
            self.left_sidebar_visible = True
        self.update_idletasks()
        # Force refresh on toggle to fix grid
        self.on_content_resize(type('Event', (object,), {'width': self.canvas.winfo_width()})())


    def toggle_right_sidebar(self):
        if self.right_sidebar_visible:
            self.sidebar_container.grid_remove()
            self.toggle_right_btn.configure(text=ICON_LEFT)
            self.right_sidebar_visible = False
        else:
            self.sidebar_container.grid()
            self.toggle_right_btn.configure(text=ICON_RIGHT)
            self.right_sidebar_visible = True
        self.update_idletasks()
        # Force refresh on toggle to fix grid
        self.on_content_resize(type('Event', (object,), {'width': self.canvas.winfo_width()})())

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.on_content_resize(event)

    def _bind_mouse_wheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mouse_wheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if self.logic.total_items == 0: return
        try:
            delta = 0
            if event.num == 5: delta = 1
            elif event.num == 4: delta = -1
            elif event.delta: delta = -1 if event.delta > 0 else 1
            if delta != 0: self.canvas.yview_scroll(delta, "units")
        except: pass

    def change_layout_mode(self, mode):
        # Optimization: Don't re-render if mode is the same, unless forcing a refresh via other means
        if self.current_layout_mode == mode and self.cards:
            return
            
        self.current_layout_mode = mode
        self.last_width = 0 
        self.refresh_view()

    def on_content_resize(self, event):
        # Ignore invalid widths during startup/minimize
        if event.width < 50: return
        
        # Debounce to avoid excessive recalculations
        if abs(event.width - getattr(self, 'last_width', 0)) < 10: return
        self.last_width = event.width
        
        # Determine Columns
        if self.current_layout_mode == "List": 
            new_cols = 1
        else:
            # Enforce minimums to prevent "weird" squeezed sizes
            if self.current_layout_mode == "Large":
                min_card_width = 280 
            elif self.current_layout_mode == "Normal":
                min_card_width = 200 
            else: # Small
                min_card_width = 160
                
            new_cols = max(1, (event.width - 20) // min_card_width)
        
        # Update Grid Configuration
        if new_cols != self.content_columns:
            self.content_columns = new_cols
            for i in range(12): self.content_area.grid_columnconfigure(i, weight=0, uniform="") 
            
            if self.current_layout_mode == "List": 
                self.content_area.grid_columnconfigure(0, weight=1)
            else:
                for i in range(self.content_columns): 
                    self.content_area.grid_columnconfigure(i, weight=1, uniform="cards")
            
            # Re-grid cards
            for i, card in enumerate(self.cards):
                card.grid(row=i // new_cols, column=i % new_cols, sticky="nsew", padx=CARD_PADDING, pady=CARD_PADDING)

        # Deferred Image Resizing logic
        if self.resize_timer: self.after_cancel(self.resize_timer)
        
        def perform_resize(w_width):
            if self.current_layout_mode == "List": return
            
            col_width = (w_width - 20) // self.content_columns
            if col_width < 50: return
            
            # Calculate height maintaining aspect ratio mostly, but clamped
            new_height = int(col_width * 0.75) + 85 - (CARD_PADDING * 2)
            
            # CRITICAL FIX: Enforce min heights based on mode to prevent "weird" squeezed sizes
            if self.current_layout_mode == "Large":
                min_h = 180
            elif self.current_layout_mode == "Normal":
                min_h = 160 # UPDATED: Normal mode height
            else: # Small
                min_h = 140

            if new_height < min_h: new_height = min_h
            
            # Determine image resolution to load
            img_size_dim = max(50, min(int(col_width * 0.85), 512))
            
            for card in self.cards: 
                try: 
                    card.configure(height=new_height)
                    if hasattr(self.card_manager, 'update_card_image'):
                        self.card_manager.update_card_image(card, (img_size_dim, img_size_dim))
                except: pass
                
        self.resize_timer = self.after(150, lambda: perform_resize(event.width))

if __name__ == "__main__":
    app = StickerBotApp()
    app.mainloop()