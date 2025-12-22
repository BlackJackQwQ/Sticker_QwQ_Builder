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
        icon_lbl = ctk.CTkLabel(card, text=ICON_ADD, width=48, height=48, fg_color=COLORS["card_hover"], corner_radius=8, font=("Arial", 24), text_color=COLORS["accent"])
        icon_lbl.grid(row=0, column=0, padx=12, pady=10)
        ctk.CTkLabel(card, text="Add New Pack", font=FONT_TITLE, text_color=COLORS["text_main"]).grid(row=0, column=1, sticky="w", padx=5)
    else:
        center_box = ctk.CTkFrame(card, fg_color=COLORS["transparent"])
        center_box.grid(row=0, column=0, rowspan=2, sticky="nsew") 
        fs = 48 if app.current_layout_mode == "Large" else 32
        ctk.CTkLabel(center_box, text=ICON_ADD, font=("Arial", fs), text_color=COLORS["text_sub"]).pack(expand=True)
        ctk.CTkLabel(center_box, text="Add Pack", font=FONT_TITLE, text_color=COLORS["text_main"]).pack(pady=(0, 20))

    utils.bind_hover_effects(card, cmd)
    app.cards.append(card)

def create_all_stickers_card(app, utils, index: int):
    card = utils.create_base_frame(index)
    total_stickers = sum(p.get('count', 0) for p in app.library_data)
    cmd = lambda e: app.show_gallery(None)

    if app.current_layout_mode == "List":
        icon_lbl = ctk.CTkLabel(card, text=ICON_LIBRARY, width=48, height=48, fg_color=COLORS["card_hover"], corner_radius=8, font=("Arial", 20))
        icon_lbl.grid(row=0, column=0, padx=12, pady=10)
        info_box = ctk.CTkFrame(card, fg_color="transparent")
        info_box.grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(info_box, text="All Stickers Library", font=FONT_NORMAL, text_color=COLORS["text_main"]).pack(anchor="w")
        ctk.CTkLabel(info_box, text=f"{total_stickers} Total Items", font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(anchor="w")
    else:
        img_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"])
        img_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        fs = 32 if app.current_layout_mode == "Large" else 24
        ctk.CTkLabel(img_frame, text=ICON_LIBRARY, font=("Arial", fs), text_color=COLORS["text_sub"]).place(relx=0.5, rely=0.5, anchor="center")
        
        info_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"], height=40)
        info_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        ctk.CTkLabel(info_frame, text="All Stickers", font=FONT_NORMAL, text_color=COLORS["text_main"], anchor="w").pack(fill="x")
        ctk.CTkLabel(info_frame, text=f"{total_stickers} Items", font=FONT_CAPTION, text_color=COLORS["text_sub"], anchor="w").pack(fill="x")

    utils.bind_hover_effects(card, cmd)
    app.cards.append(card)

def create_all_stickers_in_collection_card(app, utils, index: int):
    card = utils.create_base_frame(index)
    cmd = lambda e: app.show_gallery(None)
    
    count = 0
    if app.logic.current_collection_data:
        count = app.logic.current_collection_data.get('count', 0)

    if app.current_layout_mode == "List":
        icon_lbl = ctk.CTkLabel(card, text=ICON_LIBRARY, width=48, height=48, fg_color=COLORS["card_hover"], corner_radius=8, font=("Arial", 20))
        icon_lbl.grid(row=0, column=0, padx=12, pady=10)
        
        info_box = ctk.CTkFrame(card, fg_color="transparent")
        info_box.grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(info_box, text="All Collection Stickers", font=FONT_NORMAL, text_color=COLORS["text_main"]).pack(anchor="w")
        ctk.CTkLabel(info_box, text=f"{count} Total Items", font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(anchor="w")
        
    else:
        img_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"])
        img_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        fs = 32 if app.current_layout_mode == "Large" else 24
        ctk.CTkLabel(img_frame, text=ICON_LIBRARY, font=("Arial", fs), text_color=COLORS["text_sub"]).place(relx=0.5, rely=0.5, anchor="center")
        
        info_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"], height=40)
        info_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        ctk.CTkLabel(info_frame, text="All Collection Stickers", font=FONT_NORMAL, text_color=COLORS["text_main"], anchor="w").pack(fill="x")
        ctk.CTkLabel(info_frame, text=f"{count} Items", font=FONT_CAPTION, text_color=COLORS["text_sub"], anchor="w").pack(fill="x")
    
    utils.bind_hover_effects(card, cmd)
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

    target_size = SIZE_LARGE if app.current_layout_mode == "Large" else SIZE_SMALL
    card.image_path = thumb
    card.placeholder_text = ICON_FOLDER
    
    # Detect Animation (Robust)
    is_anim_cover = utils.is_file_animated(thumb)
    card.is_animated_content = is_anim_cover

    if app.current_layout_mode == "List":
        # List View
        icon_txt = ICON_PLAY if is_anim_cover else ICON_FOLDER
        icon = ctk.CTkLabel(card, text=icon_txt, font=("Arial", 24), text_color=COLORS["accent"])
        icon.grid(row=0, column=0, padx=15, pady=10)
        
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(info, text=folder_data['name'], font=FONT_NORMAL, text_color=COLORS["text_main"]).pack(anchor="w")
        ctk.CTkLabel(info, text=f"Collection • {folder_data['pack_count']} Packs • {folder_data['count']} Stickers", font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(anchor="w")
        
    else:
        # Grid View
        img_frame = ctk.CTkFrame(card, fg_color=COLORS["transparent"])
        img_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        
        if thumb:
            img_lbl = ctk.CTkLabel(img_frame, text="", fg_color=COLORS["transparent"])
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
        info.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
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
    else: target_size = SIZE_LIST
    
    placeholder = "NSFW" if is_nsfw else "IMG"
    card.image_path = thumb_path
    card.placeholder_text = placeholder

    if app.current_layout_mode == "List":
        # --- LIST VIEW ---
        img_bg = ctk.CTkLabel(card, text=placeholder, width=48, height=48, fg_color=COLORS["transparent"], corner_radius=6, text_color=COLORS["text_sub"])
        img_bg.grid(row=0, column=0, padx=12, pady=10)
        card.image_label = img_bg
        if not is_nsfw: utils.load_image_to_label(img_bg, thumb_path, target_size, placeholder)
        
        info_box = ctk.CTkFrame(card, fg_color="transparent")
        info_box.grid(row=0, column=1, sticky="w", padx=5)
        
        ctk.CTkLabel(info_box, text=pack_data["name"], font=FONT_NORMAL, text_color=COLORS["text_main"]).pack(anchor="w")
        
        count = pack_data.get('count', 0)
        tag_count = len(pack_data.get('tags', []))
        sub_text = f"{count} Stickers"
        if tag_count > 0: sub_text += f" • {tag_count} Tags"
        ctk.CTkLabel(info_box, text=sub_text, font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(anchor="w")
        
        status_box = ctk.CTkFrame(card, fg_color="transparent")
        status_box.grid(row=0, column=3, sticky="e", padx=15)
        
        if is_anim: ctk.CTkLabel(status_box, text=ICON_PLAY, font=("Arial", 16), text_color=COLORS["accent"]).pack(side="left", padx=5)
        if pack_data.get('is_favorite'):
            ctk.CTkLabel(status_box, text=ICON_FAV_ON, font=("Arial", 16), text_color=COLORS["gold"]).pack(side="right")
            
    else:
        # --- GRID VIEW ---
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
    else: target_size = SIZE_LIST
    
    card.image_path = load_path
    card.placeholder_text = txt

    if app.current_layout_mode == "List":
        # --- LIST VIEW ---
        img_bg = ctk.CTkLabel(card, text=txt, width=48, height=48, fg_color=COLORS["transparent"], corner_radius=6, text_color=COLORS["text_sub"])
        img_bg.grid(row=0, column=0, padx=12, pady=10)
        card.image_label = img_bg 
        if show_image: utils.load_image_to_label(img_bg, load_path, target_size, txt)
        
        info_box = ctk.CTkFrame(card, fg_color="transparent")
        info_box.grid(row=0, column=1, sticky="w", padx=5)
        
        ctk.CTkLabel(info_box, text=display_name, font=FONT_NORMAL, text_color=COLORS["text_main"]).pack(anchor="w")
        
        ftype = Path(final_path).suffix if final_path else "?"
        ctk.CTkLabel(info_box, text=f"{ftype} • {len(sticker_data.get('tags', []))} Tags", font=FONT_CAPTION, text_color=COLORS["text_sub"]).pack(anchor="w")

        status_box = ctk.CTkFrame(card, fg_color="transparent")
        status_box.grid(row=0, column=3, sticky="e", padx=15)
        
        if is_anim: ctk.CTkLabel(status_box, text=ICON_PLAY, font=("Arial", 16), text_color=COLORS["accent"]).pack(side="left", padx=5)
        if sticker_data.get('is_favorite'): 
            ctk.CTkLabel(status_box, text=ICON_FAV_ON, font=("Arial", 16), text_color=COLORS["gold"]).pack(side="right")
            
    else:
        # --- GRID VIEW ---
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