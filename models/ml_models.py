"""
Urban Mobility Intelligence OS
Machine Learning Models — Demand, Duration, Cancellation prediction
"""

from __future__ import annotations

import os
import json
import pickle
import warnings
import numpy as np
import pandas as pd
from typing import Dict, Any

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, classification_report, roc_auc_score,
)
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

try:
    from xgboost import XGBRegressor, XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("⚠️  XGBoost not installed — using GradientBoosting fallback")


# ─── Model Registry ───────────────────────────────────────────────────────────
class ModelRegistry:
    """Stores trained models and their metadata."""

    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.metrics: Dict[str, Dict] = {}
        self.feature_importances: Dict[str, pd.Series] = {}

    def register(self, name: str, model, metrics: dict, feature_names: list):
        self.models[name] = model
        self.metrics[name] = metrics
        if hasattr(model, "feature_importances_"):
            self.feature_importances[name] = pd.Series(
                model.feature_importances_, index=feature_names
            ).sort_values(ascending=False)

    def save(self, directory: str):
        os.makedirs(directory, exist_ok=True)
        for name, model in self.models.items():
            with open(os.path.join(directory, f"{name}.pkl"), "wb") as f:
                pickle.dump(model, f)
        with open(os.path.join(directory, "metrics.json"), "w") as f:
            json.dump(self.metrics, f, indent=2)
        print(f"💾 Models saved to {directory}/")

    def load(self, directory: str):
        for fname in os.listdir(directory):
            if fname.endswith(".pkl"):
                name = fname.replace(".pkl", "")
                with open(os.path.join(directory, fname), "rb") as f:
                    self.models[name] = pickle.load(f)
        metrics_path = os.path.join(directory, "metrics.json")
        if os.path.exists(metrics_path):
            with open(metrics_path) as f:
                self.metrics = json.load(f)
        print(f"📦 Models loaded from {directory}/")


registry = ModelRegistry()


# ─── Feature columns ──────────────────────────────────────────────────────────
FEATURE_COLS = [
    "hour", "weekday", "month", "is_weekend", "peak_hour",
    "distance_km", "surge_multiplier", "wait_time_min",
    "event_flag", "traffic_numeric", "congestion_index",
    "zone_id_enc", "weather_enc", "traffic_level_enc",
    "efficiency", "zone_demand_density",
]


def _prepare(df: pd.DataFrame, target: str):
    available = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available].fillna(0)
    y = df[target]
    return train_test_split(X, y, test_size=0.2, random_state=42), available


# ─── 1. Demand Prediction ─────────────────────────────────────────────────────
def train_demand_model(df: pd.DataFrame) -> dict:
    print("\n🤖 Training Demand Prediction Model...")
    (X_train, X_test, y_train, y_test), feats = _prepare(df, "demand_score")

    if HAS_XGB:
        model = XGBRegressor(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1
        )
    else:
        model = RandomForestRegressor(
            n_estimators=200, max_depth=10, min_samples_leaf=3,
            random_state=42, n_jobs=-1
        )

    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    metrics = {
        "mae":  round(mean_absolute_error(y_test, preds), 4),
        "rmse": round(np.sqrt(mean_squared_error(y_test, preds)), 4),
        "r2":   round(r2_score(y_test, preds), 4),
    }
    registry.register("demand_model", model, metrics, feats)
    print(f"   MAE={metrics['mae']}  RMSE={metrics['rmse']}  R²={metrics['r2']}")
    return metrics


# ─── 2. Duration Prediction ───────────────────────────────────────────────────
def train_duration_model(df: pd.DataFrame) -> dict:
    print("\n🤖 Training Ride Duration Model...")
    (X_train, X_test, y_train, y_test), feats = _prepare(df, "duration_min")

    model = RandomForestRegressor(
        n_estimators=200, max_depth=10, min_samples_leaf=5,
        random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    metrics = {
        "mae":  round(mean_absolute_error(y_test, preds), 4),
        "rmse": round(np.sqrt(mean_squared_error(y_test, preds)), 4),
        "r2":   round(r2_score(y_test, preds), 4),
    }
    registry.register("duration_model", model, metrics, feats)
    print(f"   MAE={metrics['mae']}  RMSE={metrics['rmse']}  R²={metrics['r2']}")
    return metrics


# ─── 3. Cancellation Prediction ───────────────────────────────────────────────
def train_cancellation_model(df: pd.DataFrame) -> dict:
    print("\n🤖 Training Cancellation Prediction Model...")
    (X_train, X_test, y_train, y_test), feats = _prepare(df, "cancelled")

    if HAS_XGB:
        model = XGBClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            scale_pos_weight=5, random_state=42, n_jobs=-1, eval_metric="logloss"
        )
    else:
        model = RandomForestClassifier(
            n_estimators=200, max_depth=8, class_weight="balanced",
            random_state=42, n_jobs=-1
        )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": round(accuracy_score(y_test, preds), 4),
        "roc_auc":  round(roc_auc_score(y_test, proba), 4),
        "report":   classification_report(y_test, preds, output_dict=True),
    }
    registry.register("cancellation_model", model, metrics, feats)
    print(f"   Accuracy={metrics['accuracy']}  ROC-AUC={metrics['roc_auc']}")
    return metrics


# ─── 4. Train All ─────────────────────────────────────────────────────────────
def train_all_models(df: pd.DataFrame, save_dir: str = "models/saved") -> ModelRegistry:
    print("=" * 60)
    print("🚀 Urban Mobility OS — Model Training Pipeline")
    print("=" * 60)

    demand_metrics   = train_demand_model(df)
    duration_metrics = train_duration_model(df)
    cancel_metrics   = train_cancellation_model(df)

    registry.save(save_dir)

    print("\n📊 Training Summary:")
    print(f"  Demand   → R²={demand_metrics['r2']}")
    print(f"  Duration → R²={duration_metrics['r2']}")
    print(f"  Cancel   → AUC={cancel_metrics['roc_auc']}")
    print("=" * 60)
    return registry


# ─── 5. Inference ─────────────────────────────────────────────────────────────
def predict_demand(features: dict) -> float:
    model = registry.models.get("demand_model")
    if model is None:
        return 1.0
    X = pd.DataFrame([features])
    available = [c for c in FEATURE_COLS if c in X.columns]
    X = X[available].fillna(0)
    return float(model.predict(X)[0])


def predict_duration(features: dict) -> float:
    model = registry.models.get("duration_model")
    if model is None:
        return 15.0
    X = pd.DataFrame([features])
    available = [c for c in FEATURE_COLS if c in X.columns]
    X = X[available].fillna(0)
    return float(model.predict(X)[0])


def predict_cancellation_prob(features: dict) -> float:
    model = registry.models.get("cancellation_model")
    if model is None:
        return 0.1
    X = pd.DataFrame([features])
    available = [c for c in FEATURE_COLS if c in X.columns]
    X = X[available].fillna(0)
    return float(model.predict_proba(X)[0][1])
