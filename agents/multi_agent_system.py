"""
Urban Mobility Intelligence OS
Multi-Agent System — Driver, User, and System Coordinator agents
"""

from __future__ import annotations

import random
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import time


# ─── Enums ────────────────────────────────────────────────────────────────────
class DriverStatus(Enum):
    IDLE = "idle"
    EN_ROUTE = "en_route"
    ON_TRIP = "on_trip"
    OFFLINE = "offline"


class RideStatus(Enum):
    PENDING = "pending"
    MATCHED = "matched"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ─── Data Classes ─────────────────────────────────────────────────────────────
@dataclass
class Location:
    zone_id: str
    lat: float = 0.0
    lng: float = 0.0

    def distance_to(self, other: "Location") -> float:
        return abs(hash(self.zone_id) - hash(other.zone_id)) % 10 + 1.0


@dataclass
class RideRequest:
    request_id: str
    user_id: str
    pickup: Location
    dropoff: Location
    timestamp: float
    max_wait: float = 12.0
    status: RideStatus = RideStatus.PENDING
    assigned_driver: Optional[str] = None
    fare: float = 0.0


@dataclass
class DriverAgent:
    """
    Autonomous driver agent that navigates to high-demand zones,
    accepts/rejects rides based on opportunity score.
    """
    driver_id: str
    location: Location
    status: DriverStatus = DriverStatus.IDLE
    earnings: float = 0.0
    trips_completed: int = 0
    trips_rejected: int = 0
    strategy: str = "greedy"   # greedy | balanced | conservative

    def opportunity_score(self, request: RideRequest, zone_demand: Dict[str, float]) -> float:
        dist = self.location.distance_to(request.pickup)
        demand = zone_demand.get(request.pickup.zone_id, 1.0)
        return (request.fare * demand) / max(dist, 0.5)

    def decide_accept(self, request: RideRequest, zone_demand: Dict[str, float]) -> bool:
        score = self.opportunity_score(request, zone_demand)
        if self.strategy == "greedy":
            return score > 2.0
        elif self.strategy == "balanced":
            return score > 3.0
        else:  # conservative
            return score > 5.0

    def move_to_best_zone(self, zone_demand: Dict[str, float]) -> str:
        """Move to the zone with highest demand."""
        best_zone = max(zone_demand, key=zone_demand.get)
        self.location = Location(zone_id=best_zone)
        return best_zone


@dataclass
class UserAgent:
    """
    User agent that generates ride requests based on time/location patterns.
    """
    user_id: str
    location: Location
    patience: float = 10.0   # max wait minutes
    trips_requested: int = 0
    trips_completed: int = 0
    trips_cancelled: int = 0

    def generate_request(self, zones: List[str], fare_estimate: float) -> RideRequest:
        dropoff_zone = random.choice([z for z in zones if z != self.location.zone_id])
        self.trips_requested += 1
        return RideRequest(
            request_id=f"R{self.user_id}_{self.trips_requested}",
            user_id=self.user_id,
            pickup=self.location,
            dropoff=Location(zone_id=dropoff_zone),
            timestamp=time.time(),
            fare=fare_estimate,
            max_wait=self.patience,
        )

    def evaluate_wait(self, wait_time: float) -> bool:
        """Returns True if user cancels due to long wait."""
        return wait_time > self.patience


@dataclass
class SystemAgent:
    """
    Central coordinator: matches drivers to users, manages surge pricing,
    monitors system health.
    """
    name: str = "CityOS-Coordinator"
    total_matches: int = 0
    total_cancellations: int = 0
    total_revenue: float = 0.0
    surge_active: bool = False
    current_surge: float = 1.0
    event_log: List[Dict] = field(default_factory=list)

    def compute_surge(self, demand_score: float) -> float:
        if demand_score > 2.0:
            self.surge_active = True
            self.current_surge = round(min(2.5, 1.0 + (demand_score - 1.0) * 0.6), 2)
        elif demand_score > 1.4:
            self.surge_active = True
            self.current_surge = round(1.0 + (demand_score - 1.0) * 0.3, 2)
        else:
            self.surge_active = False
            self.current_surge = 1.0
        return self.current_surge

    def match_driver(
        self,
        request: RideRequest,
        drivers: List[DriverAgent],
        zone_demand: Dict[str, float],
    ) -> Optional[DriverAgent]:
        idle_drivers = [d for d in drivers if d.status == DriverStatus.IDLE]
        if not idle_drivers:
            return None

        # Score each driver
        scored = [
            (d, d.opportunity_score(request, zone_demand))
            for d in idle_drivers
            if d.decide_accept(request, zone_demand)
        ]
        if not scored:
            # Fallback: nearest idle driver
            scored = [(d, -d.location.distance_to(request.pickup)) for d in idle_drivers]

        best_driver = max(scored, key=lambda x: x[1])[0]
        return best_driver

    def process_request(
        self,
        request: RideRequest,
        drivers: List[DriverAgent],
        zone_demand: Dict[str, float],
    ) -> Dict:
        driver = self.match_driver(request, drivers, zone_demand)

        if driver is None:
            request.status = RideStatus.CANCELLED
            self.total_cancellations += 1
            self.event_log.append({
                "event": "no_driver_available",
                "request_id": request.request_id,
                "zone": request.pickup.zone_id,
            })
            return {"status": "cancelled", "reason": "no_driver_available"}

        # Simulate wait time
        wait = driver.location.distance_to(request.pickup) * 1.5
        # Check if user would cancel due to long wait (use max_wait from request)
        if wait > request.max_wait:
            request.status = RideStatus.CANCELLED
            self.total_cancellations += 1
            self.event_log.append({
                "event": "user_cancelled",
                "request_id": request.request_id,
                "wait_time": wait,
            })
            return {"status": "cancelled", "reason": "user_patience_exceeded", "wait": wait}

        # Complete ride
        request.status = RideStatus.COMPLETED
        request.assigned_driver = driver.driver_id
        driver.status = DriverStatus.ON_TRIP
        driver.trips_completed += 1
        driver.earnings += request.fare * 0.76
        driver.status = DriverStatus.IDLE

        self.total_matches += 1
        self.total_revenue += request.fare

        self.event_log.append({
            "event": "ride_completed",
            "request_id": request.request_id,
            "driver_id": driver.driver_id,
            "fare": request.fare,
            "wait": round(wait, 1),
        })

        return {
            "status": "completed",
            "driver_id": driver.driver_id,
            "fare": request.fare,
            "wait_time": round(wait, 1),
        }


