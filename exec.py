# Windows PowerShell:   shell | Invoke-Expression
# Unix Bash:            eval $(python3 shell.py)
# All:                  python3 shell.py | <bash / cmd / powershell>
import sys
import os.path
import platform
import subprocess
import logging
import types
import json
import argparse


def init_logs():
    log_file_path = os.path.join(os.path.dirname(__file__), 'logs', 'exec.log')
    logging.basicConfig(
        filename=log_file_path, filemode="a", format="%(levelname)s:%(name)s:%(asctime)s:%(message)s", datefmt='%Y-%m-%d %H:%M:%S', level='INFO'
    )
    logging.info('##### NEW RUN #####')
    logging.info('New run args: %s', sys.argv)


def clean_sys_args():
    if 'exec-py' in sys.argv:
        sys.argv.pop(sys.argv.index('run-py'))


def get_sys_arg(index):
    if len(sys.argv) >= index + 1:
        return sys.argv[index]
    else:
        return ''


def get_rest_sys_args(index):
    if len(sys.argv) >= index + 1:
        return ' ' + ' '.join(sys.argv[index:])
    else:
        return ''


def load_saved_commands():
    saved_commands_path = os.path.join(os.path.dirname(__file__), 'saved_commands.json')
    if os.path.isfile(saved_commands_path):
        with open(saved_commands_path) as saved_commands:
            command_json = json.load(saved_commands)
    else:
        command_json = {}
    return command_json, saved_commands_path


def save_command():
    command_name = sys.argv[2]
    command_code = ' '.join(sys.argv[3:])

    command_json, saved_commands_path = load_saved_commands()
    command_json[command_name] = command_code

    with open(saved_commands_path, 'w') as saved_commands:
        json.dump(command_json, saved_commands, indent=4)


def delete_command():
    command_name = sys.argv[2]
    command_json, saved_commands_path = load_saved_commands()

    del command_json[command_name]

    with open(saved_commands_path, 'w') as saved_commands:
        json.dump(command_json, saved_commands)


init_logs()
clean_sys_args()
COMMANDS = {
    # Setup
    'python-setup': 'python -m pip install --upgrade pip & python -m pip install --upgrade virtualenv pandas jupyter notebook aiohttp requests matplotlib',
    # Docker
    'udev': 'docker attach ubuntu-dev',
    'udev-bash': 'docker exec -it ubuntu-dev /bin/bash',
    'udev-up': 'docker-compose --file C:/Users/peter/OneDrive/MyOneDrive/Code/docker/ubuntu_dev/docker-compose.yml up -d --force-recreate',
    'udev-down': 'docker-compose --file C:/Users/peter/OneDrive/MyOneDrive/Code/docker/ubuntu_dev/docker-compose.yml down',
    'udev-build': 'docker-compose --file C:/Users/peter/OneDrive/MyOneDrive/Code/docker/ubuntu_dev/docker-compose.yml build',
    # Other
    'test-print': 'echo Working',
    'git-update': 'git checkout master && git stash && git pull && git stash pop && git branch --merged',
    'save-command': save_command,
    'delete-command': delete_command,
}


def take_saved_commands_to_use():
    saved_commands = load_saved_commands()[0]
    COMMANDS.update(saved_commands)


def command_list(as_string=False):
    commands = list(COMMANDS.keys())
    commands.sort()

    if as_string:
        commands = '\n' + '\n'.join(commands)

    return commands


def print_help():
    sys.stdout.write(f'This is {__file__}\n')
    sys.stdout.write(f'Available commands: {command_list(as_string=True)}\n')


def handle_unrecognized_command():
    sys.stdout.write(f'Unrecognized command. Available commands: {command_list(as_string=True)}\n')


def formulate_command():
    def localize_command(command):
        command = command.replace('~', '%userprofile%')
        return command

    command = COMMANDS[sys.argv[1]]

    if isinstance(command, str):
        command = localize_command(command)

    return command


def run_command(command, confirmation=True):
    def ask_confirmation_from_user():
        conf = ''
        while conf.lower() not in ['y', 'n']:
            conf = input(command + '\nDo you want to run? (y/n) ')

            if conf.lower() == 'n':
                sys.stdout.write('Command cancelled\n')

        return conf.lower() == 'y'

    def patch_environ():
        env = os.environ.copy()

        system32 = os.path.join(os.environ['SystemRoot'], 'SysNative' if platform.architecture()[0] == '32bit' else 'System32')
        # ssh_path = os.path.join(system32, 'OpenSSH', 'ssh.exe')
        ssh_path = os.path.join(system32, 'OpenSSH')
        env['PATH'] += ';' + ssh_path + ';'

        return env

    def run_command(command):
        if isinstance(command, types.FunctionType):
            command()
        elif isinstance(command, str):
            command = command.split(' ')
            subprocess.run(  # pylint: disable=subprocess-run-check
                command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, env=patch_environ(), shell=True
            )
        elif isinstance(command, list):
            for elem in command:
                run_command(elem)
        else:
            logging.warning('Unknown command type')

    if isinstance(command, str):
        command = command + get_rest_sys_args(2)

    if confirmation and not ask_confirmation_from_user():
        logging.info('Command cancelled')
        return

    logging.info('Running: %s', command)
    run_command(command)


def print_command(command):
    if isinstance(command, types.FunctionType):
        print(f'Python function {command}')
    else:
        del sys.argv[sys.argv.index('--print')]
        if len(sys.argv) > 2:
            command = ' '.join([command] + sys.argv[2:])
        sys.stdout.write(command)


def main(arguments):
    """
    WARNING: This script does not automatically validate shell inputs and thus should only be used locally.

    Notes:
    If you want to run this from the command line with just the file name without extension, add ".py;" to the environment variable PATHTEXT
    """

    if len(sys.argv) == 1:
        print_help()
        return

    take_saved_commands_to_use()

    if sys.argv[1] in COMMANDS:
        command = formulate_command()
        if arguments.print:
            print_command(command)
        else:
            run_command(command, confirmation=arguments.confirmation)
    else:
        handle_unrecognized_command()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.description = f'This is a tool for abstracting long to write or complicated shell commands. Available commands: {command_list()}'
    parser.add_argument('--print', action='store_true', default=False, help='Print out the command instead of executing')
    parser.add_argument('--confirmation', action='store_true', default=False, help='Print the command and ask for confirmation before executing')
    arguments, _ = parser.parse_known_args()
    main(arguments)
