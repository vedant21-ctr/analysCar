"""
Urban Mobility Intelligence OS
FastAPI Backend — REST API serving all analytics, ML, simulation, and agent data
"""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

# ── Path setup ─────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.core.data_processor import DataProcessor
from backend.core.decision_engine import DecisionEngine
from backend.core.ai_insights import AIInsightGenerator
from backend.core.sustainability import SustainabilityAnalyzer
from simulation.simulation_engine import SimulationEngine, SimulationConfig
from agents.multi_agent_system import MultiAgentSimulation
from models.ml_models import registry, train_all_models, predict_demand, predict_duration, predict_cancellation_prob

# ── App init ───────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Urban Mobility Intelligence OS",
    description="Next-generation smart city mobility analytics platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global state ───────────────────────────────────────────────────────────────
_processor: Optional[DataProcessor] = None
_df: Optional[pd.DataFrame] = None
_decision_engine: Optional[DecisionEngine] = None
_insight_gen: Optional[AIInsightGenerator] = None
_sustainability: Optional[SustainabilityAnalyzer] = None
_sim_engine = SimulationEngine()


def _get_df() -> pd.DataFrame:
    global _df, _processor, _decision_engine, _insight_gen, _sustainability
    if _df is None:
        data_path = ROOT / "data" / "uber_rides.csv"
        if not data_path.exists():
            # Generate dataset on first run
            sys.path.insert(0, str(ROOT / "data"))
            from generate_dataset import generate_dataset
            generate_dataset()

        _processor = DataProcessor(str(data_path))
        _processor.run_pipeline()
        _df = _processor.df

        # Use raw (unscaled) data for analytics engines
        raw_df = getattr(_processor, "_raw_df", _df)
        _decision_engine = DecisionEngine(raw_df)
        _insight_gen = AIInsightGenerator(raw_df)
        _sustainability = SustainabilityAnalyzer(raw_df)

        # Train models
        models_dir = str(ROOT / "models" / "saved")
        if not os.path.exists(models_dir) or not os.listdir(models_dir if os.path.exists(models_dir) else "."):
            train_all_models(_df, models_dir)
        else:
            try:
                registry.load(models_dir)
            except Exception:
                train_all_models(_df, models_dir)

    return _df


# ── Pydantic models ────────────────────────────────────────────────────────────
class SimulationRequest(BaseModel):
    n_drivers: int = Field(500, ge=10, le=5000)
    demand_multiplier: float = Field(1.0, ge=0.1, le=5.0)
    weather: str = Field("Clear")
    traffic_level: str = Field("Medium")
    event_flag: int = Field(0, ge=0, le=1)
    hour: int = Field(8, ge=0, le=23)
    base_fare: float = Field(12.0, ge=1.0, le=100.0)
    surge_threshold: float = Field(1.4, ge=1.0, le=3.0)


class PredictionRequest(BaseModel):
    hour: int = 8
    weekday: int = 1
    month: int = 6
    is_weekend: int = 0
    peak_hour: int = 1
    distance_km: float = 5.0
    surge_multiplier: float = 1.0
    wait_time_min: float = 5.0
    event_flag: int = 0
    traffic_numeric: float = 0.5
    congestion_index: float = 0.5
    zone_id_enc: int = 5
    weather_enc: int = 0
    traffic_level_enc: int = 1
    efficiency: float = 2.5
    zone_demand_density: float = 1.0


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Urban Mobility Intelligence OS API", "version": "1.0.0", "status": "operational"}


@app.get("/api/overview")
def get_overview():
    df = _get_df()
    stats = _processor.compute_stats()
    return JSONResponse(content=stats)


@app.get("/api/demand/hourly")
def demand_hourly():
    df = _get_df()
    raw = getattr(_processor, "_raw_df", df)
    hourly = raw.groupby("hour").agg(
        avg_demand=("demand_score", "mean"),
        total_rides=("ride_id", "count"),
        avg_fare=("fare_usd", "mean"),
        surge_rate=("surge_flag", "mean"),
    ).reset_index()
    return hourly.round(3).to_dict("records")


@app.get("/api/demand/weekly")
def demand_weekly():
    df = _get_df()
    raw = getattr(_processor, "_raw_df", df)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekly = raw.groupby("weekday").agg(
        avg_demand=("demand_score", "mean"),
        total_rides=("ride_id", "count"),
        avg_fare=("fare_usd", "mean"),
    ).reset_index()
    weekly["day_name"] = weekly["weekday"].apply(lambda x: days[x])
    return weekly.round(3).to_dict("records")


@app.get("/api/demand/monthly")
def demand_monthly():
    df = _get_df()
    raw = getattr(_processor, "_raw_df", df)
    monthly = raw.groupby("month").agg(
        total_rides=("ride_id", "count"),
        total_revenue=("fare_usd", "sum"),
        avg_demand=("demand_score", "mean"),
        avg_fare=("fare_usd", "mean"),
    ).reset_index()
    return monthly.round(2).to_dict("records")


