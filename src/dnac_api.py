from src import constants as c

import requests
from requests.auth import HTTPBasicAuth

##  DISABLE SSL WARNINGS
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


def get_token():
    """Retrieves session token from DNA-center"""
    print('Requesting session token...')
    try:
        response = requests.post(
            c.DNAC_URL+c.DNAC_AUTH,
            auth=HTTPBasicAuth(c.DNAC_USERNAME, c.DNAC_API_KEY),
            verify=False
        )
    except ConnectionError as e:
        raise e    
    except TimeoutError as e:
        raise e
    except Exception as e:
        print(response.content)
        raise SystemExit(e)
        
    token = response.json()["Token"]
    return token


## GET DEVICE LIST ACCORDING TO PARAMETERS
def get_device_list(token, family, offset=0):
    """Get device list according to provided device family.\n
    Returns a maximum of 100 devices per request.\n
    Use offset to retrieve a larger number of devices."""
    headers = {'X-Auth-Token': token, 'Content-Type': 'application/json'}

    params = {
        'limit': 100,       #Max 100, set this to a lower number for faster testing
        'family': family
    }

    if offset > 0:
        params['offset'] = offset

    try:
        response = requests.get(
            c.DNAC_URL+c.DNAC_NETWORK_DEVICE,
            headers = headers,
            verify=False,
            params=params
        )
    except ConnectionError as e:
        raise e    
    except TimeoutError as e:
        raise e
    except Exception as e:
        print(response.content)
        raise SystemExit(e)
    else:
        return response.json()['response']


def get_interfaces(token, device):
    """Get interface information per device"""
    response = None
    headers = {'X-Auth-Token': token, 'Content-Type': 'application/json'}
    print(f'Requesting interface data for {device["hostname"]}')
    try:
        response = requests.get(
            c.DNAC_URL+c.DNAC_INTERFACES+device['id'],
            headers=headers,
            verify=False
        )
    except ConnectionError as e:
        raise e    
    except TimeoutError as e:
        raise e
    except Exception as e:
        print(response.content)
        raise SystemExit(e)
    else:
        return response.json()['response']


def check_for_ipv4address(interfaces):
    """Checks if an interface has an ipv4 address assigned"""
    interfaces_with_ipv4address=[]    
    for interface in interfaces:
        if interface['ipv4Address'] is not None:
            interfaces_with_ipv4address.append(interface)
    return interfaces_with_ipv4address


def main():
    """Main function, should only be used for development, testing and debugging."""
    token = get_token()
    devices = []
    offset = 0

    while True:
        print(f'\nOffset: {offset}')
        response = get_device_list(token, offset)
        if len(response) == 100:
            offset+=100
            devices += response
            print(f'Total devices so far: {len(devices)}')
        else:
            break
    
    print(f'\nDone! Number of devices: {len(devices)}')


if __name__ == '__main__':
    main()
    print()
