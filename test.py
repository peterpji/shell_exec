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


class TestBasicFunctionality(unittest.TestCase):
    def test_single_command(self):
        with patch('exec.sys.argv', [os.path.join(os.path.dirname(__file__), 'exec.py'), 'test-print']):
            main()

    def test_list(self):
        with patch('exec.sys.argv', [os.path.join(os.path.dirname(__file__), 'exec.py'), 'test-print-list']):
            main()

    def test_print_command(self):
        with patch('exec.sys.argv', [os.path.join(os.path.dirname(__file__), 'exec.py'), 'test-print', '--print']):
            with patch('builtins.print') as out:
                main()
        self.assertEqual(out.call_args_list[0][0][0], 'echo Working')


if __name__ == '__main__':
    unittest.main()
