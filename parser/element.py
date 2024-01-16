from base.ast import AST

class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class Var(AST):
    """The Var node is constructed out of ID token."""
    def __init__(self, token):
        self.token = token
        self.value = token.value

class Compound(AST):
    """Represents a list of statements"""
    def __init__(self):
        self.children = []