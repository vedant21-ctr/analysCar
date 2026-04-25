"""
Urban Mobility Intelligence OS
Simulation Engine — Monte Carlo city simulation with configurable parameters
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import random


# ─── Simulation Config ────────────────────────────────────────────────────────
@dataclass
class SimulationConfig:
    n_drivers: int = 500
    demand_multiplier: float = 1.0       # 0.5 = half demand, 2.0 = double
    weather: str = "Clear"               # Clear | Rainy | Fog | Snow
    traffic_level: str = "Medium"        # Low | Medium | High
    event_flag: int = 0                  # 0 or 1
    hour: int = 8                        # 0–23
    n_zones: int = 20
    simulation_steps: int = 60           # minutes
    base_fare: float = 12.0
    surge_threshold: float = 1.4         # demand score above which surge kicks in


# ─── Simulation Result ────────────────────────────────────────────────────────
@dataclass
class SimulationResult:
    config: SimulationConfig
    predicted_demand: float
    total_rides: int
    avg_wait_time: float
    total_revenue: float
    avg_driver_earnings: float
    surge_multiplier: float
    cancellation_rate: float
    utilization_rate: float
    zone_breakdown: List[Dict]
    time_series: List[Dict]
    recommendations: List[str]


# ─── Core Engine ──────────────────────────────────────────────────────────────
class SimulationEngine:
    """
    Monte Carlo simulation of urban ride-hailing dynamics.
    Models demand, supply, pricing, and driver behaviour.
    """

    WEATHER_DEMAND_BOOST = {"Clear": 1.0, "Cloudy": 1.05, "Rainy": 1.35, "Fog": 1.15, "Snow": 1.45}
    WEATHER_CANCEL_BOOST = {"Clear": 0.0, "Cloudy": 0.02, "Rainy": 0.08, "Fog": 0.04, "Snow": 0.12}
    TRAFFIC_DURATION_MULT = {"Low": 1.0, "Medium": 1.3, "High": 1.75}
    TRAFFIC_WAIT_BOOST = {"Low": -1.0, "Medium": 0.0, "High": 2.5}

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        random.seed(seed)

    def _hour_demand_base(self, hour: int) -> float:
        if 7 <= hour <= 9:   return 2.0
        if 11 <= hour <= 13: return 1.3
        if 17 <= hour <= 20: return 2.3
        if 22 <= hour <= 23: return 1.5
        if 0 <= hour <= 5:   return 0.35
        return 0.9

    def _compute_surge(self, demand_score: float, cfg: SimulationConfig) -> float:
        if demand_score > cfg.surge_threshold * 1.5:
            return round(self.rng.uniform(1.8, 2.5), 2)
        if demand_score > cfg.surge_threshold:
            return round(self.rng.uniform(1.2, 1.8), 2)
        return 1.0

    def run(self, cfg: SimulationConfig) -> SimulationResult:
        """Execute a full simulation run and return structured results."""

        # ── Demand calculation ─────────────────────────────────────────────
        base_demand = self._hour_demand_base(cfg.hour)
        weather_boost = self.WEATHER_DEMAND_BOOST[cfg.weather]
        demand_score = base_demand * cfg.demand_multiplier * weather_boost * (1 + 0.4 * cfg.event_flag)
        demand_score = float(np.clip(demand_score + self.rng.normal(0, 0.1), 0.1, 4.0))

        # ── Surge pricing ──────────────────────────────────────────────────
        surge = self._compute_surge(demand_score, cfg)

        # ── Ride volume ────────────────────────────────────────────────────
        rides_per_step = int(demand_score * cfg.n_drivers * 0.15 * cfg.demand_multiplier)
        total_rides = rides_per_step * cfg.simulation_steps

        # ── Wait time ──────────────────────────────────────────────────────
        supply_ratio = cfg.n_drivers / max(total_rides / cfg.simulation_steps, 1)
        base_wait = max(1.0, 8.0 / supply_ratio)
        wait_boost = self.TRAFFIC_WAIT_BOOST[cfg.traffic_level]
        avg_wait = round(base_wait + wait_boost + self.rng.normal(0, 0.5), 1)
        avg_wait = max(1.0, avg_wait)

        # ── Cancellation ───────────────────────────────────────────────────
        cancel_rate = (
            0.05
            + (avg_wait > 10) * 0.12
            + self.WEATHER_CANCEL_BOOST[cfg.weather]
            + (demand_score > 1.8) * 0.05
        )
        cancel_rate = round(float(np.clip(cancel_rate, 0, 0.5)), 3)

        # ── Revenue ────────────────────────────────────────────────────────
        duration_mult = self.TRAFFIC_DURATION_MULT[cfg.traffic_level]
        avg_fare = cfg.base_fare * surge * duration_mult
        completed_rides = int(total_rides * (1 - cancel_rate))
        total_revenue = round(completed_rides * avg_fare, 2)
        avg_driver_earnings = round(avg_fare * 0.76, 2)

        # ── Utilization ────────────────────────────────────────────────────
        utilization = round(min(1.0, completed_rides / (cfg.n_drivers * cfg.simulation_steps * 0.5)), 3)

        # ── Zone breakdown ─────────────────────────────────────────────────
        zone_breakdown = []
        for z in range(1, cfg.n_zones + 1):
            zone_demand = demand_score * self.rng.uniform(0.5, 1.5)
            zone_rides = int(completed_rides / cfg.n_zones * self.rng.uniform(0.6, 1.4))
            zone_breakdown.append({
                "zone_id": f"Z{z:02d}",
                "demand_score": round(zone_demand, 3),
                "rides": zone_rides,
                "revenue": round(zone_rides * avg_fare, 2),
                "avg_wait": round(avg_wait * self.rng.uniform(0.7, 1.3), 1),
            })

        # ── Time series (per minute) ───────────────────────────────────────
        time_series = []
        cumulative_revenue = 0.0
        for step in range(cfg.simulation_steps):
            step_rides = int(rides_per_step * (1 - cancel_rate) * self.rng.uniform(0.8, 1.2))
            step_revenue = round(step_rides * avg_fare, 2)
            cumulative_revenue += step_revenue
            time_series.append({
                "minute": step,
                "rides": step_rides,
                "revenue": step_revenue,
                "cumulative_revenue": round(cumulative_revenue, 2),
                "active_drivers": int(cfg.n_drivers * utilization * self.rng.uniform(0.85, 1.0)),
            })

        # ── Recommendations ────────────────────────────────────────────────
        recommendations = self._generate_recommendations(
            demand_score, avg_wait, cancel_rate, surge, cfg
        )

        return SimulationResult(
            config=cfg,
            predicted_demand=round(demand_score, 3),
            total_rides=total_rides,
            avg_wait_time=avg_wait,
            total_revenue=total_revenue,
            avg_driver_earnings=avg_driver_earnings,
            surge_multiplier=surge,
            cancellation_rate=cancel_rate,
            utilization_rate=utilization,
            zone_breakdown=zone_breakdown,
            time_series=time_series,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self, demand: float, wait: float, cancel: float, surge: float, cfg: SimulationConfig
    ) -> List[str]:
        recs = []
        if demand > 1.8:
            recs.append(f"🔥 High demand detected (score={demand:.2f}). Deploy {int(cfg.n_drivers * 0.2)} additional drivers.")
        if wait > 8:
            recs.append(f"⏱️ Average wait {wait:.1f} min is above threshold. Incentivize drivers in high-demand zones.")
        if cancel > 0.15:
            recs.append(f"❌ Cancellation rate {cancel*100:.1f}% is elevated. Consider reducing wait time or offering bonuses.")
        if surge > 1.5:
            recs.append(f"💰 Surge at {surge:.1f}x — communicate transparently to users to reduce churn.")
        if cfg.weather in ["Rainy", "Snow"]:
            recs.append(f"🌧️ {cfg.weather} weather increases demand by {int((self.WEATHER_DEMAND_BOOST[cfg.weather]-1)*100)}%. Pre-position drivers near transit hubs.")
        if cfg.event_flag:
            recs.append("🎉 Event detected. Activate event-mode surge caps and pre-deploy drivers to venue zones.")
        if not recs:
            recs.append("✅ System operating within normal parameters. No immediate action required.")
        return recs

    def sensitivity_analysis(self, base_cfg: SimulationConfig, param: str, values: list) -> pd.DataFrame:
        """Run simulation across a range of parameter values."""
        rows = []
        for v in values:
            cfg = SimulationConfig(**{**base_cfg.__dict__, param: v})
            result = self.run(cfg)
            rows.append({
                param: v,
                "demand": result.predicted_demand,
                "rides": result.total_rides,
                "revenue": result.total_revenue,
                "wait_time": result.avg_wait_time,
                "cancel_rate": result.cancellation_rate,
                "surge": result.surge_multiplier,
            })
        return pd.DataFrame(rows)
