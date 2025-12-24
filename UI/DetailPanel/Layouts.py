import customtkinter as ctk
import random
from pathlib import Path
from typing import Dict, Any, Optional

from Core.Config import BASE_DIR, LIBRARY_FOLDER
from UI.ViewUtils import COLORS, open_file_location, ToastNotification
from Resources.Icons import (
    FONT_HEADER, FONT_DISPLAY, FONT_TITLE, FONT_NORMAL, FONT_SMALL,
    ICON_FAV_OFF, ICON_FAV_ON, ICON_FOLDER, ICON_UPDATE, ICON_REMOVE,
    ICON_ADD, ICON_SETTINGS, ICON_LINK, ICON_FILE,
    ICON_FMT_ANIM, ICON_FMT_STATIC, ICON_FMT_MIXED,
    ICON_STATS, ICON_CLEAR
)

# Imported Components (Atoms & Molecules)
from UI.DetailPanel.Elements import (
    create_section_header, create_modern_button, create_action_button, 
    update_fav_btn, adjust_text_size
)
from UI.DetailPanel.Sections import TagSection, StatsBlock, LinkStatusSection

class BaseLayout:
    """Shared functionality for all Detail Views."""
    def __init__(self, app, parent_frame, loader):
        self.app = app
        self.loader = loader
        
        # The main scrollable container for this view
        self.frame = ctk.CTkScrollableFrame(
            parent_frame, fg_color=COLORS["bg_sidebar"], corner_radius=0,
            scrollbar_button_color=COLORS["scrollbar_fg"], 
            scrollbar_button_hover_color=COLORS["scrollbar_hover"]
        )
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Common Image State
        self.image_label: Optional[ctk.CTkLabel] = None
        self.image_frame: Optional[ctk.CTkFrame] = None
        self.current_img_path: Optional[str] = None
        self.current_load_id: int = 0

    def show(self):
        self.frame.grid(row=0, column=0, sticky="nsew")

    def hide(self):
        self.frame.grid_remove()

    def _setup_image_area(self, parent):
        """Builds the standard image container."""
        self.image_frame = ctk.CTkFrame(parent, fg_color=COLORS["transparent"], corner_radius=12)
        self.image_frame.pack(fill="x", pady=(0, 10), padx=20)
        
        # Initial State: Placeholder Text
        self.image_label = ctk.CTkLabel(
            self.image_frame, text="Select Item", 
            text_color=COLORS["text_placeholder"], 
            fg_color=COLORS["transparent"]
        )
        self.image_label.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Bind resize for responsive image loading
        self.image_frame.bind("<Configure>", self._on_image_resize)

    def _on_image_resize(self, event):
        """Triggered when the sidebar is resized."""
        if not self.current_img_path or not self.image_label: return
        # Delegate to AsyncLoader
        self.loader.request_image_load(
            self.current_img_path, 
            self.image_label, 
            event.width, 
            self.current_load_id
        )

    def _reset_image_label(self):
        """Clears the image label to prevent ghosting when switching views."""
        if self.image_label and self.image_label.winfo_exists():
            try:
                # FIX: Wrap in try/except to catch "image doesn't exist" TclError
                self.image_label.configure(image=None, text="Loading...", text_color=COLORS["text_sub"])
            except Exception:
                # Fallback: Sometimes just setting text works if image kwarg fails
                try: self.image_label.configure(text="Loading...")
                except: pass


