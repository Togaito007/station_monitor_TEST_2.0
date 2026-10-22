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

json_path = resource_path("stations.json")
#json_path_2 = resource_path("stations_sec.json")

with open(json_path, "r") as f:
    stations = json.load(f)
    
#with open(json_path2, "r") as f:
#   stations_sec = json.load(f)
