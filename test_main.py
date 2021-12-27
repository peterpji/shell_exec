import sys
import unittest
from unittest.mock import MagicMock, patch
from functools import wraps
from exec.command import Command

from exec.main import main


def patch_input(inputs: list[str]):
    def make_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            sys.argv = [sys.argv[0]] + inputs
            func(*args, **kwargs)

        return wrapper

    return make_wrapper


def set_commands_base(commands_base):
    get_commands_base_mock = patch('exec.get_commands_parsed.get_commands_base')
    get_commands_base_mock.return_value = commands_base
    get_commands_base_mock.start()


class TestBasicFunctionality(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_shell = MagicMock()
        patch('exec.str_sub_command.str_sub_command.Popen', self.mock_shell).start()
        return super().setUp()

    @patch_input(['test-print'])
    def test_single_command(self):
        set_commands_base({'test-print': Command('echo Working')})
        main()
        self.assertEqual(self.mock_shell.call_args_list[0][0][0], 'echo Working')

    @patch_input(['test-print', '123'])
    def test_single_command_with_args(self):
        main()
        self.assertEqual(self.mock_shell.call_args_list[0][0][0], 'echo Working 123')

    @patch_input(['test-print-list'])
    def test_list(self):
        main()

        expectation = ['echo Working once', 'echo Working twice']

        for call, expectation_elem in zip(self.mock_shell.call_args_list, expectation):
            self.assertEqual(call[0][0], expectation_elem)
        self.assertEqual(len(self.mock_shell.call_args_list), len(expectation))

    @patch_input(['test-print-list', '123'])
    def test_list_with_args(self):
        main()

        expectation = ['echo Working once', 'echo Working twice']

        for call, expectation_elem in zip(self.mock_shell.call_args_list, expectation):
            self.assertEqual(call[0][0], expectation_elem)
        self.assertEqual(len(self.mock_shell.call_args_list), len(expectation))

    @patch_input(['test-print', '--print'])
    @patch('builtins.print')
    def test_print_command(self, mock_print):
        main()
        self.assertEqual(mock_print.call_args_list[0][0][0].command, 'echo Working')


if __name__ == '__main__':
    unittest.main()
