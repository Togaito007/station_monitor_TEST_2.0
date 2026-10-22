import aiohttp
import asyncio
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import json
import os
from urllib.parse import urlsplit
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.responses import RedirectResponse,FileResponse,HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from plyer import notification
from inst_mon.instrument_monitor import get_weather_data
from inst_mon.battery_monitor import BatteryMonitor
from gbon_page.dashboard import render_dashboard_html
from stations import get_station_metadata, save_station, stations as configured_stations


        
# Pydantic models for API responses
class StationStatus(BaseModel):
    name: str
    url: str
    status: str  # "up", "down", "unknown"
    data: Dict[str, Any]
    battery_voltage: float
    last_checked: str

class ConfigResponse(BaseModel):
    refresh_time: int
    noti_status: bool
    down_alert_minutes: int
    server_ip: str
    server_port: int

class ConfigUpdate(BaseModel):
    refresh_time: Optional[int] = None
    noti_status: Optional[bool] = None
    down_alert_minutes: Optional[int] = None
    server_ip: Optional[str] = None
    server_port: Optional[int] = None
class StationUpdate(BaseModel):
    name: str
    url: str
    metadata: Optional[Dict[str, str]] = None
# Global state
battery_monitor = BatteryMonitor()
monitoring_task: Optional[asyncio.Task] = None

# Monitoring state
stations_status: Dict[str, Dict] = {}
down_stations: List[str] = []
down_data: Dict[str, List[str]] = {}
station_down_since: Dict[str, datetime] = {}
instrument_down_since: Dict[str, Dict[str, datetime]] = {}

# Configuration
config = {
    "refresh_time": 30,
    "noti_status": False,
    "down_alert_minutes": 30,
    "server_ip": "0.0.0.0",
    "server_port": 8000
}

# Load config from file
def load_config():
    global config
    try:
        with open('server_confige.json', 'r') as f:
            config.update(json.load(f))
    except FileNotFoundError:
        save_config()

def save_config():
    with open('server_confige.json', 'w') as f:
        json.dump(config, f, indent=2)

stations = list(configured_stations)
load_config()

# Notification function
def alert_message(title, message, t_out=15):
    notification.notify(
        title=title,
        message=message,
        timeout=t_out
    )

# Logging function
def log_it(name, message=""):
    os.makedirs('Logs', exist_ok=True)
    with open('Logs/' + name + '.txt', 'a') as a:
        a.write(str(datetime.now()) + '\n' + message + '\n------LOG_END\n')

# Station checking functions (existing logic)
async def check_station(session, url):
    try:
        async with session.get(url, timeout=30, ssl=False) as response:
            return response.status == 200
    except Exception:
        return False

executor = ThreadPoolExecutor(max_workers=10)

async def check_station_and_data(session, name, url):
    try:
        async with session.get(url, timeout=30, ssl=False) as response:
            accessible = response.status == 200
    except Exception:
        return False, None

    if accessible:
        loop = asyncio.get_event_loop()
        try:
            data = await asyncio.wait_for(
                loop.run_in_executor(executor, get_weather_data, url),
                timeout=30
            )
        except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
            data = None
        return True, data
    else:
        return False, None

