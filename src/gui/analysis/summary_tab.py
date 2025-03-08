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
    _create_game_evolution_chart(view_instance,chart_container, move_evaluations, title_font, subheader_font)
    
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