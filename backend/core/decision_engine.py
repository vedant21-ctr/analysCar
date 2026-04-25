"""
Urban Mobility Intelligence OS
Decision Engine — actionable intelligence for drivers, operators, and city planners
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import List, Dict, Any


class DecisionEngine:
    """
    Generates data-driven recommendations for:
    - Best zones for drivers
    - Optimal working hours
    - Surge pricing strategy
    - Fleet deployment
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def best_zones_for_drivers(self, top_n: int = 5) -> List[Dict]:
        zone_stats = (
            self.df.groupby("zone_id")
            .agg(
                avg_earnings=("driver_earnings_usd", "mean"),
                avg_wait=("wait_time_min", "mean"),
                avg_demand=("demand_score", "mean"),
                total_rides=("ride_id", "count"),
                avg_opportunity=("driver_opportunity_score", "mean"),
                cancel_rate=("cancelled", "mean"),
            )
            .reset_index()
        )
        zone_stats["composite_score"] = (
            zone_stats["avg_earnings"] * 0.35
            + zone_stats["avg_demand"] * 0.25
            + zone_stats["avg_opportunity"] * 0.25
            - zone_stats["avg_wait"] * 0.10
            - zone_stats["cancel_rate"] * 10 * 0.05
        )
        top = zone_stats.nlargest(top_n, "composite_score")
        return top.to_dict("records")

    def best_working_hours(self) -> List[Dict]:
        hour_stats = (
            self.df.groupby("hour")
            .agg(
                avg_fare=("fare_usd", "mean"),
                avg_demand=("demand_score", "mean"),
                avg_earnings=("driver_earnings_usd", "mean"),
                surge_rate=("surge_flag", "mean"),
                total_rides=("ride_id", "count"),
            )
            .reset_index()
        )
        hour_stats["hour_score"] = (
            hour_stats["avg_earnings"] * 0.4
            + hour_stats["avg_demand"] * 0.3
            + hour_stats["surge_rate"] * 10 * 0.3
        )
        hour_stats["label"] = hour_stats["hour"].apply(self._hour_label)
        return hour_stats.sort_values("hour_score", ascending=False).to_dict("records")

    def surge_pricing_recommendations(self) -> List[Dict]:
        recs = []
        hour_demand = self.df.groupby("hour")["demand_score"].mean()
        for hour, demand in hour_demand.items():
            if demand > 1.8:
                suggested_surge = round(1.0 + (demand - 1.0) * 0.6, 2)
                recs.append({
                    "hour": hour,
                    "label": self._hour_label(hour),
                    "demand_score": round(demand, 3),
                    "suggested_surge": min(suggested_surge, 2.5),
                    "action": "Activate surge pricing",
                    "priority": "HIGH",
                })
            elif demand > 1.3:
                recs.append({
                    "hour": hour,
                    "label": self._hour_label(hour),
                    "demand_score": round(demand, 3),
                    "suggested_surge": round(1.0 + (demand - 1.0) * 0.3, 2),
                    "action": "Mild surge recommended",
                    "priority": "MEDIUM",
                })
        return sorted(recs, key=lambda x: x["demand_score"], reverse=True)

    def fleet_deployment_plan(self) -> List[Dict]:
        zone_hour = (
            self.df.groupby(["zone_id", "hour"])["demand_score"]
            .mean()
            .reset_index()
        )
        peak_zones = zone_hour[zone_hour["demand_score"] > 1.5]
        plan = []
        for _, row in peak_zones.iterrows():
            drivers_needed = int(row["demand_score"] * 10)
            plan.append({
                "zone_id": row["zone_id"],
                "hour": int(row["hour"]),
                "demand_score": round(row["demand_score"], 3),
                "drivers_recommended": drivers_needed,
                "priority": "HIGH" if row["demand_score"] > 2.0 else "MEDIUM",
            })
        return sorted(plan, key=lambda x: x["demand_score"], reverse=True)[:20]

    def weather_impact_analysis(self) -> Dict:
        weather_stats = (
            self.df.groupby("weather")
            .agg(
                avg_demand=("demand_score", "mean"),
                avg_fare=("fare_usd", "mean"),
                cancel_rate=("cancelled", "mean"),
                avg_wait=("wait_time_min", "mean"),
                total_rides=("ride_id", "count"),
            )
            .reset_index()
        )
        baseline = weather_stats[weather_stats["weather"] == "Clear"]["avg_demand"].values
        if len(baseline) > 0:
            weather_stats["demand_lift_pct"] = (
                (weather_stats["avg_demand"] - baseline[0]) / baseline[0] * 100
            ).round(1)
        return weather_stats.to_dict("records")

    def cancellation_hotspots(self) -> List[Dict]:
        zone_cancel = (
            self.df.groupby("zone_id")
            .agg(
                cancel_rate=("cancelled", "mean"),
                avg_wait=("wait_time_min", "mean"),
                total_rides=("ride_id", "count"),
            )
            .reset_index()
        )
        hotspots = zone_cancel[zone_cancel["cancel_rate"] > zone_cancel["cancel_rate"].quantile(0.75)]
        hotspots = hotspots.sort_values("cancel_rate", ascending=False)
        hotspots["recommendation"] = hotspots.apply(
            lambda r: f"Reduce wait time by {max(1, int(r['avg_wait']-5))} min via driver incentives",
            axis=1,
        )
        return hotspots.to_dict("records")

    def generate_full_report(self) -> Dict:
        return {
            "best_zones": self.best_zones_for_drivers(),
            "best_hours": self.best_working_hours()[:8],
            "surge_recommendations": self.surge_pricing_recommendations()[:10],
            "fleet_plan": self.fleet_deployment_plan()[:10],
            "weather_impact": self.weather_impact_analysis(),
            "cancellation_hotspots": self.cancellation_hotspots()[:5],
        }

    @staticmethod
    def _hour_label(hour: int) -> str:
        if 0 <= hour <= 5:   return f"{hour:02d}:00 (Late Night)"
        if 6 <= hour <= 9:   return f"{hour:02d}:00 (Morning Rush)"
        if 10 <= hour <= 12: return f"{hour:02d}:00 (Mid Morning)"
        if 13 <= hour <= 16: return f"{hour:02d}:00 (Afternoon)"
        if 17 <= hour <= 20: return f"{hour:02d}:00 (Evening Rush)"
        return f"{hour:02d}:00 (Night)"
