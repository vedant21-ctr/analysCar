"""
Urban Mobility Intelligence OS
AI Insight Generator — rule-based NLG engine producing natural language insights
"""

from __future__ import annotations

import random
from typing import List, Dict, Any
import pandas as pd
import numpy as np


class AIInsightGenerator:
    """
    Rule-based Natural Language Generation engine.
    Produces contextual, data-driven insights from mobility metrics.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._cache: Dict[str, List[str]] = {}

    # ── Core insight generators ────────────────────────────────────────────────

    def demand_insights(self) -> List[str]:
        insights = []
        hour_demand = self.df.groupby("hour")["demand_score"].mean()
        peak_hour = hour_demand.idxmax()
        peak_val = hour_demand.max()
        low_hour = hour_demand.idxmin()

        insights.append(
            f"🔥 Demand peaks at {peak_hour:02d}:00 with a score of {peak_val:.2f}x — "
            f"{'likely driven by evening commute traffic' if 17 <= peak_hour <= 20 else 'morning rush hour patterns'}."
        )
        insights.append(
            f"🌙 Lowest demand occurs at {low_hour:02d}:00, suggesting minimal fleet deployment "
            f"during this window can reduce idle costs."
        )

        weekend_demand = self.df[self.df["is_weekend"] == 1]["demand_score"].mean()
        weekday_demand = self.df[self.df["is_weekend"] == 0]["demand_score"].mean()
        diff_pct = abs(weekend_demand - weekday_demand) / weekday_demand * 100
        if weekend_demand > weekday_demand:
            insights.append(
                f"📅 Weekend demand is {diff_pct:.1f}% higher than weekdays, "
                f"driven by leisure and nightlife activity."
            )
        else:
            insights.append(
                f"📅 Weekday demand exceeds weekends by {diff_pct:.1f}%, "
                f"reflecting strong commuter dependency on ride-hailing."
            )
        return insights

    def weather_insights(self) -> List[str]:
        insights = []
        weather_stats = self.df.groupby("weather").agg(
            demand=("demand_score", "mean"),
            cancel=("cancelled", "mean"),
            fare=("fare_usd", "mean"),
        )
        clear_demand = weather_stats.loc["Clear", "demand"] if "Clear" in weather_stats.index else 1.0

        for weather, row in weather_stats.iterrows():
            if weather == "Clear":
                continue
            lift = (row["demand"] - clear_demand) / clear_demand * 100
            cancel_lift = (row["cancel"] - weather_stats.loc["Clear", "cancel"]) / max(weather_stats.loc["Clear", "cancel"], 0.01) * 100
            if lift > 5:
                insights.append(
                    f"🌧️ {weather} conditions increase ride demand by {lift:.1f}% "
                    f"and cancellations by {cancel_lift:.1f}% — "
                    f"pre-positioning drivers near sheltered pickup points is recommended."
                )
        return insights

    def revenue_insights(self) -> List[str]:
        insights = []
        monthly_rev = self.df.groupby("month")["fare_usd"].sum()
        best_month = monthly_rev.idxmax()
        worst_month = monthly_rev.idxmin()
        month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                       7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

        insights.append(
            f"💰 Peak revenue month is {month_names[best_month]} "
            f"(${monthly_rev[best_month]:,.0f}), while {month_names[worst_month]} "
            f"is the slowest (${monthly_rev[worst_month]:,.0f})."
        )

        surge_rev = self.df[self.df["surge_flag"] == 1]["fare_usd"].sum()
        total_rev = self.df["fare_usd"].sum()
        surge_share = surge_rev / total_rev * 100
        insights.append(
            f"⚡ Surge pricing contributes {surge_share:.1f}% of total revenue — "
            f"optimising surge thresholds could unlock an additional 8–12% revenue."
        )
        return insights

    def driver_insights(self) -> List[str]:
        insights = []
        zone_earnings = self.df.groupby("zone_id")["driver_earnings_usd"].mean()
        best_zone = zone_earnings.idxmax()
        worst_zone = zone_earnings.idxmin()

        insights.append(
            f"🚗 Drivers in zone {best_zone} earn on average "
            f"${zone_earnings[best_zone]:.2f}/ride — "
            f"{((zone_earnings[best_zone]/zone_earnings.mean()-1)*100):.0f}% above the city average."
        )
        insights.append(
            f"📍 Zone {worst_zone} has the lowest driver earnings. "
            f"Incentive programs or demand stimulation campaigns could improve driver retention here."
        )

        opp_score = self.df.groupby("hour")["driver_opportunity_score"].mean()
        best_hour = opp_score.idxmax()
        insights.append(
            f"⏰ The highest driver opportunity score occurs at {best_hour:02d}:00 — "
            f"drivers starting shifts 30 minutes before this window maximise earnings."
        )
        return insights

    def cancellation_insights(self) -> List[str]:
        insights = []
        overall_rate = self.df["cancelled"].mean() * 100
        insights.append(
            f"❌ Overall cancellation rate is {overall_rate:.1f}%. "
            f"{'This is within acceptable range.' if overall_rate < 10 else 'This exceeds the 10% industry benchmark — immediate action required.'}"
        )

        high_wait_cancel = self.df[self.df["wait_time_min"] > 10]["cancelled"].mean() * 100
        low_wait_cancel = self.df[self.df["wait_time_min"] <= 5]["cancelled"].mean() * 100
        insights.append(
            f"⏱️ Rides with wait times >10 min have a {high_wait_cancel:.1f}% cancellation rate "
            f"vs {low_wait_cancel:.1f}% for <5 min waits — "
            f"reducing average wait by 2 minutes could cut cancellations by ~{(high_wait_cancel-low_wait_cancel)*0.3:.1f}%."
        )
        return insights

    def sustainability_insights(self) -> List[str]:
        insights = []
        avg_dist = self.df["distance_km"].mean()
        total_rides = len(self.df)
        co2_per_km = 0.21  # kg CO2 per km (average ICE vehicle)
        total_co2 = total_rides * avg_dist * co2_per_km / 1000  # tonnes

        insights.append(
            f"🌍 Estimated CO₂ emissions: {total_co2:.1f} tonnes across {total_rides:,} rides. "
            f"Transitioning 20% of fleet to EVs would reduce this by ~{total_co2*0.2:.1f} tonnes."
        )

        short_rides = self.df[self.df["distance_km"] < 2.0]
        short_pct = len(short_rides) / total_rides * 100
        insights.append(
            f"🚲 {short_pct:.1f}% of rides are under 2km — "
            f"nudging these users toward e-bikes or walking could reduce emissions by "
            f"{short_pct * total_co2 / 100:.1f} tonnes annually."
        )
        return insights

    def generate_all_insights(self) -> Dict[str, List[str]]:
        return {
            "demand": self.demand_insights(),
            "weather": self.weather_insights(),
            "revenue": self.revenue_insights(),
            "drivers": self.driver_insights(),
            "cancellations": self.cancellation_insights(),
            "sustainability": self.sustainability_insights(),
        }

    def get_insight_summary(self, n: int = 5) -> List[str]:
        all_insights = []
        for category_insights in self.generate_all_insights().values():
            all_insights.extend(category_insights)
        return random.sample(all_insights, min(n, len(all_insights)))