@app.get("/api/zones/heatmap")
def zones_heatmap():
    df = _get_df()
    raw = getattr(_processor, "_raw_df", df)
    zone_stats = raw.groupby("zone_id").agg(
        total_rides=("ride_id", "count"),
        avg_demand=("demand_score", "mean"),
        avg_fare=("fare_usd", "mean"),
        avg_earnings=("driver_earnings_usd", "mean"),
        cancel_rate=("cancelled", "mean"),
        avg_wait=("wait_time_min", "mean"),
        congestion=("congestion_index", "mean"),
    ).reset_index()
    return zone_stats.round(3).to_dict("records")


@app.get("/api/weather/analysis")
def weather_analysis():
    df = _get_df()
    raw = getattr(_processor, "_raw_df", df)
    weather_stats = raw.groupby("weather").agg(
        total_rides=("ride_id", "count"),
        avg_demand=("demand_score", "mean"),
        avg_fare=("fare_usd", "mean"),
        cancel_rate=("cancelled", "mean"),
        avg_wait=("wait_time_min", "mean"),
        avg_duration=("duration_min", "mean"),
    ).reset_index()
    return weather_stats.round(3).to_dict("records")


@app.get("/api/revenue/trends")
def revenue_trends():
    df = _get_df()
    raw = getattr(_processor, "_raw_df", df)
    monthly = raw.groupby("month").agg(
        total_revenue=("fare_usd", "sum"),
        driver_earnings=("driver_earnings_usd", "sum"),
        total_rides=("ride_id", "count"),
    ).reset_index()
    return monthly.round(2).to_dict("records")


@app.get("/api/decision/report")
def decision_report():
    _get_df()
    return _decision_engine.generate_full_report()


@app.get("/api/insights")
def get_insights():
    _get_df()
    return _insight_gen.generate_all_insights()


@app.get("/api/sustainability")
def sustainability_report():
    _get_df()
    return _sustainability.full_report()


@app.post("/api/simulate")
def run_simulation(req: SimulationRequest):
    cfg = SimulationConfig(
        n_drivers=req.n_drivers,
        demand_multiplier=req.demand_multiplier,
        weather=req.weather,
        traffic_level=req.traffic_level,
        event_flag=req.event_flag,
        hour=req.hour,
        base_fare=req.base_fare,
        surge_threshold=req.surge_threshold,
    )
    result = _sim_engine.run(cfg)
    return {
        "predicted_demand": result.predicted_demand,
        "total_rides": result.total_rides,
        "avg_wait_time": result.avg_wait_time,
        "total_revenue": result.total_revenue,
        "avg_driver_earnings": result.avg_driver_earnings,
        "surge_multiplier": result.surge_multiplier,
        "cancellation_rate": result.cancellation_rate,
        "utilization_rate": result.utilization_rate,
        "zone_breakdown": result.zone_breakdown[:10],
        "time_series": result.time_series[:30],
        "recommendations": result.recommendations,
    }


@app.get("/api/simulate/sensitivity")
def sensitivity_analysis(
    param: str = Query("demand_multiplier"),
    steps: int = Query(10, ge=3, le=20),
):
    cfg = SimulationConfig()
    param_ranges = {
        "demand_multiplier": list(np.linspace(0.5, 3.0, steps)),
        "n_drivers": list(range(100, 1001, max(1, 900 // steps))),
        "hour": list(range(0, 24, max(1, 24 // steps))),
    }
    if param not in param_ranges:
        raise HTTPException(400, f"param must be one of {list(param_ranges.keys())}")
    df = _sim_engine.sensitivity_analysis(cfg, param, param_ranges[param])
    return df.round(3).to_dict("records")


@app.get("/api/agents/simulate")
def run_agent_simulation(
    n_drivers: int = Query(50, ge=10, le=200),
    n_users: int = Query(200, ge=50, le=1000),
    steps: int = Query(50, ge=10, le=200),
):
    sim = MultiAgentSimulation(n_drivers=n_drivers, n_users=n_users, steps=steps)
    summary = sim.run()
    return summary


@app.post("/api/predict/demand")
def predict_demand_endpoint(req: PredictionRequest):
    val = predict_demand(req.dict())
    return {"predicted_demand": round(val, 4)}


@app.post("/api/predict/duration")
def predict_duration_endpoint(req: PredictionRequest):
    val = predict_duration(req.dict())
    return {"predicted_duration_min": round(val, 2)}


@app.post("/api/predict/cancellation")
def predict_cancellation_endpoint(req: PredictionRequest):
    val = predict_cancellation_prob(req.dict())
    return {"cancellation_probability": round(val, 4)}


@app.get("/api/models/metrics")
def model_metrics():
    return registry.metrics


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
