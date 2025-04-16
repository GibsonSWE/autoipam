from . import constants as c

import os
import json
import csv
import ipaddress
from datetime import datetime


def show_version():
    """Displays the current script version"""
    print(f"Version: {c.RELEASE['version']}")
    print(f"Released: {c.RELEASE['date']}")


def calc_org(hostname:str):
    """Calculates organization for device using hostname (Not yet implemented)"""
    pass


def calc_owner(hostname:str):
    """Calculates owner for device using hostname"""
    if hostname.find('SE-MUN-PAPER') != -1:
        return 'SCA Munksund När-IT'
    elif hostname.find('SE-OBB') != -1:
        return 'SCA Obbola När-IT'
    else:
        return 'SCA IT-infrastruktur network'
    

def calc_subnet(ip_address:str, subnet_mask:str):
    """Calculates subnet information from ip-address and subnet mask"""
    print(f"Calculating subnet for ip {ip_address} with mask {subnet_mask}")
    ip = ipaddress.IPv4Address(ip_address)
    subnet_mask = ipaddress.IPv4Address(subnet_mask)

    network_address_full = ipaddress.IPv4Network(f'{ip}/{subnet_mask}', strict=False)
    subnet = {
        'network_address_full': str(network_address_full),
        'network_address': str(network_address_full.network_address),
        'subnet_mask': str(network_address_full.netmask),
        'cidr': str(network_address_full.prefixlen)
    }
    return subnet


def calc_master_subnets(subnet:dict):
    """Calculates all the possible master subnets for a given subnet"""
    print(f'Calculating master subnets for {subnet}')
    master_subnets = set()
    subnet_obj = ipaddress.ip_network(str(subnet))

    for i in range(8, subnet_obj.prefixlen + 1):
        prefixlen_diff = subnet_obj.prefixlen - i
        if prefixlen_diff < 0:
            continue
        master_subnet = subnet_obj.supernet(prefixlen_diff)
        if subnet_obj.subnet_of(master_subnet) and str(master_subnet) != str(subnet):
            master_subnets.add(str(master_subnet))
    return master_subnets


def calc_addr_update_data(device:dict, interface:dict, address_response:dict):
    """Calculates data for address update"""
    print('Comparing data...')

    updated_address = {}

    if address_response['data'][0]['hostname'] != device['hostname'] and device['hostname'] not in (None, ''):
        updated_address['new-hostname'] = device['hostname']
        updated_address['old-hostname'] = address_response['data'][0]['hostname']

    if address_response['data'][0]['description'] != interface['description'] and interface['description'] not in (None, ''):
        updated_address['new-description'] = interface['description']
        updated_address['old-description'] = address_response['data'][0]['description']

    if address_response['data'][0]['is_gateway'] != interface['is-gateway'] and interface['is-gateway'] not in (None, ''):
        updated_address['new-is_gateway'] = interface['is-gateway']
        updated_address['old-is_gateway'] = address_response['data'][0]['is_gateway']

    if address_response['data'][0]['owner'] != device['owner'] and device['owner'] not in (None, ''):
        updated_address['new-owner'] = device['owner']
        updated_address['old-owner'] = address_response['data'][0]['owner']

    if address_response['data'][0]['mac'] != interface['mac'].lower() and interface['mac'] not in (None, ''):
        updated_address['new-mac'] = interface['mac'].lower()  
        updated_address['old-mac'] = address_response['data'][0]['mac']

    if address_response['data'][0]['custom_Device_Serial'] != device['serial'].upper() and device['serial'] not in (None, ''):
        updated_address['new-device-serial'] = device['serial'].upper()
        updated_address['old-device-serial'] = address_response['data'][0]['custom_Device_Serial']
    
    if updated_address and 'type' in device:
        updated_address['device-type'] = device['type']

    return updated_address


def compile_new_addr_data(device:dict, interface:dict, address_id:int=None):
    """Compiles new address data"""
    new_address_data = {}
    if 'type' in device:
        new_address_data['device-type'] = device['type']

    new_address_data['id'] = address_id
    new_address_data['ip'] = interface['ipv4Address']
    new_address_data['new-hostname'] = device['hostname']
    new_address_data['new-description'] = interface['description']
    new_address_data['new-is_gateway'] = 0 if interface['is-gateway'] is None else interface['is-gateway']
    new_address_data['new-owner'] = device['owner']
    new_address_data['new-mac'] = interface['mac'].lower()
    new_address_data['new-device-serial'] = device['serial'].upper()
    return new_address_data


