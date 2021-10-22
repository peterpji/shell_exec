import os.path
from time import sleep
from typing import Dict

from exec.command import Command
from exec.saved_commands import SavedCommands

FILE_DIR = os.path.dirname(os.path.abspath(__file__))


def example_func(*args):
    print('This is a python test function which prints incoming arguments')
    print(args)


def long_py_func(*_):
    try:
        print('This is a long python command')
        sleep(2)
        print('Long python command done')
    except KeyboardInterrupt:
        pass


def generate_commands() -> Dict[str, Command]:
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
            if isinstance(command, Command):
                continue
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
            'command': for_py_repos(
                'flake8 --count --statistics --max-complexity=10 --ignore=W503,E203,E226,E402,E501'
            ),
            'except_return_status': True,
        },
        'isort': for_py_repos('isort --profile=black --line-length=150 .', cd=True),
        'pre-commit': {'command': for_py_repos('pre-commit run -a', cd=True), 'except_return_status': True},
        'pylint': f'cd {os.path.join(exec_repo, "..")} && python -m pylint --ignore=.eggs {exec_repo}',
        'safety': f'safety check --full-report --file={os.path.join(exec_repo, "requirements.txt")}',
    }

    commands_js_code_quality = {
        'eslint': {
            'command': for_js_repos('eslint ./src/ --fix --config=.eslintrc-fix', cd=True),
            'except_return_status': True,
        },
        'prettier': for_js_repos('prettier --write ./src/', cd=True),
        'npm-audit': for_js_repos('npm audit', cd=True),
    }

    commands = {
        # Setup
        'python-setup': Command(
            command=[
                'python -m pip install --upgrade pip',
                'python -m pip install --upgrade'
                ' bandit black coverage flake8 isort pre-commit pylint safety'  # Packages used in example commands
                ' virtualenv requests pandas jupyter aiohttp matplotlib',  # Other useful packages
            ],
            description='Upgrades pip, packages used by this tool and some other basic packages',
        ),
        # Docker
        'udev': 'docker attach ubuntu-dev',
        'udev-bash': 'docker exec -it ubuntu-dev /bin/bash',
        'udev-exec': 'docker exec -it ubuntu-dev',
        'udev-up': f'docker-compose --file={udev_yaml} up -d --force-recreate --always-recreate-deps',
        'udev-down': f'docker-compose --file={udev_yaml} down',
        'udev-build': f'docker-compose --file={udev_yaml} build',
        'udev-compose': f'docker-compose --file={udev_yaml}',
        # Other
        'test-print': Command(
            command='echo Working', description='Echoes "Working". Example of a hello world command.'
        ),
        'test-print-list': Command(
            command=['echo Working once', 'echo Working twice'], description='Runs multiple commands in row'
        ),
        'test-python': Command(
            command=example_func, description='Example of a python command. Echoes back given arguments object'
        ),
        'test-parallel': Command(
            command=[
                'echo Long call starting && timeout 1 > nul && echo Long call done',
                long_py_func,
                'echo Hi, am I interrupting?',
            ],
            parallel=True,
        ),
        'test-non-parallel': Command(
            command=[
                'echo Long call starting && timeout 1 > nul && echo Long call done',
                long_py_func,
                'echo Hi, am I interrupting?',
            ]
        ),
        'git-update': Command(
            command=['git checkout master', 'git stash', 'git pull', 'git stash pop', 'git branch --merged'],
            description='Shortcut for pulling git master with stashing',
        ),
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

    commands['js-quality'] = {
        'command': [
            commands_js_code_quality['npm-audit'],
            commands_js_code_quality['eslint'],
            commands_js_code_quality['prettier'],
        ],
        'except_return_status': True,
    }

    SavedCommands(commands)
    convert_to_command_objects(commands)

    return commands
