import os
import ipaddress
from configparser import ConfigParser

# This file contains all the constants used in the project.


# Opens the config.ini file and reads the configuration
try:
    config_file = os.path.join(os.path.dirname(__file__), '../config.ini')
    config = ConfigParser()
    config.read(config_file)
except FileNotFoundError:
    print(f"Error: Configuration file not found at {config_file}. Please check the path.")
    raise
except Exception as e:
    print(f"Error reading configuration file: {e}")
    raise


# Current version and release date
RELEASE = {'version': 'v0.2.0 (Beta)', 'date': '2025-04-14'}

# Section ID used for phpIpam API calls
SECTION_ID = config.get('phpIpam', 'section_id')

# Paths where the reports are saved
SUBNET_REPORT_PATH = '/var/autoipam-reports/subnet-reports/'   
ADDRESS_REPORT_PATH = '/var/autoipam-reports/address-reports/'
CONFLICTS_PATH = '/var/autoipam-reports/conflicts/'             
DIFF_PATH = '/var/autoipam-reports/diff/'


# Report file names
# Time stamp and unique identifier are set in functions in utils.py
SUBNET_REPORT_FILE_NAME = 'autoipam_report_subnets'
ADDRESS_REPORT_FILE_NAME = 'autoipam_report_addresses'
DIFF_EXPORT_FILE_NAME = 'autoipam_diff'
CONFLICT_FILE_NAME = 'update_conflicts'

# API keys for the different services
IPAM_API_KEY = config.get('phpIpam', 'api_key')
CHECKPOINT_API_KEY = config.get('Checkpoint', 'api_key')
DNAC_API_KEY = config.get('DNA-Center', 'api_key')

DNAC_USERNAME = config.get('DNA-Center', 'username')
IPAM_APP_ID = config.get('phpIpam', 'app_id')

# IP ranges that the script should ignore
IGNORED_IP_RANGES = config.get('IP Configs', 'ignored_ip_ranges')


# VRFs
SCA_PROCESS_VRF = [
    ipaddress.ip_network('10.192.0.0/16'),
    ipaddress.ip_network('10.193.0.0/16'),
    ipaddress.ip_network('10.194.0.0/16'),
    ipaddress.ip_network('10.195.0.0/16')
]

SCA_FACILITY_VRF = [
    ipaddress.ip_network('10.196.0.0/16'),
    ipaddress.ip_network('10.197.0.0/16'),
    ipaddress.ip_network('10.198.0.0/16'),
    ipaddress.ip_network('10.199.0.0/16')
]

SCA_MGMT_VRF = [
    ipaddress.ip_network('10.200.0.0/16'),
    ipaddress.ip_network('10.201.0.0/16'),
    ipaddress.ip_network('10.202.0.0/16'),
    ipaddress.ip_network('10.203.0.0/16')
]

SCA_PRINT_VRF = [
    ipaddress.ip_network('10.204.0.0/16'),
    ipaddress.ip_network('10.205.0.0/16'),
    ipaddress.ip_network('10.206.0.0/16'),
    ipaddress.ip_network('10.207.0.0/16')
]

SCA_COMMON_VRF = [
    ipaddress.ip_network('10.212.0.0/16'),
    ipaddress.ip_network('10.213.0.0/16'),
    ipaddress.ip_network('10.214.0.0/16'),
    ipaddress.ip_network('10.215.0.0/16')
]

SCA_DC_VRF = [
    ipaddress.ip_network('10.216.0.0/16')
]

SCA_DMZ_VRF = [
    ipaddress.ip_network('10.218.0.0/16')
]


# IPAM endpoints
IPAM_URL = config.get('phpIpam', 'url')

IPAM_GET_CUSTOM_FIELDS = f'/api/{IPAM_APP_ID}/addresses/custom_fields/'
IPAM_ADDRESSES = f'/api/{IPAM_APP_ID}/addresses/'
IPAM_GET_SUBNET = f'/api/{IPAM_APP_ID}/subnets/cidr/'#{subnet}/ in CIDR format
IPAM_GET_VRFS = f'/api/{IPAM_APP_ID}/vrf/'
IPAM_CREATE_SUBNET = f'/api/{IPAM_APP_ID}/subnets/'
IPAM_SEARCH_ADDRESS = f'/api/{IPAM_APP_ID}/addresses/search/'#{ip}/


# Checkpoint endpoints
CHECKPOINT_URL = config.get('Checkpoint', 'url')

CHECKPOINT_AUTH = '/web_api/login'
CHECKPOINT_SHOW_NETWORKS = '/web_api/show-networks'
CHECKPOINT_SHOW_HOSTS = '/web_api/show-hosts'
CHECKPOINT_SHOW_CHECKPOINT_HOSTS = '/web_api/show-checkpoint-hosts'
CHECKPOINT_SHOW_GATEWAYS_AND_SERVERS = '/web_api/show-gateways-and-servers'
CHECKPOINT_SHOW_OBJECT = '/web_api/show-object'


# DNA-center endpoints
DNAC_URL = config.get('DNA-Center', 'url')

DNAC_AUTH = '/dna/system/api/v1/auth/token/'
DNAC_NETWORK_DEVICE = '/dna/intent/api/v1/network-device/'
DNAC_INTERFACES = '/dna/intent/api/v1/interface/network-device/'#{deviceId}


# vManage endpoints
VMANAGE_URL = config.get('Vmanage', 'url')
VMANAGE_AUTH = ''
