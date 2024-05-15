import os
import ipaddress

RELEASE = {'version': 'v0.1.4 Beta', 'date': '2024-05-15'}

SECTION_ID = 3 #SCA
SUBNET_REPORT_PATH = '/var/autoipam-reports/subnet-reports/'   
ADDRESS_REPORT_PATH = '/var/autoipam-reports/address-reports/'
CONFLICTS_PATH = '/var/autoipam-reports/conflicts/'             
DIFF_PATH = '/var/autoipam-reports/diff/'


# Time stamp and unique identifier are set in functions in utils.py
SUBNET_REPORT_FILE_NAME = 'autoipam_report_subnets'
ADDRESS_REPORT_FILE_NAME = 'autoipam_report_addresses'
DIFF_EXPORT_FILE_NAME = 'autoipam_diff'
CONFLICT_FILE_NAME = 'update_conflicts'


IPAM_API_KEY = os.environ.get('AUTOIPAM_IPAM_API_KEY')
CHECKPOINT_API_KEY = os.environ.get('AUTOIPAM_CHECKPOINT_API_KEY')
DNAC_API_KEY = os.environ.get('AUTOIPAM_DNAC_API_KEY')
DNAC_USERNAME = 'autoipam'


IGNORED_IP_RANGES = [
    '0.0.0.0/32', 
    '10.200.252.33/30',     # Checkpoint Sync Networks
    '192.168.0.0/16',       # NAT Networks?
    '172.16.0.0/16'         # NAT Networks?
]


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
IPAM_URL = 'https://ipam.sca.com'
#IPAM_URL = 'https://ipamtest.sca.com'  #TEST URL
APP_ID = 'AutoIpam'

IPAM_GET_CUSTOM_FIELDS = f'/api/{APP_ID}/addresses/custom_fields/'
IPAM_ADDRESSES = f'/api/{APP_ID}/addresses/'
IPAM_GET_SUBNET = f'/api/{APP_ID}/subnets/cidr/'#{subnet}/ in CIDR format
IPAM_GET_VRFS = f'/api/{APP_ID}/vrf/'
IPAM_CREATE_SUBNET = f'/api/{APP_ID}/subnets/'
IPAM_SEARCH_ADDRESS = f'/api/{APP_ID}/addresses/search/'#{ip}/


# Checkpoint endpoints
CHECKPOINT_URL = 'https://S1PRMGM0004.forestproducts.sca.com'

CHECKPOINT_AUTH = '/web_api/login'
CHECKPOINT_SHOW_NETWORKS = '/web_api/show-networks'
CHECKPOINT_SHOW_HOSTS = '/web_api/show-hosts'
CHECKPOINT_SHOW_CHECKPOINT_HOSTS = '/web_api/show-checkpoint-hosts'
CHECKPOINT_SHOW_GATEWAYS_AND_SERVERS = '/web_api/show-gateways-and-servers'
CHECKPOINT_SHOW_OBJECT = '/web_api/show-object'


# DNA-center endpoints
DNAC_URL = 'https://dnac.forestproducts.sca.com'

DNAC_AUTH = '/dna/system/api/v1/auth/token/'
DNAC_NETWORK_DEVICE = '/dna/intent/api/v1/network-device/'
DNAC_INTERFACES = '/dna/intent/api/v1/interface/network-device/'#{deviceId}
