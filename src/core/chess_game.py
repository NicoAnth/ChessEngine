"""
Core chess game functionality.
Manages the game state, moves, and board representation.
"""

import chess

class ChessGame:
    """Manages the chess game state and move logic."""
    
    def __init__(self):
        """Initialize a new chess game."""
        self.board = chess.Board()
        self.board_flipped = False
        self.last_move = None
        self.reset()
    
    def reset(self):
        """Reset the game to starting position."""
        self.board = chess.Board()
        self.last_move = None
    
    def make_move(self, move):
        """
        Make a move on the board.
        
        Args:
            move: A chess.Move object
            
        Returns:
            True if the move was made, False if illegal
        """
        if move in self.board.legal_moves:
            self.board.push(move)
            self.last_move = move
            return True
        return False
    
    def undo_move(self):
        """
        Undo the last move.
        
        Returns:
            True if a move was undone, False if there are no moves to undo
        """
        if self.board.move_stack:
            self.board.pop()
            self.last_move = self.board.peek() if self.board.move_stack else None
            return True
        return False
    
    def get_legal_moves(self, from_square=None):
        """
        Get legal moves from the current position.
        
        Args:
            from_square: Optional source square to filter moves
            
        Returns:
            List of legal Move objects
        """
        if from_square is not None:
            return [move for move in self.board.legal_moves if move.from_square == from_square]
        return list(self.board.legal_moves)
    
    def is_check(self):
        """Check if the current side is in check."""
        return self.board.is_check()
    
    def is_checkmate(self):
        """Check if the current position is checkmate."""
        return self.board.is_checkmate()
    
    def is_stalemate(self):
        """Check if the current position is stalemate."""
        return self.board.is_stalemate()
    
    def is_insufficient_material(self):
        """Check if there is insufficient material to checkmate."""
        return self.board.is_insufficient_material()
    
    def is_game_over(self):
        """Check if the game is over (checkmate, stalemate, etc.)."""
        return self.board.is_game_over()
    
    def get_result(self):
        """
        Get the game result.
        
        Returns:
            String describing the game result, or None if the game is not over
        """
        if not self.is_game_over():
            return None
            
        if self.is_checkmate():
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            return f"Checkmate - {winner} wins"
        elif self.is_stalemate():
            return "Stalemate - Draw"
        elif self.is_insufficient_material():
            return "Insufficient material - Draw"
        else:
            return "Game over - Draw"
    
    def get_move_count(self):
        """Get the number of half-moves played."""
        return len(self.board.move_stack)
    
    def flip_board(self):
        """
        Flip the board view.
        
        Returns:
            New board flipped state (True/False)
        """
        self.board_flipped = not self.board_flipped
        return self.board_flipped
    
    def get_turn(self):
        """
        Get the current side to move.
        
        Returns:
            chess.WHITE or chess.BLACK
        """
        return self.board.turn
    
    def get_piece_at(self, square):
        """
        Get the piece at a given square.
        
        Args:
            square: Square index (0-63)
            
        Returns:
            Piece object or None if square is empty
        """
        return self.board.piece_at(square)
    
    def get_king_square(self, color):
        """
        Get the square of the king for a given color.
        
        Args:
            color: chess.WHITE or chess.BLACK
            
        Returns:
            Square index (0-63) of the king
        """
        return self.board.king(color)
    
    def get_move_san(self, move):
        """
        Get Standard Algebraic Notation for a move.
        
        Args:
            move: A chess.Move object
            
        Returns:
            SAN string representation of the move
        """
        return self.board.san(move)
    
    def get_fen(self):
        """
        Get the FEN representation of the current position.
        
        Returns:
            FEN string
        """
        return self.board.fen()
    
    def set_from_fen(self, fen):
        """
        Set the board position from FEN.
        
        Args:
            fen: FEN string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.board = chess.Board(fen)
            return True
        except ValueError:
            return False


    def load_from_pgn(self, pgn_game):
        """
        Load a game from a PGN.
        
        Args:
            pgn_game: A chess.pgn.Game object
        
        Returns:
            True if successfully loaded
        """
        try:
            self.reset()
            # Store all moves from PGN
            self.pgn_moves = []
            self.current_move_index = -1
            
            # Create a new board from the game
            board = pgn_game.board()
            
            # Go through all moves
            for move in pgn_game.mainline_moves():
                self.pgn_moves.append(move)
            
            return True
        except Exception as e:
            print(f"Error loading PGN into game: {e}")
            return False
            
    def go_to_move(self, move_index):
        """
        Go to a specific move in the loaded PGN.
        
        Args:
            move_index: Index of the move to go to
        
        Returns:
            True if successfully navigated to the move
        """
        if not hasattr(self, 'pgn_moves') or not self.pgn_moves:
            return False
            
        # Ensure move_index is in valid range
        if move_index < -1 or move_index >= len(self.pgn_moves):
            return False
            
        # Reset board to starting position
        self.board = chess.Board()
        self.last_move = None
        
        # Apply moves up to the specified index
        for i in range(move_index + 1):
            self.board.push(self.pgn_moves[i])
            self.last_move = self.pgn_moves[i]
        
        self.current_move_index = move_index
        return True
        
    def go_to_next_move(self):
        """Go to the next move in the loaded PGN."""
        if hasattr(self, 'current_move_index') and hasattr(self, 'pgn_moves'):
            return self.go_to_move(self.current_move_index + 1)
        return False
        
    def go_to_prev_move(self):
        """Go to the previous move in the loaded PGN."""
        if hasattr(self, 'current_move_index'):
            return self.go_to_move(self.current_move_index - 1)
        return False