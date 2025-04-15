"""
Main window for the chess application.
Integrates all GUI components and handles user interactions.
"""

import threading
import tkinter as tk
import sys  # Add missing import for sys module
import os  # Add missing import for os module
import time  # Add missing import for time module
from tkinter import ttk, font, filedialog
import chess
import chess.pgn

from src.core.chess_game import ChessGame
from src.engine.engine_manager import EngineManager
from src.analysis.game_analyzer import GameAnalyzer
from src.analysis.game_difficulty import add_difficulty_analysis_to_game_analyzer
from src.utils import config, resource_loader
from src.gui.board_view import BoardView
from src.gui.controls import ControlPanel, AnalysisPanel
from src.gui.analysis_view import GameAnalysisView
from src.gui.player_banner import PlayerBanner
from src.gui.evaluation_bar import EvaluationBar

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
        self.game_analyzer = add_difficulty_analysis_to_game_analyzer(self.game_analyzer)
        # Create main window
        self.window = tk.Tk()
        self.window.title("Chessoria")
        self.window.configure(bg=config.COLORS["background"])
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Add the icon
        resource_loader.load_app_icon(self.window)
        
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
        
        # Create main frame with padding - reduce top padding to 0 to remove gap
        self.main_frame = ttk.Frame(self.window, padding=(15, 0, 15, 15))  # left, top, right, bottom
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
        # We don't need padding here as it can create empty space
        self.title_label.pack(pady=0)
        
        # Create layout frames
        self.game_frame = ttk.Frame(self.main_frame)
        self.game_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.info_frame = ttk.Frame(self.main_frame, padding=10)
        self.info_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Créer un conteneur spécifique pour l'échiquier et ses éléments associés
        self.board_container = ttk.Frame(self.game_frame)
        self.board_container.pack(fill=tk.BOTH, expand=True)
        
        # Ajout du banner des joueurs en haut du conteneur d'échiquier - initialized but not shown
        self.player_banner = PlayerBanner(self.board_container, top_padding=0)
        # PlayerBanner is created but not shown by default - it will be shown when PGN is loaded
        
        # Créer un conteneur horizontal pour l'échiquier et la barre d'évaluation
        self.board_and_eval_container = ttk.Frame(self.board_container)
        self.board_and_eval_container.pack(padx=10, pady=10)
        
        # Canvas for chess board with subtle border
        self.canvas_frame = ttk.Frame(self.board_and_eval_container, borderwidth=2, relief="solid")
        self.canvas_frame.pack(side=tk.LEFT)
        
        self.canvas = tk.Canvas(
            self.canvas_frame, 
            width=self.canvas_width, 
            height=self.canvas_height,
            bg=config.COLORS["background"], 
            highlightthickness=0
        )
        self.canvas.pack()
        
        # Ajouter la barre d'évaluation à droite de l'échiquier
        self.evaluation_bar = EvaluationBar(
            self.board_and_eval_container,
            width=30,
            height=self.canvas_height
        )
        self.evaluation_bar.pack(side=tk.LEFT, padx=(10, 0), fill=tk.Y)
        
        # Set up control panel
        control_callbacks = {
            "flip_board": self.flip_board,
            "undo_move": self.undo_last_move,
            "new_game": self.new_game,
            "analyze_game": self.analyze_game_summary
        }
        self.control_panel = ControlPanel(self.game_frame, control_callbacks)
        
        # Set up PGN navigation panel
        self.pgn_nav_frame = ttk.Frame(self.game_frame, padding=(0, 2))  # Reduced from padding=(0, 10)
        self.pgn_nav_frame.pack(fill=tk.X)
        
        # Create a modern navigation container with rounded corners and subtle styling
        self.nav_container = tk.Frame(
            self.pgn_nav_frame, 
            bg=config.COLORS["background"],
            padx=5,
            pady=2  # Reduced from pady=5
        )
        self.nav_container.pack(pady=2)  # Reduced from pady=5
        
        # Navigation button base style
        nav_button_style = {
            "font": font.Font(family="Segoe UI Symbol", size=12, weight="bold"),
            "borderwidth": 0,
            "padx": 12,
            "pady": 6,
            "cursor": "hand2",
            "relief": "flat",
            "highlightthickness": 0
        }
        
        # Button hover effect
        def on_hover(e, button, bg_color, hover_color):
            if button['state'] != tk.DISABLED:
                button.config(background=hover_color)
            
        def on_leave(e, button, bg_color):
            if button['state'] != tk.DISABLED:
                button.config(background=bg_color)
        
        # Base colors for navigation buttons
        nav_color = "#64748B"
        nav_hover = "#475569"
        disabled_color = "#A0AEC0"
        
        # First move button with icon
        self.first_move_btn = tk.Button(
            self.nav_container, 
            text="⏮",  # Unicode first track button
            command=self.go_to_first_move, 
            state=tk.DISABLED,
            bg=nav_color,
            fg="white",
            activebackground=nav_hover,
            activeforeground="white",
            disabledforeground="white",
            **nav_button_style
        )
        self.first_move_btn.pack(side=tk.LEFT, padx=3)
        self.first_move_btn.bind("<Enter>", lambda e: on_hover(e, self.first_move_btn, nav_color, nav_hover))
        self.first_move_btn.bind("<Leave>", lambda e: on_leave(e, self.first_move_btn, nav_color))
        
        # Previous move button with icon
        self.prev_move_btn = tk.Button(
            self.nav_container, 
            text="◀",  # Unicode play arrow
            command=self.go_to_prev_move, 
            state=tk.DISABLED,
            bg=nav_color,
            fg="white", 
            activebackground=nav_hover,
            activeforeground="white",
            disabledforeground="white",
            **nav_button_style
        )
        self.prev_move_btn.pack(side=tk.LEFT, padx=3)
        self.prev_move_btn.bind("<Enter>", lambda e: on_hover(e, self.prev_move_btn, nav_color, nav_hover))
        self.prev_move_btn.bind("<Leave>", lambda e: on_leave(e, self.prev_move_btn, nav_color))
        
        # Next move button with icon
        self.next_move_btn = tk.Button(
            self.nav_container, 
            text="▶",  # Unicode play arrow
            command=self.go_to_next_move, 
            state=tk.DISABLED,
            bg=nav_color,
            fg="white",
            activebackground=nav_hover,
            activeforeground="white",
            disabledforeground="white",
            **nav_button_style
        )
        self.next_move_btn.pack(side=tk.LEFT, padx=3)
        self.next_move_btn.bind("<Enter>", lambda e: on_hover(e, self.next_move_btn, nav_color, nav_hover))
        self.next_move_btn.bind("<Leave>", lambda e: on_leave(e, self.next_move_btn, nav_color))
        
        # Last move button with icon
        self.last_move_btn = tk.Button(
            self.nav_container, 
            text="⏭",  # Unicode last track button
            command=self.go_to_last_move, 
            state=tk.DISABLED,
            bg=nav_color,
            fg="white",
            activebackground=nav_hover,
            activeforeground="white",
            disabledforeground="white",
            **nav_button_style
        )
        self.last_move_btn.pack(side=tk.LEFT, padx=3)
        self.last_move_btn.bind("<Enter>", lambda e: on_hover(e, self.last_move_btn, nav_color, nav_hover))
        self.last_move_btn.bind("<Leave>", lambda e: on_leave(e, self.last_move_btn, nav_color))
        
        # Set up analysis panel
        self.analysis_panel = AnalysisPanel(self.info_frame)
    
    def setup_event_handlers(self):
        """Set up event handlers for user interactions."""
        self.canvas.bind("<Button-1>", self.on_square_clicked)
        self.canvas.bind("<Motion>", self.on_square_hover)
    
    def on_closing(self):
        """Handle window closing event."""
        self.analysis_running = False
        # Libérer les ressources du moteur
        if hasattr(self, "engine_manager") and self.engine_manager:
            try:
                self.engine_manager.quit()
            except Exception:
                pass
        try:
            # Arrêter la boucle principale
            self.window.quit()
        except Exception:
            pass
        try:
            # Détruire la fenêtre
            if self.window:
                self.window.destroy()
        except Exception:
            pass
        # Terminer immédiatement le processus
        os._exit(0)
    
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
                
            # Check if this is a potential pawn promotion move
            is_potential_promotion = (
                moving_piece.piece_type == chess.PAWN and 
                ((moving_piece.color == chess.WHITE and chess.square_rank(square) == 7) or
                 (moving_piece.color == chess.BLACK and chess.square_rank(square) == 0))
            )
            
            # For potential promotion moves, we need to check if any promotion variant is legal
            if is_potential_promotion:
                # Check if any promotion move is legal (with queen is enough for check)
                promotion_move = chess.Move(from_square, square, promotion=chess.QUEEN)
                if promotion_move in self.game.get_legal_moves():
                    # Show promotion dialog if legal
                    self.show_promotion_dialog(from_square, square)
                    return
            
            # Regular move check (non-promotion)
            move = chess.Move(from_square, square)
            legal_moves = self.game.get_legal_moves()
            
            print(f"Attempting move: {from_square}->{square}")
            print(f"Move in legal moves: {move in legal_moves}")
            
            if move in legal_moves:
                # Handle the move
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
        promo_window.geometry("300x450")
        promo_window.resizable(False, False)
        promo_window.configure(bg=config.COLORS["background"])
        promo_window.transient(self.window)
        promo_window.grab_set()
        
        # Get the player's color
        player_color = self.game.board.turn
        color_prefix = 'white' if player_color == chess.WHITE else 'black'
        
        # Center the dialog
        window_width = 300
        window_height = 450
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x_position = int((screen_width - window_width) / 2)
        y_position = int((screen_height - window_height) / 2)
        promo_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        header = tk.Label(
            promo_window, 
            text="Choisissez la promotion", 
            font=font.Font(**config.FONTS["title"]), 
            bg=config.COLORS["background"], 
            fg=config.COLORS["primary_text"]
        )
        header.pack(pady=20)
        
        # Create smaller piece images for the dialog using PIL
        from PIL import Image, ImageTk
        from src.utils.resource_loader import resource_path
        
        # Create storage for promotion piece images (to prevent garbage collection)
        promo_window.piece_images = {}
        
        # Promotion options
        options = [
            ("Dame", chess.QUEEN, f"{color_prefix}-queen"), 
            ("Tour", chess.ROOK, f"{color_prefix}-rook"),
            ("Fou", chess.BISHOP, f"{color_prefix}-bishop"), 
            ("Cavalier", chess.KNIGHT, f"{color_prefix}-knight")
        ]
        
        for text, promotion_piece, img_key in options:
            # Create frame for each option
            option_frame = tk.Frame(promo_window, bg=config.COLORS["background"])
            option_frame.pack(pady=10, fill='x', padx=20)
            
            try:
                # Load the piece image directly from file and resize it
                image_path = resource_path(f"images/{img_key}.png")
                if os.path.exists(image_path):
                    # Load and resize image
                    img = Image.open(image_path).convert("RGBA")
                    img = img.resize((40, 40), Image.Resampling.LANCZOS)
                    photo_img = ImageTk.PhotoImage(img)
                    
                    # Store reference to prevent garbage collection
                    promo_window.piece_images[img_key] = photo_img
                    
                    btn = tk.Button(
                        option_frame, 
                        text=f" {text}", 
                        image=photo_img,
                        compound=tk.LEFT,
                        font=font.Font(**config.FONTS["button"]), 
                        bg=config.COLORS["new_game_button"], 
                        fg="white", 
                        activebackground=config.COLORS["new_game_button_active"],
                        command=lambda p=promotion_piece: self.apply_promotion(from_square, to_square, p, promo_window)
                    )
                else:
                    # Fall back to text-only button if image not found
                    btn = tk.Button(
                        option_frame, 
                        text=text, 
                        font=font.Font(**config.FONTS["button"]), 
                        bg=config.COLORS["new_game_button"], 
                        fg="white", 
                        activebackground=config.COLORS["new_game_button_active"],
                        command=lambda p=promotion_piece: self.apply_promotion(from_square, to_square, p, promo_window)
                    )
            except Exception as e:
                print(f"Error creating promotion button with image: {e}")
                # Fallback to text-only button
                btn = tk.Button(
                    option_frame, 
                    text=text, 
                    font=font.Font(**config.FONTS["button"]), 
                    bg=config.COLORS["new_game_button"], 
                    fg="white", 
                    activebackground=config.COLORS["new_game_button_active"],
                    command=lambda p=promotion_piece: self.apply_promotion(from_square, to_square, p, promo_window)
                )
            btn.pack(fill='x', ipady=10)
    
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
        
        # Hide the player banner when starting a new game
        if hasattr(self, 'player_banner'):
            self.player_banner.hide()
        
        # Reset PGN-related state
        self.pgn_loaded = False
        self.disable_pgn_navigation()
        
        # Update window title to default
        self.window.title("Chessoria")
        
        # Update game info and display message
        self.update_game_info()
        self.control_panel.display_status_message("Nouvelle partie commencée", config.COLORS["success"])
        self.analyze_position_async()
    
    def analyze_position_async(self):
        """Start asynchronous position analysis."""
        # Éviter des analyses trop fréquentes avec un système de limitation de débit
        current_time = time.time()
        if hasattr(self, 'last_analysis_time'):
            # Ne pas analyser plus souvent que toutes les 0.5 secondes
            if current_time - self.last_analysis_time < 0.5:
                return
        
        # Mettre à jour le timestamp de la dernière analyse
        self.last_analysis_time = current_time
        
        # Lancer l'analyse dans un thread séparé
        threading.Thread(target=self.analyze_position, daemon=True).start()
    
    def update_evaluation_from_engine_data(self, info):
        """
        Met à jour la barre d'évaluation directement à partir des données brutes du moteur.
        
        Args:
            info: Liste d'informations retournée par le moteur d'analyse
        """
        if not info or not isinstance(info, list) or len(info) == 0:
            return
            
        # Récupérer le score du meilleur coup (premier élément)
        best_move_data = info[0]
        if 'score' not in best_move_data:
            return
            
        score_obj = best_move_data['score']
        
        # Extraire les valeurs d'évaluation
        is_mate = False
        mate_in = 0
        eval_value = 0.0
        
        # Déterminer si le score est du point de vue des blancs ou des noirs
        is_white_perspective = self.game.get_turn() == chess.WHITE
        
        # VÉRIFICATION DIRECTE DU TEXTE pour les objets PovScore(Mate)
        str_score = str(score_obj)
        if "Mate" in str_score:
            is_mate = True
            # Extraire le nombre directement depuis la chaîne
            try:
                # Format: "PovScore(Mate(+1), WHITE)" ou "PovScore(Mate(-2), BLACK)"
                mate_part = str_score.split("Mate(")[1].split(")")[0]
                mate_value = int(mate_part.replace("+", ""))
                mate_in = mate_value
                eval_value = 99.0 if mate_in > 0 else -99.0
            except Exception:
                # Valeur par défaut
                mate_in = 1 if "+" in str_score else -1
                eval_value = 99.0 if mate_in > 0 else -99.0
        elif hasattr(score_obj, 'mate'):
            # Récupérer la valeur mate directement
            try:
                mate_value = None
                if callable(score_obj.mate):
                    mate_value = score_obj.mate()
                else:
                    mate_value = score_obj.mate
                
                if mate_value is not None:
                    is_mate = True
                    mate_in = mate_value
                    eval_value = 99.0 if mate_value > 0 else -99.0
            except Exception:
                pass
        
        # Si nous avons une valeur de score très élevée mais pas encore détecté de mat
        if not is_mate and 'cp' in dir(score_obj):
            try:
                # Extraire la valeur cp
                cp_value = None
                if callable(score_obj.cp):
                    cp_value = score_obj.cp()
                else:
                    cp_value = score_obj.cp
                
                # Si la valeur CP est très élevée, considérer comme un mat
                if cp_value is not None:
                    eval_value = cp_value / 100.0
                    if abs(eval_value) >= 90.0:
                        is_mate = True
                        mate_in = 1 if eval_value > 0 else -1
            except Exception:
                pass
        
        # Si nous n'avons pas encore de valeur et ce n'est pas un mat, essayer d'extraire CP
        if not is_mate and eval_value == 0.0:
            try:
                # Méthode 1: Accès direct à l'attribut .cp
                if hasattr(score_obj, 'cp'):
                    if callable(score_obj.cp):
                        cp_value = score_obj.cp()
                    else:
                        cp_value = score_obj.cp
                    if cp_value is not None:
                        eval_value = cp_value / 100.0
                
                # Méthode 2: Accès via score_obj.score()
                elif hasattr(score_obj, 'score'):
                    cp_value = None
                    inner_score = score_obj.score()
                    if hasattr(inner_score, 'cp'):
                        if callable(inner_score.cp):
                            cp_value = inner_score.cp()
                        else:
                            cp_value = inner_score.cp
                    if cp_value is not None:
                        eval_value = cp_value / 100.0
                
                # Méthode 3: Extraire la valeur à partir de la représentation en chaîne
                if eval_value == 0.0:
                    str_rep = str(score_obj)
                    if "Cp(" in str_rep:
                        # Format comme "PovScore(Cp(+5), BLACK)"
                        cp_part = str_rep.split("Cp(")[1].split(")")[0]
                        
                        # Vérifier si le score est négatif
                        is_negative = cp_part.startswith('-')
                        # Enlever le signe (+ ou -) et convertir en entier positif
                        cp_value = int(cp_part.replace("+", "").replace("-", ""))
                        # Rétablir le signe si nécessaire
                        if is_negative:
                            cp_value = -cp_value
                        eval_value = cp_value / 100.0
            except Exception:
                pass
        
        # VÉRIFICATION FINALE: top_moves pour les mats
        try:
            for item in info:
                if 'pv' in item and item['pv'] and len(item['pv']) > 0:
                    move = item['pv'][0]
                    move_san = self.game.get_move_san(move)
                    if '#' in move_san:
                        is_mate = True
                        mate_in = 1  # Mat en 1 coup si # est visible
                        eval_value = 99.0 if is_white_perspective else -99.0
                        break
        except Exception:
            pass
        
        # CORRECTION: Si nous sommes du point de vue des noirs, inverser la valeur
        if not is_white_perspective:
            eval_value = -eval_value
            if is_mate:
                mate_in = -mate_in
        
        # Log stratégique pour les mats uniquement, évite de spam les logs normaux
        if is_mate:
            print(f"[DEBUG] Mat détecté: {mate_in} coups, évaluation: {eval_value}")
        
        # Mettre à jour directement la barre d'évaluation
        if hasattr(self, 'evaluation_bar'):
            try:
                def update_bar():
                    self.evaluation_bar.update_evaluation(
                        evaluation=eval_value,
                        is_mate=is_mate,
                        mate_in=mate_in,
                        animate=True
                    )
                
                # Exécuter depuis le thread principal
                self.window.after(0, update_bar)
            except Exception as e:
                print(f"[ERROR] Erreur lors de la mise à jour de la barre d'évaluation: {e}")

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
            
            # Vérifier d'abord si l'analyse a détecté explicitement un mat
            is_mate = False
            mate_in = 0
            mate_eval = 0.0
            
            # Récupérer les informations explicites de mate si disponibles
            if "is_mate" in info[0] and info[0]["is_mate"]:
                is_mate = True
                mate_in = info[0]["mate_in"]
                mate_eval = 10.0 if mate_in > 0 else -10.0
            
            # Si on a un objet score qui contient une méthode mate(), vérifier directement
            elif 'score' in info[0]:
                score_obj = info[0]['score']
                if hasattr(score_obj, 'mate'):
                    try:
                        mate_value = score_obj.mate() if callable(score_obj.mate) else score_obj.mate
                        if mate_value is not None:
                            is_mate = True
                            mate_in = mate_value
                            mate_eval = 10.0 if mate_in > 0 else -10.0
                    except Exception:
                        pass
            
            # Utiliser notre nouvelle méthode pour mettre à jour la barre d'évaluation
            # Si un mat a été détecté, utiliser ces valeurs
            if is_mate:
                self.window.after(0, lambda: self.evaluation_bar.update_evaluation(
                    evaluation=mate_eval,
                    is_mate=True,
                    mate_in=mate_in,
                    animate=True
                ))
            else:
                self.update_evaluation_from_engine_data(info)
            
            # Le reste du traitement reste inchangé
            for item in info:
                if item is None:
                    continue
                
                if 'pv' not in item or not item['pv']:
                    continue
                    
                move = item['pv'][0]
                if 'score' not in item:
                    continue
                    
                score_obj = item['score']
                formatted_score = self.engine_manager.format_score(score_obj)
                
                move_san = self.game.get_move_san(move)
                top_moves.append((move_san, formatted_score))
                
            # Mettre à jour l'interface utilisateur depuis le thread principal
            if top_moves:
                self.window.after(0, lambda: self.analysis_panel.display_top_moves(top_moves))
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
        current_turn = self.game.get_turn()
        self.analysis_panel.update_turn_indicator(current_turn == chess.WHITE)
        
        # Mettre à jour le banner des joueurs avec le tour actuel
        if hasattr(self, 'player_banner'):
            self.player_banner.update_names(current_turn=current_turn)
    
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
                self.window.after(0, loading_window.destroy)
                self.control_panel.display_status_message("Erreur lors de l'analyse", config.COLORS["error"])
        
        # Start analysis thread
        threading.Thread(target=run_analysis, daemon=True).start()
    
    def _show_analysis_results(self, loading_window, results):
        """Show analysis results after analysis is complete."""
        loading_window.destroy()
        
        # Add PGN headers to analysis results if a game is loaded
        if hasattr(self.game, 'pgn_headers') and self.game.pgn_headers:
            results['headers'] = self.game.pgn_headers
            
        self.analysis_view.game_analyzer = self.game_analyzer
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
                    
                    # Mettre à jour le banner des joueurs avec les informations du PGN
                    if hasattr(self, 'player_banner'):
                        # Update and show the player banner
                        self.player_banner.update_from_pgn_headers(pgn_game.headers, self.game.get_turn())
                        self.player_banner.show()  # Make the banner visible
                    
                    # Update general game info
                    self.update_game_info()
                    
                    # Mise à jour du titre de la fenêtre avec les noms des joueurs
                    white_name = pgn_game.headers.get("White", "Unknown")
                    black_name = pgn_game.headers.get("Black", "Unknown")
                    self.window.title(f"Chessoria - {white_name} vs {black_name}")
                    
                    # Display success message
                    self.control_panel.display_status_message(
                        f"Partie chargée: {white_name} vs {black_name}",
                        config.COLORS["success"]
                    )
                else:
                    self.control_panel.display_status_message("Erreur lors du chargement de la partie", config.COLORS["error"])
        except Exception as e:
            self.control_panel.display_status_message(f"Erreur: {str(e)}", config.COLORS["error"])

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
