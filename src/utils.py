from src import constants as c

import os
import json
import csv
import ipaddress
from datetime import datetime


def show_version():
    """Displays the current script version"""
    print(f"Version: {c.RELEASE['version']}")
    print(f"Released: {c.RELEASE['date']}")


def calc_org(hostname):
    """Calculates organisation for device using hostname (Not yet implemented)"""
    pass


def calc_owner(hostname):
    """Calculates owner for device using hostname"""
    if hostname.find('SE-MUN-PAPER') != -1:
        return 'SCA Munksund När-IT'
    elif hostname.find('SE-OBB') != -1:
        return 'SCA Obbola När-IT'
    else:
        return 'SCA IT-infrastruktur network'
    

def calc_subnet(ip_address, subnet_mask):
    """Calculates subnet information from ip-address and subnet mask"""
    print(f"\nCalculating subnet for ip {ip_address} with mask {subnet_mask}")
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


def calc_master_subnets(subnet):
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
    

def check_ip_in_subnet(ip_address, subnet):
    """Checks if a given ip address belongs to a subnet or address range and returns True or False"""
    ip = ipaddress.ip_address(ip_address)
    network = ipaddress.ip_network(subnet, strict=False)
    return ip in network


def check_ip_in_ignored(ip_address):
    """Checks if a given ip address is part of the ignored address ranges configured in constants.py"""
    for subnet in c.IGNORED_IP_RANGES:
        if check_ip_in_subnet(ip_address, subnet):
            print(f'{ip_address:<16} in list of ignored IP-ranges, skipping')
            return True
    return False


def calc_vrf(subnet):
    """Calculates associated VRF for a specified subnet"""
    subnet_network = ipaddress.ip_network(subnet)

    for network in c.SCA_PROCESS_VRF:
        if subnet_network.subnet_of(network):
            return 'SCA_PROCESS'
        
    for network in c.SCA_FACILITY_VRF:
        if subnet_network.subnet_of(network):
            return 'SCA_FACILITY'
    
    for network in c.SCA_MGMT_VRF:
        if subnet_network.subnet_of(network):
            return 'SCA_MGMT'
        
    for network in c.SCA_PRINT_VRF:
        if subnet_network.subnet_of(network):
            return 'SCA_PRINT'
    
    for network in c.SCA_COMMON_VRF:
        if subnet_network.subnet_of(network):
            return 'SCA_COMMON'
    
    for network in c.SCA_DC_VRF:
        if subnet_network.subnet_of(network):
            return 'SCA_DC'
        
    for network in c.SCA_DMZ_VRF:
        if subnet_network.subnet_of(network):
            return 'SCA_DMZ'
        
    return None


def export_json(file_name, data):
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


def export_csv(file_name, data, fieldnames):
    """Creates a csv file with provided data"""
    timestamp = f'_{datetime.now().strftime("%Y%m%d_%H%M")}'
    full_file_name = file_name+timestamp
    file_extension = '.csv'
    unique_file_name = check_duplicate_file(full_file_name, file_extension)
    with open(unique_file_name, 'w', encoding='utf-8-sig', newline='') as export_report:
        writer = csv.DictWriter(export_report, fieldnames=fieldnames, delimiter=';', dialect='excel')
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f'{file_name} created')


def check_duplicate_file(file_name, file_extension):
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

