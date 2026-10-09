from app.parking import ParkingZone, find_nearest_parking_zone
from app.tesla_client import VehicleStatus
from app.state import CarStateMachine


def test_find_nearest_zone():
    zones = [
        ParkingZone(id="a", name="A", latitude=52.0, longitude=4.0),
        ParkingZone(id="b", name="B", latitude=52.1, longitude=4.1),
        ParkingZone(id="c", name="C", latitude=53.0, longitude=5.0),
    ]

    nearest = find_nearest_parking_zone(52.05, 4.05, zones)
    assert nearest is not None
    assert nearest.id == "a"


def test_car_state_machine_transitions_to_parking():
    events = []

    def on_park(status, zone):
        events.append(("park", status.vehicle_id, zone))

    def on_drive(status):
        events.append(("drive", status.vehicle_id, None))

    machine = CarStateMachine(on_park=on_park, on_drive=on_drive)

    parked = VehicleStatus(vehicle_id="abc", speed_kmh=0, shift_state="P")
    moving = VehicleStatus(vehicle_id="abc", speed_kmh=12, shift_state="D")

    machine.update(parked)
    machine.update(moving)

    assert events[0][0] == "park"
    assert events[1][0] == "drive"

    assert machine.current_state == "driving"

    machine.update(parked)
    assert machine.current_state == "parked"

    assert len(events) == 3

