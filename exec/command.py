import logging
import os.path
import platform
import subprocess
import sys
from types import FunctionType, MethodType
from typing import Optional, Union


class Command:
    def __init__(
        self, command: Union[FunctionType, MethodType, str, list], except_return_status: bool = False, description: Optional[str] = None
    ) -> None:
        self.command = command
        self.except_return_status = except_return_status
        self.arguments = None
        self.description = description

    @staticmethod
    def _get_patched_environ():
        def win_add_ssh_to_path(env):
            system32 = os.path.join(os.environ['SystemRoot'], 'SysNative' if platform.architecture()[0] == '32bit' else 'System32')
            ssh_path = os.path.join(system32, 'OpenSSH')
            env['PATH'] += ';' + ssh_path

        env = os.environ.copy()
        if platform.system() == 'Windows':
            win_add_ssh_to_path(env)
        return env

    def _parse_str_command(self, sub_command=None):
        def localize_str_command(command):
            if platform.system() == 'Windows':
                command = command.replace('~', '%userprofile%')
            return command

        command = sub_command or self.command

        if not isinstance(command, str):
            raise ValueError('Command is not a string')

        command = ' '.join([command] + (self.arguments or []))
        command = localize_str_command(command)
        return command

    def execute(self, sub_command=None) -> None:

        command = sub_command or self.command

        if isinstance(command, list):
            for elem in command:
                self.execute(elem)
            return

        if isinstance(command, (FunctionType, MethodType)):
            logging.info('Running: %s', command)
            command(self.arguments)
            return

        if isinstance(command, str):
            logging.info('Running: %s', command)
            command = self._parse_str_command(command)
            command = command.split(' ')
            try:
                subprocess.run(  # pylint: disable=subprocess-run-check
                    command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, env=self._get_patched_environ(), shell=True
                ).check_returncode()
            except (subprocess.CalledProcessError, KeyboardInterrupt) as e:
                sys.tracebacklimit = 0
                if not self.except_return_status:
                    raise e
            return

        if isinstance(command, dict):
            Command(**command).execute()
            return

        raise ValueError(f'Unknown command type: {command}')

    def __repr__(self, sub_command=None) -> str:
        command = sub_command or self.command

        if isinstance(command, list):
            representation = ''
            for elem in command:
                representation += self.__repr__(elem) + '\n'
            return representation[:-1]

        if isinstance(command, dict):
            return Command(**command).__repr__()

        if isinstance(command, (FunctionType, MethodType)):
            return f'Python function: {self.command}; Args: {self.arguments}'

        if isinstance(command, str):
            command = self._parse_str_command(command)
            return command

        raise ValueError(f'Unknown command type: {command}')
