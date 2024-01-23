from enum import Enum

# Token types
#
# EOF (end-of-file) token is used to indicate that
# there is no more input left for lexical analysis
class TokenType(Enum):
    # single-character token types
    PLUS        = '+'
    MINUS       = '-'
    MUL         = '*'
    DIV         = '/'
    MOD         = '%'
    ASSIGN      = '='
    SEMI        = ';'
    COLON       = ':'
    COMMA       = ','
    LPAREN      = '('
    RPAREN      = ')'
    # block of reserved words
    PORT        = 'PORT'
    AGENT       = 'AGENT'
    ACTION      = 'ACTION'
    BEHAVIOR    = 'BEHAVIOR'
    TASK        = 'TASK'
    MAIN        = 'MAIN'
    EOF         = 'EOF'
    # others
    INTEGER     = 'INTEGER'
    ID          = 'ID'


class Token(object):
    def __init__(self, type, value, lineno=None, column=None):
        self.type = type
        self.value = value
        self.lineno = lineno
        self.column = column

    def __str__(self):
        """String representation of the class instance.

        Example:
            >>> Token(TokenType.INTEGER, 7, lineno=5, column=10)
            Token(TokenType.INTEGER, 7, position=5:10)
        """
        return 'Token({type}, {value}, position={lineno}:{column})'.format(
            type=self.type,
            value=repr(self.value),
            lineno=self.lineno,
            column=self.column,
        )

    def __repr__(self):
        return self.__str__()

