import React from 'react';

interface ScoreBadgeProps {
  score: number;
  className?: string;
}

export const ScoreBadge: React.FC<ScoreBadgeProps> = ({ score, className = '' }) => {
  const percentage = Math.round(score * 100);
  
  let colorClasses = 'bg-cyan-950/60 text-cyan-300 border-cyan-500/30';
  let barColor = 'bg-cyan-400';

  if (score >= 0.85) {
    colorClasses = 'bg-emerald-950/60 text-emerald-300 border-emerald-500/30';
    barColor = 'bg-emerald-400';
  } else if (score < 0.70) {
    colorClasses = 'bg-amber-950/60 text-amber-300 border-amber-500/30';
    barColor = 'bg-amber-400';
  }

  return (
    <div className={`inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-full border text-[10px] font-mono font-medium ${colorClasses} ${className}`}>
      <span>{percentage}% match</span>
      <div className="w-10 h-1.5 bg-black/40 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${barColor}`}
          style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
        />
      </div>
    </div>
  );
};
