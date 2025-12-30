from __future__ import annotations

from typing import TYPE_CHECKING

from .base_nodes import Node
from .node_mixin import CodeBlockMixin, ValueIterableMixin

if TYPE_CHECKING:
    from baron import BaronFST


class RedBaron(CodeBlockMixin, ValueIterableMixin, Node):
    baron_type = "root"

    def _default_fst(self) -> BaronFST:
        return {"type": "root", "value": []}

    def __init__(self, source_code: str) -> None:
        super().__init__()
        self.value = source_code

    @property
    def indentation(self) -> str:
        return ""

    @indentation.setter
    def indentation(self, value: str) -> None:
        if self.on_attribute:
            raise ValueError("Unhandled indentation on root")

    @property
    def value_on_new_line(self) -> bool:
        return True
