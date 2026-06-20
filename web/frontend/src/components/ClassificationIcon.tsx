/**
 * Inline SVG classification icons — modern, crisp at any size.
 * Each icon is a pure SVG element using currentColor for fill/stroke,
 * so the parent can control color via `style={{ color }}` or Tailwind.
 */

type IconProps = {
  size?: number;
  className?: string;
  style?: React.CSSProperties;
};

/* ─── Individual icon shapes (viewBox 0 0 24 24) ─── */

/** Théorie — open book */
function BookIcon({ size = 16, className, style }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={style}>
      <path
        d="M12 6.5C10.5 5.5 8.5 5 6 5c-1.2 0-2.3.15-3.25.4A.75.75 0 0 0 2 6.13v11.25c0 .5.5.87 1 .75A11 11 0 0 1 6 17.5c2.2 0 4.1.6 5.5 1.5m.5-12.5c1.5-1 3.5-1.5 6-1.5c1.2 0 2.3.15 3.25.4.45.12.75.52.75.98v11.25c0 .5-.5.87-1 .75A11 11 0 0 0 18 17.5c-2.2 0-4.1.6-5.5 1.5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M12 6.5v12.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

/** Super coup — starburst */
function StarburstIcon({ size = 16, className, style }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={style}>
      <path
        d="M12 2l1.8 5.5L19.5 6l-3.7 4.2L21.5 12l-5.7 1.8L17.5 20l-4.2-3.7L12 22l-1.3-5.7L6.5 20l1.7-6.2L2.5 12l5.7-1.8L4.5 6l5.7 1.5z"
        fill="currentColor"
        opacity="0.2"
      />
      <path
        d="M12 2l1.8 5.5L19.5 6l-3.7 4.2L21.5 12l-5.7 1.8L17.5 20l-4.2-3.7L12 22l-1.3-5.7L6.5 20l1.7-6.2L2.5 12l5.7-1.8L4.5 6l5.7 1.5z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Coup brillant — faceted diamond */
function DiamondIcon({ size = 16, className, style }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={style}>
      <path d="M6 3h12l4 6-10 13L2 9z" fill="currentColor" opacity="0.15" />
      <path
        d="M6 3h12l4 6-10 13L2 9z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path d="M2 9h20" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <path d="M10 3l-2 6 4 13 4-13-2-6" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" opacity="0.6" />
    </svg>
  );
}

/** Meilleur coup — bold checkmark in rounded circle */
function BestMoveIcon({ size = 16, className, style }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={style}>
      <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.15" />
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.8" />
      <path
        d="M7.5 12.5l3 3 6-6.5"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Excellent — upward chevron in circle */
function ExcellentIcon({ size = 16, className, style }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={style}>
      <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.12" />
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M8 14l4-4 4 4"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Bon coup — filled dot in circle */
function GoodMoveIcon({ size = 16, className, style }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={style}>
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="12" cy="12" r="4" fill="currentColor" />
    </svg>
  );
}

/** Imprécision — warning triangle with exclamation */
function InaccuracyIcon({ size = 16, className, style }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={style}>
      <path
        d="M12 3L2 21h20L12 3z"
        fill="currentColor"
        opacity="0.12"
      />
      <path
        d="M12 3L2 21h20L12 3z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path d="M12 10v4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="12" cy="17" r="1" fill="currentColor" />
    </svg>
  );
}

/** Erreur — X in circle */
function MistakeIcon({ size = 16, className, style }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={style}>
      <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.12" />
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.8" />
      <path
        d="M9 9l6 6m0-6l-6 6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

/** Grosse erreur — heavy double-X burst */
function BlunderIcon({ size = 16, className, style }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={style}>
      <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.18" />
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
      <path
        d="M9 9l6 6m0-6l-6 6"
        stroke="currentColor"
        strokeWidth="2.8"
        strokeLinecap="round"
      />
      {/* Emphasis ticks */}
      <path d="M5 5l1.5 1.5M19 5l-1.5 1.5M5 19l1.5-1.5M19 19l-1.5-1.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

/* ─── Lookup map ─── */

const ICON_MAP: Record<string, React.ComponentType<IconProps>> = {
  'Théorie': BookIcon,
  'Super coup': StarburstIcon,
  'Coup brillant': DiamondIcon,
  'Meilleur coup': BestMoveIcon,
  'Excellent': ExcellentIcon,
  'Bon coup': GoodMoveIcon,
  'Imprécision': InaccuracyIcon,
  'Erreur': MistakeIcon,
  'Grosse erreur': BlunderIcon,
};

/* ─── Public component ─── */

export default function ClassificationIcon({
  classification,
  size = 16,
  className,
  style,
}: {
  classification: string;
  size?: number;
  className?: string;
  style?: React.CSSProperties;
}) {
  const Icon = ICON_MAP[classification];
  if (!Icon) return null;
  return <Icon size={size} className={className} style={style} />;
}
