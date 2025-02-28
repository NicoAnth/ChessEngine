"""
Game analysis visualization module.
Displays detailed analysis of chess games.
"""

import tkinter as tk
from tkinter import ttk, font
from src.utils import config

class GameAnalysisView:
    """Displays detailed game analysis in a separate window."""
    
    def __init__(self, parent, game_analyzer):
        """
        Initialize the game analysis view.
        
        Args:
            parent: Parent window
            game_analyzer: GameAnalyzer instance
        """
        self.parent = parent
        self.game_analyzer = game_analyzer
    
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
        
        # Create analysis window
        analysis_window = tk.Toplevel(self.parent)
        analysis_window.title("Bilan de Partie")
        analysis_window.geometry("900x700")
        analysis_window.configure(bg=config.COLORS["background"])
        
        # Create tabbed interface
        notebook = ttk.Notebook(analysis_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create fonts
        title_font = font.Font(family="Segoe UI", size=13, weight="bold")
        subheader_font = font.Font(family="Segoe UI", size=11, weight="bold")
        text_font = font.Font(family="Segoe UI", size=10)
        
        # Add summary tab
        self._create_summary_tab(notebook, move_evaluations, white_stats, black_stats,
                                title_font, subheader_font, text_font)
        
        # Add moves analysis tab
        self._create_moves_tab(notebook, move_evaluations, text_font)
    
    def _create_summary_tab(self, notebook, move_evaluations, white_stats, black_stats,
                           title_font, subheader_font, text_font):
        """Create the summary tab with player statistics."""
        summary_tab = ttk.Frame(notebook)
        notebook.add(summary_tab, text="Résumé")
        
        summary_frame = tk.Frame(summary_tab, bg=config.COLORS["background"], padx=20, pady=20)
        summary_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        tk.Label(summary_frame, 
                text="RÉSUMÉ DE LA PARTIE", 
                font=title_font, 
                bg=config.COLORS["background"],
                fg=config.COLORS["primary_text"],
                pady=10).pack(anchor="center")
        
        # Players statistics side by side
        players_frame = tk.Frame(summary_frame, bg=config.COLORS["background"])
        players_frame.pack(fill=tk.X, pady=20)
        
        # White player statistics
        self._create_player_stats_frame(players_frame, "BLANCS", white_stats, 
                                      subheader_font, text_font, side=tk.LEFT)
        
        # Black player statistics
        self._create_player_stats_frame(players_frame, "NOIRS", black_stats, 
                                      subheader_font, text_font, side=tk.RIGHT)
        
        # Game statistics section
        stats_frame = tk.Frame(summary_frame, bg=config.COLORS["background"], pady=10)
        stats_frame.pack(fill=tk.X)
        
        tk.Label(stats_frame, 
                text="STATISTIQUES DE LA PARTIE", 
                font=subheader_font, 
                bg=config.COLORS["background"], 
                fg=config.COLORS["primary_text"], 
                pady=5).pack(anchor="w", pady=(20, 10))
        
        stats_data_frame = tk.Frame(stats_frame, bg="white", padx=15, pady=15, bd=1, relief=tk.RIDGE)
        stats_data_frame.pack(fill=tk.X)
        
        # General statistics displayed in a grid
        total_moves = len(move_evaluations)
        white_moves = white_stats["total_moves"]
        black_moves = black_stats["total_moves"]
        
        stat_grid = tk.Frame(stats_data_frame, bg="white")
        stat_grid.pack(fill=tk.X)
        
        # Row 1
        tk.Label(stat_grid, text="Nombre total de coups:", font=text_font, bg="white", 
                fg=config.COLORS["secondary_text"]).grid(row=0, column=0, sticky="w", pady=3)
        tk.Label(stat_grid, text=f"{total_moves}", font=text_font, bg="white", 
                fg=config.COLORS["secondary_text"]).grid(row=0, column=1, sticky="w", padx=20)
        
        # Row 2
        tk.Label(stat_grid, text="Coups des blancs:", font=text_font, bg="white", 
                fg=config.COLORS["secondary_text"]).grid(row=1, column=0, sticky="w", pady=3)
        tk.Label(stat_grid, text=f"{white_moves}", font=text_font, bg="white", 
                fg=config.COLORS["secondary_text"]).grid(row=1, column=1, sticky="w", padx=20)
        
        # Row 3
        tk.Label(stat_grid, text="Coups des noirs:", font=text_font, bg="white", 
                fg=config.COLORS["secondary_text"]).grid(row=2, column=0, sticky="w", pady=3)
        tk.Label(stat_grid, text=f"{black_moves}", font=text_font, bg="white", 
                fg=config.COLORS["secondary_text"]).grid(row=2, column=1, sticky="w", padx=20)
    
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
                        start=90, extent=-(stats["accuracy"]*3.6), 
                        outline=arc_color, width=10, style=tk.ARC)
        
        canvas.create_text(accuracy_size//2, accuracy_size//2, 
                         text=f"{stats['accuracy']}%", 
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
    
    def _create_moves_tab(self, notebook, move_evaluations, text_font):
        """Create the detailed moves analysis tab."""
        moves_tab = ttk.Frame(notebook)
        notebook.add(moves_tab, text="Analyse des coups")
        
        # Create scrollable canvas
        moves_canvas = tk.Canvas(moves_tab, bg=config.COLORS["background"])
        scrollbar = ttk.Scrollbar(moves_tab, orient="vertical", command=moves_canvas.yview)
        scrollable_frame = ttk.Frame(moves_canvas)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: moves_canvas.configure(
                scrollregion=moves_canvas.bbox("all")
            )
        )
        
        moves_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        moves_canvas.configure(yscrollcommand=scrollbar.set)
        
        moves_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Header for moves table
        header_font = font.Font(family="Segoe UI", size=10, weight="bold")
        self._create_moves_header(scrollable_frame, header_font)
        
        # List all moves with their evaluations
        for i, eval in enumerate(move_evaluations):
            self._create_move_row(scrollable_frame, eval, i, text_font)
    
    def _create_moves_header(self, parent, header_font):
        """Create the header for the moves table."""
        moves_header = tk.Frame(parent, bg="#E0E0E0", padx=10, pady=10)
        moves_header.pack(fill=tk.X)
        
        # Column headers
        columns = [
            ("Coup", 10),
            ("Notation", 12),
            ("Évaluation", 12),
            ("Qualité", 12),
            ("Meilleur coup", 15),
            ("Impact", 10)
        ]
        
        for col_name, width in columns:
            tk.Label(moves_header, text=col_name, width=width, 
                   font=header_font, bg="#E0E0E0").pack(side=tk.LEFT)
    
    def _create_move_row(self, parent, eval, index, text_font):
        """Create a row for a single move in the moves table."""
        # Alternate row colors
        bg_color = "white" if index % 2 == 0 else "#F5F5F5"
        
        move_frame = tk.Frame(parent, bg=bg_color, padx=10, pady=8)
        move_frame.pack(fill=tk.X)
        
        # Format evaluation score
        formatted_score = f"+{abs(eval['score_after']):.2f}" if eval['score_after'] >= 0 else f"-{abs(eval['score_after']):.2f}"
        formatted_change = f"{eval['score_change']:+.2f}"
        
        # Quality color
        quality_color = self.game_analyzer.get_classification_color(eval["classification"])
        
        # Score change color
        score_color = self.game_analyzer.get_score_color(eval["score_change"])
        
        # Display move data
        columns = [
            (eval["move_text"], 10, None),
            (eval["san"], 12, None),
            (formatted_score, 12, None),
            (eval["classification"], 12, quality_color),
            (eval["best_move"] if eval["best_move"] else "-", 15, None),
            (formatted_change, 10, score_color)
        ]
        
        for text, width, color in columns:
            tk.Label(move_frame, text=text, width=width, 
                   font=text_font, bg=bg_color,
                   fg=color or config.COLORS["secondary_text"]).pack(side=tk.LEFT)
            
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