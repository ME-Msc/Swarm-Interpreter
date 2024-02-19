from base.ast import AST

class NoOp(AST):
    pass

class UnaryOp(AST):
    def __init__(self, op, expr):
        self.token = self.op = op
        self.expr = expr

class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right

# class Assign(AST):
#     def __init__(self, left, op, right):
#         self.left = left
#         self.token = self.op = op
#         self.right = right