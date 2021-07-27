import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass
class Arguments:
    print: bool
    confirmation: bool
    command_name: Optional[str]
    command_args: list[str]


def parse_sys_args(get_command_list) -> Arguments:
    parser = argparse.ArgumentParser()
    parser.description = f'This is a tool for abstracting long to write or complicated shell commands. Available commands: {get_command_list()}'
    parser.add_argument('--print', action='store_true', default=False, help='Print out the command instead of executing')
    parser.add_argument('--confirmation', action='store_true', default=False, help='Print the command and ask for confirmation before executing')
    parser.add_argument('command_name', nargs='?')
    parser.add_argument('command_args', nargs='*')
    arguments, unknown_kwargs = parser.parse_known_args()
    arguments.command_args += unknown_kwargs
    return Arguments(**arguments.__dict__)
