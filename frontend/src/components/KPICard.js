import React from 'react';
import CountUp from 'react-countup';
import './KPICard.css';

export default function KPICard({
  icon,
  label,
  value,
  prefix = '',
  suffix = '',
  decimals = 0,
  change,
  changeLabel,
  gradient = 'blue',
  delay = 0,
}) {
  const gradients = {
    blue:   'linear-gradient(135deg, #4f8ef7, #06b6d4)',
    purple: 'linear-gradient(135deg, #a855f7, #ec4899)',
    green:  'linear-gradient(135deg, #10b981, #06b6d4)',
    orange: 'linear-gradient(135deg, #f59e0b, #ef4444)',
    pink:   'linear-gradient(135deg, #ec4899, #a855f7)',
  };

  const iconBgs = {
    blue:   'rgba(79, 142, 247, 0.15)',
    purple: 'rgba(168, 85, 247, 0.15)',
    green:  'rgba(16, 185, 129, 0.15)',
    orange: 'rgba(245, 158, 11, 0.15)',
    pink:   'rgba(236, 72, 153, 0.15)',
  };

  return (
    <div
      className="kpi-card"
      style={{ '--gradient': gradients[gradient] }}
    >
      <div
        className="kpi-icon"
        style={{ background: iconBgs[gradient] }}
      >
        {icon}
      </div>

      <div
        className="kpi-value"
        style={{ background: gradients[gradient], WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}
      >
        {prefix}
        <CountUp
          end={typeof value === 'number' ? value : parseFloat(value) || 0}
          duration={1.5}
          delay={delay}
          decimals={decimals}
          separator=","
        />
        {suffix}
      </div>

      <div className="kpi-label">{label}</div>

      {change !== undefined && (
        <div className={`kpi-change ${change >= 0 ? 'positive' : 'negative'}`}>
          <span>{change >= 0 ? '↑' : '↓'}</span>
          <span>{Math.abs(change)}%</span>
          {changeLabel && <span className="change-label">{changeLabel}</span>}
        </div>
      )}

      {/* Decorative glow */}
      <div className="kpi-glow" style={{ background: gradients[gradient] }} />
    </div>
  );
}
