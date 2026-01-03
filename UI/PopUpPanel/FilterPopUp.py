import customtkinter as ctk
import random
from typing import Optional, List, Dict

from UI.PopUpPanel.Base import BasePopUp
from UI.ViewUtils import COLORS, is_system_tag, format_tag_text, logger, Tooltip
from Resources.Icons import (
    FONT_HEADER, FONT_TITLE, FONT_NORMAL, FONT_SMALL,
    ICON_ADD, ICON_REMOVE, ICON_SEARCH, ICON_SETTINGS, ICON_CLEAR
)

class FilterPopUp(BasePopUp):
    """
    Handles popups related to the Left Filter Panel (Tag Management).
    Methods:
    - open_tag_manager_modal: Edit tags for specific item(s).
    - open_all_tags_modal: View global tag statistics.
    """
    def __init__(self, app):
        super().__init__(app)
        
        # Track active widgets for global click handling
        self.active_search_entry = None
        self.active_clear_btn = None
        
        # We bind to the app globally, but we'll filter events based on the active popup
        self.app.bind_all("<Button-1>", self._on_global_click, add="+")

    def _on_global_click(self, event):
        """
        Detects clicks anywhere. If the click is NOT inside the active search bar,
        remove focus from it.
        """
        if not self.active_search_entry: return
        
        try:
            clicked_widget = event.widget
            entry_widget = self.active_search_entry
            # CTkEntry has an internal entry widget usually named _entry or similar in structure
            internal_entry = getattr(self.active_search_entry, "_entry", None)
            clear_btn = self.active_clear_btn
            
            # Check if we clicked the entry, its internal component, or the clear button
            if clicked_widget == entry_widget: return
            if internal_entry and clicked_widget == internal_entry: return
            if clear_btn and clicked_widget == clear_btn: return
            
            # If the entry currently has focus, remove it by focusing the main window or popup root
            current_focus = self.app.focus_get()
            if current_focus == internal_entry or current_focus == entry_widget:
                # Find the top-level window of the entry to give focus back to it (the popup background)
                top = entry_widget.winfo_toplevel()
                top.focus_set()
                
        except Exception:
            pass

    # ==========================================================================
    #   TAG MANAGER (Contextual)
    # ==========================================================================

    def open_tag_manager_modal(self, context_type: str):
        """
        Manages tags for Pack, Collection, or Sticker.
        Replaces the inline search bar in Details panel.
        """
        # 1. Determine Context & Data from the new Controller (self.app.logic)
        target_name = ""
        current_tags = []
        all_known_tags = []
        
        if context_type == "pack":
            if not self.app.logic.current_pack_data: return
            target_name = self.app.logic.current_pack_data.get('name', 'Pack')
            current_tags = self.app.logic.current_pack_data.get('tags', [])
            all_known_tags = self.app.logic.pack_tags_ac
            
        elif context_type == "collection":
            if not self.app.logic.selected_collection_data: return
            target_name = self.app.logic.selected_collection_data.get('name', 'Collection')
            # Collection tags are stored in the root pack's 'custom_collection_tags'
            root = self.app.logic.selected_collection_data['packs'][0]
            current_tags = root.get('custom_collection_tags', [])
            all_known_tags = self.app.logic.pack_tags_ac
            
        elif context_type == "sticker":
            if not self.app.logic.selected_stickers: return
            # Use the first selected sticker for name display
            target_name = self.app.logic.current_sticker_data.get('custom_name', 'Sticker')
            current_tags = self.app.logic.current_sticker_data.get('tags', [])
            all_known_tags = self.app.logic.sticker_tags_ac

        # 2. Window Setup
        win = self._create_base_window(f"Manage Tags: {target_name}", 500, 600)
        
        # Header
        header = ctk.CTkFrame(win, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(header, text="Manage Tags", font=FONT_HEADER, text_color=COLORS["text_main"]).pack(anchor="center")
        ctk.CTkLabel(header, text=target_name, font=FONT_NORMAL, text_color=COLORS["accent"]).pack(anchor="center")

        # ==========================
        # TOP: CURRENT TAGS
        # ==========================
        top_frame = ctk.CTkFrame(win, fg_color=COLORS["bg_sidebar"], corner_radius=10)
        top_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        ctk.CTkLabel(top_frame, text="Current Tags", font=FONT_TITLE, text_color=COLORS["text_sub"]).pack(pady=(10,5), padx=10, anchor="w")
        
        current_scroll = ctk.CTkScrollableFrame(top_frame, fg_color="transparent")
        current_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        def refresh_current_list():
            for w in current_scroll.winfo_children(): w.destroy()
            
            # Re-fetch fresh list from logic
            fresh_tags = []
            if context_type == "pack": 
                fresh_tags = self.app.logic.current_pack_data.get('tags', [])
            elif context_type == "collection": 
                r = self.app.logic.selected_collection_data['packs'][0]
                fresh_tags = r.get('custom_collection_tags', [])
            elif context_type == "sticker":
                # For stickers, we check the main selection. 
                # (Logic.add_tag_manual handles batch updates, but we display the primary one here)
                if self.app.logic.selected_stickers:
                    fresh_tags = self.app.logic.current_sticker_data.get('tags', [])
            
            if not fresh_tags:
                ctk.CTkLabel(current_scroll, text="No tags assigned.", text_color=COLORS["text_sub"]).pack(pady=20)
                return

            for tag in fresh_tags:
                row = ctk.CTkFrame(current_scroll, fg_color=COLORS["card_bg"], corner_radius=6)
                row.pack(fill="x", pady=3)
                
                disp = format_tag_text(tag)
                
                # Check if tag is protected (cannot be removed from item)
                # "NSFW" is a system tag BUT it CAN be removed/added manually.
                # "Animated"/"Static" are auto-assigned and generally shouldn't be manually removed.
                is_auto_assigned = tag in ["Animated", "Static", "Local"]
                is_protected = is_auto_assigned
                
                col = COLORS["text_sub"] if is_system_tag(tag) else COLORS["text_main"]
                
                ctk.CTkLabel(row, text=disp, font=FONT_NORMAL, text_color=col).pack(side="left", padx=10, pady=5)
                
                if not is_protected:
                    # UPDATED: Added "Remove" text and increased width
                    rem_btn = ctk.CTkButton(
                        row, text=f"{ICON_REMOVE} Remove", width=80, height=24,
                        fg_color=COLORS["btn_negative"], hover_color=COLORS["btn_negative_hover"], text_color=COLORS["text_on_negative"],
                        # Call logic to remove, then refresh both lists in this modal
                        command=lambda t=tag: [
                            self.app.logic.confirm_remove_tag(context_type, t), 
                            refresh_current_list(), 
                            refresh_add_list(search_entry.get())
                        ]
                    )
                    rem_btn.pack(side="right", padx=10)
                    Tooltip(rem_btn, "Remove this tag")

        # ==========================
        # BOTTOM: ADD TAGS
        # ==========================
        bottom_frame = ctk.CTkFrame(win, fg_color="transparent")
        bottom_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        ctk.CTkLabel(bottom_frame, text="Add Tags", font=FONT_TITLE, text_color=COLORS["accent"]).pack(pady=(10, 5), anchor="w")
        
        # Search/Add Bar
        search_fr = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        search_fr.pack(fill="x", pady=(0, 5))
        
        search_entry = ctk.CTkEntry(
            search_fr, 
            placeholder_text="Search or create tag...", 
            height=30, 
            fg_color=COLORS["entry_bg"], 
            text_color=COLORS["entry_text"],
            placeholder_text_color=COLORS["text_sub"]
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        def add_typed_tag():
            txt = search_entry.get().strip()
            if txt:
                # Use new manual add method in Logic
                if hasattr(self.app.logic, 'add_tag_manual'):
                     self.app.logic.add_tag_manual(context_type, txt)
                else:
                    logger.warning("add_tag_manual not found in Logic")
                
                search_entry.delete(0, "end")
                refresh_current_list()
                refresh_add_list()

        add_main_btn = ctk.CTkButton(
            search_fr, text=f"{ICON_ADD} Add", width=60, height=30,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["text_on_accent"],
            command=add_typed_tag
        )
        add_main_btn.pack(side="right")
        Tooltip(add_main_btn, "Create or assign this tag")
        
        # List of Available Tags
        add_scroll = ctk.CTkScrollableFrame(bottom_frame, fg_color="transparent", border_width=1, border_color=COLORS["card_border"])
        add_scroll.pack(fill="both", expand=True)

        def refresh_add_list(query=""):
            for w in add_scroll.winfo_children(): w.destroy()
            query = query.lower()
            
            # Re-read current set to exclude already added tags
            current_set = set()
            if context_type == "pack": 
                current_set = set(self.app.logic.current_pack_data.get('tags', []))
            elif context_type == "collection":
                r = self.app.logic.selected_collection_data['packs'][0]
                current_set = set(r.get('custom_collection_tags', []))
            elif context_type == "sticker":
                if self.app.logic.current_sticker_data:
                    current_set = set(self.app.logic.current_sticker_data.get('tags', []))

            # Filter Available
            candidates = []
            for t in all_known_tags:
                if t in current_set: continue
                
                is_auto = t in ["Animated", "Static", "Local"]
                if is_auto: continue # Don't show these in "Add" list
                
                candidates.append(t)
                
            candidates.sort()
            
            count = 0
            for tag in candidates:
                if query and query not in tag.lower(): continue
                
                row = ctk.CTkFrame(add_scroll, fg_color=COLORS["card_bg"], corner_radius=6)
                row.pack(fill="x", pady=2)
                
                ctk.CTkLabel(row, text=tag, font=FONT_NORMAL, text_color=COLORS["text_main"]).pack(side="left", padx=10, pady=5)
                
                add_sub_btn = ctk.CTkButton(
                    row, text=f"{ICON_ADD} Add", width=70, height=24,
                    fg_color=COLORS["btn_positive"], hover_color=COLORS["btn_positive_hover"], text_color=COLORS["text_on_positive"],
                    command=lambda t=tag: [
                        getattr(self.app.logic, 'add_tag_manual', lambda a,b: None)(context_type, t), 
                        refresh_current_list(), 
                        refresh_add_list(search_entry.get())
                    ]
                )
                add_sub_btn.pack(side="right", padx=10)
                Tooltip(add_sub_btn, "Assign this existing tag")
                
                count += 1
                if count > 50 and not query: break

        search_entry.bind("<KeyRelease>", lambda e: refresh_add_list(search_entry.get()))
        search_entry.bind("<Return>", lambda e: add_typed_tag())

        refresh_current_list()
        refresh_add_list()

    # ==========================================================================
    #   GLOBAL TAG VIEW
    # ==========================================================================

    def open_all_tags_modal(self):
        # 1. Determine Context based on View Mode
        view_mode = getattr(self.app, 'view_mode', 'library')
        context_is_stickers = view_mode in ["gallery_pack", "gallery_collection"]
        context_label = "Sticker Tags" if context_is_stickers else "Pack Tags"
        
        # 2. Get the Allowlist for this context
        if context_is_stickers:
            valid_tags_for_context = self.app.logic.sticker_tags_ac
        else:
            valid_tags_for_context = self.app.logic.pack_tags_ac

        # WIDENED WINDOW for buttons
        win = self._create_base_window(f"All Tags ({context_label})", 750, 680)
        
        ctrl = ctk.CTkFrame(win, fg_color=COLORS["transparent"])
        ctrl.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(ctrl, text="Manage Tags", font=FONT_HEADER, text_color=COLORS["text_main"]).pack(anchor="center", pady=(0, 2))
        ctk.CTkLabel(ctrl, text=f"Showing {context_label}", font=FONT_NORMAL, text_color=COLORS["accent"]).pack(anchor="center", pady=(0, 10))

        # --- SEARCH BAR ---
        search_fr = ctk.CTkFrame(ctrl, fg_color="transparent")
        search_fr.pack(fill="x", pady=(0, 10))
        
        # Removed textvariable to avoid conflicts with placeholder
        search_entry = ctk.CTkEntry(
            search_fr, 
            placeholder_text="Search...",  # Added placeholder here
            height=32, 
            fg_color=COLORS["entry_bg"], 
            text_color=COLORS["entry_text"],
            placeholder_text_color=COLORS["text_sub"] # Ensure visibility
        )
        search_entry.pack(side="left", fill="x", expand=True)
        
        # Register this entry as the active one for global clicks
        self.active_search_entry = search_entry
        
        # Clear Button
        def clear_search():
            search_entry.delete(0, "end")
            # Trigger focus loss to potentially show placeholder if empty
            win.focus_set()
            rebuild()
            clear_btn.pack_forget()
            
        clear_btn = ctk.CTkButton(
            search_fr, text="×", width=24, height=24,
            fg_color="transparent", hover_color=COLORS["card_hover"], text_color=COLORS["text_sub"],
            font=("Arial", 16), command=clear_search
        )
        self.active_clear_btn = clear_btn # Register
        
        # Bind keys
        def on_search_type(event=None):
            # If text exists, show clear button. If empty, hide it.
            if search_entry.get():
                clear_btn.pack(side="right", padx=(5, 0))
            else:
                clear_btn.pack_forget()
            rebuild()
            
        def on_escape(event=None):
            clear_search()
            
        search_entry.bind("<KeyRelease>", on_search_type)
        search_entry.bind("<Escape>", on_escape)
        
        
        filter_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        filter_row.pack(fill="x")
        
        # --- SORT CONTROLS (Updated with Theme Colors) ---
        # 1. Sort Criteria Dropdown
        sort_var = ctk.StringVar(value="Frequency")
        ctk.CTkOptionMenu(
            filter_row, variable=sort_var, 
            values=["Frequency", "Name", "Date Add", "Recently Used", "Random"], 
            width=130, 
            fg_color=COLORS["dropdown_bg"], 
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            text_color=COLORS["text_main"],
            dropdown_fg_color=COLORS["card_bg"],
            dropdown_hover_color=COLORS["card_hover"],
            dropdown_text_color=COLORS["text_main"]
        ).pack(side="left", padx=(0, 5))
        
        # 2. Sort Order
        order_var = ctk.StringVar(value="Descending")
        ctk.CTkOptionMenu(
            filter_row, variable=order_var, 
            values=["Descending", "Ascending"], width=120,
            fg_color=COLORS["dropdown_bg"], 
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            text_color=COLORS["text_main"],
            dropdown_fg_color=COLORS["card_bg"],
            dropdown_hover_color=COLORS["card_hover"],
            dropdown_text_color=COLORS["text_main"]
        ).pack(side="left")

        # 3. System Toggle
        show_sys = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(filter_row, text="Show System", variable=show_sys, text_color=COLORS["text_sub"], progress_color=COLORS["accent"]).pack(side="right")
        Tooltip(filter_row.winfo_children()[-1], "Show auto-assigned tags like Animated/Static")
        
        scroll = ctk.CTkScrollableFrame(win, fg_color=COLORS["transparent"])
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        def rebuild(*args):
            if not win.winfo_exists(): return
            for w in scroll.winfo_children(): w.destroy()
            
            # --- 1. Gather Data ---
            usage = {}
            tag_dates: Dict[str, str] = {}
            tag_total_usage: Dict[str, int] = {}
            
            q = search_entry.get().lower()
            key_mode = sort_var.get()
            
            # Define data source
            pool = []
            if context_is_stickers:
                if view_mode == "gallery_pack" and self.app.logic.current_pack_data:
                    pool = [self.app.logic.current_pack_data]
                elif view_mode == "gallery_collection" and self.app.logic.current_collection_data:
                    pool = self.app.logic.current_collection_data.get('packs', [])
                else:
                    pool = self.app.library_data
            else:
                if view_mode == "collection" and self.app.logic.current_collection_data:
                    pool = self.app.logic.current_collection_data.get('packs', [])
                else:
                    pool = self.app.library_data

            # Iterate Data to build stats
            def update_stats(tags, date, usage_val):
                for t in tags:
                    usage[t] = usage.get(t, 0) + 1
                    if date > tag_dates.get(t, ""): 
                        tag_dates[t] = date
                    tag_total_usage[t] = tag_total_usage.get(t, 0) + usage_val

            for p in pool:
                p_date = p.get('added', '0000-00-00')
                if context_is_stickers:
                    for s in p.get('stickers', []):
                        s_usage = s.get('usage_count', 0)
                        update_stats(s.get('tags', []), p_date, s_usage)
                else:
                    p_usage = sum(s.get('usage_count', 0) for s in p.get('stickers', []))
                    update_stats(p.get('tags', []), p_date, p_usage)
                    update_stats(p.get('custom_collection_tags', []), p_date, p_usage)

            # --- 2. Filter List ---
            final = []
            for tag, count in usage.items():
                if tag not in valid_tags_for_context: continue
                is_auto_system = tag in ["Static", "Animated", "Local"]
                if not show_sys.get() and (is_auto_system or tag == "NSFW"): continue
                if q and q not in tag.lower(): continue
                final.append((tag, count))

            # --- 3. Sort List ---
            is_desc = (order_var.get() == "Descending")
            
            if key_mode == "Frequency":
                sort_key = lambda x: (x[1], x[0].lower())
                if is_desc: sort_key = lambda x: (-x[1], x[0].lower())
                final.sort(key=sort_key)
                if not is_desc: final.sort(key=lambda x: (x[1], x[0].lower()))
                
            elif key_mode == "Random":
                random.shuffle(final)
                
            elif key_mode == "Date Add":
                final.sort(key=lambda x: tag_dates.get(x[0], ""), reverse=is_desc)
                
            elif key_mode == "Recently Used":
                final.sort(key=lambda x: tag_total_usage.get(x[0], 0), reverse=is_desc)
                
            else: 
                final.sort(key=lambda x: x[0].lower(), reverse=is_desc)

            if not final:
                ctk.CTkLabel(scroll, text="No tags found for this view.", text_color=COLORS["text_sub"]).pack(pady=20)

            for tag, count in final:
                row = ctk.CTkFrame(scroll, fg_color=COLORS["card_bg"])
                row.pack(fill="x", pady=3)
                
                txt_col = COLORS["text_sub"] if is_system_tag(tag) else COLORS["text_main"]
                
                extra_info = ""
                if key_mode == "Recently Used":
                    extra_info = f" | {tag_total_usage.get(tag,0)} uses"
                elif key_mode == "Date Add":
                    d = tag_dates.get(tag, "")
                    extra_info = f" | {d[:10]}" if d else ""
                
                ctk.CTkLabel(row, text=f"{format_tag_text(tag)} ({count}){extra_info}", font=("Segoe UI", 12, "bold"), text_color=txt_col).pack(side="left", padx=10, pady=8)
                
                btns = ctk.CTkFrame(row, fg_color="transparent")
                btns.pack(side="right", padx=5)
                
                # Rename Button
                btn_ren = ctk.CTkButton(
                    btns, text=f"{ICON_SETTINGS} Rename", width=85, height=24, fg_color=COLORS["btn_neutral"], text_color=COLORS["text_main"],
                    command=lambda t=tag: self._prompt_rename(t, context_is_stickers, rebuild, parent=win)
                )
                btn_ren.pack(side="left", padx=2)
                
                # Remove Button
                btn_rem = ctk.CTkButton(
                    btns, text=f"{ICON_REMOVE} Remove", width=85, height=24, fg_color=COLORS["btn_negative"], 
                    command=lambda t=tag: self._prompt_delete(t, context_is_stickers, rebuild, parent=win)
                )
                btn_rem.pack(side="left", padx=2)

                # Include
                btn_inc = ctk.CTkButton(
                    btns, text=f"{ICON_ADD} Include", width=80, height=24, fg_color=COLORS["btn_positive"], 
                    command=lambda t=tag: [self.app.logic.add_filter_tag_direct(t, "Include"), win.destroy()]
                )
                btn_inc.pack(side="left", padx=2)
                
                # Exclude
                btn_exc = ctk.CTkButton(
                    btns, text="- Exclude", width=80, height=24, fg_color=COLORS["btn_negative"], 
                    command=lambda t=tag: [self.app.logic.add_filter_tag_direct(t, "Exclude"), win.destroy()]
                )
                btn_exc.pack(side="left", padx=2)

        rebuild()
        # Remove variable tracing since we are not using textvariable anymore
        # Instead, trigger rebuild on sort/filter changes directly
        sort_var.trace_add("write", rebuild)
        order_var.trace_add("write", rebuild)
        show_sys.trace_add("write", rebuild)

    # ==========================================================================
    #   HELPER DIALOGS (Rename / Delete)
    # ==========================================================================
    
    def _prompt_rename(self, old_tag, is_stickers, callback, parent=None):
        """Opens a small modal to rename a tag globally."""
        master_win = parent if parent else self.app
        
        dia = ctk.CTkToplevel(master_win)
        dia.configure(fg_color=COLORS["bg_main"])
        dia.title("Rename Tag")
        dia.geometry("400x180")
        dia.transient(master_win)
        dia.grab_set()
        
        dia.update_idletasks()
        x = master_win.winfo_x() + (master_win.winfo_width() // 2) - 200
        y = master_win.winfo_y() + (master_win.winfo_height() // 2) - 90
        dia.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(dia, text=f"Rename '{old_tag}'", font=FONT_TITLE, text_color=COLORS["text_main"]).pack(pady=(15, 10))
        
        entry = ctk.CTkEntry(dia, width=250, fg_color=COLORS["entry_bg"], text_color=COLORS["entry_text"])
        entry.insert(0, old_tag)
        entry.pack(pady=10)
        entry.focus_set()
        
        btn_box = ctk.CTkFrame(dia, fg_color="transparent")
        btn_box.pack(pady=10)
        
        def save():
            new_tag = entry.get().strip()
            if new_tag and new_tag != old_tag:
                self._exec_rename_global(old_tag, new_tag, is_stickers)
                callback()
            dia.destroy()
            
        ctk.CTkButton(btn_box, text="Save", width=100, command=save, fg_color=COLORS["accent"], text_color=COLORS["text_on_accent"]).pack(side="left", padx=10)
        ctk.CTkButton(btn_box, text="Cancel", width=100, command=dia.destroy, fg_color=COLORS["btn_neutral"], text_color=COLORS["text_main"]).pack(side="left", padx=10)

    def _prompt_delete(self, tag, is_stickers, callback, parent=None):
        """Opens a confirmation modal to delete a tag globally."""
        master_win = parent if parent else self.app
        
        dia = ctk.CTkToplevel(master_win)
        dia.configure(fg_color=COLORS["bg_main"])  # Match Theme
        dia.title("Confirm Remove")
        dia.geometry("400x160")
        dia.transient(master_win) # Ensure on top of master
        dia.grab_set()
        
        dia.update_idletasks()
        x = master_win.winfo_x() + (master_win.winfo_width() // 2) - 200
        y = master_win.winfo_y() + (master_win.winfo_height() // 2) - 80
        dia.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(dia, text=f"Remove tag '{tag}'?", font=FONT_TITLE, text_color=COLORS["text_main"]).pack(pady=(20, 5))
        ctk.CTkLabel(dia, text="This will remove it from ALL items.", font=FONT_SMALL, text_color=COLORS["text_sub"]).pack(pady=(0, 15))
        
        btn_box = ctk.CTkFrame(dia, fg_color="transparent")
        btn_box.pack(pady=10)
        
        def confirm():
            self._exec_delete_global(tag, is_stickers)
            callback()
            dia.destroy()
            
        ctk.CTkButton(btn_box, text="Confirm", width=100, command=confirm, fg_color=COLORS["btn_negative"], text_color=COLORS["text_on_negative"]).pack(side="left", padx=10)
        ctk.CTkButton(btn_box, text="Cancel", width=100, command=dia.destroy, fg_color=COLORS["btn_neutral"], text_color=COLORS["text_main"]).pack(side="left", padx=10)

    # ==========================================================================
    #   INTERNAL LOGIC EXECUTION (Bypassing Controller if needed)
    # ==========================================================================

    def _exec_rename_global(self, old_tag, new_tag, is_stickers):
        """Manually iterates library data to rename tags."""
        count = 0
        for pack in self.app.library_data:
            if not is_stickers:
                if old_tag in pack.get('tags', []):
                    pack['tags'] = [new_tag if t == old_tag else t for t in pack['tags']]
                    count += 1
                if old_tag in pack.get('custom_collection_tags', []):
                    pack['custom_collection_tags'] = [new_tag if t == old_tag else t for t in pack['custom_collection_tags']]
                    count += 1
            else:
                for sticker in pack.get('stickers', []):
                    if old_tag in sticker.get('tags', []):
                        sticker['tags'] = [new_tag if t == old_tag else t for t in sticker['tags']]
                        count += 1
        
        self._safe_save()
        logger.info(f"Renamed tag '{old_tag}' to '{new_tag}' on {count} items.")

    def _exec_delete_global(self, tag, is_stickers):
        """Manually iterates library data to delete tags."""
        count = 0
        for pack in self.app.library_data:
            if not is_stickers:
                if tag in pack.get('tags', []):
                    pack['tags'].remove(tag)
                    count += 1
                if tag in pack.get('custom_collection_tags', []):
                    pack['custom_collection_tags'].remove(tag)
                    count += 1
            else:
                for sticker in pack.get('stickers', []):
                    if tag in sticker.get('tags', []):
                        sticker['tags'].remove(tag)
                        count += 1
                        
        self._safe_save()
        logger.info(f"Deleted tag '{tag}' from {count} items.")
        
    def _safe_save(self):
        """Attempts to save the library using available methods."""
        try:
            if hasattr(self.app.logic, 'lib') and hasattr(self.app.logic.lib, 'save_library_data'):
                 self.app.logic.lib.save_library_data()
            elif hasattr(self.app.logic, 'lib') and hasattr(self.app.logic.lib, 'save_data'):
                 self.app.logic.lib.save_data()
            else:
                 self.app.logic.load_library_data() 
        except Exception as e:
            logger.error(f"Save failed in FilterPopUp: {e}")