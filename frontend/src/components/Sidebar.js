import React from 'react';
import { NavLink } from 'react-router-dom';
import './Sidebar.css';

const NAV_ITEMS = [
  { path: '/overview',   icon: '⚡', label: 'Overview',         desc: 'City KPIs' },
  { path: '/demand',     icon: '📊', label: 'Demand Analysis',  desc: 'Patterns & trends' },
  { path: '/simulation', icon: '🔮', label: 'Simulation',       desc: 'What-if scenarios' },
  { path: '/decisions',  icon: '🎯', label: 'Decision Engine',  desc: 'Actionable insights' },
  { path: '/ai-assistant', icon: '🤖', label: 'AI Assistant',   desc: 'Smart insights' },
];

export default function Sidebar({ open, onToggle }) {
  return (
    <aside className={`sidebar ${open ? 'open' : 'closed'}`}>
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-icon">🌆</div>
        {open && (
          <div className="logo-text">
            <span className="logo-title">Urban Mobility</span>
            <span className="logo-sub">Intelligence OS</span>
          </div>
        )}
        <button className="toggle-btn" onClick={onToggle} aria-label="Toggle sidebar">
          {open ? '◀' : '▶'}
        </button>
      </div>

      {/* Status indicator */}
      {open && (
        <div className="sidebar-status">
          <span className="status-dot" />
          <span className="status-text">System Online</span>
        </div>
      )}

      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {open && (
              <div className="nav-text">
                <span className="nav-label">{item.label}</span>
                <span className="nav-desc">{item.desc}</span>
              </div>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      {open && (
        <div className="sidebar-footer">
          <div className="footer-badge">
            <span>v1.0.0</span>
            <span className="footer-dot">•</span>
            <span>Production</span>
          </div>
        </div>
      )}
    </aside>
  );
}
