from . import utils
from . import constants as c
from src.ipam_manager import IPAMManager
from src.dnac_manager import DNACManager
from src.checkpoint_manager import CheckpointManager
from src.vmanage_manager import VmanageManager

import readline
import requests


class CLI:
    """CLI class that handles the command line interface"""

    def __init__(self):
        self.prompt = 'AutoIpam> '
        self.subsession_update_prompt = 'AutoIpam (update source)> '
        self.subsession_diff_prompt = 'AutoIpam (diff source)> '
        self.intro = '############################## AutoIpam ##############################'
        self.subsession = False
        self.subsession_mode = None
        self.dnac_manager = DNACManager()
        self.checkpoint_manager = CheckpointManager()
        self.vmanage_manager = VmanageManager()
        self.commands =  {
            'info_commands': {
                '?': lambda: self.show_help(),
                'help': lambda: self.show_help(),
                'version': utils.show_version
            },
            
            'exit_subsession_commands': {
                'exit': lambda: self.exit_subsession(),
                'back': lambda: self.exit_subsession()
            },

            'exit_cli_commands': {
                'exit': lambda: self.exit_cli(),
                'quit': lambda: self.exit_cli()
            },

            'action_commands': {
                'update': lambda: self.start_subsession(mode='update'),
                'diff': lambda: self.start_subsession(mode='diff')
            },

            'source_selection_commands': {
                'dnac': lambda: self.dnac_manager.get_from_dnac(),
                'checkpoint': lambda: self.checkpoint_manager.source(),
                'vmanage': lambda: self.vmanage_manager.get_from_vmanage()
            }
        }


    def completer(self, text, state):
        """Tab completer"""
        if self.subsession:
            commands = self.commands['info_commands'] | self.commands['source_selection_commands'] | self.commands['exit_subsession_commands']
        else:
            commands = self.commands['info_commands'] | self.commands['action_commands'] | self.commands['exit_cli_commands']

        options = [cmd for cmd in commands.keys() if cmd.startswith(text)]
        if state < len(options):
            return options[state]
        else:
            return None


    def set_completer(self, completer):
        """Sets the completer for the CLI"""
        self.completer = completer
        readline.set_completer(completer)
        readline.parse_and_bind('tab: complete')
        readline.parse_and_bind('set editing-mode emacs')
        readline.parse_and_bind('set show-all-if-ambiguous on')
        readline.parse_and_bind('set show-all-if-unmodified on')


    def start(self):
        """Starts the CLI"""
        print(self.intro)
        utils.show_version()

        while True:
            try:
                self.set_completer(self.completer)
                command = input(self.prompt).lower().strip()
                if command == '':
                    continue
                elif command in ['exit', 'quit']:
                    self.exit_cli()
                    break
                elif command in self.commands['info_commands']:
                    self.execute_command(command)
                elif command in self.commands['action_commands']:
                    self.execute_command(command)
                else:
                    print(f"Unknown command: {command}")
            except requests.ConnectionError as e:
                print(f"Connection error occurred: {e}")
                self.subsession = False
                continue
            except requests.Timeout as e:
                print(f"Request timed out: {e}")
                self.subsession = False
                continue
            except requests.HTTPError as e:
                print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                self.subsession = False
                continue
            except ValueError as e:
                print(f"Value error: {e}")
                self.subsession = False
                continue
            except EOFError as e:
                self.exit_cli()
                return None
            except KeyboardInterrupt:
                self.exit_cli()
                return None


    def start_subsession(self, mode:str):
        """Starts a subsession in either update or diff mode"""
        self.subsession = True
        if mode == 'update':
            self.subsession_mode = 'update'
            self.subsession_prompt = self.subsession_update_prompt
        elif mode == 'diff':
            self.subsession_mode = 'diff'
            self.subsession_prompt = self.subsession_diff_prompt

        self.ipam_manager = IPAMManager()
        while True:
            try:
                self.set_completer(self.completer)

                user_command = input(self.subsession_prompt).lower().strip()
                if user_command == '':
                    continue
                elif user_command in ['exit', 'back']:
                    self.exit_subsession()
                    break
                elif user_command in self.commands['info_commands']:
                    self.execute_command(user_command)
                elif user_command in self.commands['source_selection_commands']:

                    devices = self.execute_command(user_command)
                    if devices is None:
                        continue
                    if mode == 'update':
                        self.ipam_manager.update_ipam(devices)
                    elif mode == 'diff':
                        pending_changes = self.ipam_manager.calculate_diff(devices)
                        self.show_diff(pending_changes)
                        
                        # Creates a file in json-format and exports the calculated differences between the source and the IPAM database
                        while True:
                            export_prompt = input('\nExport diff report? [Y/n] ').lower().strip()
                            if export_prompt == 'n':
                                break
                            elif export_prompt == 'y' or export_prompt == '':
                                utils.export_json(c.DIFF_PATH+c.DIFF_EXPORT_FILE_NAME, pending_changes)
                                break
                else:
                    print(f"Unknown command: {user_command}")
            except EOFError as e:
                self.exit_subsession()
                return None
            except KeyboardInterrupt:
                self.exit_subsession()
                return None


    def execute_command(self, user_command:str):
        """Executes a user command"""
        if user_command in self.commands['info_commands']:
            return self.commands['info_commands'][user_command]()
        elif user_command in self.commands['action_commands']:
            return self.commands['action_commands'][user_command]()
        elif user_command in self.commands['source_selection_commands']:
            return self.commands['source_selection_commands'][user_command]()
        else:
            print(f"Unknown command: {user_command}")
            return None


    def show_help(self):
        """Displays the available CLI-commands for either the main session or the subsession"""
        if self.subsession:
            print()
            print(f'Usage: AutoIpam ({self.subsession_mode} source)> <command>')
            print()
            print('Available Commands:')
            print('  dnac           - Fetch data from Cisco DNA-Center')
            print('  checkpoint     - Fetch data from Check Point')
            print('  vmanage        - Fetch data from Cisco vManage')
            print('  exit/back      - Exit the current subsession')
            print()
            print('Description:')
            print('  Use these commands to select a source and update or compare data with the IPAM database.')
            print()
        else:
            print()
            print('Usage: AutoIpam> <command>')
            print()
            print('Available Commands:')
            print('  update         - Update IPAM with data from a source')
            print('  diff           - Show differences between the IPAM database and a source')
            print('  version        - Display the current script version')
            print('  ?/help         - Show help output')
            print('  exit/quit      - Exit the AutoIpam CLI')
            print()
            print('Tips:')
            print('  - Press TAB to autocomplete commands.')
            print('  - Use UP and DOWN arrows to navigate command history.')
            print()


    def show_diff(self, pending_changes:dict):
        """Prints the calculated differences between the source and the IPAM database"""
        print('\nPending Changes:')

        print('\nNew Subnet Objects:')    
        if not pending_changes['new-subnet-objects']:
            print('No new subnets')
        else:
            for entry in pending_changes['new-subnet-objects']:
                print("-----------------------------------------")
                for key, value in entry.items():
                    if value is not None:
                        key = key.replace("new-", "").replace("-", " ").replace("_", " ").strip().title()
                        if key == 'Cidr':
                            key = key.upper()
                            value = '/'+value
                        if key == 'Vrf':
                            key = key.upper()
                        print(f"    {key}: {value}")

        print('\nNew Address Objects:')
        if not pending_changes['new-address-objects']:
            print('No new addresses')
        else:
            for entry in pending_changes['new-address-objects']:
                print("-----------------------------------------")
                for key, value in entry.items():
                    if value is not None:
                        key = key.replace("new-", "").replace("-", " ").replace("_", " ").strip().title()
                        if key == 'Ip':
                            key = key.upper()
                        print(f"    {key}: {value}")

        print('\nMismatching Address Data:')
        if not pending_changes['updated-address-objects']:
            print('No changes needed')
        else:
            for entry in pending_changes['updated-address-objects']:
                print("-----------------------------------------")
                for key, value in entry.items():
                    if value is not None:    
                        print(f"    {key}: {value}")


    def exit_subsession(self):
        """Exits the current subsession"""
        print()
        self.subsession = False
        self.subsession_mode = None
        return None


    def exit_cli(self):
        """Exits the CLI"""
        print()
        print('Exiting AutoIpam...')
        return None

