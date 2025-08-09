"""
Game analysis visualization module.
Displays detailed analysis of chess games.
"""

import tkinter as tk
from tkinter import ttk, font
import math
import chess
from src.utils import resource_loader
from src.utils import config
from src.gui.moderntabs import ModernTabs
from src.gui.analysis.mini_board import MiniChessBoard
from src.gui.analysis.summary_tab import _create_summary_tab_content
from src.gui.analysis.difficulty_tab import _create_difficulty_tab_content
from src.gui.analysis.moves_tab import _create_moves_tab_content
from src.gui.analysis.utils.style_utils import set_card_state
from src.gui.player_banner import PlayerBanner  # Import the PlayerBanner class
from src.gui.evaluation_bar import EvaluationBar  # Import the EvaluationBar class
from src.user.profile import GameAnalysis  # Correction de l'importation de GameAnalysis


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

        # Référence à la bannière d'ouverture
        self.opening_label = None

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
    
    def show_analysis(self, game_analysis):
        """
        Display game analysis results.

        Args:
            game_analysis: GameAnalysis object or dictionary containing all analysis data.

        Returns:
            The created tk.Toplevel window instance, or None if creation fails.
        """
        # Normalize analysis data
        if isinstance(game_analysis, dict):
            move_evaluations = game_analysis.get("move_evaluations", [])
            white_stats = game_analysis.get("white_stats", {})
            black_stats = game_analysis.get("black_stats", {})
            position_history = game_analysis.get("position_history", [])
        else:
            move_evaluations = game_analysis.move_evaluations
            white_stats = game_analysis.white_stats
            black_stats = game_analysis.black_stats
            position_history = game_analysis.position_history

        self.analysis_results = game_analysis

        # Ensure position history
        self.position_history = position_history or self._generate_position_history(move_evaluations)

        # Create window
        analysis_window = tk.Toplevel(self.parent)
        analysis_window.title("Bilan de Partie")
        analysis_window.geometry("1400x1000")
        analysis_window.resizable(True, True)
        analysis_window.configure(bg=config.COLORS["background"])
        resource_loader.load_app_icon(analysis_window)

        # Fonts
        title_font = font.Font(**config.FONTS["title"])
        subheader_font = font.Font(**config.FONTS["analysis_subheader"])
        text_font = font.Font(**config.FONTS["analysis_text"])

        # Tabs
        tab_container = ModernTabs(
            analysis_window,
            tab_bg_color=config.COLORS["background"],
            tab_text_color=config.COLORS["primary_text"],
            tab_active_bg=config.COLORS["selected_square"],
            tab_active_text_color="white",
            tab_font=font.Font(**config.FONTS["button"]) 
        )
        tab_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        summary_frame = tk.Frame(tab_container.content_frame, bg=config.COLORS["background"])
        moves_frame = tk.Frame(tab_container.content_frame, bg=config.COLORS["background"])
        stats_frame = tk.Frame(tab_container.content_frame, bg=config.COLORS["background"])
        difficulty_frame = tk.Frame(tab_container.content_frame, bg=config.COLORS["background"])

        tab_container.add_tab("Résumé", summary_frame)
        tab_container.add_tab("Analyse des Coups", moves_frame)
        tab_container.add_tab("Statistiques", stats_frame)
        tab_container.add_tab("Difficulté", difficulty_frame)

        # Populate Summary
        _create_summary_tab_content(
            self,
            summary_frame,
            move_evaluations,
            white_stats,
            black_stats,
            title_font,
            subheader_font,
            text_font,
        )

        # Populate Moves
        try:
            _create_moves_tab_content(self, moves_frame, game_analysis, text_font)
        except Exception as e:
            print(f"Error while creating moves tab: {e}")

        # Populate Stats
        try:
            self._populate_stats_tab(stats_frame, white_stats, black_stats, subheader_font, text_font)
        except Exception as e:
            print(f"Error while creating stats tab: {e}")

        # Populate Difficulty
        try:
            if isinstance(self.analysis_results, dict):
                difficulty_metrics = self.analysis_results.get("game_difficulty")
            else:
                difficulty_metrics = getattr(self.analysis_results, "game_difficulty", None)
            _create_difficulty_tab_content(difficulty_frame, difficulty_metrics, title_font, subheader_font, text_font)
        except Exception as e:
            print(f"Error while creating difficulty tab: {e}")

        # Bind events and close handler
        analysis_window.bind("<Configure>", self._on_resize)
        analysis_window.protocol("WM_DELETE_WINDOW", lambda: self._close_analysis_window(analysis_window))

        return analysis_window

    def _close_analysis_window(self, analysis_window: tk.Toplevel):
        """Safely close the analysis window and clean up bindings/resources."""
        try:
            # Unbind keyboard navigation keys that may have been bound on this toplevel
            for key in ('<Left>', '<Right>', '<Up>', '<Down>'):
                try:
                    analysis_window.unbind(key)
                except Exception:
                    pass

            # Best effort to clear references that keep widgets alive
            for attr in ("mini_board", "move_info_label", "eval_info_label", "best_move_label",
                         "player_banner", "error_navigation"):
                if hasattr(self, attr):
                    try:
                        setattr(self, attr, None)
                    except Exception:
                        pass

            # Finally destroy the window
            if analysis_window and analysis_window.winfo_exists():
                analysis_window.destroy()
        except Exception:
            # In case of unexpected issues, force destroy as a fallback
            try:
                analysis_window.destroy()
            except Exception:
                pass

    def _on_resize(self, event):
        """Handle window resize events."""
        # This method is called when the analysis window is resized.
        # We can add logic here to adjust the layout if needed.
        # For now, it prevents the AttributeError.
        pass

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

    def _populate_stats_tab(self, parent, white_stats, black_stats, subheader_font, text_font):
        """Populate the 'Statistiques' tab with per-game metrics specific to this game."""
        container = tk.Frame(parent, bg=config.COLORS["background"], padx=15, pady=10)
        container.pack(fill=tk.BOTH, expand=True)

        # Access move evaluations from the stored analysis results
        if isinstance(self.analysis_results, dict):
            move_evals = self.analysis_results.get("move_evaluations", [])
        else:
            move_evals = getattr(self.analysis_results, "move_evaluations", [])

        # --- Opening-derived metrics ---
        # Determine theory depth (consecutive plies from start with opening info)
        theory_depth_plies = 0
        for i, ev in enumerate(move_evals):
            if ev.get("opening"):
                theory_depth_plies += 1
            else:
                break
        theory_depth_moves = (theory_depth_plies + 1) // 2 if theory_depth_plies > 0 else 0

        # Novelty: first non-theoretical move and its impact
        novelty_index = None
        for i, ev in enumerate(move_evals):
            if not ev.get("opening"):
                novelty_index = i
                break
        novelty_desc = "—"
        novelty_impact = None
        if novelty_index is not None and 0 <= novelty_index < len(move_evals):
            nev = move_evals[novelty_index]
            move_text = nev.get("move_text") or nev.get("san") or "?"
            side = "Blancs" if (novelty_index % 2 == 0) else "Noirs"
            novelty_desc = f"{move_text} ({side})"
            # score_change is from white's perspective
            novelty_impact = nev.get("score_change")

        # Exit quality: evaluation after N plies post-book (from White’s POV)
        POST_BOOK_PLIES = 4
        exit_eval = None
        if novelty_index is not None:
            target_idx = min(len(move_evals) - 1, novelty_index + POST_BOOK_PLIES)
            if target_idx >= 0:
                exit_eval = move_evals[target_idx].get("score_after")

        # Compute global volatility and max swing from raw series (side-agnostic)
        raw_series = [ev.get("score_after") for ev in move_evals if ev.get("score_after") is not None]
        if len(raw_series) >= 2:
            raw_deltas = [raw_series[i] - raw_series[i-1] for i in range(1, len(raw_series))]
            m = len(raw_deltas)
            mean_d = sum(raw_deltas) / m
            g_variance = sum((d - mean_d) ** 2 for d in raw_deltas) / m
            global_volatility = math.sqrt(g_variance)
            global_max_swing = max(abs(d) for d in raw_deltas)
        else:
            global_volatility = 0.0
            global_max_swing = 0.0

        # Global stats card
        global_card = tk.Frame(container, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#E0E0E0")
        global_card.pack(fill=tk.X, pady=(0, 10))
        tk.Label(global_card, text="Statistiques globales", font=subheader_font, bg="white", fg="#333333").pack(anchor="w")
        sep_g = tk.Frame(global_card, height=1, bg="#EEEEEE")
        sep_g.pack(fill=tk.X, pady=(4, 10))
        grid_g = tk.Frame(global_card, bg="white")
        grid_g.pack(fill=tk.X)
        grid_g.columnconfigure(0, weight=1)
        grid_g.columnconfigure(1, weight=1)
        # Helper to add a label with a '?' tooltip on the left and the value on the right
        def _add_metric_with_help(row, label_text, help_text, value_text):
            left = tk.Frame(grid_g, bg="white")
            left.grid(row=row, column=0, sticky="w", pady=2)
            tk.Label(left, text=label_text, font=text_font, bg="white", fg="#555555").pack(side=tk.LEFT)
            q = tk.Label(left, text=" ? ", font=("Segoe UI", 9, "bold"), bg="white", fg="#888888", cursor="question_arrow")
            q.pack(side=tk.LEFT, padx=(6, 0))

            tooltip = {"win": None}

            def show_tip(event=None):
                if tooltip["win"] is not None:
                    return
                tw = tk.Toplevel(left)
                tw.wm_overrideredirect(True)
                tw.configure(bg="#333333")
                # Position near cursor
                x = q.winfo_rootx() + 15
                y = q.winfo_rooty() + 20
                tw.wm_geometry(f"+{x}+{y}")
                msg = tk.Label(tw, text=help_text, justify=tk.LEFT, bg="#333333", fg="#FFFFFF", padx=8, pady=6, font=("Segoe UI", 9))
                msg.pack()
                tooltip["win"] = tw

            def hide_tip(event=None):
                if tooltip["win"] is not None:
                    try:
                        tooltip["win"].destroy()
                    except Exception:
                        pass
                    tooltip["win"] = None

            q.bind("<Enter>", show_tip)
            q.bind("<Leave>", hide_tip)
            q.bind("<Button-1>", show_tip)

            tk.Label(grid_g, text=value_text, font=text_font, bg="white", fg="#333333", anchor="e").grid(row=row, column=1, sticky="e", pady=2)

        _add_metric_with_help(
            0,
            "Volatilité (σ)",
            "Écart-type des variations d’évaluation entre demi-coups (en pions).\nPlus c’est élevé, plus la partie a fait le ‘yo-yo’.",
            f"{global_volatility:.2f}"
        )
        _add_metric_with_help(
            1,
            "Plus gros swing",
            "Plus grande variation d’évaluation entre deux demi-coups consécutifs (en pions).",
            f"{global_max_swing:.2f}"
        )
        # Opening metrics rows
        row_i = 2
        tk.Label(grid_g, text="Profondeur de théorie", font=text_font, bg="white", fg="#555555", anchor="w").grid(row=row_i, column=0, sticky="w", pady=2)
        tk.Label(grid_g, text=f"{theory_depth_plies} demi-coups ({theory_depth_moves} coups)", font=text_font, bg="white", fg="#333333", anchor="e").grid(row=row_i, column=1, sticky="e", pady=2)
        row_i += 1
        tk.Label(grid_g, text="Nouveauté", font=text_font, bg="white", fg="#555555", anchor="w").grid(row=row_i, column=0, sticky="w", pady=2)
        if novelty_impact is None:
            novelty_line = novelty_desc
        else:
            novelty_line = f"{novelty_desc} — impact {novelty_impact:+.2f}"
        tk.Label(grid_g, text=novelty_line, font=text_font, bg="white", fg="#333333", anchor="e").grid(row=row_i, column=1, sticky="e", pady=2)
        row_i += 1
        tk.Label(grid_g, text=f"Qualité sortie de livre (+{POST_BOOK_PLIES} demi-coups)", font=text_font, bg="white", fg="#555555", anchor="w").grid(row=row_i, column=0, sticky="w", pady=2)
        exit_eval_text = "—" if exit_eval is None else (f"{exit_eval:+.2f}")
        tk.Label(grid_g, text=exit_eval_text, font=text_font, bg="white", fg="#333333", anchor="e").grid(row=row_i, column=1, sticky="e", pady=2)

        # Layout: two player cards side by side
        cards = tk.Frame(container, bg=config.COLORS["background"]) 
        cards.pack(fill=tk.X)
        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)

        def build_card(parent_frame):
            return tk.Frame(parent_frame, bg="white", padx=15, pady=15, highlightthickness=1, highlightbackground="#E0E0E0")

        white_card = build_card(cards)
        white_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        black_card = build_card(cards)
        black_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Extract player names if available
        white_name = None
        black_name = None
        try:
            if isinstance(self.analysis_results, dict):
                white_name = self.analysis_results.get("white_player")
                black_name = self.analysis_results.get("black_player")
                if (white_name is None or black_name is None) and isinstance(self.analysis_results.get("headers"), dict):
                    headers = self.analysis_results.get("headers")
                    white_name = white_name or headers.get("White")
                    black_name = black_name or headers.get("Black")
            else:
                white_name = getattr(self.analysis_results, "white_player", None)
                black_name = getattr(self.analysis_results, "black_player", None)
        except Exception:
            pass

        def compute_player_metrics(player_color):
            # Thresholds
            OPPORTUNITY_GAIN = 1.0  # min gain to consider an opportunity (player POV)
            FOUND_GAIN = 0.8        # min realized gain to count as found (player POV)
            THREAT_PERSIST = 1.0    # min persist gain after opponent reply (player POV)
            MATE_PAWNS = 90.0       # threshold to consider best line as mating (player POV, in pawns)
            # Build evaluation series from player's perspective
            series = []
            for ev in move_evals:
                s = ev.get("score_after")
                if s is None:
                    continue
                series.append(s if player_color == "White" else -s)

            n = len(series)
            if n == 0:
                return {
                    "pct_win": 0.0, "pct_equal": 0.0, "pct_lose": 0.0,
                    "volatility": 0.0, "max_swing": 0.0, "reversals": 0,
                    "tactics_found": 0, "tactics_missed": 0, "threats_created": 0, "missed_opportunities": 0
                }

            # Time spent winning/equal/losing
            win = sum(1 for v in series if v >= 1.0)
            equal = sum(1 for v in series if -1.0 < v < 1.0)
            lose = n - win - equal  # <= -1.0
            pct_win = (win / n) * 100.0
            pct_equal = (equal / n) * 100.0
            pct_lose = (lose / n) * 100.0

            # Volatility and largest swing
            if n >= 2:
                deltas = [series[i] - series[i-1] for i in range(1, n)]
                m = len(deltas)
                mean_d = sum(deltas) / m
                variance = sum((d - mean_d) ** 2 for d in deltas) / m
                volatility = math.sqrt(variance)
                max_swing = max(abs(d) for d in deltas)
            else:
                volatility = 0.0
                max_swing = 0.0

            # Reversals: count crossings of 50% win probability
            probs = []
            for v in series:
                try:
                    probs.append(self.game_analyzer.score_to_win_probability(v))
                except Exception:
                    # Fallback simple logistic approximation if needed
                    try:
                        p = 1.0 / (1.0 + math.exp(-4 * v))
                    except Exception:
                        p = 0.5
                    probs.append(p)
            above = [p >= 0.5 for p in probs]
            reversals = sum(1 for i in range(1, len(above)) if above[i] != above[i-1])

            # --- Tactics and threats ---
            threats_created = 0
            # Per-subcategory opportunity tracking
            # Mate: sequence-based (count once per continuous mate net), found if n decreases at least once
            opportunities_mate_found = 0
            opportunities_mate_missed = 0
            # Gain: per-move opportunities
            opportunities_gain_found = 0
            opportunities_gain_missed = 0
            # Running state for mate sequences
            mate_seq_active = False
            mate_seq_found_any = False

            # Iterate moves for this player only
            for i, ev in enumerate(move_evals):
                if ev.get("side") != ("White" if player_color == "White" else "Black"):
                    continue

                # Player POV scores
                # Robust previous evaluation: prefer 'score_before'; if missing, use previous ply's 'score_after'
                prev_raw = ev.get("score_before")
                if prev_raw is None:
                    if i > 0:
                        prev_raw = move_evals[i-1].get("score_after", 0.0)
                    else:
                        prev_raw = 0.0
                prev_player = prev_raw
                if player_color == "Black":
                    prev_player = -prev_player
                after_player = ev.get("score_after", prev_player)
                if player_color == "Black":
                    after_player = -after_player
                score_gain = after_player - prev_player  # player's perspective

                # Use top move best score if available (already in player's POV)
                top_moves = ev.get("top_moves", []) or []
                best_line_score = top_moves[0]["score"] if len(top_moves) > 0 and isinstance(top_moves[0], dict) and "score" in top_moves[0] else None
                # Ensure best line score is numeric (already in player's POV from analyzer)
                if best_line_score is not None:
                    try:
                        best_line_score = float(best_line_score)
                    except Exception:
                        pass

                # Tactical opportunity detection (two types): mate vs gain
                mate_prev = ev.get("mate_in_prev_player")
                mate_after = ev.get("mate_in_after_player")
                is_mate_opp = (mate_prev is not None) or (best_line_score is not None and best_line_score >= MATE_PAWNS)

                # Handle mate sequence counting (sequence-based)
                if is_mate_opp and not mate_seq_active:
                    # Start a new mate opportunity sequence
                    mate_seq_active = True
                    mate_seq_found_any = False
                if mate_seq_active:
                    # Mark sequence as found if mate distance decreases on this move
                    if mate_prev is not None and mate_after is not None and mate_after < mate_prev:
                        mate_seq_found_any = True
                    # If sequence ends (no mate opportunity now), finalize
                    if not is_mate_opp:
                        if mate_seq_found_any:
                            opportunities_mate_found += 1
                        else:
                            opportunities_mate_missed += 1
                        mate_seq_active = False
                        mate_seq_found_any = False

                # Handle gain opportunities per move
                is_gain_opp = (not is_mate_opp) and (best_line_score is not None and (best_line_score - prev_player) >= OPPORTUNITY_GAIN)
                if is_gain_opp:
                    if score_gain >= FOUND_GAIN:
                        opportunities_gain_found += 1
                    else:
                        opportunities_gain_missed += 1

                # Threats created: sustained advantage increase after opponent reply
                j = i + 1
                if j < len(move_evals):
                    opp_after = move_evals[j].get("score_after", after_player)
                    # Convert to player's POV
                    if player_color == "Black":
                        opp_after = -opp_after
                    # Compare to pre-move value
                    if (opp_after - prev_player) >= THREAT_PERSIST:
                        threats_created += 1

            # Close any running mate sequence at the end of moves
            if mate_seq_active:
                if mate_seq_found_any:
                    opportunities_mate_found += 1
                else:
                    opportunities_mate_missed += 1
                mate_seq_active = False
                mate_seq_found_any = False

            return {
                "pct_win": pct_win, "pct_equal": pct_equal, "pct_lose": pct_lose,
                "volatility": volatility, "max_swing": max_swing, "reversals": reversals,
                "threats_created": threats_created,
                # Totals derived
                "opportunities_total": (opportunities_mate_found + opportunities_mate_missed + opportunities_gain_found + opportunities_gain_missed),
                # Mate breakdown (found/missed)
                "opportunities_mate_found": opportunities_mate_found,
                "opportunities_mate_missed": opportunities_mate_missed,
                # Gain breakdown (found/missed)
                "opportunities_gain_found": opportunities_gain_found,
                "opportunities_gain_missed": opportunities_gain_missed,
                # Legacy aliases (optional): keep for compatibility if referenced elsewhere
                "missed_opportunities": (opportunities_mate_missed + opportunities_gain_missed)
            }

        white_metrics = compute_player_metrics("White")
        black_metrics = compute_player_metrics("Black")

        def fill_card(card, title, metrics):
            header = tk.Frame(card, bg="white")
            header.pack(fill=tk.X, pady=(0, 8))
            icon = "♔" if title.startswith("BLANCS") else "♚"
            tk.Label(header, text=icon, font=("Segoe UI", 16), bg="white", fg="#333333").pack(side=tk.LEFT, padx=(0, 8))
            tk.Label(header, text=title, font=subheader_font, bg="white", fg="#333333").pack(side=tk.LEFT)

            # Advantage distribution bar (colored)
            sep1 = tk.Frame(card, height=1, bg="#EEEEEE")
            sep1.pack(fill=tk.X, pady=(2, 8))
            tk.Label(card, text="Temps en avantage / égalité / désavantage", font=("Segoe UI", 10, "bold"), bg="white", fg="#333333").pack(anchor="w")
            bar_frame = tk.Frame(card, bg="#F0F2F5", height=16)
            bar_frame.pack(fill=tk.X, pady=(4, 6))
            bar_frame.pack_propagate(False)
            # Create inner container and place colored segments with relative widths
            inner = tk.Frame(bar_frame, bg="#F0F2F5", height=16)
            inner.pack(fill=tk.X, expand=True)
            # Normalize to fractions [0,1]
            w = max(0.0, min(1.0, metrics["pct_win"] / 100.0))
            e = max(0.0, min(1.0, metrics["pct_equal"] / 100.0))
            l = max(0.0, min(1.0, metrics["pct_lose"] / 100.0))
            total = w + e + l
            if total <= 0:
                w = e = l = 0.0
            else:
                w, e, l = w/total, e/total, l/total
            win_seg = tk.Frame(inner, bg="#4CAF50")
            eq_seg = tk.Frame(inner, bg="#BDBDBD")
            lose_seg = tk.Frame(inner, bg="#F44336")
            # Place colored segments
            win_seg.place(relx=0.0, rely=0.0, relheight=1.0, relwidth=w)
            eq_seg.place(relx=w, rely=0.0, relheight=1.0, relwidth=e)
            lose_seg.place(relx=w+e, rely=0.0, relheight=1.0, relwidth=l)
            # Labels for percentages
            pct_text = f"Gagnant {metrics['pct_win']:.0f}%   |   Égal {metrics['pct_equal']:.0f}%   |   Perdant {metrics['pct_lose']:.0f}%"
            tk.Label(card, text=pct_text, font=text_font, bg="white", fg="#555555").pack(anchor="w")

            # Numeric metrics grid (per-player specifics)
            sep2 = tk.Frame(card, height=1, bg="#EEEEEE")
            sep2.pack(fill=tk.X, pady=(8, 6))
            grid = tk.Frame(card, bg="white")
            grid.pack(fill=tk.X)
            grid.columnconfigure(0, weight=1)
            grid.columnconfigure(1, weight=1)
            # Renversements only (global metrics shown above)
            rowp = 0
            tk.Label(grid, text="Renversements", font=text_font, bg="white", fg="#555555", anchor="w").grid(row=rowp, column=0, sticky="w", pady=2)
            tk.Label(grid, text=f"{metrics['reversals']}", font=text_font, bg="white", fg="#333333", anchor="e").grid(row=rowp, column=1, sticky="e", pady=2)

            # Tactics and threats section
            sep3 = tk.Frame(card, height=1, bg="#EEEEEE")
            sep3.pack(fill=tk.X, pady=(6, 6))
            tk.Label(card, text="Tactiques et menaces", font=("Segoe UI", 10, "bold"), bg="white", fg="#333333").pack(anchor="w")
            grid2 = tk.Frame(card, bg="white")
            grid2.pack(fill=tk.X, pady=(4, 0))
            grid2.columnconfigure(0, weight=1)
            grid2.columnconfigure(1, weight=1)
            # Local helper to create a row with a '?' tooltip
            def add_row_with_help(row, label_text, help_text, value_text):
                left = tk.Frame(grid2, bg="white")
                left.grid(row=row, column=0, sticky="w", pady=2)
                tk.Label(left, text=label_text, font=text_font, bg="white", fg="#555555").pack(side=tk.LEFT)
                q = tk.Label(left, text=" ? ", font=("Segoe UI", 9, "bold"), bg="white", fg="#888888", cursor="question_arrow")
                q.pack(side=tk.LEFT, padx=(6, 0))
                tip = {"win": None}
                def show_tip(event=None):
                    if tip["win"] is not None:
                        return
                    tw = tk.Toplevel(left)
                    tw.wm_overrideredirect(True)
                    tw.configure(bg="#333333")
                    x = q.winfo_rootx() + 15
                    y = q.winfo_rooty() + 20
                    tw.wm_geometry(f"+{x}+{y}")
                    msg = tk.Label(tw, text=help_text, justify=tk.LEFT, bg="#333333", fg="#FFFFFF", padx=8, pady=6, font=("Segoe UI", 9))
                    msg.pack()
                    tip["win"] = tw
                def hide_tip(event=None):
                    if tip["win"] is not None:
                        try:
                            tip["win"].destroy()
                        except Exception:
                            pass
                        tip["win"] = None
                q.bind("<Enter>", show_tip)
                q.bind("<Leave>", hide_tip)
                q.bind("<Button-1>", show_tip)
                tk.Label(grid2, text=value_text, font=text_font, bg="white", fg="#333333", anchor="e").grid(row=row, column=1, sticky="e", pady=2)

            # Opportunities (total + breakdown)
            add_row_with_help(
                0,
                "Opportunités (total)",
                "Nombre total d’occasions tactiques proposées par le moteur pour votre camp:\n• Mat: meilleure ligne mène à un mat (évaluation très élevée pour votre camp).\n• Gain: meilleure ligne améliore l’évaluation d’au moins le seuil (ex. +0.8).",
                f"{metrics['opportunities_total']}"
            )
            add_row_with_help(
                1,
                "— Mat (trouvées / manquées)",
                "Occasions de mat comptées par séquences (une seule fois pour un même réseau de mat).\n‘Trouvée’ si, à un moment pendant la séquence, la distance de mat (n) diminue après votre coup; sinon ‘manquée’.",
                f"{metrics['opportunities_mate_found']} / {metrics['opportunities_mate_missed']}"
            )
            add_row_with_help(
                2,
                "— Gain (trouvées / manquées)",
                "Occasions où la meilleure ligne gagne au moins le seuil défini (ex. +0.8 pion).\n‘Trouvée’ si votre coup réalise ≥ ce gain, sinon ‘manquée’.",
                f"{metrics['opportunities_gain_found']} / {metrics['opportunities_gain_missed']}"
            )
            # Threats created
            add_row_with_help(
                3,
                "Menaces créées",
                "Après votre coup et la réponse adverse, si l’évaluation reste ≥ +0.5 au-dessus de l’évaluation d’avant votre coup (de votre point de vue), on considère qu’une menace durable a été créée.",
                f"{metrics['threats_created']}"
            )
            # Missed opportunities (explicit)
            add_row_with_help(
                4,
                "Opportunités manquées",
                "Nombre d’opportunités (mat + gain) détectées mais non converties.",
                f"{metrics['missed_opportunities']}"
        )
        
        white_title = "BLANCS" + (f" ({white_name})" if white_name else "")
        black_title = "NOIRS" + (f" ({black_name})" if black_name else "")
        fill_card(white_card, white_title, white_metrics)
        fill_card(black_card, black_title, black_metrics)
        
    # Helper methods for the modernized tab
    def _create_modern_player_stats(self, parent_frame, stats, text_font):
        """Create player statistics with modern styling."""        
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

    def _create_mini_board(self, parent_frame, move_evaluations, opening_label=None):
        """Create a mini chess board panel."""
        # Le header est maintenant créé dans moves_tab.py, pas besoin de le recréer ici
        
        # Stocke la référence au label d'ouverture passé en paramètre
        if opening_label:
            self.opening_label = opening_label
            print("DEBUG: Reference to opening_label saved in _create_mini_board!")
        
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
        
        # Créer un conteneur horizontal pour l'échiquier et la barre d'évaluation
        board_and_eval_container = tk.Frame(board_container, bg="white")
        board_and_eval_container.pack(anchor="center", pady=5)
        
        # Create the mini-board canvas with piece images
        self.mini_board = MiniChessBoard(board_and_eval_container, piece_images=self.piece_images)
        self.mini_board.pack(side=tk.LEFT, pady=5)
        
        # Ajouter la barre d'évaluation à droite de l'échiquier
        self.evaluation_bar = EvaluationBar(
            board_and_eval_container,
            width=30,
            height=self.mini_board.winfo_reqheight()
        )
        self.evaluation_bar.pack(side=tk.LEFT, padx=(10, 0), fill=tk.Y)
        
        # Info panel below board with flip button to the right
        info_frame = tk.Frame(board_container, bg="white")
        info_frame.pack(fill=tk.X, pady=(5, 0))
        
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
        
        # Logs pour debugging
        print("DEBUG: Move selected:", move_index)
        print("DEBUG: move_eval:", move_eval)
        if 'opening' in move_eval:
            print("DEBUG: Opening info present:", move_eval['opening'])
        else:
            print("DEBUG: No opening info in move_eval")
        
        # Update mini board if we have position history
        if self.position_history and self.mini_board:
            if move_index < len(self.position_history):
                # Always clear existing visualizations first
                if hasattr(self.mini_board, 'delete'):
                    self.mini_board.delete("arrow")
                    self.mini_board.delete("highlight") 
                    self.mini_board.delete("error_symbol")
                    self.mini_board.delete("classification_symbol")
                
                # Get current and previous position FEN for move conversions
                current_position_fen = self.position_history[move_index+1]
                prev_position_fen = self.position_history[move_index] if move_index > 0 else self.position_history[0]
                
                # Update the board to this position
                self.mini_board.update_to_position(current_position_fen)
                
                # Update the player banner to show current turn
                # For move index: even numbers are White's moves, odd numbers are Black's moves
                if hasattr(self, 'player_banner'):
                    current_turn = chess.WHITE if (move_index + 1) % 2 == 0 else chess.BLACK
                    self.player_banner.update_names(current_turn=current_turn)
                
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
                
                # Update opening information if available - avec logs
                if 'opening' in move_eval and move_eval['opening']:
                    opening_text = ""
                    if isinstance(move_eval['opening'], dict):
                        print("DEBUG: Opening is a dict")
                        if 'eco' in move_eval['opening'] and 'name' in move_eval['opening']:
                            opening_text = f"{move_eval['opening']['eco']} - {move_eval['opening']['name']}"
                            print(f"DEBUG: Opening text formatted with ECO and name: {opening_text}")
                        elif 'name' in move_eval['opening']:
                            opening_text = move_eval['opening']['name']
                            print(f"DEBUG: Opening text with name only: {opening_text}")
                        elif 'eco' in move_eval['opening']:
                            opening_text = f"ECO {move_eval['opening']['eco']}"
                            print(f"DEBUG: Opening text with ECO only: {opening_text}")
                    else:
                        # Si opening n'est pas un dictionnaire
                        opening_text = str(move_eval['opening'])
                        print(f"DEBUG: Opening is not a dict, value: {opening_text}")
                    
                    print(f"DEBUG: Final opening_text: '{opening_text}'")
                    
                    if opening_text:
                        print("DEBUG: Updating opening_label with text:", opening_text)
                        # Vérifier si l'attribut existe
                        if hasattr(self, 'opening_label'):
                            print("DEBUG: self.opening_label exists")
                            # Vérifier si le widget est valide
                            try:
                                self.opening_label.winfo_exists()
                                print("DEBUG: opening_label widget exists and is valid")
                                self.opening_label.config(text=opening_text)
                            except (tk.TclError, AttributeError) as e:
                                print(f"DEBUG: Error updating opening_label: {e}")
                        else:
                            print("DEBUG: self.opening_label does NOT exist!")
                    else:
                        print("DEBUG: Empty opening_text, not updating label")
                        if hasattr(self, 'opening_label'):
                            try:
                                self.opening_label.config(text="")
                            except (tk.TclError, AttributeError) as e:
                                print(f"DEBUG: Error clearing opening_label: {e}")
                else:
                    print("DEBUG: No opening info, clearing label")
                    if hasattr(self, 'opening_label'):
                        try:
                            self.opening_label.config(text="")
                        except (tk.TclError, AttributeError) as e:
                            print(f"DEBUG: Error clearing opening_label: {e}")
                
                # Update evaluation info
                self._update_evaluation_labels(move_eval)
                
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
                
                # Display classification icon according to move quality
                if uci_move and "classification" in move_eval:
                    classification = move_eval["classification"]
                    self.mini_board.highlight_move_classification(uci_move, classification)
                    
                    # For error moves, also show the arrow and best move
                    if classification in ["Erreur", "Grosse erreur"] and best_move_uci:
                        # Parse from and to squares
                        from_square = chess.parse_square(uci_move[:2])
                        to_square = chess.parse_square(uci_move[2:4])
                        
                        # Get error color from config based on classification
                        error_color = config.CLASSIFICATION_COLORS.get(classification, {}).get("main", "#F44336")
                        
                        # Draw error arrow
                        self.mini_board.draw_error_indicator(from_square, to_square, color=error_color, width=3)
                        
                        # Draw best move arrow in green
                        best_from = chess.parse_square(best_move_uci[:2])
                        best_to = chess.parse_square(best_move_uci[2:4])
                        self.mini_board.draw_error_indicator(best_from, best_to, color="#4CAF50", width=3)
            else:
                # If position not available
                self.mini_board.draw_board()  # Just show empty board
                self.move_info_label.config(text="Position non disponible")
                self.eval_info_label.config(text="")
                self.best_move_label.config(text="")
                self.opening_label.config(text="")

    def _update_evaluation_labels(self, move_eval):
        """Update evaluation labels with move data."""
        # Update evaluation info
        score_after = move_eval["score_after"]
        formatted_score = f"+{abs(score_after):.2f}" if score_after >= 0 else f"-{abs(score_after):.2f}"
        color_advantage = "Blancs" if score_after >= 0 else "Noirs"
        
        self.eval_info_label.config(
            text=f"Évaluation: {formatted_score} (avantage {color_advantage})"
        )
        
        # Mettre à jour la barre d'évaluation
        if hasattr(self, 'evaluation_bar'):
            # Détecter si c'est un mat
            is_mate = False
            mate_in = 0
            
            if "mate_in" in move_eval and move_eval["mate_in"] is not None:
                is_mate = True
                mate_in = move_eval["mate_in"]
            
            # Mise à jour avec animation
            self.evaluation_bar.update_evaluation(
                evaluation=score_after,
                is_mate=is_mate,
                mate_in=mate_in,
                animate=True
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