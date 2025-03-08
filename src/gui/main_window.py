"""
Main window for the chess application.
Integrates all GUI components and handles user interactions.
"""

import threading
import tkinter as tk
from tkinter import ttk, font, filedialog
import chess
import chess.pgn

from src.core.chess_game import ChessGame
from src.engine.engine_manager import EngineManager
from src.analysis.game_analyzer import GameAnalyzer
from src.utils import config, resource_loader
from src.gui.board_view import BoardView
from src.gui.controls import ControlPanel, AnalysisPanel
from src.gui.analysis_view import GameAnalysisView

class ChessApplication:
    """Main application class for the chess GUI."""
    
    def __init__(self, engine_path):
        """
        Initialize the chess application.
        
        Args:
            engine_path: Path to the Stockfish engine executable
        """
        # Initialize engine
        self.engine_manager = EngineManager(engine_path)
        
        # Initialize game
        self.game = ChessGame()
        
        # Initialize game analyzer
        self.game_analyzer = GameAnalyzer(self.engine_manager)
        
        # Create main window
        self.window = tk.Tk()
        self.window.title("Modern Chess")
        self.window.configure(bg=config.COLORS["background"])
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # PGN navigation status
        self.pgn_loaded = False
        
        # Selected square for move input
        self.selected_square = None
        
        # Create main layout
        self.setup_gui()
        
        # Load piece images
        self.piece_images = resource_loader.load_piece_images(self.square_size)
        
        # Create board view
        self.board_view = BoardView(
            self.canvas, 
            self.game, 
            self.piece_images, 
            self.square_size, 
            self.label_offset
        )
        
        # Set up analysis view with piece images
        self.analysis_view = GameAnalysisView(self.window, self.game_analyzer, self.piece_images)
        
        # Set up event handlers
        self.setup_event_handlers()
        
        # Draw initial board
        self.board_view.redraw_board()
        
        # Start analysis
        self.analyze_position_async()
    
    def setup_gui(self):
        """Set up the GUI layout and components."""
        # Configuration parameters
        self.square_size = config.DEFAULT_SQUARE_SIZE
        self.label_offset = config.DEFAULT_LABEL_OFFSET
        self.rows, self.cols = 8, 8
        self.canvas_width = self.cols * self.square_size + self.label_offset * 2
        self.canvas_height = self.rows * self.square_size + self.label_offset * 2
        
        # Create main frame with padding
        # Create menu bar
        self.menubar = tk.Menu(self.window)
        self.window.config(menu=self.menubar)
        
        # Create File menu
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Fichier", menu=self.file_menu)
        
        # Add menu items
        self.file_menu.add_command(label="Charger fichier PGN", command=self.load_pgn_file)
        self.file_menu.add_command(label="Exporter en PGN", command=lambda: print("Export PGN placeholder"))
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Quitter", command=self.on_closing)
        
        self.main_frame = ttk.Frame(self.window, padding=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure ttk styles
        self.style = ttk.Style()
        self.style.configure("TFrame", background=config.COLORS["background"])
        self.style.configure("TButton", 
                            font=font.Font(**config.FONTS["button"]), 
                            background="#3F51B5", 
                            foreground="white")
        self.style.map("TButton",
                    background=[("active", "#303F9F"), ("pressed", "#1A237E")])
        
        # Game title
        self.title_label = ttk.Label(
            self.main_frame, 
            text="", 
            font=font.Font(**config.FONTS["title"]), 
            background=config.COLORS["background"],
            foreground=config.COLORS["primary_text"]
        )
        self.title_label.pack(pady=(0, 10))
        
        # Create layout frames
        self.game_frame = ttk.Frame(self.main_frame)
        self.game_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.info_frame = ttk.Frame(self.main_frame, padding=10)
        self.info_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas for chess board with subtle border
        self.canvas_frame = ttk.Frame(self.game_frame, borderwidth=2, relief="solid")
        self.canvas_frame.pack(padx=10, pady=10)
        
        self.canvas = tk.Canvas(
            self.canvas_frame, 
            width=self.canvas_width, 
            height=self.canvas_height,
            bg=config.COLORS["background"], 
            highlightthickness=0
        )
        self.canvas.pack()
        
        # Set up control panel
        control_callbacks = {
            "flip_board": self.flip_board,
            "undo_move": self.undo_last_move,
            "new_game": self.new_game,
            "analyze_game": self.analyze_game_summary
        }
        self.control_panel = ControlPanel(self.game_frame, control_callbacks)
        
        # Set up PGN navigation panel
        self.pgn_nav_frame = ttk.Frame(self.game_frame, padding=(0, 10))
        self.pgn_nav_frame.pack(fill=tk.X)
        
        # PGN Navigation buttons
        self.nav_buttons_frame = ttk.Frame(self.pgn_nav_frame)
        self.nav_buttons_frame.pack(pady=5)
        
        self.first_move_btn = ttk.Button(self.nav_buttons_frame, text="<<", command=self.go_to_first_move, state=tk.DISABLED)
        self.first_move_btn.pack(side=tk.LEFT, padx=2)
        
        self.prev_move_btn = ttk.Button(self.nav_buttons_frame, text="<", command=self.go_to_prev_move, state=tk.DISABLED)
        self.prev_move_btn.pack(side=tk.LEFT, padx=2)
        
        self.next_move_btn = ttk.Button(self.nav_buttons_frame, text=">", command=self.go_to_next_move, state=tk.DISABLED)
        self.next_move_btn.pack(side=tk.LEFT, padx=2)
        
        self.last_move_btn = ttk.Button(self.nav_buttons_frame, text=">>", command=self.go_to_last_move, state=tk.DISABLED)
        self.last_move_btn.pack(side=tk.LEFT, padx=2)
        
        # Set up analysis panel
        self.analysis_panel = AnalysisPanel(self.info_frame)
    
    def setup_event_handlers(self):
        """Set up event handlers for user interactions."""
        self.canvas.bind("<Button-1>", self.on_square_clicked)
        self.canvas.bind("<Motion>", self.on_square_hover)
    
    def on_closing(self):
        """Handle window closing event."""
        
        # 1. Add a flag to signal analysis threads to stop
        self.analysis_running = False
        
        # 2. Small delay to allow threads to complete current operations
        self.window.after(100, self._cleanup_and_close)
        
    def _cleanup_and_close(self):
        """Cleanup resources and close the application."""
        try:
            # 3. Make sure the engine is not being used
            if hasattr(self, 'engine_manager') and self.engine_manager:
                self.engine_manager.quit()
            
            # 4. Close any matplotlib figures
            try:
                import matplotlib.pyplot as plt
                plt.close('all')
            except ImportError:
                pass
            
            # 5. Finally, close the window
            self.window.destroy()
        except Exception as e:
            print(f"Error during application shutdown: {e}")
            # Force close in case of error
            self.window.destroy()
    
    def on_square_clicked(self, event):
        """
        Handle mouse clicks on the board.
        
        Args:
            event: Tkinter event object
        """
        # Get square from coordinates
        square = self.board_view.get_square_from_coords(event.x, event.y)
        if square is None:
            return
        
        # Debug output to verify correct square detection
        print(f"Clicked square: {chess.square_name(square)}")
            
        if self.selected_square is None:
            # First click - select a piece
            piece = self.game.get_piece_at(square)
            if piece and piece.color == self.game.get_turn():
                self.selected_square = square
                print(f"Selected piece: {piece}")
                self.board_view.highlight_legal_moves(square)
        else:
            # Second click - make a move or reselect
            from_square = self.selected_square
            moving_piece = self.game.get_piece_at(from_square)
            self.board_view.clear_highlights()
            
            if moving_piece is None:
                self.selected_square = None
                return
                
            # If clicking the same square, deselect
            if from_square == square:
                self.selected_square = None
                return
                
            # Check if the move is legal
            move = chess.Move(from_square, square)
            legal_moves = self.game.get_legal_moves()
            
            print(f"Attempting move: {from_square}->{square}")
            print(f"Move in legal moves: {move in legal_moves}")
            
            if move in legal_moves:
                # Handle pawn promotion
                if (moving_piece.piece_type == chess.PAWN and 
                   ((moving_piece.color == chess.WHITE and chess.square_rank(square)==7) or
                    (moving_piece.color == chess.BLACK and chess.square_rank(square)==0))):
                    self.show_promotion_dialog(from_square, square)
                else:
                    # Regular move
                    self.handle_move(from_square, square, move)
            else:
                # Clicking on another piece of the same color - reselect
                piece = self.game.get_piece_at(square)
                if piece and piece.color == self.game.get_turn():
                    self.selected_square = square
                    self.board_view.highlight_legal_moves(square)
                else:
                    self.selected_square = None
    
    def on_square_hover(self, event):
        """
        Handle mouse hover over the board.
        
        Args:
            event: Tkinter event object
        """
        square = self.board_view.get_square_from_coords(event.x, event.y)
        
        if square is None:
            self.window.config(cursor="")
            return
            
        # Show hand cursor for pieces that can be moved
        piece = self.game.get_piece_at(square)
        if piece and piece.color == self.game.get_turn():
            self.window.config(cursor="hand2")
        else:
            # Also show hand for legal target squares when a piece is selected
            if self.selected_square is not None:
                for move in self.game.get_legal_moves(self.selected_square):
                    if move.to_square == square:
                        self.window.config(cursor="hand2")
                        return
            self.window.config(cursor="")
    
    def handle_move(self, from_square, to_square, move):
        """
        Process a move and update the UI.
        
        Args:
            from_square: Source square
            to_square: Target square
            move: Chess move object
        """
        # Important: Make the move in the game model first
        # This ensures the game state is updated even if animation fails
        result = self.game.make_move(move)
        print(f"Move made: {result}")
        self.selected_square = None  # Clear selection after move
        
        # Define a callback for when the animation finishes
        def after_animation():
            # Update the board
            self.board_view.redraw_board()
            
            # Update analysis
            self.analyze_position_async()
            
            # Update status
            self.update_game_info()
            
            # Check game status
            if self.game.is_checkmate():
                color = "Blancs" if self.game.get_turn() == chess.BLACK else "Noirs"
                self.control_panel.display_status_message(
                    f"Échec et mat! Les {color} gagnent", 
                    config.COLORS["error"]
                )
            elif self.game.is_check():
                self.control_panel.display_status_message(
                    "Échec!", 
                    config.COLORS["warning"]
                )
        
        try:
            # Start the animation, which will call after_animation when done
            self.board_view.animate_move(from_square, to_square, move, after_animation)
        except Exception as e:
            print(f"Animation error: {e}")
            # Fallback if animation fails
            after_animation()
    
    def show_promotion_dialog(self, from_square, to_square):
        """
        Show pawn promotion dialog.
        
        Args:
            from_square: Source square
            to_square: Target square
        """
        promo_window = tk.Toplevel(self.window)
        promo_window.title("Promotion")
        promo_window.geometry("300x400")
        promo_window.resizable(False, False)
        promo_window.configure(bg=config.COLORS["background"])
        promo_window.transient(self.window)
        promo_window.grab_set()
        
        header = tk.Label(
            promo_window, 
            text="Choisissez la promotion", 
            font=font.Font(**config.FONTS["title"]), 
            bg=config.COLORS["background"], 
            fg=config.COLORS["primary_text"]
        )
        header.pack(pady=20)
        
        # Promotion options
        options = [
            ("Dame", chess.QUEEN), 
            ("Tour", chess.ROOK),
            ("Fou", chess.BISHOP), 
            ("Cavalier", chess.KNIGHT)
        ]
        
        for text, promotion_piece in options:
            btn = tk.Button(
                promo_window, 
                text=text, 
                font=font.Font(**config.FONTS["button"]), 
                bg=config.COLORS["new_game_button"], 
                fg="white", 
                activebackground=config.COLORS["new_game_button_active"],
                command=lambda p=promotion_piece: self.apply_promotion(from_square, to_square, p, promo_window)
            )
            btn.pack(pady=10, ipadx=10, ipady=5, fill='x', padx=20)
    
    def apply_promotion(self, from_square, to_square, promotion_piece, promo_window):
        """
        Apply a pawn promotion move.
        
        Args:
            from_square: Source square
            to_square: Target square
            promotion_piece: Piece type for promotion
            promo_window: Promotion dialog window
        """
        move = chess.Move(from_square, to_square, promotion=promotion_piece)
        if move in self.game.get_legal_moves():
            self.game.make_move(move)
            self.board_view.redraw_board()
            self.analyze_position_async()
            self.update_game_info()
            self.control_panel.display_status_message("Promotion", config.COLORS["success"])
        promo_window.destroy()
    
    def flip_board(self):
        """Flip the board view."""
        self.game.flip_board()
        self.board_view.redraw_board()
        self.control_panel.display_status_message("Plateau retourné")
    
    def undo_last_move(self):
        """Undo the last move."""
        if self.game.undo_move():
            self.board_view.redraw_board()
            self.analyze_position_async()
            self.update_game_info()
            self.control_panel.display_status_message("Coup annulé", config.COLORS["warning"])
        else:
            self.control_panel.display_status_message("Pas de coup à annuler", config.COLORS["error"])
    
    def new_game(self):
        """Start a new game."""
        self.game.reset()
        self.selected_square = None
        self.board_view.redraw_board()
        self.update_game_info()
        self.control_panel.display_status_message("Nouvelle partie commencée", config.COLORS["success"])
        self.analyze_position_async()
    
    def analyze_position_async(self):
        """Start asynchronous position analysis."""
        threading.Thread(target=self.analyze_position, daemon=True).start()
    
    def analyze_position(self):
        """Analyze the current board position."""
        try:
            if self.game.is_game_over():
                return
                
            info = self.engine_manager.analyze_position(self.game.board)
            if not info:
                print("No analysis information received")
                return
                
            top_moves = []
            print(f"Analysis info: {info}")
            
            for item in info:
                if item is None:
                    continue
                
                if 'pv' not in item or not item['pv']:
                    print(f"Warning: No principal variation in item: {item}")
                    continue
                    
                move = item['pv'][0]
                if 'score' not in item:
                    print(f"Warning: No score in item: {item}")
                    continue
                    
                score_obj = item['score']
                formatted_score = self.engine_manager.format_score(score_obj)
                
                move_san = self.game.get_move_san(move)
                top_moves.append((move_san, formatted_score))
                
            print(f"Processed top moves: {top_moves}")
                
            # Make sure to update UI from the main thread
            if top_moves:
                self.window.after(0, lambda: self.analysis_panel.display_top_moves(top_moves))
            else:
                print("No valid moves found in analysis")
        except Exception as e:
            print(f"Error during engine analysis: {e}")
    
    def update_game_info(self):
        """Update the game information display."""
        # Update position info
        position_status = "Starting position"
        if self.game.get_move_count() > 0:
            position_status = f"Move {self.game.get_move_count()}"
            
            if self.game.is_checkmate():
                position_status = "Échec et mat"
            elif self.game.is_stalemate():
                position_status = "Pat"
            elif self.game.is_insufficient_material():
                position_status = "Matériel insuffisant"
            elif self.game.is_check():
                position_status = "Échec"
                
        self.analysis_panel.update_position_info(position_status)
        
        # Update turn indicator
        self.analysis_panel.update_turn_indicator(self.game.get_turn() == chess.WHITE)
    
    def analyze_game_summary(self):
        """Show comprehensive game analysis."""
        if not self.game.board.move_stack:
            self.control_panel.display_status_message("Aucun coup à analyser", config.COLORS["error"])
            return
            
        # Show loading dialog
        loading_window, progress_var = self.analysis_view.show_loading_dialog(
            len(self.game.board.move_stack)
        )
        
        # Define progress callback
        def update_progress(value):
            self.window.after(0, lambda: progress_var.set(value))
        
        # Run analysis in a background thread
        def run_analysis():
            try:
                # Create a deep copy of the current move stack
                move_stack_copy = list(self.game.board.move_stack)
                
                # Create a fresh board for analysis to avoid state contamination
                # This ensures each analysis is completely independent
                analysis_board = chess.Board()
                
                # Run analysis with the copied moves
                results = self.game_analyzer.analyze_game(
                    move_stack_copy,
                    update_progress,
                    analysis_board
                )
                
                # Show results
                self.window.after(0, lambda: self._show_analysis_results(loading_window, results))
            except Exception as e:
                print(f"Error during game analysis: {e}")
                self.window.after(0, loading_window.destroy)
                self.control_panel.display_status_message("Erreur lors de l'analyse", config.COLORS["error"])
        
        # Start analysis thread
        threading.Thread(target=run_analysis, daemon=True).start()
    
    def _show_analysis_results(self, loading_window, results):
        """Show analysis results after analysis is complete."""
        loading_window.destroy()
        self.analysis_view.show_analysis(results)
    
    def load_pgn_file(self):
        """Load a chess game from a PGN file."""
        file_path = filedialog.askopenfilename(
            title="Ouvrir un fichier PGN",
            filetypes=[("Fichiers PGN", "*.pgn"), ("Tous les fichiers", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Open the PGN file
            with open(file_path, 'r') as pgn_file:
                # Read the game
                pgn_game = chess.pgn.read_game(pgn_file)
                
                if pgn_game is None:
                    self.control_panel.display_status_message("Fichier PGN invalide", config.COLORS["error"])
                    return
                    
                # Load the game
                success = self.game.load_from_pgn(pgn_game)
                
                if success:
                    # Enable PGN navigation buttons
                    self.enable_pgn_navigation()
                    self.pgn_loaded = True
                    
                    # Update the board view
                    self.board_view.redraw_board()
                    self.update_game_info()
                    
                    # Display success message
                    self.control_panel.display_status_message(
                        f"Partie chargée: {pgn_game.headers.get('White', 'Unknown')} vs {pgn_game.headers.get('Black', 'Unknown')}",
                        config.COLORS["success"]
                    )
                else:
                    self.control_panel.display_status_message("Erreur lors du chargement de la partie", config.COLORS["error"])
        except Exception as e:
            self.control_panel.display_status_message(f"Erreur: {str(e)}", config.COLORS["error"])
            print(f"Error loading PGN file: {e}")

    def enable_pgn_navigation(self):
        """Enable PGN navigation buttons."""
        self.first_move_btn.config(state=tk.NORMAL)
        self.prev_move_btn.config(state=tk.NORMAL)
        self.next_move_btn.config(state=tk.NORMAL)
        self.last_move_btn.config(state=tk.NORMAL)

    def disable_pgn_navigation(self):
        """Disable PGN navigation buttons."""
        self.first_move_btn.config(state=tk.DISABLED)
        self.prev_move_btn.config(state=tk.DISABLED)
        self.next_move_btn.config(state=tk.DISABLED)
        self.last_move_btn.config(state=tk.DISABLED)

    def go_to_first_move(self):
        """Go to the first move of the loaded PGN."""
        if self.pgn_loaded:
            if self.game.go_to_move(-1):  # -1 is typically the starting position
                self.board_view.redraw_board()
                self.update_game_info()
                self.analyze_position_async()

    def go_to_prev_move(self):
        """Go to the previous move in the loaded PGN."""
        if self.pgn_loaded:
            if self.game.go_to_prev_move():
                self.board_view.redraw_board()
                self.update_game_info()
                self.analyze_position_async()

    def go_to_next_move(self):
        """Go to the next move in the loaded PGN."""
        if self.pgn_loaded:
            if self.game.go_to_next_move():
                self.board_view.redraw_board()
                self.update_game_info()
                self.analyze_position_async()

    def go_to_last_move(self):
        """Go to the last move of the loaded PGN."""
        if self.pgn_loaded and hasattr(self.game, 'pgn_moves'):
            if self.game.go_to_move(len(self.game.pgn_moves) - 1):
                self.board_view.redraw_board()
                self.update_game_info()
                self.analyze_position_async()

    def run(self):
        """Start the main application loop."""
        self.window.mainloop()
