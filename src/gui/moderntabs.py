import tkinter as tk
from tkinter import ttk, font
from src.utils import config

class ModernTabs(tk.Frame):
    def __init__(self, parent, tab_bg_color=None, tab_text_color=None, 
                 tab_active_bg=None, tab_active_text_color=None, tab_font=None, 
                 *args, **kwargs):
            # Extract custom tab styling arguments
            self.tab_bg_color = tab_bg_color or config.COLORS.get("tab_background", "#E0E0E0")
            self.tab_text_color = tab_text_color or config.COLORS.get("tab_text", "#333333")
            self.tab_active_bg = tab_active_bg or config.COLORS.get("tab_selected_background", "#FFFFFF")
            self.tab_active_text_color = tab_active_text_color or config.COLORS.get("tab_selected_text", "#000000")
            self.tab_font = tab_font or font.Font(family="Segoe UI", size=10)

            # Call Frame.__init__ without the custom arguments
            tk.Frame.__init__(self, parent, *args, **kwargs)
            self.parent = parent
            # Use the main background color passed via kwargs or default
            self.configure(bg=kwargs.get('bg', config.COLORS["background"]))

            # Frame to hold tab buttons
            self.tab_frame = tk.Frame(self, bg=kwargs.get('bg', config.COLORS["background"]))

            # Add a separator line above the tabs
            self.separator = tk.Frame(self, height=1, bg=config.COLORS["profile_border"])
            self.separator.pack(fill=tk.X, side=tk.TOP, pady=(0, 5))  # Add some padding below separator

            # Pack tab_frame now
            self.tab_frame.pack(fill=tk.X, side=tk.TOP)

            # Frame to hold content with padding
            self.content_frame = tk.Frame(self, bg=kwargs.get('bg', config.COLORS["background"]), padx=10, pady=15)
            self.content_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

            self.tabs = {}
            self.current_tab = None
            self.animation_running = False
            self.underline_height = 3  # Define underline height
            # Flag to ensure only the first tab triggers the initial auto-selection
            self._initial_tab_scheduled = False
        
    def add_tab(self, title, content_frame):
        """Add a new tab with associated content frame"""
        
        # Create button for this tab using stored styles
        tab_button = tk.Button(
            self.tab_frame,
            text=title,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            font=self.tab_font, # Use stored font
            bg=self.tab_bg_color, # Use stored background color
            fg=self.tab_text_color, # Use stored text color
            activebackground=self.tab_active_bg, # Use stored active background
            activeforeground=self.tab_active_text_color, # Use stored active text color
            padx=15,
            pady=8,
            command=lambda: self.show_tab(title)
        )
        
        # Add underline for selected tab
        underline = tk.Frame(
            self.tab_frame, 
            height=self.underline_height, 
            bg=self.cget('bg') # Use the frame's background color initially
        )
        
        # Store references
        self.tabs[title] = {
            "button": tab_button,
            "underline": underline,
            "content": content_frame
        }
        
        # Position the button
        tab_button.pack(side=tk.LEFT, padx=(5, 5), pady=(self.underline_height + 2, 0))  # Add padding top for underline
        
        # Update underlines after a delay to ensure buttons have geometry
        self.after(50, self._update_underline_positions)
        
        # Configure content frame - always hide initially
        if content_frame.winfo_parent() != str(self.content_frame):
            print(f"Warning: Tab content frame for '{title}' should be created with ModernTabs.content_frame as parent")
        content_frame.pack_forget()
        
        # If this is the first tab added, schedule its display once (avoid race selecting last tab)
        if not self._initial_tab_scheduled:
            self._initial_tab_scheduled = True
            self.after(100, lambda t=title: self.show_tab(t))
    
    def _update_underline_positions(self):
        """Update the position of all underlines based on button positions"""
        self.update_idletasks()  # Ensure geometry is calculated
        for title, tab in self.tabs.items():
            button = tab["button"]
            underline = tab["underline"]
            
            # Place underline ABOVE its button
            underline.place(
                x=button.winfo_x(),
                y=button.winfo_y() - self.underline_height - 2,  # Position above button
                width=button.winfo_width()
            )
            # Ensure underline is visible (might be hidden initially)
            underline.lift()
    
    def _animate_underline(self, underline, target_x, target_width, steps=10):
        """Animate the underline to its new position"""
        if self.animation_running:
            return
            
        self.animation_running = True
        self.update_idletasks()  # Ensure geometry is up-to-date
        
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
        
        current_y = underline.place_info().get('y')
        if current_y:
            current_y = int(float(current_y))
        else:
            current_y = 0
        
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
                y=current_y,  # Keep Y constant
                width=new_width
            )
            
            # Schedule next step
            self.after(15, lambda: animate_step(step + 1))  # Slightly slower animation
        
        # Start animation
        animate_step(1)
    
    def show_tab(self, title):
        """Switch to the specified tab with a smooth animation"""
        if self.current_tab == title:
            return
            
        self.update_idletasks()  # Ensure widgets have geometry info
            
        # Hide current tab content and reset its underline
        if self.current_tab:
            current_tab_data = self.tabs[self.current_tab]
            current_button = current_tab_data["button"]
            current_underline = current_tab_data["underline"]
            
            current_button.configure(
                bg=self.tab_bg_color, # Use stored background color
                fg=self.tab_text_color # Use stored text color
            )
            # Reset underline color to background
            current_underline.configure(bg=self.cget('bg')) # Use the frame's background color
            
            current_tab_data["content"].pack_forget()
            
        # Get new tab elements
        new_tab_data = self.tabs[title]
        new_button = new_tab_data["button"]
        new_underline = new_tab_data["underline"]
        new_content = new_tab_data["content"]
        
        # Update new button appearance
        new_button.configure(
            bg=self.tab_active_bg, # Use stored active background
            fg=self.tab_active_text_color # Use stored active text color
        )
        
        # Show new tab content
        new_content.pack(fill=tk.BOTH, expand=True, in_=self.content_frame)
        
        # Set the new underline color
        new_underline.configure(bg=config.COLORS["profile_accent"])
        new_underline.lift()  # Ensure it's visible
        
        # Animate the underline to the new button's position
        self.update_idletasks()
        # Check if button has valid geometry before animating
        if new_button.winfo_exists() and new_button.winfo_width() > 0:
            self._animate_underline(
                new_underline,
                new_button.winfo_x(),
                new_button.winfo_width()
            )
        else:
             # If geometry not ready, place directly without animation
             new_underline.place(
                 x=new_button.winfo_x(),
                 y=new_button.winfo_y() - self.underline_height - 2,
                 width=new_button.winfo_width()
             )

        # Update current tab
        self.current_tab = title
        
        # Final update to ensure layout is correct
        self.update_idletasks()

        # Rebind global mouse wheel to the newly activated tab if it exposes a binding method
        try:
            if hasattr(new_content, "_bind_global_wheel") and callable(getattr(new_content, "_bind_global_wheel")):
                new_content._bind_global_wheel()
        except Exception as e:
            print(f"Scroll rebind warning for tab '{title}': {e}")