import React, { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts';
import ChartCard from '../components/ChartCard';
import { SkeletonCard } from '../components/LoadingSpinner';
import { useApi } from '../hooks/useApi';
import './DecisionInsights.css';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="di-tooltip">
      <p style={{ color: '#8892b0', marginBottom: 4 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color, fontWeight: 600 }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toFixed(3) : p.value}
        </p>
      ))}
    </div>
  );
};

const PRIORITY_COLORS = { HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#10b981' }; // eslint-disable-line

export default function DecisionInsights() {
  const { data: report, loading } = useApi('/api/decision/report');
  const { data: sustainability, loading: susLoading } = useApi('/api/sustainability');
  const [activeSection, setActiveSection] = useState('zones');

  const zones_df = Array.isArray(report?.best_zones) ? report.best_zones : [];
  const hours_df = Array.isArray(report?.best_hours) ? report.best_hours : [];
  const surge_df = Array.isArray(report?.surge_recommendations) ? report.surge_recommendations : [];
  const fleet_df = Array.isArray(report?.fleet_plan) ? report.fleet_plan : [];

  const sections = [
    { key: 'zones', label: '📍 Best Zones', icon: '📍' },
    { key: 'hours', label: '⏰ Best Hours', icon: '⏰' },
    { key: 'surge', label: '⚡ Surge Strategy', icon: '⚡' },
    { key: 'fleet', label: '🚗 Fleet Plan', icon: '🚗' },
    { key: 'eco', label: '🌍 Sustainability', icon: '🌍' },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title gradient-text-purple">Decision Intelligence Engine</h1>
        <p className="page-subtitle">Data-driven recommendations for operators, drivers, and city planners</p>
      </div>

      {/* Section tabs */}
      <div className="di-tabs">
        {sections.map(s => (
          <button
            key={s.key}
            className={`di-tab ${activeSection === s.key ? 'active' : ''}`}
            onClick={() => setActiveSection(s.key)}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Best Zones */}
      {activeSection === 'zones' && (
        <div className="section">
          {loading ? <SkeletonCard height={400} /> : (
            <>
              <ChartCard title="Top Zones by Driver Opportunity" subtitle="Composite score based on earnings, demand, and wait time">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={zones_df} layout="vertical" barSize={20}>
                    <defs>
                      <linearGradient id="zoneOppGrad" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#4f8ef7" />
                        <stop offset="100%" stopColor="#10b981" />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis type="number" tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis dataKey="zone_id" type="category" tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} width={40} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="composite_score" name="Opportunity Score" fill="url(#zoneOppGrad)" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <div className="di-cards-grid section">
                {zones_df.map((zone, i) => (
                  <div key={zone.zone_id} className="di-zone-card">
                    <div className="di-zone-header">
                      <span className="di-zone-rank">#{i + 1}</span>
                      <span className="di-zone-id">{zone.zone_id}</span>
                      <span className="badge badge-blue">Top Zone</span>
                    </div>
                    <div className="di-zone-stats">
                      <div className="di-stat">
                        <span className="di-stat-label">Avg Earnings</span>
                        <span className="di-stat-value green">${zone.avg_earnings?.toFixed(2)}</span>
                      </div>
                      <div className="di-stat">
                        <span className="di-stat-label">Avg Demand</span>
                        <span className="di-stat-value blue">{zone.avg_demand?.toFixed(3)}</span>
                      </div>
                      <div className="di-stat">
                        <span className="di-stat-label">Avg Wait</span>
                        <span className="di-stat-value orange">{zone.avg_wait?.toFixed(1)} min</span>
                      </div>
                      <div className="di-stat">
                        <span className="di-stat-label">Cancel Rate</span>
                        <span className="di-stat-value red">{(zone.cancel_rate * 100)?.toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Best Hours */}
      {activeSection === 'hours' && (
        <div className="section">
          {loading ? <SkeletonCard height={400} /> : (
            <>
              <ChartCard title="Driver Opportunity Score by Hour" subtitle="Best hours to maximize earnings">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={[...hours_df].sort((a, b) => a.hour - b.hour)} barSize={18}>
                    <defs>
                      <linearGradient id="hourGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.9} />
                        <stop offset="100%" stopColor="#ef4444" stopOpacity={0.6} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="hour" tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false}
                      tickFormatter={h => `${h}h`} />
                    <YAxis tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="hour_score" name="Hour Score" fill="url(#hourGrad)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <div className="hours-table-wrapper section">
                <table className="di-table">
                  <thead>
                    <tr>
                      <th>Hour</th>
                      <th>Label</th>
                      <th>Avg Earnings</th>
                      <th>Avg Demand</th>
                      <th>Surge Rate</th>
                      <th>Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {hours_df.map(row => (
                      <tr key={row.hour}>
                        <td className="mono">{row.hour}:00</td>
                        <td>{row.label}</td>
                        <td className="green">${row.avg_earnings?.toFixed(2)}</td>
                        <td className="blue">{row.avg_demand?.toFixed(3)}</td>
                        <td className="orange">{(row.surge_rate * 100)?.toFixed(1)}%</td>
                        <td>
                          <div className="score-bar">
                            <div className="score-fill" style={{ width: `${Math.min(100, row.hour_score * 10)}%` }} />
                            <span>{row.hour_score?.toFixed(2)}</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {/* Surge Strategy */}
      {activeSection === 'surge' && (
        <div className="section">
          {loading ? <SkeletonCard height={400} /> : (
            <div className="surge-grid">
              {surge_df.map((rec, i) => (
                <div key={i} className={`surge-card priority-${rec.priority?.toLowerCase()}`}>
                  <div className="surge-card-header">
                    <span className="surge-hour">{rec.label}</span>
                    <span className={`badge badge-${rec.priority === 'HIGH' ? 'red' : 'orange'}`}>
                      {rec.priority}
                    </span>
                  </div>
                  <div className="surge-metrics">
                    <div className="surge-metric">
                      <span>Demand Score</span>
                      <strong style={{ color: '#4f8ef7' }}>{rec.demand_score}</strong>
                    </div>
                    <div className="surge-metric">
                      <span>Suggested Surge</span>
                      <strong style={{ color: '#f59e0b' }}>{rec.suggested_surge}x</strong>
                    </div>
                  </div>
                  <div className="surge-action">{rec.action}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Fleet Plan */}
      {activeSection === 'fleet' && (
        <div className="section">
          {loading ? <SkeletonCard height={400} /> : (
            <ChartCard title="Fleet Deployment Plan" subtitle="Recommended driver allocation by zone and hour">
              <div className="fleet-table-wrapper">
                <table className="di-table">
                  <thead>
                    <tr>
                      <th>Zone</th>
                      <th>Hour</th>
                      <th>Demand Score</th>
                      <th>Drivers Needed</th>
                      <th>Priority</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fleet_df.map((row, i) => (
                      <tr key={i}>
                        <td className="mono blue">{row.zone_id}</td>
                        <td className="mono">{row.hour}:00</td>
                        <td>{row.demand_score?.toFixed(3)}</td>
                        <td className="green">{row.drivers_recommended}</td>
                        <td>
                          <span className={`badge badge-${row.priority === 'HIGH' ? 'red' : 'orange'}`}>
                            {row.priority}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </ChartCard>
          )}
        </div>
      )}

      {/* Sustainability */}
      {activeSection === 'eco' && (
        <div className="section">
          {susLoading ? <SkeletonCard height={400} /> : (
            <>
              <div className="eco-kpi-grid">
                <div className="eco-kpi">
                  <span className="eco-icon">🌍</span>
                  <span className="eco-value red">{sustainability?.baseline?.co2_tonnes_baseline?.toFixed(0)} t</span>
                  <span className="eco-label">Baseline CO₂</span>
                </div>
                <div className="eco-kpi">
                  <span className="eco-icon">⚡</span>
                  <span className="eco-value green">{sustainability?.optimized_30pct_ev?.co2_tonnes_optimized?.toFixed(0)} t</span>
                  <span className="eco-label">With 30% EV Fleet</span>
                </div>
                <div className="eco-kpi">
                  <span className="eco-icon">🌱</span>
                  <span className="eco-value blue">{sustainability?.optimized_30pct_ev?.reduction_pct?.toFixed(1)}%</span>
                  <span className="eco-label">CO₂ Reduction</span>
                </div>
                <div className="eco-kpi">
                  <span className="eco-icon">🌳</span>
                  <span className="eco-value orange">{sustainability?.baseline?.equivalent_trees_needed?.toLocaleString()}</span>
                  <span className="eco-label">Trees Needed/Year</span>
                </div>
              </div>

              <div className="eco-strategies section">
                <h3 className="eco-strategies-title">🌿 Eco-Optimization Strategies</h3>
                {(sustainability?.strategies || []).map((s, i) => (
                  <div key={i} className="eco-strategy-card">
                    <div className="eco-strategy-header">
                      <span className="eco-strategy-name">{s.strategy}</span>
                      <div className="eco-strategy-badges">
                        <span className={`badge badge-${s.priority === 'HIGH' ? 'green' : s.priority === 'MEDIUM' ? 'orange' : 'blue'}`}>
                          {s.priority}
                        </span>
                        <span className="eco-reduction">-{s.co2_reduction_pct}% CO₂</span>
                      </div>
                    </div>
                    <p className="eco-strategy-desc">{s.description}</p>
                    <div className="eco-strategy-meta">
                      <span>💰 {s.cost_impact}</span>
                      <span>📅 {s.timeline}</span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
