import os.path
from time import sleep

from exec.command import Command

FILE_DIR = os.path.dirname(os.path.abspath(__file__))


def _example_func(*args):
    print('This is a python test function which prints incoming arguments')
    print(args)


def _long_py_func(*_):
    try:
        print('This is a long python command')
        sleep(2)
        print('Long python command done')
    except KeyboardInterrupt:
        pass


def get_commands_base():
    udev_yaml = os.path.join(FILE_DIR, '..', '..', 'docker', 'ubuntu_dev', 'docker-compose.yml')

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
            command=_example_func, description='Example of a python command. Echoes back given arguments object'
        ),
        'test-parallel': Command(
            command=[
                'echo Long call starting && timeout 1 > nul && echo Long call done',
                _long_py_func,
                'echo Hi, am I interrupting?',
            ],
            parallel=True,
        ),
        'test-non-parallel': Command(
            command=[
                'echo Long call starting && timeout 1 > nul && echo Long call done',
                _long_py_func,
                'echo Hi, am I interrupting?',
            ]
        ),
        'git-update': Command(
            command=['git checkout master', 'git stash', 'git pull', 'git stash pop', 'git branch --merged'],
            description='Shortcut for pulling git master with stashing',
        ),
    }

    return commands
