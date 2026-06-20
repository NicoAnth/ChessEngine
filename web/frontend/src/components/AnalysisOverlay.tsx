import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import { getClassificationColor } from '../lib/utils';
import ClassificationIcon from './ClassificationIcon';
import { useTheme } from '../hooks/useTheme';

export type AnalysisProgress = {
  current: number;
  total: number;
  side: string;
  san: string;
  classification: string;
};

type AnalysisOverlayProps = {
  isOpen: boolean;
  progress: AnalysisProgress | null;
};

/* ─── Classification icon (reused from move history) ─── */
function ClassIcon({ cls }: { cls: string }) {
  const color = getClassificationColor(cls);
  return <ClassificationIcon classification={cls} size={14} style={{ color }} />;
}

/* ─── Animated particles ─── */
function Particles() {
  const particles = Array.from({ length: 18 }, (_, i) => i);
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((i) => {
        const size = 2 + Math.random() * 3;
        const left = Math.random() * 100;
        const delay = Math.random() * 6;
        const duration = 4 + Math.random() * 6;
        return (
          <motion.div
            key={i}
            className="absolute rounded-full"
            style={{
              width: size,
              height: size,
              left: `${left}%`,
              bottom: '-5%',
              background: `rgba(232, 168, 76, ${0.15 + Math.random() * 0.25})`,
            }}
            animate={{
              y: [0, -(400 + Math.random() * 300)],
              opacity: [0, 0.8, 0],
              x: [0, (Math.random() - 0.5) * 60],
            }}
            transition={{
              duration,
              delay,
              repeat: Infinity,
              ease: 'easeOut',
            }}
          />
        );
      })}
    </div>
  );
}

/* ─── Pulsing ring behind the brain icon ─── */
function PulseRings() {
  return (
    <>
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="absolute rounded-full"
          style={{
            width: 80,
            height: 80,
            border: '1px solid var(--accent)',
            top: '50%',
            left: '50%',
            marginTop: -40,
            marginLeft: -40,
          }}
          animate={{
            scale: [1, 2.2],
            opacity: [0.35, 0],
          }}
          transition={{
            duration: 2.4,
            delay: i * 0.8,
            repeat: Infinity,
            ease: 'easeOut',
          }}
        />
      ))}
    </>
  );
}

