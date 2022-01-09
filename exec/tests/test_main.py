import unittest
from unittest.mock import patch

from exec.command import Command
from exec.main import main
from exec.tests.utils import BaseTestClass, set_commands_base, patch_input


class TestBasicFunctionality(BaseTestClass):
    @patch_input(['test-print'])
    def test_single_command(self):
        with set_commands_base({'test-print': Command('echo Working')}):
            main()
        self.assertEqual(self.mock_shell.call_args_list[0][0][0], 'echo Working')

    @patch_input(['test-print', '123'])
    def test_single_command_with_args(self):
        with set_commands_base({'test-print': Command('echo Working')}):
            main()
        self.assertEqual(self.mock_shell.call_args_list[0][0][0], 'echo Working 123')

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
        self.assertEqual(len(self.mock_shell.call_args_list), 0)


if __name__ == '__main__':
    unittest.main()