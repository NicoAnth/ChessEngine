"""
Configuration settings for the chess application.
Contains color schemes, board dimensions, and other constants.
"""
import os
import tkinter as tk
from tkinter import font

# Board configuration
DEFAULT_SQUARE_SIZE = 75
DEFAULT_LABEL_OFFSET = 30

# Color scheme
COLORS = {
    # Board colors
    "light_square": "#EAEAEA",  
    "dark_square": "#4B76A0",   # Dark blue
    "highlight": "#4FA9E6",     # Light blue for highlighted squares
    "move_indicator": "gba(82, 203, 164, 0.4)",  
    "selected_square": "#A4CFFF",  
    "last_move": "#F9C94C",  
    "check": "#FF5C5C",  
    
    # UI colors
    "background": "#EAEAEA",  # Light gray background
    "primary_text": "#303F9F",  # Dark blue text
    "secondary_text": "#000000",  # Black text
    
    # Evaluation bar colors
    "eval_bar_border": "#B0BEC5",    # Bordure légère pour la barre d'évaluation
    "eval_bar_background": "#F5F5F5", # Fond neutre pour la barre
    "eval_white": "#FFFFFF",         # Couleur pour avantage blanc
    "eval_black": "#333333",         # Couleur pour avantage noir
    "eval_white_gradient": "#E3F2FD", # Dégradé pour avantage blanc
    "eval_black_gradient": "#424242", # Dégradé pour avantage noir
    "eval_text_white": "#303F9F",     # Texte sur fond blanc
    "eval_text_black": "#FFFFFF",     # Texte sur fond noir
    "eval_draw": "#9E9E9E",          # Couleur pour position égale
    
    # Button colors
    "control_button": "#7986CB",
    "control_button_active": "#5C6BC0",
    "new_game_button": "#4FA9E6",
    "new_game_button_active": "#388E3C",
    "analysis_button": "#35C2A0",
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
    "black_positive_score": "#6FFF6F",

    "banner_bg": "#EAEAEA",     # Fond du banner des joueurs
    "banner_white_bg": "#FFFFFF",  # Modern white rectangle background
    "banner_black_bg": "#333333",  # Modern black rectangle background
    "banner_white_text": "#000000",  # Black text on white background
    "banner_black_text": "#FFFFFF",  # White text on black background
    "banner_white_piece": "#FFFFFF",
    "banner_black_piece": "#333333",
    "banner_indicator_border": "#CCCCCC",
    "active_player": "#4FA9E6", # Couleur du joueur actif
    "inactive_player": "#757575", # Couleur du joueur inactif

    # Profile Window Colors - Updated for more modern look
    "profile_background": "#F8F9FA",  # Light grey
    "profile_card_bg": "#FFFFFF",     # White for cards
    "profile_card_shadow": "#E9ECEF", # Light shadow color
    "profile_header_bg": "#ECF2FF",   # Very light blue header
    "profile_header_gradient": "#E3EEFF", # Gradient end color
    "profile_header_text": "#1A237E", # Deeper blue for text
    "profile_text": "#344767",        # Dark blue-grey
    "profile_secondary_text": "#67748E", # Medium blue-grey
    "profile_accent": "#4361EE",      # Vibrant blue accent
    "profile_accent_secondary": "#3F37C9", # Secondary accent color
    "profile_accent_hover": "#3A56D4", # Darker blue for hover
    "profile_border": "#DEE2E6",     # Light border color
    "profile_tab_bg": "#F8F9FA",
    "profile_tab_active_bg": "#FFFFFF",
    "profile_tab_text": "#67748E",
    "profile_tab_active_text": "#4361EE",
    "profile_tab_indicator": "#4361EE", # Indicator color for active tab
    "profile_tab_border": "#DEE2E6",
    "profile_button_icon": "#FFFFFF",  # Icon color in buttons
    "profile_history_header_bg": "#F2F5FF", # Light blue for table header
    "profile_history_row_even": "#FFFFFF", 
    "profile_history_row_odd": "#F8F9FA",
    "profile_chart_colors": ["#4361EE", "#3BC9DB", "#38D9A9", "#FD7E14", "#FA5252", "#BE4BDB"], # Colors for charts
}

# Classification colors with gradients where applicable
CLASSIFICATION_COLORS = {
    "Meilleur coup": {"main": "#3BD97B", "secondary": "#A1FECB"},
    "Excellent": {"main": "#6BE29B", "secondary": None},
    "Bon coup": {"main": "#8EF0B5", "secondary": None},
    "Imprécision": {"main": "#F7C76E", "secondary": None},
    "Erreur": {"main": "#FF6B6B", "secondary": None},
    "Grosse erreur": {"main": "#F44336", "secondary": "#FF1744"},
    "Super coup": {"main": "#00E5FF", "secondary": "#89F7FE"},
    "Coup brillant": {"main": "#D500F9", "secondary": "#F770FF"},
    "Théorie": {"main": "#A78BFA ", "secondary": "#C4B5FD"}
}

