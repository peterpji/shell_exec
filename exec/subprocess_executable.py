import subprocess
import sys
from multiprocessing import Queue
from threading import Thread
from time import sleep
from typing import Optional


def _format_line(line, index):
    return line if index is None else f'[{index}] {line}'


def reader(process: subprocess.Popen, feed_type: str, queue: Queue, index: int):
    while process.poll() is None:
        line = getattr(process, feed_type).readline()
        if not line:
            sleep(0.01)
            continue
        line = _format_line(line.decode(), index)
        queue.put((feed_type, line))


class SubprocessExecutable:
    queue: Queue
    stdout_reader: Thread
    stderr_reader: Thread

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
        else:  # Avoiding pipe has some benefits, e.g. printing with color to the console
            kwargs = {
                **common_kwargs,
                'stdin': sys.stdin,
                'stdout': sys.stdout,
                'stderr': sys.stderr,
            }

        self.sub_command = subprocess.Popen(command, **kwargs)  # pylint: disable=subprocess-run-check # nosec

    def _start_output_reader(self, feed: str):
        output_reader = Thread(target=reader, args=[self.sub_command, feed, self.queue, self.index])
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
            if self._print_output_from_queue():
                sleep(0.01)
                continue

    def __call__(self) -> None:
        if not self.parallel:
            self.sub_command.wait()
            return self.sub_command.returncode

        self.queue = Queue()
        self.stdout_reader = self._start_output_reader('stdout')
        self.stderr_reader = self._start_output_reader('stderr')

        self._output_print_loop()

        assert self.sub_command.poll() is not None, 'Output printing loop should not exit before the process is done'
        return self.sub_command.returncode


def run_executable(command: str, except_return_status: bool, **kwargs):
    executable = SubprocessExecutable(command, **kwargs)
    return_code = executable()
    if not except_return_status and return_code:
        sys.tracebacklimit = 0
        raise RuntimeError(f'Process returned with status code {return_code}')
    return executable
