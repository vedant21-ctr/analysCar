import React, { useState } from 'react';
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import ChartCard from '../components/ChartCard';
import { SkeletonCard } from '../components/LoadingSpinner';
import { postApi } from '../hooks/useApi';
import './SimulationPanel.css';

const DEFAULT_CONFIG = {
  n_drivers: 500,
  demand_multiplier: 1.0,
  weather: 'Clear',
  traffic_level: 'Medium',
  event_flag: 0,
  hour: 8,
  base_fare: 12.0,
  surge_threshold: 1.4,
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="sim-tooltip">
      <p className="sim-tooltip-label">Min {label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toLocaleString() : p.value}</strong>
        </p>
      ))}
    </div>
  );
};

export default function SimulationPanel() {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [ran, setRan] = useState(false);

  const handleChange = (key, value) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const runSimulation = async () => {
    setLoading(true);
    try {
      const data = await postApi('/api/simulate', config);
      setResult(data);
      setRan(true);
    } catch (err) {
      console.error('Simulation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const SliderControl = ({ label, configKey, min, max, step = 0.1, format = v => v }) => (
    <div className="slider-control">
      <div className="slider-header">
        <span className="slider-label">{label}</span>
        <span className="slider-value">{format(config[configKey])}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={config[configKey]}
        onChange={e => handleChange(configKey, parseFloat(e.target.value))}
        className="slider"
      />
      <div className="slider-range">
        <span>{format(min)}</span>
        <span>{format(max)}</span>
      </div>
    </div>
  );

  const SelectControl = ({ label, configKey, options }) => (
    <div className="select-control">
      <label className="select-label">{label}</label>
      <select
        value={config[configKey]}
        onChange={e => handleChange(configKey, e.target.value)}
        className="select-input"
      >
        {options.map(opt => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    </div>
  );

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title gradient-text-blue">Simulation Engine</h1>
        <p className="page-subtitle">Configure city parameters and run Monte Carlo demand simulations</p>
      </div>

      <div className="sim-layout">
        {/* Control Panel */}
        <div className="sim-controls">
          <div className="controls-header">
            <span className="controls-icon">🔮</span>
            <div>
              <h3>Simulation Controls</h3>
              <p>Adjust parameters and run</p>
            </div>
          </div>

          <div className="controls-body">
            <SliderControl
              label="Number of Drivers"
              configKey="n_drivers"
              min={50}
              max={2000}
              step={50}
              format={v => v.toLocaleString()}
            />
            <SliderControl
              label="Demand Multiplier"
              configKey="demand_multiplier"
              min={0.2}
              max={3.0}
              step={0.1}
              format={v => `${v.toFixed(1)}x`}
            />
            <SliderControl
              label="Hour of Day"
              configKey="hour"
              min={0}
              max={23}
              step={1}
              format={v => `${v}:00`}
            />
            <SliderControl
              label="Base Fare ($)"
              configKey="base_fare"
              min={5}
              max={50}
              step={1}
              format={v => `$${v}`}
            />
            <SliderControl
              label="Surge Threshold"
              configKey="surge_threshold"
              min={1.0}
              max={2.5}
              step={0.1}
              format={v => `${v.toFixed(1)}x`}
            />

            <div className="controls-row">
              <SelectControl
                label="Weather"
                configKey="weather"
                options={['Clear', 'Cloudy', 'Rainy', 'Fog', 'Snow']}
              />
              <SelectControl
                label="Traffic"
                configKey="traffic_level"
                options={['Low', 'Medium', 'High']}
              />
            </div>

            <div className="toggle-control">
              <span className="toggle-label">Event Active</span>
              <button
                className={`toggle-btn-sim ${config.event_flag ? 'on' : 'off'}`}
                onClick={() => handleChange('event_flag', config.event_flag ? 0 : 1)}
              >
                {config.event_flag ? 'ON' : 'OFF'}
              </button>
            </div>

            <button
              className="run-btn"
              onClick={runSimulation}
              disabled={loading}
            >
              {loading ? (
                <span className="btn-loading">
                  <span className="btn-spinner" />
                  Simulating...
                </span>
              ) : (
                '▶ Run Simulation'
              )}
            </button>
          </div>
        </div>

        {/* Results Panel */}
        <div className="sim-results">
          {!ran && !loading && (
            <div className="sim-empty">
              <div className="sim-empty-icon">🔮</div>
              <h3>Configure & Run</h3>
              <p>Adjust the parameters on the left and click "Run Simulation" to see results</p>
            </div>
          )}

          {loading && (
            <div className="sim-loading">
              <div className="sim-loading-ring" />
              <p>Running Monte Carlo simulation...</p>
            </div>
          )}

          {result && !loading && (
            <>
              {/* KPI row */}
              <div className="sim-kpi-grid">
                {[
                  { label: 'Predicted Demand', value: result.predicted_demand?.toFixed(3), icon: '📈', color: '#4f8ef7' },
                  { label: 'Total Rides', value: result.total_rides?.toLocaleString(), icon: '🚗', color: '#10b981' },
                  { label: 'Total Revenue', value: `$${result.total_revenue?.toLocaleString()}`, icon: '💰', color: '#f59e0b' },
                  { label: 'Avg Wait', value: `${result.avg_wait_time?.toFixed(1)} min`, icon: '⏱️', color: '#a855f7' },
                  { label: 'Surge', value: `${result.surge_multiplier?.toFixed(2)}x`, icon: '⚡', color: '#ef4444' },
                  { label: 'Cancel Rate', value: `${(result.cancellation_rate * 100)?.toFixed(1)}%`, icon: '❌', color: '#ec4899' },
                ].map((kpi, i) => (
                  <div key={i} className="sim-kpi" style={{ '--kpi-color': kpi.color }}>
                    <span className="sim-kpi-icon">{kpi.icon}</span>
                    <span className="sim-kpi-value" style={{ color: kpi.color }}>{kpi.value}</span>
                    <span className="sim-kpi-label">{kpi.label}</span>
                  </div>
                ))}
              </div>

              {/* Time series chart */}
              <ChartCard title="Revenue Over Time" subtitle="Cumulative revenue during simulation (60 min)">
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={result.time_series}>
                    <defs>
                      <linearGradient id="simRevGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="minute" tick={{ fill: '#8892b0', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#8892b0', fontSize: 10 }} axisLine={false} tickLine={false}
                      tickFormatter={v => `$${(v/1000).toFixed(0)}K`} />
                    <Tooltip content={<CustomTooltip />} />
                    <Area type="monotone" dataKey="cumulative_revenue" name="Cumulative Revenue"
                      stroke="#10b981" strokeWidth={2} fill="url(#simRevGrad)" dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </ChartCard>

              {/* Rides per minute */}
              <ChartCard title="Rides Per Minute" subtitle="Completed rides throughout simulation">
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={result.time_series} barSize={6}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="minute" tick={{ fill: '#8892b0', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#8892b0', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="rides" name="Rides" fill="#4f8ef7" radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              {/* Recommendations */}
              <div className="sim-recommendations">
                <h3 className="recs-title">🎯 System Recommendations</h3>
                {result.recommendations?.map((rec, i) => (
                  <div key={i} className="rec-item">
                    <span className="rec-text">{rec}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
