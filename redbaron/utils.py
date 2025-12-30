from __future__ import annotations

import logging
import re
import sys
from collections.abc import Generator, Iterable
from io import StringIO
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from baron.utils import BaronBoundingBox

logger = logging.getLogger("redbaron")


def fix_baron_box(box: BaronBoundingBox) -> BaronBoundingBox:
    box.bottom_right.column += 1
    return box


def baron_type_from_class(cls: type) -> str:
    name = cls.__name__
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name.replace("Node", ""))
    computed_name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()
    return computed_name


def in_a_shell() -> bool:
    # the isinstance here is for building sphinx doc
    if isinstance(sys.stdout, StringIO):
        return True

    return sys.__stdin__.isatty()


def in_ipython() -> bool:
    import redbaron

    if redbaron.FORCE_IPYTHON_BEHAVIOR:
        return True

    try:
        __IPYTHON__  # type: ignore[name-defined]  # noqa: B018
    except NameError:
        return False
    return True


def indent_str(block_of_text: str, indentation: str) -> str:
    """
    Helper function to indent a block of text.

    Take a block of text, an indentation string and return the indented block.
    """
    return "\n".join([indentation + line if line else line for line in block_of_text.split("\n")]).rstrip(" ")


def deindent_str(block_of_text: str, indentation: str) -> str:
    """
    Helper function to deindent a block of text.

    Take a block of text, an indentation string and return the deindented block.
    """
    if not indentation:
        return block_of_text

    text = "\n".join([line[1:] if line.startswith(indentation[-1]) else line for line in block_of_text.split("\n")])
    return deindent_str(text, indentation[:-1])


def truncate(text: str, n: int) -> str:
    if n < 5 or len(text) <= n:
        return text

    truncated = list(text)
    truncated[-3:-1] = [".", ".", "."]
    del truncated[n - 4 : -4]
    return "".join(truncated)


def squash_successive_duplicates(iterable: Iterable[Any]) -> Generator[Any, None, None]:
    previous = None
    for j in iterable:
        if j is previous:
            continue
        previous = j
        yield j


def strip_comments(code: str) -> str:
    return "\n".join([line for line in code.split("\n") if not line.lstrip(" ").startswith("#")])
