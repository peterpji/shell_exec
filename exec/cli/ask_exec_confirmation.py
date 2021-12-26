from exec.command import Command


def ask_exec_confirmation(command: Command):
    conf = ''
    while conf.lower() not in ['y', 'n']:
        print(command)
        conf = input('Do you want to run? (y/n): ')

        if conf.lower() == 'n':
            print('Command cancelled')
        elif conf.lower() == 'y':
            print('Running command')
        else:
            print('Input not in (y/n)')

    return conf.lower() == 'y'
