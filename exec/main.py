import argparse
import ctypes
import logging
import platform
import sys

from exec.command import Command
from exec.generate_commands import generate_commands

COMMANDS = generate_commands()


def command_list(as_string=False):
    commands = list(COMMANDS.keys())
    commands.sort()

    if as_string:
        commands_parsed = []
        for command in commands:
            if COMMANDS[command].description:
                command = f'{command.ljust(25)} ; {COMMANDS[command].description}'
            commands_parsed.append(command)

        commands = '\n' + '\n'.join(commands_parsed)

    return commands


def main():
    """
    WARNING: This script executes subprocess with a shell.
    It does not automatically validate shell inputs and thus should only be used locally.
    Otherwise this opens up a shell command injection vulnerability.

    Use tips:
    If you need more help, run this script with --help flag.
    On Windows: If you want to run this from the command line with just the file name without extension, add ".py;" to the environment variable PATHTEXT
    """

    def parse_sys_argv():
        parser = argparse.ArgumentParser()
        parser.description = f'This is a tool for abstracting long to write or complicated shell commands. Available commands: {command_list()}'
        parser.add_argument('--print', action='store_true', default=False, help='Print out the command instead of executing')
        parser.add_argument('--confirmation', action='store_true', default=False, help='Print the command and ask for confirmation before executing')
        parser.add_argument('command_name', nargs='?')
        parser.add_argument('command_args', nargs='*')
        arguments, unknown_kwargs = parser.parse_known_args()
        arguments.command_args += unknown_kwargs
        return arguments

    def print_help():
        print(f'This is {__file__}')
        print()
        print(f'Available commands: {command_list(as_string=True)}')
        print('For more information, use flag --help\n')

    def handle_unrecognized_command():
        print(f'Unrecognized command. Available commands: {command_list(as_string=True)}\n')

    def rename_terminal_title(command_name: str):
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

    arguments = parse_sys_argv()

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
