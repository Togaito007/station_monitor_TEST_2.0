import requests
import re
import urllib3
import time 
import datetime
def get_weather_data(base_url):
    """
    Fetches weather data from the specified base URL and extracts key values.
    The timestamp in the request payload is dynamically generated based on the current time.

    Args:
        base_url (str): The base URL of the API (e.g., "https://10.31.16.151:8443").

    Returns:
        dict: A dictionary containing the extracted weather data, or None if an error occurs.
    """
    
    
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    api_endpoint = "/ims/rpc/com.microstepmis.agentspace.spaceview.SpaceView/getInstance"
    url = f"{base_url}{api_endpoint}"

    headers = {
        "Content-Type": "text/xml" 
    }

   
    current_timestamp_ms = int(time.time() * 1000)

    params = {
        "action": "rpc",
        "jsAllowed": "true",
        "timestamp": str(current_timestamp_ms) 
    }

    payload = """
    <x xclass="com.microstepmis.xplatform.rpc.RPCRequest" className="com.microstepmis.agentspace.spaceview.SpaceView" methodName="getInstance">
        <arguments>
            <x xclass="String">c/weatherDisplay</x>
            <x xclass="String">../cfg/displays/weatherDisplay.xml</x>
        </arguments>
    </x>
    """

    data = {}

    try:
        response = requests.post(url, headers=headers, params=params, data=payload, verify=False, timeout=30)
        response.raise_for_status()  

        response_text = response.text
 #       print(response_text)
#        input()
        wind_speed_match = re.search(r'name="f/Speed/MET".*?__x6\.value=([\d.]+);', response_text, re.DOTALL)

        if wind_speed_match:
            data['Vent(F m/s)'] = float(wind_speed_match.group(1))
        else:
            data['Vent(F m/s)'] = float('nan')	
        
        prec1h_match = re.search(r'name="f/Prec1h/MET".*?__x5\.value=([\d.]+);', response_text, re.DOTALL)

        if prec1h_match:
            data['Precipitation'] = float(prec1h_match.group(1))
        else:
            data['Precipitation'] = float('nan')
        
        stpress_match = re.search(r'name="m/StPress/MET".*?__x5\.value=([\d.]+);', response_text, re.DOTALL)

        if stpress_match and float(stpress_match.group(1)) > 800:
            data['Pression'] = float(stpress_match.group(1))
        else:
            data['Pression'] = float('nan')


        
        hum_match = re.search(r'name="m/Hum/MET".*?__x5\.value=([\d.]+);', response_text, re.DOTALL)
        if hum_match:
            data['Humidité'] = float(hum_match.group(1))
        else:
            data['Humidité'] = float('nan')
        
        temp_match = re.search(r'name="m/Temp/MET".*?__x5\.value=([\d.]+);', response_text, re.DOTALL)
        if temp_match:
            data['Temperature moyenne'] = float(temp_match.group(1))
        else:
            data['Temperature moyenne'] = float('nan')
        time_match = re.findall(r'__x4\.validFrom=(\d+);', response_text)

        if time_match:

    # Get the timestamp string
#            timestamp_str = time_match[1].group(1)  # "1779182757000"
    # Convert milliseconds string to integer seconds
            timestamp_ms = int(time_match[1])
            timestamp_s = timestamp_ms / 1000.0
    
    # Convert to a readable UTC datetime object
            dt_object = datetime.datetime.fromtimestamp(timestamp_s, tz=datetime.timezone.utc)
#            print(dt_object)  # Output: 2026-05-19 09:25:57+00:00
            data['ServerTime'] = dt_object
        else:
            print("no time")
            data['ServerTime'] = float('nan')
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    
    for key in ['Pression', 'Humidité', 'Temperature moyenne']:
        if key in data and isinstance(data[key], float) and not (data[key] != data[key]):  
            data[key] = round(data[key], 2)
    return data

