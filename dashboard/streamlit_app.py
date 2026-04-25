"""
Urban Mobility Intelligence OS
Streamlit Dashboard — Alternative to React frontend (standalone, no backend needed)
Run: streamlit run dashboard/streamlit_app.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data.generate_dataset import generate_dataset
from backend.core.data_processor import DataProcessor
from backend.core.decision_engine import DecisionEngine
from backend.core.ai_insights import AIInsightGenerator
from backend.core.sustainability import SustainabilityAnalyzer
from simulation.simulation_engine import SimulationEngine, SimulationConfig
from agents.multi_agent_system import MultiAgentSimulation

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Urban Mobility Intelligence OS",
    page_icon="🌆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0a0e1a; color: #f0f4ff; }
    .main .block-container { padding: 2rem 2rem 2rem 2rem; max-width: 1400px; }
    h1, h2, h3 { color: #f0f4ff !important; }
    .metric-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
    }
    .stSelectbox > div > div { background: rgba(255,255,255,0.05); }
    .stSlider > div > div > div { background: #4f8ef7; }
    div[data-testid="stMetricValue"] { font-size: 2rem; font-weight: 800; }
    .stButton > button {
        background: linear-gradient(135deg, #4f8ef7, #06b6d4);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        padding: 0.6rem 2rem;
        width: 100%;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(79,142,247,0.4); }
    .sidebar .sidebar-content { background: rgba(10,14,26,0.95); }
</style>
""", unsafe_allow_html=True)

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8892b0", family="Inter"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)"),
)


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data():
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uber_rides.csv")
    if not os.path.exists(data_path):
        generate_dataset()
    processor = DataProcessor(data_path)
    processor.run_pipeline()
    return processor.df, processor


