import React from 'react';
import { ShieldCheck, CheckCircle2, XCircle, AlertTriangle, HelpCircle } from 'lucide-react';

const VERDICT_CONFIG = {
  VERIFIED: {
    bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    dot: 'bg-emerald-500',
    icon: ShieldCheck,
    label: 'VERIFIED',
  },
  'LIKELY TRUE': {
    bg: 'bg-blue-50 text-blue-700 border-blue-200',
    dot: 'bg-blue-500',
    icon: CheckCircle2,
    label: 'LIKELY TRUE',
  },
  FALSE: {
    bg: 'bg-rose-50 text-rose-700 border-rose-200',
    dot: 'bg-rose-500',
    icon: XCircle,
    label: 'FALSE',
  },
  MISLEADING: {
    bg: 'bg-amber-50 text-amber-700 border-amber-200',
    dot: 'bg-amber-500',
    icon: AlertTriangle,
    label: 'MISLEADING',
  },
  UNVERIFIED: {
    bg: 'bg-slate-100 text-slate-700 border-slate-200',
    dot: 'bg-slate-400',
    icon: HelpCircle,
    label: 'UNVERIFIED',
  },
};

export default function VerdictBadge({ verdict = 'UNVERIFIED', size = 'md', showIcon = true }) {
  const normVerdict = verdict.toUpperCase().trim();
  const config = VERDICT_CONFIG[normVerdict] || VERDICT_CONFIG['UNVERIFIED'];
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-semibold',
    lg: 'text-sm px-3.5 py-1.5 gap-2 font-bold',
    xl: 'text-base px-4 py-2 gap-2.5 font-extrabold',
  }[size] || 'text-xs px-2.5 py-1 gap-1.5';

  const iconSizes = {
    sm: 12,
    md: 14,
    lg: 18,
    xl: 20,
  }[size] || 14;

  return (
    <span
      className={`inline-flex items-center rounded-full border shadow-xs transition-all ${config.bg} ${sizeClasses}`}
    >
      {showIcon && <Icon size={iconSizes} className="shrink-0" />}
      <span>{config.label}</span>
    </span>
  );
}
