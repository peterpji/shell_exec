import logging

from src.cli.ask_exec_confirmation import ask_exec_confirmation
from src.cli.parse_input_args import parse_input_args
from src.cli.prep_shell import prep_shell
from src.cli.rename_terminal_title import rename_terminal_title
from src.cli.user_help import handle_unrecognized_command, print_help
from src.get_commands_parsed import get_commands_parsed


def main():
    """
    WARNING: This script executes subprocess with a shell.
    It does not automatically validate shell inputs!
    Thus, it should only be used locally, otherwise this opens up a shell injection vulnerability.

    Use tips:
    If you need more help, run this script with --help flag.
    You can get this to your local PATH by installing this as a python package (run 'pip install .' on the project root directory).
    """
    commands = get_commands_parsed()
    prep_shell()

    arguments = parse_input_args(commands)

    if not arguments.command_name:
        print_help(commands)
        return

    if arguments.command_name not in commands:
        handle_unrecognized_command(arguments.command_name, commands)
        return

    rename_terminal_title(arguments.command_name)

    command = commands[arguments.command_name]
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
