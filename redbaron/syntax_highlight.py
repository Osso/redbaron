import importlib.util

HAS_PYGMENTS = importlib.util.find_spec("pygments") is not None


if HAS_PYGMENTS:
    from pygments import highlight
    from pygments.formatters import TerminalTrueColorFormatter  # pylint: disable=no-name-in-module
    from pygments.lexer import RegexLexer, bygroups
    from pygments.lexers import PythonLexer  # pylint: disable=no-name-in-module
    from pygments.token import Comment, Generic, Keyword, Name, Operator, String, Text

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
        return highlight(string, HelpLexer(),
                         TerminalTrueColorFormatter(style='monokai'))[:-1]

    def python_highlight(string):
        return highlight(string, PythonLexer(),
                         TerminalTrueColorFormatter(style='monokai'))[:-1]

else:
    def help_highlight(string):
        return string

    def python_highlight(string):
        return string
