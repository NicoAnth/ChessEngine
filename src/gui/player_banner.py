# --- START OF FILE player_banner.py ---

"""
Player banner component.
Displays player names, Elo (optional), and colors in a modern format.
Indicates the current player's turn.
"""

import tkinter as tk
from tkinter import font
import chess
from src.utils import config

class PlayerBanner:
    """A modern banner that displays player names, Elo, and their colors."""

    def __init__(self, parent, width=None):
        """
        Initialize the player banner.

        Args:
            parent: Parent widget
            width: Optional fixed width for the banner frame (less common now)
        """
        self.parent = parent

        # --- Banner Container ---
        self.container = tk.Frame(
            parent,
            bg=config.COLORS.get("banner_bg", "#E8EDF2"), # Slightly different background
            padx=15,
            pady=10
        )
        if width:
            self.container.configure(width=width)
            self.container.pack_propagate(False) # Prevent resizing if width is fixed

        self.container.pack(fill=tk.X, pady=(0, 10))

        # Configure grid layout (1 row, 2 columns, equal weight)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # --- Player Sections ---
        # Create containers for white and black players using grid
        self.white_section = self._create_player_section(self.container, is_white=True)
        self.white_section.grid(row=0, column=0, sticky="w") # Align left

        self.black_section = self._create_player_section(self.container, is_white=False)
        self.black_section.grid(row=0, column=1, sticky="e") # Align right

        # Default values
        self.white_name_text = "Player 1"
        self.white_elo_text = ""
        self.black_name_text = "Player 2"
        self.black_elo_text = ""

        # Initialize display
        self.update_names() # Call initial update

    def _create_player_section(self, parent_container, is_white):
        """
        Create a visually distinct section for a player.

        Args:
            parent_container: The main banner container.
            is_white: True for white player, False for black.

        Returns:
            The frame containing the player's section.
        """
        section_frame = tk.Frame(
            parent_container,
            bg=config.COLORS.get("banner_bg", "#E8EDF2"),
        )

        # --- Color Indicator ---
        indicator_size = 20 # Slightly smaller indicator
        indicator_canvas = tk.Canvas(
            section_frame,
            width=indicator_size,
            height=indicator_size,
            bg=config.COLORS.get("banner_bg", "#E8EDF2"),
            highlightthickness=0
        )
        piece_color = config.COLORS.get("banner_white_piece", "#FFFFFF") if is_white else config.COLORS.get("banner_black_piece", "#333333")
        outline_color = config.COLORS.get("banner_indicator_border", "#CCCCCC") if is_white else "" # Only outline white piece

        indicator_canvas.create_oval(
            1, 1, indicator_size-1, indicator_size-1, # Add small padding for outline
            fill=piece_color,
            outline=outline_color,
            width=1.5
        )

        # --- Text Info Frame ---
        text_frame = tk.Frame(
            section_frame,
            bg=config.COLORS.get("banner_bg", "#E8EDF2"),
        )

        # Player Name Label
        name_font = font.Font(
            family=config.FONTS.get("banner_name", {}).get("family", "Segoe UI"),
            size=config.FONTS.get("banner_name", {}).get("size", 12),
            weight=config.FONTS.get("banner_name", {}).get("weight", "bold")
        )
        name_label = tk.Label(
            text_frame,
            font=name_font,
            bg=config.COLORS.get("banner_bg", "#E8EDF2"),
            fg=config.COLORS.get("primary_text", "#111111"),
            anchor="w" # Align text left
        )
        name_label.pack(side=tk.TOP, fill=tk.X)

        # Player Elo Label (Optional)
        elo_font = font.Font(
            family=config.FONTS.get("banner_elo", {}).get("family", "Segoe UI"),
            size=config.FONTS.get("banner_elo", {}).get("size", 9),
            slant=config.FONTS.get("banner_elo", {}).get("slant", "italic")
        )
        elo_label = tk.Label(
            text_frame,
            font=elo_font,
            bg=config.COLORS.get("banner_bg", "#E8EDF2"),
            fg=config.COLORS.get("secondary_text", "#555555"),
            anchor="w" # Align text left
        )
        elo_label.pack(side=tk.TOP, fill=tk.X)

        # --- Layout within Section ---
        # Arrange indicator and text frame horizontally
        if is_white:
            indicator_canvas.pack(side=tk.LEFT, padx=(0, 8)) # Indicator on the left
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            name_label.configure(anchor="w") # Anchor left for white
            elo_label.configure(anchor="w")
        else:
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True) # Text first
            indicator_canvas.pack(side=tk.RIGHT, padx=(8, 0)) # Indicator on the right
            name_label.configure(anchor="e") # Anchor right for black
            elo_label.configure(anchor="e")

        # Store references
        if is_white:
            self.white_name_label = name_label
            self.white_elo_label = elo_label
            self.white_indicator_canvas = indicator_canvas # Keep reference if needed later
        else:
            self.black_name_label = name_label
            self.black_elo_label = elo_label
            self.black_indicator_canvas = indicator_canvas

        return section_frame

    def update_names(self, white_name=None, black_name=None, white_elo=None, black_elo=None, current_turn=None):
        """
        Update the player names, Elo, and current turn indicator.

        Args:
            white_name: Name of the white player (optional)
            black_name: Name of the black player (optional)
            white_elo: Elo of the white player (optional, can be "" or None)
            black_elo: Elo of the black player (optional, can be "" or None)
            current_turn: Current player turn (chess.WHITE or chess.BLACK)
        """
        # Update stored names/elos if provided
        if white_name is not None:
            self.white_name_text = white_name
        if black_name is not None:
            self.black_name_text = black_name
        if white_elo is not None:
            self.white_elo_text = str(white_elo) if white_elo else ""
        if black_elo is not None:
            self.black_elo_text = str(black_elo) if black_elo else ""

        # --- Set Text ---
        self.white_name_label.configure(text=self.white_name_text)
        self.black_name_label.configure(text=self.black_name_text)

        self.white_elo_label.configure(text=self.white_elo_text)
        self.black_elo_label.configure(text=self.black_elo_text)

        # --- Update Turn Indication ---
        active_color = config.COLORS.get("active_player", "#000000")
        inactive_color = config.COLORS.get("inactive_player", "#666666")
        active_weight = config.FONTS.get("banner_name_active", {}).get("weight", "bold") # Could be 'bold'
        inactive_weight = config.FONTS.get("banner_name", {}).get("weight", "bold") # Back to normal bold

        # Update fonts based on current turn
        white_name_font = self.white_name_label.cget("font")
        black_name_font = self.black_name_label.cget("font")

        if current_turn is not None:
            if current_turn == chess.WHITE:
                self.white_name_label.configure(fg=active_color)
                self.black_name_label.configure(fg=inactive_color)
                # Optionally make active name bolder (requires font object update)
                self.white_name_label.configure(font=font.Font(font=white_name_font, weight=active_weight))
                self.black_name_label.configure(font=font.Font(font=black_name_font, weight=inactive_weight))

            else: # Black's turn
                self.white_name_label.configure(fg=inactive_color)
                self.black_name_label.configure(fg=active_color)
                # Optionally make active name bolder
                self.white_name_label.configure(font=font.Font(font=white_name_font, weight=inactive_weight))
                self.black_name_label.configure(font=font.Font(font=black_name_font, weight=active_weight))
        else: # Game not started or no turn info
            default_color = config.COLORS.get("primary_text", "#111111")
            self.white_name_label.configure(fg=default_color)
            self.black_name_label.configure(fg=default_color)
            # Reset font weight
            self.white_name_label.configure(font=font.Font(font=white_name_font, weight=inactive_weight))
            self.black_name_label.configure(font=font.Font(font=black_name_font, weight=inactive_weight))

    def update_from_pgn_headers(self, headers, current_turn=None):
        """
        Update player information from PGN headers.

        Args:
            headers: PGN headers dictionary (like game.headers)
            current_turn: Current player turn (optional)
        """
        white_name = headers.get("White", "Player 1")
        black_name = headers.get("Black", "Player 2")
        white_elo = headers.get("WhiteElo", "")
        black_elo = headers.get("BlackElo", "")

        self.update_names(
            white_name=white_name,
            black_name=black_name,
            white_elo=white_elo,
            black_elo=black_elo,
            current_turn=current_turn
        )

