import ctypes
import platform
import sys


def rename_terminal_title(command_name: str):
    """
    Sets the name of the command as the title of the command line window.
    """
    if platform.system() == 'Windows':
        ctypes.windll.kernel32.SetConsoleTitleW(command_name)
        # subprocess.run(['title', command_name], shell=True)  # pylint: disable=subprocess-run-check
    else:
        sys.stdout.write(f'\x1b]2;{command_name}\x07')
