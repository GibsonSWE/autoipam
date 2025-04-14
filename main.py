#!/usr/bin/env python3

from src.cli import CLI
from src import utils
from src import constants as c

import sys


def main():
    """Main function"""
    if '--version' in sys.argv or '-v' in sys.argv:
        utils.show_version()
    elif '--help' in sys.argv or '-h' in sys.argv:
        CLI.show_help()
    else:
        cli = CLI()
        cli.start()


if __name__ == '__main__':
    main()
    print()
