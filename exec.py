import sys
import os.path
import platform
import subprocess
import logging
import types
import json
import argparse


COMMANDS = {
    # Setup
    'python-setup': [
        'python -m pip install --upgrade pip',
        'python -m pip install --upgrade virtualenv numpy pandas jupyter notebook aiohttp requests matplotlib',
    ],
    # Docker
    'udev': 'docker attach ubuntu-dev',
    'udev-bash': 'docker exec -it ubuntu-dev /bin/bash',
    'udev-up': 'docker-compose --file C:/Users/peter/OneDrive/MyOneDrive/Code/docker/ubuntu_dev/docker-compose.yml up -d --force-recreate',
    'udev-down': 'docker-compose --file C:/Users/peter/OneDrive/MyOneDrive/Code/docker/ubuntu_dev/docker-compose.yml down',
    'udev-build': 'docker-compose --file C:/Users/peter/OneDrive/MyOneDrive/Code/docker/ubuntu_dev/docker-compose.yml build',
    # Other
    'test-print': 'echo Working',
    'test-print-list': ['echo Working once,', 'echo Working twice'],
    'git-update': ['git checkout master', 'git stash', 'git pull', 'git stash pop', 'git branch --merged'],
}


def init_logging_to_file():
    log_file_path = os.path.join(os.path.dirname(__file__), 'logs', 'exec.log')
    logging.basicConfig(
        filename=log_file_path, filemode="a", format="%(levelname)s:%(name)s:%(asctime)s:%(message)s", datefmt='%Y-%m-%d %H:%M:%S', level='INFO'
    )
    logging.info('##### NEW RUN #####')
    logging.info('New run args: %s', sys.argv)


class SavedCommands:
    def __init__(self):
        def load_saved_commands():
            if os.path.isfile(self.saved_commands_path):
                with open(self.saved_commands_path) as commands_file:
                    saved_commands_dict = json.load(commands_file)
            else:
                saved_commands_dict = {}
            return saved_commands_dict

        self.saved_commands_path = os.path.join(os.path.dirname(__file__), 'saved_commands.json')
        self.saved_commands_dict = load_saved_commands()

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

    def take_saved_commands_to_use(self, commands):
        use_commands = {
            'save-command': self.save_command,
            'delete-command': self.delete_command,
        }
        commands.update(use_commands)
        commands.update(self.saved_commands_dict)


def command_list(as_string=False):
    commands = list(COMMANDS.keys())
    commands.sort()

    if as_string:
        commands = '\n' + '\n'.join(commands)

    return commands


def handle_command(command, arguments):
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


def main(arguments):
    """
    WARNING: This script does not automatically validate shell inputs and thus should only be used locally.

    Notes:
    If you want to run this from the command line with just the file name without extension, add ".py;" to the environment variable PATHTEXT
    """

    def print_help():
        print(f'This is {__file__}')
        print(f'Available commands: {command_list(as_string=True)}')
        print('For more information, use flag --help\n')

    def handle_unrecognized_command():
        print(f'Unrecognized command. Available commands: {command_list(as_string=True)}\n')

    def map_command(command_name):
        def localize_command(command):
            if platform.system() == 'Windows':
                command = command.replace('~', '%userprofile%')
            return command

        command = COMMANDS[command_name]
        if isinstance(command, str):
            command = localize_command(command)
        return command

    init_logging_to_file()
    saved_commands = SavedCommands()
    saved_commands.take_saved_commands_to_use(COMMANDS)

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
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_sys_argv()
    main(arguments)
