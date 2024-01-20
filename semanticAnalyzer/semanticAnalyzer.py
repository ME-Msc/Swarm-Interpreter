from base.nodeVisitor import NodeVisitor
from semanticAnalyzer.symbolTable import *

class SemanticAnalyzer(NodeVisitor):
    def __init__(self):
        self.current_scope = None

    # def visit_Block(self, node):
    #     for declaration in node.declarations:
    #         self.visit(declaration)
    #     self.visit(node.compound_statement)

    # def visit_Program(self, node):
    #     self.visit(node.block)

    def visit_BinOp(self, node):
        left_type = self.visit(node.left)
        while left_type.type != None:
            left_type = left_type.type

        right_type = self.visit(node.right)
        while right_type.type != None:
            right_type = right_type.type

        if left_type.name == right_type.name:
            return left_type
        else:
            raise Exception("Different types on both sides of BinOp")

    def visit_Num(self, node):
        return BuiltinTypeSymbol('INTEGER')

    def visit_UnaryOp(self, node):
        return self.visit(node.expr)

    def visit_Program(self, node):
        print('ENTER scope: global')
        global_scope = ScopedSymbolTable(
            scope_name='global',
            scope_level=1,
            enclosing_scope=self.current_scope, # None
        )
        global_scope._init_builtins()
        self.current_scope = global_scope

        # visit subtree
        self.visit(node.action)
        self.visit(node.agent)
        self.visit(node.behavior)
        self.visit(node.task)
        self.visit(node.mainTask)

        print(global_scope)
        self.current_scope = self.current_scope.enclosing_scope
        print('LEAVE scope: global')

    def visit_MainTask(self, node):
        return self.visit(node.compound_statement)
    
    def visit_Task(self, node):
        return self.visit(node.compound_statement)
    
    def visit_Behavior(self, node):
        return self.visit(node.compound_statement)
    
    def visit_Agent(self, node):
        return self.visit(node.compound_statement)
    
    def visit_Action(self, node):
        return self.visit(node.compound_statement)

    def visit_Compound(self, node):
        for child in node.children:
            self.visit(child)

    def visit_NoOp(self, node):
        return None

    # def visit_VarDecl(self, node):
    #     type_name = node.type_node.value
    #     type_symbol = self.symtab.lookup(type_name)
    #     var_name = node.var_node.value
    #     var_symbol = VarSymbol(var_name, type_symbol)
    #     self.symtab.define(var_symbol)

    def visit_Assign(self, node):
        # 'x = 5', node is '='
        #     = 
        #   /   \
        #  x     5
        var_name = node.left.value
        type_symbol = self.symtab.lookup(var_name)
        if type_symbol is None:
            type_symbol = self.visit(node.right)
            var_symbol = VarSymbol(var_name, type_symbol)
            self.symtab.insert(var_symbol)

    def visit_Var(self, node):
        var_name = node.value
        var_symbol = self.symtab.lookup(var_name)

        if var_symbol is None:
            raise Exception("Error: Symbol(identifier) not found '%s'" % var_name)
        else:
            return var_symbol
