import React from 'react';
import './LoadingSpinner.css';

export default function LoadingSpinner({ message = 'Loading data...' }) {
  return (
    <div className="loading-container">
      <div className="loading-ring">
        <div /><div /><div /><div />
      </div>
      <p className="loading-message">{message}</p>
    </div>
  );
}

export function SkeletonCard({ height = 200 }) {
  return (
    <div className="skeleton-card" style={{ height }}>
      <div className="skeleton-line short" />
      <div className="skeleton-line" />
      <div className="skeleton-block" style={{ height: height - 80 }} />
    </div>
  );
}
