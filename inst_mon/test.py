import requests
import re
import urllib3
import time 

def get_batterie_status(base_url):
    
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    headers = {
        "Content-Type": "text/xml" 
    }
   
    current_timestamp_ms = int(time.time() * 1000)

    params = {
        "action": "rpc",
        "jsAllowed": "true",
        "timestamp": str(current_timestamp_ms) 
    }

#################### GET UID ###################################
    UID_api_endpoint = "/ims/rpc/com.microstepmis.agentspace.LocalSpace/remoteAttachTrigger"
    UID_url= f"{base_url}{UID_api_endpoint}"
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
        response = requests.post(UID_url, headers=headers, params=params, data=UID_payload, verify=False)
        response.raise_for_status()  

        response_text = response.text


        UID_match = re.search(r'__x\.result="([a-f0-9\-]+)"', response_text)
        UID=UID_match.group(1)

    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
#################### GET STATUS ###################################

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
        response = requests.post(url, headers=headers, params=params, data=payload, verify=False)
        response.raise_for_status()  

        response_text = response.text

        Batterie_volt_match = re.search(r'__x5\.value="([\d.]+ V)"', response_text)
        if Batterie_volt_match:
        	Batterie_volt_value = Batterie_volt_match.group(1)
        	Batterie_volt_value = float(Batterie_volt_value.split()[0])
        else:
            Batterie_volt_value = float('nan')	

    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    

    return Batterie_volt_value


print(get_batterie_status("https://10.31.16.151:8443"))
