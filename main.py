import sys
from qtpy.QtWidgets import QApplication

from stations import stations
from ui_main import MonitorWindow

def main():
    app = QApplication(sys.argv)

    red_icon_path = "icons/red_dot.png"
    green_icon_path = "icons/green_dot.png"
    orange_icon_path = "icons/orange_dot.png"

    window = MonitorWindow(stations, red_icon_path, green_icon_path, orange_icon_path)
    window.resize(400, 50000000)
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
