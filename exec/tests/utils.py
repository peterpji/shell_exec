import sys
from contextlib import contextmanager
import unittest
from unittest.mock import MagicMock, patch


def patch_input(inputs: list[str]):
    sys.argv = [sys.argv[0]] + inputs


@contextmanager
def set_commands_base(commands_base):
    get_commands_base_mock = MagicMock()
    get_commands_base_mock.return_value = commands_base
    patcher = patch('exec.get_commands_parsed.get_commands_base', new=get_commands_base_mock)
    try:
        patcher.start()
        yield
    finally:
        patcher.stop()


class BaseTestClass(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_shell = MagicMock()
        patch('exec.str_sub_command.str_sub_command.Popen', self.mock_shell).start()
        return super().setUp()
