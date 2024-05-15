
# AutoIpam

[![Build Status](https://s3prmgm0081.forestproducts.sca.com/python/autoipam/-/badges/release.svg)](https://s3prmgm0081.forestproducts.sca.com/python/autoipam)

**AutoIpam is a terminal tool used to automatically update phpIpam with data from several sources, currently including:**
- Cisco Catalyst Center
- Check Point Manager
- Cisco Catalyst SD-WAN Manager (Not yet implemented)

## Features
- Imports interface data for networking devices
- Updates phpIPAM with address information, hostname, description, mac-address, owner and more.
- Calculates subnet affiliation per address
- Creates new subnet if not already existing in the IPAM database
- Calculates and assigns a master subnet for new subnets in the IPAM database
- Displays the current difference between the IPAM database and the source via built in diff command
- Logs any conflicts that might appear in the updating process
- Has built-in command line interface with tab-completion

## Dependencies
**AutoIpam uses a number of libraries to work properly:**
*All dependencies are included in the dependencies.txt file*

-  **[requests]** - A HTTP library used for REST API-calls.
-  **[pip-system-certs]** - This package patches pip and requests at runtime to use certificates from the default system store (rather than the bundled certs ca).
-  **[ipaddress]** - This library simplifies subnet and address calculation.

## Installation
AutoIpam requires Python version 3 to run.
Git is required to clone the Gitlab repository.

**1. Create and enter the virtual environment**

```bash
python  -m  venv  env
source  env/bin/activate
```

**2. Download the project**

```bash
git  clone  https://s3prmgm0081.forestproducts.sca.com/python/autoipam.git
```

**3. Navigate to the script folder and install the dependencies**

```bash
cd  AutoIpam
pip  install  -r  dependencies.txt
```

## Getting started

**1. Make sure the virtual environment is active**
```bash
source  env/bin/activate
```

**2. Run the script**
```bash
python3  main.py
```

**3. Type any of the following commands**
```bash
>update
>show diff
>show version
>help/?
>exit
```

## User guide
#### CLI
AutoIpam features a fully functional Command Line Interface (CLI).
When first starting the script you will see the following output displaying the current version and release date aswell  as the available commands:
```bash
############################## AutoIpam ##############################
Version: v0.1.3 Beta
Released: 2024-04-23

Commands:        Description:
update         - Update IPAM
diff           - Show data difference between the IPAM database and the source
version        - Show script version
?/help         - Show this help output
exit           - Exit script

Press TAB to autocomplete command
Use UP and DOWN arrows to traverse command history

>
```

By entering either **update** or **diff** you will enter **source mode**.
In **source mode** you have a separate set of commands available, which you can display by typing **help** or **?**.

```bash
>diff
source>help

You can update IPAM with data from the following sources:
Command:         Source:
dnac           - Cisco DNA-Center
checkpoint     - Check Point
vmanage        - Cisco vmanage
exit           - Go back

source>
```


#### Source: dnac
If you select **dnac** as your source, the script will immediately start requesting all available data from DNA-center.
The script is currently hard coded to pull interface data from the device families **Routers** and **Switches and Hubs**.

#### Source: checkpoint
If you select **checkpoint** as your source, the CLI will display all available devices to pull data from.
You can then select the id for a specific device you want to pull data from, alternatively you can select **all** and the script will then pull data from all available checkpoint devices.

```bash
source>checkpoint
Requesting device list...

ID:   Hostname:                      Device type:
0     S1PRMGM0004                    checkpoint-host
1     SE-AZURE-FW-01_0               simple-gateway
2     SE-AZURE-FW-01_1               simple-gateway
3     SE-AZURE-VPN-FW-01             CpmiGatewayCluster
4     SE-AZURE-VPN-FW-01_0           cluster-member
5     SE-AZURE-VPN-FW-01_1           cluster-member
6     SE-BOL-SAW-FW-01               CpmiGatewayCluster
7     SE-BOL-SAW-KN1402-FW-01        cluster-member
8     SE-BOL-SAW-KN1801-FW-01        cluster-member
9     SE-DC-FW-01                    CpmiGatewayCluster
10    SE-DC-FW-02                    CpmiGatewayCluster
...
50    SE-RUN-SAW-KN8001-FW-02        cluster-member
51    SE-TUN-SAW-ST1-FW              CpmiGatewayCluster
52    SE-TUN-SAW-ST1-FW-01           cluster-member
53    SE-TUN-SAW-ST1-FW-02           cluster-member

Select device: [id/all]
```

#### Exporting diff results and update reports

After a successful update or diff calculation you get prompted with an option to export the result.

```bash
Export the diff result? [Y/n] y

Exporting /var/autoipam-reports/diff/autoipam_diff_20240509_2136.json...
Done

>
```

All diff reports are saved in their own json-file under **/var/autoipam-reports/diff** with the date and timestamp entered in the file name.

All update reports are saved in two separate csv-files. These files also have date and timestamp entered in the file name.
Address updates are saved in **/var/autoipam-reports/address-reports**
Subnet updates are saved in **/var/autoipam-reports/subnet-reports**

Any conflicts that might accour during an update or diff calculation are stored in a json-file under **/var/autoipam-reports/conflicts**.


## Configuration

Most of the configurable variables are available in the **CONSTANTS.py** file in the **src/** directory within the script installation.
Configurable variables includes URLs, API-endpoints, VRF network definitions, Ignored IP-ranges and more.


## Known bugs and missing features

- Doing multiple data requests from Checkpoint too quickly will crash the script due to incorrect handling of session token and missing error handling. This bug does not risk any data loss or data corruption. It is simply a rejection from the Checkpoint API, which the script is not currently able to handle properly. (This should be a priority to fix).

    Example:
    ```bash
    Requesting data for SE-AZURE-FW-01_1
    err_too_many_requests Too many requests in a given amount of time
    Traceback (most recent call last):
    File "/usr/bin/AutoIpam/src/checkpoint_api.py", line 20, in get_sid
        raise f"{response.json()['code']} {response.json()['message']}"
    TypeError: exceptions must derive from BaseException

    During handling of the above exception, another exception occurred:

    Traceback (most recent call last):
    File "/usr/bin/AutoIpam/main.py", line 727, in lvl2
        result = cli_utils.lvl2_commands[command]()
    File "/usr/bin/AutoIpam/main.py", line 713, in source_checkpoint
        devices = get_from_checkpoint_single(device)
    File "/usr/bin/AutoIpam/main.py", line 128, in get_from_checkpoint_single
        raise e
    File "/usr/bin/AutoIpam/main.py", line 126, in get_from_checkpoint_single
        sid = checkpoint_api.get_sid()
    File "/usr/bin/AutoIpam/src/checkpoint_api.py", line 26, in get_sid
        raise Exception(e)
    Exception: exceptions must derive from BaseException

    During handling of the above exception, another exception occurred:

    Traceback (most recent call last):
    File "/usr/bin/autoipam", line 791, in <module>
        main()
    File "/usr/bin/autoipam", line 770, in main
        devices = cli_utils.lvl1_commands[command]()
    File "/usr/bin/AutoIpam/main.py", line 729, in lvl2
        raise Exception(e)
    Exception: exceptions must derive from BaseException
    ```
- The script is currently missing proper error handling for many features, which might cause unexpected crashes if the script encounters unexpected scenarios.
- The script is currently missing API version checking, which might cause the script to crash if it encounters unexpected API behavior.
