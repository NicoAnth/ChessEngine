"""Shared metrics visualization components for chess analysis."""

import tkinter as tk
from tkinter import font
from src.utils import config

def _create_accuracy_chart(view_instance, parent_frame, accuracy, is_white=True):
    """Create a circular accuracy indicator with modern design.
    
    Args:
        view_instance: The GameAnalysisView instance
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

def _create_metric_box(view_instance, parent, label, value, column, color):
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

def _create_enhanced_move_quality_display(view_instance, parent_frame, stats, text_font):
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
    _create_metric_box(
        view_instance,
        key_stats_frame, 
        "Meilleurs coups", 
        f"{best_move_pct}%", 
        0,
        "#4285F4"  # Blue 
    )
    
    # Create metric box for Accuracy (if you want to include it alongside the circle)
    _create_metric_box(
        view_instance,
        key_stats_frame, 
        "Précision", 
        f"{accuracy}%", 
        1,
        "#34A853"  # Green
    )
    
    # Create metric box for Critical Accuracy if available
    if "critical_accuracy" in stats:
        _create_metric_box(
            view_instance,
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
        cls_color = view_instance.game_analyzer.get_classification_color(cls)
        
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