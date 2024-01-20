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
        task_name = 'TASK_' + node.name
        task_symbol = TaskSymbol(task_name)
        self.current_scope.insert(task_symbol)

        print('ENTER scope: %s' %  task_name)
        # Scope for parameters and local variables
        task_scope = ScopedSymbolTable(
            scope_name = task_name,
            scope_level = self.current_scope.scope_level + 1,
            enclosing_scope = self.current_scope
        )
        self.current_scope = task_scope

       	# Insert parameters into the procedure scope
        for param in node.params:
            param_name = param.var_node.value
            param_type = None		# self.current_scope.lookup(param_name)
            var_symbol = VarSymbol(param_name, param_type)
            self.current_scope.insert(var_symbol)
            task_symbol.params.append(var_symbol)
        
        self.visit(node.compound_statement)

        print(task_scope)

        self.current_scope = self.current_scope.enclosing_scope
        print('LEAVE scope: %s \n\n' %  task_name)
    
    def visit_Behavior(self, node):
        behavior_name = 'BEHAVIOR_' + node.name
        behavior_symbol = BehaviorSymbol(behavior_name)
        self.current_scope.insert(behavior_symbol)

        print('ENTER scope: %s' %  behavior_name)
        # Scope for parameters and local variables
        behavior_scope = ScopedSymbolTable(
            scope_name = behavior_name,
            scope_level = self.current_scope.scope_level + 1,
            enclosing_scope = self.current_scope
        )
        self.current_scope = behavior_scope

        ## Insert parameters into the procedure scope
        for param in node.params:
            param_name = param.var_node.value
            param_type = None		# self.current_scope.lookup(param_name)
            var_symbol = VarSymbol(param_name, param_type)
            self.current_scope.insert(var_symbol)
            behavior_symbol.params.append(var_symbol)
        
        self.visit(node.compound_statement)

        print(behavior_scope)

        self.current_scope = self.current_scope.enclosing_scope
        print('LEAVE scope: %s \n\n' %  behavior_name)
    
    def visit_Agent(self, node):
        agent_name = 'AGENT_' + node.name
        agent_symbol = AgentSymbol(agent_name)
        self.current_scope.insert(agent_symbol)

        print('ENTER scope: %s' %  agent_name)
        # Scope for parameters and local variables
        agent_scope = ScopedSymbolTable(
            scope_name = agent_name,
            scope_level = self.current_scope.scope_level + 1,
            enclosing_scope = self.current_scope
        )
        self.current_scope = agent_scope

        # Insert parameters into the procedure scope
        for param in node.params:
            param_name = param.var_node.value
            param_type = None		# self.current_scope.lookup(param_name)
            var_symbol = VarSymbol(param_name, param_type)
            self.current_scope.insert(var_symbol)
            agent_symbol.params.append(var_symbol)
        
        self.visit(node.compound_statement)

        print(agent_scope)

        self.current_scope = self.current_scope.enclosing_scope
        print('LEAVE scope: %s \n\n' %  agent_name)
    
    def visit_Action(self, node):
        action_name = 'ACTION_' + node.name
        action_symbol = ActionSymbol(action_name)
        self.current_scope.insert(action_symbol)

        print('ENTER scope: %s' %  action_name)
        # Scope for parameters and local variables
        action_scope = ScopedSymbolTable(
            scope_name = action_name,
            scope_level = self.current_scope.scope_level + 1,
            enclosing_scope = self.current_scope
        )
        self.current_scope = action_scope

        # Insert parameters into the procedure scope
        for param in node.params:
            param_name = param.var_node.value
            param_type = None		# self.current_scope.lookup(param_name)
            var_symbol = VarSymbol(param_name, param_type)
            self.current_scope.insert(var_symbol)
            action_symbol.params.append(var_symbol)
        
        self.visit(node.compound_statement)

        print(action_scope)

        self.current_scope = self.current_scope.enclosing_scope
        print('LEAVE scope: %s \n\n' %  action_name)

    def visit_Compound(self, node):
        for child in node.children:
            self.visit(child)

    def visit_NoOp(self, node):
        return None

    def visit_Assign(self, node):
        # 'x = 5', node is '='
        #     = 
        #   /   \
        #  x     5
        var_name = node.left.value
        type_symbol = self.current_scope.lookup(var_name)
        if type_symbol is None:
            type_symbol = self.visit(node.right)
            var_symbol = VarSymbol(var_name, type_symbol)
            self.current_scope.insert(var_symbol)

    def visit_Var(self, node):
        var_name = node.value
        var_symbol = self.current_scope.lookup(var_name)

        if var_symbol is None:
            raise Exception("Error: Symbol(identifier) not found '%s'" % var_name)
        else:
            return var_symbol