# Example Usage (within your main application):
# Assuming 'parent_frame' is where you want to put the banner
# and 'config' is loaded with COLORS and FONTS dictionaries.

# Make sure your config.py has entries like:
# config = {
#     "COLORS": {
#         "banner_bg": "#E8EDF2",
#         "banner_white_piece": "#FFFFFF",
#         "banner_black_piece": "#333333",
#         "banner_indicator_border": "#CCCCCC",
#         "primary_text": "#111111",
#         "secondary_text": "#555555",
#         "active_player": "#0D47A1", # Example active color (dark blue)
#         "inactive_player": "#757575", # Example inactive color (grey)
#         # ... other colors
#     },
#     "FONTS": {
#         "banner_name": {"family": "Segoe UI", "size": 12, "weight": "bold"},
#         "banner_name_active": {"weight": "bold"}, # Can specify different active weight if needed
#         "banner_elo": {"family": "Segoe UI", "size": 9, "slant": "italic"},
#         # ... other fonts
#     }
# }

# In ChessApplication.__init__ or setup_gui:
# self.player_banner = PlayerBanner(self.game_frame) # Or wherever it should go

# In ChessApplication.update_game_info:
# if hasattr(self, 'player_banner'):
#     current_turn = self.game.get_turn()
#     # Get current names/elos if needed, or pass None if only turn updates
#     self.player_banner.update_names(current_turn=current_turn)

# In ChessApplication.load_pgn_file (after loading game):
# if success and hasattr(self, 'player_banner'):
#     self.player_banner.update_from_pgn_headers(pgn_game.headers, self.game.get_turn())

# In ChessApplication.new_game:
# if hasattr(self, 'player_banner'):
#     self.player_banner.update_names(
#         white_name="Player 1", black_name="Player 2",
#         white_elo="", black_elo="",
#         current_turn=chess.WHITE # Or self.game.get_turn()
#     )

# --- END OF FILE player_banner.py ---