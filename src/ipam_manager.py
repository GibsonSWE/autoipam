from src import constants as c
#from . import constants as c
import requests
import ipaddress


#---------- Used for dev/debugging ----------

#with open('../debug_dnac_device.json', 'r') as f:
#    debug_device = json.load(f)
#
#with open('../debug_interface.json') as f:
#    debug_interface = json.load(f)

#---------- Used for dev/debugging ----------


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
            self.base_url + c.IPAM_GET_CUSTOM_FIELDS,
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


    def get_subnet(self, network_address):
        """Requests subnet information for a given network address"""
        response = requests.get(
            self.base_url + c.IPAM_GET_SUBNET+network_address+'/',
            headers=self.headers(), 
            verify=True
        )

        if response.status_code != 200:
            raise ValueError(f"Unexpected response status: {response.status_code} - {response.content}")

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


    def get_subnet_id(self, network_address):
        """Requests a subnet ID for a given network address"""
        print(f'Searching subnet ID for {network_address}')

        response = requests.get(
            self.base_url + c.IPAM_GET_SUBNET + network_address + '/',
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
    

    def get_vrf_id(self, vrf_name):
        """Requests a list of available VRFs from the IPAM database and calculates matching vrfId for a specified VRF-name"""
        response = requests.get(
            self.base_url + c.IPAM_GET_VRFS,
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
        

    def get_master_subnet(self, possible_master_subnets):
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


    def create_subnet(self, network_address, subnet_mask, cidr, subnet_name, subnet_description, vrf_id, section_id, master_subnet_id=None):
        """Creates a new subnet object in the IPAM-database"""
        print(f'Creating object for subnet {network_address}/{cidr}')
        headers = {'token': c.IPAM_API_KEY, 'Content-Type': 'application/json'}

        params = {
            'subnet': network_address,
            'mask': cidr,
            'sectionId': section_id,
            'description': subnet_description or 'Created by AutoIpam',
            'vrfId': vrf_id
        }
        if master_subnet_id is not None:
            params['masterSubnetId'] = master_subnet_id

        if subnet_name:
            params['custom_Subnet_Name'] = subnet_name


            response = requests.post(
                c.IPAM_URL + c.IPAM_CREATE_SUBNET,
                headers=headers,
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
    

    def get_address(self, network_address):
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

    

    def create_address(self, interface, device, subnet_id):
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


    def update_address(self, updated_address):
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


def main(self):
    #subnet_info = get_subnet('10.0.0.10')
    #subnet_id = get_subnet_id('10.0.0.10')
    subnets = self.get_all_subnets()
    print(subnets.content[0])

if __name__ == "__main__":
    print()
    main()
    print()
