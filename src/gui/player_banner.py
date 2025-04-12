# --- START OF FILE player_banner.py ---

"""
Player banner component.
Displays player names and colors in a modern, visually appealing format.
"""

import tkinter as tk
from tkinter import font
import chess
from src.utils import config

class PlayerBanner:
    """A modern banner that displays player names and their colors."""
    
    def __init__(self, parent, width=None):
        """
        Initialize the player banner.
        
        Args:
            parent: Parent widget
            width: Optional width for the banner
        """
        self.parent = parent
        self.width = width
        
        # Create the banner container with a subtle background
        self.container = tk.Frame(
            parent,
            bg=config.COLORS.get("banner_bg", "#F0F4F8"),
            padx=15,
            pady=8
        )
        
        # Adapter le banner pour qu'il s'étende avec la fenêtre
        self.container.pack(fill=tk.X, pady=(0, 10))
        
        # Configurer des poids de colonnes pour permettre un redimensionnement approprié
        self.container.columnconfigure(0, weight=1)  # Joueur blanc (à gauche)
        self.container.columnconfigure(1, weight=0)  # Espace central flexible
        self.container.columnconfigure(2, weight=1)  # Joueur noir (à droite)
        
        # Créer des frames pour les joueurs blancs et noirs qui s'adaptent au redimensionnement
        self.white_frame = tk.Frame(
            self.container,
            bg=config.COLORS.get("banner_bg", "#F0F4F8"),
        )
        self.white_frame.grid(row=0, column=0, sticky="w")
        
        # Espace central flexible
        spacer = tk.Frame(
            self.container,
            bg=config.COLORS.get("banner_bg", "#F0F4F8"),
            width=50  # Largeur minimale
        )
        spacer.grid(row=0, column=1)
        
        self.black_frame = tk.Frame(
            self.container,
            bg=config.COLORS.get("banner_bg", "#F0F4F8"),
        )
        self.black_frame.grid(row=0, column=2, sticky="e")
        
        # Create two containers for white and black players
        self.white_container = self._create_player_container(self.white_frame, is_white=True)
        self.black_container = self._create_player_container(self.black_frame, is_white=False)
        
        # Default values
        self.white_name = "Player 1"
        self.black_name = "Player 2"
        
    def _create_player_container(self, parent, is_white):
        """
        Create a container for a player.
        
        Args:
            parent: Parent frame
            is_white: True for white player, False for black
        
        Returns:
            Player container widget
        """
        container = tk.Frame(
            parent,
            bg=config.COLORS.get("banner_bg", "#F0F4F8"),
        )
        container.pack(side=tk.LEFT if is_white else tk.RIGHT)
        
        # Create horizontal layout
        name_container = tk.Frame(
            container,
            bg=config.COLORS.get("banner_bg", "#F0F4F8"),
        )
        name_container.pack(side=tk.LEFT)
        
        # Player color indicator
        color = "#FFFFFF" if is_white else "#111111"
        indicator_size = 24
        
        # Create color indicator canvas with shadow effect
        indicator_canvas = tk.Canvas(
            container,
            width=indicator_size + 4,  # Extra space for shadow
            height=indicator_size + 4,  # Extra space for shadow
            bg=config.COLORS.get("banner_bg", "#F0F4F8"),
            highlightthickness=0
        )
        indicator_canvas.pack(side=tk.LEFT, padx=(0, 10) if is_white else (10, 0))
        
        # Draw shadow
        shadow_offset = 2
        indicator_canvas.create_oval(
            shadow_offset, 
            shadow_offset, 
            indicator_size + shadow_offset, 
            indicator_size + shadow_offset,
            fill="#AAAAAA",
            outline=""
        )
        
        # Draw piece color circle
        indicator_canvas.create_oval(
            0, 0, indicator_size, indicator_size,
            fill=color,
            outline="#DDDDDD" if is_white else "",
            width=1
        )
        
        # Create player name label with custom font - more adaptable avec ellipsis
        name_font = font.Font(family="Segoe UI", size=11, weight="bold")
        
        label = tk.Label(
            name_container,
            font=name_font,
            bg=config.COLORS.get("banner_bg", "#F0F4F8"),
            fg=config.COLORS.get("primary_text", "#111111"),
            anchor="w" if is_white else "e",
            justify=tk.LEFT if is_white else tk.RIGHT
        )
        label.pack(side=tk.LEFT if is_white else tk.RIGHT)
        
        # Store reference to the label
        if is_white:
            self.white_label = label
        else:
            self.black_label = label
            
        return container
    
    def update_names(self, white_name=None, black_name=None, current_turn=None):
        """
        Update the player names and current turn indicator.
        
        Args:
            white_name: Name of the white player (optional)
            black_name: Name of the black player (optional)
            current_turn: Current player turn (chess.WHITE or chess.BLACK)
        """
        # Update names if provided
        if white_name is not None:
            self.white_name = white_name
        
        if black_name is not None:
            self.black_name = black_name
        
        # Format names based on whose turn it is
        if current_turn is not None:
            white_text = f"{self.white_name}"
            black_text = f"{self.black_name}"
            
            # Add turn indicator
            if current_turn == chess.WHITE:
                white_text += " ▶"  # Triangle indicator for current turn
                self.white_label.configure(fg=config.COLORS.get("active_player", "#000000"))
                self.black_label.configure(fg=config.COLORS.get("inactive_player", "#666666"))
            else:
                black_text += " ◀"  # Triangle indicator for current turn
                self.white_label.configure(fg=config.COLORS.get("inactive_player", "#666666"))
                self.black_label.configure(fg=config.COLORS.get("active_player", "#000000"))
        else:
            white_text = self.white_name
            black_text = self.black_name
            self.white_label.configure(fg=config.COLORS.get("primary_text", "#111111"))
            self.black_label.configure(fg=config.COLORS.get("primary_text", "#111111"))
        
        # Mettre à jour les labels avec une limite de caractères si nécessaire
        # On limite à 20 caractères pour éviter les problèmes de mise en page
        max_length = 20
        if len(white_text) > max_length:
            white_text = white_text[:max_length-3] + "..."
        if len(black_text) > max_length:
            black_text = black_text[:max_length-3] + "..."
            
        # Update labels
        self.white_label.configure(text=white_text)
        self.black_label.configure(text=black_text)
        
    def update_from_pgn_headers(self, headers, current_turn=None):
        """
        Update player information from PGN headers.
        
        Args:
            headers: PGN headers dictionary
            current_turn: Current player turn (optional)
        """
        white_name = headers.get("White", "Player 1")
        black_name = headers.get("Black", "Player 2")
        
        # Add player Elo ratings if available
        if "WhiteElo" in headers and headers["WhiteElo"]:
            white_name += f" ({headers['WhiteElo']})"
        
        if "BlackElo" in headers and headers["BlackElo"]:
            black_name += f" ({headers['BlackElo']})"
        
        self.update_names(white_name, black_name, current_turn)

# --- END OF FILE player_banner.py ---