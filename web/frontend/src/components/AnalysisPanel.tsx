import { motion, AnimatePresence } from 'framer-motion';
import { BarChart3, Target, TrendingUp } from 'lucide-react';
import type { SideStats } from '../lib/types';
import { formatScore } from '../lib/utils';

type AnalysisPanelProps = {
  score: string;
  depth: number | null;
  bestMove: string;
  whiteStats: SideStats;
  blackStats: SideStats;
  turn: string;
  moveCount: number;
  error: string;
};

export function AnalysisPanel({
  score,
  depth,
  bestMove,
  whiteStats,
  blackStats,
  turn,
  moveCount,
  error,
}: AnalysisPanelProps) {
  return (
    <div className="glass-panel p-5 flex flex-col gap-4">
      {/* Eval Section */}
      <div className="grid grid-cols-3 gap-3">
        <MetricCard
          icon={<BarChart3 size={14} />}
          label="Eval"
          value={formatScore(score)}
          accent={parseFloat(score) >= 0}
        />
        <MetricCard
          icon={<Target size={14} />}
          label="Depth"
          value={depth !== null ? `${depth}` : '—'}
        />
        <MetricCard
          icon={<TrendingUp size={14} />}
          label="Best"
          value={bestMove || '—'}
        />
      </div>

      {/* Divider */}
      <div style={{ height: 1, background: 'var(--border-subtle)' }} />

      {/* Accuracy Bars */}
      <div className="flex flex-col gap-2">
        <span
          className="text-[10px] uppercase tracking-wider font-semibold"
          style={{ color: 'var(--text-muted)' }}
        >
          Accuracy
        </span>
        <AccuracyRow label="White" value={whiteStats.accuracy ?? 0} />
        <AccuracyRow label="Black" value={blackStats.accuracy ?? 0} />
      </div>

      {/* Game info */}
      <div
        className="flex items-center justify-between text-[11px] px-1"
        style={{ color: 'var(--text-muted)' }}
      >
        <span>Move {moveCount}</span>
        <span>{turn} to play</span>
      </div>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="text-xs px-3 py-2 rounded-md"
            style={{
              background: 'rgba(248, 113, 113, 0.08)',
              border: '1px solid rgba(248, 113, 113, 0.15)',
              color: 'var(--danger)',
            }}
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Sub-components ──

function MetricCard({
  icon,
  label,
  value,
  accent = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div
      className="flex flex-col items-center gap-1 py-2.5 rounded-lg"
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      <span style={{ color: 'var(--text-muted)' }}>{icon}</span>
      <motion.span
        key={value}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-sm font-bold font-mono tabular-nums"
        style={{ color: accent ? 'var(--accent)' : 'var(--text-primary)' }}
      >
        {value}
      </motion.span>
      <span
        className="text-[9px] uppercase tracking-wider font-medium"
        style={{ color: 'var(--text-muted)' }}
      >
        {label}
      </span>
    </div>
  );
}

function AccuracyRow({ label, value }: { label: string; value: number }) {
  const color =
    value >= 90
      ? 'var(--success)'
      : value >= 70
        ? 'var(--warning)'
        : value >= 50
          ? 'var(--cls-mistake)'
          : 'var(--danger)';

  return (
    <div className="flex items-center gap-3">
      <span
        className="text-[11px] font-medium w-10"
        style={{ color: 'var(--text-secondary)' }}
      >
        {label}
      </span>
      <div
        className="flex-1 h-1.5 rounded-full overflow-hidden"
        style={{ background: 'var(--bg-hover)' }}
      >
        <motion.div
          className="h-full rounded-full"
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(value, 100)}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
      </div>
      <span
        className="text-[11px] font-mono font-bold tabular-nums w-10 text-right"
        style={{ color }}
      >
        {value > 0 ? `${Math.round(value)}%` : '—'}
      </span>
    </div>
  );
}
