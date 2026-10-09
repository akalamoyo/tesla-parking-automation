from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from app.parking import ParkingZone, find_nearest_parking_zone
from app.tesla_client import VehicleStatus


@dataclass(slots=True)
class ParkingSession:
    vehicle_id: str
    zone_id: str | None = None
    zone_name: str | None = None
    active: bool = False
    last_registered_at: str | None = None


class CarStateMachine:
    def __init__(
        self,
        on_drive: Callable[[VehicleStatus], None] | None = None,
        on_park: Callable[[VehicleStatus, ParkingZone], None] | None = None,
        driving_speed_kmh_threshold: float = 5.0,
    ):
        self.on_drive = on_drive or (lambda status: None)
        self.on_park = on_park or (lambda status, zone: None)
        self.driving_speed_kmh_threshold = driving_speed_kmh_threshold
        self.current_state: str = "unknown"

    def _is_driving(self, status: VehicleStatus) -> bool:
        speed = status.speed_kmh if status.speed_kmh is not None else 0
        if speed >= self.driving_speed_kmh_threshold:
            return True
        if status.shift_state in {"D", "R", "N"} and speed > 0:
            return True
        return False

    def _is_parked(self, status: VehicleStatus) -> bool:
        speed = status.speed_kmh if status.speed_kmh is not None else 0
        if speed <= 0:
            return True
        return False

    def update(self, status: VehicleStatus) -> str:
        if self._is_driving(status):
            if self.current_state != "driving":
                self.current_state = "driving"
                self.on_drive(status)
            return self.current_state

        if self._is_parked(status):
            if self.current_state != "parked":
                self.current_state = "parked"
                zone = self._choose_zone(status)
                self.on_park(status, zone)
            return self.current_state

        return self.current_state

    def _choose_zone(self, status: VehicleStatus) -> ParkingZone | None:
        # The real implementation should call the municipality parking API to fetch available zones.
        # This method returns a placeholder zone if lat/long are available and a zone list is passed
        # in the callback context; in this starter app we keep it simple and return None.
        return None


class ParkingController:
    def __init__(self, vehicle_status_provider: Any, parking_provider: Any, driving_speed_kmh_threshold: float = 5.0):
        self.vehicle_status_provider = vehicle_status_provider
        self.parking_provider = parking_provider
        self.driving_speed_kmh_threshold = driving_speed_kmh_threshold
        self.active_session: ParkingSession | None = None
        self.state_machine = CarStateMachine(
            on_drive=self._stop_parking_registration,
            on_park=self._register_parking,
            driving_speed_kmh_threshold=self.driving_speed_kmh_threshold,
        )

    async def _register_parking(self, status: VehicleStatus, zone: ParkingZone | None) -> None:
        if status.latitude is None or status.longitude is None:
            return

        if not zone:
            zones = await self.parking_provider.list_zones()
            zone = find_nearest_parking_zone(status.latitude, status.longitude, zones)

        if not zone:
            return

        result = await self.parking_provider.register_parking(zone, status.vehicle_id)
        self.active_session = ParkingSession(
            vehicle_id=status.vehicle_id,
            zone_id=zone.id,
            zone_name=zone.name,
            active=True,
            last_registered_at=result.get("status"),
        )

    async def _stop_parking_registration(self, status: VehicleStatus) -> None:
        if self.active_session is None:
            return

        await self.parking_provider.stop_parking(status.vehicle_id)
        self.active_session = None

    async def run_once(self) -> str:
        status = await self.vehicle_status_provider.get_vehicle_status()
        return self.state_machine.update(status)
