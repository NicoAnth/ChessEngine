"""
Chess opening detection service.
Detects chess openings using ECO (Encyclopedia of Chess Openings) database.
"""

import os
import json
import chess
from pathlib import Path

class OpeningDetector:
    """A service for detecting chess openings from move sequences."""

    def __init__(self):
        """Initialize the opening detector with ECO database."""
        self.openings_by_moves = {}  # Dictionary to store openings by move sequence
        self.openings_by_fen = {}    # Dictionary to store openings by FEN
        self.eco_loaded = False      # Flag to track if ECO database is loaded
        self.current_opening = None  # Current detected opening

    def load_eco_database(self, eco_folder_path=None):
        """
        Load the ECO database from JSON files.
        
        Args:
            eco_folder_path: Path to the folder containing ECO JSON files. If None,
                            defaults to the 'eco.json' folder in project root.
        
        Returns:
            bool: True if loading was successful, False otherwise.
        """
        if self.eco_loaded:
            return True  # Already loaded

        try:
            # If no path is provided, try to find the eco.json folder
            if eco_folder_path is None:
                # Try relative to current working directory
                if os.path.exists(os.path.join(os.getcwd(), 'eco.json')):
                    eco_folder_path = os.path.join(os.getcwd(), 'eco.json')
                # Try relative to this file's location (src/analysis)
                else:
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
                    eco_folder_path = os.path.join(project_root, 'eco.json')

            # Check if the eco folder exists
            if not os.path.exists(eco_folder_path):
                print(f"ECO database folder not found at {eco_folder_path}")
                return False

            # Load ECO files (A through E)
            eco_sections = ['A', 'B', 'C', 'D', 'E']
            total_openings = 0

            for section in eco_sections:
                eco_file_path = os.path.join(eco_folder_path, f'eco{section}.json')
                
                if not os.path.exists(eco_file_path):
                    print(f"ECO file not found: {eco_file_path}")
                    continue
                
                with open(eco_file_path, 'r', encoding='utf-8') as f:
                    try:
                        eco_data = json.load(f)
                        
                        # Process each opening in the file
                        for fen, opening_data in eco_data.items():
                            if 'moves' in opening_data and 'name' in opening_data:
                                moves = opening_data['moves']
                                name = opening_data['name']
                                eco_code = opening_data.get('eco', '')
                                
                                # Store by moves sequence (as a string for easy lookup)
                                # Normalize the moves format to handle variations in notation
                                normalized_moves = self._normalize_moves(moves)
                                self.openings_by_moves[normalized_moves] = {
                                    'eco': eco_code,
                                    'name': name
                                }
                                
                                # Store by FEN too (key of the JSON object)
                                self.openings_by_fen[fen] = {
                                    'eco': eco_code,
                                    'name': name
                                }
                                
                                total_openings += 1
                    except json.JSONDecodeError:
                        print(f"Error parsing ECO JSON file: {eco_file_path}")
                        continue

            print(f"ECO database loaded: {total_openings} openings")
            self.eco_loaded = True
            return True
        
        except Exception as e:
            print(f"Error loading ECO database: {e}")
            return False
    
    def _normalize_moves(self, moves_str):
        """
        Normalize a moves string to handle different formats.
        
        Args:
            moves_str: String of moves in SAN format (e.g., "1. e4 e5 2. Nf3 Nc6")
            
        Returns:
            Normalized string with consistent spacing and numbering removed
        """
        # Remove move numbers (e.g., "1.", "2.")
        moves = []
        parts = moves_str.strip().split()
        
        for part in parts:
            # Skip move numbers (e.g., "1.", "2.")
            if part.endswith('.'):
                continue
            moves.append(part)
        
        # Return normalized string
        return ' '.join(moves)

    def detect_opening(self, board):
        """
        Detect the chess opening based on the current board state.
        
        Args:
            board: A chess.Board object representing the current position
            
        Returns:
            dict: Dictionary with 'eco' and 'name' if an opening is detected,
                 None otherwise
        """
        if not self.eco_loaded:
            if not self.load_eco_database():
                return None

        # First try by FEN (most specific)
        current_fen = board.fen()
        if current_fen in self.openings_by_fen:
            self.current_opening = self.openings_by_fen[current_fen]
            return self.current_opening
        
        # Try by normalized position (ignoring move counters)
        fen_parts = current_fen.split(' ')
        position_fen = ' '.join(fen_parts[:4])  # Position, active color, castling, en passant
        
        for stored_fen, opening_info in self.openings_by_fen.items():
            stored_parts = stored_fen.split(' ')
            if len(stored_parts) >= 4:
                stored_position = ' '.join(stored_parts[:4])
                if stored_position == position_fen:
                    self.current_opening = opening_info
                    return opening_info
        
        # Try by move sequence
        if board.move_stack:
            # Convert the move stack to SAN notation
            temp_board = chess.Board()
            moves_san = []
            
            for move in board.move_stack:
                san = temp_board.san(move)
                moves_san.append(san)
                temp_board.push(move)
            
            # Try to match against openings by move sequence
            while moves_san:
                # Create candidate move string and normalize it
                candidate_moves = ' '.join(moves_san)
                normalized_candidate = self._normalize_moves(candidate_moves)
                
                if normalized_candidate in self.openings_by_moves:
                    self.current_opening = self.openings_by_moves[normalized_candidate]
                    return self.current_opening
                
                # Remove last move and try again with a shorter sequence
                moves_san.pop()
                
            # Direct match failed, try matching move by move (to handle transpositions)
            temp_board = chess.Board()
            for i in range(len(board.move_stack)):
                temp_board.push(board.move_stack[i])
                temp_fen = temp_board.fen()
                
                # Check if this intermediate position matches an opening
                if temp_fen in self.openings_by_fen:
                    self.current_opening = self.openings_by_fen[temp_fen]
                    return self.current_opening
                
                # Try with normalized FEN
                temp_fen_parts = temp_fen.split(' ')
                temp_position = ' '.join(temp_fen_parts[:4])
                
                for stored_fen, opening_info in self.openings_by_fen.items():
                    stored_parts = stored_fen.split(' ')
                    if len(stored_parts) >= 4:
                        stored_position = ' '.join(stored_parts[:4])
                        if stored_position == temp_position:
                            self.current_opening = opening_info
                            return opening_info
        
        # If we're still in a previously detected opening, return that
        return self.current_opening

    def get_current_opening(self):
        """
        Get the current detected opening.
        
        Returns:
            dict: Dictionary with 'eco' and 'name' if an opening is detected,
                 None otherwise
        """
        return self.current_opening

    def reset(self):
        """Reset the detector state."""
        self.current_opening = None