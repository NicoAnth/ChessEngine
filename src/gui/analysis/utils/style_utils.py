"""Style utility functions for chess analysis UI components."""

import tkinter as tk
from src.utils import config


def update_card_appearance(card, bg_color, text_color, preserve_quality=False):
    """Update card appearance with consistent styling.
    
    Args:
        card: The card frame to update
        bg_color: Background color to apply
        text_color: Text color to apply
        preserve_quality: Whether to preserve quality indicator colors
    """
    if not card or not hasattr(card, 'labels'):
        return
        
    # Update card background
    card.config(bg=bg_color)
    
    # Update all labels
    for label in card.labels:
        if hasattr(label, 'config'):
            try:
                # Update background color for all elements
                if label.winfo_class() == "Canvas":
                    label.config(bg=bg_color)
                    if hasattr(label, 'parent_frame'):
                        label.parent_frame.config(bg=bg_color)
                else:
                    label.config(bg=bg_color)
                    
                # Update text color for labels, preserving special colors when needed
                if label.winfo_class() == "Label" and hasattr(label, 'cget'):
                    label_text = label.cget('text')
                    
                    # For error cards, ensure we use high-contrast text colors
                    if card.error_active:
                        is_white = card.move_index % 2 == 0
                        
                        # Keep special quality indicator colors
                        if label_text in ["Excellent", "Bon coup", "Imprécision", "Erreur", "Grosse erreur"]:
                            # Keep current quality color
                            pass
                        # Keep score change parenthesis colors
                        elif label_text.startswith('(') and label_text.endswith(')'):
                            # Keep current score change color
                            pass
                        elif label.master and hasattr(label.master, 'winfo_class') and label.master.winfo_class() == "Frame":
                            # Check if part of best move indicator
                            for sibling in label.master.winfo_children():
                                if hasattr(sibling, 'cget') and sibling.winfo_class() == "Label" and sibling.cget('text') == "→":
                                    # Use a darker color for best move text that works on both backgrounds
                                    best_move_color = "#222222" if is_white else "#000000"
                                    label.config(fg=best_move_color)
                                    break
                            else:
                                # Regular text - use the error text color
                                label.config(fg=text_color)
                        else:
                            # Regular text - use the error text color
                            label.config(fg=text_color)
                    else:
                        # Normal non-error appearance - use the standard logic
                        is_white = card.move_index % 2 == 0
                        secondary_text_color = config.COLORS["white_move_secondary_text"] if is_white else config.COLORS["black_move_secondary_text"]
                        
                        for sibling in label.master.winfo_children():
                            if hasattr(sibling, 'cget') and hasattr(sibling, 'winfo_class'):
                                if sibling.winfo_class() == "Label" and sibling.cget('text') == "→":
                                    # This is secondary text, use appropriate color
                                    label.config(fg=secondary_text_color)
                                    break
                        else:
                            # Regular text
                            label.config(fg=text_color)
            except Exception as e:
                # Skip problematic widgets
                pass


def activate_error_card(card, classification):
    """Active l'apparence d'erreur sur une carte."""
    card.classification = classification  # Important de stocker la classification
    set_card_state(card, {'error_active': True})


def deactivate_error_card(card):
    """Désactive l'apparence d'erreur sur une carte."""
    set_card_state(card, {'error_active': False})


def ensure_error_icon(card, classification):
    """Ensure error icon is added to the card if needed."""
    # Check if icon already exists
    if hasattr(card, 'has_error_icon') and card.has_error_icon:
        return
        
    # Icon based on classification
    icon_text = "❌" if classification == "Grosse erreur" else "⚠️"
    
    # Find the quality label
    for label in card.labels:
        if hasattr(label, 'cget') and hasattr(label, 'winfo_class'):
            if label.winfo_class() == "Label" and label.cget('text') == classification:
                # Get the parent frame
                parent = label.master
                
                # Create icon next to quality label
                icon_label = tk.Label(
                    parent,
                    text=icon_text,
                    font=tk.font.Font(**config.FONTS["move_quality"]),
                    bg=card.cget('bg'),
                    fg=label.cget('fg')
                )
                icon_label.pack(side=tk.LEFT, padx=(0, 5))
                
                # Add to card labels for highlight management
                card.labels.append(icon_label)
                card.has_error_icon = True
                break


