import { useRef, useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ScrollText, ChevronDown, ChevronUp, BookOpen } from 'lucide-react';
import type { MoveInsight } from '../lib/types';
import {
  getClassificationColor,
  getClassificationLabel,
  formatScore,
} from '../lib/utils';
import ClassificationIcon from './ClassificationIcon';
import { useTheme } from '../hooks/useTheme';

type MoveHistoryProps = {
  insights: MoveInsight[];
  activePly: number;
  onSelectPly: (ply: number) => void;
};

type MoveRow = [MoveInsight | undefined, MoveInsight | undefined];

export function MoveHistory({ insights, activePly, onSelectPly }: MoveHistoryProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [expandedMove, setExpandedMove] = useState<string | null>(null);
  const { isDark } = useTheme();

  // Auto-scroll to bottom when new moves arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [insights.length]);

  // Group moves into rows: [White, Black]
  const rows: MoveRow[] = insights.reduce((acc: MoveRow[], move) => {
    if (move.side === 'White') {
      acc.push([move, undefined]);
    } else if (acc.length > 0) {
      acc[acc.length - 1][1] = move;
    }
    return acc;
  }, []);

  const toggleExpand = (key: string) => {
    setExpandedMove((prev) => (prev === key ? null : key));
  };

  // Detect the row index where theory ends (opening goes from present to absent)
  const theoryEndRowIndex = useMemo(() => {
    let lastTheoryPly = -1;
    for (let i = 0; i < insights.length; i++) {
      if (insights[i].opening?.name) {
        lastTheoryPly = i;
      }
    }
    if (lastTheoryPly < 0) return -1; // No theory moves at all
    if (lastTheoryPly >= insights.length - 1) return -1; // Never left theory
    // The separator goes after the row containing lastTheoryPly
    // Row index = floor(lastTheoryPly / 2)
    return Math.floor(lastTheoryPly / 2);
  }, [insights]);

  return (
    <div className="glass-panel flex flex-col overflow-hidden" style={{ minHeight: 0 }}>
      {/* Header */}
      <div
        className="flex items-center gap-2 px-4 py-3"
        style={{ borderBottom: '1px solid var(--border-subtle)' }}
      >
        <ScrollText size={14} style={{ color: 'var(--accent)' }} />
        <span
          className="text-xs uppercase tracking-wider font-semibold"
          style={{ color: 'var(--text-secondary)' }}
        >
          Moves
        </span>
        <span
          className="ml-auto text-[10px] font-mono px-2 py-0.5 rounded-full"
          style={{
            background: 'var(--bg-surface)',
            color: 'var(--text-muted)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          {insights.length}
        </span>
      </div>

      {/* Move list */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto py-1" style={{ minHeight: 0 }}>
        <AnimatePresence initial={false}>
          {rows.map((pair, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: 0.02 }}
              className="px-1"
            >
              <div
                className="move-row grid px-2 py-1"
                style={{ gridTemplateColumns: '28px 1fr 1fr' }}
              >
                {/* Move number */}
                <span
                  className="text-[11px] font-mono tabular-nums pt-1"
                  style={{ color: 'var(--text-muted)' }}
                >
                  {pair[0]?.move_num ?? i + 1}.
                </span>

                {/* White move */}
                <MoveCell
                  insight={pair[0]}
                  ply={pair[0] ? (pair[0].move_num - 1) * 2 + 1 : null}
                  isActive={pair[0] ? activePly === (pair[0].move_num - 1) * 2 + 1 : false}
                  isExpanded={expandedMove === `${i}-w`}
                  onSelect={onSelectPly}
                  onToggle={() => toggleExpand(`${i}-w`)}
                />

                {/* Black move */}
                <MoveCell
                  insight={pair[1]}
                  ply={pair[1] ? (pair[1].move_num - 1) * 2 + 2 : null}
                  isActive={pair[1] ? activePly === (pair[1].move_num - 1) * 2 + 2 : false}
                  isExpanded={expandedMove === `${i}-b`}
                  onSelect={onSelectPly}
                  onToggle={() => toggleExpand(`${i}-b`)}
                />
              </div>

              {/* Expanded detail panel */}
              <AnimatePresence>
                {(expandedMove === `${i}-w` || expandedMove === `${i}-b`) && (
                  <MoveDetail
                    insight={
                      expandedMove === `${i}-w` ? pair[0] : pair[1]
                    }
                  />
                )}
              </AnimatePresence>

              {/* Theory exit separator */}
              {i === theoryEndRowIndex && (
                <div
                  className="flex items-center gap-2 mx-3 my-1.5"
                >
                  <div className="flex-1 h-px" style={{ background: 'rgba(167, 139, 250, 0.2)' }} />
                  <div className="flex items-center gap-1 px-2 py-0.5 rounded-full"
                    style={{
                      background: 'rgba(167, 139, 250, 0.08)',
                      border: '1px solid rgba(167, 139, 250, 0.12)',
                    }}
                  >
                    <BookOpen size={9} style={{ color: 'var(--cls-theory)' }} />
                    <span
                      className="text-[9px] font-medium uppercase tracking-wider"
                      style={{ color: 'var(--cls-theory)' }}
                    >
                      Fin de la théorie
                    </span>
                  </div>
                  <div className="flex-1 h-px" style={{ background: 'rgba(167, 139, 250, 0.2)' }} />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Empty state */}
        {insights.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 gap-3">
            <div className="relative">
              <div
                className="absolute inset-0 rounded-full"
                style={{
                  background: 'radial-gradient(circle, var(--accent-soft) 0%, transparent 70%)',
                  transform: 'scale(2.5)',
                  opacity: 0.6,
                }}
              />
              <img
                src={isDark ? '/Caissa.png' : '/CaissaNoire.png'}
                alt="Caissa"
                className="relative w-12 h-12 object-contain"
                style={{ opacity: 0.4, filter: isDark ? 'drop-shadow(0 0 8px rgba(232, 168, 76, 0.15))' : 'none' }}
              />
            </div>
            <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
              Jouez un coup ou importez une partie
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Score Change Indicator ──

function ScoreChangeChip({ change, side }: { change: number; side: 'White' | 'Black' }) {
  // Positive change = good for the side that played
  // For display, we show the absolute centipawn change with a sign
  const isNegative = side === 'White' ? change < -0.1 : change > 0.1;
  const isPositive = side === 'White' ? change > 0.1 : change < -0.1;
  const absDelta = Math.abs(change);

  if (absDelta < 0.05) return null; // negligible change

  const color = isNegative
    ? 'var(--cls-mistake)'
    : isPositive
      ? 'var(--cls-best)'
      : 'var(--text-muted)';

  return (
    <span
      className="text-[9px] font-mono tabular-nums ml-0.5 opacity-60 group-hover:opacity-100 transition-opacity"
      style={{ color }}
    >
      {isNegative ? '−' : '+'}
      {absDelta.toFixed(1)}
    </span>
  );
}

// ── Move Cell ──

function MoveCell({
  insight,
  ply,
  isActive,
  isExpanded,
  onSelect,
  onToggle,
}: {
  insight: MoveInsight | undefined;
  ply: number | null;
  isActive: boolean;
  isExpanded: boolean;
  onSelect: (ply: number) => void;
  onToggle: () => void;
}) {
  if (!insight) return <span />;

  const color = getClassificationColor(insight.classification);
  const hasDetail = insight.best_move || insight.classification !== 'Théorie';

  const handleSelect = () => {
    if (ply === null) return;
    onSelect(ply);
  };

  return (
    <div
      className="flex items-center gap-1 group cursor-pointer rounded px-1 py-0.5 -mx-1"
      style={{
        background: isActive
          ? `color-mix(in srgb, ${color} 16%, transparent)`
          : isExpanded
            ? `color-mix(in srgb, ${color} 8%, transparent)`
            : undefined,
        outline: isActive ? `1px solid color-mix(in srgb, ${color} 60%, transparent)` : undefined,
      }}
      onClick={handleSelect}
    >
      {/* Classification icon */}
      <ClassificationIcon
        classification={insight.classification}
        size={14}
        className="flex-shrink-0 opacity-80 group-hover:opacity-100 transition-opacity"
        style={{ color }}
      />

      {/* Move SAN */}
      <span
        className="text-[13px] font-semibold cursor-default"
        style={{ color: 'var(--text-primary)' }}
      >
        {insight.san}
      </span>

      {/* Score change */}
      {insight.score_change !== undefined && (
        <ScoreChangeChip change={insight.score_change} side={insight.side} />
      )}

      {/* Expand indicator */}
      {hasDetail && (
        <button
          type="button"
          className="ml-auto opacity-0 group-hover:opacity-40 transition-opacity"
          onClick={(event) => {
            event.stopPropagation();
            onToggle();
          }}
          title="Détails du coup"
        >
          {isExpanded ? (
            <ChevronUp size={10} style={{ color: 'var(--text-muted)' }} />
          ) : (
            <ChevronDown size={10} style={{ color: 'var(--text-muted)' }} />
          )}
        </button>
      )}
    </div>
  );
}

// ── Move Detail (expanded) ──

function MoveDetail({ insight }: { insight: MoveInsight | undefined }) {
  if (!insight) return null;

  const color = getClassificationColor(insight.classification);
  const label = getClassificationLabel(insight.classification);

  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.2, ease: 'easeInOut' }}
      className="overflow-hidden"
    >
      <div
        className="mx-2 mb-1 rounded-lg px-3 py-2 text-[11px]"
        style={{
          background: `color-mix(in srgb, ${color} 6%, var(--bg-surface))`,
          borderLeft: `2px solid ${color}`,
        }}
      >
        {/* Classification label row */}
        <div className="flex items-center gap-2 mb-1.5">
          <ClassificationIcon classification={insight.classification} size={16} style={{ color }} />
          <span className="font-semibold" style={{ color }}>
            {label}
          </span>
          <span
            className="ml-auto font-mono tabular-nums"
            style={{ color: 'var(--text-muted)' }}
          >
            {formatScore(String(insight.score_after))}
          </span>
        </div>

        {/* Score before → after */}
        <div className="flex items-center gap-2" style={{ color: 'var(--text-secondary)' }}>
          <span className="font-mono tabular-nums text-[10px]">
            {formatScore(String(insight.score_before))} → {formatScore(String(insight.score_after))}
          </span>
          {insight.score_change !== undefined && Math.abs(insight.score_change) >= 0.05 && (
            <span
              className="font-mono tabular-nums text-[10px] font-semibold"
              style={{
                color:
                  (insight.side === 'White' ? insight.score_change : -insight.score_change) < -0.1
                    ? 'var(--cls-mistake)'
                    : 'var(--cls-best)',
              }}
            >
              ({insight.score_change > 0 ? '+' : ''}{insight.score_change.toFixed(2)})
            </span>
          )}
        </div>

        {/* Best alternative move */}
        {insight.best_move && (
          <div
            className="mt-1.5 flex items-center gap-1.5"
            style={{ color: 'var(--text-muted)' }}
          >
            <span className="text-[10px]">Best:</span>
            <span
              className="font-semibold text-[11px]"
              style={{ color: 'var(--cls-best)' }}
            >
              {insight.best_move}
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
}
