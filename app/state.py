from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from geopy.distance import geodesic


@dataclass(slots=True)
class ParkingZone:
    id: str
    name: str
    latitude: float
    longitude: float
    radius_meters: int = 50


class ParkingZoneProvider:
    """Single interface for the municipality or parking operator API."""

    async def list_zones(self) -> list[ParkingZone]:
        raise NotImplementedError

    async def register_parking(self, zone: ParkingZone, vehicle_id: str) -> Any:
        raise NotImplementedError

    async def stop_parking(self, vehicle_id: str) -> Any:
        raise NotImplementedError


class ManualParkingZoneProvider(ParkingZoneProvider):
    def __init__(self, source: str | None = None):
        self.source = source

    def _load_sources(self) -> list[dict[str, Any]]:
        if self.source is None:
            return []

        try:
            payload = json.loads(self.source)
        except json.JSONDecodeError:
            raise ValueError("LOCAL_PARKING_ZONES_JSON must contain valid JSON.")

        if not isinstance(payload, list):
            raise ValueError("LOCAL_PARKING_ZONES_JSON must decode to a JSON list of parking zones.")

        return payload

    async def list_zones(self) -> list[ParkingZone]:
        zones: list[ParkingZone] = []
        for item in self._load_sources():
            zones.append(
                ParkingZone(
                    id=str(item["id"]),
                    name=str(item.get("name", "Unnamed zone")),
                    latitude=float(item["latitude"]),
                    longitude=float(item["longitude"]),
                    radius_meters=int(item.get("radius_meters", 50)),
                )
            )
        return zones

    async def register_parking(self, zone: ParkingZone, vehicle_id: str) -> dict[str, Any]:
        return {
            "vehicle_id": vehicle_id,
            "zone_id": zone.id,
            "zone_name": zone.name,
            "status": "registered",
        }

    async def stop_parking(self, vehicle_id: str) -> dict[str, Any]:
        return {
            "vehicle_id": vehicle_id,
            "status": "cancelled",
        }


def find_nearest_parking_zone(latitude: float, longitude: float, zones: list[ParkingZone]) -> ParkingZone | None:
    if latitude is None or longitude is None or not zones:
        return None

    nearest = None
    nearest_distance = None

    for zone in zones:
        distance = geodesic((latitude, longitude), (zone.latitude, zone.longitude)).meters
        if nearest_distance is None or distance < nearest_distance:
            nearest = zone
            nearest_distance = distance

    return nearest
