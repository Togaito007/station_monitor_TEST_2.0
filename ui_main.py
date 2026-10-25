from qtpy.QtWidgets import QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QLabel, QPushButton, QMessageBox, QDialog, QDialogButtonBox, QHBoxLayout, QMenu, QLineEdit, QAction, QTableWidget, QTableWidgetItem, QFormLayout
from qtpy.QtGui import QIcon, QFont, QColor
from qtpy.QtCore import Qt
from qtpy import QtGui, QtCore
import webbrowser
import json
import os
from datetime import datetime
import httpx
import sys
import math
from urllib.parse import quote
from stations import STATION_FIELDS, get_station_metadata, save_station, station_codes


class StationDiagnosticsWorker(QtCore.QThread):
    results_ready = QtCore.Signal(dict)
    error_occurred = QtCore.Signal(str)

    def __init__(self, station_name, server_url, parent=None):
        super().__init__(parent)
        self.station_name = station_name
        self.server_url = server_url

    def run(self):
        try:
            response = httpx.get(
                f"{self.server_url}/stations/{quote(self.station_name, safe='')}/diagnostics",
                timeout=900.0,
            )
            response.raise_for_status()
            self.results_ready.emit(response.json()["results"])
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            self.error_occurred.emit(str(exc))


def load_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "confige.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                return json.load(f)
            except Exception:
                pass
    # Defaults
    else:
    	return {
        "noti_status": False,
        "down_alert_minutes": 60,
        "server_ip": "0.0.0.0",
        "server_port": 8000
    }

def save_config(config):
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "confige.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

def green_circle_icon(size=24):
    """Return a QIcon for a green circle of the given size."""
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setBrush(QColor(0, 255, 0))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)
    painter.end()
    return QIcon(pixmap)

def orange_half_circle_icon(size=24):
    """Return a QIcon for an orange half-circle of the given size."""
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setBrush(QColor(255, 165, 0))
    painter.setPen(Qt.NoPen)
    path = QtGui.QPainterPath()
    path.moveTo(size / 2, size)
    path.arcTo(0, 0, size, size, 0, 180)
    painter.drawPath(path)
    painter.end()
    return QIcon(pixmap)

def red_quarter_circle_icon(size=24):
    """Return a QIcon for a red quarter-circle of the given size."""
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setBrush(QColor(255, 0, 0))
    painter.setPen(Qt.NoPen)
    path = QtGui.QPainterPath()
    path.moveTo(size / 2, size / 2)
    path.arcTo(0, 0, size, size, 0, 90)
    painter.drawPath(path)
    painter.end()
    return QIcon(pixmap)