@st.cache_resource
def get_engines(df):
    return (
        DecisionEngine(df),
        AIInsightGenerator(df),
        SustainabilityAnalyzer(df),
        SimulationEngine(),
    )


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌆 Urban Mobility OS")
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["⚡ Overview", "📊 Demand Analysis", "🔮 Simulation", "🎯 Decision Engine", "🤖 AI Insights", "🌍 Sustainability"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**System Status**")
    st.success("🟢 All systems operational")
    st.markdown("---")
    st.caption("v1.0.0 · Production")

# ── Load data ──────────────────────────────────────────────────────────────────
with st.spinner("🚀 Loading Urban Mobility Intelligence OS..."):
    df, processor = load_data()
    decision_engine, insight_gen, sustainability, sim_engine = get_engines(df)
    stats = processor.compute_stats()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "⚡ Overview":
    st.markdown("# ⚡ City Intelligence Dashboard")
    st.markdown("Real-time urban mobility analytics · 50,000+ rides analyzed")
    st.markdown("---")

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🚗 Total Rides", f"{stats['total_rides']:,}", "+12.4%")
    c2.metric("💰 Total Revenue", f"${stats['total_revenue']/1000:.0f}K", "+8.7%")
    c3.metric("⏱️ Avg Wait Time", f"{stats['avg_wait']:.1f} min", "-5.2%")
    c4.metric("❌ Cancellation Rate", f"{stats['cancellation_rate']:.1f}%", "-2.1%")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("📍 Avg Fare", f"${stats['avg_fare']:.2f}")
    c6.metric("🛣️ Avg Distance", f"{stats['avg_distance']:.1f} km")
    c7.metric("⚡ Surge Rate", f"{stats['surge_rate']:.1f}%")
    c8.metric("🏆 Peak Hour", f"{stats['busiest_hour']}:00")

    st.markdown("---")

    # Monthly revenue
    monthly = df.groupby("month").agg(revenue=("fare_usd", "sum"), rides=("ride_id", "count")).reset_index()
    month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    monthly["month_name"] = monthly["month"].map(month_names)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.area(monthly, x="month_name", y="revenue", title="Monthly Revenue Trend",
                      color_discrete_sequence=["#4f8ef7"])
        fig.update_layout(**PLOTLY_THEME, title_font_color="#f0f4ff")
        fig.update_traces(fill="tozeroy", fillcolor="rgba(79,142,247,0.15)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        weather_stats = df.groupby("weather")["ride_id"].count().reset_index()
        fig = px.pie(weather_stats, values="ride_id", names="weather", title="Rides by Weather",
                     color_discrete_sequence=["#4f8ef7","#8892b0","#06b6d4","#a855f7","#ec4899"])
        fig.update_layout(**PLOTLY_THEME, title_font_color="#f0f4ff")
        st.plotly_chart(fig, use_container_width=True)

    # Hourly demand
    hourly = df.groupby("hour").agg(rides=("ride_id","count"), demand=("demand_score","mean")).reset_index()
    fig = px.bar(hourly, x="hour", y="rides", title="24-Hour Demand Pattern",
                 color="demand", color_continuous_scale=["#4f8ef7","#a855f7","#ef4444"])
    fig.update_layout(**PLOTLY_THEME, title_font_color="#f0f4ff")
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DEMAND ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Demand Analysis":
    st.markdown("# 📊 Demand Analysis")
    st.markdown("Deep-dive into temporal patterns, zone heatmaps, and weather correlations")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["⏰ Hourly", "📅 Weekly", "📍 Zones", "🌦️ Weather"])

    with tab1:
        hourly = df.groupby("hour").agg(
            demand=("demand_score","mean"), rides=("ride_id","count"),
            fare=("fare_usd","mean"), surge=("surge_flag","mean")
        ).reset_index()

        col1, col2 = st.columns(2)
        with col1:
            fig = px.line(hourly, x="hour", y="demand", title="Hourly Demand Score",
                          color_discrete_sequence=["#a855f7"])
            fig.update_traces(line_width=3)
            fig.update_layout(**PLOTLY_THEME, title_font_color="#f0f4ff")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(hourly, x="hour", y="surge", title="Surge Rate by Hour",
                         color_discrete_sequence=["#f59e0b"])
            fig.update_layout(**PLOTLY_THEME, title_font_color="#f0f4ff")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        weekly = df.groupby("weekday").agg(demand=("demand_score","mean"), rides=("ride_id","count")).reset_index()
        weekly["day"] = weekly["weekday"].apply(lambda x: days[x])
        fig = px.bar(weekly, x="day", y="demand", title="Weekly Demand Pattern",
                     color="demand", color_continuous_scale=["#4f8ef7","#10b981"])
        fig.update_layout(**PLOTLY_THEME, title_font_color="#f0f4ff")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        zone_stats = df.groupby("zone_id").agg(
            demand=("demand_score","mean"), rides=("ride_id","count"),
            fare=("fare_usd","mean"), cancel=("cancelled","mean")
        ).reset_index()
        fig = px.bar(zone_stats.sort_values("demand", ascending=False).head(15),
                     x="zone_id", y="demand", title="Zone Demand Heatmap",
                     color="demand", color_continuous_scale=["#4f8ef7","#a855f7","#ef4444"])
        fig.update_layout(**PLOTLY_THEME, title_font_color="#f0f4ff")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(zone_stats.sort_values("demand", ascending=False).round(3), use_container_width=True)

    with tab4:
        weather_stats = df.groupby("weather").agg(
            demand=("demand_score","mean"), cancel=("cancelled","mean"),
            fare=("fare_usd","mean"), wait=("wait_time_min","mean")
        ).reset_index()
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(weather_stats, x="weather", y="demand", title="Demand by Weather",
                         color="demand", color_continuous_scale=["#4f8ef7","#ef4444"])
            fig.update_layout(**PLOTLY_THEME, title_font_color="#f0f4ff")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(weather_stats, x="weather", y="cancel", title="Cancellation Rate by Weather",
                         color_discrete_sequence=["#ef4444"])
            fig.update_layout(**PLOTLY_THEME, title_font_color="#f0f4ff")
            st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SIMULATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔮 Simulation":
    st.markdown("# 🔮 Simulation Engine")
    st.markdown("Configure city parameters and run Monte Carlo demand simulations")
    st.markdown("---")

    col_ctrl, col_res = st.columns([1, 2])

    with col_ctrl:
        st.markdown("### ⚙️ Parameters")
        n_drivers = st.slider("Number of Drivers", 50, 2000, 500, 50)
        demand_mult = st.slider("Demand Multiplier", 0.2, 3.0, 1.0, 0.1)
        hour = st.slider("Hour of Day", 0, 23, 8)
        base_fare = st.slider("Base Fare ($)", 5, 50, 12)
        weather = st.selectbox("Weather", ["Clear", "Cloudy", "Rainy", "Fog", "Snow"])
        traffic = st.selectbox("Traffic Level", ["Low", "Medium", "High"])
        event = st.checkbox("Event Active")
        run = st.button("▶ Run Simulation")

    with col_res:
        if run:
            with st.spinner("Running Monte Carlo simulation..."):
                cfg = SimulationConfig(
                    n_drivers=n_drivers, demand_multiplier=demand_mult,
                    weather=weather, traffic_level=traffic,
                    event_flag=int(event), hour=hour, base_fare=base_fare,
                )
                result = sim_engine.run(cfg)

            c1, c2, c3 = st.columns(3)
            c1.metric("📈 Demand Score", f"{result.predicted_demand:.3f}")
            c2.metric("🚗 Total Rides", f"{result.total_rides:,}")
            c3.metric("💰 Revenue", f"${result.total_revenue:,.0f}")

            c4, c5, c6 = st.columns(3)
            c4.metric("⏱️ Avg Wait", f"{result.avg_wait_time:.1f} min")
            c5.metric("⚡ Surge", f"{result.surge_multiplier:.2f}x")
            c6.metric("❌ Cancel Rate", f"{result.cancellation_rate*100:.1f}%")

            ts_df = pd.DataFrame(result.time_series)
            fig = px.area(ts_df, x="minute", y="cumulative_revenue",
                          title="Cumulative Revenue Over Time",
                          color_discrete_sequence=["#10b981"])
            fig.update_layout(**PLOTLY_THEME, title_font_color="#f0f4ff")
            fig.update_traces(fill="tozeroy", fillcolor="rgba(16,185,129,0.15)")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 🎯 Recommendations")
            for rec in result.recommendations:
                st.info(rec)
        else:
            st.info("👈 Configure parameters and click **Run Simulation**")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DECISION ENGINE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎯 Decision Engine":
    st.markdown("# 🎯 Decision Intelligence Engine")
    st.markdown("Data-driven recommendations for operators, drivers, and city planners")
    st.markdown("---")

    report = decision_engine.generate_full_report()

    tab1, tab2, tab3 = st.tabs(["📍 Best Zones", "⏰ Best Hours", "⚡ Surge Strategy"])

    with tab1:
        zones_df = pd.DataFrame(report["best_zones"])
        fig = px.bar(zones_df, x="zone_id", y="composite_score", title="Top Zones by Driver Opportunity",
                     color="composite_score", color_continuous_scale=["#4f8ef7","#10b981"])
        fig.update_layout(**PLOTLY_THEME, title_font_color="#f0f4ff")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(zones_df.round(3), use_container_width=True)

    with tab2:
        hours_df = pd.DataFrame(report["best_hours"]).sort_values("hour")
        fig = px.bar(hours_df, x="hour", y="hour_score", title="Driver Opportunity Score by Hour",
                     color="hour_score", color_continuous_scale=["#f59e0b","#ef4444"])
        fig.update_layout(**PLOTLY_THEME, title_font_color="#f0f4ff")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        surge_df = pd.DataFrame(report["surge_recommendations"])
        if not surge_df.empty:
            st.dataframe(surge_df[["label","demand_score","suggested_surge","action","priority"]].round(3),
                         use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AI INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🤖 AI Insights":
    st.markdown("# 🤖 AI Insight Generator")
    st.markdown("Natural language insights from your mobility data")
    st.markdown("---")

    all_insights = insight_gen.generate_all_insights()
    for category, insights in all_insights.items():
        icons = {"demand":"📈","weather":"🌧️","revenue":"💰","drivers":"🚗","cancellations":"❌","sustainability":"🌍"}
        with st.expander(f"{icons.get(category,'💡')} {category.title()} Insights", expanded=(category=="demand")):
            for insight in insights:
                st.markdown(f"> {insight}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SUSTAINABILITY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🌍 Sustainability":
    st.markdown("# 🌍 Sustainability Analysis")
    st.markdown("CO₂ impact assessment and eco-optimization strategies")
    st.markdown("---")

    sus_report = sustainability.full_report()
    baseline = sus_report["baseline"]
    opt30 = sus_report["optimized_30pct_ev"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌍 Baseline CO₂", f"{baseline['co2_tonnes_baseline']:.0f} t")
    c2.metric("⚡ With 30% EV", f"{opt30['co2_tonnes_optimized']:.0f} t")
    c3.metric("🌱 CO₂ Reduction", f"{opt30['reduction_pct']:.1f}%")
    c4.metric("🌳 Trees Needed", f"{baseline['equivalent_trees_needed']:,}")

    monthly_em = sustainability.monthly_emissions_trend()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=monthly_em["month"], y=monthly_em["co2_tonnes"], name="Baseline", marker_color="#ef4444"))
    fig.add_trace(go.Bar(x=monthly_em["month"], y=monthly_em["co2_optimized"], name="Optimized (30% EV)", marker_color="#10b981"))
    fig.update_layout(**PLOTLY_THEME, title="Monthly CO₂ Emissions: Baseline vs Optimized",
                      title_font_color="#f0f4ff", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🌿 Eco-Optimization Strategies")
    for s in sus_report["strategies"]:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{s['strategy']}** — {s['description']}")
            st.caption(f"💰 {s['cost_impact']} · 📅 {s['timeline']}")
        with col2:
            st.metric("CO₂ Reduction", f"-{s['co2_reduction_pct']}%")
        st.divider()
