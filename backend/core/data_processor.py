"""
Urban Mobility Intelligence OS
Core Data Processor — cleaning, validation, feature engineering
"""

from __future__ import annotations

import os
import warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from typing import Tuple

warnings.filterwarnings("ignore")


# ─── Constants ────────────────────────────────────────────────────────────────
CATEGORICAL_COLS = ["weather", "traffic_level", "zone_id"]
NUMERIC_COLS = [
    "distance_km", "duration_min", "fare_usd", "surge_multiplier",
    "wait_time_min", "driver_earnings_usd", "demand_score",
    "efficiency", "congestion_index", "cancellation_risk",
    "zone_demand_density", "driver_opportunity_score",
]
TARGET_DEMAND   = "demand_score"
TARGET_DURATION = "duration_min"
TARGET_CANCEL   = "cancelled"


class DataProcessor:
    """End-to-end data pipeline for Urban Mobility Intelligence OS."""

    def __init__(self, data_path: str):
        self.data_path = data_path
        self.raw_df: pd.DataFrame | None = None
        self.df: pd.DataFrame | None = None
        self.encoders: dict[str, LabelEncoder] = {}
        self.scaler = MinMaxScaler()
        self._stats: dict = {}

    # ── 1. Load ────────────────────────────────────────────────────────────────
    def load(self) -> "DataProcessor":
        self.raw_df = pd.read_csv(self.data_path, parse_dates=["timestamp"])
        print(f"📂 Loaded {len(self.raw_df):,} rows × {len(self.raw_df.columns)} cols")
        return self

    # ── 2. Clean ───────────────────────────────────────────────────────────────
    def clean(self) -> "DataProcessor":
        df = self.raw_df.copy()

        # Drop duplicates
        before = len(df)
        df.drop_duplicates(subset=["ride_id"], inplace=True)
        print(f"🧹 Removed {before - len(df)} duplicate rows")

        # Handle missing values
        for col in NUMERIC_COLS:
            if col in df.columns:
                df[col].fillna(df[col].median(), inplace=True)
        for col in CATEGORICAL_COLS:
            if col in df.columns:
                df[col].fillna(df[col].mode()[0], inplace=True)

        # Remove outliers via IQR on key numeric columns
        outlier_cols = ["fare_usd", "distance_km", "duration_min", "wait_time_min"]
        for col in outlier_cols:
            if col not in df.columns:
                continue
            Q1, Q3 = df[col].quantile(0.01), df[col].quantile(0.99)
            IQR = Q3 - Q1
            df = df[(df[col] >= Q1 - 1.5 * IQR) & (df[col] <= Q3 + 1.5 * IQR)]

        # Ensure non-negative values
        for col in ["fare_usd", "distance_km", "duration_min", "wait_time_min"]:
            if col in df.columns:
                df = df[df[col] > 0]

        df.reset_index(drop=True, inplace=True)
        print(f"✅ After cleaning: {len(df):,} rows remain")
        self.df = df
        return self

    # ── 3. Feature Engineering ─────────────────────────────────────────────────
    def engineer_features(self) -> "DataProcessor":
        df = self.df.copy()

        # Temporal enrichment
        if "timestamp" in df.columns:
            df["hour"]    = df["timestamp"].dt.hour
            df["day"]     = df["timestamp"].dt.day
            df["weekday"] = df["timestamp"].dt.weekday
            df["month"]   = df["timestamp"].dt.month
            df["quarter"] = df["timestamp"].dt.quarter
            df["week_of_year"] = df["timestamp"].dt.isocalendar().week.astype(int)
            df["is_weekend"] = (df["weekday"] >= 5).astype(int)

        # Demand score (rides per hour / avg rides)
        if "demand_score" not in df.columns:
            hourly_counts = df.groupby(["zone_id", "hour"])["ride_id"].transform("count")
            avg_rides = df.groupby("zone_id")["ride_id"].transform("count") / 24
            df["demand_score"] = (hourly_counts / avg_rides.replace(0, 1)).round(3)

        # Efficiency = fare / distance
        df["efficiency"] = (df["fare_usd"] / df["distance_km"].replace(0, np.nan)).round(3)

        # Peak hour flag
        df["peak_hour"] = df["hour"].apply(
            lambda h: 1 if h in list(range(7, 10)) + list(range(17, 21)) else 0
        )

        # Driver opportunity score
        df["driver_opportunity_score"] = (
            (df["driver_earnings_usd"] / df["wait_time_min"].replace(0, 1)) * df["demand_score"]
        ).round(3)

        # Zone demand density
        zone_avg = df.groupby("zone_id")["demand_score"].transform("mean")
        df["zone_demand_density"] = (df["demand_score"] / zone_avg.replace(0, 1)).round(3)

        # Congestion index
        traffic_map = {"Low": 0.2, "Medium": 0.5, "High": 0.9}
        df["traffic_numeric"] = df["traffic_level"].map(traffic_map).fillna(0.5)
        df["congestion_index"] = (
            (df["traffic_numeric"] + df["demand_score"] * 0.3) / 1.3
        ).clip(0, 1).round(3)

        # Cancellation risk
        df["cancellation_risk"] = (
            0.05
            + (df["wait_time_min"] > 10).astype(float) * 0.12
            + df["weather"].isin(["Rainy", "Snow"]).astype(float) * 0.08
            + (df["demand_score"] > 1.8).astype(float) * 0.05
        ).clip(0, 1).round(3)

        # Revenue per minute
        df["revenue_per_min"] = (df["fare_usd"] / df["duration_min"].replace(0, 1)).round(3)

        # Surge flag
        df["surge_flag"] = (df["surge_multiplier"] > 1.0).astype(int)

        # Time of day category
        df["time_of_day"] = pd.cut(
            df["hour"],
            bins=[-1, 5, 11, 16, 20, 23],
            labels=["Night", "Morning", "Afternoon", "Evening", "Late Night"],
        )

        self.df = df
        print(f"⚙️  Feature engineering complete — {len(df.columns)} features")
        return self

    # ── 4. Encode & Scale ──────────────────────────────────────────────────────
    def encode_and_scale(self) -> "DataProcessor":
        df = self.df.copy()

        for col in CATEGORICAL_COLS:
            if col in df.columns:
                le = LabelEncoder()
                df[f"{col}_enc"] = le.fit_transform(df[col].astype(str))
                self.encoders[col] = le

        # Store raw values for stats before scaling
        self._raw_df = df.copy()

        scale_cols = [c for c in NUMERIC_COLS if c in df.columns]
        df[scale_cols] = self.scaler.fit_transform(df[scale_cols])

        self.df = df
        print("🔢 Encoding & scaling complete")
        return self

    # ── 5. Stats ───────────────────────────────────────────────────────────────
    def compute_stats(self) -> dict:
        # Use raw (unscaled) data for human-readable stats
        df = getattr(self, "_raw_df", self.df)
        self._stats = {
            "total_rides": len(df),
            "total_revenue": round(float(df["fare_usd"].sum()), 2),
            "avg_fare": round(float(df["fare_usd"].mean()), 2),
            "avg_distance": round(float(df["distance_km"].mean()), 2),
            "avg_duration": round(float(df["duration_min"].mean()), 2),
            "avg_wait": round(float(df["wait_time_min"].mean()), 2),
            "cancellation_rate": round(float(df["cancelled"].mean() * 100), 2),
            "surge_rate": round(float(df["surge_flag"].mean() * 100), 2),
            "peak_hour_share": round(float(df["peak_hour"].mean() * 100), 2),
            "top_zone": str(df.groupby("zone_id")["ride_id"].count().idxmax()),
            "busiest_hour": int(df.groupby("hour")["ride_id"].count().idxmax()),
        }
        return self._stats

    # ── 6. Get ML-ready splits ─────────────────────────────────────────────────
    def get_ml_features(self, target: str) -> Tuple[pd.DataFrame, pd.Series]:
        # Use raw (unscaled) data for ML training — tree models don't need scaling
        df = getattr(self, "_raw_df", self.df).dropna(subset=[target])
        feature_cols = [
            "hour", "weekday", "month", "is_weekend", "peak_hour",
            "distance_km", "surge_multiplier", "wait_time_min",
            "event_flag", "traffic_numeric", "congestion_index",
            "zone_id_enc", "weather_enc", "traffic_level_enc",
            "efficiency", "zone_demand_density",
        ]
        available = [c for c in feature_cols if c in df.columns]
        X = df[available].fillna(0)
        y = df[target]
        return X, y

    # ── 7. Full pipeline ───────────────────────────────────────────────────────
    def run_pipeline(self) -> "DataProcessor":
        return self.load().clean().engineer_features().encode_and_scale()

    def save_processed(self, out_path: str) -> None:
        self.df.to_csv(out_path, index=False)
        print(f"💾 Processed data saved → {out_path}")
