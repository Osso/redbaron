from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base_nodes import BaseNode

type BaronPathKey = str | int
type BaronPath = list[BaronPathKey]


class Path:
    """Holds the path to a FST node

    Path(node):

    Note that the second argument "path" is a baron path, i.e. list of
    keys that can be given for example by
    redbaron.Path(node).to_baron_path()

    The second form is useful when converting a path given by baron
    to a redbaron node
    """

    node: BaseNode
    path: BaronPath

    def __init__(self, node: BaseNode) -> None:
        assert node is not None

        self.node = node
        self.path = Path.baron_path_from_node(node)

    @staticmethod
    def baron_path_from_node(node: BaseNode) -> BaronPath:
        "Path coming from the node's root"
        assert node is not None

        path: BaronPath = []
        while node.parent:
            path.insert(0, Path.get_on_attribute(node))
            node = node.parent

        return path

    @staticmethod
    def get_on_attribute(node: BaseNode) -> BaronPathKey:
        from .base_nodes import RESERVED_KEYWORDS

        index = node.on_attribute
        if index:
            if index[-1] == "_" and index[:-1] in RESERVED_KEYWORDS:
                index = index[:-1]
            return index

        index = node.parent.baron_index(node)
        assert index is not None
        return index

    @classmethod
    def from_baron_path(cls, node: BaseNode, path: BaronPath) -> Path:
        "Path going down the node following the given path"
        for key in path:
            if node is None:
                raise ValueError("node is None")

            try:
                if key in getattr(node, "_raw_keys", []):
                    break
                if key in getattr(node, "_constant_keys", []):
                    break
                node = node.get_from_baron_index(key)
            except AttributeError:
                raise ValueError(f"{node} has no attribute {key}") from None
            except IndexError:
                raise ValueError(f"{node} has no index {key}") from None

        return cls(node)

    def to_baron_path(self) -> BaronPath:
        return self.path

    def __str__(self) -> str:
        return f"Path({self.node.baron_type} @ {self.path})"

    def __repr__(self) -> str:
        return f"<{self} object at {id(self)}>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Path):
            return self.to_baron_path() == other.to_baron_path()

        return self.to_baron_path() == other
