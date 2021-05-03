import subprocess
import sys
from time import sleep
from typing import Optional


class SubprocessExecutable:
    def __init__(self, command: str, parallel: bool = False, index: Optional[int] = None, **common_kwargs) -> None:
        self.index = index
        self.content = ['', '']
        self.parallel = parallel

        if parallel:
            kwargs = {
                **common_kwargs,
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
            }
        else:
            kwargs = {
                **common_kwargs,
                'stdin': sys.stdin,
                'stdout': sys.stdout,
                'stderr': sys.stderr,
            }

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
        if not self.parallel:
            self.sub_command.wait()
            return self.sub_command.returncode

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
