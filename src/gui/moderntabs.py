import tkinter as tk
from tkinter import ttk, font
from src.utils import config

class ModernTabs(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.configure(bg=config.COLORS["background"])
        
        # Frame to hold tab buttons
        self.tab_frame = tk.Frame(self, bg=config.COLORS["background"])
        self.tab_frame.pack(fill=tk.X, side=tk.TOP)
        
        # Add a separator line below the tabs
        self.separator = tk.Frame(self, height=1, bg=config.COLORS["profile_border"])
        self.separator.pack(fill=tk.X, side=tk.TOP)
        
        # Frame to hold content with padding
        self.content_frame = tk.Frame(self, bg=config.COLORS["background"], padx=10, pady=15)
        self.content_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        self.tabs = {}
        self.current_tab = None
        self.animation_running = False
        
    def add_tab(self, title, content_frame):
        """Add a new tab with associated content frame"""
        
        # Create button for this tab
        tab_button = tk.Button(
            self.tab_frame,
            text=title,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            font=("Segoe UI", 10),
            bg=config.COLORS["tab_background"],
            fg=config.COLORS["tab_text"],
            activebackground=config.COLORS["tab_selected_background"],
            activeforeground=config.COLORS["tab_selected_text"],
            padx=15,
            pady=8,
            command=lambda: self.show_tab(title)
        )
        
        # Add underline for selected tab
        underline = tk.Frame(
            self.tab_frame, 
            height=3, 
            bg=config.COLORS["tab_underline"]
        )
        
        # Store references
        self.tabs[title] = {
            "button": tab_button,
            "underline": underline,
            "content": content_frame
        }
        
        # Position the button and underline
        tab_button.pack(side=tk.LEFT, padx=(5, 5), pady=(5, 0))
        
        # Update underlines after all tabs are added
        self.after(10, self._update_underline_positions)
        
        # Configure content frame
        content_frame.pack_forget()  # Hide initially
        
        # Ensure the content frame is a child of self.content_frame
        if content_frame.master != self.content_frame:
            content_frame.master = self.content_frame
        
        # If this is the first tab, show it
        if self.current_tab is None:
            self.show_tab(title)
    
    def _update_underline_positions(self):
        """Update the position of all underlines based on button positions"""
        for title, tab in self.tabs.items():
            button = tab["button"]
            underline = tab["underline"]
            
            # Place underline beneath its button
            underline.place(
                x=button.winfo_x(),
                y=button.winfo_y() + button.winfo_height(),
                width=button.winfo_width()
            )
    
    def _animate_underline(self, underline, target_x, target_width, steps=10):
        """Animate the underline to its new position"""
        if self.animation_running:
            return
            
        self.animation_running = True
        
        # Get current position
        current_x = underline.place_info().get('x')
        if current_x:
            current_x = int(float(current_x))
        else:
            current_x = 0
            
        current_width = underline.place_info().get('width')
        if current_width:
            current_width = int(float(current_width))
        else:
            current_width = 0
        
        # Calculate step sizes
        x_step = (target_x - current_x) / steps
        width_step = (target_width - current_width) / steps
        
        def animate_step(step):
            if step > steps:
                self.animation_running = False
                return
                
            # Update position and width
            new_x = current_x + (x_step * step)
            new_width = current_width + (width_step * step)
            
            underline.place(
                x=new_x,
                y=underline.place_info().get('y'),
                width=new_width
            )
            
            # Schedule next step
            self.after(10, lambda: animate_step(step + 1))
        
        # Start animation
        animate_step(1)
    
    def show_tab(self, title):
        """Switch to the specified tab with a smooth animation"""
        
        # If already on this tab, do nothing
        if self.current_tab == title:
            return
            
        # Hide current tab content if any
        if self.current_tab:
            current_button = self.tabs[self.current_tab]["button"]
            current_underline = self.tabs[self.current_tab]["underline"]
            
            # Update button appearance
            current_button.configure(
                bg=config.COLORS["tab_background"],
                fg=config.COLORS["tab_text"]
            )
            
            # Hide the content
            self.tabs[self.current_tab]["content"].pack_forget()
            
        # Get new tab elements
        new_button = self.tabs[title]["button"]
        new_underline = self.tabs[title]["underline"]
        
        # Update button appearance
        new_button.configure(
            bg=config.COLORS["tab_selected_background"],
            fg=config.COLORS["tab_selected_text"]
        )
        
        # Show new tab content with a slight fade effect
        new_content = self.tabs[title]["content"]
        new_content.pack(fill=tk.BOTH, expand=True, in_=self.content_frame)
        
        # Set the underline color
        new_underline.configure(bg=config.COLORS["profile_accent"])
        
        # Animate the underline position
        self._animate_underline(
            new_underline,
            new_button.winfo_x(),
            new_button.winfo_width()
        )
        
        # Update current tab
        self.current_tab = title