from base.nodeVisitor import NodeVisitor
from symbols.symbol import *

class SymbolTable(object):
    def __init__(self):
        self._symbols = {}
        self._init_builtins()

    def _init_builtins(self):
        self.define(BuiltinTypeSymbol('INTEGER'))

    def __str__(self):
        s = 'Symbols: {symbols}'.format(
            symbols=[(key, value) if key != 'INTEGER' else (value) for key, value in self._symbols.items()]
        )
        return s

    __repr__ = __str__

    def define(self, symbol:Symbol):
        print('Define: %s' % symbol)
        if symbol.name == 'INTEGER':
            self._symbols[symbol.name] = symbol
        else:
            self._symbols[symbol.name] = symbol.type

    def lookup(self, name):
        print('Lookup: %s' % name)
        symbol = self._symbols.get(name)
        # 'symbol' is either an instance of the Symbol class or 'None'
        return symbol


class SymbolTableBuilder(NodeVisitor):
    def __init__(self):
        self.symtab = SymbolTable()

    # def visit_Block(self, node):
    #     for declaration in node.declarations:
    #         self.visit(declaration)
    #     self.visit(node.compound_statement)

    # def visit_Program(self, node):
    #     self.visit(node.block)

    def visit_BinOp(self, node):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        if left_type.name == right_type.name:
            return left_type
        else:
            raise Exception("Different types on both sides of BinOp")

    def visit_Num(self, node):
        return BuiltinTypeSymbol('INTEGER')

    def visit_UnaryOp(self, node):
        return self.visit(node.expr)

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
            self.symtab.define(var_symbol)

    def visit_Var(self, node):
        var_name = node.value
        var_symbol = self.symtab.lookup(var_name)

        if var_symbol is None:
            raise NameError(repr(var_name))
        else:
            return var_symbol
