#!/usr/bin/env python3

from src import ipam_api, dnac_api, checkpoint_api, vmanage_api
from src import utils
from src import cli_utils
from src import constants as c

import readline
import sys


def get_from_dnac():
    """Returns list from DNA-center with interface data per device"""
    try:
        token = dnac_api.get_token()
    except Exception as e:
        raise e

    retrieved_device_list = []
    device_data = []
    
    offset = 0
    print('Requesting device data from DNA-Center. Please wait...\n')
    while True:
        try:
            response = dnac_api.get_device_list(token, 'Routers', offset)
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
            response = dnac_api.get_device_list(token, 'Switches and Hubs', offset)
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
            retrieved_interfaces = dnac_api.get_interfaces(token, device)
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


def get_from_vmanage():
    print('Not implemented yet.')
    devices = None
    return devices


def get_from_checkpoint_all():
    """Returns list of devices from Check Point, where each device includes a list of interface data"""
    print('Requesting data from Checkpoint...')
    try:
        sid = checkpoint_api.get_sid()
    except Exception as e:
        raise e

    try:
        response = checkpoint_api.get_device_list(sid)
    except Exception as e:
        raise e

    devices = []

    for retrieved_device in response:
        selected_device_data = select_checkpoint_data(sid, retrieved_device)
        if selected_device_data is False:
            continue
        else:
            devices.append(selected_device_data)

    return devices


def get_from_checkpoint_single(device):
    """Returns interface data for a specific device"""
    print(f"\nRequesting data for {device['name']}")
    try:
        sid = checkpoint_api.get_sid()
    except Exception as e:
        raise e

    devices = []

    selected_device_data = select_checkpoint_data(sid, device)
    if selected_device_data is False:
        return
    else:
        devices.append(selected_device_data)
        return devices        


def select_checkpoint_data(sid, device):
    """Selects data and converts it to a standardized convention"""
    device_interfaces = []
    try:
        retrieved_device_data = checkpoint_api.get_device_data(sid, device['uid'])
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


def calculate_diff(devices):
    """Calculates the differences between the source and the IPAM database"""

    #Defines a new dictionary including four lists with pending new and updated subnets and addresses
    pending_changes = {
        'new-subnets': [], 
        'new-addresses': [],
        'updated-subnets': [],
        'updated-addresses': []
        }
    
    for device in devices:    
        for interface in device['interfaces']:
            try:
                address_response = ipam_api.get_address(interface['ipv4Address'])
            except Exception as e:
                raise e

            if address_response is False:
                subnet = utils.calc_subnet(interface['ipv4Address'], interface['ipv4Mask'])
                network_address = subnet['network_address']
                network_address_full = subnet['network_address_full']
                subnet_mask = subnet['subnet_mask']
                cidr = subnet['cidr']
                subnet_id = ipam_api.get_subnet_id(network_address_full)
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
                        master_subnet = ipam_api.get_master_subnet(possible_master_subnets)
                    except Exception as e:
                        raise e
                    
                    print(f"Calculated master subnet for {network_address_full}: {master_subnet}")
                    print()

                    new_subnet = compile_new_subnet_data(subnet_id, network_address, subnet_mask, cidr, subnet_name, subnet_description, vrf_name)

                    if new_subnet['new-subnet-description'] == '' or new_subnet['new-subnet-description'] is None:
                        new_subnet['new-subnet-description'] = 'Created by AutoIpam'

                    if not pending_changes['new-subnets']:
                        pending_changes['new-subnets'].append(new_subnet)
                    else:
                        # Check if the new subnet address is already present in the list
                        if network_address not in [i['new-network-address'] for i in pending_changes['new-subnets']]:
                            pending_changes['new-subnets'].append(new_subnet)

                new_address = compile_new_addr_data(device, interface)

                if not pending_changes['new-addresses']:
                    pending_changes['new-addresses'].append(new_address)
                else:
                    # Check if the new address is already present in the list
                    if interface['ipv4Address'] not in [i['ip'] for i in pending_changes['new-addresses']]:
                        pending_changes['new-addresses'].append(new_address)

            else:
                print(f"IP-address {interface['ipv4Address']:10} already exists in the IPAM-database")
                updated_address = calc_addr_update_data(device, interface, address_response)

                if updated_address:
                    updated_address['id'] = address_response['data'][0]['id']
                    updated_address['ip-address'] = interface['ipv4Address']
                    updated_address['change-type'] = 'update'
                    
                    pending_changes['updated-addresses'].append(updated_address)
                else:
                    print(f"No changes needed for {interface['ipv4Address']}")

    return pending_changes   


