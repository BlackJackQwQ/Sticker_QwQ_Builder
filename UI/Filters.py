import customtkinter as ctk
import random
from typing import Dict, List, Optional, Any

# ADDED: Tooltip import
from UI.ViewUtils import COLORS, is_system_tag, format_tag_text, Tooltip
from Resources.Icons import (
    FONT_HEADER, FONT_TITLE, FONT_NORMAL, FONT_SMALL,
    ICON_ARROW_RIGHT, ICON_ARROW_DOWN, ICON_ADD, ICON_REMOVE, ICON_CLEAR
)

class FilterManager:
    """
    Manages the Left Sidebar (Filter Panel).
    Responsible for Searching, Sorting, and filtering Tags.
    """

    def __init__(self, app, container: ctk.CTkFrame):
        self.app = app
        self.container = container
        
        # State
        self.show_expanded_tags: bool = False
        
        # Track which sections are expanded/collapsed
        self.collapsed_sections: Dict[str, bool] = {
            "Include": True, 
            "Exclude": True, 
            "TopTags": False 
        }
        
        self.setup_ui()
        
        # FIX: Global binding to detect clicks outside entry
        self.app.bind_all("<Button-1>", self._on_global_click, add="+")

    # ==========================================================================
    #   MAIN UI BUILDER
    # ==========================================================================

    def refresh_ui(self):
        """Rebuilds the entire sidebar UI."""
        for w in self.container.winfo_children(): w.destroy()
        self.setup_ui() 
        
        is_library = (self.app.view_mode == "library")
        title = "Pack Filters" if is_library else "Sticker Filters"
        self.title_lbl.configure(text=title)
        
        if is_library:
            opts = ["Recently Added", "Alphabetical", "Sticker Count", "Usage", "Random"]
        else:
            opts = ["Index", "Usage", "Random"]
            
        self.sort_opt.configure(values=opts)
        
        if self.app.logic.sort_by not in opts: 
            self.app.logic.sort_by = opts[0]
            
        self.sort_opt.set(self.app.logic.sort_by)
        self.order_opt.set(self.app.logic.sort_order)
        
        if self.app.logic.nsfw_enabled: self.nsfw_switch.select()
        else: self.nsfw_switch.deselect()
            
        if self.app.logic.only_favorites: self.fav_switch.select()
        else: self.fav_switch.deselect()
        
        self.file_type_seg.set(self.app.logic.filter_file_type)
        self.tag_match_seg.set(self.app.logic.filter_tag_mode)

    def setup_ui(self):
        """Initial layout construction."""
        self.scroll = ctk.CTkScrollableFrame(self.container, corner_radius=0, fg_color=COLORS["bg_sidebar"])
        self.scroll.pack(fill="both", expand=True)

        # Header
        self.title_lbl = ctk.CTkLabel(self.scroll, text="Filters", font=FONT_HEADER, text_color=COLORS["text_main"])
        self.title_lbl.pack(pady=(15, 5), padx=15, anchor="w")
        
        self.reset_btn = ctk.CTkButton(
            self.scroll, text="Reset to Default", width=120, height=26,
            fg_color=COLORS["card_bg"], text_color=COLORS["text_sub"], hover_color=COLORS["card_hover"],
            font=FONT_SMALL, command=self.app.logic.reset_filters
        )
        self.reset_btn.pack(pady=(0, 15), padx=15, anchor="w")
        # ADDED: Tooltip
        Tooltip(self.reset_btn, "Reset all filters, sorting, and search queries to default.")
        
        self._build_sort_controls()
        self._build_general_filters()
        self._build_file_type_controls()
        self._build_tag_controls()
        
        self.include_list_frame = self.create_collapsible_section("Include", "Included Tags")
        self.exclude_list_frame = self.create_collapsible_section("Exclude", "Excluded Tags")
        self.top_tags_frame = self.create_collapsible_section("TopTags", "Tag Frequency")
        
        self.render_filter_tags("Include")
        self.render_filter_tags("Exclude")
        self.update_top_tags_ui()
        
        # Bottom Button to Open Modal
        view_all_btn = ctk.CTkButton(
            self.scroll, text="View All Tags", 
            command=self.app.popup_manager.open_all_tags_modal, 
            corner_radius=8, fg_color=COLORS["card_bg"], 
            text_color=COLORS["text_main"], hover_color=COLORS["card_border"]
        )
        view_all_btn.pack(pady=20, fill="x", padx=15)
        # ADDED: Tooltip
        Tooltip(view_all_btn, "Open a window to browse and manage all available tags.")

    def _on_global_click(self, event):
        """
        Detects clicks anywhere in the app.
        If the click is NOT inside the tag filter entry, remove focus from it.
        """
        try:
            clicked_widget = event.widget
            entry_widget = self.tag_filter_entry
            internal_entry = self.tag_filter_entry._entry if hasattr(self.tag_filter_entry, "_entry") else None
            clear_btn = getattr(self, 'clear_tag_btn', None)
            
            # Don't lose focus if clicking entry, internal entry, or clear button
            if clicked_widget in [entry_widget, internal_entry, clear_btn]:
                return
            
            # Also check if clicking on autocomplete suggestions
            if self.ac_frame.winfo_exists() and self.ac_frame.winfo_ismapped():
                for child in self.ac_frame.winfo_children():
                    if clicked_widget == child:
                        return

            if self.app.focus_get() == internal_entry:
                self.app.focus_set()
                self.clear_ac() # Also close dropdown
                
        except Exception:
            pass

    # ==========================================================================
    #   COMPONENT BUILDERS
    # ==========================================================================

    def _build_sort_controls(self):
        lbl = self._create_header_label("Sorting")
        Tooltip(lbl, "Options for ordering the list.")
        
        self.sort_opt = self._create_option_menu(["Recently Added", "Alphabetical", "Sticker Count", "Usage", "Random"])
        # ADDED: Tooltip
        Tooltip(self.sort_opt, "Choose criteria to sort the library items.")
        
        self.order_opt = self._create_option_menu(["Ascending", "Descending"])
        self.order_opt.set("Descending")
        # ADDED: Tooltip
        Tooltip(self.order_opt, "Toggle sort direction (Ascending/Descending).")

    def _build_general_filters(self):
        switch_args = {
            "command": self.app.logic.on_filter_change,
            "text_color": COLORS["text_main"],
            "fg_color": COLORS["switch_fg"],
            "button_color": COLORS["switch_button"],
            "height": 24,
            "font": FONT_NORMAL
        }
        
        lbl = self._create_header_label("Visibility")
        Tooltip(lbl, "Toggle content visibility settings.")
        
        self.nsfw_switch = ctk.CTkSwitch(self.scroll, text="Show NSFW", progress_color=COLORS["btn_negative"], **switch_args)
        self.nsfw_switch.pack(pady=2, anchor="w", padx=15)
        # ADDED: Tooltip
        Tooltip(self.nsfw_switch, "Allow content marked as Not Safe For Work to appear.")
        
        self.fav_switch = ctk.CTkSwitch(self.scroll, text="Favorites Only", progress_color=COLORS["btn_positive"], **switch_args)
        self.fav_switch.pack(pady=(2, 10), anchor="w", padx=15)
        # ADDED: Tooltip
        Tooltip(self.fav_switch, "Hide everything except your favorited packs/stickers.")

    def _build_file_type_controls(self):
        lbl = self._create_header_label("File Type")
        # WORKAROUND: Bind Tooltip to Header Label since SegmentedButton crashes on bind
        Tooltip(lbl, "Filter by file format:\n• All: Show everything\n• Static: Images only\n• Animated: GIFs/Videos only")
        
        self.file_type_seg = ctk.CTkSegmentedButton(
            self.scroll, values=["All", "Static", "Animated"],
            command=self.app.logic.on_filter_change,
            selected_color=COLORS["seg_selected"], selected_hover_color=COLORS["seg_selected"],
            unselected_color=COLORS["seg_fg"], unselected_hover_color=COLORS["card_hover"],
            text_color=COLORS["seg_text"]
        )
        self.file_type_seg.pack(fill="x", padx=15, pady=5)
        self.file_type_seg.set("All")
        # Tooltip REMOVED from segmented button to prevent crash

    def _build_tag_controls(self):
        lbl = self._create_header_label("Tag Filter")
        # WORKAROUND: Bind Tooltip to Header Label
        Tooltip(lbl, "Control how multiple tags are handled:\n• Match All: Item must contain ALL tags.\n• Match Any: Item must contain AT LEAST ONE tag.")
        
        self.tag_match_seg = ctk.CTkSegmentedButton(
            self.scroll, values=["Match All", "Match Any"],
            command=self.app.logic.on_filter_change,
            height=24, font=FONT_SMALL,
            selected_color=COLORS["seg_selected"], selected_hover_color=COLORS["seg_selected"],
            unselected_color=COLORS["seg_fg"], unselected_hover_color=COLORS["card_hover"],
            text_color=COLORS["seg_text"]
        )
        self.tag_match_seg.pack(fill="x", padx=15, pady=(0, 5))
        self.tag_match_seg.set("Match All")
        # Tooltip REMOVED from segmented button to prevent crash
        
        # Search Container for relative positioning
        search_container = ctk.CTkFrame(self.scroll, fg_color="transparent")
        search_container.pack(fill="x", padx=15, pady=5)
        
        self.tag_filter_entry = ctk.CTkEntry(
            search_container, placeholder_text="Enter Tag...", corner_radius=8, height=30,
            fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], text_color=COLORS["entry_text"]
        )
        self.tag_filter_entry.pack(side="left", fill="x", expand=True)
        # ADDED: Tooltip
        Tooltip(self.tag_filter_entry, "Type a tag and press Enter to add it.\nUse the + / - buttons below to specify inclusion.")
        
        # Clear Button (Improved Search Bar)
        self.clear_tag_btn = ctk.CTkButton(
            search_container, text="×", width=24, height=24,
            fg_color="transparent", hover_color=COLORS["card_hover"], text_color=COLORS["text_sub"],
            font=("Arial", 16), command=self._clear_search_input
        )
        # Initially hidden, packed when text exists
        # ADDED: Tooltip
        Tooltip(self.clear_tag_btn, "Clear current tag search")
        
        self.tag_filter_entry.bind("<KeyRelease>", self.check_tag_input)
        self.tag_filter_entry.bind("<Return>", self._on_enter_pressed)
        self.tag_filter_entry.bind("<Escape>", self._on_escape_pressed)
        
        # Autocomplete Frame (Initially Hidden to avoid empty block)
        self.ac_frame = ctk.CTkFrame(self.scroll, fg_color=COLORS["card_bg"], height=0)
        # Do not pack initially
        
        # Button Row (Stored as self.tag_btn_row so we can insert AC frame before it)
        self.tag_btn_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.tag_btn_row.pack(fill="x", pady=5, padx=15)
        
        btn_inc = ctk.CTkButton(
            self.tag_btn_row, text=f"{ICON_ADD} Include", width=80, corner_radius=8,
            fg_color=COLORS["btn_positive"], text_color=COLORS["text_on_positive"], hover_color=COLORS["btn_positive_hover"], 
            command=lambda: self.app.logic.add_filter_tag_direct(self.tag_filter_entry.get().strip(), "Include")
        )
        btn_inc.pack(side="left", padx=(0, 5), expand=True, fill="x")
        # ADDED: Tooltip
        Tooltip(btn_inc, "Add the typed tag to the 'Must Have' list.")
        
        btn_exc = ctk.CTkButton(
            self.tag_btn_row, text="- Exclude", width=80, corner_radius=8,
            fg_color=COLORS["btn_negative"], text_color=COLORS["text_on_negative"], hover_color=COLORS["btn_negative_hover"], 
            command=lambda: self.app.logic.add_filter_tag_direct(self.tag_filter_entry.get().strip(), "Exclude")
        )
        btn_exc.pack(side="left", expand=True, fill="x")
        # ADDED: Tooltip
        Tooltip(btn_exc, "Add the typed tag to the 'Must NOT Have' list.")

    def _create_header_label(self, text: str) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(self.scroll, text=text, font=FONT_TITLE, text_color=COLORS["text_sub"])
        lbl.pack(pady=(12, 2), anchor="w", padx=15)
        return lbl

    def _create_option_menu(self, values: List[str]) -> ctk.CTkOptionMenu:
        menu = ctk.CTkOptionMenu(
            self.scroll, values=values, command=self.app.logic.on_filter_change, 
            corner_radius=8, 
            fg_color=COLORS["dropdown_bg"], 
            button_color=COLORS["accent"], 
            button_hover_color=COLORS["accent_hover"], 
            text_color=COLORS["text_main"],
            dropdown_fg_color=COLORS["card_bg"],
            dropdown_hover_color=COLORS["card_hover"],
            dropdown_text_color=COLORS["text_main"]
        )
        menu.pack(fill="x", pady=2, padx=15)
        return menu

    def create_collapsible_section(self, key: str, title: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.scroll, fg_color=COLORS["transparent"])
        frame.pack(fill="x", padx=10, pady=5)
        
        is_collapsed = self.collapsed_sections.get(key, True)
        arrow = ICON_ARROW_RIGHT if is_collapsed else ICON_ARROW_DOWN
        
        def toggle():
            self.collapsed_sections[key] = not self.collapsed_sections[key]
            self.refresh_ui()
            
        btn = ctk.CTkButton(
            frame, text=f"{arrow}  {title}", fg_color=COLORS["transparent"], text_color=COLORS["text_sub"], 
            anchor="w", command=toggle, height=24, font=FONT_SMALL, hover_color=COLORS["card_bg"]
        )
        btn.pack(fill="x")
        # ADDED: Tooltip
        Tooltip(btn, "Click to expand/collapse this section.")
        
        content = ctk.CTkFrame(self.scroll, fg_color=COLORS["transparent"])
        if not is_collapsed: content.pack(fill="x", padx=15)
        return content

    def _on_enter_pressed(self, event):
        txt = self.tag_filter_entry.get().strip()
        if txt and hasattr(self.app.logic, 'add_filter_tag_direct'):
            self.app.logic.add_filter_tag_direct(txt, "Include")
            self._clear_search_input()

    def _on_escape_pressed(self, event):
        self._clear_search_input()
        self.app.focus_set() 

    def _clear_search_input(self):
        self.tag_filter_entry.delete(0, "end")
        self.clear_ac()
        self.clear_tag_btn.pack_forget()

    def clear_ac(self):
        """Helper to clear autocomplete suggestions and hide the frame."""
        if self.ac_frame.winfo_exists():
            for w in self.ac_frame.winfo_children(): w.destroy()
            self.ac_frame.pack_forget() # FIX: Hide the frame to remove the empty block

    def check_tag_input(self, event):
        try: typed = self.tag_filter_entry.get().lower()
        except: return
        
        # Show/Hide Clear Button
        if typed:
            self.clear_tag_btn.pack(side="right", padx=(5, 0))
        else:
            self.clear_tag_btn.pack_forget()
            self.clear_ac() # Ensure dropdown clears when empty
            return
        
        # We don't call clear_ac() here because it hides the frame, causing flicker
        # Instead, just destroy children
        for w in self.ac_frame.winfo_children(): w.destroy()
        
        source = self.app.logic.pack_tags_ac if self.app.view_mode == "library" else self.app.logic.sticker_tags_ac
        matches = [t for t in source if typed in t.lower() and not is_system_tag(t)][:5] 
        
        if not matches:
            self.ac_frame.pack_forget() # Hide if no matches
            return

        # Show frame before adding buttons if not already shown
        if not self.ac_frame.winfo_ismapped():
             self.ac_frame.pack(fill="x", padx=15, pady=(0, 5), before=self.tag_btn_row)

        for t in matches:
            btn = ctk.CTkButton(
                self.ac_frame, text=t, height=28, anchor="w",
                fg_color=COLORS["card_bg"], 
                hover_color=COLORS["card_hover"], 
                text_color=COLORS["text_main"],
                font=FONT_NORMAL,
                command=lambda tag=t: self.apply_ac(tag)
            )
            btn.pack(fill="x", pady=1)

    def apply_ac(self, tag: str):
        self.tag_filter_entry.delete(0, "end")
        self.tag_filter_entry.insert(0, tag)
        self.clear_ac()
        self.clear_tag_btn.pack(side="right", padx=(5, 0))

    def render_filter_tags(self, type_: str):
        target = self.app.logic.include_tags if type_ == "Include" else self.app.logic.exclude_tags
        frame = self.include_list_frame if type_ == "Include" else self.exclude_list_frame
        
        if not frame or not frame.winfo_exists(): return
        for w in frame.winfo_children(): w.destroy()
        
        if not target:
            lbl = ctk.CTkLabel(frame, text="(None)", text_color=COLORS["text_sub"], font=FONT_SMALL)
            lbl.pack(anchor="w", pady=2)
            return
            
        wrapper = ctk.CTkFrame(frame, fg_color=COLORS["transparent"])
        wrapper.pack(fill="x", anchor="w")
        
        for i, tag in enumerate(target):
            disp = format_tag_text(tag)
            btn_col = COLORS["btn_positive"] if type_ == "Include" else COLORS["btn_negative"]
            txt_col = COLORS["text_on_positive"] if type_ == "Include" else COLORS["text_on_negative"]
            
            ctk.CTkButton(
                wrapper, text=f"{disp}  {ICON_REMOVE}", width=0, height=22, corner_radius=8,
                fg_color=btn_col, text_color=txt_col, font=("Segoe UI", 10, "bold"),
                command=lambda t=tag: self.app.logic.remove_filter_tag(t, type_)
            ).pack(side="left", padx=2, pady=2)
            
            if (i+1) % 2 == 0: 
                wrapper = ctk.CTkFrame(frame, fg_color=COLORS["transparent"])
                wrapper.pack(fill="x", anchor="w")

    def update_top_tags_ui(self):
        if not self.top_tags_frame or not self.top_tags_frame.winfo_exists(): return
        for w in self.top_tags_frame.winfo_children(): w.destroy()
        
        usage = self.app.logic.get_tag_usage()
        sorted_tags = sorted(usage.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_tags:
             ctk.CTkLabel(self.top_tags_frame, text="(Empty)", text_color=COLORS["text_sub"], font=FONT_SMALL).pack(anchor="w", pady=2)
             return
        
        limit = 5
        visible_tags = sorted_tags if self.show_expanded_tags else sorted_tags[:limit]
             
        for tag, count in visible_tags:
            if is_system_tag(tag): continue
            
            row = ctk.CTkFrame(self.top_tags_frame, fg_color=COLORS["transparent"])
            row.pack(fill="x", pady=1)
            
            ctk.CTkLabel(row, text=f"{format_tag_text(tag)} ({count})", font=FONT_SMALL, text_color=COLORS["text_main"], anchor="w").pack(side="left", fill="x", expand=True)
            
            ctk.CTkButton(row, text=ICON_ADD, width=24, height=20, fg_color=COLORS["btn_positive"], command=lambda t=tag: self.app.logic.add_filter_tag_direct(t, "Include")).pack(side="right", padx=2)
            ctk.CTkButton(row, text="-", width=24, height=20, fg_color=COLORS["btn_negative"], command=lambda t=tag: self.app.logic.add_filter_tag_direct(t, "Exclude")).pack(side="right", padx=2)
            
        if len(sorted_tags) > limit:
            btn_txt = "Show Less" if self.show_expanded_tags else f"Show All ({len(sorted_tags)})"
            ctk.CTkButton(
                self.top_tags_frame, text=btn_txt, width=80, height=20,
                fg_color=COLORS["transparent"], border_width=1, border_color=COLORS["text_sub"],
                text_color=COLORS["text_sub"], font=FONT_SMALL, hover_color=COLORS["card_bg"],
                command=self.toggle_expanded_tags
            ).pack(fill="x", pady=(5, 0))

    def toggle_expanded_tags(self):
        self.show_expanded_tags = not self.show_expanded_tags
        self.update_top_tags_ui()

    def refresh_tag_buttons(self):
        self.update_top_tags_ui()

    def reset_all(self):
        self.refresh_tag_buttons()