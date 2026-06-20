import { Undo2, ArrowUpDown, ArrowLeft, ArrowRight } from 'lucide-react';
import type { ReactNode } from 'react';

type GameControlsProps = {
  onUndo: () => void;
  onFlip: () => void;
  onPrevMove: () => void;
  onNextMove: () => void;
  canGoPrev: boolean;
  canGoNext: boolean;
  boardOrientation: 'white' | 'black';
};

export function GameControls({
  onUndo,
  onFlip,
  onPrevMove,
  onNextMove,
  canGoPrev,
  canGoNext,
  boardOrientation,
}: GameControlsProps) {
  return (
    <div className="flex items-center gap-2">
      <ControlButton
        icon={<ArrowLeft size={15} />}
        label="Prev"
        onClick={onPrevMove}
        disabled={!canGoPrev}
      />
      <ControlButton
        icon={<ArrowRight size={15} />}
        label="Next"
        onClick={onNextMove}
        disabled={!canGoNext}
      />
      <ControlButton
        icon={<Undo2 size={15} />}
        label="Undo"
        onClick={onUndo}
      />
      <ControlButton
        icon={<ArrowUpDown size={15} />}
        label={boardOrientation === 'white' ? 'Flip ↓' : 'Flip ↑'}
        onClick={onFlip}
      />
    </div>
  );
}

function ControlButton({
  icon,
  label,
  onClick,
  disabled = false,
}: {
  icon: ReactNode;
  label: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
        color: 'var(--text-secondary)',
      }}
      onMouseEnter={(e) => {
        if (disabled) return;
        e.currentTarget.style.background = 'var(--bg-hover)';
        e.currentTarget.style.borderColor = 'var(--border-default)';
        e.currentTarget.style.color = 'var(--text-primary)';
      }}
      onMouseLeave={(e) => {
        if (disabled) return;
        e.currentTarget.style.background = 'var(--bg-elevated)';
        e.currentTarget.style.borderColor = 'var(--border-subtle)';
        e.currentTarget.style.color = 'var(--text-secondary)';
      }}
    >
      {icon}
      {label}
    </button>
  );
}
