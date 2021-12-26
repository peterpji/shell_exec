import os.path
from typing import Dict

from exec.command import Command
from exec.commands_dict import get_commands_base
from exec.saved_commands import add_saved_commands_functionality

FILE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_commands_parsed() -> Dict[str, Command]:
    """
    Check readme for valid command formats
    """

    commands = get_commands_base()
    commands = add_saved_commands_functionality(commands)
    commands = _convert_values_to_command_objects(commands)
    return commands


def _convert_values_to_command_objects(commands):
    commands_new = {}
    for command_name, command in commands.items():
        if isinstance(command, Command):
            command_parsed = command
        elif isinstance(command, dict):
            command_parsed = Command(**command)
        else:
            command_parsed = Command(command)
        commands_new[command_name] = command_parsed
    return commands_new
