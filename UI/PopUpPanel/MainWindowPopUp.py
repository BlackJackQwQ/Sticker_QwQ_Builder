import customtkinter as ctk
import webbrowser
from tkinter import colorchooser
from typing import Optional, Callable, List
from pathlib import Path

from UI.PopUpPanel.Base import BasePopUp
from UI.ViewUtils import COLORS, ToastNotification, load_ctk_image
from Core.Config import SETTINGS_FILE, save_json, load_json, BASE_DIR, LIBRARY_FOLDER
from Resources.Icons import (
    FONT_HEADER, FONT_TITLE, FONT_NORMAL, FONT_SMALL, FONT_CAPTION,
    ICON_CHECK, ICON_SAVE, ICON_ADD, ICON_SEARCH
)
from Resources.Themes import THEME_PALETTES

class MainWindowPopUp(BasePopUp):
    """
    Handles popups related to Global App Actions and the Main Header.
    """
    def __init__(self, app):
        super().__init__(app)
        self.settings_win: Optional[ctk.CTkToplevel] = None
        self.temp_theme_choice: str = "Classic"

    # ==========================================================================
    #   SETTINGS MODAL
    # ==========================================================================

    def open_settings_modal(self):
        """
        Opens the main configuration window.
        """
        if self.settings_win and self.settings_win.winfo_exists():
            try: self.settings_win.focus()
            except: self.settings_win = None
            return

        self.temp_theme_choice = self.app.logic.current_theme_name
        self.settings_win = self._create_base_window("Settings", 450, 600)
        
        tabs = ctk.CTkTabview(self.settings_win, fg_color=COLORS["transparent"])
        tabs.pack(fill="both", expand=True, padx=10, pady=5)
        
        tab_general = tabs.add("General")
        tab_custom = tabs.add("Theme Creator")
        
        # --- TAB 1: GENERAL SETTINGS ---
        scroll = ctk.CTkScrollableFrame(tab_general, fg_color=COLORS["transparent"])
        scroll.pack(fill="both", expand=True)
        
        # Theme Selector
        ctk.CTkLabel(scroll, text="Preset Theme", font=FONT_TITLE, text_color=COLORS["text_sub"]).pack(pady=(10, 5), anchor="center")
        
        def on_theme_select(new_theme):
            self.temp_theme_choice = new_theme
            
        theme_menu = ctk.CTkOptionMenu(
            scroll, 
            values=list(THEME_PALETTES.keys()) + ["Custom"], 
            command=on_theme_select,
            fg_color=COLORS["dropdown_bg"], button_color=COLORS["accent"], 
            button_hover_color=COLORS["accent_hover"], text_color=COLORS["dropdown_text"]
        )
        theme_menu.set(self.app.logic.current_theme_name)
        theme_menu.pack(fill="x", pady=5, padx=20)
        
        ctk.CTkButton(
            scroll, text=f"{ICON_CHECK} Save & Reload App", 
            fg_color=COLORS["btn_positive"], text_color=COLORS["text_on_positive"], 
            hover_color=COLORS["btn_positive_hover"], 
            command=lambda: self.app.logic.save_new_theme_and_restart(self.temp_theme_choice)
        ).pack(fill="x", pady=10, padx=20)

        # Bot Token Section
        ctk.CTkLabel(scroll, text="Bot Token", font=FONT_TITLE, text_color=COLORS["text_sub"]).pack(pady=(20, 5), anchor="center")
        
        # Button Row: Tutorial + Link
        help_row = ctk.CTkFrame(scroll, fg_color=COLORS["transparent"])
        help_row.pack(pady=5)
        
        ctk.CTkButton(
            help_row, text="Tutorial", width=100, height=24,
            fg_color=COLORS["btn_info"], text_color=COLORS["text_on_info"],
            command=self.open_token_tutorial_modal
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            help_row, text="Link to @BotFather", width=140, height=24,
            fg_color=COLORS["card_bg"], text_color=COLORS["text_main"], hover_color=COLORS["card_hover"],
            command=lambda: webbrowser.open("https://t.me/BotFather")
        ).pack(side="left", padx=5)
        
        token_fr = ctk.CTkFrame(scroll, fg_color=COLORS["transparent"])
        token_fr.pack(fill="x", padx=20, pady=10)
        
        entry = ctk.CTkEntry(
            token_fr, show="*", 
            fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], 
            text_color=COLORS["entry_text"]
        )
        entry.insert(0, self.app.client.token)
        entry.pack(side="left", fill="x", expand=True)
        
        def toggle_show(): 
            current = entry.cget("show")
            entry.configure(show="" if current == "*" else "*")
            
        ctk.CTkButton(
            token_fr, text="👁", width=30, 
            fg_color=COLORS["card_bg"], text_color=COLORS["text_main"], 
            hover_color=COLORS["card_hover"], command=toggle_show
        ).pack(side="left", padx=2)
        
        def save_token(): 
            new_token = entry.get().strip()
            self.app.client.set_token(new_token)
            self.app.logic.save_settings()
            ToastNotification(self.settings_win, "Saved", "Token updated successfully.")
            
        ctk.CTkButton(
            token_fr, text=f"{ICON_SAVE} Save", width=60, 
            fg_color=COLORS["accent"], text_color=COLORS["text_on_accent"], 
            hover_color=COLORS["accent_hover"], command=save_token
        ).pack(side="left", padx=5)
        
        # --- TAB 2: THEME CREATOR ---
        self._build_theme_creator(tab_custom)

    def open_token_tutorial_modal(self):
        """New Tutorial Popup"""
        win = self._create_base_window("Token Tutorial", 400, 300)
        scroll = ctk.CTkScrollableFrame(win, fg_color=COLORS["transparent"])
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        steps = [
            "1. Open Telegram and search for @BotFather.",
            "2. Send the command /newbot.",
            "3. Follow the instructions to name your bot.",
            "4. BotFather will give you a long API Token.",
            "5. Copy that token and paste it here."
        ]
        
        ctk.CTkLabel(scroll, text="How to get a Token", font=FONT_HEADER, text_color=COLORS["text_main"]).pack(pady=(0, 15))
        
        for step in steps:
            ctk.CTkLabel(scroll, text=step, font=FONT_NORMAL, text_color=COLORS["text_sub"], wraplength=340, justify="left").pack(anchor="w", pady=5)
            
        ctk.CTkButton(scroll, text="Got it!", fg_color=COLORS["accent"], text_color=COLORS["text_on_accent"], command=win.destroy).pack(pady=20)

    def _build_theme_creator(self, parent: ctk.CTkFrame):
        scroll = ctk.CTkScrollableFrame(parent, fg_color=COLORS["transparent"])
        scroll.pack(fill="both", expand=True)
        
        ctk.CTkLabel(scroll, text="Create Custom Palette", font=FONT_TITLE, text_color=COLORS["text_main"]).pack(pady=10)
        
        def pick_color(btn):
            color = colorchooser.askcolor(title="Choose color")[1]
            if color:
                btn.configure(fg_color=color, text=color)
                return color
            return None

        custom_colors = {"bg_main": "#202020", "text_main": "#ffffff", "accent": "#3498db"}
        
        for key, name in [("bg_main", "Background"), ("text_main", "Text"), ("accent", "Accent")]:
            row = ctk.CTkFrame(scroll, fg_color=COLORS["transparent"])
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=name, text_color=COLORS["text_sub"]).pack(side="left")
            btn = ctk.CTkButton(row, text="Pick", width=100, fg_color=COLORS["card_bg"])
            btn.configure(command=lambda b=btn, k=key: custom_colors.update({k: pick_color(b) or custom_colors[k]}))
            btn.pack(side="right")

        def generate_and_save():
            base_bg = custom_colors["bg_main"]
            base_txt = custom_colors["text_main"]
            base_acc = custom_colors["accent"]
            
            new_theme = {
                "mode": "Dark",
                "transparent": "transparent", "white": "white", "black": "black", "gold": "#FFD700",
                "bg_main": base_bg, "bg_sidebar": base_bg,
                "card_bg": base_bg, "card_border": base_acc, "card_hover": base_acc,
                "text_main": base_txt, "text_sub": base_txt, "text_inv": base_bg, "text_placeholder": "gray50",
                "accent": base_acc, "accent_hover": base_acc, "text_on_accent": base_txt,
                "btn_positive": "#2ecc71", "btn_positive_hover": "#27ae60", "text_on_positive": "white",
                "btn_negative": "#e74c3c", "btn_negative_hover": "#c0392b", "text_on_negative": "white",
                "btn_info": "#f1c40f", "btn_info_hover": "#f39c12", "text_on_info": "black",
                "btn_primary": base_acc, "btn_primary_hover": base_acc, "text_on_primary": base_txt,
                "btn_neutral": "gray40", "btn_neutral_hover": "gray50", "text_on_neutral": base_txt,
                "entry_bg": base_bg, "entry_border": base_acc, "entry_text": base_txt,
                "scrollbar_bg": "transparent", "scrollbar_fg": base_acc, "scrollbar_hover": base_acc,
                "switch_fg": base_acc, "switch_progress": base_acc, "switch_button": base_txt,
                "dropdown_bg": base_bg, "dropdown_hover": base_acc, "dropdown_text": base_txt,
                "seg_fg": base_bg, "seg_text": base_txt, "seg_selected": base_acc, "seg_selected_text": base_txt
            }
            
            current = load_json(SETTINGS_FILE)
            current["custom_theme_data"] = new_theme
            current["theme_name"] = "Custom"
            save_json(current, SETTINGS_FILE)
            self.app.restart_app()

        ctk.CTkButton(
            scroll, text=f"{ICON_CHECK} Generate & Apply", 
            fg_color=COLORS["accent"], text_color=COLORS["text_on_accent"], 
            hover_color=COLORS["accent_hover"], command=generate_and_save
        ).pack(fill="x", pady=20)

    # ==========================================================================
    #   SIMPLE DIALOGS
    # ==========================================================================

    def open_add_pack_modal(self):
        win = self._create_base_window("Add Packs", 450, 320)
        ctk.CTkLabel(win, text="Add New Packs", font=FONT_HEADER, text_color=COLORS["text_main"]).pack(pady=(20, 5))
        ctk.CTkLabel(win, text="Paste Telegram Sticker URLs (One per line)", font=FONT_NORMAL, text_color=COLORS["text_sub"]).pack()
        
        textbox = ctk.CTkTextbox(
            win, width=350, height=120, 
            fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], 
            text_color=COLORS["entry_text"]
        )
        textbox.pack(pady=15)
        textbox.focus()
        
        def confirm(e=None):
            raw = textbox.get("1.0", "end-1c")
            if raw:
                urls = [u.strip() for u in raw.split('\n') if u.strip()]
                if urls:
                    if win.winfo_exists(): win.destroy()
                    self.app.logic.add_pack_from_url(urls)
        
        btn_row = ctk.CTkFrame(win, fg_color=COLORS["transparent"])
        btn_row.pack(pady=10)
        ctk.CTkButton(btn_row, text="Cancel", width=100, fg_color=COLORS["card_bg"], text_color=COLORS["text_main"], command=win.destroy).pack(side="left", padx=10)
        ctk.CTkButton(btn_row, text=f"{ICON_ADD} Queue Packs", width=100, fg_color=COLORS["btn_positive"], text_color=COLORS["text_on_positive"], command=confirm).pack(side="left", padx=10)

    def open_update_modal(self, run_func: Callable):
        win = self._create_base_window("Updating Library", 400, 180)
        lbl = ctk.CTkLabel(win, text="Checking Updates...", font=FONT_HEADER, text_color=COLORS["text_main"])
        lbl.pack(pady=(30, 10))
        prog = ctk.CTkProgressBar(win, width=320, progress_color=COLORS["btn_positive"])
        prog.pack(pady=15)
        prog.set(0)
        
        run_func(
            lambda v: prog.set(v) if win.winfo_exists() else None,
            lambda t: lbl.configure(text=t) if win.winfo_exists() else None,
            lambda: win.destroy() if win.winfo_exists() else None
        )
        
    def show_search_history(self, history_list: List[str]):
        win = self._create_base_window("History", 300, 400)
        ctk.CTkLabel(win, text="Recent Searches", font=FONT_HEADER, text_color=COLORS["text_main"]).pack(pady=15)
        scroll = ctk.CTkScrollableFrame(win, fg_color=COLORS["transparent"])
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        for item in reversed(history_list):
            ctk.CTkButton(
                scroll, text=item, height=35, anchor="w", 
                fg_color=COLORS["card_bg"], hover_color=COLORS["card_hover"], text_color=COLORS["text_main"], 
                command=lambda x=item: [self.app.search_entry.delete(0, "end"), self.app.search_entry.insert(0, x), self.app.logic.on_search(), win.destroy()]
            ).pack(fill="x", pady=2)
            
        ctk.CTkButton(win, text="Clear", fg_color=COLORS["btn_negative"], command=lambda: [history_list.clear(), win.destroy()]).pack(pady=10)

    # ==========================================================================
    #   USAGE STATS (LEADERBOARD)
    # ==========================================================================

    def open_usage_stats_modal(self):
        """Updated: Shows image previews for most used stickers"""
        win = self._create_base_window("Most Used Stickers", 550, 600)
        ctk.CTkLabel(win, text="Leaderboard", font=FONT_HEADER, text_color=COLORS["text_main"]).pack(pady=(15, 5))
        scroll = ctk.CTkScrollableFrame(win, fg_color=COLORS["transparent"])
        scroll.pack(fill="both", expand=True, padx=15, pady=10)
        
        top = self.app.logic.get_most_used_stickers(limit=20)
        if not top:
            ctk.CTkLabel(scroll, text="No usage data yet.", text_color=COLORS["text_sub"]).pack(pady=50)
            return
            
        max_u = top[0]['usage'] or 1
        
        for i, s in enumerate(top):
            row = ctk.CTkFrame(scroll, fg_color=COLORS["card_bg"], corner_radius=10)
            row.pack(fill="x", pady=5)
            
            # Rank
            ctk.CTkLabel(row, text=f"#{i+1}", font=("Arial", 16, "bold"), text_color=COLORS["accent"], width=30).pack(side="left", padx=(10, 5))
            
            # Image Preview
            img_path = s.get('image_path')
            if img_path and Path(img_path).exists():
                img_lbl = ctk.CTkLabel(row, text="", width=40, height=40)
                img_lbl.pack(side="left", padx=5, pady=5)
                try:
                    ctk_img = load_ctk_image(img_path, (40, 40))
                    if ctk_img: img_lbl.configure(image=ctk_img)
                except: pass
            else:
                ctk.CTkLabel(row, text="?", width=40, text_color=COLORS["text_sub"]).pack(side="left", padx=5)

            # Info Column
            r_box = ctk.CTkFrame(row, fg_color="transparent")
            r_box.pack(side="left", fill="both", expand=True, padx=10, pady=5)
            
            # Top Row: Name + Usage
            h = ctk.CTkFrame(r_box, fg_color="transparent")
            h.pack(fill="x")
            ctk.CTkLabel(h, text=s['name'], font=FONT_NORMAL, text_color=COLORS["text_main"]).pack(side="left")
            ctk.CTkLabel(h, text=f"{s['usage']} uses", font=("Segoe UI", 12, "bold"), text_color=COLORS["text_sub"]).pack(side="right")
            
            # Bottom Row: Pack Name
            ctk.CTkLabel(r_box, text=f"from: {s.get('pack_display_name', 'Unknown')}", font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(anchor="w")
            
            # Progress Bar
            bar = ctk.CTkProgressBar(r_box, progress_color=COLORS["btn_positive"], height=6)
            bar.pack(fill="x", pady=(5, 0))
            bar.set(s['usage'] / max_u)