class PackLayout(BaseLayout):
    """Layout for displaying Sticker Pack details."""
    
    def __init__(self, app, parent, loader):
        super().__init__(app, parent, loader)
        self.setup_ui()

    def setup_ui(self):
        # 1. Header
        ctk.CTkLabel(self.frame, text="Pack Details", font=FONT_HEADER, text_color=COLORS["text_main"]).pack(pady=(20, 15), padx=10, fill="x")

        # 2. Image
        self._setup_image_area(self.frame)

        # 3. Primary Actions
        create_modern_button(self.frame, "Change Cover", self.app.logic.open_cover_selector).pack(fill="x", padx=30, pady=(0, 5))
        self.rename_btn = create_modern_button(self.frame, "Rename", self.app.logic.toggle_rename_pack_ui)
        self.rename_btn.pack(fill="x", padx=30, pady=(0, 15))

        # 4. Title & URL
        self.title_box = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.title_box.pack(fill="x", padx=15, pady=(0, 5))
        
        self.title_lbl = ctk.CTkLabel(self.title_box, text="--", font=FONT_DISPLAY, text_color=COLORS["text_main"])
        self.title_lbl.pack(fill="x")
        self.title_box.bind("<Configure>", lambda e: adjust_text_size(e, self.title_lbl, 22))
        
        # Rename Entry (Hidden by default)
        self.title_entry = ctk.CTkEntry(self.title_box, font=FONT_TITLE, justify="center", fg_color=COLORS["entry_bg"])
        
        self.url_lbl = ctk.CTkLabel(self.frame, text="--", font=FONT_NORMAL, text_color=COLORS["text_sub"], cursor="hand2")
        self.url_lbl.pack(fill="x", pady=(0, 15))
        self.url_lbl.bind("<Button-1>", self.app.logic.open_url)

        # 5. Favorite
        self.fav_btn = ctk.CTkButton(self.frame, height=32, font=FONT_NORMAL, corner_radius=8, command=lambda: self.app.logic.toggle_favorite("pack"))
        self.fav_btn.pack(fill="x", padx=30, pady=(0, 20))

        # 6. Components (Tags, Collections, Stats)
        self.tags = TagSection(self.frame, self.app, "pack")
        self.collection_link = LinkStatusSection(self.frame, self.app)
        self.stats = StatsBlock(self.frame, ["Total Stickers", "Format", "Date Added", "Date Updated"])

        # 7. Bottom Actions
        create_section_header(self.frame, "Actions")
        
        # Dynamic path getter
        def open_folder():
            if self.app.logic.current_pack_data:
                p = BASE_DIR / LIBRARY_FOLDER / self.app.logic.current_pack_data['t_name']
                open_file_location(p, False)

        create_action_button(self.frame, f"{ICON_FOLDER} Open Folder", COLORS["btn_info"], COLORS["text_on_info"], open_folder)
        
        self.dl_btn = create_action_button(self.frame, f"{ICON_UPDATE} Download", COLORS["btn_primary"], COLORS["text_on_primary"], 
                                           lambda: [self.app.logic.trigger_redownload(), ToastNotification(self.app, "Queued", "Pack re-download started.")])
        
        create_action_button(self.frame, f"{ICON_REMOVE} Remove Pack", COLORS["btn_negative"], COLORS["text_on_negative"], 
                             lambda: [self.app.logic.confirm_remove_pack(), ToastNotification(self.app, "Action", "Remove Pack requested.")])

        ctk.CTkFrame(self.frame, height=40, fg_color="transparent").pack()


    def refresh(self, data: Dict[str, Any], load_id: int):
        self.current_load_id = load_id
        self._reset_image_label()
        
        # 1. Image Logic (Thumbnail or Random)
        thumb = data.get('thumbnail_path') or data.get('temp_thumbnail')
        if not thumb and data.get('count', 0) > 0:
             try:
                 tname = data['t_name']
                 base = BASE_DIR / LIBRARY_FOLDER / tname
                 # PRIORITIZE GIF/WebM
                 for ext in [".gif", ".webm", ".webp", ".png"]:
                    p = base / f"sticker_{random.randint(0, data['count']-1)}{ext}"
                    if p.exists():
                        thumb = str(p)
                        break
             except: pass
        
        self.current_img_path = thumb
        
        # Explicit check for missing file to show "Broken" state immediately
        if thumb and not Path(thumb).exists():
             try:
                self.image_label.configure(image=None, text="⚠️ File Missing", text_color=COLORS["btn_negative"])
             except: pass
        else:
             self.loader.request_image_load(thumb, self.image_label, self.image_frame.winfo_width(), load_id)

        # 2. Texts
        self.title_lbl.configure(text=data.get("name", "Unknown"))
        self.title_lbl.pack(fill="x")
        self.title_entry.pack_forget() # Reset rename state
        self.rename_btn.configure(text="Rename")
        
        display_url = data.get("t_name") or data.get("url", "--").split("/")[-1]
        self.url_lbl.configure(text=display_url)
        
        update_fav_btn(self.fav_btn, data.get('is_favorite', False), COLORS)
        
        # 3. Components
        self.tags.render(data.get('tags', []))
        self.collection_link.update(data)
        
        # Format detection
        stickers = data.get('stickers', [])
        has_anim = any("Animated" in s.get('tags', []) for s in stickers)
        has_static = any("Static" in s.get('tags', []) for s in stickers)
        fmt = f"Mixed {ICON_FMT_MIXED}"
        if has_anim and not has_static: fmt = f"Animated {ICON_FMT_ANIM}"
        elif has_static and not has_anim: fmt = f"Static {ICON_FMT_STATIC}"
        
        self.stats.update({
            "Total Stickers": data.get('count', 0),
            "Date Added": data.get('added', '--'),
            "Date Updated": data.get('updated', '--'),
            "Format": fmt
        })
        
        dl_txt = f"{ICON_UPDATE} Re-Download" if data.get("downloaded") else f"{ICON_UPDATE} Download Pack"
        self.dl_btn.configure(text=dl_txt)


