import ctypes
import logging
import platform
import sys

from exec.command import Command
from exec.cli import parse_sys_args
from exec.generate_commands import generate_commands

COMMANDS = generate_commands()


def _get_command_list(as_string=False) -> list:
    def convert_to_cli_output_format(commands) -> list[str]:
        commands_parsed = []
        for command in commands:
            if COMMANDS[command].description:
                command = f'{command.ljust(25)} ; {COMMANDS[command].description}'
            commands_parsed.append(command)
        return commands_parsed

    commands = list(COMMANDS.keys())
    commands.sort()

    if as_string:
        commands = '\n' + '\n'.join(convert_to_cli_output_format(commands))

    return commands


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
        print(f'Available commands: {_get_command_list(as_string=True)}')
        print('For more information, use flag --help\n')

    def handle_unrecognized_command():
        print(f'Unrecognized command. Available commands: {_get_command_list(as_string=True)}\n')

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

    arguments = parse_sys_args(_get_command_list)

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


if __name__ == '__main__':
    main()