def update_ipam(devices):
    """Updates the IPAM database with the provided device and interface list"""
    updated_addresses = []
    updated_subnets = []
    conflicts = []
    for device in devices:
        for interface in device['interfaces']:
            try:
                address_response = ipam_api.get_address(interface['ipv4Address'])
            except Exception as e:
                raise e
            
            updated_address = {}
            updated_subnet = {}

            if address_response is not False:
                print(f"IP-address {interface['ipv4Address']:10} already exists in the IPAM-database")

                updated_address = calc_addr_update_data(device, interface, address_response)

                if updated_address:
                    updated_address['id'] = address_response['data'][0]['id']
                    updated_address['change-type'] = 'update'
                    updated_address['ip'] = interface['ipv4Address']

                    try:
                        ipam_api.update_address(updated_address)
                    except Exception as e:
                        raise e
                    else:
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
                subnet_description = ''
                vrf_name = utils.calc_vrf(network_address_full)
                vrf_id = ipam_api.get_vrf_id(vrf_name)
                
                try:
                    subnet_id = ipam_api.get_subnet_id(network_address_full)
                except Exception as e:
                    raise e

                if subnet_id is False:
                    return
                elif subnet_id is None:
                    possible_master_subnets = utils.calc_master_subnets(network_address_full)
                    
                    try:
                        master_subnet = ipam_api.get_master_subnet(possible_master_subnets)
                    except Exception as e:
                        raise e
                    
                    if master_subnet is not None:
                        try:
                            master_subnet_id = ipam_api.get_subnet_id(master_subnet)
                        except Exception as e:
                            raise e
                        try:
                            response = ipam_api.create_subnet(network_address, subnet_mask, cidr, subnet_name, subnet_description, vrf_id, c.SECTION_ID, master_subnet_id)
                            subnet_id = response['id']
                            if subnet_id is None:
                                print(f'Error creating {response["subnet"]}')
                                print(response['error'])
                                print('Skipping...')
                                conflicts.append(response)
                                continue
                            else:
                                change_type = 'create'
                        except Exception as e:
                            raise e
                    else:
                        print(f"Calculated existing master subnet for {network_address_full}: {master_subnet}")
                        
                        try:
                            response = ipam_api.create_subnet(network_address, subnet_mask, cidr, subnet_name, subnet_description, vrf_id, c.SECTION_ID)
                            subnet_id = response['id']
                            if subnet_id is None:
                                print(f'Error creating {response["subnet"]}')
                                print(response['error'])
                                print('Skipping...')
                                conflicts.append(response)
                                continue       
                        except Exception as e:
                            raise e
                    
                    # Data for NEW subnet
                    updated_subnet = compile_new_subnet_data(subnet_id, network_address, subnet_mask, cidr, subnet_name, subnet_description, vrf_name)
                    updated_subnet['change-type'] = 'create'
                    updated_subnets.append(updated_subnet)
                        
                    if subnet_id is False:
                        return
                try:    
                    address_id = ipam_api.create_address(interface, device, subnet_id)
                except Exception as e:
                    raise e
                
                # Data for NEW address
                updated_address = compile_new_addr_data(device, interface, address_id)
                updated_address['change-type'] = 'create'
                updated_addresses.append(updated_address)

    if len(conflicts) > 0:
        utils.export_json(c.CONFLICTS_PATH+c.CONFLICT_FILE_NAME, conflicts)

    print('\nUpdate finished!')

    if len(updated_subnets) > 0 or len(updated_addresses) > 0:
        print(f'Created {len(updated_subnets)} new subnets')
        export_prompt = input('Export report? [Y/n] ').lower().strip()
        if export_prompt == 'y' or export_prompt == '':
            export_update_report(updated_subnets, updated_addresses)
    else:
        print('No changes were made')


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
    utils.export_csv(c.SUBNET_REPORT_PATH+c.SUBNET_REPORT_FILE_NAME, updated_subnets, field_names)

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
    utils.export_csv(c.ADDRESS_REPORT_PATH+c.ADDRESS_REPORT_FILE_NAME, updated_addresses, field_names)


