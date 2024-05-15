from src import constants as c

import requests
import json

##  DISABLE SSL WARNINGS
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

 
def get_sid():
    """Requests a session ID"""
    headers = {'Content-Type': "application/json"}
    payload = json.dumps({"api-key": c.CHECKPOINT_API_KEY})

    try:
        response = requests.post(c.CHECKPOINT_URL+c.CHECKPOINT_AUTH, headers=headers, verify=False, data=payload)
        if response.status_code != 200:
            print(f"{response.json()['code']} {response.json()['message']}")
            raise f"{response.json()['code']} {response.json()['message']}"
    except ConnectionError as e:
        raise ConnectionError(e)    
    except TimeoutError as e:
        raise ConnectionError(e)
    except Exception as e:
        raise Exception(e)
    else:
        sid = response.json()['sid']
        return sid


def get_device_list(sid):
    """Requests a list of devices"""
    headers = {'Content-Type': "application/json", 'X-chkp-sid': sid}
    payload = json.dumps({"limit": 500})
    try:
        response = requests.post(c.CHECKPOINT_URL+c.CHECKPOINT_SHOW_GATEWAYS_AND_SERVERS, headers=headers, verify=False, data=payload)
    except ConnectionError as e:
        raise e    
    except TimeoutError as e:
        raise e
    #except Exception as e:
    #    pass
    else:
        return response.json()['objects']
    

def get_device_data(sid, uid):
    """Requests data for a given device"""
    headers = {'Content-Type': "application/json", 'X-chkp-sid': sid}
    payload = json.dumps({"uid": uid,
               "details-level": "full"})
    try:
        response = requests.post(c.CHECKPOINT_URL+c.CHECKPOINT_SHOW_OBJECT,  headers=headers, verify=False, data=payload)
    except ConnectionError as e:
        raise e    
    except TimeoutError as e:
        raise e
    #except Exception as e:
    #    pass
    else:
        return response.json()['object']


def main():
    sid=get_sid()
    if sid is not False:
        device_list = get_device_list(sid)
        return device_list


if __name__ == "__main__":
    device_list = main()
    print(device_list)
