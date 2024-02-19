from base.nodeVisitor import NodeVisitor
from lexer.token import TokenType
from semanticAnalyzer.symbolTable import *
from base.error import SemanticError, ErrorCode

class SemanticAnalyzer(NodeVisitor):
    def __init__(self, log_or_not=False):
        self.current_scope = None
        self.log_or_not = log_or_not

    def visit_Program(self, node):
        self.log('ENTER scope: global')
        global_scope = ScopedSymbolTable(
            scope_name='global',
            scope_level=1,
            enclosing_scope=self.current_scope, # None
            log_or_not=self.log_or_not
        )
        global_scope._init_builtins()
        self.current_scope = global_scope

        # visit subtree
        self.visit(node.action_list)
        self.visit(node.agent_list)
        self.visit(node.behavior_list)
        self.visit(node.task_list)
        self.visit(node.main)

        self.log(global_scope)
        self.current_scope = self.current_scope.enclosing_scope
        self.log('LEAVE scope: global')

    def visit_Port(self, node):
        pass

    def visit_ActionList(self, node):
        for child in node.children:
            self.visit(child)

    def visit_Action(self, node):
        action_name = 'ACTION_' + node.name
        action_symbol = ActionSymbol(action_name)
        # Insert parameters into the action_symbol.formal_params
        for param in node.formal_params.children:
            param_name = param.var_node.value
            param_type = None
            var_symbol = VarSymbol(param_name, param_type)
            action_symbol.formal_params.append(var_symbol)
        self.current_scope.insert(action_symbol)

        self.log('ENTER scope: %s' %  action_name)
        # Scope for parameters and local variables
        action_scope = ScopedSymbolTable(
            scope_name = action_name,
            scope_level = self.current_scope.scope_level + 1,
            enclosing_scope = self.current_scope,
            log_or_not = self.log_or_not
        )
        self.current_scope = action_scope

        # Insert parameters into the action scope
        for param in node.formal_params.children:
            param_name = param.var_node.value
            param_type = None		# self.current_scope.lookup(param_name)
            var_symbol = VarSymbol(param_name, param_type)
            self.current_scope.insert(var_symbol)

        self.visit(node.compound_statement)
        self.log(action_scope)
        self.current_scope = self.current_scope.enclosing_scope
        self.log('LEAVE scope: %s \n\n' %  action_name)

    def visit_ActionCall(self, node):
        action_name = 'ACTION_' + node.name
        action_symbol = self.current_scope.lookup(action_name)
        # formal_params is in Symbol, do not need '.children'
        formal_params = action_symbol.formal_params
        # actual_params is in AST node, need '.children'
        actual_params = node.actual_params.children
        if len(actual_params) != len(formal_params):
            self.error(
                error_code=ErrorCode.WRONG_PARAMS_NUM,
                token=node.token,
            )
        for param_node in node.actual_params:
            self.visit(param_node)
        
        # accessed by the interpreter when executing procedure call
        node.symbol = action_symbol

    def visit_AgentList(self, node):
        for child in node.children:
            self.visit(child)

    def visit_Agent(self, node):
        agent_name = 'AGENT_' + node.name
        agent_symbol = AgentSymbol(agent_name)
        # Insert agent_symbol into the global scope
        self.current_scope.insert(agent_symbol)

        self.log('ENTER scope: %s' %  agent_name)
        # Scope for parameters and local variables
        agent_scope = ScopedSymbolTable(
            scope_name = agent_name,
            scope_level = self.current_scope.scope_level + 1,
            enclosing_scope = self.current_scope,
            log_or_not = self.log_or_not
        )
        self.current_scope = agent_scope
        # Insert abilities into the agent scope
        for ability in node.abilities.children:
            ability_name = ability.value
            ability_type = None		# self.current_scope.lookup(param_name)
            var_symbol = VarSymbol(ability_name, ability_type)
            self.current_scope.insert(var_symbol)
            agent_symbol.abilities.append(var_symbol)

        self.log(agent_scope)
        self.current_scope = self.current_scope.enclosing_scope
        self.log('LEAVE scope: %s \n\n' %  agent_name)

    def visit_AgentCall(self, node):
        agent_name = 'AGENT_' + node.name
        agent_symbol = self.current_scope.lookup(agent_name)
        node.symbol = agent_symbol

    def visit_BehaviorList(self, node):
        for child in node.children:
            self.visit(child)

    def visit_Behavior(self, node):
        behavior_name = 'BEHAVIOR_' + node.name
        behavior_symbol = BehaviorSymbol(behavior_name)
        # Insert behavior_symbol into the global scope
        for param in node.formal_params.children:
            param_name = param.var_node.value
            param_type = None
            var_symbol = VarSymbol(param_name, param_type)
            behavior_symbol.formal_params.append(var_symbol)
        self.current_scope.insert(behavior_symbol)

        self.log('ENTER scope: %s' %  behavior_name)
        # Scope for parameters and local variables
        behavior_scope = ScopedSymbolTable(
            scope_name = behavior_name,
            scope_level = self.current_scope.scope_level + 1,
            enclosing_scope = self.current_scope,
            log_or_not = self.log_or_not
        )
        self.current_scope = behavior_scope

        ## Insert parameters into the behavior scope
        for param in node.formal_params.children:
            param_name = param.var_node.value
            param_type = None		# self.current_scope.lookup(param_name)
            var_symbol = VarSymbol(param_name, param_type)
            self.current_scope.insert(var_symbol)
        
        # visit routine_block before goal_block,
        # because variables may be defined in routine_block
        self.visit(node.init_block)
        self.visit(node.routine_block)
        self.visit(node.goal_block)
        self.log(behavior_scope)
        self.current_scope = self.current_scope.enclosing_scope
        self.log('LEAVE scope: %s \n\n' %  behavior_name)

    def visit_BehaviorCall(self, node):
        behavior_name = 'BEHAVIOR_' + node.name
        behavior_symbol = self.current_scope.lookup(behavior_name)
        formal_params = behavior_symbol.formal_params
        actual_params = node.actual_params
        if len(actual_params) != len(formal_params):
            self.error(
                error_code=ErrorCode.WRONG_PARAMS_NUM,
                token=node.token,
            )
        for param_node in node.actual_params:
            self.visit(param_node)
        
        # accessed by the interpreter when executing procedure call
        node.symbol = behavior_symbol

    def visit_TaskList(self, node):
        for child in node.children:
            self.visit(child)

    def visit_Task(self, node):
        task_name = 'TASK_' + node.name
        task_symbol = TaskSymbol(task_name)
        # Insert behavior_symbol into the global scope
        for param in node.formal_params.children:
            param_name = param.var_node.value
            param_type = None
            var_symbol = VarSymbol(param_name, param_type)
            task_symbol.formal_params.append(var_symbol)
        self.current_scope.insert(task_symbol)

        self.log('ENTER scope: %s' %  task_name)
        # Scope for parameters and local variables
        task_scope = ScopedSymbolTable(
            scope_name = task_name,
            scope_level = self.current_scope.scope_level + 1,
            enclosing_scope = self.current_scope,
            log_or_not = self.log_or_not
        )
        self.current_scope = task_scope

       	# Insert parameters into the procedure scope
        for param in node.formal_params.children:
            param_name = param.var_node.value
            param_type = None		# self.current_scope.lookup(param_name)
            var_symbol = VarSymbol(param_name, param_type)
            self.current_scope.insert(var_symbol)
        
        # visit routine_block before goal_block,
        # because variables may be defined in routine_block
        self.visit(node.init_block)
        self.visit(node.routine_block)
        self.visit(node.goal_block)
        self.log(task_scope)
        self.current_scope = self.current_scope.enclosing_scope
        self.log('LEAVE scope: %s \n\n' %  task_name)
        # task_symbol.ast = node.compound_statement
    
    def visit_TaskCall(self, node):
        task_name = 'TASK_' + node.name
        task_symbol = self.current_scope.lookup(task_name)
        formal_params = task_symbol.formal_params
        actual_params = node.actual_params
        if len(actual_params) != len(formal_params):
            self.error(
                error_code=ErrorCode.WRONG_PARAMS_NUM,
                token=node.token,
            )
        for param_node in node.actual_params:
            self.visit(param_node)
        
        task_symbol = self.current_scope.lookup(task_name)
        # accessed by the interpreter when executing procedure call
        node.symbol = task_symbol

    def visit_Main(self, node):
        self.visit(node.agent_call)
        self.visit(node.task_call)

    def visit_InitBlock(self, node):
        self.visit(node.compound_statement)

    def visit_GoalBlock(self, node):
        self.visit(node.statements)
        self.visit(node.expression)
    
    def visit_RoutineBlock(self, node):
        for child in node.children:
            self.visit(child)

    def visit_Compound(self, node):
        for child in node.children:
            self.visit(child)

    def visit_Expression(self, node):
        self.visit(node.expression)

    # def visit_Assign(self, node):
    #     # 'x = 5', node is '='
    #     #     = 
    #     #   /   \
    #     #  x     5
    #     var_name = node.left.value
    #     type_symbol = self.current_scope.lookup(var_name)
    #     if type_symbol is None:
    #         type_symbol = self.visit(node.right)
    #         var_symbol = VarSymbol(var_name, type_symbol)
    #         self.current_scope.insert(var_symbol)

    def visit_Var(self, node):
        var_name = node.value
        var_symbol = self.current_scope.lookup(var_name)
        if var_symbol is None:
            self.error(error_code=ErrorCode.ID_NOT_FOUND, token=node.token)
        else:
            return var_symbol

    def visit_Num(self, node):
        return BuiltinTypeSymbol('INTEGER')

    def visit_BinOp(self, node):
        if node.op.type == TokenType.ASSIGN:
            var_name = node.left.value
            type_symbol = self.current_scope.lookup(var_name)
            if type_symbol is None:
                type_symbol = self.visit(node.right)
                var_symbol = VarSymbol(var_name, type_symbol)
                self.current_scope.insert(var_symbol)
        elif node.op.type == TokenType.IS_EQUAL:
            # don not check symbol type
            # because both side can be formal_param whose type is 'None' or anything
            return
        else: # TODO: comparable symbol
            left_type = self.visit(node.left)
            if left_type != None:
                while hasattr(left_type, 'type'):
                    left_type = left_type.type
            right_type = self.visit(node.right)
            if right_type != None :
                while hasattr(right_type, 'type'):
                    right_type = right_type.type
            if left_type == right_type:
                return left_type
            else:
                raise Exception("Different types on both sides of BinOp")

    def visit_UnaryOp(self, node):
        return self.visit(node.expr)

    def visit_NoOp(self, node):
        return None

    def log(self, msg):
        if self.log_or_not:
            print(msg)

    def error(self, error_code, token):
        raise SemanticError(
            error_code=error_code,
            token=token,
            message=f'{error_code.value} -> {token}',
        )