async def get_statuses(stations, noti_status, down_alert_minutes=60, refresh_time=15):
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        statuses = []
        data_list = []
        notifications = []
        now = datetime.now()

        tasks = [
            check_station_and_data(session, name, url)
            for name, url in stations
        ]
        results = await asyncio.gather(*tasks)

        for i, (name, url) in enumerate(stations):
            accessible, data = results[i]
            data_list.append(data)

            if not accessible and (name not in down_stations):
                message = f"Station {name} is down. URL: {url}"
                log_it("logs", message)
                if noti_status:
                    alert_message('Station down', message)
                down_stations.append(name)
                station_down_since[name] = now
            elif accessible and (name in down_stations):
                message = f"Station {name} is back up. URL: {url}"
                log_it("logs", message)
                if noti_status:
                    alert_message('Station back up', message)
                down_stations.remove(name)
                if name in station_down_since:
                    del station_down_since[name]
            statuses.append(accessible)

            if accessible and data is not None:
                prev_down = set(down_data.get(name, []))
                current_down = set(k for k, v in data.items() if str(v) == "nan")

                for param in current_down - prev_down:
                    message = f"{param} is down at {name}."
                    log_it("logs", message)
                    if noti_status:
                        alert_message(f"{param} down", message)

                    if name not in instrument_down_since:
                        instrument_down_since[name] = {}
                    instrument_down_since[name][param] = now

                for param in prev_down - current_down:
                    message = f"{param} is back-up at {name}."
                    log_it("logs", message)
                    if noti_status:
                        alert_message(f"{param} back-up", message)

                    if name in instrument_down_since and param in instrument_down_since[name]:
                        del instrument_down_since[name][param]
                if current_down:
                    down_data[name] = list(current_down)
                elif name in down_data:
                    del down_data[name]

                if name in instrument_down_since and not instrument_down_since[name]:
                    del instrument_down_since[name]
            elif name in down_data:
                del down_data[name]
                if name in instrument_down_since:
                    del instrument_down_since[name]

        for name in down_stations:
            if name in station_down_since and (now - station_down_since[name]) >= timedelta(minutes=down_alert_minutes):
                notif_text = f"Station {name} has been down for {down_alert_minutes} minutes"
                notifications.append((notif_text, now.strftime("%Y-%m-%d %H:%M:%S")))
                if noti_status:
                    alert_message("Station down", notif_text)
                log_it("logs", notif_text)

        for name, params in instrument_down_since.items():
            for param, down_time in params.items():
                if (now - down_time) >= timedelta(minutes=down_alert_minutes):
                    notif_text = f"{name}'s instrument '{param}' has been down for {down_alert_minutes} minutes"
                    notifications.append((notif_text, now.strftime("%Y-%m-%d %H:%M:%S")))
                    if noti_status:
                        alert_message("Instrument down", notif_text)
                    log_it("logs", notif_text)

        print(f"Checking ...{datetime.now()}")

    return statuses, data_list, notifications

async def get_battery_voltages(stations):
    loop = asyncio.get_event_loop()
    voltages = []
    for name, url in stations:
        # Run battery check in executor to avoid blocking
        voltage = await loop.run_in_executor(None, battery_monitor.get_batterie_status, url)
        voltages.append(voltage)
    return voltages

# Background monitoring loop
async def monitoring_loop():
    while True:
        try:
            # Get current status
            statuses, data, notifications = await get_statuses(stations, config["noti_status"], config["down_alert_minutes"], config["refresh_time"])
            voltages = await get_battery_voltages(stations)

            # Update global state
            for i, (name, url) in enumerate(stations):
                status_str = "up" if statuses[i] else "down"
                station_data = data[i] if data[i] is not None else {}
                voltage = voltages[i] if i < len(voltages) else float('nan')

                stations_status[name] = {
                    "name": name,
                    "url": url,
                    "status": status_str,
                    "data": station_data,
                    "battery_voltage": voltage,
                    "last_checked": datetime.now().isoformat()
                }

            await asyncio.sleep(config["refresh_time"])
        except Exception as e:
            print(f"Monitoring loop error: {e}")
            await asyncio.sleep(30)  # Retry after 30 seconds on error

# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global monitoring_task
    monitoring_task = asyncio.create_task(monitoring_loop())
    print("Station Monitor API started")
    yield
    # Shutdown
    if monitoring_task:
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass
    print("Station Monitor API stopped")

