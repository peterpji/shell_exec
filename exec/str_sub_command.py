from subprocess import Popen, PIPE
import sys
from multiprocessing import Queue
from threading import Thread
from time import sleep
from types import FunctionType, MethodType
from typing import Dict, List, Optional, Union
import os
import platform

command_low_level_type = Union[FunctionType, MethodType, str, list]


def reader(process: Popen, feed_type: str, queue: Queue, print_prefix: int):
    def read_line():
        line = getattr(process, feed_type).readline()
        if not line:
            return False
        line = print_prefix + line.decode()
        queue.put((feed_type, line))

        return True

    while process.poll() is None:
        if not read_line():
            sleep(0.01)
    sleep(0.01)
    while read_line():
        pass


class ShellPrinter:
    def __init__(self, sub_process, print_prefix: Optional[int] = None) -> None:
        self.sub_process = sub_process
        self.print_prefix = print_prefix

        self.queue = Queue()
        self.stdout_reader = self._start_output_reader('stdout')
        self.stderr_reader = self._start_output_reader('stderr')

    def _start_output_reader(self, feed: str):
        output_reader = Thread(target=reader, args=[self.sub_process, feed, self.queue, self.print_prefix])
        output_reader.start()
        return output_reader

    def _print_output_from_queue(self):
        if self.queue.empty():
            sleep(0.01)
            return False
        feed_type, line = self.queue.get()
        print(f"{line}", end='', file=getattr(sys, feed_type))
        return True

    def _output_print_loop(self):
        while self.stdout_reader.is_alive() or self.stderr_reader.is_alive() or not self.queue.empty():
            self._print_output_from_queue()
        self._print_output_from_queue()

    def start(self):
        self._output_print_loop()


def _get_patched_environ() -> Dict[str, str]:
    def win_add_ssh_to_path(env):
        system32 = os.path.join(os.environ['SystemRoot'], 'SysNative' if platform.architecture()[0] == '32bit' else 'System32')
        ssh_path = os.path.join(system32, 'OpenSSH')
        env['PATH'] += ';' + ssh_path

    env = os.environ.copy()
    if platform.system() == 'Windows':
        win_add_ssh_to_path(env)
    return env


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


class StrSubCommand:
    def __init__(
        self,
        command: str,
        except_return_status: bool = False,
        parallel: bool = False,
        index: Optional[int] = None,
    ) -> None:
        self.parallel = parallel
        self.except_return_status = except_return_status
        self.print_prefix = '' if index is None else f'[{index}] '

        subprocess_kwargs = {'shell': True, 'env': _get_patched_environ()}

        if parallel:
            kwargs = {
                **subprocess_kwargs,
                'stdout': PIPE,
                'stderr': PIPE,
            }
        else:  # Avoiding pipe has some benefits, e.g. printing with color to the console as a default on some software
            kwargs = {
                **subprocess_kwargs,
                'stdin': sys.stdin,
                'stdout': sys.stdout,
                'stderr': sys.stderr,
            }

        self.sub_command = Popen(command, **kwargs)  # pylint: disable=subprocess-run-check # nosec

    def _handle_error(self, return_code):
        if not self.except_return_status and return_code:
            sys.tracebacklimit = 0
            raise RuntimeError(f'Process returned with status code {return_code}')

    def __call__(self) -> None:
        if not self.parallel:
            self.sub_command.wait()
            return self.sub_command.returncode

        output_printer = ShellPrinter(self.sub_command, self.print_prefix)
        output_printer.start()

        assert self.sub_command.poll() is not None, 'Output printing loop should not exit before the process is done'
        self._handle_error(self.sub_command.returncode)
        return self.sub_command.returncode


def run_executable(command: str, **kwargs):
    executable = StrSubCommand(command, **kwargs)
    executable()
    return executable
