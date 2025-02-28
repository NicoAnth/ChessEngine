# CLAUDE.md - Chess Engine Development Guidelines

## Build & Run Commands
- Run main app: `python main.py`
- Create executable: `pyinstaller main.py --onefile --add-data "Images/*;Images/"`
- Install dependencies: `pip install -r requirements.txt`
- Run tests: `pytest tests/`

## Code Style Guidelines
- **Imports**: Group standard library imports first, then third-party packages, then local modules
- **Formatting**: Use 4-space indentation; max line length 100 characters
- **Naming**: 
  - Classes: PascalCase (e.g., `ModernChessGUI`)
  - Methods/Functions: snake_case (e.g., `highlight_legal_moves`)
  - Constants: UPPER_SNAKE_CASE
- **Error Handling**: Use try/except blocks with specific exceptions and meaningful error messages
- **Documentation**: Add docstrings for classes and non-trivial methods
- **UI Components**: Keep UI layout and styling code separate from game logic
- **Chess Logic**: Leverage the `chess` library for game rules and avoid reimplementing chess logic

## Project Structure
- `/Images`: Contains chess piece images
- `main.py`: Main application entry point and GUI implementation
- Use the polyglot-master directory for opening book functionality