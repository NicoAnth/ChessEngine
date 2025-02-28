# Modern Chess Engine

A modern chess GUI application with Stockfish integration, move analysis, and game statistics.

## Features

- Modern and clean user interface
- Real-time position analysis using Stockfish
- Game analysis with move classification and player statistics
- Move animations and visual highlights
- Support for standard chess rules including promotions
- Board flipping and move undoing

## Project Structure

```
/ChessEngine
  /src
    /core          - Core chess game logic
    /engine        - Stockfish engine integration
    /analysis      - Game analysis functionality  
    /gui           - User interface components
    /utils         - Utilities and configuration
  /images          - Chess piece images
  main.py          - Application entry point
```

## Requirements

- Python 3.8+
- Required Python packages:
  - chess (python-chess)
  - Pillow (PIL)
  - tkinter

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install python-chess pillow
   ```
3. Download Stockfish chess engine from https://stockfishchess.org/download/

## Usage

Run the main script with the path to your Stockfish engine:

```
python main.py /path/to/stockfish
```

If no path is provided, it will look for Stockfish at the default location.

## Controls

- **Flip Board**: Flips the board view
- **Undo Move**: Undoes the last move
- **Nouvelle Partie**: Starts a new game
- **Bilan de Partie**: Shows comprehensive game analysis with player statistics

## Game Analysis

The game analysis feature provides:

- Move classification (Excellent, Good, Ok, Inaccuracy, Mistake, Blunder)
- Player accuracy scores
- Move-by-move statistics with alternative best moves
- Visual comparison of move quality

## License

This project is licensed under the MIT License - see the LICENSE file for details.