# Tesla Parking Automation

This repository contains a Python-based starter for an application that monitors a Tesla and automatically manages parking registration in the Netherlands.

The goal is:

- detect when the Tesla is parked
- find the nearest configured parking zone
- register the car for parking
- stop the registration when the car starts driving

This project is intentionally structured so you can plug in the real parking-zone provider used by your municipality or parking operator.

## Why Python?

Python is the best fit for this project because it has:

- mature HTTP client support for Tesla APIs and municipal APIs
- strong async support for polling vehicle telemetry
- easy integration with cron, Docker, and serverless execution
- a large ecosystem for geospatial logic and scheduling

## Key idea

The app continuously polls Tesla vehicle data and tracks a state machine:

- if the car is moving -> `driving`
- if the car is stationary -> `parked`
- when changing to `parked`, register with the nearest configured parking zone
- when changing to `driving`, stop the active parking registration

## Required real-world configuration

This repo does not include a working municipal parking API implementation, because most parking zones in the Netherlands require a local provider or municipality-specific API. You should replace the `ParkingZoneProvider` implementation with the official system your municipality or parking operator exposes.

## Project layout

- `app/config.py` - environment configuration
- `app/tesla_client.py` - Tesla API access and vehicle state extraction
- `app/parking.py` - parking-zone lookup and registration scheduling
- `app/state.py` - state machine for parked vs driving transitions
- `app/main.py` - CLI entry point

## Quick start

1. Clone this repo
2. Create a virtual environment
3. Install dependencies
4. Copy `.env.example` to `.env` and add your Tesla credentials and parking config
5. Run the app

Example:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
python -m app.main
```

## Environment variables

See `.env.example` for a complete example.

Required values:

- `TESLA_EMAIL`
- `TESLA_PASSWORD`
- `TESLA_VEHICLE_ID` or VIN-based selection logic
- `LOCAL_PARKING_ZONES_JSON` with a list of configured parking zones

## Example parking zone JSON

```json
[
  {
    "id": "zone-1",
    "name": "Centrum Zuid",
    "latitude": 52.3676,
    "longitude": 4.9041,
    "radius_meters": 50
  },
  {
    "id": "zone-2",
    "name": "Marnixstraat",
    "latitude": 52.3721,
    "longitude": 4.8932,
    "radius_meters": 50
  }
]
```

## Notes

- The parking-zone provider integration must be implemented for your local authority or parking operator.
- The app is designed to be safe: it only triggers registration when the car transitions from driving to parked and only stops registration when the car transitions back to driving.
- For production use, add persistence, retries, and a proper secret manager.

## License

MIT
