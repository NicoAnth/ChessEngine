"""Shared metrics visualization components for chess analysis."""

import tkinter as tk

def _create_accuracy_chart(view_instance, parent_frame, accuracy, is_white=True):
    """Create a circular accuracy indicator with modern design."""
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
    radius = size/2 - 10
    thickness = 8
    
    # Draw background circle
    bg_color = "#F0F0F0"
    canvas.create_oval(
        center_x - radius, 
        center_y - radius, 
        center_x + radius, 
        center_y + radius, 
        outline=bg_color, 
        width=thickness
    )
    
    # Choose color based on accuracy
    if accuracy < 50:
        fill_color = "#FF6B6B" if is_white else "#E84855"
    elif accuracy < 75:
        fill_color = "#FFD166" if is_white else "#EFCA08"
    else:
        fill_color = "#06D6A0" if is_white else "#0CB69A"
    
    # Draw the filled progress arc
    canvas.create_arc(
        center_x - radius, 
        center_y - radius, 
        center_x + radius, 
        center_y + radius,
        start=90,
        extent=-accuracy * 3.6,  # Convert percentage to degrees
        outline=fill_color,
        style="arc",
        width=thickness
    )
    
    # Display accuracy percentage and label
    canvas.create_text(
        center_x,
        center_y - 10,
        text=f"{int(accuracy)}%",
        font=("Segoe UI", 22, "bold"),
        fill="#333333"
    )
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
    # Add key metrics in highlighted boxes
    key_stats_frame = tk.Frame(parent_frame, bg="white")
    key_stats_frame.pack(fill=tk.X, pady=(0, 15))
    
    # Configure columns
    key_stats_frame.columnconfigure(0, weight=1)
    key_stats_frame.columnconfigure(1, weight=1)
    if "critical_accuracy" in stats:
        key_stats_frame.columnconfigure(2, weight=1)
    
    # Create metric boxes for key stats
    _create_metric_box(
        view_instance,
        key_stats_frame, 
        "Meilleurs coups", 
        f"{stats.get('best_move_percentage', 0)}%", 
        0,
        "#4285F4"
    )
    
    _create_metric_box(
        view_instance,
        key_stats_frame, 
        "Précision", 
        f"{stats.get('accuracy', 0)}%", 
        1,
        "#34A853"
    )
    
    if "critical_accuracy" in stats:
        _create_metric_box(
            view_instance,
            key_stats_frame, 
            "Précision critique", 
            f"{stats.get('critical_accuracy', 0)}%", 
            2,
            "#FBBC05"
        )
    
    # Skip if no counts data
    counts = stats.get("counts", {})
    if not counts:
        return
    
    # Container for distribution
    dist_frame = tk.Frame(parent_frame, bg="white")
    dist_frame.pack(fill=tk.X, pady=(0, 10))
    
    # Ordered classifications
    ordered_classifications = [
        "Excellent", "Bon coup", "Imprécision", "Erreur", "Grosse erreur"
    ]
    
    # Only include classifications that exist in the data
    classifications = [cls for cls in ordered_classifications if cls in counts]
    
    # Total moves for percentage calculation
    total_moves = stats["total_moves"]
    
    # Create quality bars
    for cls in classifications:
        count = counts.get(cls, 0)
        if total_moves <= 0:
            percentage = 0
        else:
            percentage = round((count / total_moves * 100))
        
        # Classification row
        cls_frame = tk.Frame(dist_frame, bg="white")
        cls_frame.pack(fill=tk.X, pady=4)
        
        # Get color for this classification
        cls_color = view_instance.game_analyzer.get_classification_color(cls)
        
        # Color indicator
        tk.Frame(cls_frame, width=6, height=20, bg=cls_color).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        
        # Classification name
        tk.Label(
            cls_frame, 
            text=cls, 
            width=12, 
            anchor="w", 
            font=text_font,
            bg="white", 
            fg="#333333"
        ).pack(side=tk.LEFT)
        
        # Progress bar container
        bar_container = tk.Frame(cls_frame, bg="#F0F0F0", height=20, width=150)
        bar_container.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        bar_container.pack_propagate(False)
        
        if percentage > 0:
            # Color bar showing percentage
            bar = tk.Frame(bar_container, bg=cls_color, height=20)
            bar.place(relx=0, rely=0, relwidth=percentage/100, relheight=1.0)
            
            # Percentage text - inside bar if wide enough, outside if narrow
            if percentage >= 18:
                tk.Label(
                    bar,
                    text=f"{percentage}%",
                    font=("Segoe UI", 9),
                    bg=cls_color,
                    fg="white"
                ).place(relx=0.5, rely=0.5, anchor="center")
            else:
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