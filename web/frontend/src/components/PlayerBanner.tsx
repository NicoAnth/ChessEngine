import { motion } from 'framer-motion';
import type { SideStats } from '../lib/types';

type PlayerBannerProps = {
  color: 'white' | 'black';
  stats: SideStats;
  isActive: boolean;
  playerName?: string;
  playerElo?: string;
  className?: string;
};

export function PlayerBanner({
  color,
  stats,
  isActive,
  playerName,
  playerElo,
  className = '',
}: PlayerBannerProps) {
  const isWhite = color === 'white';
  const accuracy = stats.accuracy ?? 0;
  const displayName = playerName || (isWhite ? 'White' : 'Black');

  // Accuracy ring color
  const ringColor =
    accuracy >= 90
      ? 'var(--success)'
      : accuracy >= 70
        ? 'var(--warning)'
        : accuracy >= 50
          ? 'var(--cls-mistake)'
          : 'var(--danger)';

  return (
    <div
      className={`flex items-center gap-3 px-3 py-2 rounded-lg ${className}`}
      style={{
        background: isActive ? 'var(--accent-soft)' : 'transparent',
        border: isActive ? '1px solid rgba(232,168,76,0.15)' : '1px solid transparent',
        transition: 'all 0.3s ease',
      }}
    >
      {/* Piece icon */}
      <div
        className="w-8 h-8 rounded-md flex items-center justify-center text-lg font-bold select-none"
        style={{
          background: isWhite
            ? 'linear-gradient(135deg, #f0ead6, #d4c4a8)'
            : 'linear-gradient(135deg, #2a2a3e, #1a1a2e)',
          color: isWhite ? '#1a1a2e' : '#f0ead6',
          boxShadow: isActive ? `0 0 12px ${isWhite ? 'rgba(240,234,214,0.2)' : 'rgba(42,42,62,0.4)'}` : 'none',
        }}
      >
        {isWhite ? '♔' : '♚'}
      </div>

      {/* Name + status */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span
            className="text-sm font-semibold truncate"
            style={{ color: 'var(--text-primary)' }}
            title={displayName}
          >
            {displayName}
          </span>
          {playerElo && (
            <span
              className="text-[10px] font-mono px-1.5 py-0.5 rounded"
              style={{
                background: 'var(--bg-surface)',
                color: 'var(--text-muted)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              {playerElo}
            </span>
          )}
          {isActive && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="w-1.5 h-1.5 rounded-full flex-shrink-0"
              style={{ backgroundColor: 'var(--accent)' }}
            />
          )}
        </div>
        {!playerName && (
          <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
            Player
          </span>
        )}
      </div>

      {/* Accuracy circle */}
      {accuracy > 0 && (
        <div className="flex flex-col items-center">
          <svg width="32" height="32" viewBox="0 0 36 36">
            <circle
              cx="18" cy="18" r="14"
              fill="none"
              stroke="var(--border-subtle)"
              strokeWidth="3"
            />
            <circle
              cx="18" cy="18" r="14"
              fill="none"
              stroke={ringColor}
              strokeWidth="3"
              strokeDasharray={`${(accuracy / 100) * 88} 88`}
              strokeLinecap="round"
              transform="rotate(-90 18 18)"
              style={{ transition: 'stroke-dasharray 0.6s ease' }}
            />
          </svg>
          <span className="text-[10px] font-mono font-bold" style={{ color: ringColor, marginTop: -22 }}>
            {Math.round(accuracy)}
          </span>
        </div>
      )}
    </div>
  );
}
