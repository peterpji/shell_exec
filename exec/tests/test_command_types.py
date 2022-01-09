import unittest

from exec.command import Command
from exec.main import main
from exec.tests.utils import BaseTestClass, patch_input, set_commands_base


class TestBasicFunctionality(BaseTestClass):
    def test_command_class(self):
        patch_input(['test-print'])
        with set_commands_base({'test-print': Command('echo Working')}):
            main()
        self.assertEqual(self.mock_shell.call_args_list[0][0][0], 'echo Working')

    def test_dict(self):
        patch_input(['test-print'])
        with set_commands_base({'test-print': {'command': 'echo Working'}}):
            main()
        self.assertEqual(self.mock_shell.call_args_list[0][0][0], 'echo Working')

    def test_str(self):
        patch_input(['test-print'])
        with set_commands_base({'test-print': 'echo Working'}):
            main()
        self.assertEqual(self.mock_shell.call_args_list[0][0][0], 'echo Working')

    def test_list(self):
        patch_input(['test-print'])
        expectation = ['echo Working once', 'echo Working twice']
        with set_commands_base({'test-print': Command(expectation)}):
            main()

        for call, expectation_elem in zip(self.mock_shell.call_args_list, expectation):
            self.assertEqual(call[0][0], expectation_elem)
        self.assertEqual(len(self.mock_shell.call_args_list), len(expectation))


if __name__ == '__main__':
    unittest.main()
