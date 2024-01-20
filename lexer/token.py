# Token types
#
# EOF (end-of-file) token is used to indicate that
# there is no more input left for lexical analysis
INTEGER     = 'INTEGER'
PLUS        = 'PLUS'
MINUS       = 'MINUS'
MUL         = 'MUL'
DIV         = 'DIV'
MOD         = 'MOD'
LPAREN      = 'LPAREN'
RPAREN      = 'RPAREN'
ID          = 'ID'
ASSIGN      = 'ASSIGN'
SEMI        = 'SEMI'
COLON       = 'COLON'
COMMA       = 'COMMA'
PORT        = 'PORT'
AGENT       = 'AGENT'
ACTION      = 'ACTION'
BEHAVIOR    = 'BEHAVIOR'
TASK        = 'TASK'
MAIN        = 'MAIN'
EOF         = 'EOF'


class Token(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        """String representation of the class instance.

        Examples:
            Token(INTEGER, 3)
            Token(PLUS, '+')
            Token(MUL, '*')
        """
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()