# Update ERROR_COLORS for backwards compatibility
ERROR_COLORS = {
    "Grosse erreur": {
        "bg": "#FFCDD2",         # Light red background
        "text": "#F44336",       # Main color from CLASSIFICATION_COLORS
        "hover_bg": "#EFBEC3",   # Darker red for hover
        "hover_text": "#FF1744", # Secondary color from CLASSIFICATION_COLORS
        "selected_bg": "#EF9A9A", # Bright red for selection
        "square_color": "#F44336", # Color for highlighting squares on board
        "square_border": "#FF1744", # Border color for highlighted squares
        "indicator_color": "#F44336" # Color for modern error indicator
    },
    "Erreur": {
        "bg": "#FFE0B2",         # Light orange background
        "text": "#FF6B6B",       # Main color from CLASSIFICATION_COLORS
        "hover_bg": "#EFD1A3",   # Darker orange for hover
        "hover_text": "#FF6B6B", # Same as main color (no secondary color)
        "selected_bg": "#FFCC80", # Bright orange for selection
        "square_color": "#FF6B6B", # Color for highlighting squares on board
        "square_border": "#FF6B6B", # Border color for highlighted squares
        "indicator_color": "#FF6B6B" # Color for modern error indicator
    }
}

# Font configurations
FONTS = {
    "title": {"family": "Segoe UI", "size": 18, "weight": "bold"}, # Increased size
    "subtitle": {"family": "Segoe UI", "size": 13, "weight": "bold"},
    "button": {"family": "Segoe UI", "size": 10, "weight": "normal"},
    "label": {"family": "Segoe UI", "size": 11, "weight": "normal"}, # Slightly smaller default label
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
    "move_details": {"family": "Segoe UI", "size": 9, "weight": "normal"},

    # Profile Window Fonts - Updated for more modern look
    "profile_username": {"family": "Segoe UI", "size": 22, "weight": "bold"},
    "profile_header_info": {"family": "Segoe UI", "size": 10, "weight": "normal"},
    "profile_section_title": {"family": "Segoe UI", "size": 14, "weight": "bold"},
    "profile_stat_label": {"family": "Segoe UI", "size": 11, "weight": "normal"},
    "profile_stat_value": {"family": "Segoe UI", "size": 11, "weight": "bold"},
    "profile_history_header": {"family": "Segoe UI", "size": 10, "weight": "bold"},
    "profile_history_row": {"family": "Segoe UI", "size": 10, "weight": "normal"},
    "profile_button": {"family": "Segoe UI", "size": 10, "weight": "bold"}
}

# Engine analysis settings
ENGINE_ANALYSIS = {
    "default_depth": 15,          # Standard depth for position analysis
    "detailed_depth": 20,         # Deeper analysis for detailed evaluations
    "tactical_depth": 16,         # Depth for tactical sequences
    "multipv": 3,                 # Number of alternative moves to consider
    "mate_score": 10000,          # Score value assigned to checkmate
    
    # Number of parallel engine instances to use for analysis
    # This directly controls how many moves can be analyzed simultaneously
    # Higher values use more CPU resources but improve analysis speed
    # If you have more than 8 cores, consider increasing this value
    "analysis_threads": max(1, min(os.cpu_count() // 2, 4)),  # Use half available cores, capped at 4, min 1
    
    # Number of threads used by each Stockfish engine instance internally
    # This is directly passed to Stockfish's own configuration
    # For optimal performance, this can typically be left at 1 since we're running multiple instances
    "engine_threads_per_instance": 1  # Each engine instance uses 1 thread
}

# Expected Points move classification thresholds
MOVE_CLASSIFICATION = {
    # Classification based on expected points loss
    "meilleur_coup_threshold": 0.00,     # No loss of expected points (perfect move)
    "excellent_threshold": 0.02,         # Tiny loss of expected points (0.00-0.02)
    "bon_coup_threshold": 0.05,          # Small loss of expected points (0.02-0.05)
    "imprecision_threshold": 0.10,       # Notable loss of expected points (0.05-0.10)
    "erreur_threshold": 0.20,            # Significant loss of expected points (0.10-0.20)
    "grosse_erreur_threshold": 1.00,     # Major loss of expected points (0.20-1.00)
    
    # Special classification thresholds
    "position_improvement_threshold": 0.15,  # Threshold for position improvement (for Super coup)
    "only_move_eval_drop": 0.4,            # Threshold for "only good move" detection
    "sacrifice_threshold": 1,             # Material value that counts as a sacrifice
    "winning_position_threshold": 0.85,     # Win probability considered "winning position"
}

# Accuracy calculation weights
ACCURACY_WEIGHTS = {
    "Meilleur coup": 100,
    "Excellent": 95,
    "Bon coup": 80,
    "Imprécision": 50,
    "Erreur": 20,
    "Grosse erreur": 0,
    "Super coup": 100,
    "Coup brillant": 100,
    "Théorie": 100  # Les coups d'ouverture sont considérés comme parfaits pour le calcul de précision
}

# Animation settings
ANIMATION = {
    "duration": 250,
    "steps": 15
}

# Status message display duration (milliseconds)
STATUS_DURATION = 3000
