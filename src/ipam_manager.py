from . import constants as c
from . import utils

import requests
import ipaddress


class IPAMManager:
    """Class for managing IPAM operations"""
    def __init__(self):
        self.base_url = c.IPAM_URL
        self.api_key = c.IPAM_API_KEY
        self.get_subnet_endpoint = c.IPAM_GET_SUBNET
        self.create_subnet_endpoint = c.IPAM_CREATE_SUBNET
        self.addresses_endpoint = c.IPAM_ADDRESSES
        self.search_address_endpoint = c.IPAM_SEARCH_ADDRESS
        self.get_vrfs_endpoint = c.IPAM_GET_VRFS
        self.get_custom_fields_endpoint = c.IPAM_GET_CUSTOM_FIELDS

    def headers(self):
        """Returns the headers for API requests"""
        return {
            'token': self.api_key,
            'Content-Type': 'application/json'
        }

    def get_custom_fields(self):
        """Retrieves available custom fields"""
        response = requests.get(
            self.base_url + self.get_custom_fields_endpoint,
            headers=self.headers(), 
            verify=True
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        return response

    def get_all_subnets(self):
        """Retrieves available custom fields"""
        response = requests.get(
            self.base_url + '/api/AutoIpam/subnets/',
            headers=self.headers(),
            verify=True
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        return response


    def get_subnet(self, network_address:str):
        """Requests subnet information for a given network address"""
        response = requests.get(
            self.base_url + self.get_subnet_endpoint+network_address+'/',
            headers=self.headers(), 
            verify=True
        )

        if response.status_code != 200:
            raise ValueError(f"Unexpected response status: {response.status_code} - {response.content}")
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        response_data = response.json()
        if not response_data.get('success', False):
            if response_data.get('message') == 'No subnets found':
                return None
            else:
                raise ValueError(f"API error: {response_data.get('message')}")

        subnet = {
            'network_address': response.json()['data'][0]['subnet'],
            'cidr': response.json()['data'][0]['mask'],
            'id': response.json()['data'][0]['id']
        }

        return subnet


    def get_subnet_id(self, network_address:str):
        """Requests a subnet ID for a given network address"""
        print(f'Searching subnet ID for {network_address}')

        response = requests.get(
            self.base_url + self.get_subnet_endpoint + network_address + '/',
            headers=self.headers(),
            verify=True
        )
        if response.status_code == 404:
            response_data = response.json()
            if response_data.get('message') == 'No subnets found':
                print(response_data['message'])
                return None
            else:
                # raise ValueError(f"Unexpected 404 response: {response_data.get('message')}")
                raise ValueError(f"Unexpected 404 response: {response_data}")
        else:
            response.raise_for_status()  # Raise an HTTPError for other bad responses (4xx and 5xx)

        response_data = response.json()
        subnet_id = response_data['data'][0]['id']
        print(f"Found subnet with ID: {subnet_id}")
        return subnet_id
    

    def get_vrf_id(self, vrf_name:str):
        """Requests a list of available VRFs from the IPAM database and calculates matching vrfId for a specified VRF-name"""
        response = requests.get(
            self.base_url + self.get_vrfs_endpoint,
            headers=self.headers(),
            verify=True
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        response_data = response.json()
        if not response_data.get('success', False):
            raise ValueError(f"API error: {response_data.get('message')}")
        vrf_list = response_data.get('data', [])

        for vrf in vrf_list:
            if vrf.get('name') == vrf_name:
                return vrf.get('vrfId')

        print(f"VRF with name '{vrf_name}' not found")
        return None
        

    def get_master_subnet(self, possible_master_subnets:list):
        """Searches for existing subnets in the IPAM database that match the list of possible master subnets"""
        existing_possible_master_subnets = []
        for master_subnet in possible_master_subnets:
            try:
                subnet_match = self.get_subnet(master_subnet)
                if subnet_match is not None:
                    existing_possible_master_subnets.append(f"{subnet_match['network_address']}/{subnet_match['cidr']}")
            except ValueError as e:
                if "No subnets found" in str(e):
                    continue
                else:
                    print(f"Value error while processing subnet {master_subnet}: {e}")

        # Sorts the existing master subnets by prefix length in descending order
        sorted_possible_master_subnets = sorted(existing_possible_master_subnets, key=lambda x: ipaddress.ip_network(x).prefixlen, reverse=True)
        
        print(f'Matching master subnets found:')

        if len(sorted_possible_master_subnets) > 0:
            for subnet in sorted_possible_master_subnets:
                print(subnet)
            print()        
            return sorted_possible_master_subnets[0]
        else:
            print('None')
            return None


    def create_subnet(self, network_address:str, cidr:str, subnet_name:str, subnet_description:str, vrf_id, section_id, master_subnet_id=None):
        """Creates a new subnet object in the IPAM-database"""
        print(f'Creating object for subnet {network_address}/{cidr}')


        params = {
            'subnet': network_address,
            'mask': cidr,
            'sectionId': section_id,
            'description': subnet_description or 'Created by AutoIpam',
            'vrfId': vrf_id
        }
        if master_subnet_id is not None:
            params['masterSubnetId'] = master_subnet_id

        if subnet_description == '' or subnet_description is None:
            params['description'] = 'Created by AutoIpam'

        if subnet_name != '' and subnet_name is not None:
            params['custom_Subnet_Name'] = subnet_name


        response = requests.post(
            self.base_url + c.IPAM_CREATE_SUBNET,
            headers=self.headers(),
            verify=True,
            params=params
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        response_data = response.json()

        if response.status_code == 201:
            print(f"{response_data['message']} with ID: {response_data['id']}")
            return {'id': response_data['id']}
        elif response.status_code == 409:
            print(f"Conflict: {response_data['message']}")
            return {
                'id': None,
                'subnet': f"{network_address}/{cidr}",
                'error': response_data['message']
            }
    

    def get_address(self, network_address:str):
        """Requests data for a given network address"""
        print(f'Requesting data for address {network_address} from {self.base_url}')

        response = requests.get(
            self.base_url + c.IPAM_SEARCH_ADDRESS + network_address + '/',
            headers=self.headers(),
            verify=True,
        )

        if response.status_code == 502:
            raise ValueError(f"Bad Gateway: Received 502 error from the server. \nResponse content: \n{response.text}")
        
        if 'application/json' not in response.headers.get('Content-Type', ''):
            raise ValueError(f"Unexpected response format: {response.headers.get('Content-Type')}. Response content: {response.text}")

        response_data = response.json()
        if response_data.get('success') is True:
            return response_data
        elif response.status_code == 404 and response_data.get('message') == 'Address not found':
            return False
        else:
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
    

    def create_address(self, interface:dict, device:dict, subnet_id):
        """Creates a new address object in the IPAM-database"""
        print(f"Creating object for address {interface['ipv4Address']}")
        params = {
            'subnetId': subnet_id,
            'ip': interface['ipv4Address'],
            'description': interface.get('description', 'No description provided'),
            'hostname': device.get('hostname', 'Unknown'),
            'is_gateway': interface.get('is-gateway', False),
            'owner': device.get('owner', 'Unknown'),
            'note': 'Created by AutoIpam',
            'mac': interface.get('mac', '00:00:00:00:00:00'),
            'custom_Device_Serial': device.get('serial', 'Unknown')
        }

        response = requests.post(
            self.base_url + c.IPAM_ADDRESSES,
            headers=self.headers(),
            verify=True,
            params=params
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        response_data = response.json()
        if response.status_code == 201:
            print(f"{response_data['message']} with ID: {response_data['id']}\n")
            return response_data['id']
        else:
            raise ValueError(f"Unexpected response: {response.status_code} - {response.content}")


    def update_address(self, updated_address:dict):
        """Updates an existing address object in the IPAM-database"""
        print(f"Updating address object ID: {updated_address['id']}...")
        params = {}

        if 'new-hostname' in updated_address.keys():
            params['hostname'] = updated_address['new-hostname']
        if 'new-description' in updated_address.keys():
            params['description'] = updated_address['new-description']
        if 'new-is_gateway' in updated_address.keys():
            params['is_gateway'] = updated_address['new-is_gateway']
        if 'new-owner' in updated_address.keys():
            params['owner'] = updated_address['new-owner']
        if 'new-mac' in updated_address.keys():
            params['mac'] = updated_address['new-mac']
        if 'new-device-serial' in updated_address.keys():
            params['custom_Device_Serial'] = updated_address['new-device-serial']


        response = requests.patch(
            self.base_url + c.IPAM_ADDRESSES + str(updated_address['id']) + '/',
            headers=self.headers(),
            verify=True,
            params=params
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        response_data = response.json()
        if response_data.get('message') == 'Address updated':
            print(f"Address {updated_address['ip']} updated successfully.")
            return
        else:
            raise ValueError(f"Update failed: {response_data.get('message', 'Unknown error')}")
    

    # This method should be rewritten and/or split into multiple methods or potentially classes like Device and Interface
    def update_ipam(self, devices:list):
        """Updates the IPAM database with the provided device and interface list"""
        updated_addresses = []
        updated_subnets = []
        conflicts = []
        for device in devices:
            for interface in device['interfaces']:
                address_response = self.get_address(interface['ipv4Address'])
                updated_address = {}
                updated_subnet = {}

                if address_response is not False:
                    print(f"IP-address {interface['ipv4Address']:10} already exists in the IPAM-database")

                    updated_address = utils.calc_addr_update_data(device, interface, address_response)

                    if updated_address:
                        updated_address['id'] = address_response['data'][0]['id']
                        updated_address['change-type'] = 'update'
                        updated_address['ip'] = interface['ipv4Address']

                        self.update_address(updated_address)
                        updated_addresses.append(updated_address)
                    else:
                        print(f"No changes needed for address object {interface['ipv4Address']}")

                else:
                    subnet = utils.calc_subnet(interface['ipv4Address'], interface['ipv4Mask'])
                    network_address = subnet['network_address']
                    network_address_full = subnet['network_address_full']
                    subnet_mask = subnet['subnet_mask']
                    cidr = subnet['cidr']
                    subnet_name = interface['subnet-name']
                    subnet_description = interface['subnet-description']
                    vrf_name = utils.calc_vrf(network_address_full)
                    vrf_id = self.get_vrf_id(vrf_name)

                    subnet_id = self.get_subnet_id(network_address_full)


                    if subnet_id is False:
                        return
                    elif subnet_id is None:
                        possible_master_subnets = utils.calc_master_subnets(network_address_full)
                        master_subnet = self.get_master_subnet(possible_master_subnets)
                        
                        if master_subnet is not None:
                            master_subnet_id = self.get_subnet_id(master_subnet)
                            response = self.create_subnet(network_address, cidr, subnet_name, subnet_description, vrf_id, c.SECTION_ID, master_subnet_id)
                            subnet_id = response['id']
                            if subnet_id is None:
                                print(f'Error creating {response["subnet"]}')
                                print(response['error'])
                                print('Skipping...')
                                conflicts.append(response)
                                continue

                        else:
                            print(f"Calculated existing master subnet for {network_address_full}: {master_subnet}")
                            
                            response = self.create_subnet(network_address, cidr, subnet_name, subnet_description, vrf_id, c.SECTION_ID)
                            try:
                                subnet_id = response['id']
                            except TypeError as e:
                                print(f"Type error: {e}")
                                print(f"Subnet ID: {subnet_id}")
                                print(f"Response: {response}")
                                exit()
                            if subnet_id is None:
                                print(f'Error creating {response["subnet"]}')
                                print(response['error'])
                                print('Skipping...')
                                conflicts.append(response)
                                continue 
                        
                        # Data for NEW subnet
                        updated_subnet = utils.compile_new_subnet_data(subnet_id, network_address, subnet_mask, cidr, subnet_name, subnet_description, vrf_name)
                        updated_subnet['change-type'] = 'create'
                        updated_subnets.append(updated_subnet)
                            
                        if subnet_id is False:
                            return
    
                    address_id = self.create_address(interface, device, subnet_id)

                    # Data for NEW address
                    updated_address = utils.compile_new_addr_data(device, interface, address_id)
                    updated_address['change-type'] = 'create'
                    updated_addresses.append(updated_address)

        if len(conflicts) > 0:
            utils.export_json(c.CONFLICTS_PATH+c.CONFLICT_FILE_NAME, conflicts)

        print('\nUpdate finished!')

        if len(updated_subnets) > 0 or len(updated_addresses) > 0:
            print(f'Created {len(updated_subnets)} new subnets')
            export_prompt = input('Export report? [Y/n] ').lower().strip()
            if export_prompt == 'y' or export_prompt == '':
                utils.export_update_report(updated_subnets, updated_addresses)
        else:
            print('No changes were made')


    def calculate_diff(self, devices:list):
        """Calculates the differences between the source and the IPAM database"""

        #Defines a new dictionary including four lists with pending new and updated subnets and addresses
        pending_changes = {
            'new-subnet-objects': [], 
            'new-address-objects': [],
            'updated-subnet-objects': [],
            'updated-address-objects': []
            }
        
        for device in devices:    
            for interface in device['interfaces']:
                try:
                    address_response = self.get_address(interface['ipv4Address'])
                except Exception as e:
                    raise e

                if address_response is False:
                    subnet = utils.calc_subnet(interface['ipv4Address'], interface['ipv4Mask'])
                    network_address = subnet['network_address']
                    network_address_full = subnet['network_address_full']
                    subnet_mask = subnet['subnet_mask']
                    cidr = subnet['cidr']
                    subnet_id = self.get_subnet_id(network_address_full)
                    subnet_name = interface['subnet-name']
                    subnet_description = ''
                    vrf_name = utils.calc_vrf(network_address_full)

                    if subnet_id is False:
                        return
                    elif subnet_id is None:
                        # Calculates all possible master subnets for the specified subnet
                        possible_master_subnets = utils.calc_master_subnets(network_address_full)

                        # Searches for matching master subnets in the IPAM-database
                        try:
                            master_subnet = self.get_master_subnet(possible_master_subnets)
                        except Exception as e:
                            raise e
                        
                        print(f"Calculated master subnet for {network_address_full}: {master_subnet}")
                        print()

                        new_subnet = utils.compile_new_subnet_data(subnet_id, network_address, subnet_mask, cidr, subnet_name, subnet_description, vrf_name)

                        if new_subnet['new-subnet-description'] == '' or new_subnet['new-subnet-description'] is None:
                            new_subnet['new-subnet-description'] = 'Created by AutoIpam'

                        if not pending_changes['new-subnet-objects']:
                            pending_changes['new-subnet-objects'].append(new_subnet)
                        else:
                            # Check if the new subnet address is already present in the list
                            if network_address not in [i['new-network-address'] for i in pending_changes['new-subnet-objects']]:
                                pending_changes['new-subnet-objects'].append(new_subnet)

                    new_address = utils.compile_new_addr_data(device, interface)

                    # Ensures "new-is_gateway" is properly translated for readability in terminal output
                    if new_address['new-is_gateway'] == 0:
                        new_address['new-is_gateway'] = False
                    elif new_address['new-is_gateway'] == 1:
                        new_address['new-is_gateway'] = True

                    # Checks if the list is empty, and adds the new address directly without checking for duplicates
                    if not pending_changes['new-address-objects']:
                        pending_changes['new-address-objects'].append(new_address)
                    else:
                        # Checks if the new address is already present in the list, to avoid duplicates
                        if interface['ipv4Address'] not in [i['ip'] for i in pending_changes['new-address-objects']]:
                            pending_changes['new-address-objects'].append(new_address)

                else:
                    print(f"IP-address {interface['ipv4Address']:10} already exists in the IPAM-database")
                    updated_address = utils.calc_addr_update_data(device, interface, address_response)

                    if updated_address:
                        updated_address['id'] = address_response['data'][0]['id']
                        updated_address['ip-address'] = interface['ipv4Address']
                        updated_address['change-type'] = 'update'
                        
                        # Ensures "new-is_gateway" is properly translated for readability in terminal output
                        if updated_address['new-is_gateway'] == 0:
                            updated_address['new-is_gateway'] = False
                        elif updated_address['new-is_gateway'] == 1:
                            updated_address['new-is_gateway'] = True

                        pending_changes['updated-address-objects'].append(updated_address)
                    else:
                        print(f"No changes needed for {interface['ipv4Address']}")

        return pending_changes   

