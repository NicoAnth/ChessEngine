"""
Chess board visualization module.
Handles rendering the chess board, pieces, and move highlights.
"""

import chess
import tkinter as tk
from src.utils import config

class BoardView:
    """Renders the chess board and pieces."""
    
    def __init__(self, canvas, game, piece_images, square_size=None, label_offset=None):
        """
        Initialize the board view.
        
        Args:
            canvas: Tkinter canvas to draw on
            game: ChessGame instance
            piece_images: Dictionary of piece images
            square_size: Size of each square
            label_offset: Offset for board labels
        """
        self.canvas = canvas
        self.game = game
        self.piece_images = piece_images
        self.square_size = square_size or config.DEFAULT_SQUARE_SIZE
        self.label_offset = label_offset or config.DEFAULT_LABEL_OFFSET
        self.rows, self.cols = 8, 8
        self.highlight_ids = []
        
        # For move animation
        self.animating_move = None
        self.animated_piece_id = None
    
    def redraw_board(self):
        """Fully redraw the board and pieces."""
        self.clear_highlights()
        self.canvas.delete("all")
        self.draw_board()
        self.place_pieces()
    
    def clear_highlights(self):
        """Clear all highlight markers from the board."""
        for item in self.highlight_ids:
            self.canvas.delete(item)
        self.highlight_ids = []
    
    def draw_board(self):
        """Draw the chess board with coordinates and highlights."""
        # Draw files (columns) labels
        for col in range(self.cols):
            label = chr(104 - col) if self.game.board_flipped else chr(col + 97)
            x = (col + 0.5) * self.square_size + self.label_offset
            y = self.cols * self.square_size + self.label_offset * 1.5
            self.canvas.create_text(
                x, y, 
                text=label, 
                font=("Segoe UI", 11, "bold"), 
                fill=config.COLORS["primary_text"]
            )
        
        # Draw ranks (rows) labels
        for row in range(self.rows):
            label = str(row + 1) if self.game.board_flipped else str(8 - row)
            x = self.label_offset/2
            y = (row + 0.5) * self.square_size + self.label_offset
            self.canvas.create_text(
                x, y, 
                text=label, 
                font=("Segoe UI", 11, "bold"), 
                fill=config.COLORS["primary_text"]
            )
        
        # Draw squares
        for row in range(self.rows):
            for col in range(self.cols):
                color = config.COLORS["light_square"] if (row+col) % 2 == 0 else config.COLORS["dark_square"]
                x1 = col * self.square_size + self.label_offset
                y1 = row * self.square_size + self.label_offset
                x2 = (col+1) * self.square_size + self.label_offset
                y2 = (row+1) * self.square_size + self.label_offset
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
        
        # Highlight last move
        if self.game.last_move is not None:
            from_square, to_square = self.game.last_move.from_square, self.game.last_move.to_square
            for sq in [from_square, to_square]:
                col, row = chess.square_file(sq), chess.square_rank(sq)
                if self.game.board_flipped:
                    col = 7 - col
                else:
                    row = 7 - row
                x1 = col * self.square_size + self.label_offset
                y1 = row * self.square_size + self.label_offset
                highlight = self.canvas.create_rectangle(
                    x1, y1, x1 + self.square_size, y1 + self.square_size,
                    fill=config.COLORS["last_move"], stipple="gray25"
                )
                self.highlight_ids.append(highlight)
        
        # Highlight king in check
        if self.game.is_check():
            king_square = self.game.get_king_square(self.game.get_turn())
            col, row = chess.square_file(king_square), chess.square_rank(king_square)
            if self.game.board_flipped:
                col = 7 - col
            else:
                row = 7 - row
            x1 = col * self.square_size + self.label_offset
            y1 = row * self.square_size + self.label_offset
            highlight = self.canvas.create_rectangle(
                x1, y1, x1 + self.square_size, y1 + self.square_size,
                outline=config.COLORS["check"], width=4
            )
            self.highlight_ids.append(highlight)
    
    def place_pieces(self):
        """Place chess pieces on the board."""
        piece_name_map = {
            chess.PAWN: 'pawn',
            chess.KNIGHT: 'knight',
            chess.BISHOP: 'bishop',
            chess.ROOK: 'rook',
            chess.QUEEN: 'queen',
            chess.KING: 'king',
        }
        
        for square in chess.SQUARES:
            # Skip animating piece - it's handled separately
            if self.animating_move is not None and square == self.animating_move[0]:
                continue
                
            piece = self.game.get_piece_at(square)
            if piece:
                color = 'white' if piece.color == chess.WHITE else 'black'
                piece_name = f"{color}-{piece_name_map[piece.piece_type]}"
                col, row = chess.square_file(square), chess.square_rank(square)
                
                if self.game.board_flipped:
                    col = 7 - col
                else:
                    row = 7 - row
                
                x = col * self.square_size + self.square_size/2 + self.label_offset
                y = row * self.square_size + self.square_size/2 + self.label_offset
                
                self.canvas.create_image(x, y, image=self.piece_images[piece_name])
    
    def highlight_legal_moves(self, from_square):
        """
        Highlight legal moves from a selected square.
        
        Args:
            from_square: The source square to highlight moves from
        """
        self.clear_highlights()
        
        # Highlight selected square
        col, row = chess.square_file(from_square), chess.square_rank(from_square)
        if self.game.board_flipped:
            col = 7 - col
        else:
            row = 7 - row
        
        x = col * self.square_size + self.label_offset
        y = row * self.square_size + self.label_offset
        
        selected = self.canvas.create_rectangle(
            x, y, x + self.square_size, y + self.square_size,
            fill=config.COLORS["selected_square"], outline="", stipple="gray50"
        )
        self.highlight_ids.append(selected)
        
        # Highlight legal moves with modern dot indicators
        legal_moves = self.game.get_legal_moves(from_square)
        
        for move in legal_moves:
            to_square = move.to_square
            col, row = chess.square_file(to_square), chess.square_rank(to_square)
            
            if self.game.board_flipped:
                col = 7 - col
            else:
                row = 7 - row
                
            x = col * self.square_size + self.label_offset
            y = row * self.square_size + self.label_offset
            
            target_piece = self.game.get_piece_at(to_square)
            
            if target_piece:
                # Highlight captures with a rectangle
                highlight = self.canvas.create_rectangle(
                    x + 3, y + 3, x + self.square_size - 3, y + self.square_size - 3,
                    outline=config.COLORS["highlight"], width=3
                )
            else:
                # Highlight empty squares with a dot
                circle_radius = self.square_size // 6
                highlight = self.canvas.create_oval(
                    x + self.square_size/2 - circle_radius,
                    y + self.square_size/2 - circle_radius,
                    x + self.square_size/2 + circle_radius,
                    y + self.square_size/2 + circle_radius,
                    fill=config.COLORS["highlight"], outline=""
                )
                
            self.highlight_ids.append(highlight)
    
    def get_square_center(self, square):
        """
        Get the center coordinates of a square.
        
        Args:
            square: Chess square index (0-63)
            
        Returns:
            (x, y) coordinate tuple for the center of the square
        """
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        
        if self.game.board_flipped:
            col = 7 - file
            row = rank
        else:
            col = file
            row = 7 - rank
            
        x = col * self.square_size + self.square_size/2 + self.label_offset
        y = row * self.square_size + self.square_size/2 + self.label_offset
        
        return x, y
    
    def get_square_from_coords(self, x, y):
        """
        Convert screen coordinates to a chess square.
        
        Args:
            x, y: Screen coordinates
            
        Returns:
            Chess square index (0-63) or None if outside the board
        """
        if (x < self.label_offset or 
            x >= 8 * self.square_size + self.label_offset or
            y < self.label_offset or 
            y >= 8 * self.square_size + self.label_offset):
            return None
            
        col = (x - self.label_offset) // self.square_size
        row = (y - self.label_offset) // self.square_size
        
        if self.game.board_flipped:
            square = chess.square(7-col, row)
        else:
            square = chess.square(col, 7-row)
            
        return square
    
    def animate_move(self, from_square, to_square, move, callback=None):
        """
        Animate a piece moving across the board.
        
        Args:
            from_square: Starting square
            to_square: Ending square
            move: Chess move object
            callback: Function to call when animation completes
        """
        piece = self.game.get_piece_at(from_square)
        if piece is None:
            if callback:
                callback()
            return
            
        self.animating_move = (from_square, to_square, piece)
        
        piece_name_map = {
            chess.PAWN: 'pawn',
            chess.KNIGHT: 'knight',
            chess.BISHOP: 'bishop',
            chess.ROOK: 'rook',
            chess.QUEEN: 'queen',
            chess.KING: 'king'
        }
        
        color = 'white' if piece.color == chess.WHITE else 'black'
        piece_name = f"{color}-{piece_name_map[piece.piece_type]}"
        piece_img = self.piece_images[piece_name]
        
        start_x, start_y = self.get_square_center(from_square)
        end_x, end_y = self.get_square_center(to_square)
        
        self.animated_piece_id = self.canvas.create_image(start_x, start_y, image=piece_img)
        
        duration = config.ANIMATION["duration"]
        steps = config.ANIMATION["steps"]
        delay = duration // steps
        
        delta_x = (end_x - start_x) / steps
        delta_y = (end_y - start_y) / steps
        
        def animate_step(step):
            if step < steps:
                self.canvas.move(self.animated_piece_id, delta_x, delta_y)
                self.canvas.after(delay, lambda: animate_step(step+1))
            else:
                self.animating_move = None
                self.canvas.delete(self.animated_piece_id)
                self.animated_piece_id = None
                
                if callback:
                    callback()