from . import constants as c
from . import utils

import json
import requests
from requests.auth import HTTPBasicAuth


##  DISABLE SSL WARNINGS
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class VmanageManager:
    """ A class to manage Cisco Vmanage API calls """
    def __init__(self):
        self.base_url = c.VMANAGE_URL
        self.auth_url = c.VMANAGE_AUTH
        self.token = None
        self.devices = []
        self.interfaces = []
        self.interfaces_with_ipv4address = []

    def get_from_vmanage(self):
        print('Not implemented yet.')
        devices = None
        return devices
    