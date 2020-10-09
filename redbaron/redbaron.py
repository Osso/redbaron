from redbaron import nodes
from redbaron.base_nodes import (GenericNodesMixin,
                                 LineProxyList,
                                 NodeList)

import baron
import baron.path


class RedBaron(GenericNodesMixin, LineProxyList):
    def __init__(self, source_code):

        if isinstance(source_code, str):
            self.build_from_str(source_code)
        else:
            # Might be init from same object, or slice
            super().__init__(source_code)

        self.on_attribute = None
        self.parent = None

    def build_from_str(self, source_code):
        self.node_list = NodeList.from_fst(baron.parse(source_code),
                                           parent=self, on_attribute="root")
        self.middle_separator = nodes.EndlNode({"type": "endl",
                                                "formatting": [],
                                                "value": "\n",
                                                "indent": ""})

        def current_line_to_el(current_line):
            if not current_line:
                el = nodes.EmptyLine()
            elif len(current_line) == 1:
                el = current_line[0]
            else:
                el = nodes.NodeList(current_line)
            return el

        self.data = []
        current_line = []
        for node in self.node_list:
            if node.type == "endl":
                self.data.append([current_line_to_el(current_line), [node]])
            else:
                current_line.append(node)
        if current_line:
            self.data.append([current_line_to_el(current_line), []])
        self.node_list.parent = None

    def to_node_object(self, value):
        return super().to_node_object(value, self, "root")

    def to_node_object_list(self, value):
        return super().to_node_object_list(value, self, "root")
