"""
PGN handling utilities for loading and parsing chess games.
"""
import chess.pgn
import io

def load_pgn_from_file(file_path):
    """
    Load a PGN game from a file.
    
    Args:
        file_path: Path to the PGN file
    
    Returns:
        A chess.pgn.Game object, or None if loading failed
    """
    try:
        with open(file_path, 'r') as pgn_file:
            game = chess.pgn.read_game(pgn_file)
        return game
    except Exception as e:
        print(f"Error loading PGN: {e}")
        return None
        
def load_pgn_from_text(pgn_text):
    """
    Load a PGN game from text.
    
    Args:
        pgn_text: PGN text content
    
    Returns:
        A chess.pgn.Game object, or None if parsing failed
    """
    try:
        pgn_io = io.StringIO(pgn_text)
        game = chess.pgn.read_game(pgn_io)
        return game
    except Exception as e:
        print(f"Error parsing PGN: {e}")
        return None
        
def get_game_metadata(game):
    """
    Extract metadata from a PGN game.
    
    Args:
        game: A chess.pgn.Game object
    
    Returns:
        Dictionary with game metadata
    """
    metadata = {}
    for key in game.headers:
        metadata[key] = game.headers[key]
    return metadata