import logging


def prep_shell():
    """
    This functions prepares shell for printing command outputs.
    E.g. some commands may have colorized outputs, which should be handled correctly.
    """
    try:
        import colorama  # A library fixing shell formating for windows.

        colorama.init()
    except Exception:
        logging.debug('Colorama not initialized')
