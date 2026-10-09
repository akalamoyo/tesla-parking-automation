from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    tesla_email: str | None = Field(default=None, alias="TESLA_EMAIL")
    tesla_password: str | None = Field(default=None, alias="TESLA_PASSWORD")
    tesla_access_token: str | None = Field(default=None, alias="TESLA_ACCESS_TOKEN")
    tesla_refresh_token: str | None = Field(default=None, alias="TESLA_REFRESH_TOKEN")
    tesla_vehicle_id: str | None = Field(default=None, alias="TESLA_VEHICLE_ID")

    polling_interval_seconds: int = Field(default=30, alias="POLLING_INTERVAL_SECONDS")
    driving_speed_kmh_threshold: float = Field(default=5.0, alias="DRIVING_SPEED_KMH_THRESHOLD")
    parking_zone_provider: str = Field(default="manual", alias="PARKING_ZONE_PROVIDER")
    local_parking_zones_json: str | None = Field(default=None, alias="LOCAL_PARKING_ZONES_JSON")

    @property
    def has_tesla_credentials(self) -> bool:
        return bool(self.tesla_email and self.tesla_password) or bool(self.tesla_access_token)
