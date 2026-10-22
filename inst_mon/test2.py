import requests
import re
import urllib3
import time # Import the time module

import requests
import re
import urllib3
import time # Import the time module

def get_weather_data(base_url):
    """
    Fetches weather data from the specified base URL and extracts key values.
    The timestamp in the request payload is dynamically generated based on the current time.

    Args:
        base_url (str): The base URL of the API (e.g., "https://10.31.16.151:8443").

    Returns:
        dict: A dictionary containing the extracted weather data, or None if an error occurs.
    """
    
    # Disable SSL warnings for self-signed certificates in your local network
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    api_endpoint = "/ims/rpc/com.microstepmis.agentspace.spaceview.SpaceView/getInstance"
    url = f"{base_url}{api_endpoint}"

    headers = {
        "Content-Type": "text/xml" # Based on the request payload being XML-like
    }

    # Generate the current timestamp in milliseconds
    # The timestamp in your example (1749634755781) looks like a Unix timestamp in milliseconds.
    # Python's time.time() returns seconds since epoch, so multiply by 1000 and convert to int.
    current_timestamp_ms = int(time.time() * 1000)

    params = {
        "action": "rpc",
        "jsAllowed": "true",
        "timestamp": str(current_timestamp_ms) # Convert to string for the URL parameter
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
        response = requests.post(url, headers=headers, params=params, data=payload, verify=False)
        response.raise_for_status()  # Raise an exception for HTTP errors

        response_text = response.text

        # 1. Extract WindSpeed (inst value)
        wind_speed_match = re.search(r'name="f/Speed/MET".*?__x6\.value=([\d.]+);', response_text, re.DOTALL)

        if wind_speed_match:
            data['Vent(F m/s)'] = float(wind_speed_match.group(1))

        # 2. Extract Prec1h (value)
        prec1h_match = re.search(r'name="f/Prec1h/MET".*?__x5\.value=([\d.]+);', response_text, re.DOTALL)

        if prec1h_match:
            data['Precipitation'] = float(prec1h_match.group(1))
        else:
            data['Precipitation'] = float('nan')
        # 3. Extract StPress (value)
        stpress_match = re.search(r'name="m/QFE/MET".*?__x5\.value=([\d.]+);', response_text, re.DOTALL)

        if stpress_match and float(stpress_match.group(1)) > 800:
            data['Pression'] = float(stpress_match.group(1))
        else:
            data['Pression'] = float('nan')


        # 4. Extract Hum (value)
        hum_match = re.search(r'name="m/Hum/MET".*?__x5\.value=([\d.]+);', response_text, re.DOTALL)
        if hum_match:
            data['Humidité'] = float(hum_match.group(1))
        else:
            data['Humidité'] = float('nan')
        # 5. Extract Temp (value)
        temp_match = re.search(r'name="m/Temp/MET".*?__x5\.value=([\d.]+);', response_text, re.DOTALL)
        if temp_match:
            data['Temperature moyenne'] = float(temp_match.group(1))
        else:
            data['Temperature moyenne'] = float('nan')
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    # Round the values to 2 decimal places if they are not NaN
    for key in ['Pression', 'Humidité', 'Temperature moyenne']:
        if key in data and isinstance(data[key], float) and not (data[key] != data[key]):  # check for NaN
            data[key] = round(data[key], 2)
    return data

# Example usage:


# Example usage:
base_address = "https://10.31.16.151:8443"
weather_data = get_weather_data(base_address)

if weather_data:
    print("Extracted Weather Data:")
    for key, value in weather_data.items():
        print(f"- {key}: {value}")
else:
    print("Failed to retrieve weather data.")
