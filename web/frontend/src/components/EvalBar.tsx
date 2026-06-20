import { motion } from 'framer-motion';
import { scoreToBarPercent, formatScore } from '../lib/utils';

type EvalBarProps = {
  score: string;
  flipped: boolean;
};

/**
 * Vertical evaluation bar sitting next to the board.
 * Score remains from White's perspective.
 * Orientation only controls which side (white/black) is visually at the bottom.
 */
export function EvalBar({ score, flipped }: EvalBarProps) {
  const percent = scoreToBarPercent(score);
  const fillHeight = percent;
  const displayScore = formatScore(score);
  const isWhiteAdvantage = parseFloat(score) >= 0;
  const advantageOnTop = isWhiteAdvantage ? flipped : !flipped;

  return (
    <div className="flex flex-col items-center gap-1 select-none" style={{ width: 28 }}>
      {/* Score label top */}
      <motion.span
        key={displayScore}
        initial={{ opacity: 0, y: -4 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-[10px] font-mono font-bold tabular-nums"
        style={{
          color: isWhiteAdvantage ? 'var(--eval-white)' : 'var(--text-muted)',
        }}
      >
        {advantageOnTop ? displayScore : ''}
      </motion.span>

      {/* Bar */}
      <div
        className="eval-bar flex-1 w-full relative"
        style={{ minHeight: 0 }}
      >
        <motion.div
          className="eval-bar-fill"
          initial={{ height: '50%' }}
          animate={{ height: `${fillHeight}%` }}
          transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
          style={{
            bottom: flipped ? 'auto' : 0,
            top: flipped ? 0 : 'auto',
          }}
        />
        {/* Center line */}
        <div
          className="absolute left-0 right-0"
          style={{
            top: '50%',
            height: 1,
            background: 'rgba(255,255,255,0.1)',
          }}
        />
      </div>

      {/* Score label bottom */}
      <motion.span
        key={`b-${displayScore}`}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-[10px] font-mono font-bold tabular-nums"
        style={{
          color: !isWhiteAdvantage ? 'var(--eval-white)' : 'var(--text-muted)',
        }}
      >
        {!advantageOnTop ? displayScore : ''}
      </motion.span>
    </div>
  );
}
