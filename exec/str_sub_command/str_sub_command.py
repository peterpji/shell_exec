import logging
import os
import platform
import sys
from subprocess import PIPE, Popen
from types import FunctionType, MethodType
from typing import Any, Dict, Optional, Union

from exec.str_sub_command.printer import ShellPrinter

command_low_level_type = Union[FunctionType, MethodType, str, list]


def run_str_sub_command(command: str, **kwargs):
    executable = StrSubCommand(command, **kwargs)
    executable()
    return executable


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

        kwargs = _parse_popen_kwargs(parallel)
        self.sub_command = Popen(command, **kwargs)  # pylint: disable=subprocess-run-check # nosec

    def _handle_error(self, return_code: int):
        if not self.except_return_status and return_code:
            sys.tracebacklimit = 0
            raise RuntimeError(f'Process returned with status code {return_code}')

    def __call__(self) -> None:
        def parallel_printer():
            output_printer.start()
            assert (
                self.sub_command.poll() is not None
            ), 'Output printing loop should not exit before the process is done'

        if not self.parallel:
            _keyboard_interrupt_handler(self.sub_command.wait, self.sub_command)
            return self.sub_command.returncode

        output_printer = ShellPrinter(self.sub_command, self.print_prefix)
        _keyboard_interrupt_handler(parallel_printer, self.sub_command)

        self._handle_error(self.sub_command.returncode)
        return self.sub_command.returncode


def _keyboard_interrupt_handler(callback, sub_command):
    try:
        callback()
    except KeyboardInterrupt:
        try:
            sub_command.terminate()
            logging.info('Terminated')
        except KeyboardInterrupt:
            sub_command.kill()
            logging.info('Killed')


def _parse_popen_kwargs(parallel: bool) -> dict[str, Any]:
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
    return kwargs


def _get_patched_environ() -> Dict[str, str]:
    def win_add_ssh_to_path(env):
        system32 = os.path.join(
            os.environ['SystemRoot'],
            'SysNative' if platform.architecture()[0] == '32bit' else 'System32',
        )
        ssh_path = os.path.join(system32, 'OpenSSH')
        env['PATH'] += ';' + ssh_path

    env = os.environ.copy()
    if platform.system() == 'Windows':
        win_add_ssh_to_path(env)
    return env