class MonitorWindow(QWidget):
    def __init__(self, stations, red_icon_path, green_icon_path, orange_icon_path):
        super().__init__()
        self.config = load_config()
        self.refresh_time = 15  # Client-side default, server controls actual monitoring
        self.noti_status = self.config.get("noti_status", False)
        self.down_alert_minutes = self.config.get("down_alert_minutes", 60)
        self.server_ip = self.config.get("server_ip", "10.1.1.1")
        self.server_port = self.config.get("server_port", 8000)
        self.SERVER_URL = f"http://{self.server_ip}:{self.server_port}"
        self.stations = sorted(stations, key=lambda x: x[0].lower())
        self.station_data = [None] * len(self.stations)
        self.notifications = []
        self.battery_voltages = [float('nan')] * len(self.stations)

        # HTTP client for server communication
        self.http_client = httpx.Client(timeout=10.0)
        self.server_available = True
        self._diagnostics_worker = None

        self.setWindowTitle("Station Monitor")
        self.setStyleSheet("""
            QWidget {
                background-color: #4b515e;
                color: #D8DEE9;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 14px;
            }
            QListWidget {
                border: 1px solid #4C566A;
                background-color: #3B4252;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #81A1C1;
                color: #2E3440;
            }
        """)

        # Settings button (top right)
        self.settings_button = QPushButton()
        self.settings_button.setIcon(QIcon.fromTheme("settings", QIcon("icons/settings.png")))
        self.settings_button.setFixedSize(40, 40)  # Button size
        self.settings_button.setIconSize(QtCore.QSize(40, 40))  # Icon size
        self.settings_button.setCursor(Qt.PointingHandCursor)  # Makes it interactive (pointer cursor)
        self.settings_button.setToolTip("Open settings")  # <-- Add this line for hover text
        self.settings_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #434C5E;
                border-radius: 8px;
            }
            QPushButton:pressed {
                background-color: #4C566A;
                border-radius: 8px;
            }
        """)
        self.settings_button.clicked.connect(self.open_settings_dialog)

        # Notification bell button
        self.bell_icon_off = QIcon("icons/notification-bell_off.png")
        self.bell_icon_on = QIcon("icons/notification-bell_on.png")
        self.bell_button = QPushButton()
        self.bell_button.setIcon(self.bell_icon_off)
        self.bell_button.setFixedSize(40, 40)
        self.bell_button.setIconSize(QtCore.QSize(40, 40))
        self.bell_button.setCursor(Qt.PointingHandCursor)
        self.bell_button.setToolTip("Show notifications")
        self.bell_button.setStyleSheet("""
            QPushButton { border: none; background: transparent; padding: 0px; }
            QPushButton:hover { background-color: #434C5E; border-radius: 8px; }
            QPushButton:pressed { background-color: #4C566A; border-radius: 8px; }
        """)
        self.bell_button.clicked.connect(self.show_notifications_window)

        # Layout
        layout = QVBoxLayout()
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.bell_button)      # Notification bell on the left
        hlayout.addStretch()                     # Spacer in the middle
        hlayout.addWidget(self.settings_button)  # Settings icon on the right
        layout.addLayout(hlayout)

        self.list_widget = QListWidget()
        self.list_widget.setSpacing(4)
        self.list_widget.setFont(QFont('Segoe UI', 11))
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        # Load icons once
        self.red_icon = QIcon(red_icon_path)
        self.green_icon = QIcon(green_icon_path)
        self.orange_icon = QIcon(orange_icon_path)

        # Populate list in alphabetical order
        for station_name, _ in self.stations:
            item = QListWidgetItem(station_name)
            item.setIcon(self.red_icon)
            item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.list_widget.addItem(item)
            self.setFixedWidth(self.sizeHint().width())
            self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())

        self.list_widget.itemClicked.connect(self.show_station_data)
        self.list_widget.itemActivated.connect(self.show_station_data)
        self.list_widget.itemDoubleClicked.connect(self.show_station_data)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

        # Start periodic updates from server
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_from_server)
        self.timer.start(self.refresh_time * 1000)  # Convert to ms

        # Initial update
        self.update_from_server()

    def fetch_status_from_server(self):
        try:
            response = self.http_client.get(f"{self.SERVER_URL}/stations/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Server error: {e}")
            self.server_available = False
            return None

    def fetch_notifications_from_server(self):
        try:
            response = self.http_client.get(f"{self.SERVER_URL}/notifications")
            response.raise_for_status()
            return response.json()["notifications"]
        except Exception as e:
            print(f"Failed to fetch notifications: {e}")
            return []

    def update_from_server(self):
        status_data = self.fetch_status_from_server()
        notifications = self.fetch_notifications_from_server()

        if status_data:
            self.server_available = True
            # Convert server data to UI format
            icon_states = []
            for station in status_data:
                station_name = station["name"]
                status = station["status"]
                data = station["data"]
                voltage = station["battery_voltage"]

                # Find index in our stations list
                try:
                    idx = next(i for i, (name, _) in enumerate(self.stations) if name == station_name)
                    self.station_data[idx] = data
                    self.battery_voltages[idx] = float(voltage) if isinstance(voltage, (int, float)) else float('nan')
                except StopIteration:
                    continue

                # Determine icon state
                if status == "up":

                    if (voltage!=None and 11.5 < voltage <12.0) or any(voltage==None or str(v).lower() in ["nan","none"] for v in data.values()):
#                        print(f"here orange: {voltage}")
                        icon_states.append("orange")
                    elif (voltage != None and voltage <11.5):
 #                       print(f"here red: {voltage}")
                        icon_states.append("red")
                    else:
#                        print(f"here green: {voltage}")
                        icon_states.append("green")
                else:
                        icon_states.append("red")

            self.update_icons(icon_states)
            self.update_notifications(notifications)
        else:
            self.server_available = False
            # Show server offline state
            self.show_server_offline()

    def show_server_offline(self):
        # Set all stations to red/offline state
        icon_states = ["red"] * len(self.stations)
        self.update_icons(icon_states)
        # Update window title to indicate offline
        self.setWindowTitle("Station Monitor - SERVER OFFLINE")

        # Start periodic updates from server
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_from_server)
        self.timer.start(self.refresh_time * 1000)  # Convert to ms

        # Initial update
        self.update_from_server()

    def open_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        layout = QVBoxLayout(dialog)

        # Notifications toggle
        notif_label = QLabel("Enable Notifications:")
        notif_toggle = QPushButton("ON")
        notif_toggle.setCheckable(True)
        notif_toggle.setChecked(self.noti_status)
        notif_toggle.setText("ON" if self.noti_status else "OFF")
        notif_toggle.setStyleSheet(
            "QPushButton { background-color: #BF616A; color: white; font-weight: bold; border-radius: 8px; padding: 8px 24px; } "
            "QPushButton:checked { background-color: #A3BE8C; }"
        )
        def toggle_notif():
            self.noti_status = notif_toggle.isChecked()
            notif_toggle.setText("ON" if self.noti_status else "OFF")
        notif_toggle.clicked.connect(toggle_notif)

        notif_layout = QHBoxLayout()
        notif_layout.addWidget(notif_label)
        notif_layout.addWidget(notif_toggle)
        layout.addLayout(notif_layout)

        # Down alert threshold
        down_alert_label = QLabel("Down alert threshold (minutes):")
        down_alert_edit = QLineEdit(str(self.down_alert_minutes))
        down_alert_edit.setValidator(QtGui.QIntValidator(1, 1440))
        down_alert_layout = QHBoxLayout()
        down_alert_layout.addWidget(down_alert_label)
        down_alert_layout.addWidget(down_alert_edit)
        layout.addLayout(down_alert_layout)

        # Server IP
        server_ip_label = QLabel("Server IP:")
        server_ip_edit = QLineEdit(self.server_ip)
        server_ip_layout = QHBoxLayout()
        server_ip_layout.addWidget(server_ip_label)
        server_ip_layout.addWidget(server_ip_edit)
        layout.addLayout(server_ip_layout)

        # Server Port
        server_port_label = QLabel("Server Port:")
        server_port_edit = QLineEdit(str(self.server_port))
        server_port_edit.setValidator(QtGui.QIntValidator(1, 65535))
        server_port_layout = QHBoxLayout()
        server_port_layout.addWidget(server_port_label)
        server_port_layout.addWidget(server_port_edit)
        layout.addLayout(server_port_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)

        def on_accept():
            try:
                self.down_alert_minutes = int(down_alert_edit.text())
                self.server_ip = server_ip_edit.text()
                self.server_port = int(server_port_edit.text())
                self.SERVER_URL = f"http://{self.server_ip}:{self.server_port}"
            except Exception:
                pass
            self.config["noti_status"] = self.noti_status
            self.config["down_alert_minutes"] = self.down_alert_minutes
            self.config["server_ip"] = self.server_ip
            self.config["server_port"] = self.server_port
            save_config(self.config)

            # Send config update to server (only server-relevant settings)
            server_config = {
                "noti_status": self.noti_status,
                "down_alert_minutes": self.down_alert_minutes
            }
            try:
                response = self.http_client.put(f"{self.SERVER_URL}/config", json=server_config)
                response.raise_for_status()
                print("Config updated on server")
            except Exception as e:
                print(f"Failed to update server config: {e}")

            dialog.accept()

        button_box.accepted.connect(on_accept)
        button_box.rejected.connect(dialog.reject)
        dialog.exec_()

    def update_icons(self, icon_states):
        for i, state in enumerate(icon_states):
            if i < self.list_widget.count():
                item = self.list_widget.item(i)
                base_name = self.stations[i][0]
                item.setText(base_name)

                # Set station state icon (dot) on the left
                if state == "green":
                    item.setIcon(self.green_icon)
                elif state == "orange":
                    item.setIcon(self.orange_icon)
                else:
                    item.setIcon(self.red_icon)

    def update_notifications(self, notifications):
        """Update notification list and bell icon."""
        self.notifications = notifications
        if notifications:
            self.bell_button.setIcon(self.bell_icon_on)
        else:
            self.bell_button.setIcon(self.bell_icon_off)

    def show_station_data(self, item):
        idx = self.list_widget.row(item)
        data = self.station_data[idx]
        station_name, station_url = self.stations[idx]

        # Use cached battery voltage from server
        battery_voltage = self.battery_voltages[idx]
        if battery_voltage != battery_voltage:  # NaN check
            battery_str = "N/A"
        else:
            battery_str = f"{battery_voltage:.2f} V"

        if not data:
            msg = "No data fetched."
        elif isinstance(data, dict):
            msg = "\n".join(f"{k}: {v}" for k, v in data.items())
        else:
            msg = str(data)
        msg += f"\nBattery Voltage: {battery_str}"

        dialog = QDialog(self)
        dialog.setWindowTitle(station_name)
        layout = QVBoxLayout(dialog)
        label = QLabel(msg)
        layout.addWidget(label)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        com_button = QPushButton("COM")
        display_button = QPushButton("Display")
        button_box.addButton(com_button, QDialogButtonBox.ActionRole)
        button_box.addButton(display_button, QDialogButtonBox.ActionRole)
        layout.addWidget(button_box)

        def open_browser():
            webbrowser.open(station_url)

        def open_com():
            com_url = station_url.rstrip('/') + "/ims/html2/communication.html"
            webbrowser.open(com_url)

        display_button.clicked.connect(open_browser)
        com_button.clicked.connect(open_com)
        button_box.accepted.connect(dialog.accept)
        dialog.exec_()

    def show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if item is not None:
            menu = QMenu(self)
            action1 = menu.addAction("Modify station")
            action2 = menu.addAction("Logs")
            action3 = menu.addAction("Diagnostics")
            action = menu.exec_(self.list_widget.mapToGlobal(pos))
            if action == action1:
                self.modify_station_dialog(item)
            elif action == action2:
                self.show_station_logs(item)
            elif action == action3:
                self.show_station_diagnostics(item)

    def show_station_diagnostics(self, item):
        if self._diagnostics_worker is not None and self._diagnostics_worker.isRunning():
            return

        station_name = item.text()
        try:
            metadata = get_station_metadata(station_name)
        except (OSError, ValueError, KeyError) as exc:
            QMessageBox.critical(self, "Unable to load station", str(exc))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"{station_name} Diagnostics")
        dialog.setWindowFlag(Qt.WindowCloseButtonHint, False)
        layout = QVBoxLayout(dialog)
        result_labels = {}
        for category, ip_field in (
            ("Main IMS", "Main IP"),
            ("Main server", "Main IP"),
            ("Secondary IMS", "Secondary IP"),
            ("Secondary server", "Secondary IP"),
        ):
            label = QLabel(f"{category} ({metadata[ip_field]}): Checking...")
            result_labels[category] = label
            layout.addWidget(label)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        close_button = button_box.button(QDialogButtonBox.Close)
        close_button.setEnabled(False)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        worker = StationDiagnosticsWorker(station_name, self.SERVER_URL, self)
        self._diagnostics_worker = worker

        def show_results(results):
            for category, result in results.items():
                label = result_labels[category]
                label.setText(f"{category} ({result['ip']}): {result['status']}")
            close_button.setEnabled(True)

        def show_error(message):
            for label in result_labels.values():
                label.setText(f"Error: {message}")
            close_button.setEnabled(True)

        def finish_worker():
            if self._diagnostics_worker is worker:
                self._diagnostics_worker = None

        worker.results_ready.connect(show_results)
        worker.error_occurred.connect(show_error)
        worker.finished.connect(finish_worker)
        worker.start()
        dialog.exec_()

    def show_station_logs(self, item):
        idx = self.list_widget.row(item)
        station_name, station_url = self.stations[idx]
        icao = station_codes.get(station_name, station_name)

        # Fetch logs from server
        try:
            response = self.http_client.get(f"{self.SERVER_URL}/logs?lines=1000")
            response.raise_for_status()
            server_logs = response.json()["logs"]
        except Exception as e:
            print(f"Failed to fetch logs from server: {e}")
            server_logs = []

        # Filter logs for this station
        logs = []
        for i, line in enumerate(server_logs):
            if icao in line:
                # Time is the previous line (if it looks like a datetime)
                if i > 0 and self.is_datetime_line(server_logs[i-1]):
                    time_str = server_logs[i-1].strip()
                else:
                    time_str = ""
                event_str = line.strip()
                logs.append((time_str, event_str))

        # UI for filtering and exporting
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{station_name} Logs")
        layout = QVBoxLayout(dialog)

        # Date filter widgets
        filter_layout = QHBoxLayout()
        from_label = QLabel("From:")
        from_date = QLineEdit()
        from_date.setPlaceholderText("YYYY-MM-DD")
        to_label = QLabel("To:")
        to_date = QLineEdit()
        to_date.setPlaceholderText("YYYY-MM-DD")
        filter_button = QPushButton("Filter")
        filter_layout.addWidget(from_label)
        filter_layout.addWidget(from_date)
        filter_layout.addWidget(to_label)
        filter_layout.addWidget(to_date)
        filter_layout.addWidget(filter_button)
        layout.addLayout(filter_layout)

        table = QTableWidget(dialog)
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Time", "Event"])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.horizontalHeader().setStretchLastSection(True)

        # Helper to filter logs by date
        def filter_logs():
            f = from_date.text().strip()
            t = to_date.text().strip()
            filtered = []
            for time_str, event_str in logs:
                if self.is_datetime_line(time_str):
                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
                    if f:
                        try:
                            dt_from = datetime.strptime(f, "%Y-%m-%d")
                            if dt < dt_from:
                                continue
                        except Exception:
                            pass
                    if t:
                        try:
                            dt_to = datetime.strptime(t, "%Y-%m-%d")
                            if dt > dt_to:
                                continue
                        except Exception:
                            pass
                filtered.append((time_str, event_str))
            return filtered

        # Fill table with logs (filtered or not)
        def update_table(logs_to_display):
            table.setRowCount(len(logs_to_display))
            for row, (time_str, event_str) in enumerate(reversed(logs_to_display)):
                table.setItem(row, 0, QTableWidgetItem(time_str))
                table.setItem(row, 1, QTableWidgetItem(event_str))

        # Initial display
        update_table(logs)

        # Filter button logic
        def on_filter():
            filtered = filter_logs()
            update_table(filtered)

        filter_button.clicked.connect(on_filter)

        # Export button
        export_button = QPushButton("Export")
        def on_export():
            filtered = []
            for row in range(table.rowCount()):
                time_str = table.item(row, 0).text()
                event_str = table.item(row, 1).text()
                filtered.append((time_str, event_str))
            outputs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Outputs")
            os.makedirs(outputs_dir, exist_ok=True)
            export_path = os.path.join(outputs_dir, f"{station_name.replace(' ', '_')}_logs.csv")
            with open(export_path, "w", encoding="utf-8") as f:
                f.write("Time,Event\n")
                for time_str, event_str in filtered:
                    # Escape commas in event_str
                    event_str = event_str.replace(",", ";")
                    f.write(f'"{time_str}","{event_str}"\n')
            QMessageBox.information(self, "Export", f"Logs exported to {export_path}")

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.addButton(export_button, QDialogButtonBox.ActionRole)
        layout.addWidget(table)
        layout.addWidget(button_box)

        export_button.clicked.connect(on_export)
        button_box.accepted.connect(dialog.accept)
        dialog.exec_()

    def is_datetime_line(self, line):
        # Checks if the line looks like a datetime string
        try:
            datetime.strptime(line.strip(), "%Y-%m-%d %H:%M:%S.%f")
            return True
        except Exception:
            return False

    def show_notifications_window(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Notifications")
        layout = QVBoxLayout(dialog)

        table = QTableWidget(dialog)
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Notification", "Time"])
        table.setRowCount(len(self.notifications))
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.horizontalHeader().setStretchLastSection(True)

        # Most recent first
        for row, notif in enumerate(reversed(self.notifications)):
            text = notif.get("message", "No message")
            t = notif.get("timestamp", "No time")
            table.setItem(row, 0, QTableWidgetItem(text))
            table.setItem(row, 1, QTableWidgetItem(str(t)))

        layout.addWidget(table)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        clear_button = QPushButton("Clear")
        button_box.addButton(clear_button, QDialogButtonBox.ActionRole)
        layout.addWidget(button_box)

        def clear_notifications():
            self.notifications = []
            self.update_notifications([])
            table.setRowCount(0)
            self.bell_button.setIcon(self.bell_icon_off)

        clear_button.clicked.connect(clear_notifications)
        button_box.accepted.connect(dialog.accept)
        dialog.exec_()

    def modify_station_dialog(self, item):
        idx = self.list_widget.row(item)
        station_name, station_url = self.stations[idx]
        try:
            metadata = get_station_metadata(station_name)
        except (OSError, ValueError, KeyError) as exc:
            QMessageBox.critical(self, "Unable to load station", str(exc))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Modify Station")
        form_layout = QFormLayout(dialog)
        fields = {
            field: QLineEdit(metadata[field])
            for field in STATION_FIELDS
        }
        form_layout.addRow("Name:", fields["Name"])
        form_layout.addRow("OACI code:", fields["OACI_code"])
        form_layout.addRow("OMM code:", fields["OMM_code"])

        ip_fields = QHBoxLayout()
        ip_fields.addWidget(fields["Main IP"])
        swap_button = QPushButton("↔")
        swap_button.setToolTip("Swap main and secondary IP addresses")
        swap_button.setAccessibleName("Swap main and secondary IP addresses")
        swap_button.setFixedWidth(36)
        ip_fields.addWidget(swap_button)
        ip_fields.addWidget(fields["Secondary IP"])

        def swap_station_ips():
            main_ip = fields["Main IP"].text()
            secondary_ip = fields["Secondary IP"].text()
            fields["Main IP"].setText(secondary_ip)
            fields["Secondary IP"].setText(main_ip)

        swap_button.clicked.connect(swap_station_ips)
        form_layout.addRow("Main / Secondary IP:", ip_fields)
        form_layout.addRow("PORT:", fields["PORT"])
        form_layout.addRow("Protocol:", fields["Protocol"])

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        form_layout.addRow(button_box)

        def on_accept():
            updated_metadata = {
                field: fields[field].text().strip()
                for field in STATION_FIELDS
            }
            changes = [
                f"{field}: '{metadata[field]}' -> '{updated_metadata[field]}'"
                for field in STATION_FIELDS
                if metadata[field] != updated_metadata[field]
            ]
            try:
                new_url = save_station(station_name, updated_metadata)
            except (OSError, ValueError, KeyError) as exc:
                QMessageBox.critical(self, "Unable to save station", str(exc))
                return

            # Update in memory
            new_name = updated_metadata["Name"]
            self.stations[idx] = (new_name, new_url)
            item.setText(new_name)
            # Notify server about station modification
            if changes:
                station_update = {
                    "name": new_name,
                    "url": new_url,
                    "metadata": updated_metadata,
                }
                try:
                    response = self.http_client.put(f"{self.SERVER_URL}/stations/{station_name}", json=station_update)
                    response.raise_for_status()
                    print(f"Server notified about station modification: {station_name} -> {new_name}")
                except Exception as e:
                    print(f"Failed to notify server about station modification: {e}")
                try:
                    log_msg = (
                        f"{datetime.now()} - Modified station {station_name}:\n"
                        + "\n".join(changes)
                        + "\n------LOG_END\n"
                    )
                    self.log_modification(log_msg)
                except OSError as exc:
                    QMessageBox.critical(self, "Unable to write station log", str(exc))
            dialog.accept()

        button_box.accepted.connect(on_accept)
        button_box.rejected.connect(dialog.reject)

        dialog.exec_()

    def log_modification(self, message):
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, "logs.txt")
        with open(log_path, "a") as log_file:
            log_file.write(message)
