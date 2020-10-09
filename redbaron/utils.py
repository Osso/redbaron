from io import StringIO
import logging
import re
import sys

logger = logging.getLogger("redbaron")


def baron_type_to_redbaron_classname(baron_type):
    return "".join(map(lambda x: x.capitalize(), baron_type.split("_"))) + "Node"


def redbaron_classname_to_baron_type(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name.replace("Node", ""))
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def log(msg, *args):
    logger.DEBUG(msg, *args)


def in_a_shell():
    # the isinstance here is for building sphinx doc
    if isinstance(sys.stdout, StringIO):
        return True

    return sys.__stdin__.isatty()


def in_ipython():
    import redbaron

    if redbaron.force_ipython_behavior:
        return True

    try:
        __IPYTHON__
    except NameError:
        return False
    else:
        return True


def indent(block_of_text, indentation):
    """
    Helper function to indent a block of text.

    Take a block of text, an indentation string and return the indented block.
    """
    return "\n".join([indentation + line
                      for line in block_of_text.splitlines()])


def truncate(text, n):
    if n < 5 or len(text) <= n:
        return text

    truncated = list(text)
    truncated[-3:-1] = ['.', '.', '.']
    del truncated[n-4:-4]
    return "".join(truncated)


def display_property_atttributeerror_exceptions(function):
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except AttributeError:
            import traceback
            traceback.print_exc()
            raise

    return wrapper
