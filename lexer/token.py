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
    DOLLAR      = '$'
    ASSIGN      = '='
    SEMI        = ';'
    COLON       = ':'
    COMMA       = ','
    TILDE       = '~'
    L_PAREN     = '('
    R_PAREN     = ')'
    L_BRACE     = '{'
    R_BRACE     = '}'
    L_BRACKET   = '['
    R_BRACKET   = ']'
    LESS        = '<'
    GREATER     = '>'
    HASH        = '#'
    # multi-character token types
    DOUBLE_LESS     = '<<'
    DOUBLE_GREATER  = '>>'
    LESS_EQUAL      = '<='
    GREATER_EQUAL   = '>='
    IS_EQUAL        = '=='
    NOT_EQUAL       = '!='
    RPC_CALL        = ':='
    PARALLEL        = '||'
    # block of reserved words
    PORT        = 'PORT'
    AGENT       = 'AGENT'
    ACTION      = 'ACTION'
    BEHAVIOR    = 'BEHAVIOR'
    TASK        = 'TASK'
    MAIN        = 'MAIN'
    INIT        = 'INIT'
    GOAL        = 'GOAL'
    ROUTINE     = 'ROUTINE'
    IF          = 'IF'
    ELSE        = 'ELSE'
    GET         = 'GET'
    PUT         = 'PUT'
    FROM        = 'FROM'
    TO          = 'TO'
    ORDER       = 'ORDER'
    EACH        = 'EACH'
    NOT         = 'NOT'
    AND         = 'AND'
    OR          = 'OR'
    # others
    EOF         = 'EOF'
    INTEGER     = 'INTEGER'
    ID          = 'ID'


class Token(object):
    def __init__(self, category, value, lineno=None, column=None):
        self.category = category
        self.value = value
        self.lineno = lineno
        self.column = column

    def __str__(self):
        """String representation of the class instance.

        Example:
            >>> Token(TokenType.INTEGER, 7, lineno=5, column=10)
            Token(TokenType.INTEGER, 7, position=5:10)
        """
        return 'Token({category}, {value}, position={lineno}:{column})'.format(
            category=self.category,
            value=repr(self.value),
            lineno=self.lineno,
            column=self.column,
        )

    def __repr__(self):
        return self.__str__()

