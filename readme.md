# Purpose

# Config
There are multiple ways to configure the COMMANDS dict.  
Keys of the dict are the command names user can write to shell.  
Values are either executed in the shell (str) or python (functions, methods). Lists are also a valid data type and each list element is executed once.

# Security
WARNING: This script executes subprocess with a shell.  
It does not automatically validate shell inputs and thus should only be used locally.  
Otherwise this opens up a shell command injection vulnerability.

# Valid command formats
* String: Interpreted as a shell command
* Python function or method with a single argument
    * Runs the function with argparse namespace as the argument. This namespace contains e.g. the command line arguments given.
* List: list of commands are run in order.
    * By default, stops the execution if any of the command raise an exception or return a non-zero exit code (shell).
* Dict: provides an option to input further flags.
    * The actual commands run are in key 'command'.
    * Currently implemented:
        * except_return_status: Ignore exceptions and non-zero exit codes when running a list of commands.
        * description: Printed with help texts
