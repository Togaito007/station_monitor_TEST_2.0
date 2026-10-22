# stations.py
import json
import os
import sys
from urllib.parse import urlsplit

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

json_path = resource_path("STATS_full.json")

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


def save_station(old_name, new_name, url):
    parsed_url = urlsplit(url)
    if not parsed_url.scheme or not parsed_url.hostname or parsed_url.port is None:
        raise ValueError("Station address must include a protocol, IP address, and port.")

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

    record["Name"] = new_name
    record["Protocol"] = parsed_url.scheme
    record["Main IP"] = parsed_url.hostname
    record["PORT"] = str(parsed_url.port)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    station_codes[new_name] = record["OACI_code"]