def compile_new_subnet_data(subnet_id:int, network_address:str, subnet_mask:str, cidr:int, subnet_name:str, subnet_description:str, vrf_name:str):
    """Compiles new subnet data"""
    subnet_data = {}
    subnet_data['id'] = subnet_id
    subnet_data['new-network-address'] = network_address
    subnet_data['new-subnet-mask'] = subnet_mask
    subnet_data['new-cidr'] = cidr
    subnet_data['new-subnet-name'] = subnet_name
    subnet_data['new-subnet-description'] = subnet_description
    subnet_data['new-vrf'] = vrf_name
    return subnet_data


def check_ip_in_subnet(ip_address:str, subnet:dict):
    """Checks if a given ip address belongs to a subnet or address range and returns True or False"""
    ip = ipaddress.ip_address(ip_address)
    network = ipaddress.ip_network(subnet, strict=False)
    return ip in network


def check_ignored_address(ip_address:str):
    """Checks if a given ip address is part of the ignored address ranges configured in constants.py"""
    for subnet in c.IGNORED_IP_RANGES:
        if check_ip_in_subnet(ip_address, subnet):
            print(f'{ip_address:<16} in list of ignored IP-ranges. Skipping...')
            return True
    return False


def calc_vrf(subnet:dict):
    """Calculates associated VRF for a specified subnet"""
    subnet_network = ipaddress.ip_network(subnet)

    for vrf, networks in c.VRFS.items():
        for network in networks:
            if subnet_network.subnet_of(network):
                return vrf


def export_update_report(updated_subnets, updated_addresses):
    """Exports a report in csv-format with all applied changes"""

    # Export subnets report
    field_names = [
        'id',
        'change-type',
        'old-network-address',
        'new-network-address',
        'old-cidr',
        'new-cidr',
        'old-subnet-mask',
        'new-subnet-mask',
        'old-subnet-name',
        'new-subnet-name',
        'old-subnet-description',
        'new-subnet-description',
        'old-vrf',
        'new-vrf'
    ]
    export_csv(c.SUBNET_REPORT_PATH+c.SUBNET_REPORT_FILE_NAME, updated_subnets, field_names)

    # Export addresses report
    field_names = [
        'id', 
        'change-type',
        'device-type', 
        'ip', 
        'old-hostname', 
        'new-hostname', 
        'old-description',
        'new-description',
        'old-is_gateway',
        'new-is_gateway',
        'old-owner',
        'new-owner',
        'old-mac',
        'new-mac',
        'old-device-serial',
        'new-device-serial'
    ]
    export_csv(c.ADDRESS_REPORT_PATH+c.ADDRESS_REPORT_FILE_NAME, updated_addresses, field_names)


def export_json(file_name:str, data):
    """Creates a json file with provided data"""
    timestamp = f'_{datetime.now().strftime("%Y%m%d_%H%M")}'
    full_file_name = file_name+timestamp
    file_extension = '.json'
    unique_file_name = check_duplicate_file(full_file_name, file_extension)
    print(f'\nExporting {unique_file_name}...')
    try:
        with open(unique_file_name, "w", encoding="utf-8") as f: 
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(e)
    else:
        print('Done\n')


def export_csv(file_name:str, data, fieldnames:list):
    """Creates a csv file with provided data and ensures the required folder structure exists"""
    timestamp = f'_{datetime.now().strftime("%Y%m%d_%H%M")}'
    full_file_name = file_name+timestamp
    file_extension = '.csv'
    unique_file_name = check_duplicate_file(full_file_name, file_extension)
    
    # Ensure the folder structure exists
    folder_path = os.path.dirname(unique_file_name)
    if folder_path and not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    with open(unique_file_name, 'w', encoding='utf-8-sig', newline='') as export_report:
        writer = csv.DictWriter(export_report, fieldnames=fieldnames, delimiter=';', dialect='excel')
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f'{unique_file_name} created')


def check_duplicate_file(file_name:str, file_extension:str):
    """Checks for duplicate file name and appends a unique identifier to the provided file name if needed"""
    dupe_identifier = ''
    dupe_num = 1
    while True:
        unique_file_name = f'{file_name}{dupe_identifier}{file_extension}'
        if os.path.exists(unique_file_name) is True:
            dupe_identifier = f'_{dupe_num}'
            dupe_num+=1
        else:
            break
    return unique_file_name

