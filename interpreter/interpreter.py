import asyncio

from base.nodeVisitor import NodeVisitor
from base.error import InterpreterError, ErrorCode
from lexer.token import TokenType
from semanticAnalyzer.symbol import SymbolCategroy
from interpreter.memory import ARType, ActivationRecord, CallStack
from interpreter.rpc import client

class Interpreter(NodeVisitor):
    def __init__(self, tree, log_or_not=False):
        self.tree = tree
        self.log_or_not = log_or_not
        self.call_stack = CallStack()
        self.ID_MAP = {}

    def log(self, msg):
        if self.log_or_not:
            print(msg)

    def error(self, error_code, token):
        raise InterpreterError(
            error_code=error_code,
            token=token,
            message=f'{error_code.value} -> {token}',
        )

    def visit_Program(self, node, **kwargs):
        self.log(f'ENTER: Program')
        ar = ActivationRecord(
            name="Program",
            category=ARType.PROGRAM,
            nesting_level=0,
        )
        self.call_stack.push(ar)
        self.visit(node.main)

        self.log(str(self.call_stack))
        self.call_stack.pop()
        self.log(f'LEAVE: Program')
        self.log(str(self.call_stack))
    
    def visit_Action(self, node, **kwargs):
        self.visit(node.compound_statement, **kwargs)

    def visit_Agent(self, node, **kwargs):
        return self.visit(node.compound_statement)

    def visit_AgentCall(self, node, **kwargs):
        agt_smbl = node.symbol
        agt_name = agt_smbl.name
        cnt = self.visit(node.count)
        ar = self.call_stack.peek()

        ar[agt_name] = (agt_name, 0, cnt)
        for i in range(cnt):
            key = (agt_name, i)
            value = len(self.ID_MAP)
            self.ID_MAP[key] = value
        getattr(client, "createUavs")(cnt)

    def visit_Behavior(self, node, **kwargs):
        self.visit(node.init_block, **kwargs)
        self.visit(node.routine_block, **kwargs)
        while not self.visit(node.goal_block, **kwargs):
            self.visit(node.routine_block, **kwargs)
    
    def visit_FunctionCall(self, node, **kwargs):
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
        self.log(f'Agent now: {kwargs["agent"]} : {kwargs["id"]}')
        self.log(str(self.call_stack))

        # evaluate function body
        if function_symbol.category != SymbolCategroy.RPC:
            self.visit(function_symbol.ast, **kwargs)
        else: # call RPC server
            # add ID as first arg
            rpc_args = [self.ID_MAP[(kwargs['agent'], kwargs['id'])], ]
            # add rpc_call args
            for actual_param in node.actual_params:
                actual_value = self.visit(actual_param)
                rpc_args.append(actual_value)
            getattr(client, node.name)(*rpc_args)

        self.log(str(self.call_stack))
        self.log(f'Agent now: {kwargs["agent"]} : {kwargs["id"]}')
        self.log(f'LEAVE: {log_switch_case[function_symbol.category]} {function_name}')
        self.call_stack.pop()
        self.log(str(self.call_stack))

    def visit_Task(self, node, **kwargs):
        self.visit(node.init_block)
        self.visit(node.routine_block)
        while not self.visit(node.goal_block):
            self.visit(node.routine_block)
    
    def visit_TaskCall(self, node, **kwargs):
        getattr(client, "resetWorld")()
        for actual_agent_node in node.actual_params_agent_list:
            agent_range = self.visit(actual_agent_node.agent)
            if agent_range is None:
                self.error(error_code=ErrorCode.ID_NOT_FOUND, token=actual_agent_node.agent.token)

            agent_start = self.visit(actual_agent_node.start)
            if agent_start < agent_range[1]:
                self.error(error_code=ErrorCode.OUT_OF_RANGE, token=actual_agent_node.start.token)

            agent_end = self.visit(actual_agent_node.end)
            if agent_end > agent_range[2]:
                self.error(error_code=ErrorCode.OUT_OF_RANGE, token=actual_agent_node.end.token)

        task_name = node.name
        task_symbol = node.symbol
        ar = ActivationRecord(
            name = task_name,
            category = ARType.TASK,
            nesting_level = len(self.call_stack._records),
        )
        
        formal_params_agent_list = task_symbol.formal_params_agent_list
        actual_params_agent_list = node.actual_params_agent_list

        formal_params = task_symbol.formal_params
        actual_params = node.actual_params

        for param_agent_symbol, argument_agent_node in zip(formal_params_agent_list, actual_params_agent_list):
            ar[param_agent_symbol.agent] = self.visit(argument_agent_node.agent)
            ar[param_agent_symbol.start] = self.visit(argument_agent_node.start)
            ar[param_agent_symbol.end] = self.visit(argument_agent_node.end)

        for param_symbol, argument_node in zip(formal_params, actual_params):
            ar[param_symbol.name] = self.visit(argument_node)

        self.call_stack.push(ar)

        self.log(f'ENTER: Task {task_name}')
        self.log(str(self.call_stack))

        # evaluate task body
        self.visit(task_symbol.ast)

        self.log(str(self.call_stack))
        self.call_stack.pop()
        self.log(f'LEAVE: Task {task_name}')
        self.log(str(self.call_stack))

    def visit_TaskOrder(self, node, **kwargs):
        agent_s_e, start, end = self.visit(node.agent_range)
        now = start
        while now < end:
            self.visit(node.function_call_statements, agent=agent_s_e[0], id=now)
            now += 1

    def visit_TaskEach(self, node, **kwargs):
        pass

    def visit_AgentRange(self, node, **kwargs):
        agent = self.visit(node.agent)
        start = self.visit(node.start)
        end = self.visit(node.end)
        return (agent, start, end)

    def visit_Main(self, node, **kwargs):
        ar = ActivationRecord(
            name = "Main",
            category = ARType.MAIN,
            nesting_level = len(self.call_stack._records),
        )
        
        self.call_stack.push(ar)

        self.log(f'ENTER: Main')

        for agent_call_node in node.agent_call_list.children:
            self.visit(agent_call_node)
        self.log(str(self.call_stack))
        self.visit(node.task_call)
        
        self.log(str(self.call_stack))
        self.call_stack.pop()
        self.log(f'LEAVE: Main')
        self.log(str(self.call_stack))

    def visit_InitBlock(self, node, **kwargs):
        self.visit(node.compound_statement, **kwargs)

    def visit_GoalBlock(self, node, **kwargs):
        self.visit(node.statements, **kwargs)
        result = self.visit(node.goal)
        if result == None:
            return True
        return result
    
    def visit_RoutineBlock(self, node, **kwargs):
        # each child is a parallel block as compound
        for child in node.children:
            self.visit(child, **kwargs)

    def visit_Compound(self, node, **kwargs):
        for child in node.children:
            self.visit(child, **kwargs)

    def visit_IfElse(self, node, **kwargs):
        expr_result = self.visit(node.expression)
        if expr_result:
            self.visit(node.true_compound)
        else:
            if node.false_compound is not None:
                self.visit(node.false_compound)

    def visit_Expression(self, node, **kwargs):
        return self.visit(node.expr)

    def visit_Var(self, node, **kwargs):
        var_name = node.value
        ar = self.call_stack.peek()
        var_value = ar.get(var_name)
        if var_value is None:
            raise NameError(repr(var_name))
        else:
            return var_value
        
    def visit_Num(self, node, **kwargs):
        return node.value

    def visit_BinOp(self, node, **kwargs):
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
        elif node.op.category == TokenType.PUT:
            stigmergy_name = node.right.value
            expr_value = self.visit(node.left)
            ar = self.call_stack.bottom()
            ar[stigmergy_name] = expr_value
        elif node.op.category == TokenType.GET:
            var_name = node.left.value
            stigmergy_name = node.right.value
            ar = self.call_stack.bottom()
            var_value = ar[stigmergy_name]
            cur_ar = self.call_stack.peek()
            cur_ar[var_name] = var_value
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

    def visit_UnaryOp(self, node, **kwargs):
        op = node.op.category
        if op == TokenType.PLUS:
            return +self.visit(node.expr)
        elif op == TokenType.MINUS:
            return -self.visit(node.expr)
        elif op == TokenType.NOT:
            return not self.visit(node.expr)

    def visit_NoOp(self, node, **kwargs):
        pass

    def interpret(self):
        tree = self.tree
        if tree is None:
            return ''
        return self.visit(tree)

