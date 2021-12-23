import json
import os
from typing import Dict, Tuple

from exec.command import Command  # pylint: disable=unused-import # Used in type annotations

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_COMMANDS_PATH = os.path.join(FILE_DIR, 'saved_commands.json')


class SavedCommands:
    def __init__(self, commands_dict: Dict[str, Command]):
        """
        Initialization adds save_command and delete_command methods to the commands_dict
        """

        self.external_commands_dict = commands_dict
        self.saved_commands_dict = self._load_saved_commands()
        self._take_saved_commands_to_use()

    def save_command(self, arguments: list):
        command_name, command_code = self._parse_arguments(arguments)
        self.saved_commands_dict[command_name] = command_code

        self._ensure_directory_exists()
        self._save_to_file()
        self._take_saved_commands_to_use()

    @staticmethod
    def _parse_arguments(arguments: list) -> Tuple[str, str]:
        command_name = arguments[0]
        command_code = ' '.join(arguments[1:])
        return command_name, command_code

    @staticmethod
    def _ensure_directory_exists() -> None:
        if not os.path.isdir(os.path.dirname(SAVED_COMMANDS_PATH)):
            os.mkdir(os.path.dirname(SAVED_COMMANDS_PATH))

    def delete_command(self, arguments: list) -> None:
        command_name = arguments[0]
        del self.saved_commands_dict[command_name]

        self._save_to_file()
        self._take_saved_commands_to_use()

    def _save_to_file(self) -> None:
        with open(SAVED_COMMANDS_PATH, 'w') as commands_file:
            json.dump(self.saved_commands_dict, commands_file, indent=4)

    @staticmethod
    def _load_saved_commands() -> Dict[str, str]:
        if os.path.isfile(SAVED_COMMANDS_PATH):
            with open(SAVED_COMMANDS_PATH) as commands_file:
                saved_commands_dict = json.load(commands_file)
        else:
            saved_commands_dict = {}
        return saved_commands_dict

    def _take_saved_commands_to_use(self) -> None:
        use_commands = {
            'save-command': Command(
                command=self.save_command,
                description='Syntax: save-command <command-name-without-spaces> <command line command>',
            ),
            'delete-command': Command(self.delete_command),
        }
        self.external_commands_dict.update(use_commands)
        saved_commands_dict = {
            command_name: Command(command=command_code)
            for command_name, command_code in self.saved_commands_dict.items()
        }
        self.external_commands_dict.update(saved_commands_dict)
