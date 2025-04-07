# Modern Chess Analysis Engine

A sophisticated chess GUI application with Stockfish integration, comprehensive game analysis, and interactive visualization tools.

## Features

- **Modern Interface**: Clean, intuitive design with smooth animations
- **Powerful Analysis**: Real-time position evaluation with Stockfish engine
- **Game Insights**: Move quality classification, accuracy metrics, and tactical analysis
- **Error Navigation**: Interactive system to explore mistakes and learn from them
- **Player Statistics**: Detailed performance metrics and quality breakdowns
- **PGN Support**: Load and analyze games from PGN files
- **Full Chess Support**: Complete implementation of chess rules with promotion, castling, etc.

## Screenshots

### Main Interface
![image](https://github.com/user-attachments/assets/37a51a3b-2b82-4a26-940e-f09098ef595c)

### Game Analysis
![image](https://github.com/user-attachments/assets/b37cb94a-9cb6-4f06-91ce-5c6aa809bddb)

![image](https://github.com/user-attachments/assets/05a0fada-c1c0-4302-b7ee-3089f88a102c)
![image](https://github.com/user-attachments/assets/e7e29555-349b-4aaa-bae4-43434d6cf4e3)
![image](https://github.com/user-attachments/assets/3eab7935-f732-4966-b435-82aa0ebb61e6)

## Project Structure

```
/ChessEngine
├── src/
│   ├── analysis/            - Game analysis algorithms
│   │   ├── game_analyzer.py    - Main analysis orchestration
│   │   ├── move_analyzer.py    - Individual move analysis
│   │   ├── move_classifier.py  - Move classification logic
│   │   ├── tactical_analyzer.py - Tactical sequence analysis
│   │   ├── player_stats.py     - Player statistics calculation
│   │   └── game_difficulty.py  - Position complexity calculation
│   │
│   ├── core/                - Chess game fundamentals
│   │   └── chess_game.py       - Game state and move management
│   │
│   ├── engine/              - Engine integration
│   │   └── engine_manager.py   - Stockfish communication
│   │
│   ├── gui/                 - User interface components
│   │   ├── analysis/           - Analysis visualization
│   │   │   ├── components/        - Reusable UI components
│   │   │   │   ├── chess_card.py     - Move card display
│   │   │   │   └── error_navigation.py - Error browsing system
│   │   │   ├── utils/             - UI utilities
│   │   │   │   └── style_utils.py    - Visual styling helpers
│   │   │   ├── mini_board.py      - Chess position display
│   │   │   ├── moves_tab.py       - Move analysis display
│   │   │   └── summary_tab.py     - Game statistics overview
│   │   │
│   │   ├── analysis_view.py    - Analysis window management
│   │   ├── board_view.py       - Interactive chessboard
│   │   ├── controls.py         - Game control buttons
│   │   ├── main_window.py      - Application main window
│   │   └── moderntabs.py       - Custom tab implementation
│   │
│   └── utils/               - Utility functions
│       ├── config.py           - Application configuration
│       ├── png_handler.py      - Image processing
│       └── resource_loader.py  - Asset loading
│
├── images/                - Chess piece images and resources
├── main.py                - Application entry point
└── README.md              - This documentation
```

## Requirements

- Python 3.8 or higher
- Required packages:
  - python-chess (>=1.9.0)
  - Pillow (>=9.0.0)
  - tkinter (included with most Python installations)

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/ChessEngine.git
cd ChessEngine
```

2. Install dependencies
```bash
pip install python-chess pillow
```

3. Download Stockfish Engine
   - Download from stockfishchess.org
   - For Windows: Extract the ZIP and note the path to stockfish.exe
   - For Linux: Extract and make the binary executable with `chmod +x stockfish`
   - For Mac: Use the provided DMG or download the universal binary

4. Configuration
   - Edit `config.py` if needed to modify default settings
   - Set your Stockfish path in the configuration or use the command line argument

## Usage

Launch the application:
```bash
python main.py [/path/to/stockfish]
```

### Game Analysis Features

**Move Classification:**
- Excellent (0-0.3 pawn loss)
- Good (0.3-0.7 pawn loss)
- Inaccuracy (0.7-1.5 pawn loss)
- Mistake (1.5-3.0 pawn loss)
- Blunder (3.0+ pawn loss)

**Player Statistics:**
- Accuracy percentage
- Move quality distribution
- Critical position identification
- Tactical depth analysis

**Error Navigation:**
- Interactive navigation between mistakes
- Visual indicators of error severity
- Best move alternatives with evaluations

**Position Complexity:**
- Decision difficulty scoring (1-10)
- Tactical complexity analysis
- Pattern recognition factors

## Development

### Building from Source

1. Clone the repository
2. Install development dependencies: `pip install -r requirements-dev.txt` (if applicable)
3. Run tests: `python -m unittest discover tests`

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Stockfish for the powerful chess engine
- python-chess for the chess logic library
