import requests
import re
import urllib3
import time

class BatteryMonitor:
    def __init__(self):
        self.cached_uid = None

    def get_uid(self, base_url, headers, params):
        #if self.cached_uid:
        #    return self.cached_uid

        UID_api_endpoint = "/ims/rpc/com.microstepmis.agentspace.LocalSpace/remoteAttachTrigger"
        UID_url = f"{base_url}{UID_api_endpoint}"
        UID_payload = """
        <x xclass="com.microstepmis.xplatform.rpc.RPCRequest" className="com.microstepmis.agentspace.LocalSpace" methodName="remoteAttachTrigger">
            <arguments>
                <x xclass="null"/>
                <x xclass="null"/>
                <x xclass="String[]">
                    <x>monitoring/block/bite/BV/DCP_AWS</x>
                </x>
                <x xclass="Integer">0</x>
                <x xclass="Boolean">true</x>
            </arguments>
        </x>
        """
        try:
            response = requests.post(UID_url, headers=headers, params=params, data=UID_payload, verify=False, timeout=10)
            response.raise_for_status()
            UID_match = re.search(r'__x\.result="([a-f0-9\-]+)"', response.text)
            if UID_match:
                self.cached_uid = UID_match.group(1)
                return self.cached_uid
            else:
                print("UID not found in response")
                self.cached_uid = None
                return None
        except Exception as e:
            print(f"Error fetching UID: {e}")
            self.cached_uid = None
            return None

    def get_batterie_status(self, base_url):
        """
        Fetches the battery voltage from the station at base_url.
        Returns the voltage as a float, or float('nan') if not available.
        """
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        headers = {"Content-Type": "text/xml"}
        current_timestamp_ms = int(time.time() * 1000)
        params = {
            "action": "rpc",
            "jsAllowed": "true",
            "timestamp": str(current_timestamp_ms)
        }

        UID = self.get_uid(base_url, headers, params)
        if not UID:
            return float('nan')

        api_endpoint = "/ims/rpc/com.microstepmis.agentspace.LocalSpace/receiveTrigger"
        url = f"{base_url}{api_endpoint}"
        payload = f"""
        <x xclass="com.microstepmis.xplatform.rpc.RPCRequest" className="com.microstepmis.agentspace.LocalSpace" methodName="receiveTrigger">
            <arguments>
                <x xclass="null"/>
                <x xclass="String">{UID}</x>
                <x xclass="Long">5000</x>
                <x xclass="Integer">-1</x>
            </arguments>
        </x>
        """

        try:
            response = requests.post(url, headers=headers, params=params, data=payload, verify=False, timeout=10)
            response.raise_for_status()
            response_text = response.text
            Batterie_volt_match = re.search(r'__x5\.value="([\d.]+ V)"', response_text)
            if Batterie_volt_match:
                Batterie_volt_value = float(Batterie_volt_match.group(1).split()[0])
            else:
                Batterie_volt_value = float('nan')
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            # Invalidate UID if request fails (could be expired)
            self.cached_uid = None
            return float('nan')
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.cached_uid = None
            return float('nan')

        return Batterie_volt_value

# Usage example:
if __name__ == "__main__":
    monitor = BatteryMonitor()
    print(monitor.get_batterie_status("https://10.31.16.151:8443"))