export function AnalysisOverlay({ isOpen, progress }: AnalysisOverlayProps) {
  const { isDark } = useTheme();
  const pct = progress ? Math.round((progress.current / progress.total) * 100) : 0;
  const ratio = progress ? progress.current / progress.total : 0;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.35 }}
        >
          {/* Backdrop */}
          <div
            className="absolute inset-0"
            style={{
              background: 'rgba(0, 0, 0, 0.55)',
              backdropFilter: 'blur(16px) saturate(120%)',
              WebkitBackdropFilter: 'blur(16px) saturate(120%)',
            }}
          />

          {/* Particles */}
          <Particles />

          {/* Card */}
          <motion.div
            className="relative z-10 flex flex-col items-center gap-7 px-12 py-10 rounded-2xl"
            style={{
              background: 'var(--glass-bg)',
              backdropFilter: 'blur(24px) saturate(160%)',
              WebkitBackdropFilter: 'blur(24px) saturate(160%)',
              border: '1px solid var(--border-default)',
              boxShadow:
                '0 0 0 1px var(--border-subtle), var(--shadow-lg), 0 0 80px rgba(232, 168, 76, 0.08)',
              minWidth: 380,
              maxWidth: 460,
            }}
            initial={{ scale: 0.92, opacity: 0, y: 24 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 12 }}
            transition={{ type: 'spring', bounce: 0.15, duration: 0.5 }}
          >
            {/* Caissa icon with pulse rings */}
            <div className="relative flex items-center justify-center" style={{ width: 80, height: 80 }}>
              <PulseRings />
              <motion.div
                className="relative z-10 w-16 h-16 rounded-2xl flex items-center justify-center overflow-hidden"
                style={{
                  background: 'linear-gradient(135deg, var(--accent-soft), rgba(232,168,76,0.03))',
                  border: '1px solid var(--accent-soft)',
                }}
                animate={{ rotate: [0, 2, -2, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
              >
                <img
                  src={isDark ? '/Caissa.png' : '/CaissaNoire.png'}
                  alt="Caissa"
                  className="w-11 h-11 object-contain"
                  style={{ filter: 'drop-shadow(0 0 8px rgba(232, 168, 76, 0.25))' }}
                />
              </motion.div>
            </div>

            {/* Title */}
            <div className="text-center">
              <h2
                className="text-base font-semibold tracking-tight"
                style={{ color: 'var(--text-primary)' }}
              >
                Analyse en cours
              </h2>
              <p
                className="text-xs mt-1"
                style={{ color: 'var(--text-muted)' }}
              >
                Profondeur 16 · Évaluation de chaque position
              </p>
            </div>

            {/* Progress bar */}
            <div className="w-full flex flex-col gap-2.5">
              <div className="flex items-center justify-between">
                <span
                  className="text-[11px] font-medium"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  Coup {progress?.current ?? 0} / {progress?.total ?? 0}
                </span>
                <span
                  className="text-[11px] font-bold font-mono tabular-nums"
                  style={{ color: 'var(--accent)' }}
                >
                  {pct}%
                </span>
              </div>

              {/* Bar track */}
              <div
                className="relative w-full h-2 rounded-full overflow-hidden"
                style={{ background: 'var(--bg-hover)' }}
              >
                {/* Glow under bar */}
                <div
                  className="absolute inset-0 rounded-full"
                  style={{
                    background: `linear-gradient(90deg, transparent ${Math.max(0, pct - 15)}%, var(--accent-glow) ${pct}%, transparent ${pct + 2}%)`,
                    opacity: 0.5,
                    filter: 'blur(4px)',
                  }}
                />
                {/* Filled bar */}
                <motion.div
                  className="absolute inset-y-0 left-0 rounded-full"
                  style={{
                    background: 'linear-gradient(90deg, var(--accent), #f0b860)',
                    boxShadow: '0 0 12px var(--accent-glow)',
                  }}
                  initial={{ width: '0%' }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.4, ease: 'easeOut' }}
                />
              </div>
            </div>

            {/* Current move being analyzed */}
            <AnimatePresence mode="wait">
              {progress && progress.san && (
                <motion.div
                  key={`${progress.current}-${progress.san}`}
                  className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl"
                  style={{
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                  }}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ duration: 0.18 }}
                >
                  {/* Move number + side indicator */}
                  <span
                    className="text-[10px] font-mono tabular-nums"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    {Math.ceil(progress.current / 2)}.
                    {progress.side === 'Black' ? '..' : ''}
                  </span>

                  {/* SAN */}
                  <span
                    className="text-sm font-semibold font-mono"
                    style={{ color: 'var(--text-primary)' }}
                  >
                    {progress.san}
                  </span>

                  {/* Classification badge */}
                  {progress.classification && (
                    <div className="flex items-center gap-1.5 ml-1">
                      <ClassIcon cls={progress.classification} />
                      <span
                        className="text-[10px] font-medium"
                        style={{ color: getClassificationColor(progress.classification) }}
                      >
                        {progress.classification}
                      </span>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Animated ellipsis / inspirational micro text */}
            <div className="flex items-center gap-2">
              <Sparkles size={10} style={{ color: 'var(--text-muted)', opacity: 0.5 }} />
              <motion.span
                className="text-[10px] italic"
                style={{ color: 'var(--text-muted)', opacity: 0.6 }}
                animate={{ opacity: [0.4, 0.7, 0.4] }}
                transition={{ duration: 2.5, repeat: Infinity }}
              >
                {ratio < 0.3
                  ? 'Exploration de l\'ouverture…'
                  : ratio < 0.7
                    ? 'Analyse du milieu de partie…'
                    : 'Évaluation de la finale…'}
              </motion.span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
