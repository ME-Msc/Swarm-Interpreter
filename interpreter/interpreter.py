from base.nodeVisitor import NodeVisitor
from lexer.token import TokenType
from semanticAnalyzer.symbol import SymbolCategroy
from interpreter.memory import ARType, ActivationRecord, CallStack

class Interpreter(NodeVisitor):
    def __init__(self, tree, log_or_not=False):
        self.tree = tree
        self.log_or_not = log_or_not
        self.call_stack = CallStack()

    def log(self, msg):
        if self.log_or_not:
            print(msg)

    def visit_Program(self, node):
        self.log(f'ENTER: Program')
        ar = ActivationRecord(
            name="Program",
            category=ARType.PROGRAM,
            nesting_level=0,
        )
        self.call_stack.push(ar)
        self.visit(node.main)

        self.call_stack.pop()
        self.log(f'LEAVE: Program')
        self.log(str(self.call_stack))
    
    def visit_Action(self, node):
        self.visit(node.compound_statement)

    def visit_Agent(self, node):
        return self.visit(node.compound_statement)

    def visit_AgentCall(self, node):
        pass

    def visit_Behavior(self, node):
        self.visit(node.init_block)
        self.visit(node.routine_block)
        while not self.visit(node.goal_block):
            self.visit(node.routine_block)
    
    def visit_FunctionCall(self, node):
        function_name = node.name
        function_symbol = node.symbol
        ar_category_switch_case = {
            SymbolCategroy.BEHAVIOR : ARType.BEHAVIOR,
            SymbolCategroy.ACTION : ARType.ACTION,
            SymbolCategroy.RPC : ARType.RPC
        }
        ar = ActivationRecord(
            name = function_name,
            category = ar_category_switch_case[function_symbol.category],
            nesting_level = len(self.call_stack._records)
        )
        
        if function_symbol.category != SymbolCategroy.RPC: # BeahviorCall or ActionCall
            formal_params = function_symbol.formal_params
            actual_params = node.actual_params
            for param_symbol, argument_node in zip(formal_params, actual_params):
                ar[param_symbol.name] = self.visit(argument_node)
        else:
            actual_params = node.actual_params
            for argument_node in actual_params:
                ar[argument_node.value] = self.visit(argument_node)
            
        self.call_stack.push(ar)

        log_switch_case = {
            SymbolCategroy.BEHAVIOR : "Behavior",
            SymbolCategroy.ACTION : "Action",
            SymbolCategroy.RPC : "Rpc"
        }
        self.log(f'ENTER: {log_switch_case[function_symbol.category]} {function_name}')
        self.log(str(self.call_stack))

        # evaluate function body
        if function_symbol.category != SymbolCategroy.RPC:
            self.visit(function_symbol.ast)
        # else:
            # TODO: call RPC server

        self.log(f'LEAVE: {log_switch_case[function_symbol.category]} {function_name}')
        self.call_stack.pop()
        self.log(str(self.call_stack))

    def visit_Task(self, node):
        self.visit(node.init_block)
        self.visit(node.routine_block)
        while not self.visit(node.goal_block):
            self.visit(node.routine_block)
    
    def visit_TaskCall(self, node):
        task_name = node.name
        task_symbol = node.symbol
        ar = ActivationRecord(
            name = task_name,
            category = ARType.TASK,
            nesting_level = len(self.call_stack._records),
        )
        
        formal_params = task_symbol.formal_params
        actual_params = node.actual_params

        for param_symbol, argument_node in zip(formal_params, actual_params):
            ar[param_symbol.name] = self.visit(argument_node)

        self.call_stack.push(ar)

        self.log(f'ENTER: Task {task_name}')
        self.log(str(self.call_stack))

        # evaluate task body
        self.visit(task_symbol.ast)

        self.call_stack.pop()
        self.log(f'LEAVE: Task {task_name}')
        self.log(str(self.call_stack))

    def visit_Main(self, node):
        self.log(f'ENTER: Main')
        ar = ActivationRecord(
            name = "Main",
            category = ARType.MAIN,
            nesting_level = len(self.call_stack._records),
        )
        self.call_stack.push(ar)
        self.visit(node.agent_call)
        self.visit(node.task_call)

        self.call_stack.pop()
        self.log(f'LEAVE: Main')
        self.log(str(self.call_stack))

    def visit_InitBlock(self, node):
        self.visit(node.compound_statement)

    def visit_GoalBlock(self, node):
        self.visit(node.statements)
        result = self.visit(node.goal)
        if result == None:
            return True
        return result
    
    def visit_RoutineBlock(self, node):
        # each child is a parallel block as compound
        for child in node.children:
            self.visit(child)

    def visit_Compound(self, node):
        for child in node.children:
            self.visit(child)

    def visit_Expression(self, node):
        return self.visit(node.expr)

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

    def visit_BinOp(self, node):
        if node.op.category == TokenType.PLUS:
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.category == TokenType.MINUS:
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.category == TokenType.MUL:
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.category == TokenType.DIV:
            return self.visit(node.left) // self.visit(node.right)
        elif node.op.category == TokenType.MOD:
            return self.visit(node.left) % self.visit(node.right)
        elif node.op.category == TokenType.ASSIGN:
            var_name = node.left.value
            var_value = self.visit(node.right)
            ar = self.call_stack.peek()
            ar[var_name] = var_value
        elif node.op.category == TokenType.LESS:
            return self.visit(node.left) < self.visit(node.right)
        elif node.op.category == TokenType.GREATER:
            return self.visit(node.left) < self.visit(node.right)
        elif node.op.category == TokenType.LESS_EQUAL:
            return self.visit(node.left) <= self.visit(node.right)
        elif node.op.category == TokenType.GREATER_EQUAL:
            return self.visit(node.left) >= self.visit(node.right)
        elif node.op.category == TokenType.IS_EQUAL:
            return self.visit(node.left) == self.visit(node.right)
        elif node.op.category == TokenType.NOT_EQUAL:
            return self.visit(node.left) != self.visit(node.right)

    def visit_UnaryOp(self, node):
        op = node.op.category
        if op == TokenType.PLUS:
            return +self.visit(node.expr)
        elif op == TokenType.MINUS:
            return -self.visit(node.expr)
        elif op == TokenType.NOT:
            return not self.visit(node.expr)

    def visit_NoOp(self, node):
        pass

    def interpret(self):
        tree = self.tree
        if tree is None:
            return ''
        return self.visit(tree)

