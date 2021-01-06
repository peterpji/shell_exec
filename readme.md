# Purpose

# Config
There are multiple ways to configure the COMMANDS dict.  
Keys of the dict are the command names user can write to shell.  
Values are either executed in the shell (str) or python (functions, methods). Lists are also a valid data type and each list element is executed once.

# Security
WARNING: This script executes subprocess with a shell.  
It does not automatically validate shell inputs and thus should only be used locally.  
Otherwise this opens up a shell command injection vulnerability.
