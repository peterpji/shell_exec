import argparse
import ctypes
import json
import logging
import os.path
import platform
import subprocess
import sys
import types

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_COMMANDS_PATH = os.path.join(FILE_DIR, 'saved_commands.json')


def example_func(*args):
    print('This is a python test function')
    print(args)


def generate_commands() -> dict:
    """
    Check readme for valid command formats
    """
    udev_yaml = os.path.join(FILE_DIR, '..', 'docker', 'ubuntu_dev', 'docker-compose.yml')

    commands = {
        # Setup
        'python-setup': {
            'command': [
                'python -m pip install --upgrade pip',
                'python -m pip install --upgrade bandit black coverage flake8 pylint safety virtualenv requests pandas jupyter aiohttp matplotlib',
            ],
            'description': 'Upgrades pip, packages used by this tool and some other basic packages',
        },
        # Docker
        'udev': 'docker attach ubuntu-dev',
        'udev-bash': 'docker exec -it ubuntu-dev /bin/bash',
        'udev-run': 'docker exec -it ubuntu-dev',
        'udev-up': f'docker-compose --file={udev_yaml} up -d --force-recreate --always-recreate-deps',
        'udev-down': f'docker-compose --file={udev_yaml} down',
        'udev-build': f'docker-compose --file={udev_yaml} build',
        'udev-exec': 'docker exec -it ubuntu-dev',
        'udev-compose': f'docker-compose --file={udev_yaml}',
        # Code quality
        'bandit': f'bandit -r {FILE_DIR} --skip=B101,B404,B602 --format=txt',
        'black': f'black --line-length=150 --skip-string-normalization --exclude=logs/ {FILE_DIR}',
        'coverage': [f'python -m coverage run --source={FILE_DIR} -m unittest discover', 'python -m coverage report'],
        'flake8-show-stoppers': f'flake8 {FILE_DIR} --count --statistics --select=E9,F63,F7,F82 --show-source',  # Most critical issues
        'flake8': f'flake8 {FILE_DIR} --count --statistics --max-complexity=10 --select=F,C --ignore=E501,W503,E226,E203',
        'isort': [f'isort {FILE_DIR}', 'run black'],  # Ensure that code formating stays consistent after the import fixes using black
        'pre-commit-tools': f'cd {FILE_DIR} && pre-commit run -a',
        'pylint': f'cd {os.path.join(FILE_DIR, "..")} && python -m pylint {FILE_DIR}',
        'safety': f'safety check --full-report --file={os.path.join(FILE_DIR, "requirements.txt")}',
        # Other
        'test-print': {'command': 'echo Working', 'description': 'Echoes "Working". Example of a hello world command.'},
        'test-print-list': {'command': ['echo Working once', 'echo Working twice'], 'description': 'Runs multiple commands in row'},
        'test-python': {'command': example_func, 'description': 'Example of a python command. Echoes back given arguments object'},
        'git-update': {
            'command': ['git checkout master', 'git stash', 'git pull', 'git stash pop', 'git branch --merged'],
            'description': 'Shortcut for pulling git master with stashing',
        },
    }

    commands['quality'] = {
        'command': [
            commands['isort'],
            commands['black'],
            commands['bandit'],
            commands['safety'],
            commands['flake8-show-stoppers'],
            commands['flake8'],
            commands['pylint'],
        ],
        'except_return_status': True,
    }

    return commands


COMMANDS = generate_commands()