def add_error_icon(card, move_eval):
    """Add an error icon to a move card."""
    ensure_error_icon(card, move_eval["classification"])


def restore_original_colors(card):
    """Restore original colors for a card."""
    deactivate_error_card(card)

def set_card_state(card, states=None):
    """
    Fonction centrale qui gère tous les changements d'apparence des cartes.
    
    Args:
        card: La carte à modifier
        states: Dictionnaire des états à modifier {
            'selected': True/False, 
            'error_active': True/False,
            'hover': True/False
        }
    """
    # Mise à jour des états si fournis
    if states:
        if 'selected' in states:
            card.selected = states['selected']
        if 'error_active' in states:
            card.error_active = states['error_active']
        if 'hover' in states:
            card.hover_active = states.get('hover', False)
    
    # Déterminer l'état visuel selon la priorité:
    # 1. Erreur > 2. Sélection > 3. Survol > 4. Normal
    
    is_white = card.move_index % 2 == 0

    if card.error_active and card.selected:
        # Obtenir la configuration d'erreur
        error_config = config.ERROR_COLORS.get(card.classification, {})
        
        # Créer une variation plus intense de la couleur d'erreur pour montrer la sélection
        # Utiliser une couleur plus foncée ou avec une bordure visible
        bg_color = error_config.get("bg", "#FFCDD2")
        text_color = error_config.get("text", "#D32F2F")
        
        # Ajouter une bordure visible pour indiquer la sélection
        card.configure(highlightbackground=text_color, highlightthickness=2)
        
        # Mettre à jour l'apparence avec la couleur d'erreur
        update_card_appearance(card, bg_color, text_color, preserve_quality=True)
        return

    # Si juste en mode erreur (non sélectionné), supprimer la bordure spéciale si elle existe
    if card.error_active and not card.selected:
        card.configure(highlightthickness=1)
    
    # PRIORITÉ 1: ERREUR (plus haute priorité)
    if card.error_active:
        error_config = config.ERROR_COLORS.get(card.classification, {})
        
        # Si en survol sur une erreur
        if getattr(card, 'hover_active', False):
            bg_color = error_config.get("hover_bg", error_config.get("bg", "#FFCDD2"))
            text_color = error_config.get("hover_text", error_config.get("text", "#D32F2F"))
        else:
            bg_color = error_config.get("bg", "#FFCDD2") 
            text_color = error_config.get("text", "#D32F2F")
            
        update_card_appearance(card, bg_color, text_color, preserve_quality=True)
        return
        
    # PRIORITÉ 2: SÉLECTION
    if card.selected:
        bg_color = config.COLORS["white_move_highlight"] if is_white else config.COLORS["black_move_highlight"]
        text_color = config.COLORS["white_move_text"] if is_white else config.COLORS["black_move_text"]
        update_card_appearance(card, bg_color, text_color)
        return
        
    # PRIORITÉ 3: SURVOL
    if getattr(card, 'hover_active', False):
        bg_color = config.COLORS["white_move_hover"] if is_white else config.COLORS["black_move_hover"]
        text_color = config.COLORS["white_move_text"] if is_white else config.COLORS["black_move_text"]
        update_card_appearance(card, bg_color, text_color)
        return
        
    # PRIORITÉ 4: NORMAL (par défaut)
    bg_color = config.COLORS["white_move_background"] if is_white else config.COLORS["black_move_background"]
    text_color = config.COLORS["white_move_text"] if is_white else config.COLORS["black_move_text"]
    update_card_appearance(card, bg_color, text_color)
