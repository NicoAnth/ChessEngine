"""
Barre d'évaluation pour afficher l'avantage dans une position d'échecs.
"""

import tkinter as tk
from tkinter import font
from src.utils import config
import math
import threading
import traceback

class EvaluationBar:
    """
    Barre d'évaluation moderne et élégante pour afficher l'avantage dans une position d'échecs.
    
    Cette barre verticale indique visuellement l'avantage entre les blancs et les noirs,
    avec des animations fluides lors des changements d'évaluation.
    """
    
    def __init__(self, parent, width=30, height=None):
        """
        Initialise la barre d'évaluation.
        
        Args:
            parent: Widget parent
            width: Largeur de la barre en pixels
            height: Hauteur de la barre (par défaut, utilise la hauteur du parent)
        """
        self.parent = parent
        self.width = width
        self.height = height or parent.winfo_reqheight()
        
        # Valeurs d'évaluation
        self.current_eval = 0.0  # 0 = égalité, positif = avantage blanc, négatif = avantage noir
        self.target_eval = 0.0   # Valeur cible pour l'animation
        self.formatted_eval = "+0.0"  # Evaluation formatée pour affichage
        self.is_mate = False     # True si l'évaluation est un mat
        self.mate_in = 0         # Nombre de coups avant mat (si is_mate est True)
        
        # Constantes pour le rendu
        self.MAX_VISUAL_EVAL = 10.0  # L'évaluation visuelle maximale (±5 pions)
        self.animation_in_progress = False
        self.animation_id = None
        
        # Calculer la hauteur des composants
        label_height = 22  # Hauteur optimale pour le label
        bar_height = self.height - label_height  # Le reste pour la barre
        
        # Créer le conteneur principal
        self.container = tk.Frame(
            parent, 
            width=width,
            height=self.height,
            bg=config.COLORS["background"], 
            padx=0, 
            pady=0
        )
        self.container.pack_propagate(False)
        
        # Créer le canvas pour la barre
        self.canvas = tk.Canvas(
            self.container,
            width=width,
            height=bar_height,
            bg=config.COLORS["eval_bar_background"],
            highlightthickness=1,
            highlightbackground=config.COLORS["eval_bar_border"]
        )
        self.canvas.pack(side=tk.TOP, fill=tk.X)
        
        # Définir une police moderne
        self.eval_font = font.Font(family="Segoe UI", size=9, weight="bold")
        
        # Couleurs modernes avec alpha pour transparence
        label_bg = "#2C3E50"  # Bleu marine élégant
        label_fg = "#ECF0F1"  # Blanc cassé
        
        # Créer un cadre pour contenir le label avec de l'espace
        self.label_frame = tk.Frame(
            self.container,
            width=width,
            height=label_height,
            bg=config.COLORS["background"],
            padx=0,
            pady=2
        )
        self.label_frame.pack(side=tk.TOP, fill=tk.X)
        self.label_frame.pack_propagate(False)
        
        # Créer le label avec un style moderne
        self.eval_label = tk.Label(
            self.label_frame,
            text=self.formatted_eval,
            font=self.eval_font,
            bg=label_bg,
            fg=label_fg,
            anchor=tk.CENTER,
            padx=0,
            pady=1
        )
        
        # Arrondir visuellement les coins du label (effet visuel uniquement)
        # Utiliser un padding sur les côtés pour éviter que le texte soit trop près des bords
        self.eval_label.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=3, pady=1)
        
        # Dessiner la barre initiale (position égale)
        self.draw_bar()

    def pack(self, **kwargs):
        """Emballe le conteneur avec les options données."""
        self.container.pack(**kwargs)
        
    def grid(self, **kwargs):
        """Place le conteneur dans une grille avec les options données."""
        self.container.grid(**kwargs)
        
    def place(self, **kwargs):
        """Place le conteneur avec les options données."""
        self.container.place(**kwargs)
        
    def draw_bar(self):
        """Dessine la barre d'évaluation selon la valeur actuelle."""
        self.canvas.delete("all")
        
        # Calculer la hauteur de la barre
        canvas_height = self.canvas.winfo_height()
        
        # Si le canvas n'est pas encore rendu, utiliser la hauteur demandée
        if canvas_height <= 1:
            canvas_height = self.height
        
        # Limiter l'évaluation pour l'affichage
        visual_eval = self.current_eval
        
        # Si c'est un mat, remplir complètement en faveur du gagnant
        if self.is_mate:
            if self.mate_in > 0:  # Blancs gagnent
                visual_eval = self.MAX_VISUAL_EVAL * 1.5
            else:  # Noirs gagnent
                visual_eval = -self.MAX_VISUAL_EVAL * 1.5
        else:
            # Limiter l'évaluation pour l'affichage
            visual_eval = max(min(visual_eval, self.MAX_VISUAL_EVAL), -self.MAX_VISUAL_EVAL)
        
        # Calculer le pourcentage de la barre (0.5 = égalité)
        bar_ratio = 0.5 + (visual_eval / (2 * self.MAX_VISUAL_EVAL))
        
        # Calcul de la position de la ligne de démarcation (entre blanc et noir)
        split_y = int(canvas_height * bar_ratio)
        
        # OPTIMISATION: Réduire le nombre de lignes dessinées en utilisant des rectangles
        # au lieu de dessiner une ligne pour chaque pixel
        
        # Partie BLANCHE - Dans la partie SUPÉRIEURE (0 à split_y)
        if split_y > 0:
            # Utiliser un rectangle pour la partie blanche avec un dégradé simplifié
            gradient_steps = min(10, split_y)  # Limiter le nombre d'étapes du dégradé
            gradient_height = split_y / gradient_steps if gradient_steps > 0 else 0
            
            for i in range(gradient_steps):
                # Calculer l'intensité du dégradé
                intensity = i / gradient_steps
                # Interpoler entre les couleurs blanc et blanc-gradient
                color = self._interpolate_color(
                    config.COLORS["eval_white"], 
                    config.COLORS["eval_white_gradient"], 
                    intensity * 0.7
                )
                
                y_start = i * gradient_height
                y_end = (i + 1) * gradient_height
                
                # Dessiner un rectangle pour cette étape du dégradé
                self.canvas.create_rectangle(
                    0, y_start, self.width, y_end, 
                    fill=color, outline=color
                )
        
        # Partie NOIRE - Dans la partie INFÉRIEURE (split_y à canvas_height)
        if split_y < canvas_height:
            # Utiliser un rectangle pour la partie noire avec un dégradé simplifié
            remaining_height = canvas_height - split_y
            gradient_steps = min(10, remaining_height)  # Limiter le nombre d'étapes du dégradé
            gradient_height = remaining_height / gradient_steps if gradient_steps > 0 else 0
            
            for i in range(gradient_steps):
                # Calculer l'intensité du dégradé
                intensity = i / gradient_steps
                # Interpoler entre les couleurs noir et noir-gradient
                color = self._interpolate_color(
                    config.COLORS["eval_black"], 
                    config.COLORS["eval_black_gradient"], 
                    intensity * 0.7
                )
                
                y_start = split_y + i * gradient_height
                y_end = split_y + (i + 1) * gradient_height
                
                # Dessiner un rectangle pour cette étape du dégradé
                self.canvas.create_rectangle(
                    0, y_start, self.width, y_end, 
                    fill=color, outline=color
                )
        
        # Dessiner une ligne de démarcation
        line_color = config.COLORS["eval_draw"]
        self.canvas.create_line(
            0, split_y, self.width, split_y, 
            fill=line_color, 
            width=1
        )
        
        # Mettre à jour la couleur du texte pour meilleure lisibilité
        if self.is_mate:
            if self.mate_in > 0:  # Blancs gagnent
                self.eval_label.config(
                    fg=config.COLORS["eval_text_white"],
                    bg=config.COLORS["eval_white"]
                )
            else:  # Noirs gagnent
                self.eval_label.config(
                    fg=config.COLORS["eval_text_black"],
                    bg=config.COLORS["eval_black"]
                )
        else:
            self.eval_label.config(
                fg=config.COLORS["primary_text"],
                bg=config.COLORS["background"]
            )
            
    def update_evaluation(self, evaluation, is_mate=False, mate_in=0, animate=True):
        """
        Met à jour l'évaluation.
        
        Args:
            evaluation: Valeur numérique de l'évaluation (positif = avantage blanc)
            is_mate: True si l'évaluation est un mat
            mate_in: Nombre de coups avant mat (si is_mate est True)
            animate: Si True, anime le changement de l'évaluation
        """
        # Stocker les nouvelles valeurs
        self.target_eval = float(evaluation)
        
        # Double vérification des paramètres de mat
        # Détecter les situations spéciales où is_mate=False mais devrait être True
        if not is_mate:
            # 1. Détecter par score très élevé
            if abs(self.target_eval) >= 90.0:
                is_mate = True
                mate_in = 1 if self.target_eval > 0 else -1  # Valeur positive = mat pour les blancs
                
            # 2. Détecter par la chaîne de l'objet (si nous avons une chaîne avec "Mate")
            elif isinstance(evaluation, str) and "Mate" in evaluation:
                is_mate = True
                try:
                    # Format: "Mate(+3)"
                    mate_part = evaluation.split("Mate(")[1].split(")")[0]
                    mate_in = int(mate_part.replace("+", ""))
                except Exception:
                    mate_in = 1  # Valeur par défaut si extraction échoue
        
        # Vérifier que les valeurs sont cohérentes
        if is_mate and mate_in == 0:
            # Corriger les situations où is_mate=True mais mate_in=0
            mate_in = 1 if self.target_eval > 0 else -1
            
        # Mettre à jour les attributs
        self.is_mate = is_mate
        self.mate_in = mate_in
        
        # Mettre à jour le texte formaté
        if is_mate:
            # Format: "#3" ou "-#3"
            self.formatted_eval = f"{'#' if mate_in > 0 else '-#'}{abs(mate_in)}"
            # Log minimal pour les situations de mat
            print(f"[INFO] Évaluation: Mat en {abs(mate_in)} coup(s) pour les {'Blancs' if mate_in > 0 else 'Noirs'}")
        else:
            # Format: +1.5 ou -0.5
            sign = "+" if evaluation >= 0 else ""
            self.formatted_eval = f"{sign}{evaluation:.1f}"
            
        # Mettre à jour le texte du label
        self.eval_label.config(text=self.formatted_eval)
        
        # Si animation demandée et que l'évaluation est différente
        if animate and abs(self.current_eval - self.target_eval) > 0.01:
            if not self.animation_in_progress:
                self.animation_in_progress = True
                self.animate_evaluation()
        else:
            # Pas d'animation, mettre à jour directement
            self.current_eval = self.target_eval
            self.draw_bar()
    
    def animate_evaluation(self):
        """Anime la transition entre l'ancienne et la nouvelle évaluation."""
        # Annuler l'animation précédente si elle existe
        if self.animation_id:
            self.canvas.after_cancel(self.animation_id)
            self.animation_id = None
            
        # Calculer le pas de l'animation
        diff = self.target_eval - self.current_eval
        step = diff * 0.1  # Avance de 10% vers la cible à chaque frame
        
        # Appliquer le pas
        self.current_eval += step
        
        # Si on est proche de la cible, terminer l'animation
        if abs(self.current_eval - self.target_eval) < 0.01:
            self.current_eval = self.target_eval
            self.animation_in_progress = False
        
        # Redessiner la barre
        self.draw_bar()
        
        # Continuer l'animation si nécessaire
        if self.animation_in_progress:
            self.animation_id = self.canvas.after(20, self.animate_evaluation)
    
    def _interpolate_color(self, color1, color2, t):
        """
        Interpoler entre deux couleurs hexadécimales.
        
        Args:
            color1: Première couleur au format "#RRGGBB"
            color2: Deuxième couleur au format "#RRGGBB"
            t: Facteur d'interpolation entre 0 et 1
        
        Returns:
            Couleur interpolée au format "#RRGGBB"
        """
        # Convertir les couleurs hexadécimales en valeurs RGB
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        
        # Interpoler chaque composante
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        
        # Convertir en format hexadécimal
        return f"#{r:02x}{g:02x}{b:02x}"