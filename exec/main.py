import logging

from exec.cli.ask_exec_confirmation import ask_exec_confirmation
from exec.cli.parse_input_args import parse_input_args
from exec.cli.rename_terminal_title import rename_terminal_title
from exec.cli.user_help import handle_unrecognized_command, print_help
from exec.generate_commands import generate_commands

COMMANDS = generate_commands()


def main():
    """
    WARNING: This script executes subprocess with a shell.
    It does not automatically validate shell inputs!
    Thus, it should only be used locally, otherwise this opens up a shell injection vulnerability.

    Use tips:
    If you need more help, run this script with --help flag.
    You can get this to your local PATH by installing this as a python package (run 'pip install .' on the project root directory).
    """

    arguments = parse_input_args(COMMANDS)

    if not arguments.command_name:
        print_help(COMMANDS)
        return

    if arguments.command_name not in COMMANDS:
        handle_unrecognized_command(COMMANDS)
        return

    rename_terminal_title(arguments.command_name)

    command = COMMANDS[arguments.command_name]
    command.arguments = arguments.command_args

    if arguments.print:
        print(command)
        return

    if arguments.confirmation and not ask_exec_confirmation(command):
        logging.info('Command cancelled')
        return

    command.execute()


if __name__ == '__main__':
    main()
