"""Chess board visualization for analysis."""

import tkinter as tk
import chess
from src.utils import config

class MiniChessBoard(tk.Canvas):
    """A simple chess board canvas for displaying positions."""
    
    def __init__(self, parent, piece_images=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.configure(bg="white", highlightthickness=1, highlightbackground="#E0E0E0")
        self.square_size = 40  # Default square size
        
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
        """Draw the empty chess board."""
        self.delete("all")  # Clear canvas
        
        # Calculate canvas size based on square size
        board_size = self.square_size * 8
        self.config(width=board_size, height=board_size)
        
        # Draw squares
        for row in range(8):
            for col in range(8):
                # Calculate position
                x1 = col * self.square_size
                y1 = row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                
                # Determine square color (light or dark)
                is_light = (row + col) % 2 == 0
                fill_color = config.COLORS["light_square"] if is_light else config.COLORS["dark_square"]
                
                # Draw square
                self.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline="")
                
                # Add coordinates labels on the bottom and right edges
                if row == 7:
                    self.create_text(
                        x1 + self.square_size/2, 
                        y2 - 10, 
                        text=chr(col + 97),  # 'a' through 'h'
                        fill="#555555" if is_light else "#CCCCCC",
                        font=("Segoe UI", 8)
                    )
                if col == 7:
                    self.create_text(
                        x2 - 10, 
                        y1 + self.square_size/2, 
                        text=str(8 - row),  # '8' through '1'
                        fill="#555555" if is_light else "#CCCCCC",
                        font=("Segoe UI", 8)
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
            
            # Calculate position
            x = col * self.square_size + self.square_size/2
            y = row * self.square_size + self.square_size/2
            
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
    
    def update_to_position(self, fen):
        """Update board to show the position from FEN."""
        try:
            self.board = chess.Board(fen)
            self.draw_position()
        except Exception as e:
            print(f"Error updating chess position: {e}")