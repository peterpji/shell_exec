import os
import sys
import unittest
from contextlib import contextmanager
from io import StringIO
from unittest.mock import patch

from exec.main import main


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def patch_input(inputs: list[str]):
    return patch('exec.main.sys.argv', [os.path.join(os.path.dirname(__file__), 'exec.py'), *inputs])


def patch_popen(*args, **kwargs):
    return patch('exec.str_sub_command.str_sub_command.Popen')(*args, **kwargs)


class TestBasicFunctionality(unittest.TestCase):
    @patch_input(['test-print'])
    @patch_popen
    def test_single_command(self, mock_shell):
        main()
        self.assertEqual(mock_shell.call_args_list[0][0][0], 'echo Working')

    @patch_input(['test-print', '123'])
    @patch_popen
    def test_single_command_with_args(self, mock_shell):
        main()
        self.assertEqual(mock_shell.call_args_list[0][0][0], 'echo Working 123')

    @patch_input(['test-print-list'])
    @patch_popen
    def test_list(self, mock_shell):
        main()

        expectation = ['echo Working once', 'echo Working twice']

        for call, expectation_elem in zip(mock_shell.call_args_list, expectation):
            self.assertEqual(call[0][0], expectation_elem)
        self.assertEqual(len(mock_shell.call_args_list), len(expectation))

    @patch_input(['test-print-list', '123'])
    @patch_popen
    def test_list_with_args(self, mock_shell):
        main()

        expectation = ['echo Working once', 'echo Working twice']

        for call, expectation_elem in zip(mock_shell.call_args_list, expectation):
            self.assertEqual(call[0][0], expectation_elem)
        self.assertEqual(len(mock_shell.call_args_list), len(expectation))

    @patch_input(['test-print', '--print'])
    @patch('builtins.print')
    def test_print_command(self, mock_print):
        main()
        self.assertEqual(mock_print.call_args_list[0][0][0].command, 'echo Working')


if __name__ == '__main__':
    unittest.main()
