from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings


@dataclass(slots=True)
class VehicleStatus:
    vehicle_id: str
    latitude: float | None = None
    longitude: float | None = None
    speed_kmh: float | None = None
    shift_state: str | None = None
    is_user_present: bool | None = None
    is_parking_brake_on: bool | None = None
    state: str | None = None
    raw: dict[str, Any] | None = None


class TeslaClient:
    """Minimal Tesla API client wrapper.

    This project intentionally keeps the Tesla access logic isolated so it can be swapped for a
    different auth strategy if needed.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = "https://owner-api.teslamotors.com"
        self.access_token = settings.tesla_access_token

    async def login(self) -> str:
        if self.access_token:
            return self.access_token

        if not self.settings.tesla_email or not self.settings.tesla_password:
            raise ValueError("TESLA_EMAIL and TESLA_PASSWORD are required when no access token is present.")

        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            response = await client.post(
                "/api/1/users/session",
                json={
                    "email": self.settings.tesla_email,
                    "password": self.settings.tesla_password,
                },
            )
            response.raise_for_status()
            payload = response.json()
            self.access_token = payload.get("access_token")
            if not self.access_token:
                raise ValueError("Tesla login response did not include an access token.")
            self.settings.tesla_access_token = self.access_token
            return self.access_token

    async def get_vehicles(self) -> list[dict[str, Any]]:
        token = await self.login()

        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            response = await client.get(
                "/api/1/vehicles",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", [])

    async def get_vehicle_status(self, vehicle_id: str | None = None) -> VehicleStatus:
        if vehicle_id is None:
            vehicle_id = self.settings.tesla_vehicle_id
        if not vehicle_id:
            vehicles = await self.get_vehicles()
            if not vehicles:
                raise ValueError("No Tesla vehicles were found for this account.")
            vehicle_id = str(vehicles[0]["id"])
            self.settings.tesla_vehicle_id = vehicle_id

        token = await self.login()

        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            response = await client.get(
                f"/api/1/vehicles/{vehicle_id}/data",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            payload = response.json()
            response_data = payload.get("response", {})

            status = VehicleStatus(
                vehicle_id=str(vehicle_id),
                latitude=response_data.get("drive_state", {}).get("latitude"),
                longitude=response_data.get("drive_state", {}).get("longitude"),
                speed_kmh=response_data.get("drive_state", {}).get("speed"),
                shift_state=response_data.get("drive_state", {}).get("shift_state"),
                is_user_present=response_data.get("vehicle_state", {}).get("is_user_present"),
                is_parking_brake_on=response_data.get("vehicle_state", {}).get("parking_brake_on"),
                state=response_data.get("state"),
                raw=response_data,
            )

        return status

    async def get_vehicle_status_dict(self) -> dict[str, Any]:
        status = await self.get_vehicle_status()
        return json.loads(json.dumps(status.raw or {}))
