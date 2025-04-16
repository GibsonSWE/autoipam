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
        self.token = 1234
        return


    ## GET DEVICE LIST ACCORDING TO PARAMETERS
    def get_device_list(self, family:str, offset=0):
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
            #response.raise_for_status()

        with open('dnac_devices.json', 'r') as f:
            dnac_devices = json.load(f)
        return dnac_devices['response']


    def get_interfaces(self, device:dict):
        """Get interface information per device"""
        response = None
        print(f'Requesting interface data for {device["hostname"]}')
        #response = requests.get(
        #    self.base_url + c.DNAC_INTERFACES + device['id'],
        #    headers=self.headers(),
        #    verify=False
        #)
        #return response.json()['response']
        #response.raise_for_status()
        with open('dnac_interfaces.json', 'r') as f:
            dnac_interfaces = json.load(f)
        
        for entry in dnac_interfaces:
            if entry.get('id') == device['id']:
                return entry['response']

        raise ValueError(f'No interface data found for {device["hostname"]} with ID {device["id"]}')


    def check_for_ipv4address(self, interfaces:list):
        """Checks if an interface has an ipv4 address assigned and returns a list of those interfaces"""
        interfaces_with_ipv4address=[]    
        for interface in interfaces:
            if interface['ipv4Address'] is not None:
                interfaces_with_ipv4address.append(interface)
        return interfaces_with_ipv4address


    def get_from_dnac(self):
        """Returns list from DNA-center with interface data per device"""
        try:
            self.get_token()
        except Exception as e:
            raise e

        retrieved_device_list = []
        device_data = []
        
        request_offset = 0
        print('Requesting device data from DNA-Center. Please wait...\n')
        while True:
            response = self.get_device_list('Routers', request_offset)

            retrieved_device_list += response

            if len(response) == 100:
                request_offset+=100
                continue
            break

        request_offset = 0
        while True:
            response = self.get_device_list('Switches and Hubs', request_offset)

            retrieved_device_list += response     
            
            if len(response) == 100:
                request_offset+=100
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
            
            retrieved_interfaces = self.get_interfaces(device)
            
            device_interfaces = []
            for interface in retrieved_interfaces:
                if interface['ipv4Address'] is not None:
                    if utils.check_ignored_address(interface['ipv4Address']):
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

