from base.nodeVisitor import NodeVisitor
from lexer.token import TokenType

class Interpreter(NodeVisitor):
    def __init__(self, tree):
        self.tree = tree
        self.GLOBAL_MEMORY = {}

    def visit_NoOp(self, node):
        pass
    
    def visit_UnaryOp(self, node):
        op = node.op.type
        if op == TokenType.PLUS:
            return +self.visit(node.expr)
        elif op == TokenType.MINUS:
            return -self.visit(node.expr)

    def visit_BinOp(self, node):
        if node.op.type == TokenType.PLUS:
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == TokenType.MINUS:
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.type == TokenType.MUL:
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.type == TokenType.DIV:
            return self.visit(node.left) // self.visit(node.right)
        elif node.op.type == TokenType.MOD:
            return self.visit(node.left) % self.visit(node.right)

    def visit_Program(self, node):
        self.visit(node.action)
        self.visit(node.agent)
        self.visit(node.behavior)
        self.visit(node.task)
        self.visit(node.mainTask)

    def visit_MainTask(self, node):
        return self.visit(node.compound_statement)
    
    def visit_Task(self, node):
        return self.visit(node.compound_statement)
    
    def visit_TaskCall(self, node):
        pass

    def visit_Behavior(self, node):
        return self.visit(node.compound_statement)
    
    def visit_Agent(self, node):
        return self.visit(node.compound_statement)
    
    def visit_Action(self, node):
        return self.visit(node.compound_statement)

    def visit_Compound(self, node):
        for child in node.children:
            self.visit(child)
            
    def visit_Assign(self, node):
        var_name = node.left.value
        var_value = self.visit(node.right)
        self.GLOBAL_MEMORY[var_name] = var_value

    def visit_Var(self, node):
        var_name = node.value
        var_value = self.GLOBAL_MEMORY.get(var_name)
        if var_value is None:
            raise NameError(repr(var_name))
        else:
            return var_value
        
    def visit_Num(self, node):
        return node.value
    
    def interpret(self):
        tree = self.tree
        if tree is None:
            return ''
        return self.visit(tree)

