import sys
from multiprocessing import Queue
from subprocess import Popen
from threading import Thread
from time import sleep
from typing import Optional


class ShellPrinterWrapper:
    def __init__(self, sub_process, print_prefix: Optional[int] = None) -> None:
        self.sub_process = sub_process
        self.print_prefix = print_prefix

        self.queue = Queue()
        self.stdout_reader = self._start_output_reader('stdout')
        self.stderr_reader = self._start_output_reader('stderr')

    def _start_output_reader(self, feed: str):
        output_reader = Thread(target=_reader, args=[self.sub_process, feed, self.queue, self.print_prefix])
        output_reader.start()
        return output_reader

    def _print_output_from_queue(self):
        if self.queue.empty():
            sleep(0.01)
            return False
        feed_type, line = self.queue.get()
        print(f'{line}', end='', file=getattr(sys, feed_type))
        return True

    def _output_print_loop(self):
        while self.stdout_reader.is_alive() or self.stderr_reader.is_alive() or not self.queue.empty():
            self._print_output_from_queue()
        self._print_output_from_queue()

    def start(self):
        self._output_print_loop()


def _reader(process: Popen, feed_type: str, queue: Queue, print_prefix: int):
    def read_line():
        line = getattr(process, feed_type).readline()
        if not line:
            return False

        line = print_prefix + line.decode()
        queue.put((feed_type, line))
        return True

    def read_rest_of_the_queue():
        while read_line():
            pass

    while process.poll() is None:
        new_line_printed = read_line()
        if not new_line_printed:
            sleep(0.01)

    sleep(0.01)
    read_rest_of_the_queue()
