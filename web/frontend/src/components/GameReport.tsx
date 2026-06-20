import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, BarChart3, Gauge, Trophy, Target, Percent, Activity, Crosshair, TrendingUp, Shield, HelpCircle } from 'lucide-react';
import type { SideStats, EvalPoint, DifficultyInfo, GameInfo, MoveInsight } from '../lib/types';
import { getClassificationColor } from '../lib/utils';
import { useTheme } from '../hooks/useTheme';
import ClassificationIcon from './ClassificationIcon';

type GameReportProps = {
  isOpen: boolean;
  onClose: () => void;
  whiteStats: SideStats;
  blackStats: SideStats;
  evalChart: EvalPoint[];
  difficulty: DifficultyInfo | null;
  gameInfo: GameInfo | null;
  insights: MoveInsight[];
  onSelectPly: (ply: number) => void;
};

export function GameReport({
  isOpen,
  onClose,
  whiteStats,
  blackStats,
  evalChart,
  difficulty,
  gameInfo,
  insights,
  onSelectPly,
}: GameReportProps) {
  const hasData = insights.length > 0;
  const { isDark } = useTheme();

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50"
            style={{ background: 'rgba(0, 0, 0, 0.6)', backdropFilter: 'blur(4px)' }}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className="fixed inset-0 z-50 flex items-center justify-center p-6 pointer-events-none"
          >
            <div
              className="glass-panel pointer-events-auto relative flex flex-col overflow-hidden"
              style={{
                width: '100%',
                maxWidth: 780,
                maxHeight: 'calc(100vh - 80px)',
              }}
            >
              {/* Header */}
              <div
                className="flex items-center justify-between px-6 py-4"
                style={{ borderBottom: '1px solid var(--border-subtle)' }}
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center"
                    style={{ background: 'var(--accent-soft)', color: 'var(--accent)' }}
                  >
                    <BarChart3 size={18} />
                  </div>
                  <div>
                    <h2
                      className="text-base font-bold"
                      style={{ color: 'var(--text-primary)' }}
                    >
                      Rapport de Partie
                    </h2>
                    {gameInfo?.white && gameInfo?.black && (
                      <p className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
                        {gameInfo.white} vs {gameInfo.black}
                        {gameInfo.result && gameInfo.result !== '*' && ` · ${gameInfo.result}`}
                      </p>
                    )}
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="w-8 h-8 rounded-lg flex items-center justify-center cursor-pointer opacity-60 hover:opacity-100 transition-opacity"
                  style={{
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-secondary)',
                  }}
                >
                  <X size={16} />
                </button>
              </div>

              {/* Scrollable Content */}
              <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
                {!hasData ? (
                  <div className="flex flex-col items-center justify-center py-16 gap-4">
                    <div className="relative">
                      <div
                        className="absolute inset-0 rounded-full"
                        style={{
                          background: 'radial-gradient(circle, var(--accent-soft) 0%, transparent 70%)',
                          transform: 'scale(3)',
                          opacity: 0.5,
                        }}
                      />
                      <img
                        src={isDark ? '/Caissa.png' : '/CaissaNoire.png'}
                        alt="Caissa"
                        className="relative w-16 h-16 object-contain"
                        style={{ opacity: 0.35, filter: isDark ? 'drop-shadow(0 0 12px rgba(232, 168, 76, 0.15))' : 'none' }}
                      />
                    </div>
                    <span className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>
                      Jouez ou importez une partie pour voir le rapport
                    </span>
                  </div>
                ) : (
                  <>
                    {/* ── Eval Graph ── */}
                    <ReportSection title="Game Evolution" icon={<BarChart3 size={14} />}>
                      <EvalGraph data={evalChart} onSelectPly={onSelectPly} onClose={onClose} />
                    </ReportSection>

                    {/* ── Player Accuracy Cards ── */}
                    <div className="grid grid-cols-2 gap-4">
                      <PlayerCard
                        label={gameInfo?.white ?? 'White'}
                        color="white"
                        stats={whiteStats}
                        difficulty={difficulty?.white ?? null}
                      />
                      <PlayerCard
                        label={gameInfo?.black ?? 'Black'}
                        color="black"
                        stats={blackStats}
                        difficulty={difficulty?.black ?? null}
                      />
                    </div>

                    {/* ── Classification Breakdown ── */}
                    <ReportSection title="Move Classification" icon={<Crosshair size={14} />}>
                      <div className="grid grid-cols-2 gap-4">
                        <ClassificationBreakdown
                          label={gameInfo?.white ?? 'White'}
                          counts={whiteStats.counts ?? {}}
                          total={whiteStats.total_moves ?? 0}
                        />
                        <ClassificationBreakdown
                          label={gameInfo?.black ?? 'Black'}
                          counts={blackStats.counts ?? {}}
                          total={blackStats.total_moves ?? 0}
                        />
                      </div>
                    </ReportSection>

                    {/* ── Difficulty ── */}
                    {difficulty && (
                      <ReportSection title="Game Difficulty" icon={<Gauge size={14} />}>
                        <DifficultyMeter value={difficulty.overall} />
                      </ReportSection>
                    )}
                  </>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// ───────────────────────── Sub-components ─────────────────────────

function ReportSection({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <span style={{ color: 'var(--accent)' }}>{icon}</span>
        <span
          className="text-[11px] uppercase tracking-wider font-semibold"
          style={{ color: 'var(--text-secondary)' }}
        >
          {title}
        </span>
      </div>
      {children}
    </div>
  );
}

// ── Eval Graph (pure SVG) ──

function EvalGraph({
  data,
  onSelectPly,
  onClose,
}: {
  data: EvalPoint[];
  onSelectPly: (ply: number) => void;
  onClose: () => void;
}) {
  if (data.length < 2) {
    return (
      <div
        className="flex items-center justify-center py-8 rounded-lg text-xs"
        style={{ background: 'var(--bg-surface)', color: 'var(--text-muted)' }}
      >
        Not enough data for graph
      </div>
    );
  }

  const W = 700;
  const H = 160;
  const PAD_X = 32;
  const PAD_Y = 16;
  const graphW = W - PAD_X * 2;
  const graphH = H - PAD_Y * 2;

  // Clamp scores for display (±6 pawns)
  const clamp = (v: number) => Math.max(-6, Math.min(6, v));
  const maxAbsScore = 6;

  const toX = (i: number) => PAD_X + (i / (data.length - 1)) * graphW;
  const toY = (score: number) =>
    PAD_Y + ((maxAbsScore - clamp(score)) / (2 * maxAbsScore)) * graphH;

  // Build path
  const points = data.map((d, i) => ({ x: toX(i), y: toY(d.score) }));
  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ');

  // Area fill paths (white above center, black below)
  const centerY = toY(0);
  const whiteAreaPath = `M${PAD_X},${centerY} ` +
    points.map((p) => `L${p.x},${Math.min(p.y, centerY)}`).join(' ') +
    ` L${PAD_X + graphW},${centerY} Z`;
  const blackAreaPath = `M${PAD_X},${centerY} ` +
    points.map((p) => `L${p.x},${Math.max(p.y, centerY)}`).join(' ') +
    ` L${PAD_X + graphW},${centerY} Z`;

  const handleClick = (ply: number) => {
    onSelectPly(ply);
    onClose();
  };

  return (
    <div
      className="rounded-lg overflow-hidden"
      style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}
    >
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full"
        style={{ height: 160 }}
        preserveAspectRatio="none"
      >
        {/* White advantage area */}
        <path d={whiteAreaPath} fill="rgba(240, 234, 214, 0.12)" />
        {/* Black advantage area */}
        <path d={blackAreaPath} fill="rgba(30, 30, 50, 0.25)" />

        {/* Grid lines */}
        {[-4, -2, 0, 2, 4].map((v) => (
          <line
            key={v}
            x1={PAD_X}
            x2={PAD_X + graphW}
            y1={toY(v)}
            y2={toY(v)}
            stroke="var(--border-subtle)"
            strokeWidth={v === 0 ? 1.5 : 0.5}
            strokeDasharray={v === 0 ? undefined : '3,3'}
          />
        ))}

        {/* Y-axis labels */}
        {[-4, -2, 0, 2, 4].map((v) => (
          <text
            key={v}
            x={PAD_X - 6}
            y={toY(v) + 3}
            textAnchor="end"
            fill="var(--text-muted)"
            fontSize="8"
            fontFamily="monospace"
          >
            {v > 0 ? `+${v}` : v}
          </text>
        ))}

        {/* Eval line */}
        <path
          d={linePath}
          fill="none"
          stroke="var(--accent)"
          strokeWidth={2}
          strokeLinejoin="round"
        />

        {/* Clickable points (invisible hit areas) */}
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={6}
            fill="transparent"
            className="cursor-pointer"
            onClick={() => handleClick(data[i].ply)}
          >
            <title>Move {data[i].ply}: {data[i].score > 0 ? '+' : ''}{data[i].score.toFixed(2)}</title>
          </circle>
        ))}
      </svg>
    </div>
  );
}

