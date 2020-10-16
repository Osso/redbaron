HAS_PYGMENTS = True

try:
    import pygments  # pylint: disable=unused-import
except ImportError:
    HAS_PYGMENTS = False


if HAS_PYGMENTS:
    from pygments.token import Comment, Text, String, Keyword, Name, Operator, Generic
    from pygments.lexer import RegexLexer, bygroups
    from pygments import highlight
    from pygments.lexers import PythonLexer
    from pygments.formatters import Terminal256Formatter

    class HelpLexer(RegexLexer):
        name = 'Lexer for RedBaron .help() method output'

        tokens = {
            'root': [
                (r'\x1b(.*?)\[(\d+)m', Generic),  # avoid escaping twice, see issue#180
                (r"#.*$", Comment),
                (r"('([^\\']|\\.)*'|\"([^\\\"]|\\.)*\")", String),
                (r"(None|False|True)", String),
                (r'(\*)( \w+Node)', bygroups(Operator, Keyword)),
                (r'\w+Node', Name.Function),
                (r'(\*|=|->|\(|\)|\.\.\.)', Operator),
                (r'\w+', Text),
                (r'\s+', Text),
            ]
        }

    def help_highlight(string):
        return highlight(string, HelpLexer(), Terminal256Formatter(style='monokai'))

    def python_highlight(string):
        return highlight(string, PythonLexer(encoding="utf-8"),
                         Terminal256Formatter(style='monokai',
                                              encoding="utf-8"))

else:
    def help_highlight(string):
        return string.encode("utf-8")

    def python_highlight(string):
        return string.encode("utf-8")
