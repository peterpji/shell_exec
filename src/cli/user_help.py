from typing import Dict, List

from src.command import Command


def print_help(commands: Dict[str, Command]):
    print(f'This is {__file__}')
    print()
    print(f'Available commands: {_parse_command_list_with_help(commands)}')
    print('For more information, use flag --help\n')


def handle_unrecognized_command(command_name: str, commands: Dict[str, Command]):
    similar_commands = {k: v for k, v in commands.items() if command_name in k}
    if similar_commands:
        print(f'Unrecognized command. Similar commands: {_parse_command_list_with_help(similar_commands)}\n')
        return
    print(f'Unrecognized command. Available commands: {_parse_command_list_with_help(commands)}\n')


def _parse_command_list_with_help(commands: Dict[str, Command]):
    def convert_to_cli_output_format(command_keys) -> List[str]:
        commands_parsed = []
        for command in command_keys:
            if commands[command].description:
                command = f'{command.ljust(25)} ; {commands[command].description}'
            commands_parsed.append(command)
        return commands_parsed

    command_keys = list(commands.keys())
    command_keys.sort()
    commands_string = '\n' + '\n'.join(convert_to_cli_output_format(command_keys))
    return commands_string
