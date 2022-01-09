import unittest

from exec.command import Command
from exec.main import main
from exec.tests.utils import BaseTestClass, patch_input, set_commands_base


class TestBasicFunctionality(BaseTestClass):
    @patch_input(['test-print'])
    def test_command_class(self):
        with set_commands_base({'test-print': Command('echo Working')}):
            main()
        self.assertEqual(self.mock_shell.call_args_list[0][0][0], 'echo Working')

    @patch_input(['test-print'])
    def test_dict(self):
        with set_commands_base({'test-print': {'command': 'echo Working'}}):
            main()
        self.assertEqual(self.mock_shell.call_args_list[0][0][0], 'echo Working')

    @patch_input(['test-print'])
    def test_str(self):
        with set_commands_base({'test-print': 'echo Working'}):
            main()
        self.assertEqual(self.mock_shell.call_args_list[0][0][0], 'echo Working')

    @patch_input(['test-print'])
    def test_list(self):
        expectation = ['echo Working once', 'echo Working twice']
        with set_commands_base({'test-print': Command(expectation)}):
            main()

        for call, expectation_elem in zip(self.mock_shell.call_args_list, expectation):
            self.assertEqual(call[0][0], expectation_elem)
        self.assertEqual(len(self.mock_shell.call_args_list), len(expectation))


if __name__ == '__main__':
    unittest.main()
