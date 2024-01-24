from base.nodeVisitor import NodeVisitor
from lexer.token import TokenType
from interpreter.memory import ARType, ActivationRecord, CallStack

class Interpreter(NodeVisitor):
    def __init__(self, tree, log_or_not=False):
        self.tree = tree
        self.log_or_not = log_or_not
        self.call_stack = CallStack()

    def log(self, msg):
        if self.log_or_not:
            print(msg)

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
        self.log(f'ENTER: PROGRAM Main')
        ar = ActivationRecord(
            name="Main",
            type=ARType.PROGRAM,
            nesting_level=1,
        )
        self.call_stack.push(ar)

        # self.visit(node.action)
        # self.visit(node.agent)
        # self.visit(node.behavior)
        # self.visit(node.task)
        self.visit(node.mainTask)
        
        self.log(f'LEAVE: PROGRAM Main')
        self.log(str(self.call_stack))

        self.call_stack.pop()

    def visit_MainTask(self, node):
        return self.visit(node.compound_statement)
    
    def visit_Task(self, node):
        return self.visit(node.compound_statement)
    
    def visit_TaskCall(self, node):
        task_name = node.name
        task_symbol = node.symbol
        ar = ActivationRecord(
            name = task_name,
            type = ARType.TASK,
            nesting_level = task_symbol.scope_level + 1,
        )
        
        formal_params = task_symbol.formal_params
        actual_params = node.actual_params

        for param_symbol, argument_node in zip(formal_params, actual_params):
            ar[param_symbol.name] = self.visit(argument_node)

        self.call_stack.push(ar)

        self.log(f'ENTER: TASK {task_name}')
        self.log(str(self.call_stack))

        # evaluate task body
        self.visit(task_symbol.ast)

        self.log(f'LEAVE: PROCEDURE {task_name}')
        self.log(str(self.call_stack))

        self.call_stack.pop()

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
        ar = self.call_stack.peek()
        ar[var_name] = var_value

    def visit_Var(self, node):
        var_name = node.value
        ar = self.call_stack.peek()
        var_value = ar.get(var_name)
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

