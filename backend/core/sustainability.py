"""
Urban Mobility Intelligence OS
Sustainability Analysis — CO2 estimation, eco-optimization, green strategies
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List


# ─── Emission constants ───────────────────────────────────────────────────────
CO2_ICE_KG_PER_KM   = 0.210   # Internal combustion engine
CO2_HYBRID_KG_PER_KM = 0.110
CO2_EV_KG_PER_KM    = 0.053   # Grid-average electricity
CO2_EBIKE_KG_PER_KM = 0.008
CO2_WALK_KG_PER_KM  = 0.000


class SustainabilityAnalyzer:

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def baseline_emissions(self) -> Dict:
        total_km = self.df["distance_km"].sum()
        total_rides = len(self.df)
        co2_tonnes = total_km * CO2_ICE_KG_PER_KM / 1000

        return {
            "total_rides": total_rides,
            "total_km": round(total_km, 1),
            "co2_tonnes_baseline": round(co2_tonnes, 2),
            "co2_per_ride_kg": round(co2_tonnes * 1000 / total_rides, 3),
            "equivalent_trees_needed": int(co2_tonnes * 45),  # ~45 trees absorb 1 tonne/year
        }

    def optimized_emissions(self, ev_share: float = 0.30, ebike_share: float = 0.15) -> Dict:
        total_km = self.df["distance_km"].sum()
        ice_share = 1.0 - ev_share - ebike_share

        co2_tonnes = (
            total_km * ice_share * CO2_ICE_KG_PER_KM
            + total_km * ev_share * CO2_EV_KG_PER_KM
            + total_km * ebike_share * CO2_EBIKE_KG_PER_KM
        ) / 1000

        baseline = self.baseline_emissions()["co2_tonnes_baseline"]
        reduction_pct = (baseline - co2_tonnes) / baseline * 100

        return {
            "ev_share_pct": round(ev_share * 100, 1),
            "ebike_share_pct": round(ebike_share * 100, 1),
            "co2_tonnes_optimized": round(co2_tonnes, 2),
            "co2_reduction_tonnes": round(baseline - co2_tonnes, 2),
            "reduction_pct": round(reduction_pct, 1),
        }

    def short_ride_analysis(self) -> Dict:
        short = self.df[self.df["distance_km"] < 2.0]
        pct = len(short) / len(self.df) * 100
        co2_saved = short["distance_km"].sum() * CO2_ICE_KG_PER_KM / 1000

        return {
            "short_rides_count": len(short),
            "short_rides_pct": round(pct, 1),
            "co2_saveable_tonnes": round(co2_saved, 2),
            "recommendation": (
                f"Redirecting {pct:.1f}% of sub-2km rides to e-bikes/walking "
                f"saves {co2_saved:.1f} tonnes CO₂ annually."
            ),
        }

    def monthly_emissions_trend(self) -> pd.DataFrame:
        monthly = (
            self.df.groupby("month")
            .agg(total_km=("distance_km", "sum"), rides=("ride_id", "count"))
            .reset_index()
        )
        monthly["co2_tonnes"] = (monthly["total_km"] * CO2_ICE_KG_PER_KM / 1000).round(2)
        monthly["co2_optimized"] = (monthly["total_km"] * 0.7 * CO2_ICE_KG_PER_KM / 1000 +
                                    monthly["total_km"] * 0.3 * CO2_EV_KG_PER_KM / 1000).round(2)
        return monthly

    def eco_strategies(self) -> List[Dict]:
        return [
            {
                "strategy": "EV Fleet Transition",
                "description": "Replace 30% of ICE vehicles with EVs",
                "co2_reduction_pct": 22,
                "cost_impact": "High upfront, 40% lower operating cost",
                "timeline": "12–24 months",
                "priority": "HIGH",
            },
            {
                "strategy": "Short-Ride Redirection",
                "description": "Nudge sub-2km rides to e-bikes via app incentives",
                "co2_reduction_pct": 8,
                "cost_impact": "Low — partnership with micro-mobility providers",
                "timeline": "1–3 months",
                "priority": "HIGH",
            },
            {
                "strategy": "Route Optimization",
                "description": "AI-powered routing to reduce idle distance by 15%",
                "co2_reduction_pct": 12,
                "cost_impact": "Medium — ML infrastructure investment",
                "timeline": "3–6 months",
                "priority": "MEDIUM",
            },
            {
                "strategy": "Carpooling Incentives",
                "description": "Promote shared rides during peak hours",
                "co2_reduction_pct": 18,
                "cost_impact": "Low — pricing model adjustment",
                "timeline": "1–2 months",
                "priority": "MEDIUM",
            },
            {
                "strategy": "Off-Peak Demand Shifting",
                "description": "Discount pricing to shift 10% of peak rides to off-peak",
                "co2_reduction_pct": 5,
                "cost_impact": "Revenue-neutral with dynamic pricing",
                "timeline": "Immediate",
                "priority": "LOW",
            },
        ]

    def full_report(self) -> Dict:
        return {
            "baseline": self.baseline_emissions(),
            "optimized_30pct_ev": self.optimized_emissions(ev_share=0.30),
            "optimized_50pct_ev": self.optimized_emissions(ev_share=0.50, ebike_share=0.20),
            "short_ride_analysis": self.short_ride_analysis(),
            "strategies": self.eco_strategies(),
        }
