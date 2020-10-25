class Path:
    """Holds the path to a FST node

    Path(node): path coming from the node's root
    Path.from_baron_path(node, path): path going down the node following the given path

    Note that the second argument "path" is a baron path, i.e. list of
    keys that can be given for example by
    redbaron.Path(node).to_baron_path()

    The second form is useful when converting a path given by baron
    to a redbaron node
    """

    def __init__(self, node):
        self.node = node
        self.path = Path.path_from_node(node)

    @staticmethod
    def path_from_node(node):
        path = []
        if node is None:
            return path

        while node.parent:
            path.insert(0, Path.get_on_attribute(node))
            node = node.parent

        return path

    @staticmethod
    def get_on_attribute(node):
        if node.on_attribute:
            return node.on_attribute

        index = node.parent.baron_index(node)
        assert index is not None
        return index

    @classmethod
    def from_baron_path(cls, node, path):
        for key in path:
            if node is None:
                raise ValueError("node is None")

            if isinstance(key, str):
                if key in node._raw_keys:
                    break
                try:
                    node = getattr(node, key)
                except AttributeError:
                    raise ValueError(f"{node} has no attribute {key}")
            else:
                try:
                    node = node.get_from_baron_index(key)
                except IndexError:
                    raise ValueError(f"{node} has no index {key}")

        return cls(node)

    def to_baron_path(self):
        return self.path

    def __str__(self):
        return 'Path(%s%s @ %s)' % (
            self.node.__class__.__name__,
            '(' + self.node.type + ')' if self.node else '',
            str(self.path))

    def __repr__(self):
        return '<' + self.__str__() + ' object at ' + str(id(self)) + '>'

    def __eq__(self, other):
        if isinstance(other, Path):
            return self.to_baron_path() == other.to_baron_path()

        if isinstance(other, list):
            return self.to_baron_path() == other

        return False
