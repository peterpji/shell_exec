import ctypes
import logging
import platform
import sys
from typing import Dict

from exec.command import Command
from exec.parse_sys_args import parse_sys_args
from exec.generate_commands import generate_commands

COMMANDS = generate_commands()


def main():
    """
    WARNING: This script executes subprocess with a shell.
    It does not automatically validate shell inputs!
    Thus, it should only be used locally, otherwise this opens up a shell injection vulnerability.

    Use tips:
    If you need more help, run this script with --help flag.
    You can get this to your local PATH by installing this as a python package (run 'pip install .' on the project root directory).
    """

    def print_help():
        print(f'This is {__file__}')
        print()
        print(f'Available commands: {_parse_command_list_with_help(COMMANDS)}')
        print('For more information, use flag --help\n')

    def handle_unrecognized_command():
        print(f'Unrecognized command. Available commands: {_parse_command_list_with_help(COMMANDS)}\n')

    def rename_terminal_title(command_name: str):
        """
        Sets the name of the command as the title of the command line window.
        """
        if platform.system() == 'Windows':
            ctypes.windll.kernel32.SetConsoleTitleW(command_name)
            # subprocess.run(['title', command_name], shell=True)  # pylint: disable=subprocess-run-check
        else:
            sys.stdout.write(f'\x1b]2;{command_name}\x07')

    def ask_confirmation_from_user(command: Command):
        conf = ''
        while conf.lower() not in ['y', 'n']:
            print(command)
            conf = input('Do you want to run? (y/n): ')

            if conf.lower() == 'n':
                print('Command cancelled')
            elif conf.lower() == 'y':
                print('Running command')
            else:
                print('Input not in (y/n)')

        return conf.lower() == 'y'

    arguments = parse_sys_args(_parse_command_list_with_help(COMMANDS))

    if not arguments.command_name:
        print_help()
        return

    if arguments.command_name not in COMMANDS:
        handle_unrecognized_command()
        return

    rename_terminal_title(arguments.command_name)

    command = COMMANDS[arguments.command_name]
    command.arguments = arguments.command_args

    if arguments.print:
        print(command)
        return

    if arguments.confirmation and not ask_confirmation_from_user(command):
        logging.info('Command cancelled')
        return

    command.execute()


def _parse_command_list_with_help(commands: Dict[str, Command]):
    def convert_to_cli_output_format(command_keys) -> list[str]:
        commands_parsed = []
        for command in command_keys:
            if commands[command].description:
                command = f'{command.ljust(25)} ; {commands[command].description}'
            commands_parsed.append(command)
        return commands_parsed

    command_keys = list(commands.keys())
    command_keys.sort()
    commands_string = '\n' + '\n'.join(convert_to_cli_output_format(command_keys))
    return commands_string


if __name__ == '__main__':
    main()
