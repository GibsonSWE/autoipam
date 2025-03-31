from src import constants as c

import requests
import ipaddress


#---------- Used for dev/debugging ----------

#with open('../debug_dnac_device.json', 'r') as f:
#    debug_device = json.load(f)
#
#with open('../debug_interface.json') as f:
#    debug_interface = json.load(f)

#---------- Used for dev/debugging ----------


def get_custom_fields():
    """Retrieves available custom fields"""
    headers = {'token': c.IPAM_API_KEY, 'Content-Type': 'application/json'}
    response = requests.get(
        c.IPAM_URL+c.IPAM_GET_CUSTOM_FIELDS,
        headers=headers, 
        verify=True
    )
    return response


def get_subnet(network_address):
    """Requests subnet information for a given network address"""
    headers = {'token': c.IPAM_API_KEY, 'Content-Type': 'application/json'}

    try:
        response = requests.get(
            c.IPAM_URL+c.IPAM_GET_SUBNET+network_address+'/',
            headers=headers, 
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

    except requests.ConnectionError as e:
        raise ConnectionError(f"Connection error occurred: {e}")
    except requests.Timeout as e:
        raise TimeoutError(f"Request timed out: {e}")
    except ValueError as e:
        raise ValueError(f"Value error: {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")
    else:
        subnet = {
            'network_address': response.json()['data'][0]['subnet'],
            'cidr': response.json()['data'][0]['mask'],
            'id': response.json()['data'][0]['id']
        }
        return subnet


def get_subnet_id(network_address):
    """Requests a subnet ID for a given network address"""
    print(f'Searching subnet ID for {network_address}')
    headers = {'token': c.IPAM_API_KEY, 'Content-Type': 'application/json'}

    try:
        response = requests.get(
            c.IPAM_URL+c.IPAM_GET_SUBNET+network_address+'/',
            headers=headers, 
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

    except requests.ConnectionError as e:
        raise ConnectionError(f"Connection error occurred: {e}")
    except requests.Timeout as e:
        raise TimeoutError(f"Request timed out: {e}")
    except requests.HTTPError as e:
        raise ValueError(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except ValueError as e:
        raise ValueError(f"Value error: {e}")
    except KeyError as e:
        raise KeyError(f"Unexpected response structure: Missing key {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")
    

def get_vrf_id(vrf_name):
    """Requests a list of available VRFs from the IPAM database and calculates matching vrfId for a specified VRF-name"""
    headers = {'token': c.IPAM_API_KEY, 'Content-Type': 'application/json'}

    try:
        response = requests.get(
            c.IPAM_URL+c.IPAM_GET_VRFS,
            headers=headers,
            verify=True
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
    except requests.ConnectionError as e:
        raise ConnectionError(f"Connection error occurred: {e}")
    except requests.Timeout as e:
        raise TimeoutError(f"Request timed out: {e}")
    except requests.HTTPError as e:
        raise ValueError(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")

    try:
        response_data = response.json()
        if not response_data.get('success', False):
            raise ValueError(f"API error: {response_data.get('message')}")
        vrf_list = response_data.get('data', [])
    except (ValueError, KeyError) as e:
        raise ValueError(f"Error parsing response: {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred while processing the response: {e}")

    for vrf in vrf_list:
        if vrf.get('name') == vrf_name:
            return vrf.get('vrfId')

    print(f"VRF with name '{vrf_name}' not found")
    return None
        

def get_master_subnet(possible_master_subnets):
    """Searches for existing subnets in the IPAM database that match the list of possible master subnets"""
    existing_possible_master_subnets = []
    for master_subnet in possible_master_subnets:
        try:
            subnet_match = get_subnet(master_subnet)
            if subnet_match is not None:
                existing_possible_master_subnets.append(f"{subnet_match['network_address']}/{subnet_match['cidr']}")
        except ValueError as e:
            if "No subnets found" in str(e):
                continue
            else:
                print(f"Value error while processing subnet {master_subnet}: {e}")
        except ConnectionError as e:
            print(f"Connection error while processing subnet {master_subnet}: {e}")
        except TimeoutError as e:
            print(f"Timeout error while processing subnet {master_subnet}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while processing subnet {master_subnet}: {e}")

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


def create_subnet(network_address, subnet_mask, cidr, subnet_name, subnet_description, vrf_id, section_id, master_subnet_id=None):
    """Creates a new subnet object in the IPAM-database"""
    print(f'Creating object for subnet {network_address}/{cidr}')
    headers = {'token': c.IPAM_API_KEY, 'Content-Type': 'application/json'}

    params = {
        'subnet': network_address,
        'mask': cidr,
        'sectionId': section_id,
        'description': subnet_description,
        'vrfId': vrf_id
    }
    if master_subnet_id is not None:
        params['masterSubnetId'] = master_subnet_id

    if subnet_description == '' or subnet_description is None:
        params['description'] = 'Created by AutoIpam'

    if subnet_name != '' and subnet_name is not None:
        params['custom_Subnet_Name'] = subnet_name

    try:
        response = requests.post(
            c.IPAM_URL+c.IPAM_CREATE_SUBNET,
            headers=headers, 
            verify=True,
            params=params
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
    except requests.ConnectionError as e:
        raise ConnectionError(f"Connection error occurred: {e}")
    except requests.Timeout as e:
        raise TimeoutError(f"Request timed out: {e}")
    except requests.HTTPError as e:
        raise ValueError(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")
    else:
        try:
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
            else:
                raise ValueError(f"Unexpected response: {response.status_code} - {response.content}")
        except (ValueError, KeyError) as e:
            raise ValueError(f"Error parsing response: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred while processing the response: {e}")
    

def get_address(network_address):
    """Requests data for a given network address"""
    headers = {'token': c.IPAM_API_KEY, 'Content-Type': 'application/json'}
    print(f'Requesting data for address {network_address} from {c.IPAM_URL}')

    try:
        response = requests.get(
            c.IPAM_URL+c.IPAM_SEARCH_ADDRESS+network_address+'/',
            headers=headers, 
            verify=True,
        )
        response_data = response.json()
        if response_data.get('success') is True:
            return response_data
        elif response.status_code == 404 and response_data.get('message') == 'Address not found':
            return False
        else:
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

    except requests.ConnectionError as e:
        raise ConnectionError(f"Connection error occurred: {e}")
    except requests.Timeout as e:
        raise TimeoutError(f"Request timed out: {e}")
    except requests.HTTPError as e:
        raise ValueError(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")

    

def create_address(interface, device, subnet_id):
    """Creates a new address object in the IPAM-database"""
    print(f"Creating object for address {interface['ipv4Address']}")
    headers = {'token': c.IPAM_API_KEY, 'Content-Type': 'application/json'}
    params = {
        'subnetId': subnet_id,
        'ip': interface['ipv4Address'],
        'description': interface['description'],
        'hostname': device['hostname'],
        'is_gateway': interface['is-gateway'],
        'owner': device['owner'],
        'note': 'Created by AutoIpam',
        'mac': interface['mac'],
        'custom_Device_Serial': device['serial']
    }

    try:
        response = requests.post(
            c.IPAM_URL+c.IPAM_ADDRESSES,
            headers=headers, 
            verify=True,
            params=params
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
    except requests.ConnectionError as e:
        raise ConnectionError(f"Connection error occurred: {e}")
    except requests.Timeout as e:
        raise TimeoutError(f"Request timed out: {e}")
    except requests.HTTPError as e:
        error_message = f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        print(error_message)
        raise ValueError(error_message)
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")
    else:
        try:
            response_data = response.json()
            if response.status_code == 201:
                print(f"{response_data['message']} with ID: {response_data['id']}\n")
                return response_data['id']
            else:
                raise ValueError(f"Unexpected response: {response.status_code} - {response.content}")
        except (ValueError, KeyError) as e:
            raise ValueError(f"Error parsing response: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred while processing the response: {e}")


def update_address(updated_address):
    """Updates an existing address object in the IPAM-database"""
    print(f"Updating address object ID: {updated_address['id']}...")
    headers = {'token': c.IPAM_API_KEY, 'Content-Type': 'application/json'}
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

    try:
        response = requests.patch(
            c.IPAM_URL+c.IPAM_ADDRESSES+str(updated_address['id'])+'/',
            headers=headers, 
            verify=True,
            params=params
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
    except requests.ConnectionError as e:
        raise ConnectionError(f"Connection error occurred: {e}")
    except requests.Timeout as e:
        raise TimeoutError(f"Request timed out: {e}")
    except requests.HTTPError as e:
        error_message = f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        print(error_message)
        raise ValueError(error_message)
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")
    else:
        try:
            response_data = response.json()
            if response_data.get('message') == 'Address updated':
                print(f"Address {updated_address['ip']} updated successfully.")
                return
            else:
                raise ValueError(f"Update failed: {response_data.get('message', 'Unknown error')}")
        except (ValueError, KeyError) as e:
            raise ValueError(f"Error parsing response: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred while processing the response: {e}")


def main():
    pass


if __name__ == "__main__":
    print()
    main()
    print()
