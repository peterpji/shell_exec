import logging
import os
import platform
import subprocess
import sys
from multiprocessing import Process
from types import FunctionType, MethodType
from typing import Dict, List, Optional, Union

from .subprocess_executable import run_executable

try:
    import colorama  # A library fixing shell formating for windows.

    colorama.init()
except Exception:
    pass

command_low_level_type = Union[FunctionType, MethodType, str, list]


class Command:
    def __init__(
        self,
        command: command_low_level_type,
        description: Optional[str] = None,
        except_return_status: bool = False,
        parallel: bool = False,
    ) -> None:
        self.command = command
        self.arguments = None
        self.description = description
        self.except_return_status = except_return_status

        self.command_stack: List[Union[subprocess.CompletedProcess, subprocess.Popen, Process]] = []
        self.parallel = parallel

    @staticmethod
    def _get_patched_environ() -> Dict[str, str]:
        def win_add_ssh_to_path(env):
            system32 = os.path.join(os.environ['SystemRoot'], 'SysNative' if platform.architecture()[0] == '32bit' else 'System32')
            ssh_path = os.path.join(system32, 'OpenSSH')
            env['PATH'] += ';' + ssh_path

        env = os.environ.copy()
        if platform.system() == 'Windows':
            win_add_ssh_to_path(env)
        return env

    def _parse_str_command(self, sub_command: command_low_level_type = None):
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

    def execute(self) -> None:
        def check_all_sub_commands_are_complete():
            if not self.parallel:
                return
            _ = [c.join() for c in self.command_stack if isinstance(c, Process)]

        self._execute_sub_command(self.command)
        check_all_sub_commands_are_complete()

    def _execute_sub_command(self, sub_command: command_low_level_type) -> None:
        if isinstance(sub_command, list):
            for elem in sub_command:
                self.arguments = []
                self._execute_sub_command(elem)
            return

        if isinstance(sub_command, dict):
            Command(**sub_command).execute()
            return

        if isinstance(sub_command, (FunctionType, MethodType)):
            logging.info('Running: %s', sub_command)
            if self.parallel:
                # Using multiprocessing module has some drawbacks, mainly not being able to take user input anymore
                # Thus, it is only used when needed
                sub_process = Process(target=sub_command, args=self.arguments)
                sub_process.start()
                self.command_stack.append(sub_process)
                return
            sub_command(self.arguments)
            return

        if isinstance(sub_command, str):
            logging.info('Running: %s', sub_command)
            sub_command = self._parse_str_command(sub_command)
            common_kwargs = {'shell': True, 'env': self._get_patched_environ()}
            if self.parallel:
                process = Process(
                    target=run_executable,
                    args=[sub_command, self.except_return_status],
                    kwargs={**common_kwargs, 'index': len(self.command_stack)},
                )
                process.start()
                # TODO Notify user if parallel process exits with return_code != 0
            else:
                # Using "Process" here would standardize how the commands work but it would disable sys.stdin piping.
                process = run_executable(sub_command, self.except_return_status, stdin=sys.stdin, **common_kwargs)
            self.command_stack.append(process)
            return

        raise ValueError(f'Unknown command type {type(sub_command)}: {sub_command}')

    def __repr__(self, sub_command: command_low_level_type = None) -> str:
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
