from base.ast import AST

class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value