def show_diff(pending_changes):
    """Displays the calculated differences between the source and the IPAM database"""
    print('\nPending changes:')

    print('\nNew subnets:')    
    if not pending_changes['new-subnets']:
        print('No new subnets')
    else:
        for entry in pending_changes['new-subnets']:
            print("-----------------------------------------")
            for key, value in entry.items():
                print(f"    {key}: {value}")

    print('\nNew addresses:')
    if not pending_changes['new-addresses']:
        print('No new addresses')
    else:
        for entry in pending_changes['new-addresses']:
            print("-----------------------------------------")
            for key, value in entry.items():
                print(f"    {key}: {value}")

    print('\nMismatching address data:')
    if not pending_changes['updated-addresses']:
        print('No changes needed')
    else:
        for entry in pending_changes['updated-addresses']:
            print("-----------------------------------------")
            for key, value in entry.items():
                print(f"    {key}: {value}")

    # Creates a file in json-format and exports the calculated differences between the source and the IPAM database
    while True:
        export_prompt = input('\nExport the diff result? [Y/n] ').lower().strip()
        if export_prompt == 'n':
            return
        elif export_prompt == 'y' or export_prompt == '':
            utils.export_json(c.DIFF_PATH+c.DIFF_EXPORT_FILE_NAME, pending_changes)
            return


def source_checkpoint():
    """ """
    try:
        sid = checkpoint_api.get_sid()
    except Exception as e:
        raise e

    print('Requesting device list...')
    device_list = checkpoint_api.get_device_list(sid)
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
            devices = get_from_checkpoint_all()
            return devices
        elif device_select_prompt.isnumeric():
            device_select_prompt = int(device_select_prompt)
            if device_select_prompt not in device_range:
                print('Out of range')
                continue
            for device in device_list:
                if device.get('presented-id') == device_select_prompt:

                    devices = get_from_checkpoint_single(device)
            return devices
        else:
            continue


def lvl2():
    """Sub session level 2"""
    while True:
        readline.set_completer(cli_utils.lvl2_completer)
        readline.parse_and_bind('tab: complete')
        command = input('source>').lower().strip()
        if command in cli_utils.lvl2_commands:
            try:
                result = cli_utils.lvl2_commands[command]()
            except Exception as e:
                raise Exception(e)
            if command == 'exit':
                return None
            elif command in ('help', '?'):
                continue
            elif command == 'version':
                continue
            else:
                break
        elif command == '':
            continue
        else:
            print('%Invalid command')
    return result


def main():
    """Main function"""
    if '--version' in sys.argv or '-v' in sys.argv:
        utils.show_version()
    elif '--help' in sys.argv or '-h' in sys.argv:
        cli_utils.show_lvl1_help()
    else:
        print('\n############################## AutoIpam ##############################')
        utils.show_version()
        cli_utils.show_lvl1_help()
        while True:
            readline.set_completer(cli_utils.lvl1_completer)
            readline.parse_and_bind('tab: complete')
            command = input('>').lower().strip()
            if command in cli_utils.lvl1_commands:
                if command == 'update':
                    devices = cli_utils.lvl1_commands[command]()
                    if devices is not None:
                        update_ipam(devices)
                    else:
                        continue
                elif command == 'diff':
                    devices = cli_utils.lvl1_commands[command]()
                    if devices is not None:
                        pending_changes = calculate_diff(devices)
                        show_diff(pending_changes)
                    else:
                        continue

                elif command == 'exit':
                    return
                else:
                    cli_utils.lvl1_commands[command]()
            elif command == '':
                continue
            else:
                print('%Invalid command')


if __name__ == '__main__':
    main()
    print()
