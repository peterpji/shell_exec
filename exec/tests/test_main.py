import unittest
from unittest.mock import patch

from exec.command import Command
from exec.main import main
from exec.tests.utils import BaseTestClass, set_commands_base, patch_input


class TestBasicFunctionality(BaseTestClass):
    def test_passing_args(self):
        patch_input(['test-print', '123'])
        with set_commands_base({'test-print': Command('echo Working')}):
            main()
        self.assertEqual(self.mock_shell.call_args_list[0][0][0], 'echo Working 123')

    def test_list_ignores_args(self):
        patch_input(['test-print', '123'])

        expectation = ['echo Working once', 'echo Working twice']
        with set_commands_base({'test-print': Command(expectation)}):
            main()

        for call, expectation_elem in zip(self.mock_shell.call_args_list, expectation):
            self.assertEqual(call[0][0], expectation_elem)
        self.assertEqual(len(self.mock_shell.call_args_list), len(expectation))

    @patch('builtins.print')
    def test_print_command(self, mock_print):
        patch_input(['test-print', '--print'])
        with set_commands_base({'test-print': Command('echo Working')}):
            main()
        self.assertEqual(mock_print.call_args_list[0][0][0].command, 'echo Working')
        self.assertEqual(len(self.mock_shell.call_args_list), 0)


if __name__ == '__main__':
    unittest.main()
