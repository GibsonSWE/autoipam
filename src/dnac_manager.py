from src import constants as c
from src import utils

import json
import requests
from requests.auth import HTTPBasicAuth

##  DISABLE SSL WARNINGS
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


class DNACManager:
    """Class to manage Cisco DNA-Center API calls"""
    def __init__(self):
        self.base_url = c.DNAC_URL
        self.auth_url = c.DNAC_AUTH
        self.token = None
        self.devices = []
        self.interfaces = []
        self.interfaces_with_ipv4address = []


    def headers(self):
        """Sets the header for the API requests"""
        headers = {
            'X-Auth-Token': self.token,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        return headers

    def get_token(self):
        """Retrieves session token from DNA-center"""
        print('\nRequesting session token...')
        #response = requests.post(
        #    self.base_url+self.auth_url,
        #    auth=HTTPBasicAuth(c.DNAC_USERNAME, c.DNAC_API_KEY),
        #    verify=False
        #)
        #response.rase_for_status()
            
        #token = response.json()["Token"]
        token = 1234
        return token


    ## GET DEVICE LIST ACCORDING TO PARAMETERS
    def get_device_list(self, token, family, offset=0):
        """Get device list according to provided device family.\n
        Returns a maximum of 100 devices per request.\n
        Use offset to retrieve a larger number of devices."""

        params = {
            'limit': 100,       #Max 100, set this to a lower number for faster testing
            'family': family
        }

        if offset > 0:
            params['offset'] = offset

            #response = requests.get(
            #    self.base_url + c.DNAC_NETWORK_DEVICE,
            #    headers = self.headers(),
            #    verify=False,
            #    params=params
            #)
            #return response.json()['response']

        with open('dnac_devices.json', 'r') as f:
            dnac_devices = json.load(f)
        return dnac_devices['response']


    def get_interfaces(self, token, device):
        """Get interface information per device"""
        response = None
        print(f'Requesting interface data for {device["hostname"]}')
        #response = requests.get(
        #    self.base_url + c.DNAC_INTERFACES + device['id'],
        #    headers=self.headers(),
        #    verify=False
        #)
        #return response.json()['response']
        
        with open('dnac_interfaces.json', 'r') as f:
            dnac_interfaces = json.load(f)
        
        for entry in dnac_interfaces:
            if entry.get('id') == device['id']:
                return entry['response']

        raise ValueError(f'No interface data found for {device["hostname"]} with ID {device["id"]}')


    def check_for_ipv4address(self, interfaces):
        """Checks if an interface has an ipv4 address assigned"""
        interfaces_with_ipv4address=[]    
        for interface in interfaces:
            if interface['ipv4Address'] is not None:
                interfaces_with_ipv4address.append(interface)
        return interfaces_with_ipv4address


    def get_from_dnac(self):
        """Returns list from DNA-center with interface data per device"""
        dnac_session = DNACManager()
        try:
            token = DNACManager.get_token(dnac_session)
        except Exception as e:
            raise e

        retrieved_device_list = []
        device_data = []
        
        offset = 0
        print('Requesting device data from DNA-Center. Please wait...\n')
        while True:
            try:
                response = DNACManager.get_device_list(dnac_session, token, 'Routers', offset)
            except Exception as e:
                raise e

            retrieved_device_list += response

            if len(response) == 100:
                offset+=100
                continue
            break

        offset = 0
        while True:
            try:
                response = DNACManager.get_device_list(dnac_session, token, 'Switches and Hubs', offset)
            except Exception as e:
                raise e

            retrieved_device_list += response     
            
            if len(response) == 100:
                offset+=100
                continue
            break
        

        for device in retrieved_device_list:
            selected_device_data = {
                'hostname': device['hostname'],
                'description': device['description'],
                'role': device['role'],
                "serial": device['serialNumber'],
                'owner': utils.calc_owner(device['hostname']),
                'organisation': ''
            }
            try:
                retrieved_interfaces = DNACManager.get_interfaces(dnac_session, token, device)
            except Exception as e:
                raise e
            
            device_interfaces = []
            for interface in retrieved_interfaces:
                if interface['ipv4Address'] is not None:
                    if utils.check_ip_in_ignored(interface['ipv4Address']):
                        continue
                    elif interface['adminStatus'] == 'DOWN':
                        print(f'Interface {interface["portName"]} administratively down. Skipping...')
                        continue
                    selected_interface_data = { 
                        'description': interface['portName'],
                        'ipv4Address': interface['ipv4Address'] ,
                        'ipv4Mask': interface['ipv4Mask'],
                        'mac': interface['macAddress'],
                        'vlan-id': interface['vlanId'],
                        'subnet-name': '',
                        'subnet-description': '',
                        'is-gateway': None
                    }
                    device_interfaces.append(selected_interface_data)
            selected_device_data['interfaces'] = device_interfaces
            device_data.append(selected_device_data)

        return device_data

