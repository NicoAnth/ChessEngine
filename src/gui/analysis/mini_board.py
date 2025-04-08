"""Chess board visualization for analysis."""

import tkinter as tk
import chess
from src.utils import config
from tkinter import font

class MiniChessBoard(tk.Canvas):
    """A simple chess board canvas for displaying positions."""
    
    def __init__(self, parent, piece_images=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.configure(bg="white", highlightthickness=1, highlightbackground="#E0E0E0")
        self.square_size = 70  # Increased from 60 to 70 for an even larger board
        self.margin = 25      # Increased from 20 to 25 for better proportions
        self.flipped = False  # Track board orientation
        
        # Modern styling for coordinate markers
        self.marker_font = font.Font(family="Segoe UI", size=11, weight="normal")  # Increased font size
        self.light_marker_color = "#8596AA"  # Subtle blue-gray that works on both light and dark squares
        self.dark_marker_color = "#2A3542"   # Darker shade for contrast on light squares
        
        # Import the resource_loader here
        from src.utils.resource_loader import load_piece_images
        
        # Load piece images directly at the correct size
        self.pieces = {}
        piece_types = ['p', 'n', 'b', 'r', 'q', 'k', 'P', 'N', 'B', 'R', 'Q', 'K']
        
        # Map chess piece symbols to image keys
        self.piece_name_map = {
            'p': 'black-pawn', 'n': 'black-knight', 'b': 'black-bishop', 
            'r': 'black-rook', 'q': 'black-queen', 'k': 'black-king',
            'P': 'white-pawn', 'N': 'white-knight', 'B': 'white-bishop', 
            'R': 'white-rook', 'Q': 'white-queen', 'K': 'white-king'
        }
        
        # Load the images at the appropriate size
        self.piece_images = load_piece_images(self.square_size)
        
        # Map the piece symbols to the loaded images
        for piece in piece_types:
            image_key = self.piece_name_map.get(piece)
            if image_key in self.piece_images:
                self.pieces[piece] = self.piece_images[image_key]
            else:
                self.pieces[piece] = None
        
        # Load error indicator icons
        self._load_error_icons()
        
        self.board = chess.Board()  # Initial position
        self.draw_board()
    
    def _load_error_icons(self):
        """Load all move classification icons and resize them appropriately."""
        from PIL import Image, ImageTk
        import os
        
        # Increase icon size to 60% of square size for better visibility
        icon_size = int(self.square_size * 0.6)
        
        try:
            # Get the base directory
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            
            # Initialize all icons as None
            self.meilleur_coup_icon = None
            self.excellent_icon = None
            self.bon_coup_icon = None
            self.imprecision_icon = None
            self.erreur_icon = None
            self.grosse_erreur_icon = None
            self.super_coup_icon = None
            self.coup_brillant_icon = None
            
            # Define all icon paths
            icon_paths = {
                "meilleur_coup": os.path.join(base_dir, "images", "Meilleur_coup.png"),
                "excellent": os.path.join(base_dir, "images", "excellent.png"),
                "bon_coup": os.path.join(base_dir, "images", "Bon_coup.png"),
                "imprecision": os.path.join(base_dir, "images", "Imprecision.png"),
                "erreur": os.path.join(base_dir, "images", "mistake.png"),
                "grosse_erreur": os.path.join(base_dir, "images", "blunder.png"),
                "super_coup": os.path.join(base_dir, "images", "super_coup.png"),
                "coup_brillant": os.path.join(base_dir, "images", "Brillant.png")
            }
            
            # Load each icon
            for icon_name, icon_path in icon_paths.items():
                if os.path.exists(icon_path):
                    img = Image.open(icon_path)
                    img = img.resize((icon_size, icon_size), Image.LANCZOS)
                    setattr(self, f"{icon_name}_icon", ImageTk.PhotoImage(img))
                else:
                    print(f"Warning: {icon_name} icon not found at {icon_path}")
            
            # For backward compatibility (these variables are used in existing code)
            self.mistake_icon = self.erreur_icon
            self.blunder_icon = self.grosse_erreur_icon
                
        except Exception as e:
            print(f"Error loading classification icons: {e}")
            # Reset all icons to None in case of error
            self.meilleur_coup_icon = None
            self.excellent_icon = None
            self.bon_coup_icon = None
            self.imprecision_icon = None
            self.erreur_icon = None 
            self.grosse_erreur_icon = None
            self.super_coup_icon = None
            self.coup_brillant_icon = None
            self.mistake_icon = None
            self.blunder_icon = None
    
    def draw_board(self):
        """Draw the empty chess board with coordinates outside."""
        self.delete("all")  # Clear canvas
        
        # Calculate board size including margins
        board_size = self.square_size * 8
        total_size = board_size + 2 * self.margin
        
        # Configure canvas size to include margins
        self.config(width=total_size, height=total_size)
        
        # Draw squares with offset for margins
        for row in range(8):
            for col in range(8):
                # Calculate position with margin offset
                actual_row = row if not self.flipped else 7 - row
                actual_col = col if not self.flipped else 7 - col
                
                x1 = actual_col * self.square_size + self.margin
                y1 = actual_row * self.square_size + self.margin
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                
                # Determine square color (light or dark)
                is_light = (row + col) % 2 == 0
                fill_color = config.COLORS["light_square"] if is_light else config.COLORS["dark_square"]
                
                # Draw square
                self.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline="")
        
        # Add modern coordinate markers outside the board
        self._draw_modern_coordinates()
    
    def _draw_modern_coordinates(self):
        """Draw modernized coordinate markers outside the board edges."""
        square_size = self.square_size
        margin = self.margin
        
        # Horizontal coordinates (a-h) along the bottom
        for i in range(8):
            # Get the file letter (a-h)
            # If flipped, reverse the file order
            file_idx = 7 - i if self.flipped else i
            file_letter = chr(97 + file_idx)
            
            # Position centered below each square
            x = margin + (i * square_size) + (square_size // 2)
            y = margin + (8 * square_size) + (margin // 2)
            
            # Create elegant text
            self.create_text(
                x, y, 
                text=file_letter, 
                font=self.marker_font, 
                fill=self.dark_marker_color,
                tags="coordinate"
            )
            
        # Vertical coordinates (1-8) along the left side
        for i in range(8):
            # Get the rank number (8 to 1, top to bottom)
            # If flipped, reverse the rank order
            rank_idx = i if self.flipped else 7 - i
            rank_number = str(rank_idx + 1)
            
            # Position centered to the left of each square
            x = margin // 2
            y = margin + (i * square_size) + (square_size // 2)
            
            # Create elegant text
            self.create_text(
                x, y, 
                text=rank_number, 
                font=self.marker_font, 
                fill=self.dark_marker_color,
                tags="coordinate"
            )
    
    def draw_position(self, board=None):
        """Draw pieces on the board based on FEN position."""
        if board:
            self.board = board
        
        self.draw_board()  # Redraw empty board
        
        # Draw pieces according to current position
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if not piece:
                continue
                
            # Convert square index to coordinates
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)  # Invert row (chess uses 0=bottom, tkinter uses 0=top)
            
            # Apply flip if needed
            if self.flipped:
                col = 7 - col
                row = 7 - row
            
            # Calculate position including margin
            x = col * self.square_size + self.margin + self.square_size/2
            y = row * self.square_size + self.margin + self.square_size/2
            
            # Get piece symbol
            piece_symbol = piece.symbol()
            
            if self.pieces[piece_symbol]:
                # Draw piece using image
                self.create_image(x, y, image=self.pieces[piece_symbol], tags="piece")
            else:
                # Draw text representation as fallback
                color = "white" if piece_symbol.isupper() else "black"
                fill_color = "#000000" if color == "white" else "#FFFFFF"
                self.create_text(
                    x, y, 
                    text=piece_symbol.upper(), 
                    fill=fill_color,
                    font=("Arial", int(self.square_size * 0.6), "bold"),
                    tags="piece"
                )
    
    def flip_board(self):
        """Toggle the board orientation."""
        self.flipped = not self.flipped
        self.draw_position()  # Redraw with new orientation
        return self.flipped  # Return new state for potential UI updates
    
    def update_to_position(self, fen):
        """Update board to show the position from FEN."""
        try:
            self.board = chess.Board(fen)
            self.draw_position()
        except Exception as e:
            print(f"Error updating chess position: {e}")
    
    def draw_error_indicator(self, from_square, to_square, color="red", width=3):
        """Draw an arrow to indicate an error move."""
        if from_square is None or to_square is None:
            return
            
        # Calculate square coordinates
        file_from, rank_from = chess.square_file(from_square), chess.square_rank(from_square)
        file_to, rank_to = chess.square_file(to_square), chess.square_rank(to_square)
        
        # Apply flipping if needed
        if self.flipped:
            file_from, rank_from = 7 - file_from, 7 - rank_from
            file_to, rank_to = 7 - file_to, 7 - rank_to
        
        # Convert to canvas coordinates (center of squares)
        x1 = (file_from * self.square_size) + (self.square_size // 2) + self.margin
        y1 = ((7 - rank_from) * self.square_size) + (self.square_size // 2) + self.margin
        x2 = (file_to * self.square_size) + (self.square_size // 2) + self.margin
        y2 = ((7 - rank_to) * self.square_size) + (self.square_size // 2) + self.margin
        
        # Calculate arrow head points
        arrow_size = 10
        dx, dy = x2 - x1, y2 - y1
        length = (dx**2 + dy**2)**0.5
        udx, udy = dx / length, dy / length  # Unit vector
        
        # Adjust end point to stop at square edge
        x2 = x2 - udx * (self.square_size // 3)
        y2 = y2 - udy * (self.square_size // 3)
        
        # Recalculate with adjusted end point
        dx, dy = x2 - x1, y2 - y1
        length = (dx**2 + dy**2)**0.5
        udx, udy = dx / length, dy / length  # Unit vector
        
        # Calculate perpendicular unit vector
        perpx, perpy = -udy, udx
        
        # Arrow head points
        ax1 = x2 - arrow_size * udx + arrow_size * 0.5 * perpx
        ay1 = y2 - arrow_size * udy + arrow_size * 0.5 * perpy
        ax2 = x2 - arrow_size * udx - arrow_size * 0.5 * perpx
        ay2 = y2 - arrow_size * udy - arrow_size * 0.5 * perpy
        
        # Draw line with semi-transparency
        arrow_line = self.create_line(
            x1, y1, x2, y2, 
            fill=color, 
            width=width,
            arrow="last",
            arrowshape=(15, 15, 7),
            tags="arrow"
        )
        
        return arrow_line
    
    def highlight_error_move(self, move_uci, best_move_uci=None, error_type=None):
        """Highlight an error move and its better alternative."""
        # Clear existing arrows and highlights
        self.delete("arrow")
        self.delete("highlight")
        self.delete("error_symbol")
        
        if not move_uci:
            return
            
        try:
            # Parse the error move
            from_square = chess.parse_square(move_uci[:2])
            to_square = chess.parse_square(move_uci[2:4])
            
            # Get error color from config based on error type
            error_color = "#F44336"  # Default red color
            square_color = None
            square_border = None
            symbol_type = "mistake"  # Default symbol type
            
            if error_type and error_type in config.ERROR_COLORS:
                error_color = config.ERROR_COLORS[error_type]["text"]
                square_color = config.ERROR_COLORS[error_type]["square_color"]
                square_border = config.ERROR_COLORS[error_type]["square_border"]
                symbol_type = "blunder" if error_type == "Grosse erreur" else "mistake"
            
            # Highlight the destination square of the error move with border
            if square_color:
                self.highlight_square(
                    to_square, 
                    color=square_color, 
                    border_color=square_border,
                    tag="highlight"
                )
            
            # Draw error arrow from source to destination
            self.draw_error_indicator(from_square, to_square, color=error_color, width=3)
            
            # Add error icon based on error type (mistake or blunder)
            self.place_error_icon(to_square, error_type=symbol_type)
            
            # Draw green arrow for the best move if provided
            if best_move_uci and len(best_move_uci) >= 4:
                best_from = chess.parse_square(best_move_uci[:2])
                best_to = chess.parse_square(best_move_uci[2:4])
                self.draw_error_indicator(best_from, best_to, color="#4CAF50", width=3)
                
        except Exception as e:
            print(f"Error highlighting move: {e}")
    
    def place_classification_icon(self, square, classification_type):
        """Place a classification icon on the corner of a square based on the move classification type.
        
        Args:
            square: Chess square index
            classification_type: The type of classification (e.g., "Meilleur coup", "Excellent", etc.)
        """
        if square is None:
            return
            
        # Calculate square coordinates
        file_idx = chess.square_file(square)
        rank_idx = chess.square_rank(square)
        
        # Apply flipping if needed
        if self.flipped:
            file_idx, rank_idx = 7 - file_idx, 7 - rank_idx
        
        # Calculate the intersection point (top-right corner of the square)
        x = (file_idx * self.square_size) + self.margin + self.square_size
        y = ((7 - rank_idx) * self.square_size) + self.margin
        
        # Select the appropriate icon based on classification
        icon_map = {
            "Meilleur coup": self.meilleur_coup_icon,
            "Excellent": self.excellent_icon,
            "Bon coup": self.bon_coup_icon,
            "Imprécision": self.imprecision_icon,
            "Erreur": self.erreur_icon,
            "Grosse erreur": self.grosse_erreur_icon,
            "Super coup": self.super_coup_icon,
            "Coup brillant": self.coup_brillant_icon
        }
        
        # Get corresponding icon
        icon = icon_map.get(classification_type)
        
        # Use tag specific to the classification for easier removal
        tag = f"{classification_type.lower().replace(' ', '_')}_symbol"
        
        # Remove any existing classification icons
        self.delete("classification_symbol")
        
        # If we have the icon, place it on the board with CENTER anchor
        if icon:
            self.create_image(x, y, image=icon, tags=["classification_symbol", tag], anchor=tk.CENTER)
        else:
            # Fallback: Draw a colored circle if icon not found
            size = int(self.square_size * 0.25)
            # Get color from config or use default
            color = config.CLASSIFICATION_COLORS.get(classification_type, {}).get("main", "#757575")
            self.create_oval(
                x - size, y - size, x + size, y + size,
                fill=color,
                outline="white",
                width=1.5,
                tags=["classification_symbol", tag]
            )
        
        return tag
    
    def place_error_icon(self, square, error_type="mistake"):
        """Place an error icon centered on the corner of a square using the loaded image.
        For backward compatibility - maps error_type to classification type."""
        # Map old error types to new classification types
        classification_map = {
            "mistake": "Erreur",
            "blunder": "Grosse erreur"
        }
        classification = classification_map.get(error_type, "Erreur")
        return self.place_classification_icon(square, classification)
    
    def highlight_excellent_move(self, move_uci):
        """Highlight an excellent move by placing the excellent icon at the destination square."""
        if not move_uci:
            return
        try:
            to_square = chess.parse_square(move_uci[2:4])
            return self.place_classification_icon(to_square, "Excellent")
        except Exception as e:
            print(f"Error highlighting excellent move: {e}")
    
    def highlight_move_classification(self, move_uci, classification):
        """Highlight a move with the appropriate classification icon.
        
        Args:
            move_uci: The UCI string of the move (e.g., "e2e4")
            classification: The classification of the move (e.g., "Meilleur coup")
        """
        if not move_uci:
            return
        try:
            to_square = chess.parse_square(move_uci[2:4])
            return self.place_classification_icon(to_square, classification)
        except Exception as e:
            print(f"Error highlighting move with classification {classification}: {e}")
    
    def highlight_square(self, square, color="#8BB3FF", border_color=None, tag="highlight"):
        """Highlight a specific square with a subtle color overlay.
        
        Args:
            square: Chess square index
            color: Fill color for the highlight
            border_color: Border color (optional)
            tag: Canvas tag for the highlight elements
        """
        if square is None:
            return
            
        # Calculate square coordinates
        file_idx = chess.square_file(square)
        rank_idx = chess.square_rank(square)
        
        # Apply flipping if needed
        if self.flipped:
            file_idx, rank_idx = 7 - file_idx, 7 - rank_idx
        
        # Convert to canvas coordinates
        x1 = (file_idx * self.square_size) + self.margin
        y1 = ((7 - rank_idx) * self.square_size) + self.margin
        x2 = x1 + self.square_size
        y2 = y1 + self.square_size
        
        # Create semi-transparent overlay rectangle using stipple pattern
        highlight = self.create_rectangle(
            x1, y1, x2, y2,
            fill=color,
            stipple="gray50",  # Creates a semi-transparent effect
            width=0,
            tags=tag
        )
        
        # Add border if specified
        if border_color:
            self.create_rectangle(
                x1+1, y1+1, x2-1, y2-1,
                outline=border_color,
                width=2,
                fill="",
                tags=tag
            )
        
        # Ensure that the highlight appears behind the pieces
        self.tag_lower(tag, "piece")
        
        return highlight