import React from 'react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts';
import KPICard from '../components/KPICard';
import ChartCard from '../components/ChartCard';
import { SkeletonCard } from '../components/LoadingSpinner';
import { useApi } from '../hooks/useApi';
import './Overview.css';

const MONTH_NAMES = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const WEATHER_COLORS = {
  Clear: '#4f8ef7', Cloudy: '#8892b0', Rainy: '#06b6d4', Fog: '#a855f7', Snow: '#ec4899',
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'rgba(10,14,26,0.95)', border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: 10, padding: '10px 14px', fontSize: 12,
    }}>
      <p style={{ color: '#8892b0', marginBottom: 6 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color, fontWeight: 600 }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toLocaleString() : p.value}
        </p>
      ))}
    </div>
  );
};

export default function Overview() {
  const { data: stats, loading: statsLoading } = useApi('/api/overview');
  const { data: monthly, loading: monthlyLoading } = useApi('/api/demand/monthly');
  const { data: weather, loading: weatherLoading } = useApi('/api/weather/analysis');
  const { data: hourly, loading: hourlyLoading } = useApi('/api/demand/hourly');

  const monthlyFormatted = Array.isArray(monthly) ? monthly.map(m => ({
    ...m,
    name: MONTH_NAMES[m.month],
    revenue_k: +(m.total_revenue / 1000).toFixed(1),
  })) : [];

  const weatherPie = Array.isArray(weather) ? weather.map(w => ({
    name: w.weather,
    value: w.total_rides,
    color: WEATHER_COLORS[w.weather] || '#4f8ef7',
  })) : [];

  return (
    <div className="page">
      {/* Header */}
      <div className="page-header">
        <div className="overview-header-content">
          <div>
            <h1 className="page-title gradient-text-blue">City Intelligence Dashboard</h1>
            <p className="page-subtitle">Real-time urban mobility analytics · 50,000+ rides analyzed</p>
          </div>
          <div className="live-badge">
            <span className="live-dot" />
            <span>Live Analytics</span>
          </div>
        </div>
      </div>

      {/* KPI Grid */}
      <section className="section">
        {statsLoading ? (
          <div className="grid-4">
            {[...Array(4)].map((_, i) => <SkeletonCard key={i} height={160} />)}
          </div>
        ) : (
          <div className="grid-4">
            <KPICard
              icon="🚗"
              label="Total Rides"
              value={stats?.total_rides || 0}
              gradient="blue"
              change={12.4}
              changeLabel="vs last period"
              delay={0}
            />
            <KPICard
              icon="💰"
              label="Total Revenue"
              value={+(stats?.total_revenue / 1000 || 0).toFixed(0)}
              prefix="$"
              suffix="K"
              gradient="green"
              change={8.7}
              changeLabel="vs last period"
              delay={0.1}
            />
            <KPICard
              icon="⏱️"
              label="Avg Wait Time"
              value={stats?.avg_wait || 0}
              suffix=" min"
              decimals={1}
              gradient="orange"
              change={-5.2}
              changeLabel="improvement"
              delay={0.2}
            />
            <KPICard
              icon="❌"
              label="Cancellation Rate"
              value={stats?.cancellation_rate || 0}
              suffix="%"
              decimals={1}
              gradient="purple"
              change={-2.1}
              changeLabel="improvement"
              delay={0.3}
            />
          </div>
        )}
      </section>

      {/* Second KPI row */}
      <section className="section">
        {statsLoading ? (
          <div className="grid-4">
            {[...Array(4)].map((_, i) => <SkeletonCard key={i} height={140} />)}
          </div>
        ) : (
          <div className="grid-4">
            <KPICard
              icon="📍"
              label="Avg Fare"
              value={stats?.avg_fare || 0}
              prefix="$"
              decimals={2}
              gradient="pink"
              delay={0.1}
            />
            <KPICard
              icon="🛣️"
              label="Avg Distance"
              value={stats?.avg_distance || 0}
              suffix=" km"
              decimals={1}
              gradient="blue"
              delay={0.15}
            />
            <KPICard
              icon="⚡"
              label="Surge Rate"
              value={stats?.surge_rate || 0}
              suffix="%"
              decimals={1}
              gradient="orange"
              delay={0.2}
            />
            <KPICard
              icon="🏆"
              label="Peak Hour"
              value={stats?.busiest_hour || 0}
              suffix=":00"
              gradient="green"
              delay={0.25}
            />
          </div>
        )}
      </section>

      {/* Charts row 1 */}
      <section className="section grid-2">
        <ChartCard
          title="Monthly Revenue Trend"
          subtitle="Total fare revenue across 12 months"
        >
          {monthlyLoading ? <SkeletonCard height={260} /> : (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={monthlyFormatted}>
                <defs>
                  <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4f8ef7" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#4f8ef7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}K`} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="revenue_k" name="Revenue ($K)" stroke="#4f8ef7" strokeWidth={2} fill="url(#revGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard
          title="Rides by Weather"
          subtitle="Distribution of rides across weather conditions"
        >
          {weatherLoading ? <SkeletonCard height={260} /> : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={weatherPie}
                  cx="50%"
                  cy="50%"
                  innerRadius={70}
                  outerRadius={100}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {weatherPie?.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  formatter={(value) => <span style={{ color: '#8892b0', fontSize: 12 }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </section>

      {/* Hourly demand */}
      <section className="section">
        <ChartCard
          title="24-Hour Demand Pattern"
          subtitle="Average demand score and ride volume by hour of day"
        >
          {hourlyLoading ? <SkeletonCard height={280} /> : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={hourly} barSize={18}>
                <defs>
                  <linearGradient id="demandGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#a855f7" stopOpacity={0.9} />
                    <stop offset="100%" stopColor="#4f8ef7" stopOpacity={0.6} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="hour" tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false}
                  tickFormatter={h => `${h}:00`} />
                <YAxis tick={{ fill: '#8892b0', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="total_rides" name="Total Rides" fill="url(#demandGrad)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </section>

      {/* Zone top performers */}
      <section className="section">
        <ChartCard title="System Status" subtitle="Platform health indicators">
          <div className="status-grid">
            {[
              { label: 'Data Pipeline', status: 'Operational', color: 'green' },
              { label: 'ML Models', status: 'Active', color: 'green' },
              { label: 'Simulation Engine', status: 'Ready', color: 'blue' },
              { label: 'Agent System', status: 'Standby', color: 'orange' },
              { label: 'Decision Engine', status: 'Operational', color: 'green' },
              { label: 'AI Insights', status: 'Active', color: 'purple' },
            ].map((item, i) => (
              <div key={i} className="status-item">
                <span className={`status-indicator ${item.color}`} />
                <span className="status-name">{item.label}</span>
                <span className={`status-value ${item.color}`}>{item.status}</span>
              </div>
            ))}
          </div>
        </ChartCard>
      </section>
    </div>
  );
}
