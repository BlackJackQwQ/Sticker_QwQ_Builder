import customtkinter as ctk
import random
from pathlib import Path
from typing import Dict, Any

from Core.Config import BASE_DIR, LIBRARY_FOLDER
from UI.ViewUtils import COLORS
from Resources.Icons import (
    ICON_ADD, ICON_LIBRARY, ICON_FOLDER, ICON_PLAY, ICON_FAV_ON,
    FONT_TITLE, FONT_NORMAL, FONT_SMALL, FONT_CAPTION
)

# Constants for render sizes
SIZE_LARGE = (320, 320)
SIZE_NORMAL = (240, 240)
SIZE_SMALL = (180, 180)
SIZE_LIST  = (48, 48)

# ==============================================================================
#   UTILITY CARDS (Add Pack, All Stickers)
# ==============================================================================

def create_add_card(app, utils, index: int, is_sticker: bool = False):
    if is_sticker: return 
    card = utils.create_base_frame(index)
    cmd = lambda e: app.popup_manager.open_add_pack_modal()
    
    if app.current_layout_mode == "List":
        # List View - Standardized
        card.grid_columnconfigure(1, weight=1)
        
        # Col 0: Icon
        icon_lbl = ctk.CTkLabel(card, text=ICON_ADD, width=48, height=48, fg_color=COLORS["card_hover"], corner_radius=8, font=("Arial", 24), text_color=COLORS["accent"])
        icon_lbl.grid(row=0, column=0, padx=12, pady=10)
        
        # Col 1: Text
        info_box = ctk.CTkFrame(card, fg_color="transparent")
        info_box.grid(row=0, column=1, sticky="ew", padx=5)
        
        ctk.CTkLabel(info_box, text="Add New Pack", font=FONT_TITLE, text_color=COLORS["text_main"]).pack(anchor="w")
        ctk.CTkLabel(info_box, text="Create from URL", font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(anchor="w")
        
    else:
        # Grid View - Standardized Layout
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)
        
        img_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"], corner_radius=10)
        img_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 2))
        
        fs = 64 if app.current_layout_mode == "Large" else 48
        ctk.CTkLabel(img_frame, text=ICON_ADD, font=("Arial", fs), text_color=COLORS["text_sub"]).place(relx=0.5, rely=0.5, anchor="center")
        
        # Bottom Frame (Info Area)
        info_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"], height=55)
        info_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 5))
        
        info_frame.grid_columnconfigure(0, weight=1)
        
        name_font = FONT_TITLE if app.current_layout_mode == "Large" else FONT_NORMAL
        ctk.CTkLabel(info_frame, text="Add Pack", font=name_font, text_color=COLORS["text_main"], anchor="w").grid(row=0, column=0, sticky="ew")
        
        sub_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        sub_row.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        ctk.CTkLabel(sub_row, text="Create New", font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(side="left")

    utils.bind_hover_effects(card, cmd)
    app.cards.append(card)

def create_all_stickers_card(app, utils, index: int):
    card = utils.create_base_frame(index)
    total_stickers = sum(p.get('count', 0) for p in app.library_data)

    # --- 1. Check for Custom System Cover ---
    thumb_path = app.logic.custom_covers.get("virtual_all_stickers")
    
    # --- 2. Fallback to Random ---
    if not thumb_path or not Path(thumb_path).exists():
        thumb_path = None # Reset if invalid
        try:
            candidate_packs = random.sample(app.library_data, min(len(app.library_data), 5)) if app.library_data else []
            for pack in candidate_packs:
                count = pack.get('count', 0)
                if count > 0:
                    ridx = random.randint(0, count - 1)
                    tname = pack['t_name']
                    base = BASE_DIR / LIBRARY_FOLDER / tname
                    for ext in ['.png', '.gif', '.webp', '.webm', '.mp4']:
                        p = base / f"sticker_{ridx}{ext}"
                        if p.exists():
                            thumb_path = str(p)
                            break
                if thumb_path: break
        except: pass

    # --- Virtual Data for Details Panel ---
    virtual_data = {
        "name": "All Stickers Library",
        "t_name": "all_library_virtual",
        "count": total_stickers,
        "tags": ["System", "Library", "Aggregated"],
        "is_favorite": False,
        "thumbnail_path": thumb_path,
        "description": "Browse all stickers from every pack in your library flattened into one view.",
        "linked_packs": [],          
        "custom_collection_name": "", 
        "custom_collection_tags": []  
    }

    # Commands: Click -> Details, Double -> Gallery
    cmd_click = lambda e: app.details_manager.show_pack_details(virtual_data)
    cmd_double = lambda: app.show_gallery(None)

    # Prepare Image Logic
    if app.current_layout_mode == "Large": target_size = SIZE_LARGE
    elif app.current_layout_mode == "Small": target_size = SIZE_SMALL
    elif app.current_layout_mode == "List": target_size = SIZE_LIST
    else: target_size = SIZE_NORMAL # Default to Normal
    
    is_anim = utils.is_file_animated(thumb_path)
    card.is_animated_content = is_anim
    card.image_path = thumb_path
    card.placeholder_text = ICON_LIBRARY

    if app.current_layout_mode == "List":
        # List View
        card.grid_columnconfigure(1, weight=1)
        
        # Col 0
        img_bg = ctk.CTkLabel(card, text=ICON_LIBRARY, width=48, height=48, fg_color=COLORS["transparent"], corner_radius=6, font=("Arial", 20), text_color=COLORS["accent"])
        img_bg.grid(row=0, column=0, padx=12, pady=10)
        card.image_label = img_bg
        
        if thumb_path:
            if is_anim:
                utils.animate_card(card, thumb_path, target_size, img_bg)
            else:
                utils.load_image_to_label(img_bg, thumb_path, target_size, ICON_LIBRARY)
        else:
             img_bg.configure(text=ICON_LIBRARY)

        # Col 1
        info_box = ctk.CTkFrame(card, fg_color="transparent")
        info_box.grid(row=0, column=1, sticky="ew", padx=5)
        ctk.CTkLabel(info_box, text="All Stickers Library", font=FONT_NORMAL, text_color=COLORS["text_main"]).pack(anchor="w")
        ctk.CTkLabel(info_box, text=f"{total_stickers} Total Items", font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(anchor="w")
    else:
        # Grid View
        card.grid_rowconfigure(0, weight=1)     
        card.grid_columnconfigure(0, weight=1)  
        
        img_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"], corner_radius=10)
        img_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 2))
        
        img_lbl = ctk.CTkLabel(img_frame, text="", fg_color="transparent")
        img_lbl.place(relx=0.5, rely=0.5, anchor="center")
        card.image_label = img_lbl
        
        if thumb_path:
            if is_anim:
                utils.animate_card(card, thumb_path, target_size, img_lbl)
            else:
                utils.load_image_to_label(img_lbl, thumb_path, target_size, ICON_LIBRARY)
        else:
            fs = 48 if app.current_layout_mode == "Large" else 32
            img_lbl.configure(text=ICON_LIBRARY, font=("Arial", fs), text_color=COLORS["text_sub"])
        
        info_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"], height=55)
        info_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 5))
        
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_rowconfigure(0, weight=1)
        
        name_font = FONT_TITLE if app.current_layout_mode == "Large" else FONT_NORMAL
        ctk.CTkLabel(info_frame, text="All Stickers", font=name_font, text_color=COLORS["text_main"], anchor="w").grid(row=0, column=0, sticky="ew")
        
        sub_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        sub_row.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        ctk.CTkLabel(sub_row, text=f"{total_stickers} Items", font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(side="left")

    utils.bind_hover_effects(card, cmd_click, cmd_double)
    app.cards.append(card)

def create_all_stickers_in_collection_card(app, utils, index: int):
    card = utils.create_base_frame(index)
    
    count = 0
    packs = []
    col_name = "Collection"
    
    if app.logic.current_collection_data:
        count = app.logic.current_collection_data.get('count', 0)
        packs = app.logic.current_collection_data.get('packs', [])
        col_name = app.logic.current_collection_data.get('name', 'Collection')

    # --- 1. Check for Custom System Cover ---
    col_id = f"collection_{col_name}"
    thumb_path = app.logic.custom_covers.get(col_id)

    # --- 2. Fallback to random ---
    if not thumb_path or not Path(thumb_path).exists():
        thumb_path = None
        try:
            candidate_packs = random.sample(packs, min(len(packs), 5)) if packs else []
            for pack in candidate_packs:
                p_count = pack.get('count', 0)
                if p_count > 0:
                    ridx = random.randint(0, p_count - 1)
                    tname = pack['t_name']
                    base = BASE_DIR / LIBRARY_FOLDER / tname
                    for ext in ['.png', '.gif', '.webp', '.webm', '.mp4']:
                        p = base / f"sticker_{ridx}{ext}"
                        if p.exists():
                            thumb_path = str(p)
                            break
                if thumb_path: break
        except: pass

    # --- Virtual Data for Details Panel ---
    virtual_data = {
        "name": f"All in {col_name}",
        "t_name": col_id, # Used as key for saving cover later
        "count": count,
        "tags": ["System", "Collection", "Aggregated"],
        "is_favorite": False,
        "thumbnail_path": thumb_path,
        "description": f"Browse all {count} stickers contained within the '{col_name}' collection.",
        "linked_packs": [],          
        "custom_collection_name": "", 
        "custom_collection_tags": []  
    }
    
    # Commands: Click -> Details, Double -> Gallery
    cmd_click = lambda e: app.details_manager.show_pack_details(virtual_data)
    cmd_double = lambda: app.show_gallery(None)

    # Prepare Image Logic
    if app.current_layout_mode == "Large": target_size = SIZE_LARGE
    elif app.current_layout_mode == "Small": target_size = SIZE_SMALL
    elif app.current_layout_mode == "List": target_size = SIZE_LIST
    else: target_size = SIZE_NORMAL
    
    is_anim = utils.is_file_animated(thumb_path)
    card.is_animated_content = is_anim
    card.image_path = thumb_path
    card.placeholder_text = ICON_LIBRARY

    if app.current_layout_mode == "List":
        # List View
        card.grid_columnconfigure(1, weight=1)
        
        # Col 0
        img_bg = ctk.CTkLabel(card, text=ICON_LIBRARY, width=48, height=48, fg_color=COLORS["transparent"], corner_radius=6, font=("Arial", 20), text_color=COLORS["accent"])
        img_bg.grid(row=0, column=0, padx=12, pady=10)
        card.image_label = img_bg
        
        if thumb_path:
            if is_anim:
                utils.animate_card(card, thumb_path, target_size, img_bg)
            else:
                utils.load_image_to_label(img_bg, thumb_path, target_size, ICON_LIBRARY)
        else:
             img_bg.configure(text=ICON_LIBRARY)
        
        # Col 1
        info_box = ctk.CTkFrame(card, fg_color="transparent")
        info_box.grid(row=0, column=1, sticky="ew", padx=5)
        ctk.CTkLabel(info_box, text="All Collection Stickers", font=FONT_NORMAL, text_color=COLORS["text_main"]).pack(anchor="w")
        ctk.CTkLabel(info_box, text=f"{count} Total Items", font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(anchor="w")
        
    else:
        # Grid View
        card.grid_rowconfigure(0, weight=1)     
        card.grid_columnconfigure(0, weight=1)  
        
        img_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"], corner_radius=10)
        img_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 2))
        
        img_lbl = ctk.CTkLabel(img_frame, text="", fg_color="transparent")
        img_lbl.place(relx=0.5, rely=0.5, anchor="center")
        card.image_label = img_lbl
        
        if thumb_path:
            if is_anim:
                utils.animate_card(card, thumb_path, target_size, img_lbl)
            else:
                utils.load_image_to_label(img_lbl, thumb_path, target_size, ICON_LIBRARY)
        else:
            fs = 48 if app.current_layout_mode == "Large" else 32
            img_lbl.configure(text=ICON_LIBRARY, font=("Arial", fs), text_color=COLORS["text_sub"])
        
        info_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"], height=55)
        info_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 5))
        
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_rowconfigure(0, weight=1)
        
        name_font = FONT_TITLE if app.current_layout_mode == "Large" else FONT_NORMAL
        ctk.CTkLabel(info_frame, text="All In Collection", font=name_font, text_color=COLORS["text_main"], anchor="w").grid(row=0, column=0, sticky="ew")
        
        sub_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        sub_row.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        ctk.CTkLabel(sub_row, text=f"{count} Items", font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(side="left")
    
    utils.bind_hover_effects(card, cmd_click, cmd_double)
    app.cards.append(card)

# ==============================================================================
#   CONTENT CARDS (Pack, Folder, Sticker)
# ==============================================================================

def create_folder_card(app, utils, index: int, folder_data: Dict[str, Any]):
    card = utils.create_base_frame(index)
    cmd_click = lambda e: app.logic.show_collection_details(folder_data)
    cmd_double = lambda: app.logic.open_collection(folder_data)

    # Folder Visuals (Dynamic Random Logic)
    thumb = folder_data.get('thumbnail_path')
    if not thumb:
        packs = folder_data.get('packs', [])
        if packs:
            cand_pack = random.choice(packs[:5]) 
            tname = cand_pack['t_name']
            count = cand_pack.get('count', 0)
            if count > 0:
                ridx = random.randint(0, count - 1)
                base = BASE_DIR / LIBRARY_FOLDER / tname
                for ext in ['.png', '.gif', '.webp', '.webm', '.mp4']:
                    p = base / f"sticker_{ridx}{ext}"
                    if p.exists(): 
                        thumb = str(p)
                        break

    if app.current_layout_mode == "Large": target_size = SIZE_LARGE
    elif app.current_layout_mode == "Small": target_size = SIZE_SMALL
    elif app.current_layout_mode == "List": target_size = SIZE_LIST
    else: target_size = SIZE_NORMAL

    card.image_path = thumb
    card.placeholder_text = ICON_FOLDER
    
    # Detect Animation (Robust)
    is_anim_cover = utils.is_file_animated(thumb)
    card.is_animated_content = is_anim_cover

    if app.current_layout_mode == "List":
        # List View
        card.grid_columnconfigure(1, weight=1)

        # Col 0
        img_bg = ctk.CTkLabel(card, text=ICON_FOLDER, width=48, height=48, fg_color=COLORS["transparent"], corner_radius=6, text_color=COLORS["text_sub"])
        img_bg.grid(row=0, column=0, padx=12, pady=10)
        card.image_label = img_bg
        
        if thumb:
            if is_anim_cover:
                utils.animate_card(card, thumb, SIZE_LIST, img_bg) # Pass SIZE_LIST explicitly
            else:
                utils.load_image_to_label(img_bg, thumb, SIZE_LIST, ICON_FOLDER)
        
        # Col 1
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=1, sticky="ew", padx=5)
        ctk.CTkLabel(info, text=folder_data['name'], font=FONT_NORMAL, text_color=COLORS["text_main"]).pack(anchor="w")
        ctk.CTkLabel(info, text=f"Collection • {folder_data['pack_count']} Packs • {folder_data['count']} Stickers", font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(anchor="w")
        
    else:
        # Grid View
        card.grid_rowconfigure(0, weight=1)     
        card.grid_columnconfigure(0, weight=1)  

        img_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"], corner_radius=10) # Added corner_radius to match Pack
        img_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 2)) # Match Pack padding
        
        if thumb:
            img_lbl = ctk.CTkLabel(img_frame, text="", fg_color="transparent")
            img_lbl.place(relx=0.5, rely=0.5, anchor="center")
            card.image_label = img_lbl
            
            if is_anim_cover:
                utils.animate_card(card, thumb, target_size, img_lbl)
            else:
                utils.load_image_to_label(img_lbl, thumb, target_size)
        else:
            ctk.CTkLabel(img_frame, text=ICON_FOLDER, font=("Arial", 64), text_color=COLORS["accent"]).place(relx=0.5, rely=0.5, anchor="center")
        
        # Badge
        ctk.CTkLabel(img_frame, text="COLLECTION", font=("Arial", 10, "bold"), fg_color=COLORS["btn_primary"], text_color=COLORS["text_on_primary"], corner_radius=4).place(relx=0.05, rely=0.05)

        info = ctk.CTkFrame(card, fg_color=COLORS["transparent"], height=55)
        info.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 5)) # Match Pack padding
        
        info.grid_columnconfigure(0, weight=1)
        info.grid_rowconfigure(0, weight=1)
        
        name_font = FONT_TITLE if app.current_layout_mode == "Large" else FONT_NORMAL
        
        ctk.CTkLabel(info, text=folder_data['name'], font=name_font, text_color=COLORS["text_main"], anchor="w", justify="left").grid(row=0, column=0, sticky="ew")
        
        sub_row = ctk.CTkFrame(info, fg_color="transparent")
        sub_row.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        ctk.CTkLabel(sub_row, text=f"{folder_data['pack_count']} Packs inside", font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(side="left")

    utils.bind_hover_effects(card, cmd_click, cmd_double)
    app.cards.append(card)

def create_pack_card(app, utils, index: int, pack_data: Dict[str, Any]):
    card = utils.create_base_frame(index)
    cmd_click = lambda e: app.details_manager.show_pack_details(pack_data)
    cmd_double = lambda: app.show_gallery(pack_data)

    thumb_path = pack_data.get('thumbnail_path')
    if not thumb_path:
        count = pack_data.get('count', 0)
        if count > 0:
            ridx = random.randint(0, count - 1)
            tname = pack_data['t_name']
            base = BASE_DIR / LIBRARY_FOLDER / tname
            for ext in ['.png', '.gif', '.webp', '.webm', '.mp4']:
                p = base / f"sticker_{ridx}{ext}"
                if p.exists():
                    thumb_path = str(p)
                    break
    
    is_nsfw = not app.logic.nsfw_enabled and "NSFW" in pack_data.get('tags', [])
    if is_nsfw: thumb_path = None
    
    # Detect Animation (Robust)
    is_anim = utils.is_file_animated(thumb_path)
    card.is_animated_content = is_anim

    if app.current_layout_mode == "Large": target_size = SIZE_LARGE
    elif app.current_layout_mode == "Small": target_size = SIZE_SMALL
    elif app.current_layout_mode == "List": target_size = SIZE_LIST
    else: target_size = SIZE_NORMAL
    
    placeholder = "NSFW" if is_nsfw else "IMG"
    card.image_path = thumb_path
    card.placeholder_text = placeholder

    if app.current_layout_mode == "List":
        # --- LIST VIEW ---
        card.grid_columnconfigure(1, weight=1)

        # Col 0
        img_bg = ctk.CTkLabel(card, text=placeholder, width=48, height=48, fg_color=COLORS["transparent"], corner_radius=6, text_color=COLORS["text_sub"])
        img_bg.grid(row=0, column=0, padx=12, pady=10)
        card.image_label = img_bg
        
        if not is_nsfw and thumb_path:
            if is_anim:
                utils.animate_card(card, thumb_path, SIZE_LIST, img_bg)
            else:
                utils.load_image_to_label(img_bg, thumb_path, SIZE_LIST, placeholder)
        
        # Col 1
        info_box = ctk.CTkFrame(card, fg_color="transparent")
        info_box.grid(row=0, column=1, sticky="ew", padx=5)
        
        ctk.CTkLabel(info_box, text=pack_data["name"], font=FONT_NORMAL, text_color=COLORS["text_main"]).pack(anchor="w")
        
        count = pack_data.get('count', 0)
        tag_count = len(pack_data.get('tags', []))
        sub_text = f"{count} Stickers"
        if tag_count > 0: sub_text += f" • {tag_count} Tags"
        ctk.CTkLabel(info_box, text=sub_text, font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(anchor="w")
        
        # Col 2
        status_box = ctk.CTkFrame(card, fg_color="transparent")
        status_box.grid(row=0, column=2, sticky="e", padx=15)
        
        if is_anim: ctk.CTkLabel(status_box, text=ICON_PLAY, font=("Arial", 16), text_color=COLORS["accent"]).pack(side="left", padx=5)
        if pack_data.get('is_favorite'):
            ctk.CTkLabel(status_box, text=ICON_FAV_ON, font=("Arial", 16), text_color=COLORS["gold"]).pack(side="right")
            
    else:
        # --- GRID VIEW ---
        card.grid_rowconfigure(0, weight=1)     
        card.grid_columnconfigure(0, weight=1)  

        img_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"], corner_radius=10)
        img_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 2))
        
        txt_col = COLORS["btn_negative"] if is_nsfw else COLORS["text_sub"]
        img_lbl = ctk.CTkLabel(img_frame, text=placeholder, text_color=txt_col, fg_color=COLORS["transparent"])
        img_lbl.place(relx=0.5, rely=0.5, anchor="center")
        card.image_label = img_lbl 
        
        if not is_nsfw:
            if is_anim:
                utils.animate_card(card, thumb_path, target_size, img_lbl)
            else:
                utils.load_image_to_label(img_lbl, thumb_path, target_size, placeholder)
        
        info_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"], height=55)
        info_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 5))
        
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_rowconfigure(0, weight=1)
        
        name_font = FONT_TITLE if app.current_layout_mode == "Large" else FONT_NORMAL
        
        ctk.CTkLabel(info_frame, text=pack_data["name"], font=name_font, text_color=COLORS["text_main"], anchor="w", justify="left").grid(row=0, column=0, sticky="ew")
        
        sub_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        sub_row.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        
        ctk.CTkLabel(sub_row, text=f"{pack_data['count']} Stickers", font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(side="left")
        if pack_data.get('is_favorite'): 
            ctk.CTkLabel(sub_row, text=ICON_FAV_ON, font=FONT_NORMAL, text_color=COLORS["gold"]).pack(side="right")

    utils.bind_hover_effects(card, cmd_click, cmd_double)
    app.cards.append(card)

def create_sticker_card(app, utils, index: int, sticker_data: Dict[str, Any], pack_tname: str, idx_in_pack: int):
    card = utils.create_base_frame(index)
    card.sticker_data = sticker_data 
    
    base_path = BASE_DIR / LIBRARY_FOLDER / pack_tname
    final_path = None
    for ext in ['.png', '.gif', '.webp', '.webm', '.mp4']:
        p = base_path / f"sticker_{idx_in_pack}{ext}"
        if p.exists(): final_path = str(p); break
    
    display_name = sticker_data.get('custom_name', "") or f"Sticker {idx_in_pack+1}"
    cmd = lambda e: app.logic.on_sticker_click(sticker_data, idx_in_pack, final_path, pack_tname, e)

    is_nsfw = "NSFW" in sticker_data.get('tags', [])
    show_image = not (is_nsfw and not app.logic.nsfw_enabled)
    txt = "NSFW" if not show_image else "FILE"
    load_path = final_path if show_image else None
    
    # Check Animation
    is_anim = "Animated" in sticker_data.get('tags', []) or "Video" in sticker_data.get('tags', [])
    if not is_anim and load_path:
        is_anim = utils.is_file_animated(load_path)

    card.is_animated_content = is_anim
    
    if app.current_layout_mode == "Large": target_size = SIZE_LARGE
    elif app.current_layout_mode == "Small": target_size = SIZE_SMALL
    elif app.current_layout_mode == "List": target_size = SIZE_LIST
    else: target_size = SIZE_NORMAL
    
    card.image_path = load_path
    card.placeholder_text = txt

    if app.current_layout_mode == "List":
        # --- LIST VIEW ---
        card.grid_columnconfigure(1, weight=1)

        # Col 0
        img_bg = ctk.CTkLabel(card, text=txt, width=48, height=48, fg_color=COLORS["transparent"], corner_radius=6, text_color=COLORS["text_sub"])
        img_bg.grid(row=0, column=0, padx=12, pady=10)
        card.image_label = img_bg 
        
        if show_image and load_path:
            if is_anim:
                utils.animate_card(card, load_path, SIZE_LIST, img_bg)
            else:
                utils.load_image_to_label(img_bg, load_path, SIZE_LIST, txt)
        
        # Col 1
        info_box = ctk.CTkFrame(card, fg_color="transparent")
        info_box.grid(row=0, column=1, sticky="ew", padx=5)
        
        ctk.CTkLabel(info_box, text=display_name, font=FONT_NORMAL, text_color=COLORS["text_main"]).pack(anchor="w")
        
        ftype = Path(final_path).suffix if final_path else "?"
        ctk.CTkLabel(info_box, text=f"{ftype} • {len(sticker_data.get('tags', []))} Tags", font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(anchor="w")

        # Col 2
        status_box = ctk.CTkFrame(card, fg_color="transparent")
        status_box.grid(row=0, column=2, sticky="e", padx=15)
        
        if is_anim: ctk.CTkLabel(status_box, text=ICON_PLAY, font=("Arial", 16), text_color=COLORS["accent"]).pack(side="left", padx=5)
        if sticker_data.get('is_favorite'): 
            ctk.CTkLabel(status_box, text=ICON_FAV_ON, font=("Arial", 16), text_color=COLORS["gold"]).pack(side="right")
            
    else:
        # --- GRID VIEW ---
        card.grid_rowconfigure(0, weight=1)     
        card.grid_columnconfigure(0, weight=1)  

        img_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"], corner_radius=8)
        img_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 2))
        
        txt_col = COLORS["btn_negative"] if not show_image else COLORS["text_sub"]
        img_lbl = ctk.CTkLabel(img_frame, text=txt, text_color=txt_col, fg_color=COLORS["transparent"])
        img_lbl.place(relx=0.5, rely=0.5, anchor="center")
        card.image_label = img_lbl 
        
        if show_image:
            if is_anim:
                utils.animate_card(card, load_path, target_size, img_lbl)
            else:
                utils.load_image_to_label(img_lbl, load_path, target_size, txt)
        
        if sticker_data.get('is_favorite'):
             ctk.CTkLabel(img_frame, text=ICON_FAV_ON, font=("Arial", 16), text_color=COLORS["gold"]).place(relx=0.9, rely=0.1, anchor="center")
        
        info_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"], height=40)
        info_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 6))
        
        info_frame.grid_columnconfigure(0, weight=1)
        
        name_font = FONT_NORMAL if app.current_layout_mode == "Large" else FONT_SMALL
        ctk.CTkLabel(info_frame, text=display_name, font=name_font, text_color=COLORS["text_main"], anchor="w").grid(row=0, column=0, sticky="ew")

    utils.bind_hover_effects(card, cmd)
    app.cards.append(card)