class SavedCommands:
    def __init__(self, commands_dict):
        """
        Initialization adds save_command and delete_command methods to the commands_dict
        """

        def load_saved_commands():
            if os.path.isfile(SAVED_COMMANDS_PATH):
                with open(SAVED_COMMANDS_PATH) as commands_file:
                    saved_commands_dict = json.load(commands_file)
            else:
                saved_commands_dict = {}
            return saved_commands_dict

        self.saved_commands_dict = load_saved_commands()
        self._take_saved_commands_to_use(commands_dict)

    def save_command(self, arguments):
        command_name = arguments.command_args[0]
        command_code = ' '.join(arguments.command_args[1:])

        self.saved_commands_dict[command_name] = command_code

        if not os.path.isdir(os.path.dirname(SAVED_COMMANDS_PATH)):
            os.mkdir(os.path.dirname(SAVED_COMMANDS_PATH))

        with open(SAVED_COMMANDS_PATH, 'w') as commands_file:
            json.dump(self.saved_commands_dict, commands_file, indent=4)

    def delete_command(self, arguments):
        command_name = arguments.command_args[0]
        del self.saved_commands_dict[command_name]

        with open(SAVED_COMMANDS_PATH, 'w') as commands_file:
            json.dump(self.saved_commands_dict, commands_file, indent=4)

    def _take_saved_commands_to_use(self, commands_dict):
        use_commands = {
            'save-command': {
                'command': self.save_command,
                'description': 'Syntax: save-command <command-name-without-spaces> <command line command>',
            },
            'delete-command': self.delete_command,
        }
        commands_dict.update(use_commands)
        commands_dict.update(self.saved_commands_dict)


def command_list(as_string=False):
    commands = list(COMMANDS.keys())
    commands.sort()

    if as_string:
        commands_parsed = []
        for command in commands:
            if isinstance(COMMANDS[command], dict) and COMMANDS[command].get('description'):
                command = f'{command.ljust(25)} ; {COMMANDS[command]["description"]}'
            commands_parsed.append(command)

        commands = '\n' + '\n'.join(commands_parsed)

    return commands


def handle_command(command, arguments):
    """
    This function handles printing and running commands as well as asking for user confirmation if necessary.
    """

    def print_command(command, args):
        if isinstance(command, dict):
            command = command['command']
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

        if platform.system() == 'Windows':
            system32 = os.path.join(os.environ['SystemRoot'], 'SysNative' if platform.architecture()[0] == '32bit' else 'System32')
            ssh_path = os.path.join(system32, 'OpenSSH')
            env['PATH'] += ';' + ssh_path

        return env

    def run_command(command, except_return_status=None):
        if isinstance(command, dict):
            except_return_status = except_return_status or command.get('except_return_status')
            command = command['command']
        if isinstance(command, (types.FunctionType, types.MethodType)):
            logging.info('Running: %s', command)
            command(arguments)
        elif isinstance(command, str):
            logging.info('Running: %s', command)
            command = command.split(' ')
            try:
                subprocess.run(  # pylint: disable=subprocess-run-check
                    command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, env=patch_environ(), shell=True
                ).check_returncode()
            except (subprocess.CalledProcessError, KeyboardInterrupt) as e:
                sys.tracebacklimit = 0
                if not except_return_status:
                    raise e
        elif isinstance(command, list):
            for elem in command:
                run_command(elem, except_return_status)
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

    def init_logging_to_file():
        log_file_path = os.path.join(os.path.dirname(__file__), 'logs', 'exec.log')
        logging.basicConfig(
            filename=log_file_path, filemode='a', format='%(levelname)s:%(name)s:%(asctime)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S', level='INFO'
        )
        logging.info('##### NEW RUN #####')
        logging.info('New run args: %s', sys.argv)

    def print_help():
        print(f'This is {__file__}')
        print()
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

    def rename_terminal_title():
        if platform.system() == 'Windows':
            ctypes.windll.kernel32.SetConsoleTitleW(arguments.command_name)
            # subprocess.run(['title', arguments.command_name], shell=True)  # pylint: disable=subprocess-run-check
        else:
            sys.stdout.write(f'\x1b]2;{arguments.command_name}\x07')

    arguments = parse_sys_argv()
    init_logging_to_file()
    SavedCommands(COMMANDS)

    if not arguments.command_name:
        print_help()
        return

    if arguments.command_name in COMMANDS:
        rename_terminal_title()
        command = map_command(arguments.command_name)
        handle_command(command, arguments)
    else:
        handle_unrecognized_command()


if __name__ == '__main__':
    main()
