"""
Configuration settings for the chess application.
Contains color schemes, board dimensions, and other constants.
"""

# Board configuration
DEFAULT_SQUARE_SIZE = 75
DEFAULT_LABEL_OFFSET = 30

# Color scheme
COLORS = {
    # Board colors
    "light_square": "#E8EDF9",  # Light blue-white
    "dark_square": "#7D93B0",   # Medium slate blue
    "highlight": "#6FCF97",     # Soft green
    "move_indicator": "rgba(109, 217, 178, 0.5)",  # Semi-transparent green
    "selected_square": "#8BB3FF",  # Light blue
    "last_move": "#FFD700",  # Gold
    "check": "#FF6B6B",  # Soft red
    
    # UI colors
    "background": "#F0F2F5",  # Light gray background
    "primary_text": "#303F9F",  # Dark blue text
    "secondary_text": "#000000",  # Black text
    
    # Button colors
    "control_button": "#7986CB",
    "control_button_active": "#5C6BC0",
    "new_game_button": "#4CAF50",
    "new_game_button_active": "#388E3C",
    "analysis_button": "#FF9800",
    "analysis_button_active": "#F57C00",
        
    # Tab colors
    "tab_background": "#F0F2F5",  # Same as background
    "tab_selected_background": "#FFFFFF",  # White background for selected tabs
    "tab_text": "#303F9F",  # Same as primary_text
    "tab_selected_text": "#000000",  # Black text for selected tabs
    "tab_underline": "#F0F2F5",  # Same as background (invisible)
    "tab_selected_underline": "#7986CB",  # Same as control_button
        
    # Status colors
    "success": "#4CAF50",  # Green
    "warning": "#FF9800",  # Orange
    "error": "#E53935",    # Red
        
    # Move classification colors
    "excellent": "#2ba92b",  # Vert foncé pour les coups excellents
    "good": "#75b32e",       # Vert clair pour les bons coups
    "ok": "#3582c4",         # Bleu pour les coups corrects
    "inaccuracy": "#e69d00", # Ambre pour les imprécisions
    "mistake": "#df7d00",    # Orange pour les erreurs
    "blunder": "#cc2222",    # Rouge pour les fautes graves
    
    # Move analysis colors
    "moves_title_text": "#333333",
    "header_background": "#FFFFFF", 
    "header_text": "#333333",
    "separator": "#CCCCCC",
    "move_number": "#777777",
    
    # White move card colors
    "white_move_background": "#FFFFFF",
    "white_move_hover": "#ECF4FF",
    "white_move_text": "#333333",
    "white_move_secondary_text": "#666666",
    "white_move_border": "#E0E0E0",
    "white_move_highlight": "#D4E6FF",
    
    # Black move card colors
    "black_move_background": "#2C2C2C",
    "black_move_hover": "#3D3D3D",
    "black_move_text": "#FFFFFF",
    "black_move_secondary_text": "#CCCCCC",
    "black_quality_text": "#BBBBBB",
    "black_move_border": "#444444",
    "black_move_highlight": "#4A4A8C",
    
    # Score change colors
    "negative_score": "#FF5252",
    "positive_score": "#4CAF50",
    "black_negative_score": "#FF7070",
    "black_positive_score": "#6FFF6F"
}

# Error highlighting colors for move analysis
ERROR_COLORS = {
    "Grosse erreur": {
        "bg": "#FFCDD2",         # Light red background
        "text": "#D32F2F",       # Dark red text
        "hover_bg": "#EFBEC3",   # Darker red for hover
        "hover_text": "#C62828", # Darker red text for hover
        "selected_bg": "#EF9A9A", # Bright red for selection
        "square_color": "#FF5252", # Color for highlighting squares on board
        "square_border": "#D32F2F", # Border color for highlighted squares
        "indicator_color": "#D32F2F" # Color for modern error indicator
    },
    "Erreur": {
        "bg": "#FFE0B2",         # Light orange background
        "text": "#F57C00",       # Dark orange text
        "hover_bg": "#EFD1A3",   # Darker orange for hover
        "hover_text": "#E65100", # Darker orange text for hover
        "selected_bg": "#FFCC80", # Bright orange for selection
        "square_color": "#FF9800", # Color for highlighting squares on board
        "square_border": "#F57C00", # Border color for highlighted squares
        "indicator_color": "#F57C00" # Color for modern error indicator
    }
}

# Font configurations
FONTS = {
    "title": {"family": "Segoe UI", "size": 16, "weight": "bold"},
    "button": {"family": "Segoe UI", "size": 10, "weight": "normal"},
    "label": {"family": "Segoe UI", "size": 12, "weight": "normal"},
    "coordinate": {"family": "Segoe UI", "size": 11, "weight": "bold"},
    "analysis_header": {"family": "Segoe UI", "size": 13, "weight": "bold"},
    "analysis_subheader": {"family": "Segoe UI", "size": 11, "weight": "bold"},
    "analysis_text": {"family": "Segoe UI", "size": 10, "weight": "normal"},
    
    # Move analysis fonts
    "moves_title": {"family": "Segoe UI", "size": 14, "weight": "bold"},
    "moves_header": {"family": "Segoe UI", "size": 10, "weight": "bold"},
    "move_notation": {"family": "Segoe UI", "size": 12, "weight": "bold"},
    "move_quality": {"family": "Segoe UI", "size": 9, "weight": "normal"},
    "move_evaluation": {"family": "Segoe UI", "size": 11, "weight": "bold"},
    "move_details": {"family": "Segoe UI", "size": 9, "weight": "normal"}
}

# Engine analysis settings
ENGINE_ANALYSIS = {
    "default_depth": 15,
    "detailed_depth": 18,
    "multipv": 3,
    "mate_score": 10000
}

# Move classification thresholds
MOVE_CLASSIFICATION = {
    "excellent_threshold": 0.5,
    "good_threshold": 0.2,
    "inaccuracy_threshold": -0.5,
    "mistake_threshold": -1.0,
    "blunder_threshold": -2.0
}

# Accuracy calculation weights
ACCURACY_WEIGHTS = {
    "Excellent": 100,
    "Bon coup": 80,
    "Imprécision": 50,
    "Erreur": 20,
    "Grosse erreur": 0
}

# Animation settings
ANIMATION = {
    "duration": 250,
    "steps": 15
}

# Status message display duration (milliseconds)
STATUS_DURATION = 3000