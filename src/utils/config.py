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
    "blunder": "#cc2222"     # Rouge pour les fautes graves
}

# Font configurations
FONTS = {
    "title": {"family": "Segoe UI", "size": 16, "weight": "bold"},
    "button": {"family": "Segoe UI", "size": 10, "weight": "normal"},
    "label": {"family": "Segoe UI", "size": 12, "weight": "normal"},
    "coordinate": {"family": "Segoe UI", "size": 11, "weight": "bold"},
    "analysis_header": {"family": "Segoe UI", "size": 13, "weight": "bold"},
    "analysis_subheader": {"family": "Segoe UI", "size": 11, "weight": "bold"},
    "analysis_text": {"family": "Segoe UI", "size": 10, "weight": "normal"}
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