# --- START OF FILE player_banner.py ---

"""
Player banner component.
Displays player names, Elo (optional), colors, and time control in a modern format.
Indicates the current player's turn.
"""

import tkinter as tk
from tkinter import font
import chess
import re # Import regex for parsing
from src.utils import config

class PlayerBanner:
    """A modern banner that displays player names, Elo, time control, and their colors."""

    def __init__(self, parent, width=None, top_padding=0):
        """
        Initialize the player banner.

        Args:
            parent: Parent widget
            width: Optional fixed width for the banner frame (less common now)
            top_padding: Optional top padding for the banner (default: 0)
        """
        self.parent = parent

        # --- Banner Container ---
        self.container = tk.Frame(
            parent,
            bg=config.COLORS.get("banner_bg", "#E8EDF2"), # Slightly different background
            padx=5,  # Reduced container padding slightly
            pady=10
        )
        if width:
            self.container.configure(width=width)
            self.container.pack_propagate(False) # Prevent resizing if width is fixed

        # Use the configurable top_padding
        self.container.pack(fill=tk.X, pady=(top_padding, 10))

        # Configure grid layout (1 row, 3 columns: Player | Time | Player)
        self.container.grid_columnconfigure(0, weight=1) # White player section expands
        self.container.grid_columnconfigure(1, weight=0) # Time control section stays centered
        self.container.grid_columnconfigure(2, weight=1) # Black player section expands
        self.container.grid_rowconfigure(0, weight=1)

        # --- Player Sections ---
        # Create containers for white and black players using grid
        self.white_section = self._create_player_section(self.container, is_white=True)
        self.white_section.grid(row=0, column=0, sticky="ew") # Align left, expand horizontally

        # --- Time Control Section ---
        self.time_control_label = self._create_time_control_section(self.container)
        self.time_control_label.grid(row=0, column=1, sticky="ns", padx=10) # Center column, vertical stretch, add padding

        # --- Black Player Section ---
        self.black_section = self._create_player_section(self.container, is_white=False)
        self.black_section.grid(row=0, column=2, sticky="ew") # Align right, expand horizontally

        # Default values
        self.white_name_text = "Player 1"
        self.white_elo_text = ""
        self.black_name_text = "Player 2"
        self.black_elo_text = ""
        self.time_control_text = "" # Default time control text

        # Initialize display
        self.update_names() # Call initial update

    def _create_player_section(self, parent_container, is_white):
        """
        Create a visually distinct modern rectangular section for a player.
        (Code remains largely the same as before, just minor adjustments might be needed for spacing if any)

        Args:
            parent_container: The main banner container.
            is_white: True for white player, False for black.

        Returns:
            The frame containing the player's section.
        """
        # Colors for the modern rectangular design
        white_bg = config.COLORS.get("banner_white_bg", "#FFFFFF")
        black_bg = config.COLORS.get("banner_black_bg", "#333333")
        white_text = config.COLORS.get("banner_white_text", "#000000")
        black_text = config.COLORS.get("banner_black_text", "#FFFFFF")

        # Select colors based on player
        bg_color = white_bg if is_white else black_bg
        text_color = white_text if is_white else black_text

        # Section frame to hold the rectangle, allows alignment within the grid cell
        section_frame = tk.Frame(
            parent_container,
            bg=config.COLORS.get("banner_bg", "#E8EDF2"), # Match container background
        )

        # Create the rectangular container (visual element)
        rect_frame = tk.Frame(
            section_frame,
            bg=bg_color,
            padx=15,
            pady=8,
            highlightthickness=0,
            bd=0
        )

        # Text Info Frame inside the rectangle
        text_frame = tk.Frame(
            rect_frame,
            bg=bg_color,
        )

        # Player Name Label
        name_font_config = config.FONTS.get("banner_name", {})
        name_font = font.Font(
            family=name_font_config.get("family", "Segoe UI"),
            size=name_font_config.get("size", 12),
            weight=name_font_config.get("weight", "bold")
        )
        name_label = tk.Label(
            text_frame,
            font=name_font,
            bg=bg_color,
            fg=text_color,
            anchor="w" if is_white else "e" # Align text left for white, right for black
        )
        name_label.pack(side=tk.TOP, fill=tk.X)

        # Player Elo Label (Optional)
        elo_font_config = config.FONTS.get("banner_elo", {})
        elo_font = font.Font(
            family=elo_font_config.get("family", "Segoe UI"),
            size=elo_font_config.get("size", 9),
            slant=elo_font_config.get("slant", "italic")
        )
        elo_label = tk.Label(
            text_frame,
            font=elo_font,
            bg=bg_color,
            fg=text_color,
            anchor="w" if is_white else "e" # Align text left for white, right for black
        )
        elo_label.pack(side=tk.TOP, fill=tk.X)

        # --- Layout within Section ---
        text_frame.pack(side=tk.LEFT if is_white else tk.RIGHT, fill=tk.BOTH, expand=True) # Align text left/right
        rect_frame.pack(side=tk.LEFT if is_white else tk.RIGHT, fill=tk.BOTH, expand=True) # Rectangle fills its part of the section

        # Store references
        if is_white:
            self.white_name_label = name_label
            self.white_elo_label = elo_label
            self.white_rect_frame = rect_frame
        else:
            self.black_name_label = name_label
            self.black_elo_label = elo_label
            self.black_rect_frame = rect_frame

        return section_frame

    def _create_time_control_section(self, parent_container):
        """Creates the label for displaying the time control."""
        tc_font_config = config.FONTS.get("banner_time_control", {})
        tc_font = font.Font(
            family=tc_font_config.get("family", "Segoe UI"),
            size=tc_font_config.get("size", 10),
            weight=tc_font_config.get("weight", "normal")
        )
        tc_color = config.COLORS.get("banner_time_control_text", "#555555") # A medium gray color
        bg_color = config.COLORS.get("banner_bg", "#E8EDF2") # Match container background

        time_control_label = tk.Label(
            parent_container,
            font=tc_font,
            fg=tc_color,
            bg=bg_color,
            text="" # Start empty
        )
        return time_control_label

    def _format_time_control(self, tc_string):
        """
        Formats the PGN TimeControl string into a readable format (MM:SS | Incr).

        Args:
            tc_string: The TimeControl string from PGN headers.

        Returns:
            A formatted string for display, or an empty string if invalid/unsupported.
        """
        if not tc_string or tc_string == "-" or tc_string == "?":
            return ""
        if tc_string == "*":
            return "Unlimited"

        # Try to match common formats like "Seconds+Increment" or just "Seconds"
        match = re.match(r"(\d+)(?:\+(\d+))?", tc_string)
        if match:
            base_seconds = int(match.group(1))
            increment_seconds = int(match.group(2)) if match.group(2) else 0

            minutes = base_seconds // 60
            seconds = base_seconds % 60
            formatted_time = f"{minutes:01d}:{seconds:02d}" # MM:SS format (don't force 2 digits for minutes)

            if increment_seconds > 0:
                return f"{formatted_time} | {increment_seconds}"
            else:
                return formatted_time
        else:
            # Handle other potential formats like moves/time (e.g., 40/7200) if needed
            # For now, just return the raw string if it doesn't match the expected pattern
            # or return empty if it's likely not a standard time control we want to show.
            # Let's return empty for unknown formats for now.
            # Consider logging a warning here if needed: print(f"Unknown TimeControl format: {tc_string}")
            return "" # Or maybe tc_string if you want to display unknowns literally

    def update_names(self, white_name=None, black_name=None, white_elo=None, black_elo=None, current_turn=None, time_control_text=None):
        """
        Update the player names, Elo, current turn indicator, and time control.

        Args:
            white_name: Name of the white player (optional)
            black_name: Name of the black player (optional)
            white_elo: Elo of the white player (optional, can be "" or None)
            black_elo: Elo of the black player (optional, can be "" or None)
            current_turn: Current player turn (chess.WHITE or chess.BLACK)
            time_control_text: Formatted time control string (optional)
        """
        # Update stored names/elos/time control if provided
        if white_name is not None:
            self.white_name_text = white_name
        if black_name is not None:
            self.black_name_text = black_name
        if white_elo is not None:
            self.white_elo_text = str(white_elo) if white_elo else ""
        if black_elo is not None:
            self.black_elo_text = str(black_elo) if black_elo else ""
        if time_control_text is not None:
             self.time_control_text = time_control_text # Update stored text

        # --- Set Text ---
        self.white_name_label.configure(text=self.white_name_text)
        self.black_name_label.configure(text=self.black_name_text)
        self.white_elo_label.configure(text=self.white_elo_text)
        self.black_elo_label.configure(text=self.black_elo_text)
        self.time_control_label.configure(text=self.time_control_text) # Update time control display

        # Default text colors
        white_text_color = config.COLORS.get("banner_white_text", "#000000")
        black_text_color = config.COLORS.get("banner_black_text", "#FFFFFF")

        # Active player color (highlight color)
        active_color = config.COLORS.get("active_player", "#0D47A1") # Use a single active color for simplicity now

        # --- Update Turn Indication (Color and Font Weight) ---
        active_weight = config.FONTS.get("banner_name_active", {}).get("weight", "bold")
        inactive_weight = config.FONTS.get("banner_name", {}).get("weight", "bold") # Keep original weight reference

        # Get base fonts (to avoid cumulative changes)
        white_name_base_font = font.Font(font=self.white_name_label.cget("font"))
        white_name_base_font.configure(weight=inactive_weight) # Ensure base is inactive weight
        black_name_base_font = font.Font(font=self.black_name_label.cget("font"))
        black_name_base_font.configure(weight=inactive_weight) # Ensure base is inactive weight

        white_font_to_use = white_name_base_font
        black_font_to_use = black_name_base_font
        white_name_fg = white_text_color
        white_elo_fg = white_text_color
        black_name_fg = black_text_color
        black_elo_fg = black_text_color

        if current_turn is not None:
            if current_turn == chess.WHITE:
                # White is active
                white_name_fg = active_color
                # Use a font object configured with the active weight
                white_font_to_use = font.Font(font=white_name_base_font)
                white_font_to_use.configure(weight=active_weight)
                # Black remains inactive
                black_font_to_use = black_name_base_font # Already configured for inactive
            else:  # Black's turn
                # Black is active
                black_name_fg = active_color
                 # Use a font object configured with the active weight
                black_font_to_use = font.Font(font=black_name_base_font)
                black_font_to_use.configure(weight=active_weight)
                # White remains inactive
                white_font_to_use = white_name_base_font # Already configured for inactive
        # else: Game not started or no turn info - defaults are already set

        # Apply the determined configurations
        self.white_name_label.configure(fg=white_name_fg, font=white_font_to_use)
        self.white_elo_label.configure(fg=white_elo_fg) # Elo usually keeps normal color/font
        self.black_name_label.configure(fg=black_name_fg, font=black_font_to_use)
        self.black_elo_label.configure(fg=black_elo_fg) # Elo usually keeps normal color/font


    def update_from_pgn_headers(self, headers, current_turn=None):
        """
        Update player information and time control from PGN headers.

        Args:
            headers: PGN headers dictionary (like game.headers)
            current_turn: Current player turn (optional)
        """
        white_name = headers.get("White", "Player 1")
        black_name = headers.get("Black", "Player 2")
        white_elo = headers.get("WhiteElo", "")
        black_elo = headers.get("BlackElo", "")
        time_control_str = headers.get("TimeControl", "") # Get TimeControl header

        # Format the time control string
        formatted_tc = self._format_time_control(time_control_str)

        self.update_names(
            white_name=white_name,
            black_name=black_name,
            white_elo=white_elo,
            black_elo=black_elo,
            current_turn=current_turn,
            time_control_text=formatted_tc # Pass the formatted string
        )

# --- END OF FILE player_banner.py ---