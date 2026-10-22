# stations.py
import json
import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

json_path = resource_path("STATS_full.json")
STATION_FIELDS = (
    "Name",
    "OACI_code",
    "OMM_code",
    "Main IP",
    "Secondary IP",
    "PORT",
    "Protocol",
)

with open(json_path, "r", encoding="utf-8") as f:
    station_records = json.load(f)

stations = [
    (
        station["Name"],
        f'{station["Protocol"]}://{station["Main IP"]}:{station["PORT"]}',
    )
    for station in station_records
]
station_codes = {
    station["Name"]: station["OACI_code"]
    for station in station_records
}


def get_station_metadata(name):
    station_code = station_codes.get(name)
    with open(json_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    record = next(
        (
            station
            for station in records
            if station["Name"] == name
            or (station_code and station.get("OACI_code") == station_code)
        ),
        None,
    )
    if record is None:
        raise ValueError(f"Station '{name}' was not found in STATS_full.json.")
    return {field: str(record[field]) for field in STATION_FIELDS}


def save_station(old_name, metadata):
    station_code = station_codes.get(old_name)
    with open(json_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    record = next(
        (
            station
            for station in records
            if station["Name"] == old_name
            or (station_code and station.get("OACI_code") == station_code)
        ),
        None,
    )
    if record is None:
        raise ValueError(f"Station '{old_name}' was not found in STATS_full.json.")

    updated_metadata = {
        field: str(metadata[field]).strip()
        for field in STATION_FIELDS
    }
    if any(not value for value in updated_metadata.values()):
        raise ValueError("All station metadata fields must have a value.")
    if updated_metadata["Protocol"] not in ("http", "https"):
        raise ValueError("Protocol must be either 'http' or 'https'.")
    try:
        port = int(updated_metadata["PORT"])
    except ValueError as exc:
        raise ValueError("PORT must be a number between 1 and 65535.") from exc
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be a number between 1 and 65535.")
    updated_metadata["PORT"] = str(port)

    record.update(updated_metadata)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    station_records[:] = records
    station_codes.pop(old_name, None)
    station_codes[record["Name"]] = record["OACI_code"]
    return f'{record["Protocol"]}://{record["Main IP"]}:{record["PORT"]}'
