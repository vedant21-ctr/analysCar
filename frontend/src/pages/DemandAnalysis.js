import React, { useState } from 'react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import ChartCard from '../components/ChartCard';
import { SkeletonCard } from '../components/LoadingSpinner';
import { useApi } from '../hooks/useApi';
import './DemandAnalysis.css';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <p className="tooltip-label">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toFixed(3) : p.value}</strong>
        </p>
      ))}
    </div>
  );
};

export default function DemandAnalysis() {
  const [activeTab, setActiveTab] = useState('hourly');
  const { data: hourlyRaw, loading: hourlyLoading } = useApi('/api/demand/hourly');
  const { data: weeklyRaw, loading: weeklyLoading } = useApi('/api/demand/weekly');
  const { data: weatherRaw, loading: weatherLoading } = useApi('/api/weather/analysis');
  const { data: zonesRaw, loading: zonesLoading } = useApi('/api/zones/heatmap');

  // Safe arrays — never null
  const hourly = Array.isArray(hourlyRaw) ? hourlyRaw : [];
  const weekly = Array.isArray(weeklyRaw) ? weeklyRaw.map(w => ({ ...w, name: DAYS[w.weekday] || w.weekday })) : [];
  const weather = Array.isArray(weatherRaw) ? weatherRaw : [];
  const zones = Array.isArray(zonesRaw) ? zonesRaw : [];
  const topZones = [...zones].sort((a, b) => b.avg_demand - a.avg_demand).slice(0, 10);
  const radarData = weather.map(w => ({
    subject: w.weather,
    demand: +(w.avg_demand * 100).toFixed(0),
    fare: +(w.avg_fare).toFixed(0),
    cancel: +(w.cancel_rate * 100).toFixed(0),
  }));

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title gradient-text-purple">Demand Analysis</h1>
        <p className="page-subtitle">Deep-dive into temporal patterns, zone heatmaps, and weather correlations</p>
      </div>

      <div className="tab-bar">
        {['hourly', 'weekly', 'zones', 'weather'].map(tab => (
          <button key={tab} className={`tab-btn ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Hourly */}
      {activeTab === 'hourly' && (
        <div className="section">
          <div className="grid-2">
            <ChartCard title="Hourly Demand Score" subtitle="Average demand intensity by hour">
              {hourlyLoading || !hourly.length ? <SkeletonCard height={280} /> : (
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={hourly}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="hour" tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={h => `${h}h`} />
                    <YAxis tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Line type="monotone" dataKey="avg_demand" name="Demand Score" stroke="#a855f7" strokeWidth={3} dot={false} activeDot={{ r: 5 }} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </ChartCard>

            <ChartCard title="Surge Rate by Hour" subtitle="% of rides with surge pricing active">
              {hourlyLoading || !hourly.length ? <SkeletonCard height={280} /> : (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={hourly} barSize={14}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="hour" tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={h => `${h}h`} />
                    <YAxis tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="surge_rate" name="Surge Rate" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </ChartCard>
          </div>

          <ChartCard title="Hourly Metrics Table" subtitle="Full breakdown of all hourly KPIs" className="section">
            {hourlyLoading || !hourly.length ? <SkeletonCard height={300} /> : (
              <div className="metrics-table-wrapper">
                <table className="metrics-table">
                  <thead>
                    <tr>
                      <th>Hour</th><th>Avg Demand</th><th>Total Rides</th>
                      <th>Avg Fare</th><th>Surge Rate</th><th>Intensity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {hourly.map(row => {
                      const intensity = Math.min(1, (row.avg_demand || 0) / 2.5);
                      return (
                        <tr key={row.hour}>
                          <td className="hour-cell">{row.hour}:00</td>
                          <td>{(row.avg_demand || 0).toFixed(3)}</td>
                          <td>{(row.total_rides || 0).toLocaleString()}</td>
                          <td>${(row.avg_fare || 0).toFixed(2)}</td>
                          <td>{((row.surge_rate || 0) * 100).toFixed(1)}%</td>
                          <td>
                            <div className="intensity-bar">
                              <div className="intensity-fill" style={{ width: `${intensity * 100}%`, background: `hsl(${220 + intensity * 60}, 80%, 60%)` }} />
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </ChartCard>
        </div>
      )}

      {/* Weekly */}
      {activeTab === 'weekly' && (
        <div className="section grid-2">
          <ChartCard title="Weekly Demand Pattern" subtitle="Average demand by day of week">
            {weeklyLoading || !weekly.length ? <SkeletonCard height={300} /> : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={weekly} barSize={32}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" tick={{ fill: '#8892b0', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="avg_demand" name="Avg Demand" fill="#10b981" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>

          <ChartCard title="Weekly Avg Fare" subtitle="Average fare by day of week">
            {weeklyLoading || !weekly.length ? <SkeletonCard height={300} /> : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={weekly} barSize={32}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" tick={{ fill: '#8892b0', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="avg_fare" name="Avg Fare ($)" fill="#a855f7" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </div>
      )}

      {/* Zones */}
      {activeTab === 'zones' && (
        <div className="section">
          <ChartCard title="Zone Demand Heatmap" subtitle="Top 10 zones by average demand score">
            {zonesLoading || !topZones.length ? <SkeletonCard height={320} /> : (
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={topZones} layout="vertical" barSize={18}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis type="number" tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis dataKey="zone_id" type="category" tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} width={40} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="avg_demand" name="Avg Demand" fill="#4f8ef7" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>

          <div className="grid-3 section">
            {topZones.slice(0, 6).map((zone, i) => (
              <div key={zone.zone_id} className="zone-card">
                <div className="zone-rank">#{i + 1}</div>
                <div className="zone-id">{zone.zone_id}</div>
                <div className="zone-metrics">
                  <div className="zone-metric"><span className="zone-metric-label">Demand</span><span className="zone-metric-value" style={{ color: '#4f8ef7' }}>{(zone.avg_demand || 0).toFixed(3)}</span></div>
                  <div className="zone-metric"><span className="zone-metric-label">Rides</span><span className="zone-metric-value">{(zone.total_rides || 0).toLocaleString()}</span></div>
                  <div className="zone-metric"><span className="zone-metric-label">Avg Fare</span><span className="zone-metric-value" style={{ color: '#10b981' }}>${(zone.avg_fare || 0).toFixed(2)}</span></div>
                  <div className="zone-metric"><span className="zone-metric-label">Cancel %</span><span className="zone-metric-value" style={{ color: '#ef4444' }}>{((zone.cancel_rate || 0) * 100).toFixed(1)}%</span></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Weather */}
      {activeTab === 'weather' && (
        <div className="section grid-2">
          <ChartCard title="Weather Impact Radar" subtitle="Multi-metric comparison across weather conditions">
            {weatherLoading || !radarData.length ? <SkeletonCard height={320} /> : (
              <ResponsiveContainer width="100%" height={320}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(255,255,255,0.1)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#8892b0', fontSize: 11 }} />
                  <PolarRadiusAxis tick={{ fill: '#8892b0', fontSize: 9 }} />
                  <Radar name="Demand" dataKey="demand" stroke="#4f8ef7" fill="#4f8ef7" fillOpacity={0.2} />
                  <Radar name="Fare" dataKey="fare" stroke="#10b981" fill="#10b981" fillOpacity={0.2} />
                  <Radar name="Cancel%" dataKey="cancel" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} />
                </RadarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>

          <ChartCard title="Cancellation Rate by Weather" subtitle="How weather affects ride completion">
            {weatherLoading || !weather.length ? <SkeletonCard height={320} /> : (
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={weather} barSize={28}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="weather" tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="cancel_rate" name="Cancel Rate" fill="#ef4444" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </div>
      )}
    </div>
  );
}
