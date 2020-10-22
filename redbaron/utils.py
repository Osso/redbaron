from io import StringIO
import logging
import sys

logger = logging.getLogger("redbaron")


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


def indent_str(block_of_text, indentation):
    """
    Helper function to indent a block of text.

    Take a block of text, an indentation string and return the indented block.
    """
    return "\n".join([indentation + line
                      for line in block_of_text.split("\n")]).rstrip(" ")


def deindent_str(block_of_text, indentation):
    """
    Helper function to indent a block of text.

    Take a block of text, an indentation string and return the indented block.
    """
    if not indentation:
        return block_of_text

    text = "\n".join([line[1:] if line.startswith(indentation[-1]) else line
                      for line in block_of_text.split("\n")])
    return deindent_str(text, indentation[:-1])


def truncate(text, n):
    if n < 5 or len(text) <= n:
        return text

    truncated = list(text)
    truncated[-3:-1] = ['.', '.', '.']
    del truncated[n-4:-4]
    return "".join(truncated)


def squash_successive_duplicates(iterable):
    previous = None
    for j in iterable:
        if j is previous:
            continue
        previous = j
        yield j
