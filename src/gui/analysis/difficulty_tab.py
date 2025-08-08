"""Difficulty tab components for chess analysis."""

import tkinter as tk
from tkinter import font

from src.utils import config
from src.gui.analysis.summary_tab import _create_difficulty_metrics_display


def _create_difficulty_tab_content(parent_frame, difficulty_metrics, title_font, subheader_font, text_font):
    """Populate the 'Difficulté' tab with a scrollable difficulty metrics view.

    Args:
        parent_frame: The tk.Frame that represents the tab content area.
        difficulty_metrics: Dict with overall/white/black difficulty and factors.
        title_font: tk.font.Font for section titles.
        subheader_font: tk.font.Font for sub headers.
        text_font: tk.font.Font for regular text.
    """
    # Create scrollable canvas with modern styling
    canvas_frame = tk.Frame(parent_frame, bg=config.COLORS["background"])\

    canvas_frame.pack(fill=tk.BOTH, expand=True)

    difficulty_canvas = tk.Canvas(
        canvas_frame,
        bg=config.COLORS["background"],
        highlightthickness=0,
        bd=0,
    )

    # Modern scrollbar
    scrollbar = tk.Scrollbar(
        canvas_frame,
        orient="vertical",
        command=difficulty_canvas.yview,
        width=10,
        bd=0,
        highlightthickness=0,
        troughcolor="#EAEAEA",
        bg=config.COLORS["background"],
        activebackground=config.COLORS["selected_square"],
    )

    # Inner content frame
    content_frame = tk.Frame(difficulty_canvas, bg=config.COLORS["background"], padx=15, pady=10)

    # Configure scrolling
    content_frame.bind(
        "<Configure>",
        lambda e: difficulty_canvas.configure(scrollregion=difficulty_canvas.bbox("all")),
    )

    # Mouse wheel helpers
    def _on_mousewheel(event):
        difficulty_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_linux_scroll_up(event):
        difficulty_canvas.yview_scroll(-1, "units")

    def _on_linux_scroll_down(event):
        difficulty_canvas.yview_scroll(1, "units")

    # Bind mouse wheel events
    difficulty_canvas.bind("<MouseWheel>", _on_mousewheel)
    content_frame.bind("<MouseWheel>", _on_mousewheel)
    difficulty_canvas.bind("<Button-4>", _on_linux_scroll_up)
    difficulty_canvas.bind("<Button-5>", _on_linux_scroll_down)
    content_frame.bind("<Button-4>", _on_linux_scroll_up)
    content_frame.bind("<Button-5>", _on_linux_scroll_down)

    # Ensure canvas can receive focus for mouse wheel events
    difficulty_canvas.bind("<Enter>", lambda event: difficulty_canvas.focus_set())

    # Resize binding for canvas window
    def resize_canvas(event):
        canvas_width = event.width
        difficulty_canvas.itemconfig(window_id, width=canvas_width)

    difficulty_canvas.bind("<Configure>", resize_canvas)
    window_id = difficulty_canvas.create_window((0, 0), window=content_frame, anchor="nw")
    difficulty_canvas.configure(yscrollcommand=scrollbar.set)

    # Pack canvas and scrollbar
    difficulty_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Title
    title_container = tk.Frame(content_frame, bg=config.COLORS["background"])
    title_container.pack(fill=tk.X, pady=(0, 10))

    tk.Label(
        title_container,
        text="DIFFICULTÉ DE LA PARTIE",
        font=title_font,
        bg=config.COLORS["background"],
        fg=config.COLORS["primary_text"],
        pady=5,
    ).pack(anchor="center")

    separator = tk.Frame(title_container, height=2, bg=config.COLORS["selected_square"])
    separator.pack(fill=tk.X, padx=50)

    # Content
    if difficulty_metrics:
        _create_difficulty_metrics_display(content_frame, difficulty_metrics, title_font, subheader_font, text_font)
    else:
        empty = tk.Frame(content_frame, bg="white", padx=20, pady=20, highlightthickness=1, highlightbackground="#E0E0E0")
        empty.pack(fill=tk.X, pady=(10, 20))
        tk.Label(
            empty,
            text="Aucune métrique de difficulté disponible pour cette partie.",
            font=text_font,
            bg="white",
            fg=config.COLORS["secondary_text"],
        ).pack(anchor="w")