# ─── Simulation Runner ────────────────────────────────────────────────────────
class MultiAgentSimulation:
    """Orchestrates a full multi-agent city simulation."""

    def __init__(
        self,
        n_drivers: int = 50,
        n_users: int = 200,
        n_zones: int = 20,
        steps: int = 100,
        seed: int = 42,
    ):
        random.seed(seed)
        np.random.seed(seed)

        self.zones = [f"Z{i:02d}" for i in range(1, n_zones + 1)]
        self.steps = steps

        # Initialise agents
        self.drivers = [
            DriverAgent(
                driver_id=f"D{i:03d}",
                location=Location(zone_id=random.choice(self.zones)),
                strategy=random.choice(["greedy", "balanced", "conservative"]),
            )
            for i in range(n_drivers)
        ]

        self.users = [
            UserAgent(
                user_id=f"U{i:04d}",
                location=Location(zone_id=random.choice(self.zones)),
                patience=random.uniform(5, 15),
            )
            for i in range(n_users)
        ]

        self.system = SystemAgent()
        self.step_logs: List[Dict] = []

    def _zone_demand(self, step: int) -> Dict[str, float]:
        """Dynamic zone demand that changes each step."""
        return {
            z: max(0.1, np.random.normal(1.0 + 0.5 * np.sin(step / 10), 0.3))
            for z in self.zones
        }

    def run(self) -> Dict:
        print(f"🤖 Running Multi-Agent Simulation ({self.steps} steps)...")

        for step in range(self.steps):
            zone_demand = self._zone_demand(step)
            demand_score = np.mean(list(zone_demand.values()))
            surge = self.system.compute_surge(demand_score)

            # Drivers reposition to best zones
            for driver in self.drivers:
                if driver.status == DriverStatus.IDLE and random.random() < 0.3:
                    driver.move_to_best_zone(zone_demand)

            # Users generate requests
            active_users = random.sample(self.users, min(len(self.users), int(demand_score * 10)))
            step_rides = 0
            step_revenue = 0.0

            for user in active_users:
                fare = round(random.uniform(8, 30) * surge, 2)
                request = user.generate_request(self.zones, fare)
                result = self.system.process_request(request, self.drivers, zone_demand)
                if result["status"] == "completed":
                    step_rides += 1
                    step_revenue += fare

            self.step_logs.append({
                "step": step,
                "demand_score": round(demand_score, 3),
                "surge": surge,
                "rides": step_rides,
                "revenue": round(step_revenue, 2),
                "active_drivers": len([d for d in self.drivers if d.status != DriverStatus.OFFLINE]),
                "cancellations": self.system.total_cancellations,
            })

        return self.get_summary()

    def get_summary(self) -> Dict:
        top_earner = max(self.drivers, key=lambda d: d.earnings)
        return {
            "total_rides": self.system.total_matches,
            "total_cancellations": self.system.total_cancellations,
            "total_revenue": round(self.system.total_revenue, 2),
            "cancellation_rate": round(
                self.system.total_cancellations
                / max(self.system.total_matches + self.system.total_cancellations, 1),
                3,
            ),
            "top_driver": {
                "id": top_earner.driver_id,
                "earnings": round(top_earner.earnings, 2),
                "trips": top_earner.trips_completed,
            },
            "avg_driver_earnings": round(
                np.mean([d.earnings for d in self.drivers]), 2
            ),
            "step_logs": self.step_logs,
            "event_log_sample": self.system.event_log[:20],
        }
