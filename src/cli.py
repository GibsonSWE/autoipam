from src import utils
import main


def show_lvl1_help():
    """Displays the available CLI-commands for subsession level 1"""
    print()
    print('Commands:        Description:')
    print('update         - Update IPAM')
    print('diff           - Show data difference between the IPAM database and the source')
    print('version        - Show script version')
    print('?/help         - Show this help output')
    print('exit           - Exit script\n')
    print('Press TAB to autocomplete command')
    print('Use UP and DOWN arrows to traverse command history')
    print()


def show_lvl2_help():
    """Displays the available CLI-commands for subsession level 2"""
    print()
    print('You can update IPAM with data from the following sources:')
    print('Command:         Source:')
    print('dnac           - Cisco DNA-Center')
    print('checkpoint     - Check Point')
    print('vmanage        - Cisco vmanage')
    print('exit           - Go back')
    print()


def lvl1_completer(text, state):
    """Tab completer for subsession level 1"""
    options = [cmd for cmd in lvl1_commands.keys() if cmd.startswith(text)]
    if state < len(options):
        return options[state]
    else:
        return None


def lvl2_completer(text, state):
    """Tab completer for subsession level 2"""
    options = [cmd for cmd in lvl2_commands.keys() if cmd.startswith(text)]
    if state < len(options):
        return options[state]
    else:
        return None


def exit_func():
    """Callable exit function for subsessions"""
    return None


# Available CLI-commands per subsession level
lvl1_commands = {
    'update': main.lvl2,
    'diff': main.lvl2,
    'version': utils.show_version,
    '?': show_lvl1_help,
    'help': show_lvl1_help,
    'exit': exit_func
}

lvl2_commands = {
    'dnac': main.get_from_dnac,
    'checkpoint': main.source_checkpoint,
    'vmanage': main.get_from_vmanage,
    '?': show_lvl2_help,
    'help': show_lvl2_help,
    'version': utils.show_version,
    'exit': exit_func
}

