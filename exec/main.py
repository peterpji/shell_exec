import argparse
import ctypes
import logging
import os.path
import platform
import sys

from exec.command import Command
from exec.saved_commands import SavedCommands

FILE_DIR = os.path.dirname(os.path.abspath(__file__))


def example_func(*args):
    print('This is a python test function')
    print(args)


def generate_commands() -> dict:
    """
    Check readme for valid command formats
    """

    def for_repos(repo_list, command, cd=False):
        command_list = []
        for repo in repo_list:
            if cd:
                command_list.append(f'cd {repo} && ' + command)
            else:
                command_list.append(command + ' ' + repo)
        return command_list

    def for_py_repos(command, cd=False):
        py_repo_list = [exec_repo]
        return for_repos(py_repo_list, command, cd=cd)

    def for_js_repos(command, cd=False):
        py_repo_list = [exec_repo]
        return for_repos(py_repo_list, command, cd=cd)

    def convert_to_command_objects(commands):
        for command_name, command in commands.items():
            if isinstance(command, dict):
                commands[command_name] = Command(**command)
                continue
            commands[command_name] = Command(command)

    udev_yaml = os.path.join(FILE_DIR, '..', '..', 'docker', 'ubuntu_dev', 'docker-compose.yml')
    exec_repo = os.path.join(FILE_DIR, '..')

    commads_py_code_quality = {
        'bandit': {
            'command': for_py_repos('bandit --skip=B101,B404,B602 -r'),
            'except_return_status': True,
        },
        'black': for_py_repos('black --line-length=150 --skip-string-normalization --exclude=logs/'),
        'coverage': [f'python -m coverage run --source={exec_repo} -m unittest discover', 'python -m coverage report'],
        'flake8-show-stoppers': {  # Most critical issues
            'command': for_py_repos('flake8 --count --statistics --select=E9,F63,F7,F82 --show-source'),
            'except_return_status': True,
        },
        'flake8': {
            'command': for_py_repos('flake8 --count --statistics --max-complexity=10 --ignore=W503,E203,E226,E402,E501'),
            'except_return_status': True,
        },
        'isort': for_py_repos('isort --profile=black --line-length=150 .', cd=True),
        'pre-commit': {'command': for_py_repos('pre-commit run -a', cd=True), 'except_return_status': True},
        'pylint': f'cd {os.path.join(exec_repo, "..")} && python -m pylint --ignore=.eggs {exec_repo}',
        'safety': f'safety check --full-report --file={os.path.join(exec_repo, "requirements.txt")}',
    }

    commands_js_code_quality = {  # pylint: disable=unused-variable
        'eslint': {
            'command': for_js_repos('eslint ./src/** --fix --config=.eslintrc-fix', cd=True),
            'except_return_status': True,
        },
        'prettier': for_js_repos('prettier --write ./src/', cd=True),
        'npm-audit': for_js_repos('npm audit', cd=True),
    }

    commands = {
        # Setup
        'python-setup': {
            'command': [
                'python -m pip install --upgrade pip',
                'python -m pip install --upgrade'
                ' bandit black coverage flake8 isort pre-commit pylint safety'  # Packages used in example commands
                ' virtualenv requests pandas jupyter aiohttp matplotlib',  # Other useful packages
            ],
            'description': 'Upgrades pip, packages used by this tool and some other basic packages',
        },
        # Docker
        'udev': 'docker attach ubuntu-dev',
        'udev-bash': 'docker exec -it ubuntu-dev /bin/bash',
        'udev-exec': 'docker exec -it ubuntu-dev',
        'udev-up': f'docker-compose --file={udev_yaml} up -d --force-recreate --always-recreate-deps',
        'udev-down': f'docker-compose --file={udev_yaml} down',
        'udev-build': f'docker-compose --file={udev_yaml} build',
        'udev-compose': f'docker-compose --file={udev_yaml}',
        # Other
        'test-print': {'command': 'echo Working', 'description': 'Echoes "Working". Example of a hello world command.'},
        'test-print-list': {'command': ['echo Working once', 'echo Working twice'], 'description': 'Runs multiple commands in row'},
        'test-python': {'command': example_func, 'description': 'Example of a python command. Echoes back given arguments object'},
        'git-update': {
            'command': ['git checkout master', 'git stash', 'git pull', 'git stash pop', 'git branch --merged'],
            'description': 'Shortcut for pulling git master with stashing',
        },
    }

    commands['py-quality'] = {
        'command': [
            commads_py_code_quality['isort'],
            commads_py_code_quality['black'],
            commads_py_code_quality['flake8'],
            commads_py_code_quality['pylint'],
            commads_py_code_quality['pre-commit'],
            commads_py_code_quality['safety'],
            commads_py_code_quality['bandit'],
        ],
        'except_return_status': True,
    }

    SavedCommands(commands)
    convert_to_command_objects(commands)

    return commands


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

    def ask_confirmation_from_user(command):
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
