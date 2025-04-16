"""Summary tab components for chess analysis."""

import tkinter as tk
from tkinter import font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as ticker
from src.utils import config
from src.gui.analysis.metrics import _create_accuracy_chart, _create_enhanced_move_quality_display, _create_metric_box

def _create_summary_tab_content(view_instance, summary_frame, move_evaluations, white_stats, black_stats,
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
    
    # Récupérer l'information d'ouverture pour utilisation ultérieure
    last_move_index = len(move_evaluations) - 1
    final_opening = None
    if last_move_index >= 0 and "opening" in move_evaluations[last_move_index]:
        final_opening = move_evaluations[last_move_index]["opening"]
    
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
    white_accuracy = white_stats.get("accuracy", 0)  # Default 0% if not provided
    _create_accuracy_chart(view_instance, white_card, white_accuracy, is_white=True)  

    # White stats content
    _create_enhanced_move_quality_display(view_instance, white_card, white_stats, text_font)
    
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
    black_accuracy = black_stats.get("accuracy", 0)  # Default 0% if not provided
    _create_accuracy_chart(view_instance,black_card, black_accuracy, is_white=False)
    
    # Black stats content
    _create_enhanced_move_quality_display(view_instance, black_card, black_stats, text_font)
    
    # Create game evolution chart with card design
    chart_container = tk.Frame(
        content_frame, 
        bg="white",
        bd=0,
        highlightthickness=1,
        highlightbackground="#E0E0E0",
        padx=15,
        pady=15
    )
    chart_container.pack(fill=tk.BOTH, expand=True, pady=(20, 20))
    
    # Add chart to the container
    _create_game_evolution_chart(view_instance,chart_container, move_evaluations, title_font, subheader_font)
    
    # Déplacer le panel d'ouverture ici, après le graphique
    if final_opening:
        # Créer le panel d'ouverture avec un design élégant
        opening_panel = tk.Frame(
            content_frame, 
            bg="white",
            bd=0,
            highlightthickness=1,
            highlightbackground="#E0E0E0",
            padx=20,
            pady=15
        )
        opening_panel.pack(fill=tk.X, pady=(5, 20))
        
        # En-tête avec icône
        opening_header = tk.Frame(opening_panel, bg="white")
        opening_header.pack(fill=tk.X, pady=(0, 12))
        
        # Icône d'ouverture
        tk.Label(
            opening_header,
            text="♟",  # Pion d'échecs
            font=("Segoe UI", 16),
            bg="white",
            fg="#333333"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Titre d'ouverture
        tk.Label(
            opening_header,
            text="OUVERTURE",
            font=subheader_font,
            bg="white",
            fg="#333333"
        ).pack(side=tk.LEFT)
        
        # Contenu principal
        opening_content = tk.Frame(opening_panel, bg="white")
        opening_content.pack(fill=tk.X, pady=(0, 5))
        
        # Nom de l'ouverture avec mise en évidence
        if isinstance(final_opening, dict) and "name" in final_opening:
            opening_name = final_opening.get("name", "")
            opening_eco = final_opening.get("eco", "")
            
            if opening_eco:
                # Afficher le code ECO avec un badge stylisé
                eco_badge = tk.Frame(
                    opening_content,
                    bg="#3F51B5",  # Bleu indigo
                    padx=8,
                    pady=3,
                    highlightthickness=0
                )
                eco_badge.pack(side=tk.LEFT, padx=(0, 15))
                
                tk.Label(
                    eco_badge,
                    text=opening_eco,
                    font=("Segoe UI", 11, "bold"),
                    bg="#3F51B5",
                    fg="white"
                ).pack()
            
            # Nom de l'ouverture en plus petit (taille réduite)
            tk.Label(
                opening_content,
                text=opening_name,
                font=("Segoe UI", 12),  # Taille réduite de 14 à 12, et sans gras
                bg="white",
                fg="#212121"
            ).pack(side=tk.LEFT)
        else:
            # Afficher le texte de l'ouverture si ce n'est pas un dictionnaire
            opening_text = str(final_opening)
            tk.Label(
                opening_content,
                text=opening_text,
                font=("Segoe UI", 12),  # Taille réduite de 14 à 12
                bg="white",
                fg="#212121"
            ).pack(side=tk.LEFT)
    
    # Add game difficulty metrics if available
    if hasattr(view_instance, 'game_analyzer') and hasattr(view_instance.game_analyzer, 'difficulty_calculator'):
        if "difficulty_metrics" in view_instance.analysis_results:
            _create_difficulty_metrics_display(content_frame, 
                                              view_instance.analysis_results["difficulty_metrics"],
                                              title_font, 
                                              subheader_font,
                                              text_font)
    
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

    view_instance._create_count_statistics(game_stats_card, total_moves, white_moves, black_moves, subheader_font, text_font)

    stat_grid = tk.Frame(game_stats_card, bg="white")
    stat_grid.pack(fill=tk.X)
    
    # Make columns equal width
    stat_grid.columnconfigure(0, weight=1)
    stat_grid.columnconfigure(1, weight=1)
    
    # Stats with modern styling
    view_instance._create_stat_row(stat_grid, "Nombre total de coups:", f"{total_moves}", 0, text_font)
    view_instance._create_stat_row(stat_grid, "Coups des blancs:", f"{white_moves}", 1, text_font)
    view_instance._create_stat_row(stat_grid, "Coups des noirs:", f"{black_moves}", 2, text_font)
    
    # Recursively bind mousewheel to all widgets
    view_instance._bind_mousewheel_to_widgets(content_frame, _on_mousewheel, _on_linux_scroll_up, _on_linux_scroll_down)

def _create_game_evolution_chart(view_instance, summary_frame, move_evaluations, title_font, subheader_font):
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
    
    # Ajouter le canvas Matplotlib au frame Tkinter
    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill=tk.BOTH, expand=True)
    canvas.draw()

def _create_difficulty_metrics_display(content_frame, difficulty_metrics, title_font, subheader_font, text_font):
    """Create a modern visual display for game difficulty metrics."""
    # Main difficulty card
    difficulty_card = tk.Frame(
        content_frame, 
        bg="white",
        bd=0,
        highlightthickness=1,
        highlightbackground="#E0E0E0",
        padx=20,
        pady=20
    )
    difficulty_card.pack(fill=tk.X, pady=(0, 20))
    
    # Header with icon
    difficulty_header = tk.Frame(difficulty_card, bg="white")
    difficulty_header.pack(fill=tk.X, pady=(0, 15))
    
    # Use chess piece as the icon
    difficulty_icon = tk.Label(
        difficulty_header,
        text="♕",  # Queen symbol for complex thinking
        font=("Segoe UI", 16),
        bg="white",
        fg="#333333"
    )
    difficulty_icon.pack(side=tk.LEFT, padx=(0, 10))
    
    tk.Label(
        difficulty_header,
        text="DIFFICULTÉ DE LA PARTIE",
        font=subheader_font,
        bg="white",
        fg="#333333"
    ).pack(side=tk.LEFT, anchor="w")
    
    # Separator
    separator = tk.Frame(difficulty_card, height=1, bg="#E0E0E0")
    separator.pack(fill=tk.X, pady=(0, 15))
    
    # Get difficulty data
    overall_difficulty = difficulty_metrics.get("overall_difficulty", 5)
    white_difficulty = difficulty_metrics.get("white_difficulty", {})
    black_difficulty = difficulty_metrics.get("black_difficulty", {})
    
    # Main difficulty display (overall)
    main_difficulty_frame = tk.Frame(difficulty_card, bg="white")
    main_difficulty_frame.pack(fill=tk.X, pady=10)
    
    # Create visual meter for overall difficulty
    _create_difficulty_meter(main_difficulty_frame, overall_difficulty, "DIFFICULTÉ GLOBALE", text_font)
    
    # Player-specific difficulty section
    players_difficulty_frame = tk.Frame(difficulty_card, bg="white")
    players_difficulty_frame.pack(fill=tk.X, pady=15)
    
    # Configure grid for player columns
    players_difficulty_frame.columnconfigure(0, weight=1)
    players_difficulty_frame.columnconfigure(1, weight=1)
    
    # Create white difficulty panel
    white_diff_frame = tk.Frame(players_difficulty_frame, bg="white", padx=10)
    white_diff_frame.grid(row=0, column=0, sticky="nsew")
    
    # White difficulty title
    white_title_frame = tk.Frame(white_diff_frame, bg="white")
    white_title_frame.pack(fill=tk.X, pady=(0, 10))
    
    # White icon and title
    white_icon = tk.Label(
        white_title_frame,
        text="♔",  # White king symbol
        font=("Segoe UI", 16),
        bg="white",
        fg="#333333"
    )
    white_icon.pack(side=tk.LEFT, padx=(0, 5))
    
    tk.Label(
        white_title_frame,
        text="DIFFICULTÉ BLANCS",
        font=("Segoe UI", 10, "bold"),
        bg="white",
        fg="#333333"
    ).pack(side=tk.LEFT)
    
    # White difficulty meter
    white_difficulty_value = white_difficulty.get("overall_difficulty", 5)
    _create_player_difficulty_meter(white_diff_frame, white_difficulty_value, text_font)
    
    # Create black difficulty panel
    black_diff_frame = tk.Frame(players_difficulty_frame, bg="white", padx=10)
    black_diff_frame.grid(row=0, column=1, sticky="nsew")
    
    # Black difficulty title
    black_title_frame = tk.Frame(black_diff_frame, bg="white")
    black_title_frame.pack(fill=tk.X, pady=(0, 10))
    
    # Black icon and title
    black_icon = tk.Label(
        black_title_frame,
        text="♚",  # Black king symbol
        font=("Segoe UI", 16),
        bg="white",
        fg="#333333"
    )
    black_icon.pack(side=tk.LEFT, padx=(0, 5))
    
    tk.Label(
        black_title_frame,
        text="DIFFICULTÉ NOIRS",
        font=("Segoe UI", 10, "bold"),
        bg="white",
        fg="#333333"
    ).pack(side=tk.LEFT)
    
    # Black difficulty meter
    black_difficulty_value = black_difficulty.get("overall_difficulty", 5)
    _create_player_difficulty_meter(black_diff_frame, black_difficulty_value, text_font)
    
    # Factors section - split into tabs for White/Black
    factors_frame = tk.Frame(difficulty_card, bg="white")
    factors_frame.pack(fill=tk.X, pady=(15, 0))
    
    # Title for factors
    tk.Label(
        factors_frame,
        text="FACTEURS DE DIFFICULTÉ",
        font=("Segoe UI", 10, "bold"),
        bg="white",
        fg="#333333"
    ).pack(anchor="w", pady=(0, 10))
    
    # Create tabs for White and Black factors
    factors_tabs_frame = tk.Frame(factors_frame, bg="white")
    factors_tabs_frame.pack(fill=tk.X)
    
    # Tab buttons
    tabs_button_frame = tk.Frame(factors_tabs_frame, bg="white")
    tabs_button_frame.pack(fill=tk.X)
    
    # Content frames
    white_factors_content = tk.Frame(factors_tabs_frame, bg="white")
    black_factors_content = tk.Frame(factors_tabs_frame, bg="white")
    
    # Track active tab
    active_tab = tk.StringVar(value="white")
    
    # Function to switch tabs
    def switch_tab(tab):
        active_tab.set(tab)
        if tab == "white":
            white_tab_btn.config(bg="#3F51B5", fg="white")
            black_tab_btn.config(bg="#F0F2F5", fg="#333333")
            black_factors_content.pack_forget()
            white_factors_content.pack(fill=tk.X)
        else:
            white_tab_btn.config(bg="#F0F2F5", fg="#333333")
            black_tab_btn.config(bg="#3F51B5", fg="white")
            white_factors_content.pack_forget()
            black_factors_content.pack(fill=tk.X)
    
    # Tab buttons
    white_tab_btn = tk.Button(
        tabs_button_frame,
        text="BLANCS",
        font=("Segoe UI", 9),
        bg="#3F51B5", fg="white",
        relief="flat",
        padx=15, pady=5,
        command=lambda: switch_tab("white")
    )
    white_tab_btn.pack(side=tk.LEFT)
    
    black_tab_btn = tk.Button(
        tabs_button_frame,
        text="NOIRS",
        font=("Segoe UI", 9),
        bg="#F0F2F5", fg="#333333",
        relief="flat",
        padx=15, pady=5,
        command=lambda: switch_tab("black")
    )
    black_tab_btn.pack(side=tk.LEFT)
    
    # Nice labels for the factors
    factor_labels = {
        "decision_difficulty": "Complexité Décisionnelle",
        "positional_difficulty": "Complexité Positionnelle",
        "tactical_difficulty": "Complexité Tactique",
        "defensive_difficulty": "Difficulté Défensive",
        "concrete_difficulty": "Calculs Concrets"
    }
    
    # Pack the white factors content initially
    white_factors_content.pack(fill=tk.X, pady=10)
    
    # Create white factors bars
    white_factors = white_difficulty.get("difficulty_factors", {})
    for factor, label in factor_labels.items():
        value = white_factors.get(factor, 5.0)
        _create_factor_bar(white_factors_content, label, value, text_font)
    
    # Create black factors bars (initially hidden)
    black_factors = black_difficulty.get("difficulty_factors", {})
    for factor, label in factor_labels.items():
        value = black_factors.get(factor, 5.0)
        _create_factor_bar(black_factors_content, label, value, text_font)

def _create_difficulty_meter(parent, difficulty_value, title, text_font):
    """Create an attractive circular meter to display the difficulty value."""
    # Frame for the meter
    meter_frame = tk.Frame(parent, bg="white")
    meter_frame.pack(pady=10, anchor="center")
    
    # Size parameters
    meter_size = 150
    
    # Create canvas for drawing
    canvas = tk.Canvas(
        meter_frame, 
        width=meter_size, 
        height=meter_size, 
        bg="white",
        highlightthickness=0
    )
    canvas.pack(anchor="center")
    
    # Draw outer circle
    canvas.create_oval(10, 10, meter_size-10, meter_size-10, 
                      outline="#E0E0E0", width=10, fill="white")
    
    # Determine color based on difficulty
    if difficulty_value <= 3.0:
        color = "#4CAF50"  # Green for easy
    elif difficulty_value <= 6.0:
        color = "#FFC107"  # Yellow for medium
    else:
        color = "#F44336"  # Red for hard
    
    # Calculate arc extent (0-10 scale to 0-360 degrees)
    arc_extent = min(difficulty_value * 36, 360)  # Each point = 36 degrees
    
    # Draw colored arc
    canvas.create_arc(
        10, 10, meter_size-10, meter_size-10,
        start=90, extent=-arc_extent,
        outline=color, width=10, style="arc"
    )
    
    # Add difficulty value text
    canvas.create_text(
        meter_size//2, meter_size//2,
        text=f"{difficulty_value}",
        font=("Segoe UI", 24, "bold"),
        fill=color
    )
    
    # Add "sur 10" text below
    canvas.create_text(
        meter_size//2, meter_size//2 + 30,
        text="sur 10",
        font=("Segoe UI", 12),
        fill="#757575"
    )
    
    # Title below the meter
    tk.Label(
        meter_frame,
        text=title,
        font=("Segoe UI", 11, "bold"),
        bg="white",
        fg="#333333"
    ).pack(pady=(5, 0))

def _create_phase_difficulty_meter(parent, difficulty_value, title, column, text_font):
    """Create a smaller meter for phase difficulties."""
    # Frame for each phase
    phase_frame = tk.Frame(parent, bg="white", padx=5)
    phase_frame.grid(row=0, column=column, sticky="nsew")
    
    # Determine color based on difficulty
    if difficulty_value <= 3.0:
        color = "#4CAF50"  # Green for easy
    elif difficulty_value <= 6.0:
        color = "#FFC107"  # Yellow for medium
    else:
        color = "#F44336"  # Red for hard
    
    # Title
    tk.Label(
        phase_frame,
        text=title,
        font=("Segoe UI", 9, "bold"),
        bg="white",
        fg="#333333"
    ).pack(anchor="center", pady=(0, 5))
    
    # Progress bar style meter
    bar_container = tk.Frame(
        phase_frame, 
        bg="#F5F5F5", 
        height=15,
        width=100
    )
    bar_container.pack(anchor="center", pady=5)
    bar_container.pack_propagate(False)
    
    # Filled portion of the bar
    filled_width = min(difficulty_value * 10, 100)  # Scale to 0-100 width
    if filled_width > 0:
        filled_bar = tk.Frame(
            bar_container, 
            bg=color, 
            height=15,
            width=filled_width
        )
        filled_bar.pack(side=tk.LEFT, anchor="w")
    
    # Value text
    tk.Label(
        phase_frame,
        text=f"{difficulty_value}/10",
        font=("Segoe UI", 12, "bold"),
        bg="white",
        fg=color
    ).pack(anchor="center", pady=5)

def _create_factor_bar(parent, factor_name, factor_value, text_font):
    """Create a horizontal bar to display a difficulty factor."""
    # Row container
    factor_frame = tk.Frame(parent, bg="white")
    factor_frame.pack(fill=tk.X, pady=3)
    
    # Factor name
    tk.Label(
        factor_frame,
        text=factor_name,
        font=("Segoe UI", 9),
        bg="white",
        fg="#333333",
        width=20,
        anchor="w"
    ).pack(side=tk.LEFT, padx=(0, 10))
    
    # Bar container
    bar_container = tk.Frame(
        factor_frame, 
        bg="#F5F5F5", 
        height=15,
        width=200
    )
    bar_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
    bar_container.pack_propagate(False)
    
    # Determine color based on value
    if factor_value <= 3.0:
        color = "#4CAF50"  # Green for easy
    elif factor_value <= 6.0:
        color = "#FFC107"  # Yellow for medium
    else:
        color = "#F44336"  # Red for hard
    
    # Filled portion of the bar
    filled_width = min(factor_value * 20, 200)  # Scale to 0-200 width
    if filled_width > 0:
        filled_bar = tk.Frame(
            bar_container, 
            bg=color, 
            height=15,
            width=filled_width
        )
        filled_bar.pack(side=tk.LEFT, anchor="w")
    
    # Value text
    tk.Label(
        factor_frame,
        text=f"{factor_value}",
        font=("Segoe UI", 9, "bold"),
        bg="white",
        fg=color,
        width=4
    ).pack(side=tk.RIGHT)

def _create_player_difficulty_meter(parent, difficulty_value, text_font):
    """Create a medium-sized meter for player-specific difficulty."""
    # Container for the meter
    meter_frame = tk.Frame(parent, bg="white")
    meter_frame.pack(pady=5, anchor="center")
    
    # Size parameters - smaller than main difficulty meter
    meter_size = 120
    
    # Create canvas for drawing
    canvas = tk.Canvas(
        meter_frame, 
        width=meter_size, 
        height=meter_size, 
        bg="white",
        highlightthickness=0
    )
    canvas.pack(anchor="center")
    
    # Draw outer circle
    canvas.create_oval(10, 10, meter_size-10, meter_size-10, 
                      outline="#E0E0E0", width=8, fill="white")
    
    # Determine color based on difficulty
    if difficulty_value <= 3.0:
        color = "#4CAF50"  # Green for easy
    elif difficulty_value <= 6.0:
        color = "#FFC107"  # Yellow for medium
    else:
        color = "#F44336"  # Red for hard
    
    # Calculate arc extent (0-10 scale to 0-360 degrees)
    arc_extent = min(difficulty_value * 36, 360)  # Each point = 36 degrees
    
    # Draw colored arc
    canvas.create_arc(
        10, 10, meter_size-10, meter_size-10,
        start=90, extent=-arc_extent,
        outline=color, width=8, style="arc"
    )
    
    # Add difficulty value text
    canvas.create_text(
        meter_size//2, meter_size//2,
        text=f"{difficulty_value}",
        font=("Segoe UI", 20, "bold"),
        fill=color
    )
    
    # Add "sur 10" text below
    canvas.create_text(
        meter_size//2, meter_size//2 + 25,
        text="sur 10",
        font=("Segoe UI", 10),
        fill="#757575"
    )