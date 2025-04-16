from . import constants as c
from . import utils

import requests
import json

##  DISABLE SSL WARNINGS
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


class CheckpointManager:
    """Class to manage Checkpoint API requests"""
    def __init__(self):
        self.base_url = c.CHECKPOINT_URL
        self.auth_url = c.CHECKPOINT_AUTH
        self.api_key = c.CHECKPOINT_API_KEY

        self.sid = None
        self.device_list = None
        self.device_data = None

    def headers(self):
        """Returns the headers for Checkpoint API requests"""
        return {
            'Content-Type': "application/json", 
            'X-chkp-sid': self.sid
        }

    def get_sid(self):
        """Requests a session ID"""
        headers = {'Content-Type': "application/json"}
        payload = json.dumps({"api-key": self.api_key})

        response = requests.post(
            self.base_url+self.auth_url, 
            headers=headers, 
            verify=False, 
            data=payload
        )
        
        if response.status_code != 200:
            print(f"{response.json()['code']} {response.json()['message']}")
            raise f"{response.json()['code']} {response.json()['message']}"

        response.raise_for_status()
        sid = response.json()['sid']
        return sid


    def get_device_list(self, sid):
        """Requests a list of devices"""

        payload = json.dumps({"limit": 500})

        response = requests.post(
            self.base_url+c.CHECKPOINT_SHOW_GATEWAYS_AND_SERVERS, 
            headers=self.headers(), 
            verify=False, 
            data=payload
        )
        response.raise_for_status()
        return response.json()['objects']
        

    def get_device_data(self, sid, uid):
        """Requests data for a given device"""

        payload = json.dumps({"uid": uid,
                "details-level": "full"})

        response = requests.post(
            self.base_url+c.CHECKPOINT_SHOW_OBJECT,  
            headers=self.headers(), 
            verify=False, 
            data=payload
        )
        response.raise_for_status()
        return response.json()['object']

    def get_from_checkpoint_all(self):
        """Returns list of devices from Check Point, where each device includes a list of interface data"""
        print('Requesting data from Checkpoint...')
        try:
            sid = self.get_sid()
        except Exception as e:
            raise e

        try:
            response = self.get_device_list(sid)
        except Exception as e:
            raise e

        devices = []

        for retrieved_device in response:
            selected_device_data = self.select_checkpoint_data(sid, retrieved_device)
            if selected_device_data is False:
                continue
            else:
                devices.append(selected_device_data)

        return devices


    def get_from_checkpoint_single(self, device:dict):
        """Returns interface data for a specific device"""
        print(f"\nRequesting data for {device['name']}")
        try:
            sid = self.get_sid()
        except Exception as e:
            raise e

        devices = []

        selected_device_data = self.select_checkpoint_data(sid, device)
        if selected_device_data is False:
            return
        else:
            devices.append(selected_device_data)
            return devices        


    def select_checkpoint_data(self, sid, device:dict):
        """Selects data and converts it to a standardized convention"""
        device_interfaces = []
        try:
            retrieved_device_data = self.get_device_data(sid, device['uid'])
        except Exception as e:
            raise e
        
        if retrieved_device_data['type'] == 'simple-cluster':                                 # Simple cluster is also called "CpmiGatewayCluster" in some API-endpoints
            for interface in retrieved_device_data['interfaces']['objects']:
                if interface['ipv4-address'] != '':
                    if utils.check_ip_in_ignored(interface['ipv4-address']):
                        continue
                    else:
                        try:
                            interface_data = {
                                'interface-name': interface['name'],
                                'description': interface['comments'],
                                'ipv4Address': interface['ipv4-address'],
                                'ipv4Mask': interface['ipv4-network-mask'],
                                'cidr': interface['ipv4-mask-length'],
                                'subnet-name': interface['comments'],
                                'subnet-description': '',
                                'is-gateway': 1,
                                'mac': None,
                                'vlan-id': None
                            }

                            # Set address as gateway if the address is same as the cluster management address
                            #if interface['ipv4-address'] == retrieved_device_data['ipv4-address']:
                            #    interface_data['is-gateway'] == 1

                            if retrieved_device_data['comments'] == '':
                                interface_data['description'] = None

                            device_interfaces.append(interface_data)

                        except KeyError as e:
                            print('KeyError in step 1:')
                            print(e)
                            print(retrieved_device_data)
                            return
                    
        elif retrieved_device_data['type'] == 'checkpoint-host':
            for interface in retrieved_device_data['interfaces']:
                if utils.check_ip_in_ignored(interface['subnet4']):
                    continue
                else:
                    try:
                        interface_data = {
                            'interface-name': interface['name'],
                            'description': retrieved_device_data['comments'],
                            'ipv4Address': interface['subnet4'],
                            'ipv4Mask': interface['subnet-mask'],
                            'cidr': interface['mask-length4'],
                            'subnet-name': '',
                            'subnet-description': '',
                            'is-gateway': 0,
                            'mac': None,
                            'vlan-id': None
                        }

                        if retrieved_device_data['comments'] == '':
                            interface_data['description'] = None

                        device_interfaces.append(interface_data)

                    except KeyError as e:
                        print('KeyError in step 1:')
                        print(e)
                        print(retrieved_device_data)
                        return
                    
        elif retrieved_device_data['type'] == 'cluster-member':
            for interface in retrieved_device_data['interfaces']:
                if utils.check_ip_in_ignored(interface['ipv4-address']):
                    continue
                else:
                    try:
                        interface_data = {
                            'interface-name': interface['name'],
                            'description': retrieved_device_data['comments'],
                            'ipv4Address': interface['ipv4-address'],
                            'ipv4Mask': interface['ipv4-network-mask'],
                            'cidr': interface['ipv4-mask-length'],
                            'subnet-name': '',
                            'subnet-description': '',
                            'is-gateway': 0,
                            'mac': None,
                            'vlan-id': None
                        }

                        if retrieved_device_data['comments'] == '':
                            interface_data['description'] = None

                        device_interfaces.append(interface_data)

                    except KeyError as e:
                        print('KeyError in step 1:')
                        print(e)
                        print(retrieved_device_data)
                        return
                
        elif retrieved_device_data['type'] == 'simple-gateway':
            for interface in retrieved_device_data['interfaces']:
                if interface['ipv4-address'] != '':
                    if utils.check_ip_in_ignored(interface['ipv4-address']):
                        continue
                    else:
                        try:
                            interface_data = {
                                'interface-name': interface['name'],
                                'description': retrieved_device_data['comments'],
                                'ipv4Address': interface['ipv4-address'],
                                'ipv4Mask': interface['ipv4-network-mask'],
                                'cidr': interface['ipv4-mask-length'],
                                'subnet-name': '',
                                'subnet-description': '',
                                'is-gateway': 0,
                                'mac': None,
                                'vlan-id': None
                            }

                            if retrieved_device_data['comments'] == '':
                                interface_data['description'] = None

                            device_interfaces.append(interface_data)

                        except KeyError as e:
                            print('KeyError in step 1:')
                            print(e)
                            print(retrieved_device_data)
                            return
                
        elif retrieved_device_data['type'] == 'EthernetInterface':
            if retrieved_device_data['ipv4-address'] != '':
                if utils.check_ip_in_ignored(retrieved_device_data['ipv4-address']):
                    return
                else:
                    try:
                        interface_data = {
                            'interface-name': retrieved_device_data['name'],
                            'description': retrieved_device_data['comments'],
                            'ipv4Address': retrieved_device_data['ipv4-address'],
                            'ipv4Mask': retrieved_device_data['ipv4SubnetMask'], 
                            'cidr': retrieved_device_data['interfaces'][0]['mask-length4'],
                            'subnet-name': '',
                            'subnet-description': '',
                            'is-gateway': 0,
                            'mac': None,
                            'vlan-id': None                           
                        }

                        if retrieved_device_data['comments'] == '':
                            interface_data['description'] = None

                        device_interfaces.append(interface_data)

                    except KeyError as e:
                        print('KeyError in step 3:')
                        print(e)
                        print(retrieved_device_data)
                        return                
        
        else:
            print(f'Unknown device type: {retrieved_device_data["type"]}')
            print(retrieved_device_data)
                    

        selected_device_data = {
            'hostname': device['name'],
            'type': device['type'],
            'organisation': '',
            'owner': utils.calc_owner(device['name']),
            'serial': None,
            'interfaces': device_interfaces
        }

        if device['name'] == '':
            selected_device_data['hostname'] = None

        return selected_device_data


    def source(self):
        """ """
        try:
            sid = self.get_sid()
        except Exception as e:
            raise e

        print('Requesting device list...')
        device_list = self.get_device_list(sid)
        devices = []
        device_range = []

        print(f'\nID:   Hostname:                      Device type:')
        for id, device in enumerate(device_list):
            device['presented-id'] = id
            device_range.append(id)
            print(f'{device["presented-id"]:<5} {device["name"]:<30} {device["type"]}')

        print()
        while True:
            device_select_prompt = input("Select device: [ID/all] ").lower().strip()
            if device_select_prompt == 'exit':
                return None
            elif device_select_prompt == 'all':   
                devices = self.get_from_checkpoint_all()
                return devices
            elif device_select_prompt.isnumeric():
                device_select_prompt = int(device_select_prompt)
                if device_select_prompt not in device_range:
                    print('Out of range')
                    continue
                for device in device_list:
                    if device.get('presented-id') == device_select_prompt:

                        devices = self(device)
                return devices
            else:
                continue

