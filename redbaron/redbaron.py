from redbaron import nodes
from redbaron.base_nodes import (GenericNodesMixin,
                                 LineProxyList,
                                 NodeList)

import baron
import baron.path

# TODO
# LineProxyList: handle comments
#                should a 'pass' be put if the list would be empty?
#                add blank line arround in certain cases? Like arround function/class at first level and second level
#                expected behavior on append when blank lines at the end of the block (-> append before blank lines)
#                more explicit display for blank lines in line proxy .help()
# if node_list is modified, the proxy list won't update itself -> bugs

# CommaProxyList indented
# "change formatting style"
# the "\n" after the "[{(" is hold by the parent node, this parent node should have a method to tell the CommaProxyList where this is

# FIXME: doc others.rst line 244
# FIXME: __setattr__ is broken on formatting

# XXX
# should .next and .previous behavior should be changed to drop formatting
# nodes? I guess so if I consider that with enough abstraction the user will
# never have to play with formatting node unless he wants to


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

    def _convert_input_to_node_object(self, value, parent, on_attribute):
        return GenericNodesMixin._convert_input_to_node_object(self, value, self, "root")

    def _convert_input_to_node_object_list(self, value, parent, on_attribute):
        return GenericNodesMixin._convert_input_to_node_object_list(self, value, self, "root")
