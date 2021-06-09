import logging
import platform
import subprocess
from multiprocessing import Process
from types import FunctionType, MethodType
from typing import List, Optional, Union

from exec.str_sub_command.str_sub_command import run_str_sub_command

try:
    import colorama  # A library fixing shell formating for windows.

    colorama.init()
except Exception:
    logging.debug('Colorama not initialized')

command_low_level_type = Union[FunctionType, MethodType, str, list]


def _parse_str_command(str_sub_command: str, arguments: Optional[List[str]] = None):
    def localize_str_command(str_sub_command):
        if platform.system() == 'Windows':
            str_sub_command = str_sub_command.replace('~', '%userprofile%')
        return str_sub_command

    if not isinstance(str_sub_command, str):
        raise ValueError('Command is not a string')

    arguments = arguments or []

    str_sub_command = ' '.join([str_sub_command] + arguments)
    str_sub_command = localize_str_command(str_sub_command)
    return str_sub_command


class Command:
    arguments: Optional[List[str]]

    def __init__(
        self,
        command: command_low_level_type,
        description: Optional[str] = None,
        except_return_status: bool = False,
        parallel: bool = False,
    ) -> None:
        self.command = command
        self.description = description
        self.except_return_status = except_return_status
        self.parallel = parallel
        self.arguments = None

        self.command_stack: List[Union[subprocess.CompletedProcess, subprocess.Popen, Process]] = []

    def execute(self) -> None:
        def check_all_sub_commands_are_complete():
            if not self.parallel:
                return
            try:
                _ = [command.join() for command in self.command_stack if isinstance(command, Process)]
            except KeyboardInterrupt:
                print('Terminate command sent to the processes. Waiting for graceful exit')
                try:
                    _ = [command.join() for command in self.command_stack if isinstance(command, Process)]
                except KeyboardInterrupt:
                    print('Kill command sent to the processes. Waiting for exit')
                    _ = [command.join() for command in self.command_stack if isinstance(command, Process)]

        self._execute_sub_command(self.command)
        check_all_sub_commands_are_complete()

    def _execute_sub_command(self, sub_command: command_low_level_type) -> None:
        if isinstance(sub_command, Command):
            sub_command.execute()
            return

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
            sub_command = _parse_str_command(sub_command, self.arguments)
            if self.parallel:
                process = Process(
                    target=run_str_sub_command,
                    args=[sub_command],
                    kwargs={
                        'parallel': self.parallel,
                        'except_return_status': self.except_return_status,
                        'index': len(self.command_stack),
                    },
                )
                process.start()
                # TODO Notify user if parallel process exits with return_code != 0
            else:
                # Using "Process" here would standardize how the commands work but it would disable sys.stdin piping.
                process = run_str_sub_command(
                    sub_command,
                    except_return_status=self.except_return_status,
                    parallel=self.parallel,
                )
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

        if isinstance(command, Command):
            return command.__repr__()

        if isinstance(command, (FunctionType, MethodType)):
            return f'Python function: {self.command}; Args: {self.arguments}'

        if isinstance(command, str):
            command = _parse_str_command(command, self.arguments)
            return command

        raise ValueError(f'Unknown command type: {type(command)}')
