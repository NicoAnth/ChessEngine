"""
Resource loader utility for the chess application.
Handles loading images and other resources.
"""

import sys
import os
from PIL import Image, ImageTk, ImageFilter, ImageEnhance

def resource_path(relative_path):
    """Get absolute path to resource, handles PyInstaller path resolution"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    return os.path.join(base_path, relative_path)

def load_piece_images(square_size):
    """
    Loads and prepares chess piece images.
    
    Args:
        square_size: Size of the chess square to scale pieces appropriately
    
    Returns:
        Dictionary mapping piece names to prepared ImageTk objects
    """
    pieces = ['black-pawn', 'black-rook', 'black-knight', 'black-bishop', 'black-queen', 'black-king',
              'white-pawn', 'white-rook', 'white-knight', 'white-bishop', 'white-queen', 'white-king']
    images = {}
    
    # Create slightly larger pieces for better visual quality
    size_factor = 0.85  # Pieces take up 85% of square size
    piece_size = int(square_size * size_factor)
    
    for piece in pieces:
        image_path = resource_path(f"images/{piece}.png")
        image = Image.open(image_path).convert("RGBA")
        
        # Apply subtle enhancements for better visuals
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)  # Slightly increase contrast
        
        # Resize with high quality
        image = image.resize((piece_size, piece_size), Image.Resampling.LANCZOS)
        
        # Apply slight shadow effect for 3D look
        shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        shadow_intensity = 50  # Subtle shadow
        shadow.paste((0, 0, 0, shadow_intensity), (2, 2, image.width, image.height))
        shadow = shadow.filter(ImageFilter.GaussianBlur(2))
        
        # Create final image
        final_image = Image.new("RGBA", image.size, (0, 0, 0, 0))
        final_image.paste(shadow, (0, 0), shadow)
        final_image.paste(image, (0, 0), image)
        
        images[piece] = ImageTk.PhotoImage(final_image)
    return images

def load_app_icon(window):
    """
    Load and set the application window icon.
    
    Args:
        window: The tkinter window to apply the icon to
    """
    try:
        from PIL import Image, ImageTk
        import os
        
        # Define icon paths
        icon_path = None
        
        # Check platform-specific icon formats
        if os.name == 'nt':  # Windows
            icon_path = resource_path("images/caissablackt.ico")
            if os.path.exists(icon_path):
                window.iconbitmap(icon_path)
                return
        
        # For all platforms (or as fallback) - PNG format
        icon_path = resource_path("images/chess_icon.png")
        if os.path.exists(icon_path):
            icon_img = Image.open(icon_path)
            icon_tk = ImageTk.PhotoImage(icon_img)
            window.iconphoto(True, icon_tk)
            return
            
        print("No icon found at paths:", icon_path)
    except Exception as e:
        print(f"Could not set application icon: {e}")