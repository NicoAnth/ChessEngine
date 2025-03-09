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
        self.square_size = 40  # Default square size
        self.margin = 15      # Margin for coordinates
        self.flipped = False  # Track board orientation
        
        # Modern styling for coordinate markers
        self.marker_font = font.Font(family="Segoe UI", size=9, weight="normal")
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
        
        self.board = chess.Board()  # Initial position
        self.draw_board()
    
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