class CollectionLayout(BaseLayout):
    """Layout for Virtual Collections."""
    
    def __init__(self, app, parent, loader):
        super().__init__(app, parent, loader)
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self.frame, text="Collection Details", font=FONT_HEADER, text_color=COLORS["text_main"]).pack(pady=(20, 15), padx=10, fill="x")
        
        self._setup_image_area(self.frame)
        
        create_modern_button(self.frame, "Change Cover", self.app.logic.open_collection_cover_selector).pack(fill="x", padx=30, pady=(0, 5))
        self.rename_btn = create_modern_button(self.frame, "Rename", self.app.logic.toggle_rename_collection_ui)
        self.rename_btn.pack(fill="x", padx=30, pady=(0, 15))

        self.title_box = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.title_box.pack(fill="x", padx=15, pady=(0, 5))
        
        self.title_lbl = ctk.CTkLabel(self.title_box, text="--", font=FONT_DISPLAY, text_color=COLORS["text_main"])
        self.title_lbl.pack(fill="x")
        self.title_box.bind("<Configure>", lambda e: adjust_text_size(e, self.title_lbl, 22))
        
        self.title_entry = ctk.CTkEntry(self.title_box, font=FONT_TITLE, justify="center", fg_color=COLORS["entry_bg"])
        
        ctk.CTkLabel(self.frame, text="(Virtual Folder)", font=FONT_SMALL, text_color=COLORS["text_sub"]).pack(pady=(0, 15))

        self.fav_btn = ctk.CTkButton(self.frame, height=32, font=FONT_NORMAL, corner_radius=8, command=lambda: self.app.logic.toggle_favorite("collection"))
        self.fav_btn.pack(fill="x", padx=30, pady=(0, 20))

        self.tags = TagSection(self.frame, self.app, "collection")
        
        create_section_header(self.frame, "Collection")
        create_action_button(self.frame, f"{ICON_SETTINGS} Edit Collection", COLORS["btn_primary"], COLORS["text_on_primary"], 
                             self.app.popup_manager.open_collection_edit_modal)

        self.stats = StatsBlock(self.frame, [f"{ICON_STATS} Total Packs", f"{ICON_STATS} Total Stickers", "Format", "Date Added"])

        create_section_header(self.frame, "Actions")
        create_action_button(self.frame, f"{ICON_FOLDER} Open View", COLORS["btn_info"], COLORS["text_on_info"], 
                             lambda: self.app.logic.open_collection(self.app.logic.selected_collection_data))
        create_action_button(self.frame, f"{ICON_REMOVE} Disband", COLORS["btn_negative"], COLORS["text_on_negative"], 
                             lambda: [self.app.logic.disband_collection(), ToastNotification(self.app, "Disbanded", "Collection deleted.")])

        ctk.CTkFrame(self.frame, height=40, fg_color="transparent").pack()

    def refresh(self, data, load_id):
        self.current_load_id = load_id
        self._reset_image_label()
        
        # Image Logic
        thumb = data.get('thumbnail_path')
        if not thumb and data.get('packs'):
             try:
                 # Find random sticker from content
                 valid_packs = [p for p in data['packs'] if p.get('count', 0) > 0]
                 if valid_packs:
                     rp = random.choice(valid_packs)
                     base = BASE_DIR / LIBRARY_FOLDER / rp['t_name']
                     for ext in [".gif", ".webm", ".webp", ".png"]:
                        p = base / f"sticker_{random.randint(0, rp['count']-1)}{ext}"
                        if p.exists():
                            thumb = str(p); break
             except: pass

        self.current_img_path = thumb
        if thumb and not Path(thumb).exists():
             try:
                self.image_label.configure(image=None, text="⚠️ File Missing", text_color=COLORS["btn_negative"])
             except: pass
        else:
             self.loader.request_image_load(thumb, self.image_label, self.image_frame.winfo_width(), load_id)

        self.title_lbl.configure(text=data['name'])
        self.title_lbl.pack(fill="x")
        self.title_entry.pack_forget()
        self.rename_btn.configure(text="Rename")
        
        update_fav_btn(self.fav_btn, data.get('is_favorite', False), COLORS)
        
        # Tags for collection are stored in the root pack's custom fields
        root_tags = []
        if data.get('packs'):
            root_tags = data['packs'][0].get('custom_collection_tags', [])
        self.tags.render(root_tags)
        
        self.stats.update({
            f"{ICON_STATS} Total Packs": data.get('pack_count', 0),
            f"{ICON_STATS} Total Stickers": data.get('count', 0),
            "Date Added": data.get('added', '--'),
            "Format": "Mixed" # Simplification for collection
        })


