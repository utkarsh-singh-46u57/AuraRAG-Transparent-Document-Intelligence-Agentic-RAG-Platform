import React from 'react';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
  onClick?: () => void;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className = '',
  glow = false,
  onClick
}) => {
  return (
    <div
      onClick={onClick}
      className={`glass-card ${glow ? 'shadow-neon-glow border-purple-500/40' : ''} ${className}`}
    >
      {children}
    </div>
  );
};
