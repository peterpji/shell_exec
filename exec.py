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

    def save_command(self):
        command_name = sys.argv[2]
        command_code = ' '.join(sys.argv[3:])

        self.saved_commands_dict[command_name] = command_code

        with open(self.saved_commands_path, 'w') as commands_file:
            json.dump(self.saved_commands_dict, commands_file, indent=4)

    def delete_command(self):
        command_name = sys.argv[2]
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


init_logs()
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
    'git-update': ['git checkout master', 'git stash', 'git pull', 'git stash pop', 'git branch --merged'],
}


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
        if platform.system() == 'Windows':
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
        ssh_path = os.path.join(system32, 'OpenSSH')
        env['PATH'] += ';' + ssh_path + ';'

        return env

    def run_command(command):
        if isinstance(command, (types.FunctionType, types.MethodType)):
            command()
        elif isinstance(command, str):
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

    saved_commands = SavedCommands()
    saved_commands.take_saved_commands_to_use(COMMANDS)

    if len(sys.argv) == 1:
        print_help()
        return

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
