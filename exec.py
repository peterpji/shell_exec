import sys
import os.path
import platform
import subprocess
import logging
import types
import json
import argparse

udev_yaml = os.path.join(os.path.dirname(__file__), '..', 'docker', 'ubuntu_dev', 'docker-compose.yml')


COMMANDS = {
    # Setup
    'python-setup': [
        'python -m pip install --upgrade pip',
        'python -m pip install --upgrade pylint black virtualenv requests pandas jupyter aiohttp matplotlib',
    ],
    # Docker
    'udev': 'docker attach ubuntu-dev',
    'udev-bash': 'docker exec -it ubuntu-dev /bin/bash',
    'udev-up': f'docker-compose --file {udev_yaml} up -d --force-recreate --always-recreate-deps',
    'udev-down': f'docker-compose --file {udev_yaml} down',
    'udev-build': f'docker-compose --file {udev_yaml} build',
    # Other
    'test-print': 'echo Working',
    'test-print-list': ['echo Working once', 'echo Working twice'],
    'git-update': ['git checkout master', 'git stash', 'git pull', 'git stash pop', 'git branch --merged'],
}


class SavedCommands:
    def __init__(self, commands_dict):
        """
        Initialization adds save_command and delete_command methods to the commands_dict
        """

        def load_saved_commands():
            if os.path.isfile(self.saved_commands_path):
                with open(self.saved_commands_path) as commands_file:
                    saved_commands_dict = json.load(commands_file)
            else:
                saved_commands_dict = {}
            return saved_commands_dict

        self.saved_commands_path = os.path.join(os.path.dirname(__file__), 'saved_commands.json')
        self.saved_commands_dict = load_saved_commands()
        self._take_saved_commands_to_use(commands_dict)

    def save_command(self, arguments):
        command_name = arguments.command_args[0]
        command_code = ' '.join(arguments.command_args[1:])

        self.saved_commands_dict[command_name] = command_code

        with open(self.saved_commands_path, 'w') as commands_file:
            json.dump(self.saved_commands_dict, commands_file, indent=4)

    def delete_command(self, arguments):
        command_name = arguments.command_args[0]
        del self.saved_commands_dict[command_name]

        with open(self.saved_commands_path, 'w') as commands_file:
            json.dump(self.saved_commands_dict, commands_file, indent=4)

    def _take_saved_commands_to_use(self, commands_dict):
        use_commands = {
            'save-command': self.save_command,
            'delete-command': self.delete_command,
        }
        commands_dict.update(use_commands)
        commands_dict.update(self.saved_commands_dict)


def command_list(as_string=False):
    commands = list(COMMANDS.keys())
    commands.sort()

    if as_string:
        commands = '\n' + '\n'.join(commands)

    return commands


def handle_command(command, arguments):
    """
    This function handles printing and running commands as well as asking for user confirmation if necessary.
    """

    def print_command(command, args):
        if isinstance(command, (types.FunctionType, types.MethodType)):
            print(f'Python function: {command}; Args: {args}')
        else:
            print(command)

    def ask_confirmation_from_user(command, args):
        conf = ''
        while conf.lower() not in ['y', 'n']:
            print_command(command, args)
            conf = input('Do you want to run? (y/n): ')

            if conf.lower() == 'n':
                print('Command cancelled')
            elif conf.lower() == 'y':
                print('Running command')
            else:
                print('Input not in (y/n)')

        return conf.lower() == 'y'

    def patch_environ():
        env = os.environ.copy()
        system32 = os.path.join(os.environ['SystemRoot'], 'SysNative' if platform.architecture()[0] == '32bit' else 'System32')
        ssh_path = os.path.join(system32, 'OpenSSH')
        env['PATH'] += ';' + ssh_path + ';'

        return env

    def run_command(command):
        if isinstance(command, (types.FunctionType, types.MethodType)):
            logging.info('Running: %s', command)
            command(arguments)
        elif isinstance(command, str):
            logging.info('Running: %s', command)
            command = command.split(' ')
            subprocess.run(  # pylint: disable=subprocess-run-check
                command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, env=patch_environ(), shell=True
            ).check_returncode()
        elif isinstance(command, list):
            for elem in command:
                run_command(elem)
        else:
            logging.warning('Unknown command type')

    if isinstance(command, str):
        command = ' '.join([command] + arguments.command_args)

    if arguments.print:
        print_command(command, arguments.command_args)
        return

    if arguments.confirmation and not ask_confirmation_from_user(command, arguments.command_args):
        logging.info('Command cancelled')
        return

    run_command(command)


def main():
    """
    WARNING: This script exesutes subprocess with a shell.
    It does not automatically validate shell inputs and thus should only be used locally.
    Otherwise this opens up a shell command injection vulnerability.

    Use tips:
    If you need more help, run this script with --help flag.
    On Windows: If you want to run this from the command line with just the file name without extension, add ".py;" to the environment variable PATHTEXT
    """

    def init_logging_to_file():
        log_file_path = os.path.join(os.path.dirname(__file__), 'logs', 'exec.log')
        logging.basicConfig(
            filename=log_file_path, filemode="a", format="%(levelname)s:%(name)s:%(asctime)s:%(message)s", datefmt='%Y-%m-%d %H:%M:%S', level='INFO'
        )
        logging.info('##### NEW RUN #####')
        logging.info('New run args: %s', sys.argv)

    def print_help():
        print(f'This is {__file__}')
        print(f'Available commands: {command_list(as_string=True)}')
        print('For more information, use flag --help\n')

    def handle_unrecognized_command():
        print(f'Unrecognized command. Available commands: {command_list(as_string=True)}\n')

    def map_command(command_name):
        """
        Maps command names to the actual commands via COMMANDS dict. Tries to replace platform specific commands if necessary.
        """

        def localize_command(command):
            if platform.system() == 'Windows':
                command = command.replace('~', '%userprofile%')
            return command

        command = COMMANDS[command_name]
        if isinstance(command, str):
            command = localize_command(command)
        return command

    arguments = parse_sys_argv()
    init_logging_to_file()
    SavedCommands(COMMANDS)

    if not arguments.command_name:
        print_help()
        return

    if arguments.command_name in COMMANDS:
        command = map_command(arguments.command_name)
        handle_command(command, arguments)
    else:
        handle_unrecognized_command()


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


if __name__ == "__main__":
    main()
