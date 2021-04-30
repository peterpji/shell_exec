import logging
import os
import platform
import subprocess
import sys
from multiprocessing import Process
from time import sleep
from types import FunctionType, MethodType
from typing import Dict, List, Optional, Union

try:
    import colorama  # A library fixing shell formating for windows.

    colorama.init()
except Exception:
    pass

command_low_level_type = Union[FunctionType, MethodType, str, list]


class SubprocessExecutable:
    def __init__(self, command: str, stdin: bool = False, index: Optional[int] = None, **common_kwargs) -> None:
        self.index = index
        self.content = ['', '']

        kwargs = {'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE, **common_kwargs}
        if stdin:
            kwargs['stdin'] = sys.stdin
        self.sub_command = subprocess.Popen(command, **kwargs)  # pylint: disable=subprocess-run-check # nosec

    def _format_line(self, content):
        return content if self.index is None else f'[{self.index}] {content}'

    def print_if_content(self, source, dest, content_index):
        new_output: str = source.read1().decode()
        self.content[content_index] += new_output
        if '\n' not in self.content[content_index]:
            return
        sections = self.content[content_index].split('\n')
        line_to_print = self._format_line(sections[0])
        print(line_to_print, file=dest)
        self.content[content_index] = self.content[content_index].replace(sections[0] + '\n', '', 1)

    def print_rest(self, source, dest, content_index):
        new_output: str = source.read1().decode()
        self.content[content_index] += new_output
        if not self.content[content_index]:
            return
        line_to_print = self._format_line(self.content[content_index])
        print(line_to_print, file=dest)

    def __call__(self) -> None:
        stdout_args = [self.sub_command.stdout, sys.stdout, 0]
        stderr_args = [self.sub_command.stderr, sys.stderr, 1]
        while self.sub_command.poll() is None:
            sleep(0.01)
            self.print_if_content(*stdout_args)
            self.print_if_content(*stderr_args)
        self.print_rest(*stdout_args)
        self.print_rest(*stderr_args)
        return self.sub_command.returncode


def run_executable(command: str, except_return_status: bool, **kwargs):
    executable = SubprocessExecutable(command, **kwargs)
    return_code = executable()
    if not except_return_status and return_code:
        sys.tracebacklimit = 0
        raise RuntimeError(f'Process returned with status code {return_code}')
    return executable


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

        raise ValueError(f'Unknown command type: {sub_command}')

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