app = FastAPI(title="Station Monitor API", version="1.0.0", lifespan=lifespan)
class AutoIndexStaticFiles(StaticFiles):
    """Subclass of StaticFiles that natively catches directory views."""
    async def get_response(self, path: str, scope):
        # 1. Normalize the path and find its physical equivalent on disk
        full_path = os.path.normpath(os.path.join(self.directory, path))
        
        # 2. If it's a valid directory, intercept immediately and show the HTML index
        if os.path.isdir(full_path):
            return self._render_directory_index(path, full_path)
            
        # 3. If it's a file path, hand it off to standard StaticFiles download logic
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            raise exc

    def _render_directory_index(self, virtual_path, physical_path):
        links = []
        
        # Clean up virtual paths for formatting
        virtual_path = virtual_path.strip("/")
        
        # Add a "Go Back" button if we aren't at the root level
        if virtual_path and virtual_path != ".":
            links.append('<li>📁 <a href="../"><b>../ (Go Up)</b></a></li>')
            
        try:
            # Sort folders first, then files
            items = sorted(os.listdir(physical_path))
        except PermissionError:
            return HTMLResponse(content="<h3>Permission Denied</h3>", status_code=403)
            
        for item in items:
            if item.startswith('.'): 
                continue  # Skip hidden operating system files like .DS_Store
            
            is_dir = os.path.isdir(os.path.join(physical_path, item))
            slash = "/" if is_dir else ""
            download_attr = "" if is_dir else "download"  # Forces immediate save for files
            
            # Form clean structural hyperlinks
            links.append(
                f'<li>{"📁" if is_dir else "📄"} '
                f'<a href="{item}{slash}" {download_attr}>{item}{slash}</a></li>'
            )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Index of /{virtual_path}</title>
            <style>
                body {{ font-family: sans-serif; margin: 40px; background: #fafafa; color: #333; }}
                h2 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; }}
                ul {{ list-style: none; padding: 0; }}
                li {{ padding: 10px; border-bottom: 1px solid #eee; font-size: 16px; }}
                a {{ text-decoration: none; color: #0066cc; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h2>Index of /{virtual_path if virtual_path else 'Root'}</h2>
            <ul>
                {''.join(links)}
            </ul>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
app.mount("/rapports", AutoIndexStaticFiles(directory="../Rapports"), name="Rapports")

# API Endpoints

@app.get("/stations/status", response_model=List[StationStatus])
async def get_stations_status():
    return list(stations_status.values())

@app.get("/stations/{station_name}", response_model=StationStatus)
async def get_station_detail(station_name: str):
    if station_name not in stations_status:
        raise HTTPException(status_code=404, detail="Station not found")
    return stations_status[station_name]

@app.get("/config", response_model=ConfigResponse)
async def get_config_endpoint():
    return config

@app.put("/config")
async def update_config_endpoint(new_config: ConfigUpdate):
    global config
    update_data = new_config.dict(exclude_unset=True)
    config.update(update_data)
    save_config()
    return {"message": "Config updated", "config": config}

@app.put("/stations/{station_name}")
async def update_station_endpoint(station_name: str, station_update: StationUpdate):
    global stations
    # Find the station by old name
    station_idx = None
    for i, (name, url) in enumerate(stations):
        if name == station_name:
            station_idx = i
            break
    
    if station_idx is None:
        raise HTTPException(status_code=404, detail="Station not found")
    
    try:
        old_metadata = get_station_metadata(station_name)
        metadata = station_update.metadata or old_metadata.copy()
        metadata["Name"] = station_update.name
        if station_update.metadata is None:
            parsed_url = urlsplit(station_update.url)
            if not parsed_url.scheme or not parsed_url.hostname or parsed_url.port is None:
                raise ValueError("Station address must include a protocol, IP address, and port.")
            metadata["Protocol"] = parsed_url.scheme
            metadata["Main IP"] = parsed_url.hostname
            metadata["PORT"] = str(parsed_url.port)
        new_url = save_station(station_name, metadata)
    except (OSError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    stations[station_idx] = (station_update.name, new_url)
    
    # Update the global stations_status with the new URL
    if station_name in stations_status:
        stations_status[station_update.name] = stations_status.pop(station_name)
        stations_status[station_update.name]["name"] = station_update.name
        stations_status[station_update.name]["url"] = new_url
    
    changed_fields = ", ".join(
        f"{field}: '{old_value}' -> '{metadata[field]}'"
        for field, old_value in old_metadata.items()
        if old_value != metadata[field]
    )
    log_it(
        "logs",
        f"Server: Updated station '{station_name}' to '{station_update.name}': {changed_fields}",
    )
    
    return {
        "message": "Station updated",
        "station": {
            "name": station_update.name,
            "url": new_url
        }
    }

@app.get("/logs")
async def get_logs(lines: int = 100):
    try:
        with open("Logs/logs.txt", "r") as f:
            logs = f.readlines()#[-lines:]
        return {"logs": [log.strip() for log in logs]}
    except FileNotFoundError:
        return {"logs": []}

@app.get("/notifications")
async def get_notifications():
    notifications = []
    now = datetime.now()

    for name in down_stations:
        if name in station_down_since:
            down_time = now - station_down_since[name]
            if down_time >= timedelta(minutes=config["down_alert_minutes"]):
                notifications.append({
                    "type": "station_down",
                    "station": name,
                    "message": f"Station {name} has been down for {int(down_time.total_seconds() // 60)} minutes",
                    "timestamp": station_down_since[name].isoformat()
                })

    for name, params in instrument_down_since.items():
        for param, down_time in params.items():
            if (now - down_time) >= timedelta(minutes=config["down_alert_minutes"]):
                notifications.append({
                    "type": "instrument_down",
                    "station": name,
                    "instrument": param,
                    "message": f"{name}'s instrument '{param}' has been down for {int((now - down_time).total_seconds() // 60)} minutes",
                    "timestamp": down_time.isoformat()
                })

    return {"notifications": notifications}

@app.get("/dashboard", include_in_schema=False)
async def dashboard_page():
    return HTMLResponse(content=render_dashboard_html())

@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/dashboard")

if __name__ == "__main__":
    uvicorn.run(app, host=config["server_ip"], port=config["server_port"])