// ── Player Accuracy Card ──

function PlayerCard({
  label,
  color,
  stats,
  difficulty,
}: {
  label: string;
  color: 'white' | 'black';
  stats: SideStats;
  difficulty: number | null;
}) {
  const accuracy = stats.accuracy ?? 0;
  const bestPct = stats.best_move_percentage ?? 0;

  const accColor =
    accuracy >= 90
      ? 'var(--success)'
      : accuracy >= 70
        ? 'var(--warning)'
        : accuracy >= 50
          ? 'var(--cls-mistake)'
          : 'var(--danger)';

  return (
    <div
      className="rounded-xl p-4 flex flex-col gap-3"
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-2">
        <div
          className="w-6 h-6 rounded-md flex items-center justify-center text-sm font-bold select-none"
          style={{
            background: color === 'white'
              ? 'linear-gradient(135deg, #f0ead6, #d4c4a8)'
              : 'linear-gradient(135deg, #2a2a3e, #1a1a2e)',
            color: color === 'white' ? '#1a1a2e' : '#f0ead6',
          }}
        >
          {color === 'white' ? '♔' : '♚'}
        </div>
        <span
          className="text-sm font-semibold truncate"
          style={{ color: 'var(--text-primary)' }}
        >
          {label}
        </span>
      </div>

      {/* Accuracy circle */}
      <div className="flex items-center justify-center">
        <div className="relative">
          <svg width="80" height="80" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="42" fill="none" stroke="var(--border-subtle)" strokeWidth="6" />
            <circle
              cx="50"
              cy="50"
              r="42"
              fill="none"
              stroke={accColor}
              strokeWidth="6"
              strokeDasharray={`${(accuracy / 100) * 264} 264`}
              strokeLinecap="round"
              transform="rotate(-90 50 50)"
              style={{ transition: 'stroke-dasharray 0.8s ease' }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span
              className="text-lg font-bold font-mono tabular-nums"
              style={{ color: accColor }}
            >
              {accuracy > 0 ? Math.round(accuracy) : '—'}
            </span>
            <span
              className="text-[8px] uppercase tracking-wider font-semibold"
              style={{ color: 'var(--text-muted)' }}
            >
              Accuracy
            </span>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="flex flex-col gap-1.5">
        <MiniMetric
          icon={<Trophy size={10} />}
          label="Meilleur coup"
          value={`${Math.round(bestPct)}%`}
          tooltip="Pourcentage de coups joués qui correspondent au meilleur coup identifié par le moteur."
        />
        <MiniMetric
          icon={<Percent size={10} />}
          label="Précision"
          value={`${Math.round(stats.precision ?? 0)}%`}
          tooltip="Mesure globale de la qualité des coups, pondérée par leur impact sur la position. Un score élevé indique un jeu proche de la perfection."
        />
        <MiniMetric
          icon={<Target size={10} />}
          label="Précision critique"
          value={`${Math.round(stats.critical_accuracy ?? 0)}%`}
          tooltip="Précision des coups dans les moments critiques de la partie (gros changement d'évaluation ou position complexe)."
        />
        <MiniMetric
          icon={<Activity size={10} />}
          label="ACPL"
          value={`${Math.round(stats.acpl ?? 0)}`}
          tooltip="Average Centipawn Loss — perte moyenne en centièmes de pion par coup. Plus la valeur est basse, meilleur est le jeu. En dessous de 30 est considéré très bon."
        />
        <MiniMetric
          icon={<Crosshair size={10} />}
          label="Régularité"
          value={`${Math.round(stats.consistency ?? 0)}%`}
          tooltip="Mesure la constance du jeu. Un score élevé signifie que la qualité des coups est régulière sans grandes variations."
        />
        <MiniMetric
          icon={<TrendingUp size={10} />}
          label="En avance"
          value={`${Math.round(stats.t1_accuracy ?? 0)}%`}
          tooltip="Précision des coups joués lorsque vous étiez en position avantageuse. Indique votre capacité à convertir un avantage."
        />
        <MiniMetric
          icon={<Shield size={10} />}
          label="En défense"
          value={`${Math.round(stats.t2_accuracy ?? 0)}%`}
          tooltip="Précision des coups joués en position défavorable. Un score élevé montre une bonne résistance sous pression."
        />
        {difficulty !== null && (
          <MiniMetric
            icon={<Gauge size={10} />}
            label="Difficulté"
            value={`${difficulty}/10`}
            tooltip="Niveau de difficulté des positions rencontrées. Un score élevé indique que vous avez dû faire face à des positions complexes et tendues."
          />
        )}
      </div>
    </div>
  );
}

function MiniMetric({
  icon,
  label,
  value,
  tooltip,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  tooltip?: string;
}) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div
      className="flex items-center gap-2 px-2.5 py-1.5 rounded-md relative"
      style={{ background: 'var(--bg-elevated)' }}
    >
      <span style={{ color: 'var(--text-muted)' }}>{icon}</span>
      <span className="text-[11px] flex-1 flex items-center gap-1" style={{ color: 'var(--text-secondary)' }}>
        {label}
        {/* Help icon with tooltip */}
        {tooltip && (
          <div
            className="relative flex items-center"
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
          >
            <div
              className="w-3.5 h-3.5 rounded-full flex items-center justify-center cursor-help transition-all duration-200"
              style={{
                background: showTooltip ? 'var(--accent-soft)' : 'transparent',
                color: showTooltip ? 'var(--accent)' : 'var(--text-muted)',
              }}
            >
              <HelpCircle size={10} strokeWidth={2.5} />
            </div>

            <AnimatePresence>
              {showTooltip && (
                <motion.div
                  initial={{ opacity: 0, y: 4, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 4, scale: 0.96 }}
                  transition={{ duration: 0.15, ease: 'easeOut' }}
                  className="absolute z-50 left-0 bottom-full mb-2 pointer-events-none"
                  style={{ width: 220 }}
                >
                  <div
                    className="rounded-lg px-3 py-2.5 text-[10px] leading-relaxed shadow-lg"
                    style={{
                      background: 'var(--bg-deep)',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-secondary)',
                      backdropFilter: 'blur(12px)',
                      boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
                    }}
                  >
                    <div className="flex items-center gap-1.5 mb-1">
                      <span style={{ color: 'var(--accent)' }}>{icon}</span>
                      <span
                        className="text-[10px] font-semibold uppercase tracking-wider"
                        style={{ color: 'var(--accent)' }}
                      >
                        {label}
                      </span>
                    </div>
                    {tooltip}
                    {/* Arrow */}
                    <div
                      className="absolute -bottom-1 left-3 w-2 h-2 rotate-45"
                      style={{
                        background: 'var(--bg-deep)',
                        borderRight: '1px solid var(--border-subtle)',
                        borderBottom: '1px solid var(--border-subtle)',
                      }}
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </span>

      <span
        className="text-[11px] font-mono font-semibold tabular-nums"
        style={{ color: 'var(--text-primary)' }}
      >
        {value}
      </span>
    </div>
  );
}

// ── Classification Breakdown ──

const CLASSIFICATION_ORDER = [
  'Meilleur coup',
  'Excellent',
  'Bon coup',
  'Théorie',
  'Super coup',
  'Coup brillant',
  'Imprécision',
  'Erreur',
  'Grosse erreur',
];

function ClassificationBreakdown({
  label,
  counts,
  total,
}: {
  label: string;
  counts: Record<string, number>;
  total: number;
}) {
  return (
    <div
      className="rounded-xl p-4 flex flex-col gap-2"
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      <span
        className="text-[10px] uppercase tracking-wider font-semibold mb-1"
        style={{ color: 'var(--text-muted)' }}
      >
        {label} · {total} moves
      </span>

      {CLASSIFICATION_ORDER.map((cls) => {
        const count = counts[cls] ?? 0;
        if (count === 0) return null;
        const pct = total > 0 ? (count / total) * 100 : 0;
        const color = getClassificationColor(cls);

        return (
          <div key={cls} className="flex items-center gap-2">
            <ClassificationIcon
              classification={cls}
              size={14}
              className="flex-shrink-0"
              style={{ color }}
            />
            <span
              className="text-[11px] flex-1 truncate"
              style={{ color: 'var(--text-secondary)' }}
            >
              {cls}
            </span>
            <span
              className="text-[11px] font-mono font-semibold tabular-nums w-6 text-right"
              style={{ color }}
            >
              {count}
            </span>
            {/* Mini bar */}
            <div
              className="w-16 h-1 rounded-full overflow-hidden flex-shrink-0"
              style={{ background: 'var(--bg-hover)' }}
            >
              <motion.div
                className="h-full rounded-full"
                style={{ background: color }}
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(pct, 100)}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Difficulty Meter ──

function DifficultyMeter({ value }: { value: number }) {
  const pct = (value / 10) * 100;

  const diffColor =
    value >= 8
      ? '#F44336'
      : value >= 6
        ? '#FF6B6B'
        : value >= 4
          ? '#F7C76E'
          : '#3BD97B';

  const diffLabel =
    value >= 8
      ? 'Very Hard'
      : value >= 6
        ? 'Hard'
        : value >= 4
          ? 'Medium'
          : 'Easy';

  return (
    <div
      className="rounded-xl p-4 flex flex-col gap-3"
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
          {diffLabel}
        </span>
        <span
          className="text-lg font-bold font-mono tabular-nums"
          style={{ color: diffColor }}
        >
          {value}
          <span className="text-xs font-normal" style={{ color: 'var(--text-muted)' }}>
            /10
          </span>
        </span>
      </div>

      {/* Progress bar */}
      <div
        className="w-full h-2 rounded-full overflow-hidden"
        style={{ background: 'var(--bg-hover)' }}
      >
        <motion.div
          className="h-full rounded-full"
          style={{ background: diffColor }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />
      </div>

      {/* Scale markers */}
      <div className="flex justify-between px-0.5">
        {['Easy', 'Medium', 'Hard', 'Expert'].map((l) => (
          <span
            key={l}
            className="text-[8px] uppercase tracking-wider"
            style={{ color: 'var(--text-muted)' }}
          >
            {l}
          </span>
        ))}
      </div>
    </div>
  );
}
