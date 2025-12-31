from typing import Dict, Any

# ==============================================================================
#   THEME PALETTES
# ==============================================================================
# This dictionary contains all the color definitions for the application's visual themes.

THEME_PALETTES: Dict[str, Dict[str, str]] = {
    # --- 1. CLASSIC THEME (Dark Mode - Catppuccin Mocha Inspired) ---
    "Classic": { 
        "mode": "Dark",
        "transparent": "transparent",
        "white": "white",
        "black": "black",
        "gold": "#F9E2AF",
        "bg_main": "#1E1E2E", "bg_sidebar": "#181825",
        "card_bg": "#313244", "card_border": "#45475a", "card_hover": "#585b70",
        "text_main": "#CDD6F4", "text_sub": "#A6ADC8", "text_inv": "#1E1E2E", "text_placeholder": "gray50",
        
        "text_link": "#64D2FF", # Bright Light Blue (Requested)

        "accent": "#89B4FA", "accent_hover": "#B4BEFE", "text_on_accent": "#1E1E2E",
        "btn_positive": "#A6E3A1", "btn_positive_hover": "#94E2D5", "text_on_positive": "#1E1E2E",
        "btn_negative": "#F38BA8", "btn_negative_hover": "#EBA0AC", "text_on_negative": "#1E1E2E",
        "btn_info": "#FAB387", "btn_info_hover": "#F9E2AF", "text_on_info": "#1E1E2E",
        "btn_primary": "#89B4FA", "btn_primary_hover": "#B4BEFE", "text_on_primary": "#1E1E2E",
        "btn_neutral": "gray40", "btn_neutral_hover": "gray50", "text_on_neutral": "#CDD6F4",
        "entry_bg": "#11111b", "entry_border": "#45475a", "entry_text": "#CDD6F4",
        "scrollbar_bg": "transparent", "scrollbar_fg": "#45475a", "scrollbar_hover": "#585b70",
        "switch_fg": "#45475a", "switch_progress": "#89B4FA", "switch_button": "#CDD6F4",
        "dropdown_bg": "#313244", "dropdown_hover": "#585b70", "dropdown_text": "#CDD6F4",
        "seg_fg": "#313244", "seg_text": "#CDD6F4", "seg_selected": "#89B4FA", "seg_selected_text": "#1E1E2E" 
    },
    
    # --- 2. SAKURA THEME (Light Mode - Pink/Pastel) ---
    "Sakura": { 
        "mode": "Light",
        "transparent": "transparent",
        "white": "white",
        "black": "black",
        "gold": "#FFD700",
        "bg_main": "#FFF5F7", "bg_sidebar": "#FFE4E8",
        "card_bg": "#FFFFFF", "card_border": "#FFB7C5", "card_hover": "#FFF0F3",
        "text_main": "#5D4037", "text_sub": "#9E7777", "text_inv": "#FFFFFF", "text_placeholder": "gray60",
        
        "text_link": "#007AFF", # Vivid Blue to stand out on Pink/White

        "accent": "#FF69B4", "accent_hover": "#FF1493", "text_on_accent": "#FFFFFF",
        "btn_positive": "#81C784", "btn_positive_hover": "#66BB6A", "text_on_positive": "#FFFFFF",
        "btn_negative": "#E57373", "btn_negative_hover": "#EF5350", "text_on_negative": "#FFFFFF",
        "btn_info": "#FFB74D", "btn_info_hover": "#FFA726", "text_on_info": "#FFFFFF",
        "btn_primary": "#FF69B4", "btn_primary_hover": "#F06292", "text_on_primary": "#FFFFFF",
        "btn_neutral": "#DDDDDD", "btn_neutral_hover": "#CCCCCC", "text_on_neutral": "#5D4037",
        "entry_bg": "#FFFFFF", "entry_border": "#FFB7C5", "entry_text": "#5D4037",
        "scrollbar_bg": "transparent", "scrollbar_fg": "#FFB7C5", "scrollbar_hover": "#FF69B4",
        "switch_fg": "#FFC1E3", "switch_progress": "#FF69B4", "switch_button": "#FFFFFF",
        "dropdown_bg": "#FFFFFF", "dropdown_hover": "#FFE4E8", "dropdown_text": "#5D4037",
        "seg_fg": "#FFFFFF", "seg_text": "#5D4037", "seg_selected": "#FF69B4", "seg_selected_text": "#FFFFFF"
    },

    # --- 3. OCEAN THEME (Dark Mode - Deep Blue/Teal) ---
    "Ocean": { 
        "mode": "Dark",
        "transparent": "transparent",
        "white": "white",
        "black": "black",
        "gold": "#FCD34D",
        "bg_main": "#0f172a", "bg_sidebar": "#020617",
        "card_bg": "#1e293b", "card_border": "#334155", "card_hover": "#475569",
        "text_main": "#f1f5f9", "text_sub": "#94a3b8", "text_inv": "#0f172a", "text_placeholder": "gray50",
        
        "text_link": "#38BDF8", # Sky Blue to match Ocean accent

        "accent": "#38bdf8", "accent_hover": "#7dd3fc", "text_on_accent": "#0f172a",
        "btn_positive": "#2dd4bf", "btn_positive_hover": "#5eead4", "text_on_positive": "#0f172a",
        "btn_negative": "#f43f5e", "btn_negative_hover": "#fb7185", "text_on_negative": "#ffffff",
        "btn_info": "#fbbf24", "btn_info_hover": "#fcd34d", "text_on_info": "#0f172a",
        "btn_primary": "#0ea5e9", "btn_primary_hover": "#38bdf8", "text_on_primary": "#ffffff",
        "btn_neutral": "#334155", "btn_neutral_hover": "#475569", "text_on_neutral": "#f1f5f9",
        "entry_bg": "#1e293b", "entry_border": "#334155", "entry_text": "#f1f5f9",
        "scrollbar_bg": "transparent", "scrollbar_fg": "#334155", "scrollbar_hover": "#475569",
        "switch_fg": "#334155", "switch_progress": "#38bdf8", "switch_button": "#f1f5f9",
        "dropdown_bg": "#1e293b", "dropdown_hover": "#334155", "dropdown_text": "#f1f5f9",
        "seg_fg": "#1e293b", "seg_text": "#f1f5f9", "seg_selected": "#0ea5e9", "seg_selected_text": "#ffffff"
    },

    # --- 4. FOREST THEME (Light Mode - Nature) ---
    "Forest": { 
        "mode": "Light",
        "transparent": "transparent",
        "white": "white",
        "black": "black",
        "gold": "#d97706",
        "bg_main": "#fcfbf7", "bg_sidebar": "#f0fdf4",
        "card_bg": "#ffffff", "card_border": "#bbf7d0", "card_hover": "#dcfce7",
        "text_main": "#14532d", "text_sub": "#166534", "text_inv": "#ffffff", "text_placeholder": "#86efac",
        
        "text_link": "#007AFF", # Vivid Blue to contrast with Green

        "accent": "#22c55e", "accent_hover": "#16a34a", "text_on_accent": "#ffffff",
        "btn_positive": "#4ade80", "btn_positive_hover": "#22c55e", "text_on_positive": "#14532d",
        "btn_negative": "#f87171", "btn_negative_hover": "#ef4444", "text_on_negative": "#ffffff",
        "btn_info": "#fbbf24", "btn_info_hover": "#f59e0b", "text_on_info": "#451a03",
        "btn_primary": "#22c55e", "btn_primary_hover": "#16a34a", "text_on_primary": "#ffffff",
        "btn_neutral": "#e2e8f0", "btn_neutral_hover": "#cbd5e1", "text_on_neutral": "#14532d",
        "entry_bg": "#ffffff", "entry_border": "#86efac", "entry_text": "#14532d",
        "scrollbar_bg": "transparent", "scrollbar_fg": "#bbf7d0", "scrollbar_hover": "#86efac",
        "switch_fg": "#bbf7d0", "switch_progress": "#22c55e", "switch_button": "#ffffff",
        "dropdown_bg": "#ffffff", "dropdown_hover": "#f0fdf4", "dropdown_text": "#14532d",
        "seg_fg": "#ffffff", "seg_text": "#14532d", "seg_selected": "#22c55e", "seg_selected_text": "#ffffff"
    },

    # --- 5. SUNSET THEME (Dark Mode - Vaporwave) ---
    "Sunset": { 
        "mode": "Dark",
        "transparent": "transparent",
        "white": "white",
        "black": "black",
        "gold": "#FCD34D",
        "bg_main": "#2a0a2e", "bg_sidebar": "#18041a",
        "card_bg": "#4a1252", "card_border": "#7c2a8a", "card_hover": "#a13aa1",
        "text_main": "#ffd6fc", "text_sub": "#d692d1", "text_inv": "#2a0a2e", "text_placeholder": "#8a4a85",
        
        "text_link": "#64D2FF", # Bright Light Blue

        "accent": "#ff9e64", "accent_hover": "#ffbf8f", "text_on_accent": "#2a0a2e",
        "btn_positive": "#0db9d7", "btn_positive_hover": "#5ff0ff", "text_on_positive": "#2a0a2e",
        "btn_negative": "#ff5d5d", "btn_negative_hover": "#ff8585", "text_on_negative": "#ffffff",
        "btn_info": "#ffdb57", "btn_info_hover": "#ffeaa3", "text_on_info": "#2a0a2e",
        "btn_primary": "#db2777", "btn_primary_hover": "#f472b6", "text_on_primary": "#ffffff",
        "btn_neutral": "#5c2b63", "btn_neutral_hover": "#7c2a8a", "text_on_neutral": "#ffd6fc",
        "entry_bg": "#18041a", "entry_border": "#7c2a8a", "entry_text": "#ffd6fc",
        "scrollbar_bg": "transparent", "scrollbar_fg": "#7c2a8a", "scrollbar_hover": "#a13aa1",
        "switch_fg": "#7c2a8a", "switch_progress": "#ff9e64", "switch_button": "#ffd6fc",
        "dropdown_bg": "#4a1252", "dropdown_hover": "#5c2b63", "dropdown_text": "#ffd6fc",
        "seg_fg": "#4a1252", "seg_text": "#ffd6fc", "seg_selected": "#db2777", "seg_selected_text": "#ffffff"
    },

    # --- 6. MONOCHROME THEME (Light Mode - Minimalist) ---
    "Monochrome": { 
        "mode": "Light",
        "transparent": "transparent",
        "white": "white",
        "black": "black",
        "gold": "#555555",
        "bg_main": "#f5f5f5", "bg_sidebar": "#e5e5e5",
        "card_bg": "#ffffff", "card_border": "#d4d4d4", "card_hover": "#a3a3a3",
        "text_main": "#171717", "text_sub": "#525252", "text_inv": "#ffffff", "text_placeholder": "#a3a3a3",
        
        "text_link": "#007AFF", # Vivid Blue to stand out in Mono

        "accent": "#404040", "accent_hover": "#171717", "text_on_accent": "#ffffff",
        "btn_positive": "#d4d4d4", "btn_positive_hover": "#a3a3a3", "text_on_positive": "#171717", 
        "btn_negative": "#737373", "btn_negative_hover": "#404040", "text_on_negative": "#ffffff", 
        "btn_info": "#e5e5e5", "btn_info_hover": "#d4d4d4", "text_on_info": "#171717",
        "btn_primary": "#171717", "btn_primary_hover": "#404040", "text_on_primary": "#ffffff", 
        "btn_neutral": "#f5f5f5", "btn_neutral_hover": "#e5e5e5", "text_on_neutral": "#171717",
        "entry_bg": "#ffffff", "entry_border": "#171717", "entry_text": "#171717",
        "scrollbar_bg": "transparent", "scrollbar_fg": "#d4d4d4", "scrollbar_hover": "#737373",
        "switch_fg": "#d4d4d4", "switch_progress": "#171717", "switch_button": "#ffffff",
        "dropdown_bg": "#ffffff", "dropdown_hover": "#e5e5e5", "dropdown_text": "#171717",
        "seg_fg": "#ffffff", "seg_text": "#171717", "seg_selected": "#404040", "seg_selected_text": "#ffffff"
    }
}