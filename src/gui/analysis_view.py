"""
Game analysis visualization module.
Displays detailed analysis of chess games.
"""

import tkinter as tk
from tkinter import ttk, font
import chess
from src.utils import resource_loader
from src.utils import config
from src.gui.moderntabs import ModernTabs
from src.gui.analysis.mini_board import MiniChessBoard
from src.gui.analysis.summary_tab import _create_summary_tab_content
from src.gui.analysis.moves_tab import _create_moves_tab_content
from src.gui.analysis.utils.style_utils import set_card_state


# Helper function for binding mousewheel
def _bind_mousewheel_to_widgets(parent, on_mousewheel, on_linux_up, on_linux_down):
    """Recursively bind mousewheel events to all widgets."""
    parent.bind("<MouseWheel>", on_mousewheel)
    parent.bind("<Button-4>", on_linux_up)
    parent.bind("<Button-5>", on_linux_down)
    
    # Recursively bind to all children
    for child in parent.winfo_children():
        _bind_mousewheel_to_widgets(child, on_mousewheel, on_linux_up, on_linux_down)

class GameAnalysisView:
    """Displays detailed game analysis in a separate window."""
    
    def __init__(self, parent, game_analyzer, piece_images=None):
        """
        Initialize the game analysis view.
        
        Args:
            parent: Parent window
            game_analyzer: GameAnalyzer instance
            piece_images: Dictionary of piece images
        """
        self.parent = parent
        self.game_analyzer = game_analyzer
        self.piece_images = piece_images  # Store the piece images
        self.selected_move_row = None  # Track selected move row
        self.position_history = None   # Will store FEN positions for each move
        self.mini_board = None         # Reference to mini-board widget
        self.move_info_label = None    # Reference to move info label
        self.eval_info_label = None    # Reference to evaluation label
        self.best_move_label = None    # Reference to best move label
        
        # Error navigation attributes
        self.error_cards = []          # References to move cards with errors
        self.all_cards = []            # All move cards for selection management
        self.current_error_index = 0   # Index of current error being viewed
        self.error_mode_active = False # Whether error mode is currently active
        self.error_navigation = None   # Navigation controls reference

    def get_position_at_move(self, move_index):
        """Get the chess position (FEN) at a specific move index."""
        if not hasattr(self, 'position_history') or not self.position_history:
            return None
            
        # Position history includes initial position at index 0
        if 0 <= move_index+1 < len(self.position_history):
            return self.position_history[move_index+1]
        
        # Return initial position if requested
        if move_index == -1 and len(self.position_history) > 0:
            return self.position_history[0]
            
        return None
    
    def show_analysis(self, analysis_results):
        """
        Display game analysis results.
        
        Args:
            analysis_results: Dictionary with analysis data:
                - move_evaluations: List of move evaluations
                - white_stats: Statistics for white player
                - black_stats: Statistics for black player
        """
        move_evaluations = analysis_results["move_evaluations"]
        white_stats = analysis_results["white_stats"]
        black_stats = analysis_results["black_stats"]
        
        # Store the complete analysis results for access by tab components
        self.analysis_results = analysis_results
        
        # Get position history if it exists or create it
        if "position_history" in analysis_results:
            self.position_history = analysis_results["position_history"]
        else:
            # Generate position history if it doesn't exist
            self.position_history = self._generate_position_history(move_evaluations)
        
        # Create analysis window
        analysis_window = tk.Toplevel(self.parent)
        analysis_window.title("Bilan de Partie")
        analysis_window.geometry("1200x900")
        analysis_window.resizable(True, True)
        analysis_window.configure(bg=config.COLORS["background"])

        resource_loader.load_app_icon(analysis_window)
        
        # Create fonts
        title_font = font.Font(family="Segoe UI", size=13, weight="bold")
        subheader_font = font.Font(family="Segoe UI", size=11, weight="bold")
        text_font = font.Font(family="Segoe UI", size=10)

        # Create ModernTabs container instead of ttk.Notebook
        self.tabs = ModernTabs(analysis_window)
        self.tabs.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create content frames for each tab
        summary_frame = tk.Frame(self.tabs, bg=config.COLORS["background"])
        moves_frame = tk.Frame(self.tabs, bg=config.COLORS["background"])
        
        # Add the tabs
        self.tabs.add_tab("Bilan", summary_frame)
        self.tabs.add_tab("Analyse", moves_frame)
        
        # Add summary tab
        _create_summary_tab_content(self, summary_frame, move_evaluations, white_stats, black_stats,
                                   title_font, subheader_font, text_font)
        
        # Add moves analysis tab
        _create_moves_tab_content(self, moves_frame, move_evaluations, text_font)
    
    def _generate_position_history(self, move_evaluations):
        """Generate position history from move evaluations if not provided."""
        try:
            # Create a new board to replay the moves
            board = chess.Board()
            positions = [board.fen()]  # Start with initial position
            
            # Replay each move to generate positions
            for eval_data in move_evaluations:
                if "uci" in eval_data:
                    move = chess.Move.from_uci(eval_data["uci"])
                    board.push(move)
                    positions.append(board.fen())
                else:
                    # If UCI not available, try to parse from SAN
                    try:
                        san = eval_data.get("san")
                        if san:
                            move = board.parse_san(san)
                            board.push(move)
                            positions.append(board.fen())
                    except Exception as e:
                        print(f"Error parsing move: {e}")
                        # Add a duplicate of the last position as fallback
                        positions.append(positions[-1] if positions else board.fen())
            
            return positions
        except Exception as e:
            print(f"Error generating position history: {e}")
            return None

    def _create_count_statistics(self, parent, total_moves, white_moves, black_moves, subheader_font, text_font):
        """Create an enhanced section for count statistics with more visual emphasis."""
        
        # Create a container with subtle background color to make it stand out
        count_container = tk.Frame(
            parent,
            bg="#F5F7FA",  # Light blue-gray background for contrast
            highlightthickness=2,
            highlightbackground=config.COLORS["selected_square"],  # Border color matching your theme
            padx=15,
            pady=15
        )
        count_container.pack(fill=tk.X, expand=True, pady=10)
        
        # Title for the counts section
        count_title = tk.Label(
            count_container,
            text="DÉCOMPTE DES COUPS",
            font=subheader_font,
            bg="#F5F7FA",
            fg=config.COLORS["primary_text"]
        )
        count_title.pack(anchor="center", pady=(0, 15))
        
        # Create a grid for the statistics with 3 columns
        count_grid = tk.Frame(count_container, bg="#F5F7FA")
        count_grid.pack(fill=tk.X, expand=True, padx=10)
        
        # Configure columns for equal width
        count_grid.columnconfigure(0, weight=1)
        count_grid.columnconfigure(1, weight=1)
        count_grid.columnconfigure(2, weight=1)
        
        # Create styled stat boxes for each count
        self._create_count_box(count_grid, "TOTAL", total_moves, 0, config.COLORS["primary_text"])
        self._create_count_box(count_grid, "BLANCS", white_moves, 1, "#333333")  # For white pieces
        self._create_count_box(count_grid, "NOIRS", black_moves, 2, "#333333")   # For black pieces

    def _create_count_box(self, parent, label_text, count_value, column, text_color):
        """Create a visually prominent box for each count statistic."""
        
        # Container for each stat
        stat_box = tk.Frame(
            parent,
            bg="white",  # White background for the box
            highlightthickness=1,
            highlightbackground="#E0E0E0",
            padx=10,
            pady=10
        )
        stat_box.grid(row=0, column=column, sticky="nsew", padx=5)
        
        # Label (e.g., "TOTAL", "BLANCS", "NOIRS")
        tk.Label(
            stat_box,
            text=label_text,
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg=text_color
        ).pack(anchor="center")
        
        # Count value with larger, bolder font
        count_label = tk.Label(
            stat_box,
            text=str(count_value),
            font=("Segoe UI", 24, "bold"),  # Much larger font for emphasis
            bg="white",
            fg=config.COLORS["selected_square"]  # Use your theme color for the number
        )
        count_label.pack(anchor="center", pady=5)
        
        # Add a decorative underline
        underline = tk.Frame(
            stat_box,
            height=3,
            bg=config.COLORS["selected_square"],  # Match your theme color
            width=40  # Fixed width for the underline
        )
        underline.pack(anchor="center")
        
    # Helper methods for the modernized tab
    def _create_modern_player_stats(self, parent_frame, stats, text_font):
        """Create player statistics with modern styling."""
        # Don't display any text stats - the accuracy circle and move quality bars will handle everything
        
        # Display the move quality distribution directly
        self._create_enhanced_move_quality_display(parent_frame, stats, text_font)

    def _create_stat_row(self, parent, label_text, value_text, row, text_font):
        """Create a modern stat row with consistent styling."""
        label = tk.Label(
            parent, 
            text=label_text, 
            font=text_font, 
            bg="white",
            fg="#555555",
            anchor="w"
        )
        label.grid(row=row, column=0, sticky="w", pady=5)
        
        value = tk.Label(
            parent, 
            text=value_text, 
            font=text_font, 
            bg="white",
            fg="#333333",
            anchor="e"
        )
        value.grid(row=row, column=1, sticky="e", padx=(10, 0), pady=5)

    def _bind_mousewheel_to_widgets(self, parent, windows_callback, linux_up_callback, linux_down_callback):
        """Recursively bind mousewheel events to all widgets."""
        _bind_mousewheel_to_widgets(parent, windows_callback, linux_up_callback, linux_down_callback)
    
    def _create_player_stats_frame(self, parent, title, stats, subheader_font, text_font, side):
        """Create a frame with player statistics."""
        # Create frame with white background
        frame = tk.Frame(parent, bg="white", padx=15, pady=15, bd=1, relief=tk.RIDGE)
        frame.pack(side=side, expand=True, fill=tk.BOTH, padx=(0 if side == tk.LEFT else 10, 10 if side == tk.LEFT else 0))
        
        # Player title
        tk.Label(frame, text=title, font=subheader_font, bg="white", 
                fg=config.COLORS["primary_text"], pady=5).pack()
        
        # Accuracy with circular progress
        accuracy_size = 120
        canvas = tk.Canvas(frame, width=accuracy_size, height=accuracy_size, 
                         bg="white", highlightthickness=0)
        canvas.pack(pady=10)
        
        # Draw accuracy circle
        canvas.create_oval(10, 10, accuracy_size-10, accuracy_size-10, outline="#E0E0E0", width=10)
        
        # Arc color based on side
        arc_color = config.COLORS["excellent"] if title == "BLANCS" else "#2196F3"
        
        canvas.create_arc(10, 10, accuracy_size-10, accuracy_size-10, 
                        start=90, extent=-(stats.get("accuracy", 0)*3.6), 
                        outline=arc_color, width=10, style=tk.ARC)
        
        canvas.create_text(accuracy_size//2, accuracy_size//2, 
                        text=f"{stats.get('accuracy', 0)}%", 
                        font=font.Font(family="Segoe UI", size=20, weight="bold"), 
                        fill=config.COLORS["primary_text"])
        
        # Move classifications with stats
        classes_frame = tk.Frame(frame, bg="white")
        classes_frame.pack(fill=tk.X, pady=10)
        
        # Show each classification with count and percentage
        for cls, count in stats["counts"].items():
            if stats["total_moves"] > 0:
                percentage = round((count / stats["total_moves"]) * 100)
            else:
                percentage = 0
                
            cls_frame = tk.Frame(classes_frame, bg="white")
            cls_frame.pack(fill=tk.X, pady=2)
            
            # Get color for this classification
            cls_color = self.game_analyzer.get_classification_color(cls)
            
            # Label for classification name
            tk.Label(cls_frame, text=f"{cls}", width=12, anchor="w", 
                    font=text_font, bg="white", 
                    fg=config.COLORS["secondary_text"]).pack(side=tk.LEFT)
            
            # Progress bar frame
            bar_frame = tk.Frame(cls_frame, bg="#F0F2F5", height=15, width=150)
            bar_frame.pack(side=tk.LEFT, padx=5)
            bar_frame.pack_propagate(False)
            
            # Colored bar showing percentage
            if percentage > 0:
                bar = tk.Frame(bar_frame, bg=cls_color, height=15, width=percentage*1.5)
                bar.pack(side=tk.LEFT, anchor="w")
            
            # Count and percentage
            tk.Label(cls_frame, text=f"{count} ({percentage}%)", 
                    font=text_font, bg="white", 
                    fg=config.COLORS["secondary_text"]).pack(side=tk.LEFT)

    def _create_mini_board(self, parent_frame, move_evaluations):
        """Create a mini chess board panel."""
        # Create header with title
        header_frame = tk.Frame(parent_frame, bg=config.COLORS["background"])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title for the board section
        title_label = tk.Label(
            header_frame,
            text="Plateau d'analyse",
            font=font.Font(**config.FONTS["moves_title"]),
            bg=config.COLORS["background"],
            fg=config.COLORS["primary_text"]
        )
        title_label.pack(side=tk.LEFT)
        
        # Create container for the board
        board_container = tk.Frame(
            parent_frame,
            bg="white",
            highlightthickness=1,
            highlightbackground="#E0E0E0",
            padx=10,
            pady=10
        )
        board_container.pack(fill=tk.BOTH, expand=True)
        
        # Create the mini-board canvas with piece images
        self.mini_board = MiniChessBoard(board_container, piece_images=self.piece_images)
        self.mini_board.pack(anchor="center", pady=10)
        
        # Info panel below board with flip button to the right
        info_frame = tk.Frame(board_container, bg="white")
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Simple modern flip button - right aligned
        flip_button = tk.Button(
            info_frame,
            text="Flip",
            font=("Segoe UI", 9),
            bg=config.COLORS["control_button"],
            fg="white",
            activebackground=config.COLORS["control_button_active"],
            activeforeground="white",
            relief="flat",
            padx=10,
            pady=2,
            cursor="hand2",
            command=self._flip_analysis_board
        )
        flip_button.pack(side=tk.RIGHT, padx=5)
        
        # Move number and san display
        self.move_info_label = tk.Label(
            info_frame,
            text="Sélectionnez un coup pour voir la position",
            font=("Segoe UI", 11),
            bg="white",
            fg=config.COLORS["primary_text"]
        )
        self.move_info_label.pack(anchor="w", side=tk.LEFT)
        
        # Additional info labels below
        info_panel = tk.Frame(board_container, bg="white")
        info_panel.pack(fill=tk.X)
        
        # Evaluation display
        self.eval_info_label = tk.Label(
            info_panel,
            text="",
            font=("Segoe UI", 10),
            bg="white",
            fg=config.COLORS["secondary_text"]
        )
        self.eval_info_label.pack(anchor="w", pady=(5, 0))
        
        # Best move info (if applicable)
        self.best_move_label = tk.Label(
            info_panel,
            text="",
            font=("Segoe UI", 10),
            bg="white",
            fg=config.COLORS["secondary_text"]
        )
        self.best_move_label.pack(anchor="w", pady=(5, 0))
        
    def _flip_analysis_board(self):
        """Flip the analysis board orientation."""
        if self.mini_board:
            self.mini_board.flip_board()
            
            # If there's a currently selected move, redraw it to update the position
            if self.selected_move_row and hasattr(self.selected_move_row, 'move_index'):
                move_index = self.selected_move_row.move_index
                if self.position_history and move_index < len(self.position_history):
                    self.mini_board.update_to_position(self.position_history[move_index+1])

    def _create_moves_header(self, parent, header_font):
        """Create the header for the moves table."""
        moves_header = tk.Frame(parent, bg="#E0E0E0", padx=10, pady=10)
        moves_header.pack(fill=tk.X)
        moves_header.columnconfigure(0, weight=1)
        
        # Column headers
        columns = [
            ("Coup", 12),
            ("Évaluation", 12),
            ("Qualité", 12),
            ("Meilleur coup", 15),
            ("Impact", 10)
        ]
        
        # Configure grid columns
        for i in range(len(columns)):
            moves_header.columnconfigure(i, weight=1)
            
        # Add column headers to grid
        for i, (col_name, width) in enumerate(columns):
            tk.Label(moves_header, text=col_name, width=width, 
                    font=header_font, bg="#E0E0E0", anchor="w").grid(row=0, column=i, sticky="w")

    def _create_move_row(self, parent, eval, index, text_font):
        """Create a clickable row for a single move in the moves table."""
        # Alternate row colors
        bg_color = "white" if index % 2 == 0 else "#F5F5F5"
        
        move_frame = tk.Frame(parent, bg=bg_color, padx=10, pady=8)
        move_frame.pack(fill=tk.X)
        
        # Store the move index in the frame for reference
        move_frame.move_index = index
        
        # Configure grid columns
        for i in range(5):  # 5 columns
            move_frame.columnconfigure(i, weight=1)
        
        # Format evaluation score
        formatted_score = f"+{abs(eval['score_after']):.2f}" if eval['score_after'] >= 0 else f"-{abs(eval['score_after']):.2f}"
        formatted_change = f"{eval['score_change']:+.2f}"
        
        # Quality color
        quality_color = self.game_analyzer.get_classification_color(eval["classification"])
        
        # Score change color
        score_color = self.game_analyzer.get_score_color(eval["score_change"])
        
        # Get move text - ensure we use the correct move notation
        # Use move_text which includes the move number + SAN, or fall back to just SAN
        move_display = eval.get("move_text", "") if "move_text" in eval else eval.get("san", "")
        
        # Display move data
        columns = [
            (move_display, 12, None),  # Use move_text instead of just san
            (formatted_score, 12, None),
            (eval["classification"], 12, quality_color),
            (eval["best_move"] if eval["best_move"] else eval["san"], 15, None),
            (formatted_change, 10, score_color)
        ]
        
        # Create labels and store them in the frame for highlighting
        move_frame.labels = []
        
        for i, (text, width, color) in enumerate(columns):
            label = tk.Label(
                move_frame, 
                text=text, 
                width=width, 
                font=text_font, 
                bg=bg_color, 
                anchor="w",
                fg=color or config.COLORS["secondary_text"]
            )
            label.grid(row=0, column=i, sticky="w")
            move_frame.labels.append(label)
        
        # Make the entire row clickable by binding to both frame and labels
        move_frame.bind("<Button-1>", lambda e, idx=index, ev=eval: self._on_move_selected(e, idx, ev, move_frame))
        for label in move_frame.labels:
            label.bind("<Button-1>", lambda e, idx=index, ev=eval: self._on_move_selected(e, idx, ev, move_frame))
        
        return move_frame
    
    def _on_move_selected(self, event, move_index, move_eval, move_frame):
        """Handle click on a move row."""
        # Unhighlight previous selection if any
        if self.selected_move_row:
            try:
                self.selected_move_row.winfo_exists()
                self._unhighlight_move_row(self.selected_move_row)
            except (tk.TclError, AttributeError):
                pass
            
        # Highlight the selected row
        self._highlight_move_row(move_frame)
        self.selected_move_row = move_frame
        
        # Update mini board if we have position history
        if self.position_history and self.mini_board:
            if move_index < len(self.position_history):
                # Always clear existing visualizations first
                if hasattr(self.mini_board, 'delete'):
                    self.mini_board.delete("arrow")
                    self.mini_board.delete("highlight") 
                    self.mini_board.delete("error_symbol")
                
                # Get current and previous position FEN for move conversions
                current_position_fen = self.position_history[move_index+1]
                prev_position_fen = self.position_history[move_index] if move_index > 0 else self.position_history[0]
                
                # Update the board to this position
                self.mini_board.update_to_position(current_position_fen)
                
                # Get the move text
                if 'move_text' in move_eval and move_eval['move_text']:
                    move_text = move_eval['move_text']
                else:
                    move_number = (move_index // 2) + 1
                    is_white = move_index % 2 == 0
                    move_prefix = f"{move_number}." if is_white else f"{move_number}..."
                    move_text = f"{move_prefix} {move_eval['san']}"
                
                # Update move information label
                self.move_info_label.config(
                    text=move_text,
                    font=("Segoe UI", 11, "bold")
                )
                
                # Update evaluation info
                self._update_evaluation_labels(move_eval)
                
                # Determine if this is an error move
                error_type = None
                if move_eval.get("classification", "") == "Grosse erreur":
                    error_type = "Grosse erreur"
                elif move_eval.get("classification", "") == "Erreur":
                    error_type = "Erreur"
                # For excellent moves, trigger excellent highlighting without coloring the square.
                elif move_eval.get("classification", "") == "Excellent":
                    uci_move = self._deduce_uci_move_from_positions(prev_position_fen, current_position_fen)
                    if uci_move:
                        self.mini_board.highlight_excellent_move(uci_move)
                # If this is an error, visualize it
                if error_type:
                    # Find the actual move by comparing positions
                    uci_move = self._deduce_uci_move_from_positions(prev_position_fen, current_position_fen)
                    
                    # If direct deduction fails, try to convert from SAN
                    if not uci_move and "san" in move_eval:
                        try:
                            tmp_board = chess.Board(prev_position_fen)
                            move = tmp_board.parse_san(move_eval["san"])
                            uci_move = move.uci()
                        except Exception:
                            pass
                    
                    # Get best move in UCI format if available
                    best_move_uci = None
                    if move_eval.get("best_move"):
                        try:
                            tmp_board = chess.Board(prev_position_fen)
                            best_move = tmp_board.parse_san(move_eval["best_move"])
                            best_move_uci = best_move.uci()
                        except Exception:
                            pass
                    
                    # Visualize the error if UCI move is available
                    if uci_move:
                        self.mini_board.highlight_error_move(uci_move, best_move_uci, error_type)
            else:
                # If position not available
                self.mini_board.draw_board()  # Just show empty board
                self.move_info_label.config(text="Position non disponible")
                self.eval_info_label.config(text="")
                self.best_move_label.config(text="")

    def  _update_evaluation_labels(self, move_eval):
        """Update evaluation labels with move data."""
        # Update evaluation info
        score_after = move_eval["score_after"]
        formatted_score = f"+{abs(score_after):.2f}" if score_after >= 0 else f"-{abs(score_after):.2f}"
        color_advantage = "Blancs" if score_after >= 0 else "Noirs"
        
        self.eval_info_label.config(
            text=f"Évaluation: {formatted_score} (avantage {color_advantage})"
        )
        
        # Show best move if there was a better one
        if move_eval["best_move"] and move_eval["best_move"] != move_eval["san"]:
            # Get the score change text with color indicator for errors
            score_change_text = ""
            if move_eval["score_change"] < -0.3:
                # Format with color indication for errors
                score_color = "#F44336" if move_eval["score_change"] < -1.0 else "#FF9800"
                score_change_text = f" ({move_eval['score_change']:.2f})"
                
            self.best_move_label.config(
                text=f"Meilleur coup: {move_eval['best_move']}{score_change_text}"
            )
            
            # For error moves, add explanation
            if move_eval["classification"] in ["Erreur", "Grosse erreur"]:
                # Determine explanation text based on score change
                if abs(move_eval["score_change"]) > 2.0:
                    explanation = "Coup critique qui perd un avantage matériel significatif."
                elif abs(move_eval["score_change"]) > 1.0:
                    explanation = "Cette erreur donne un avantage important à l'adversaire."
                else:
                    explanation = "Ce coup manque une opportunité tactique."
                    
                # Check if we already have a valid explanation label
                try:
                    if hasattr(self, 'error_explanation_label') and self.error_explanation_label:
                        # Test if the widget is still valid
                        self.error_explanation_label.winfo_exists()
                        self.error_explanation_label.config(text=explanation)
                        # Ensure it's visible
                        self.error_explanation_label.pack(anchor="w", pady=(5, 0))
                    else:
                        # Create a new label since it doesn't exist
                        self.error_explanation_label = tk.Label(
                            self.best_move_label.master, 
                            text=explanation,
                            font=("Segoe UI", 9),
                            bg="white",
                            fg="#F44336",
                            wraplength=250
                        )
                        self.error_explanation_label.pack(anchor="w", pady=(5, 0))
                except (tk.TclError, AttributeError):
                    # Widget is invalid, create a new one
                    try:
                        self.error_explanation_label = tk.Label(
                            self.best_move_label.master, 
                            text=explanation,
                            font=("Segoe UI", 9),
                            bg="white",
                            fg="#F44336",
                            wraplength=250
                        )
                        self.error_explanation_label.pack(anchor="w", pady=(5, 0))
                    except Exception:
                        # If creating also fails, just skip the explanation
                        pass
            elif hasattr(self, 'error_explanation_label'):
                try:
                    # Check if widget still exists before hiding it
                    if self.error_explanation_label and self.error_explanation_label.winfo_exists():
                        self.error_explanation_label.pack_forget()
                except (tk.TclError, AttributeError):
                    # Widget is invalid, just set to None
                    self.error_explanation_label = None
        else:
            self.best_move_label.config(text="")
            if hasattr(self, 'error_explanation_label'):
                try:
                    # Check if widget still exists before hiding it
                    if self.error_explanation_label and self.error_explanation_label.winfo_exists():
                        self.error_explanation_label.pack_forget()
                except (tk.TclError, AttributeError):
                    # Widget is invalid, just set to None
                    self.error_explanation_label = None
    
    def toggle_error_mode(self, show_errors=None):
        """Toggle error highlighting mode on/off.
        
        Args:
            show_errors: Boolean to force a specific state, or None to toggle
        """
        if not hasattr(self, 'error_navigation') or not self.error_navigation:
            return
            
        # Get the toggle variable
        toggle_var = self.error_navigation.get("toggle_var")
        if not toggle_var:
            return
            
        # Set new state or toggle current state
        if show_errors is not None:
            toggle_var.set(show_errors)
        else:
            toggle_var.set(not toggle_var.get())
            
        # Update the switch appearance
        update_switch = self.error_navigation.get("update_switch")
        if update_switch:
            update_switch()
            
        # Store the current mode
        self.error_mode_active = toggle_var.get()
    
    def next_error(self):
        """Navigate to the next error."""
        if not self.error_mode_active:
            # Activate error mode first
            self.toggle_error_mode(True)
            
        # Trigger the next button
        if self.error_navigation and "next_button" in self.error_navigation:
            self.error_navigation["next_button"].invoke()
    
    def prev_error(self):
        """Navigate to the previous error."""
        if not self.error_mode_active:
            # Activate error mode first
            self.toggle_error_mode(True)
            
        # Trigger the previous button
        if self.error_navigation and "prev_button" in self.error_navigation:
            self.error_navigation["prev_button"].invoke()

    def _highlight_move_row(self, move_frame):
        """Met en évidence la ligne de coup sélectionnée."""
        set_card_state(move_frame, {'selected': True})
    
    def _unhighlight_move_row(self, move_frame):
        """Enlève la mise en évidence d'une ligne de coup."""
        set_card_state(move_frame, {'selected': False})
    
    def show_loading_dialog(self, moves_count):
        """
        Show a loading dialog during analysis.
        
        Args:
            moves_count: Total number of moves to analyze
            
        Returns:
            Tuple of (dialog_window, progress_variable)
        """
        # Create loading window
        loading_window = tk.Toplevel(self.parent)
        loading_window.title("Analyse en cours...")
        loading_window.geometry("300x150")
        loading_window.resizable(False, False)
        loading_window.configure(bg=config.COLORS["background"])
        loading_window.transient(self.parent)
        loading_window.grab_set()
        resource_loader.load_app_icon(loading_window)
        
        # Loading message
        loading_label = tk.Label(
            loading_window, 
            text="Analyse des coups en cours...", 
            font=font.Font(**config.FONTS["label"]),
            bg=config.COLORS["background"],
            fg=config.COLORS["primary_text"]
        )
        loading_label.pack(pady=(30, 10))
        
        # Progress bar
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            loading_window, 
            variable=progress_var, 
            maximum=moves_count,
            length=250
        )
        progress_bar.pack(pady=10, padx=20)
        
        return loading_window, progress_var
    
    def _deduce_uci_move_from_positions(self, prev_fen, current_fen):
        """Déduit le coup UCI joué en comparant deux positions FEN successives."""
        try:
            prev_board = chess.Board(prev_fen)
            current_board = chess.Board(current_fen)
            
            # Essayer chaque coup légal pour voir lequel produit la position actuelle
            for move in prev_board.legal_moves:
                test_board = chess.Board(prev_fen)
                test_board.push(move)
                
                # Comparer seulement la position des pièces
                if test_board.board_fen() == current_board.board_fen():
                    return move.uci()
                    
            return None
        except Exception:
            return None