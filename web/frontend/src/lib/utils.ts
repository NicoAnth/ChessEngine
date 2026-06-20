import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Merge Tailwind classes safely */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Classification → hex color (matching original project palette) */
const CLASSIFICATION_COLORS: Record<string, string> = {
  'Théorie': '#A78BFA',
  'Super coup': '#00E5FF',
  'Coup brillant': '#D500F9',
  'Meilleur coup': '#3BD97B',
  'Excellent': '#6BE29B',
  'Bon coup': '#8EF0B5',
  'Imprécision': '#F7C76E',
  'Erreur': '#FF6B6B',
  'Grosse erreur': '#F44336',
};

export function getClassificationColor(classification: string): string {
  return CLASSIFICATION_COLORS[classification] ?? 'var(--text-muted)';
}

/** Classification → short label for fallback badges */
const CLASSIFICATION_LABELS: Record<string, string> = {
  'Théorie': 'Book',
  'Super coup': 'Super',
  'Coup brillant': 'Brilliant',
  'Meilleur coup': 'Best',
  'Excellent': 'Excellent',
  'Bon coup': 'Good',
  'Imprécision': 'Inaccuracy',
  'Erreur': 'Mistake',
  'Grosse erreur': 'Blunder',
};

export function getClassificationLabel(classification: string): string {
  return CLASSIFICATION_LABELS[classification] ?? classification;
}

/** Convert centipawn score to eval bar percentage (0-100, from white's perspective) */
export function scoreToBarPercent(scoreStr: string): number {
  const score = parseFloat(scoreStr);
  if (isNaN(score)) return 50;

  // Check for mate scores
  if (Math.abs(score) > 900) {
    return score > 0 ? 98 : 2;
  }

  // Sigmoid-like mapping: score in pawns → percentage
  // Using 2/(1+e^(-0.4*score)) - 1 mapped to 0-100
  const k = 0.4;
  const sigmoid = 1 / (1 + Math.exp(-k * score));
  return Math.max(2, Math.min(98, sigmoid * 100));
}

/** Format score for display */
export function formatScore(scoreStr: string): string {
  const score = parseFloat(scoreStr);
  if (isNaN(score)) return '0.0';

  if (Math.abs(score) > 900) {
    const mateIn = score > 0 ? '+' : '-';
    return `M${mateIn}`;
  }

  const sign = score > 0 ? '+' : '';
  return `${sign}${score.toFixed(1)}`;
}
