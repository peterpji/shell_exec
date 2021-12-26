import logging
import os
import platform
import sys
from subprocess import PIPE, Popen
from types import FunctionType, MethodType
from typing import Any, Callable, Dict, Optional, Union

from exec.str_sub_command.printer import ShellPrinterWrapper

command_low_level_type = Union[FunctionType, MethodType, str, list]


def run_str_sub_command(command: str, **kwargs):
    return _run_str_sub_command(command, **kwargs)


def _run_str_sub_command(
    command: str,
    except_return_status: bool = False,
    parallel: bool = False,
    index: Optional[int] = None,
):
    def parallel_printer():
        print_prefix = '' if index is None else f'[{index}] '
        sub_command_with_printer = ShellPrinterWrapper(sub_command, print_prefix)
        sub_command_with_printer.start()
        assert sub_command.poll() is not None, 'Output printing loop should not exit before the process is done'

    kwargs = _get_popen_kwargs(parallel)
    with Popen(command, **kwargs) as sub_command:
        if not parallel:
            _keyboard_interrupt_handler(sub_command.wait, sub_command)
            return sub_command.returncode

        _keyboard_interrupt_handler(parallel_printer, sub_command)
        _handle_error(except_return_status, sub_command.returncode)
        return sub_command.returncode


def _handle_error(except_return_status: bool, return_code: int):
    if not except_return_status and return_code:
        sys.tracebacklimit = 0
        raise RuntimeError(f'Process returned with status code {return_code}')


def _keyboard_interrupt_handler(callback: Callable, sub_command: Popen[str]):
    try:
        callback()
    except KeyboardInterrupt:
        try:
            sub_command.terminate()
            logging.info('Terminated')
        except KeyboardInterrupt:
            sub_command.kill()
            logging.info('Killed')


def _get_popen_kwargs(parallel: bool) -> dict[str, Any]:
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
