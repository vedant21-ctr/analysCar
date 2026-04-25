"""
Urban Mobility Intelligence OS
Dataset Generator - Creates a rich synthetic Uber-like rides dataset
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

# ─── Configuration ────────────────────────────────────────────────────────────
N_RIDES = 50_000
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2023, 12, 31)
ZONES = [f"Z{i:02d}" for i in range(1, 21)]  # 20 city zones

ZONE_PROFILES = {
    f"Z{i:02d}": {
        "base_demand": np.random.uniform(0.4, 1.0),
        "avg_fare": np.random.uniform(8, 35),
        "avg_distance": np.random.uniform(1.5, 12.0),
        "commercial": np.random.choice([True, False]),
    }
    for i in range(1, 21)
}

WEATHER_OPTIONS = ["Clear", "Cloudy", "Rainy", "Fog", "Snow"]
WEATHER_WEIGHTS = [0.50, 0.20, 0.18, 0.07, 0.05]

TRAFFIC_OPTIONS = ["Low", "Medium", "High"]
TRAFFIC_WEIGHTS = [0.30, 0.45, 0.25]


def hour_demand_multiplier(hour: int) -> float:
    """Simulate realistic demand curves throughout the day."""
    if 7 <= hour <= 9:    return np.random.uniform(1.6, 2.2)   # morning rush
    if 11 <= hour <= 13:  return np.random.uniform(1.1, 1.4)   # lunch
    if 17 <= hour <= 20:  return np.random.uniform(1.8, 2.5)   # evening rush
    if 22 <= hour <= 23:  return np.random.uniform(1.3, 1.7)   # nightlife
    if 0 <= hour <= 5:    return np.random.uniform(0.2, 0.5)   # late night
    return np.random.uniform(0.7, 1.1)


def weather_multiplier(weather: str) -> float:
    return {"Clear": 1.0, "Cloudy": 1.05, "Rainy": 1.35, "Fog": 1.15, "Snow": 1.45}[weather]


def traffic_duration_multiplier(traffic: str) -> float:
    return {"Low": 1.0, "Medium": 1.3, "High": 1.75}[traffic]


def generate_dataset() -> pd.DataFrame:
    print("🚀 Generating Urban Mobility Dataset...")

    date_range = pd.date_range(START_DATE, END_DATE, freq="h")
    records = []

    ride_id = 1
    for _ in range(N_RIDES):
        # ── Temporal features ──────────────────────────────────────────────
        ts = START_DATE + timedelta(
            seconds=random.randint(0, int((END_DATE - START_DATE).total_seconds()))
        )
        hour = ts.hour
        day = ts.day
        weekday = ts.weekday()          # 0=Mon … 6=Sun
        month = ts.month
        is_weekend = int(weekday >= 5)

        # ── Zone & environment ─────────────────────────────────────────────
        zone_id = random.choice(ZONES)
        zp = ZONE_PROFILES[zone_id]
        weather = random.choices(WEATHER_OPTIONS, WEATHER_WEIGHTS)[0]
        traffic = random.choices(TRAFFIC_OPTIONS, TRAFFIC_WEIGHTS)[0]
        event_flag = int(random.random() < 0.08)   # 8% chance of local event

        # ── Demand & ride metrics ──────────────────────────────────────────
        h_mult = hour_demand_multiplier(hour)
        w_mult = weather_multiplier(weather)
        demand_score_raw = zp["base_demand"] * h_mult * w_mult * (1 + 0.4 * event_flag)
        demand_score = round(np.clip(demand_score_raw + np.random.normal(0, 0.1), 0.1, 3.0), 3)

        distance = round(max(0.5, np.random.normal(zp["avg_distance"], 2.0)), 2)
        duration_base = distance * 3.5  # minutes per km baseline
        duration = round(duration_base * traffic_duration_multiplier(traffic) + np.random.normal(0, 2), 1)
        duration = max(2.0, duration)

        # ── Surge & fare ───────────────────────────────────────────────────
        surge_multiplier = 1.0
        if demand_score > 1.5:  surge_multiplier = round(np.random.uniform(1.3, 2.5), 2)
        elif demand_score > 1.0: surge_multiplier = round(np.random.uniform(1.0, 1.3), 2)

        base_fare = zp["avg_fare"] * (distance / zp["avg_distance"])
        fare = round(base_fare * surge_multiplier + np.random.normal(0, 1.5), 2)
        fare = max(3.0, fare)

        # ── Wait time ──────────────────────────────────────────────────────
        wait_time = round(max(1.0, np.random.normal(
            5 + demand_score * 3 - (2 if traffic == "Low" else 0), 2
        )), 1)

        # ── Driver metrics ─────────────────────────────────────────────────
        driver_earnings = round(fare * np.random.uniform(0.72, 0.80), 2)
        driver_opportunity_score = round(
            (driver_earnings / max(wait_time, 1)) * demand_score, 3
        )

        # ── Cancellation ───────────────────────────────────────────────────
        cancel_prob = 0.05
        if wait_time > 10: cancel_prob += 0.12
        if weather in ["Rainy", "Snow"]: cancel_prob += 0.08
        if demand_score > 1.8: cancel_prob += 0.05
        cancelled = int(random.random() < cancel_prob)

        # ── Derived features ───────────────────────────────────────────────
        efficiency = round(fare / max(distance, 0.1), 3)
        peak_hour = int(hour in list(range(7, 10)) + list(range(17, 21)))
        congestion_index = round(
            ({"Low": 0.2, "Medium": 0.5, "High": 0.9}[traffic] + demand_score * 0.3) / 1.3, 3
        )
        cancellation_risk = round(np.clip(cancel_prob, 0, 1), 3)
        zone_demand_density = round(demand_score * zp["base_demand"], 3)

        records.append({
            "ride_id": ride_id,
            "timestamp": ts,
            "hour": hour,
            "day": day,
            "weekday": weekday,
            "month": month,
            "is_weekend": is_weekend,
            "zone_id": zone_id,
            "weather": weather,
            "traffic_level": traffic,
            "event_flag": event_flag,
            "distance_km": distance,
            "duration_min": duration,
            "fare_usd": fare,
            "surge_multiplier": surge_multiplier,
            "wait_time_min": wait_time,
            "driver_earnings_usd": driver_earnings,
            "cancelled": cancelled,
            "demand_score": demand_score,
            "efficiency": efficiency,
            "peak_hour": peak_hour,
            "congestion_index": congestion_index,
            "cancellation_risk": cancellation_risk,
            "zone_demand_density": zone_demand_density,
            "driver_opportunity_score": driver_opportunity_score,
        })
        ride_id += 1

    df = pd.DataFrame(records)
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)

    out_path = os.path.join(os.path.dirname(__file__), "uber_rides.csv")
    df.to_csv(out_path, index=False)
    print(f"✅ Dataset saved → {out_path}  ({len(df):,} rows × {len(df.columns)} cols)")
    return df


if __name__ == "__main__":
    df = generate_dataset()
    print(df.describe())
