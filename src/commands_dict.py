import os.path
from time import sleep

from src.command import Command

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
        # Docker
        'udev': f'docker-compose --file={udev_yaml}',
        'udev-here': 'docker run --volume=${PWD}:/docker_mount/code --rm -it --name=udev ubuntu_dev_shell bash',
        'udev-attach': 'docker attach ubuntu-dev',
        'udev-logs': 'docker logs -f --tail 10 ubuntu-dev',
        'udev-exec': 'docker exec -it ubuntu-dev',
        # Other
        'git-update': Command(
            command=['git checkout master', 'git stash', 'git pull', 'git stash pop', 'git branch --merged'],
            description='Shortcut for pulling git master with stashing',
        ),
    }

    test_commands = {
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
    }

    return {**commands, **test_commands}
