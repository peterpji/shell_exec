import json
import os
from typing import Dict, Tuple

from src.command import Command  # pylint: disable=unused-import # Used in type annotations

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_COMMANDS_PATH = os.path.join(FILE_DIR, 'saved_commands.json')


def add_saved_commands_functionality(commands_dict: Dict[str, Command]):
    saved_commands_dict = _load_saved_commands()
    saved_commands_management = _get_saved_commands_management_commands()
    return {**commands_dict, **saved_commands_dict, **saved_commands_management}


def _get_saved_commands_management_commands():
    use_commands = {
        'save-command': Command(
            command=_save_command,
            description='Syntax: save-command <command-name-without-spaces> <command line command>',
        ),
        'delete-command': Command(_delete_command),
    }
    return use_commands


def _delete_command(arguments: list) -> None:
    command_name = arguments[0]
    saved_commands_dict = _load_saved_commands()
    del saved_commands_dict[command_name]
    _save_to_file(saved_commands_dict)


def _save_command(arguments: list):
    def parse_arguments(arguments: list) -> Tuple[str, str]:
        command_name = arguments[0]
        command_code = ' '.join(arguments[1:])
        return command_name, command_code

    saved_commands_dict = _load_saved_commands()

    command_name, command_code = parse_arguments(arguments)
    saved_commands_dict[command_name] = Command(command=command_code)

    _ensure_directory_exists()
    _save_to_file(saved_commands_dict)


def _save_to_file(saved_commands_dict: Dict[str, Command]) -> None:
    saved_commands_dict_serialized = {k: v.command for k, v in saved_commands_dict.items()}
    with open(SAVED_COMMANDS_PATH, 'w', encoding='utf-8') as commands_file:
        json.dump(saved_commands_dict_serialized, commands_file, indent=4)


def _ensure_directory_exists() -> None:
    if not os.path.isdir(os.path.dirname(SAVED_COMMANDS_PATH)):
        os.mkdir(os.path.dirname(SAVED_COMMANDS_PATH))


def _load_saved_commands() -> Dict[str, Command]:
    if os.path.isfile(SAVED_COMMANDS_PATH):
        with open(SAVED_COMMANDS_PATH, encoding='utf-8') as commands_file:
            saved_commands_dict = json.load(commands_file)
    else:
        saved_commands_dict = {}

    saved_commands_dict = {
        command_name: Command(command=command_code) for command_name, command_code in saved_commands_dict.items()
    }
    return saved_commands_dict
