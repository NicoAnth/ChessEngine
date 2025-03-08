"""
Game analysis visualization module.
Displays detailed analysis of chess games.
"""

import tkinter as tk
from tkinter import ttk, font
from src.utils import config
from src.gui.moderntabs import ModernTabs
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as ticker
import numpy as np
import chess  # Added for chess position handling

# Add this function at the top of your file after your imports
def _bind_mousewheel_to_widgets(parent, on_mousewheel, on_linux_up, on_linux_down):
    """Recursively bind mousewheel events to all widgets."""
    # Bind mouse wheel events to the parent
    parent.bind("<MouseWheel>", on_mousewheel)
    parent.bind("<Button-4>", on_linux_up)
    parent.bind("<Button-5>", on_linux_down)
    
    # Recursively bind to all children
    for child in parent.winfo_children():
        _bind_mousewheel_to_widgets(child, on_mousewheel, on_linux_up, on_linux_down)

class MiniChessBoard(tk.Canvas):
    """A simple chess board canvas for displaying positions."""
    
    def __init__(self, parent, piece_images=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.configure(bg="white", highlightthickness=1, highlightbackground="#E0E0E0")
        self.square_size = 40  # Default square size
        
        # Import the resource_loader here
        from src.utils.resource_loader import load_piece_images
        
        # Load piece images directly at the correct size
        self.pieces = {}
        piece_types = ['p', 'n', 'b', 'r', 'q', 'k', 'P', 'N', 'B', 'R', 'Q', 'K']
        
        # Map chess piece symbols to image keys
        self.piece_name_map = {
            'p': 'black-pawn', 'n': 'black-knight', 'b': 'black-bishop', 
            'r': 'black-rook', 'q': 'black-queen', 'k': 'black-king',
            'P': 'white-pawn', 'N': 'white-knight', 'B': 'white-bishop', 
            'R': 'white-rook', 'Q': 'white-queen', 'K': 'white-king'
        }
        
        # Load the images at the appropriate size
        self.piece_images = load_piece_images(self.square_size)
        
        # Map the piece symbols to the loaded images
        for piece in piece_types:
            image_key = self.piece_name_map.get(piece)
            if image_key in self.piece_images:
                self.pieces[piece] = self.piece_images[image_key]
            else:
                self.pieces[piece] = None
        
        self.board = chess.Board()  # Initial position
        self.draw_board()
    
    def draw_board(self):
        """Draw the empty chess board."""
        self.delete("all")  # Clear canvas
        
        # Calculate canvas size based on square size
        board_size = self.square_size * 8
        self.config(width=board_size, height=board_size)
        
        # Draw squares
        for row in range(8):
            for col in range(8):
                # Calculate position
                x1 = col * self.square_size
                y1 = row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                
                # Determine square color (light or dark)
                is_light = (row + col) % 2 == 0
                fill_color = config.COLORS["light_square"] if is_light else config.COLORS["dark_square"]
                
                # Draw square
                self.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline="")
                
                # Add coordinates labels on the bottom and right edges
                if row == 7:
                    self.create_text(
                        x1 + self.square_size/2, 
                        y2 - 10, 
                        text=chr(col + 97),  # 'a' through 'h'
                        fill="#555555" if is_light else "#CCCCCC",
                        font=("Segoe UI", 8)
                    )
                if col == 7:
                    self.create_text(
                        x2 - 10, 
                        y1 + self.square_size/2, 
                        text=str(8 - row),  # '8' through '1'
                        fill="#555555" if is_light else "#CCCCCC",
                        font=("Segoe UI", 8)
                    )
    
    def draw_position(self, board=None):
        """Draw pieces on the board based on FEN position."""
        if board:
            self.board = board
        
        self.draw_board()  # Redraw empty board
        
        # Draw pieces according to current position
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if not piece:
                continue
                
            # Convert square index to coordinates
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)  # Invert row (chess uses 0=bottom, tkinter uses 0=top)
            
            # Calculate position
            x = col * self.square_size + self.square_size/2
            y = row * self.square_size + self.square_size/2
            
            # Get piece symbol
            piece_symbol = piece.symbol()
            
            if self.pieces[piece_symbol]:
                # Draw piece using image
                self.create_image(x, y, image=self.pieces[piece_symbol], tags="piece")
            else:
                # Draw text representation as fallback
                color = "white" if piece_symbol.isupper() else "black"
                fill_color = "#000000" if color == "white" else "#FFFFFF"
                self.create_text(
                    x, y, 
                    text=piece_symbol.upper(), 
                    fill=fill_color,
                    font=("Arial", int(self.square_size * 0.6), "bold"),
                    tags="piece"
                )
    
    def update_to_position(self, fen):
        """Update board to show the position from FEN."""
        try:
            self.board = chess.Board(fen)
            self.draw_position()
        except Exception as e:
            print(f"Error updating chess position: {e}")


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
        self.tabs.add_tab("Résumé", summary_frame)
        self.tabs.add_tab("Analyse des coups", moves_frame)
        
        # Add summary tab
        self._create_summary_tab_content(summary_frame, move_evaluations, white_stats, black_stats,
                                title_font, subheader_font, text_font)
        
        # Add moves analysis tab
        self._create_moves_tab_content(moves_frame, move_evaluations, text_font)
    
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

    def _create_accuracy_chart(self, parent_frame, accuracy, is_white=True):
        """Create a circular accuracy indicator with modern design.
        
        Args:
            parent_frame: The frame to place the chart in
            accuracy: A value between 0 and 100
            is_white: Boolean indicating if this is for white pieces
        """
        # Size of the chart
        size = 120
        # Frame to contain the chart
        chart_frame = tk.Frame(parent_frame, bg="white")
        chart_frame.pack(pady=(0, 15))
        
        # Create canvas for the circular chart
        canvas = tk.Canvas(
            chart_frame, 
            width=size, 
            height=size, 
            bg="white", 
            highlightthickness=0
        )
        canvas.pack()
        
        # Chart parameters
        center_x, center_y = size/2, size/2
        radius = size/2 - 10  # Smaller than full canvas to leave margin
        thickness = 8  # Thickness of the circle
        start_angle = 90  # Start from top (90 degrees in tkinter arc)
        
        # Calculate the extent of the arc (how much of the circle to fill)
        extent = (accuracy / 100) * 360
        
        # Draw background circle (unfilled portion)
        bg_color = "#F0F0F0"  # Light gray background
        canvas.create_oval(
            center_x - radius, 
            center_y - radius, 
            center_x + radius, 
            center_y + radius, 
            outline=bg_color, 
            width=thickness
        )
        
        # Choose color based on accuracy for filled portion
        if accuracy < 50:
            fill_color = "#FF6B6B"  # Red for low accuracy
        elif accuracy < 75:
            fill_color = "#FFD166"  # Yellow for medium accuracy
        else:
            fill_color = "#06D6A0"  # Green for high accuracy
        
        # Adjust colors if black player
        if not is_white:
            # Use slightly different colors for black to distinguish
            if accuracy < 50:
                fill_color = "#E84855"  # Slightly different red
            elif accuracy < 75:
                fill_color = "#EFCA08"  # Slightly different yellow
            else:
                fill_color = "#0CB69A"  # Slightly different green
        
        # Draw the filled progress arc
        canvas.create_arc(
            center_x - radius, 
            center_y - radius, 
            center_x + radius, 
            center_y + radius,
            start=start_angle,
            extent=-extent,  # Negative for clockwise direction
            outline=fill_color,
            style="arc",
            width=thickness
        )
        
        # Display accuracy percentage in the middle
        font_size = 22  # Larger font for the percentage
        canvas.create_text(
            center_x,
            center_y - 10,
            text=f"{int(accuracy)}%",
            font=("Segoe UI", font_size, "bold"),
            fill="#333333"
        )
        
        # Add "accuracy" label below the percentage
        canvas.create_text(
            center_x,
            center_y + 15,
            text="précision",
            font=("Segoe UI", 10),
            fill="#666666"
        )
    
    def _create_summary_tab_content(self, summary_frame, move_evaluations, white_stats, black_stats,
                        title_font, subheader_font, text_font):
        """Create the summary tab with player statistics and modern design."""
        
        # Create scrollable canvas with modern styling
        canvas_frame = tk.Frame(summary_frame, bg=config.COLORS["background"])
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        summary_canvas = tk.Canvas(
            canvas_frame, 
            bg=config.COLORS["background"],
            highlightthickness=0,  # Remove border
            bd=0  # Remove border
        )
        
        # Modern scrollbar
        scrollbar = tk.Scrollbar(
            canvas_frame, 
            orient="vertical", 
            command=summary_canvas.yview,
            width=10,  # Thinner scrollbar
            bd=0,  # No border
            highlightthickness=0,  # No highlight
            troughcolor="#EAEAEA",  # Light gray trough
            bg=config.COLORS["background"],
            activebackground=config.COLORS["selected_square"]  # Blue when active
        )
        
        # Inner content frame
        content_frame = tk.Frame(summary_canvas, bg=config.COLORS["background"], padx=15, pady=5)

        # Configure scrolling
        content_frame.bind(
            "<Configure>",
            lambda e: summary_canvas.configure(
                scrollregion=summary_canvas.bbox("all")
            )
        )

        # Add mouse wheel scrolling support
        def _on_mousewheel(event):
            # For Windows
            summary_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def _on_linux_scroll_up(event):
            summary_canvas.yview_scroll(-1, "units")
            
        def _on_linux_scroll_down(event):
            summary_canvas.yview_scroll(1, "units")

        # Bind mouse wheel events
        summary_canvas.bind("<MouseWheel>", _on_mousewheel)
        content_frame.bind("<MouseWheel>", _on_mousewheel)
        summary_canvas.bind("<Button-4>", _on_linux_scroll_up)
        summary_canvas.bind("<Button-5>", _on_linux_scroll_down)
        content_frame.bind("<Button-4>", _on_linux_scroll_up)
        content_frame.bind("<Button-5>", _on_linux_scroll_down)

        # Ensure canvas can receive focus for mouse wheel events
        summary_canvas.bind("<Enter>", lambda event: summary_canvas.focus_set())
        
        # Add binding for canvas resize
        def resize_canvas(event):
            # Update the width of the scrollable window to match canvas width
            canvas_width = event.width
            summary_canvas.itemconfig(window_id, width=canvas_width)
            
        summary_canvas.bind("<Configure>", resize_canvas)
        window_id = summary_canvas.create_window((0, 0), window=content_frame, anchor="nw")
        summary_canvas.configure(yscrollcommand=scrollbar.set)

        # Pack the canvas and scrollbar in modern way
        summary_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Title with modern styling
        title_container = tk.Frame(content_frame, bg=config.COLORS["background"])
        title_container.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            title_container,
            text="RÉSUMÉ DE LA PARTIE",
            font=title_font,
            bg=config.COLORS["background"],
            fg=config.COLORS["primary_text"],
            pady=5
        ).pack(anchor="center")
        
        # Modern separator
        separator = tk.Frame(title_container, height=2, bg=config.COLORS["selected_square"])
        separator.pack(fill=tk.X, padx=50)
        
        # Players statistics section - with modern card design
        players_frame = tk.Frame(content_frame, bg=config.COLORS["background"])
        players_frame.pack(fill=tk.X, expand=False, pady=15)
        
        # Create equal-width columns for player stats
        players_frame.columnconfigure(0, weight=1)
        players_frame.columnconfigure(1, weight=1)
        
        # White player statistics - with card design
        white_card = tk.Frame(
            players_frame, 
            bg="white",
            bd=0,
            highlightthickness=1,
            highlightbackground="#E0E0E0",
            padx=15,
            pady=15
        )
        white_card.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        # Add subtle shadow effect
        white_header_frame = tk.Frame(white_card, bg="white")
        white_header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # White icon and title in same row
        white_icon = tk.Label(
            white_header_frame,
            text="♔",  # Chess king symbol
            font=("Segoe UI", 20),
            bg="white",
            fg="#333333"
        )
        white_icon.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(
            white_header_frame,
            text="BLANCS",
            font=subheader_font,
            bg="white",
            fg="#333333"
        ).pack(side=tk.LEFT, anchor="w")
        
        # Add accuracy chart for white player
        white_accuracy = white_stats.get("accuracy", 75)  # Default 75% if not provided
        self._create_accuracy_chart(white_card, white_accuracy, is_white=True)
        
        # White stats content
        self._create_modern_player_stats(white_card, white_stats, text_font)
        
        # Black player statistics - with card design
        black_card = tk.Frame(
            players_frame, 
            bg="white",
            bd=0,
            highlightthickness=1,
            highlightbackground="#E0E0E0",
            padx=15,
            pady=15
        )
        black_card.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        # Black header
        black_header_frame = tk.Frame(black_card, bg="white")
        black_header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Black icon and title in same row
        black_icon = tk.Label(
            black_header_frame,
            text="♚",  # Chess king symbol
            font=("Segoe UI", 20),
            bg="white",
            fg="#333333"
        )
        black_icon.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(
            black_header_frame,
            text="NOIRS",
            font=subheader_font,
            bg="white",
            fg="#333333"
        ).pack(side=tk.LEFT, anchor="w")
        
        # Add accuracy chart for black player
        black_accuracy = black_stats.get("accuracy", 65)  # Default 65% if not provided
        self._create_accuracy_chart(black_card, black_accuracy, is_white=False)
        
        # Black stats content
        self._create_modern_player_stats(black_card, black_stats, text_font)
        
        # Game evolution chart with card design
        chart_container = tk.Frame(
            content_frame, 
            bg="white",
            bd=0,
            highlightthickness=1,
            highlightbackground="#E0E0E0",
            padx=15,
            pady=15
        )
        chart_container.pack(fill=tk.BOTH, expand=True, pady=(20, 25))
        
        # Add chart to the container
        self._create_game_evolution_chart(chart_container, move_evaluations, title_font, subheader_font)
        
        # Game statistics section - card design
        game_stats_card = tk.Frame(
            content_frame, 
            bg="white",
            bd=0,
            highlightthickness=1,
            highlightbackground="#E0E0E0",
            padx=20,
            pady=20
        )
        game_stats_card.pack(fill=tk.X, pady=(0, 20))
        
        # Stats header with icon
        stats_header = tk.Frame(game_stats_card, bg="white")
        stats_header.pack(fill=tk.X, pady=(0, 15))
        
        stats_icon = tk.Label(
            stats_header,
            text="📊",  # Chart icon
            font=("Segoe UI", 16),
            bg="white",
            fg="#333333"
        )
        stats_icon.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(
            stats_header,
            text="STATISTIQUES DE LA PARTIE",
            font=subheader_font,
            bg="white",
            fg="#333333"
        ).pack(side=tk.LEFT, anchor="w")
        
        # Modern separator for stats
        stats_separator = tk.Frame(game_stats_card, height=1, bg="#E0E0E0")
        stats_separator.pack(fill=tk.X, pady=(0, 15))
        
        # General statistics displayed in a grid with modern spacing
        total_moves = len(move_evaluations)
        white_moves = white_stats["total_moves"]
        black_moves = black_stats["total_moves"]

        self._create_count_statistics(game_stats_card, total_moves, white_moves, black_moves, subheader_font, text_font)

        stat_grid = tk.Frame(game_stats_card, bg="white")
        stat_grid.pack(fill=tk.X)
        
        # Make columns equal width
        stat_grid.columnconfigure(0, weight=1)
        stat_grid.columnconfigure(1, weight=1)
        
        # Stats with modern styling
        self._create_stat_row(stat_grid, "Nombre total de coups:", f"{total_moves}", 0, text_font)
        self._create_stat_row(stat_grid, "Coups des blancs:", f"{white_moves}", 1, text_font)
        self._create_stat_row(stat_grid, "Coups des noirs:", f"{black_moves}", 2, text_font)
        
        # Recursively bind mousewheel to all widgets
        self._bind_mousewheel_to_widgets(content_frame, _on_mousewheel, _on_linux_scroll_up, _on_linux_scroll_down)

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
        parent.bind("<MouseWheel>", windows_callback)
        parent.bind("<Button-4>", linux_up_callback)
        parent.bind("<Button-5>", linux_down_callback)
        
        for child in parent.winfo_children():
            self._bind_mousewheel_to_widgets(child, windows_callback, linux_up_callback, linux_down_callback)
    
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
    
    def _create_moves_tab_content(self, moves_frame_parent, move_evaluations, text_font):
        """Create the detailed moves analysis tab content with a mini-board."""
        # Create paned window to split the tab
        paned_window = ttk.PanedWindow(moves_frame_parent, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Create frame for move list (left side)
        moves_frame = tk.Frame(paned_window, bg=config.COLORS["background"])
        
        # Create frame for mini-board (right side)
        board_frame = tk.Frame(paned_window, bg=config.COLORS["background"], padx=10, pady=10)
        
        # Add both frames to the paned window
        paned_window.add(moves_frame, weight=1)
        paned_window.add(board_frame, weight=1)
        
        # Create scrollable canvas for moves list
        canvas_frame = tk.Frame(moves_frame, bg=config.COLORS["background"])
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        moves_canvas = tk.Canvas(
            canvas_frame, 
            bg=config.COLORS["background"],
            highlightthickness=0,
            bd=0
        )
        
        # Modern scrollbar
        scrollbar = tk.Scrollbar(
            canvas_frame, 
            orient="vertical", 
            command=moves_canvas.yview,
            width=10,
            bd=0,
            highlightthickness=0,
            troughcolor="#EAEAEA",
            bg=config.COLORS["background"],
            activebackground=config.COLORS["selected_square"]
        )
        
        # Inner content frame
        content_frame = tk.Frame(moves_canvas, bg=config.COLORS["background"], padx=15, pady=5)
        
        # Add mouse wheel scrolling support with boundary checking
        def _on_mousewheel(event):
            # Check if we can scroll in the requested direction
            if (event.delta > 0 and moves_canvas.yview()[0] <= 0) or \
            (event.delta < 0 and moves_canvas.yview()[1] >= 1):
                return  # Prevent scrolling beyond boundaries
            # For Windows
            moves_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _on_linux_scroll_up(event):
            # Check if at top boundary
            if moves_canvas.yview()[0] <= 0:
                return  # Prevent scrolling up when already at top
            moves_canvas.yview_scroll(-1, "units")
            
        def _on_linux_scroll_down(event):
            # Check if at bottom boundary
            if moves_canvas.yview()[1] >= 1:
                return  # Prevent scrolling down when already at bottom
            moves_canvas.yview_scroll(1, "units")
        
        # Update scroll region function
        def update_scrollregion(event=None):
            # Get the total height of the content
            content_height = content_frame.winfo_reqheight()
            canvas_height = moves_canvas.winfo_height()
            
            # Set minimum scrollregion height to match canvas height
            height = max(content_height, canvas_height)
            
            # Update the scrollregion
            moves_canvas.configure(scrollregion=(0, 0, content_frame.winfo_reqwidth(), height))
            
            # Disable scrollbar if content fits entirely within the canvas
            if content_height <= canvas_height:
                scrollbar.pack_forget()
            else:
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure content frame to update scroll region
        content_frame.bind("<Configure>", update_scrollregion)
        
        # Add binding for canvas resize
        def resize_canvas(event):
            # Update the width of the scrollable window to match canvas width
            canvas_width = event.width
            moves_canvas.itemconfig(window_id, width=canvas_width)
            
            # Update the scroll region when canvas is resized
            update_scrollregion()
        
        moves_canvas.bind("<Configure>", resize_canvas)
        
        # Bind mouse wheel events
        moves_canvas.bind("<MouseWheel>", _on_mousewheel)
        content_frame.bind("<MouseWheel>", _on_mousewheel)
        moves_canvas.bind("<Button-4>", _on_linux_scroll_up)
        moves_canvas.bind("<Button-5>", _on_linux_scroll_down)
        content_frame.bind("<Button-4>", _on_linux_scroll_up)
        content_frame.bind("<Button-5>", _on_linux_scroll_down)
        
        # Ensure canvas can receive focus for mouse wheel events
        moves_canvas.bind("<Enter>", lambda event: moves_canvas.focus_set())
        
        window_id = moves_canvas.create_window((0, 0), window=content_frame, anchor="nw")
        moves_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar in modern way
        moves_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Header for moves table
        header_font = font.Font(family="Segoe UI", size=10, weight="bold")
        self._create_moves_header(content_frame, header_font)
        
        # List all moves with their evaluations
        for i, eval in enumerate(move_evaluations):
            self._create_move_row(content_frame, eval, i, text_font)
        
        # Create mini-board in the right frame
        self._create_mini_board(board_frame, move_evaluations)
        
        # Recursively bind mousewheel to all widgets
        self._bind_mousewheel_to_widgets(content_frame, _on_mousewheel, _on_linux_scroll_up, _on_linux_scroll_down)
        
        # Initial update of the scroll region
        content_frame.update_idletasks()  # Ensure content frame has been laid out
        update_scrollregion()

    def _create_mini_board(self, parent_frame, move_evaluations):
        """Create a mini chess board panel."""
        # Title for the board section
        title_label = tk.Label(
            parent_frame,
            text="Position après le coup",
            font=("Segoe UI", 12, "bold"),
            bg=config.COLORS["background"],
            fg=config.COLORS["primary_text"]
        )
        title_label.pack(anchor="w", pady=(0, 10))
        
        # Create mini-board
        board_container = tk.Frame(
            parent_frame,
            bg="white",
            padx=10,
            pady=10,
            highlightthickness=1,
            highlightbackground="#E0E0E0"
        )
        board_container.pack(fill=tk.BOTH, expand=True)
        
        # Create the mini-board canvas with piece images
        self.mini_board = MiniChessBoard(board_container, piece_images=self.piece_images)
        self.mini_board.pack(anchor="center", pady=10)
        
        # Add move information panel below the board
        info_frame = tk.Frame(board_container, bg="white")
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Move number and san display
        self.move_info_label = tk.Label(
            info_frame,
            text="Sélectionnez un coup pour voir la position",
            font=("Segoe UI", 11),
            bg="white",
            fg=config.COLORS["primary_text"]
        )
        self.move_info_label.pack(anchor="w")
        
        # Evaluation display
        self.eval_info_label = tk.Label(
            info_frame,
            text="",
            font=("Segoe UI", 10),
            bg="white",
            fg=config.COLORS["secondary_text"]
        )
        self.eval_info_label.pack(anchor="w", pady=(5, 0))
        
        # Best move info (if applicable)
        self.best_move_label = tk.Label(
            info_frame,
            text="",
            font=("Segoe UI", 10),
            bg="white",
            fg=config.COLORS["secondary_text"]
        )
        self.best_move_label.pack(anchor="w", pady=(5, 0))
        
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
        
        # Display move data
        columns = [
            (eval["san"], 12, None),
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
            self._unhighlight_move_row(self.selected_move_row)
            
        # Highlight the selected row
        self._highlight_move_row(move_frame)
        self.selected_move_row = move_frame
        
        # If position_history is missing but we have a mini-board,
        # try to generate the position from the move data
        if not self.position_history and self.mini_board and "uci" in move_eval:
            try:
                # Create a board and play moves up to this point
                board = chess.Board()
                
                # Find all previous moves up to this one
                for i in range(move_index + 1):
                    # Get the move from move_evaluations
                    if i < len(self.game_analyzer.last_analysis_moves):
                        board.push(self.game_analyzer.last_analysis_moves[i])
                
                # Update the board directly
                self.mini_board.board = board
                self.mini_board.draw_position()
                
                # Update move information
                move_number = (move_index // 2) + 1
                is_white = move_index % 2 == 0
                move_prefix = f"{move_number}." if is_white else f"{move_number}..."
                
                self.move_info_label.config(
                    text=f"{move_prefix} {move_eval['san']}",
                    font=("Segoe UI", 11, "bold")
                )
                
                # Update evaluation info
                self._update_evaluation_labels(move_eval)
                
                return
            except Exception as e:
                print(f"Error reconstructing position: {e}")
        
        # Update the mini-board if position history exists
        if self.position_history and self.mini_board:
            if move_index < len(self.position_history):
                # Update the board position
                self.mini_board.update_to_position(self.position_history[move_index])
                
                # Update move information
                move_number = (move_index // 2) + 1
                is_white = move_index % 2 == 0
                move_prefix = f"{move_number}." if is_white else f"{move_number}..."
                
                self.move_info_label.config(
                    text=f"{move_prefix} {move_eval['san']}",
                    font=("Segoe UI", 11, "bold")
                )
                
                # Update evaluation info
                self._update_evaluation_labels(move_eval)
            else:
                # If position not available
                self.mini_board.draw_board()  # Just show empty board
                self.move_info_label.config(text="Position non disponible")
                self.eval_info_label.config(text="")
                self.best_move_label.config(text="")

    def _update_evaluation_labels(self, move_eval):
        """Update evaluation labels with move data."""
        # Update evaluation info
        score_after = move_eval["score_after"]
        formatted_score = f"+{abs(score_after):.2f}" if score_after >= 0 else f"-{abs(score_after)::.2f}"
        color_advantage = "Blancs" if score_after >= 0 else "Noirs"
        
        self.eval_info_label.config(
            text=f"Évaluation: {formatted_score} (avantage {color_advantage})"
        )
        
        # Show best move if there was a better one
        if move_eval["best_move"] and move_eval["best_move"] != move_eval["san"]:
            self.best_move_label.config(
                text=f"Meilleur coup: {move_eval['best_move']}"
            )
        else:
            self.best_move_label.config(text="")
    
    def _highlight_move_row(self, move_frame):
        """Highlight the selected move row."""
        highlight_bg = config.COLORS.get("highlight_background", "#E3F2FD")  # Light blue highlight
        highlight_fg = config.COLORS.get("highlight_text", config.COLORS["primary_text"])
        
        # Highlight frame and all labels
        move_frame.configure(bg=highlight_bg)
        for label in move_frame.labels:
            label.configure(bg=highlight_bg)
            # Keep special colors (like classification color) if they exist
            if label.cget("fg") == config.COLORS["secondary_text"]:
                label.configure(fg=highlight_fg)
    
    def _unhighlight_move_row(self, move_frame):
        """Remove highlighting from a move row."""
        # Get original background color based on even/odd row
        original_bg = "white" if move_frame.move_index % 2 == 0 else "#F5F5F5"
        
        # Restore original colors
        move_frame.configure(bg=original_bg)
        for label in move_frame.labels:
            label.configure(bg=original_bg)
            # Restore original text color if it was changed
            if label.cget("fg") == config.COLORS.get("highlight_text", config.COLORS["primary_text"]):
                label.configure(fg=config.COLORS["secondary_text"])
    
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

    def _create_game_evolution_chart(self, summary_frame, move_evaluations, title_font, subheader_font):
        """Create a modern chart showing the evolution of the game score."""
        
        # Chart title frame
        chart_frame = tk.Frame(summary_frame, bg=config.COLORS["background"])
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Chart title
        tk.Label(chart_frame,
            text="ÉVOLUTION DE LA PARTIE",
            font=subheader_font,
            bg=config.COLORS["background"],
            fg=config.COLORS["primary_text"],
            pady=5).pack(anchor="w", pady=(10, 15))
        
        # Prepare data for the chart
        scores = []
        
        for eval in move_evaluations:
            scores.append(eval["score_after"])
        
        # Set up figure with modern aesthetics
        plt.style.use('seaborn-v0_8-whitegrid')  # Clean base style
        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor('#F8F9FA')  # Light background color
        ax.set_facecolor('#F8F9FA')
        
        # Define modern color scheme
        white_advantage_color = '#4285F4'  # Google blue - matches blue accents
        black_advantage_color = '#5F6368'  # Google gray - modern neutral
        zero_line_color = '#DADCE0'        # Light gray for the neutral line
        
        # Create gradient line color based on advantage
        advantage_colors = []
        for score in scores:
            if score >= 0:
                # White advantage (blue)
                advantage_colors.append(white_advantage_color)
            else:
                # Black advantage (gray)
                advantage_colors.append(black_advantage_color)
        
        # Plot line segments with appropriate colors
        for i in range(1, len(scores)):
            if (scores[i-1] >= 0 and scores[i] >= 0) or (scores[i-1] <= 0 and scores[i] <= 0):
                # Same advantage side, use consistent color
                color = white_advantage_color if scores[i] >= 0 else black_advantage_color
                ax.plot([i-1, i], [scores[i-1], scores[i]], color=color, linewidth=2.5)
            else:
                # Crossing the zero line, use both colors
                # Find the intersection point with the zero line
                t = -scores[i-1] / (scores[i] - scores[i-1])
                zero_cross = i-1 + t
                
                # Draw first segment
                color1 = white_advantage_color if scores[i-1] >= 0 else black_advantage_color
                ax.plot([i-1, zero_cross], [scores[i-1], 0], color=color1, linewidth=2.5)
                
                # Draw second segment
                color2 = white_advantage_color if scores[i] >= 0 else black_advantage_color
                ax.plot([zero_cross, i], [0, scores[i]], color=color2, linewidth=2.5)
        
        # Add a horizontal line at score=0 (equal position)
        ax.axhline(y=0, color=zero_line_color, linestyle='-', linewidth=1.5)
        
        # Set x-axis properties
        x_ticks = range(0, len(scores), max(1, len(scores) // 10))
        ax.set_xticks(x_ticks)
        ax.set_xlim(-0.5, len(scores) - 0.5)
        
        # Modern font for axis labels
        font_properties = {
            'family': 'Segoe UI', 
            'weight': 'normal',
            'size': 10
        }
        
        # Set y-axis formatter to show +/- for advantage
        def format_func(value, pos):
            if abs(value) < 0.05:  # Almost zero
                return "0"
            return f"+{value:.1f}" if value > 0 else f"{value:.1f}"
        
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_func))
        
        # Set labels with modern typography
        ax.set_xlabel('Coups', fontdict=font_properties)
        ax.set_ylabel('Avantage', fontdict=font_properties)
        
        # Custom grid
        ax.grid(True, axis='y', linestyle='-', alpha=0.15, color='#9AA0A6')
        ax.grid(False, axis='x')  # Remove x grid for cleaner look
        
        # Remove spines for modern look
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        
        # Lighten remaining spines
        for spine in ['bottom', 'left']:
            ax.spines[spine].set_color('#DADCE0')
            ax.spines[spine].set_linewidth(0.5)
        
        # Adjust ticks
        ax.tick_params(axis='both', colors='#5F6368', labelsize=9)
        
        # Add subtle advantage regions
        ax.axhspan(0, max(scores) + 0.5, alpha=0.05, color=white_advantage_color)
        ax.axhspan(min(scores) - 0.5, 0, alpha=0.05, color=black_advantage_color)
        
        # Add interesting points (strong advantage changes)
        significant_changes = []
        threshold = 0.5
        for i in range(1, len(scores)):
            if abs(scores[i] - scores[i-1]) > threshold:
                significant_changes.append(i)
        
        # Highlight at most 5 significant changes to avoid clutter
        if len(significant_changes) > 5:
            # Sort by magnitude of change and keep top 5
            significant_changes = sorted(range(1, len(scores)), 
                                        key=lambda i: abs(scores[i] - scores[i-1]), 
                                        reverse=True)[:5]
        
        for i in significant_changes:
            ax.plot(i, scores[i], 'o', markersize=5, 
                    color=white_advantage_color if scores[i] >= 0 else black_advantage_color,
                    markeredgecolor='white', markeredgewidth=1)
        
        # Adjust layout
        fig.tight_layout()
        
        # Create matplotlib canvas widget
        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create modern legend/explanation
        explanation_frame = tk.Frame(chart_frame, bg=config.COLORS["background"])
        explanation_frame.pack(fill=tk.X, pady=(8, 0))
        
        # Add color indicators for the legend
        white_indicator = tk.Frame(explanation_frame, width=12, height=12, bg=white_advantage_color)
        white_indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        white_text = tk.Label(
            explanation_frame,
            text="Avantage aux blancs",
            font=('Segoe UI', 9),
            bg=config.COLORS["background"],
            fg=config.COLORS["secondary_text"]
        )
        white_text.pack(side=tk.LEFT, padx=(0, 15))
        
        black_indicator = tk.Frame(explanation_frame, width=12, height=12, bg=black_advantage_color)
        black_indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        black_text = tk.Label(
            explanation_frame,
            text="Avantage aux noirs",
            font=('Segoe UI', 9),
            bg=config.COLORS["background"],
            fg=config.COLORS["secondary_text"]
        )
        black_text.pack(side=tk.LEFT)
        
        return chart_frame

    def _create_enhanced_move_quality_display(self, parent_frame, stats, text_font):
        """Create a streamlined display of move quality statistics."""
        # Add key metrics in highlighted boxes first
        key_stats_frame = tk.Frame(parent_frame, bg="white")
        key_stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Format key metrics - add Best Move % and Critical Accuracy if available
        best_move_pct = stats.get("best_move_percentage", 0)
        accuracy = stats.get("accuracy", 0)  # Already shown in circle but include for completeness
        critical_accuracy = stats.get("critical_accuracy", 0)
        
        # Create a row with 2-3 key metrics in boxes
        key_stats_frame.columnconfigure(0, weight=1)
        key_stats_frame.columnconfigure(1, weight=1)
        if "critical_accuracy" in stats:
            key_stats_frame.columnconfigure(2, weight=1)
        
        # Create metric box for Best Move %
        self._create_metric_box(
            key_stats_frame, 
            "Meilleurs coups", 
            f"{best_move_pct}%", 
            0,
            "#4285F4"  # Blue 
        )
        
        # Create metric box for Accuracy (if you want to include it alongside the circle)
        self._create_metric_box(
            key_stats_frame, 
            "Précision", 
            f"{accuracy}%", 
            1,
            "#34A853"  # Green
        )
        
        # Create metric box for Critical Accuracy if available
        if "critical_accuracy" in stats:
            self._create_metric_box(
                key_stats_frame, 
                "Précision critique", 
                f"{critical_accuracy}%", 
                2,
                "#FBBC05"  # Yellow/amber
            )
        
        # Get counts and calculate percentages
        total_moves = stats["total_moves"]
        counts = stats.get("counts", {})
        
        # Skip if no counts data
        if not counts:
            return
        
        # Container for distribution
        dist_frame = tk.Frame(parent_frame, bg="white")
        dist_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Rest of the method remains the same...
        # ... (existing move quality bars code)
        
        # Sort classifications in a logical order from best to worst
        ordered_classifications = [
            "Excellent", "Bon coup", "Imprécision", "Erreur", "Grosse erreur"
        ]
        
        # Filter to only include classifications that exist in the data
        classifications = [cls for cls in ordered_classifications if cls in counts]
        
        # Create quality bars
        for idx, cls in enumerate(classifications):
            count = counts.get(cls, 0)
            percentage = round((count / total_moves * 100)) if total_moves > 0 else 0
            
            # Classification row
            cls_frame = tk.Frame(dist_frame, bg="white")
            cls_frame.pack(fill=tk.X, pady=4)
            
            # Get color for this classification
            cls_color = self.game_analyzer.get_classification_color(cls)
            
            # Color indicator
            color_indicator = tk.Frame(cls_frame, width=6, height=20, bg=cls_color)
            color_indicator.pack(side=tk.LEFT, padx=(0, 10))
            
            # Label for classification name (with consistent width)
            tk.Label(
                cls_frame, 
                text=cls, 
                width=12, 
                anchor="w", 
                font=text_font,
                bg="white", 
                fg="#333333"  # Darker text for better readability
            ).pack(side=tk.LEFT)
            
            # Progress bar frame
            bar_container = tk.Frame(cls_frame, bg="#F0F0F0", height=20, width=150)
            bar_container.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            bar_container.pack_propagate(False)
            
            if percentage > 0:
                # Color bar showing percentage
                bar = tk.Frame(bar_container, bg=cls_color, height=20)
                bar.place(relx=0, rely=0, relwidth=percentage/100, relheight=1.0)
                
                # Add percentage text inside the bar if wide enough
                if percentage >= 18:
                    tk.Label(
                        bar,
                        text=f"{percentage}%",
                        font=("Segoe UI", 9),
                        bg=cls_color,
                        fg="white"
                    ).place(relx=0.5, rely=0.5, anchor="center")
                else:
                    # Otherwise place it after the bar
                    tk.Label(
                        cls_frame,
                        text=f"{percentage}%",
                        font=("Segoe UI", 9),
                        bg="white",
                        fg="#333333"
                    ).pack(side=tk.LEFT, padx=(5, 0))
            
            # Count value
            tk.Label(
                cls_frame,
                text=f"({count})",
                font=text_font,
                bg="white",
                fg="#555555"
            ).pack(side=tk.RIGHT, padx=(0, 5))

    def _create_metric_box(self, parent, label, value, column, color):
        """Create a highlighted metric box for key statistics."""
        metric_box = tk.Frame(
            parent,
            bg="white",
            highlightthickness=2,
            highlightbackground=color,
            padx=10,
            pady=10
        )
        metric_box.grid(row=0, column=column, sticky="ew", padx=5, pady=5)
        
        # Value (large, bold)
        tk.Label(
            metric_box,
            text=value,
            font=("Segoe UI", 18, "bold"),
            bg="white",
            fg=color
        ).pack(anchor="center")
        
        # Label (smaller below)
        tk.Label(
            metric_box,
            text=label,
            font=("Segoe UI", 9),
            bg="white",
            fg="#555555"
        ).pack(anchor="center", pady=(2, 0))
