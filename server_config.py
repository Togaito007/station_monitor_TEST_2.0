from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QHBoxLayout, QMessageBox, QDialogButtonBox
from qtpy.QtGui import QIntValidator
import httpx
import json
import os

SERVER_URL = "http://localhost:8000"

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server_config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                return json.load(f)
            except Exception:
                pass
    # Defaults
    else:
    	return {
        "refresh_time": 30,
        "noti_status": False,
        "down_alert_minutes": 30,
        "server_ip": "10.1.1.1",
        "server_port": 8000
    }

def save_config(config):
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

class ServerConfigWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Server Configuration")
        self.setStyleSheet("""
            QWidget {
                background-color: #4b515e;
                color: #D8DEE9;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout()

        # Fetch current config from server
        self.config = self.fetch_config()

        # Refresh time
        refresh_label = QLabel("Refresh interval (seconds):")
        self.refresh_edit = QLineEdit(str(self.config.get("refresh_time", 30)))
        self.refresh_edit.setValidator(QIntValidator(1, 3600))
        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(refresh_label)
        refresh_layout.addWidget(self.refresh_edit)
        layout.addLayout(refresh_layout)

        # Notifications toggle
        notif_label = QLabel("Enable Notifications:")
        self.notif_toggle = QPushButton("ON" if self.config.get("noti_status", False) else "OFF")
        self.notif_toggle.setCheckable(True)
        self.notif_toggle.setChecked(self.config.get("noti_status", False))
        self.notif_toggle.setText("ON" if self.config.get("noti_status", False) else "OFF")
        self.notif_toggle.setStyleSheet(
            "QPushButton { background-color: #BF616A; color: white; font-weight: bold; border-radius: 8px; padding: 8px 24px; } "
            "QPushButton:checked { background-color: #A3BE8C; }"
        )
        def toggle_notif():
            self.notif_toggle.setText("ON" if self.notif_toggle.isChecked() else "OFF")
        self.notif_toggle.clicked.connect(toggle_notif)

        notif_layout = QHBoxLayout()
        notif_layout.addWidget(notif_label)
        notif_layout.addWidget(self.notif_toggle)
        layout.addLayout(notif_layout)

        # Down alert threshold
        down_alert_label = QLabel("Down alert threshold (minutes):")
        self.down_alert_edit = QLineEdit(str(self.config.get("down_alert_minutes", 30)))
        self.down_alert_edit.setValidator(QIntValidator(1, 1440))
        down_alert_layout = QHBoxLayout()
        down_alert_layout.addWidget(down_alert_label)
        down_alert_layout.addWidget(self.down_alert_edit)
        layout.addLayout(down_alert_layout)

        # Server IP
        server_ip_label = QLabel("Server IP:")
        self.server_ip_edit = QLineEdit(self.config.get("server_ip", "10.1.1.1"))
        server_ip_layout = QHBoxLayout()
        server_ip_layout.addWidget(server_ip_label)
        server_ip_layout.addWidget(self.server_ip_edit)
        layout.addLayout(server_ip_layout)

        # Server Port
        server_port_label = QLabel("Server Port:")
        self.server_port_edit = QLineEdit(str(self.config.get("server_port", 8000)))
        self.server_port_edit.setValidator(QIntValidator(1, 65535))
        server_port_layout = QHBoxLayout()
        server_port_layout.addWidget(server_port_label)
        server_port_layout.addWidget(self.server_port_edit)
        layout.addLayout(server_port_layout)

        # Save button
        save_button = QPushButton("Save Configuration")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def fetch_config(self):
        try:
            response = httpx.get(f"{SERVER_URL}/config", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to fetch config: {e}")
            return load_config()

    def save_config(self):
        try:
            new_config = {
                "refresh_time": int(self.refresh_edit.text()),
                "noti_status": self.notif_toggle.isChecked(),
                "down_alert_minutes": int(self.down_alert_edit.text()),
                "server_ip": self.server_ip_edit.text(),
                "server_port": int(self.server_port_edit.text())
            }
            response = httpx.put(f"{SERVER_URL}/config", json=new_config, timeout=10.0)
            response.raise_for_status()
            save_config(new_config)  # Also save locally
            QMessageBox.information(self, "Success", "Configuration saved successfully. Restart server to apply IP/Port changes.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save config: {e}")

if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = ServerConfigWindow()
    window.show()
    sys.exit(app.exec_())
