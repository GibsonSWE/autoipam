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

        if response.json()['success'] is not True:
            if response.json()['message'] == 'No subnets found':
                return None

    except ConnectionError as e:
        raise e    
    except TimeoutError as e:
        raise e
    #except Exception as e:
    #    pass
    else:
        subnet = {
            'network_address': response.json()['data'][0]['subnet'],
            'cidr': response.json()['data'][0]['mask'],
            'id': response.json()['data'][0]['id']
        }
        return subnet


def get_subnet_id(network_address):
    """Requests a subnet id for a given network address"""
    print(f'Searching subnet-id for {network_address}')
    headers = {'token': c.IPAM_API_KEY, 'Content-Type': 'application/json'}

    try:
        response = requests.get(
            c.IPAM_URL+c.IPAM_GET_SUBNET+network_address+'/',
            headers=headers, 
            verify=True
        )
        if response.json()['success'] is not True:
            if response.json()['message'] == 'No subnets found':
                print(response.json()['message'])
                return None
    except ConnectionError as e:
        raise e    
    except TimeoutError as e:
        raise e
    #except Exception as e:
    #    pass
    else:
        subnet_id = response.json()['data'][0]['id']
        print(f"Found subnet with id: {subnet_id}")
        return subnet_id
    

def get_vrf_id(vrf_name):
    """Requests a list of available VRFs from the IPAM database and calculates matching vrfId for a specified VRF-name"""
    headers = {'token': c.IPAM_API_KEY, 'Content-Type': 'application/json'}

    try:
        response = requests.get(
            c.IPAM_URL+c.IPAM_GET_VRFS,
            headers=headers,
            verify=True
        )
    except ConnectionError as e:
        raise ConnectionError(e)    
    except TimeoutError as e:
        raise TimeoutError(e)
    except Exception as e:
        raise Exception(e)
    
    if response.status_code == 200:
        vrf_list = response.json()['data']

    for vrf in vrf_list:
        if vrf['name'] == vrf_name:
            return vrf['vrfId']
        
    return None
        

def get_master_subnet(possible_master_subnets):
    """Searches for existing subnets in the IPAM database that match the list of possible master subnets"""
    existing_possible_master_subnets = []
    for master_subnet in possible_master_subnets:
        subnet_match = get_subnet(master_subnet)
        if subnet_match is not None:
            existing_possible_master_subnets.append(f"{subnet_match['network_address']}/{subnet_match['cidr']}") 

    # Sorts the existing master subnets by prefix length in descending order
    sorted_possible_master_subnets = sorted(existing_possible_master_subnets, key=lambda x: ipaddress.ip_network(x).prefixlen, reverse=True)
    
    print(f'Matching master subnets found:')
    for subnet in sorted_possible_master_subnets:
        print(subnet)
    print()

    if len(sorted_possible_master_subnets) > 0:
        return sorted_possible_master_subnets[0]
    else:
        return None


def create_subnet(network_address, subnet_mask, cidr, subnet_name, subnet_description, vrf_id, section_id, master_subnet_id=None):
    """Creates a new subnet object in the IPAM-database"""
    print(f'Creating entry for subnet {network_address}/{cidr}')
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
    except ConnectionError as e:
        raise ConnectionError(e)    
    except TimeoutError as e:
        raise TimeoutError(e)
    except Exception as e:
        raise Exception(e)
    else:
        data = {}
        if response.status_code == 201:
            data['id'] = response.json()['id']
            print(f"{response.json()['message']} with id {response.json()['id']}")
            return data
        elif response.status_code == 409:
            data['id'] = None
            data['subnet'] = network_address+'/'+cidr,
            data['error'] = response.json()['message']
            return data
        else:
            print(response.content)
            exit()
    

def get_address(network_address):
    """Requests data for a given network address"""
    headers = {'token': c.IPAM_API_KEY, 'Content-Type': 'application/json'}
    print('Requesting interface data...')

    try:
        response = requests.get(
            c.IPAM_URL+c.IPAM_SEARCH_ADDRESS+network_address+'/',
            headers=headers, 
            verify=True,
        )

    except ConnectionError as e:
        raise ConnectionError(e)    
    except TimeoutError as e:
        raise TimeoutError(e)
    #except Exception as e:
    #   pass
    else:
        if response.json()['success'] is True:
            return response.json()
        elif response.json()['message'] == 'Address not found':
            return False
    

def create_address(interface, device, subnet_id):
    """Creates a new address object in the IPAM-database"""
    print(f"Creating entry for address: {interface['ipv4Address']}")
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
    except ConnectionError as e:
        raise e    
    except TimeoutError as e:
        raise e
    #except Exception as e:
    #   pass
    else:
        if response.status_code == 201:
            print(f"{response.json()['message']} with id: {response.json()['id']}\n")
            return response.json()['id']
        else:
            print('Failed:')
            print(response.content)
            print('Parameters:')
            print(params)
            print(f'subnetId: {subnet_id}')
            exit() 


def update_address(updated_address):
    """Updates an existing address object in the IPAM-database"""
    print(f"Updating address entry {updated_address['id']}...")
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
    except ConnectionError as e:
        raise e    
    except TimeoutError as e:
        raise e
    #except Exception as e:
    #    pass
    else:
        if response.json()['message'] == 'Address updated':
            print(f"{response.json()['message']}\n")
            return
        else:
            print("Update failed:")
            print(response.content)
            exit()


def main():
    pass


if __name__ == "__main__":
    print()
    main()
    print()
