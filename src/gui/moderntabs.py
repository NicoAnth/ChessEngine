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
        
        # Frame to hold content
        self.content_frame = tk.Frame(self, bg=config.COLORS["background"])
        self.content_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        self.tabs = {}
        self.current_tab = None
        
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
        underline.place(
            x=tab_button.winfo_x(), 
            y=tab_button.winfo_y() + tab_button.winfo_height(), 
            width=tab_button.winfo_width()
        )
        
        # Configure content frame
        content_frame.pack_forget()  # Hide initially
        
        # Ensure the content frame is a child of self.content_frame
        if content_frame.master != self.content_frame:
            content_frame.master = self.content_frame
        
        # If this is the first tab, show it
        if self.current_tab is None:
            self.show_tab(title)
    
    def show_tab(self, title):
        """Switch to the specified tab"""
        
        # Hide current tab content if any
        if self.current_tab:
            self.tabs[self.current_tab]["content"].pack_forget()
            self.tabs[self.current_tab]["button"].configure(
                bg=config.COLORS["tab_background"],
                fg=config.COLORS["tab_text"]
            )
            self.tabs[self.current_tab]["underline"].configure(
                bg=config.COLORS["tab_underline"]
            )
            
        # Show new tab content
        self.tabs[title]["content"].pack(fill=tk.BOTH, expand=True, in_=self.content_frame)
        self.tabs[title]["button"].configure(
            bg=config.COLORS["tab_selected_background"],
            fg=config.COLORS["tab_selected_text"]
        )
        self.tabs[title]["underline"].configure(
            bg=config.COLORS["tab_selected_underline"]
        )
        
        # Update current tab
        self.current_tab = title