class StickerLayout(BaseLayout):
    """Layout for Single Sticker details OR Batch Selection."""
    
    def __init__(self, app, parent, loader):
        super().__init__(app, parent, loader)
        self.setup_ui()

    def setup_ui(self):
        # Header
        ctk.CTkLabel(self.frame, text="Sticker Details", font=FONT_HEADER, text_color=COLORS["text_main"]).pack(pady=(20, 15), padx=10, fill="x")

        # --- CONTAINER 1: Single Sticker View ---
        self.single_view = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.single_view.pack(fill="both", expand=True)

        self._setup_image_area(self.single_view)
        
        self.rename_btn = create_modern_button(self.single_view, "Rename", self.app.logic.toggle_rename)
        self.rename_btn.pack(fill="x", padx=30, pady=(0, 15))

        self.name_box = ctk.CTkFrame(self.single_view, fg_color="transparent")
        self.name_box.pack(fill="x", padx=15, pady=(0, 5))
        
        self.name_lbl = ctk.CTkLabel(self.name_box, text="Name", font=FONT_DISPLAY, text_color=COLORS["text_main"])
        self.name_lbl.pack(fill="x")
        self.name_box.bind("<Configure>", lambda e: adjust_text_size(e, self.name_lbl, 22))
        
        self.name_entry = ctk.CTkEntry(self.name_box, font=FONT_TITLE, justify="center", fg_color=COLORS["entry_bg"])
        
        self.filename_lbl = ctk.CTkLabel(self.single_view, text="file.png", font=FONT_NORMAL, text_color=COLORS["text_sub"])
        self.filename_lbl.pack(fill="x", pady=(0, 15))

        self.fav_btn = ctk.CTkButton(self.single_view, height=32, font=FONT_NORMAL, corner_radius=8, command=lambda: self.app.logic.toggle_favorite("sticker"))
        self.fav_btn.pack(fill="x", padx=30, pady=(0, 20))

        self.tags = TagSection(self.single_view, self.app, "sticker")
        self.stats = StatsBlock(self.single_view, ["Format", "Last Used", "Times Used", "Date Added"])

        create_section_header(self.single_view, "Actions")
        
        # Size Menu
        self.app.details_manager = type('obj', (object,), {'size_var': ctk.StringVar(value="Original")}) # Hack for Logic compatibility if needed, better to fix logic
        # Ideally logic shouldn't read from UI, but for now we replicate the var
        self.size_var = ctk.StringVar(value="Original")
        # In the new architecture, we should update the app.details_manager reference or pass this var to logic.
        # For now, we inject it into the app.details_manager shim if it doesn't exist or update Logic to read from here.
        # Let's bind it to the Logic's expectation by assigning it to the controller in __init__ of Controller.
        
        self.size_menu = ctk.CTkOptionMenu(
            self.single_view, variable=self.size_var,
            values=["Original", "Large (1024px)", "Big (512px)", "Normal (256px)", "Small (128px)", "Tiny (64px)"],
            font=FONT_SMALL, fg_color=COLORS["card_bg"], button_color=COLORS["card_border"], 
            button_hover_color=COLORS["card_hover"], text_color=COLORS["text_main"]
        )
        self.size_menu.pack(fill="x", padx=30, pady=(5, 10))

        def on_copy():
            # Inject this layout's size_var into where logic expects it, or modify Logic.py later.
            # We will assume Logic uses app.details_manager.size_var
            self.app.details_manager.size_var = self.size_var 
            self.app.logic.copy_sticker()
            ToastNotification(self.app, "Copied", "Image copied to clipboard.")

        create_action_button(self.single_view, "Copy", COLORS["btn_positive"], COLORS["text_on_positive"], on_copy)
        create_action_button(self.single_view, f"{ICON_LINK} Show File", COLORS["card_bg"], COLORS["text_main"], self.app.logic.show_file)

        # --- CONTAINER 2: Batch View ---
        self.batch_view = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.batch_view.pack(fill="both", expand=True)
        self.batch_view.pack_forget() # Hide initially
        
        ctk.CTkLabel(self.batch_view, text="📚", font=("Arial", 64), text_color=COLORS["text_sub"]).pack(pady=(50, 20))
        self.batch_count_lbl = ctk.CTkLabel(self.batch_view, text="-- Items", font=FONT_DISPLAY, text_color=COLORS["text_main"])
        self.batch_count_lbl.pack(pady=(0, 30))
        
        self.batch_tags = TagSection(self.batch_view, self.app, "sticker")

    def refresh(self, load_id):
        self.current_load_id = load_id
        
        selection = self.app.logic.selected_stickers
        count = len(selection)
        
        if count <= 1:
            self.batch_view.pack_forget()
            self.single_view.pack(fill="both", expand=True)
            
            if count == 0: 
                # Edge case: No selection (should ideally hide whole panel)
                return

            item = selection[0]
            data, idx, path, pack_tname = item[0], item[1], item[2], item[3]
            
            # Sync Logic State
            self.app.logic.current_sticker_data = data
            self.app.logic.current_sticker_path = path

            # Image
            self.current_img_path = path
            self._reset_image_label()
            
            # Explicit check for missing file here too
            if path and not Path(path).exists():
                 try:
                    self.image_label.configure(image=None, text="⚠️ File Missing", text_color=COLORS["btn_negative"])
                 except: pass
            else:
                 self.loader.request_image_load(path, self.image_label, self.image_frame.winfo_width(), load_id)
            
            # Metadata
            self.name_lbl.configure(text=data.get('custom_name') or f"Sticker {idx+1}")
            self.name_lbl.pack(fill="x")
            self.name_entry.pack_forget()
            self.rename_btn.configure(text="Rename")
            
            self.filename_lbl.configure(text=Path(path).name if path else "Unknown")
            update_fav_btn(self.fav_btn, data.get('is_favorite', False), COLORS)
            
            self.tags.render(data.get('tags', []))
            
            # Stats
            pack = next((p for p in self.app.library_data if p['t_name'] == pack_tname), None)
            is_anim = "Animated" in data.get('tags', []) or (path and path.endswith(('.gif', '.webm', '.mp4')))
            
            self.stats.update({
                "Format": f"Animated {ICON_FMT_ANIM}" if is_anim else f"Static {ICON_FMT_STATIC}",
                "Last Used": data.get('last_used', 'Never'),
                "Times Used": str(data.get('usage_count', 0)),
                "Date Added": pack['added'] if pack else "--"
            })
            
        else:
            # Batch Mode
            self.single_view.pack_forget()
            self.batch_view.pack(fill="both", expand=True)
            
            self.batch_count_lbl.configure(text=f"{count} Items Selected")
            
            # Aggregate tags from selection
            all_tags = set()
            for s in selection:
                all_tags.update(s[0].get('tags', []))
            self.batch_tags.render(list(all_tags))