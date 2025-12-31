# ==============================================================================
#   ICONS & SYMBOLS
# ==============================================================================
# Simple unicode text icons used throughout the UI to avoid image dependencies.

# General Actions
ICON_CLEAR    = "✕"
ICON_HISTORY  = "📜"
ICON_SETTINGS = "⚙"
ICON_UPDATE   = "↻"
ICON_LINK     = "🔗"
ICON_ADD      = "+"
ICON_REMOVE   = "×"
ICON_SAVE     = "💾"
ICON_CHECK    = "✓"
ICON_EDIT     = "⚙" # Updated to Cog Wheel as requested
ICON_SEARCH   = "🔍"
ICON_ACTION   = "⚡" # Added

# File Actions
ICON_OPEN     = "📂" # Open File / Folder
ICON_SHOW     = "👁"  # Show in Explorer
ICON_GO       = "➜"  # Navigation / Open View

# Navigation / Playback
ICON_LEFT        = "«"
ICON_RIGHT       = "»"
ICON_ARROW_RIGHT = "▶"
ICON_ARROW_DOWN  = "▼"
ICON_PLAY        = "▶"

# Favorites & Status
ICON_FAV_ON   = "★"
ICON_FAV_OFF  = "☆"
ICON_RANDOM   = "🎲"
ICON_STATS    = "📊"
ICON_PALETTE  = "🎨"
ICON_INFO     = "ℹ" # Added

# Cards / Library Types
ICON_FOLDER   = "📁"
ICON_LIBRARY  = "📚"  # Used for "All Stickers"
ICON_BATCH    = "📚"  # Used for batch selection in Details
ICON_FILE     = "📄"
ICON_TAG      = "🏷"  # Added

# Formats (Used in Details Panel)
ICON_FMT_ANIM   = "🎬"
ICON_FMT_STATIC = "🖼️"
ICON_FMT_MIXED  = "🎭"

# ==============================================================================
#   FONT DEFINITIONS
# ==============================================================================
# Standardized font tuples for CustomTkinter widgets.

FONT_BIG_HEADER = ("Segoe UI Display", 28, "bold")
FONT_HEADER     = ("Segoe UI Display", 24, "bold")
FONT_DISPLAY    = ("Segoe UI", 20, "bold")
FONT_TITLE      = ("Segoe UI", 16, "bold")
FONT_NORMAL     = ("Segoe UI", 14)
FONT_SMALL      = ("Segoe UI", 12)
FONT_CAPTION    = ("Segoe UI", 11)

# ==============================================================================
#   LAYOUT CONSTANTS
# ==============================================================================

# Image Sizes for different view modes
ICON_SIZE_XL   = (220, 220) 
ICON_SIZE_L    = (128, 128)
ICON_SIZE_S    = (45, 45)   
ICON_SIZE_LIST = (35, 35)

# Standard padding
CARD_PADDING   = 8
SIDEBAR_WIDTH = 250
DETAIL_WIDTH = 300