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

class Action(AST):
    def __init__(self, name, formal_params, compound_statement):
        self.name = name
        self.formal_params = formal_params  # a list of Param nodes
        self.compound_statement = compound_statement

class ActionList(AST):
    def __init__(self):
        self.children = []

class Agent(AST):
    def __init__(self, name, formal_params, compound_statement):
        self.name = name
        self.formal_params = formal_params  # a list of Param nodes
        self.compound_statement = compound_statement

class AgentList(AST):
    def __init__(self):
        self.children = []
    
class Behavior(AST):
    def __init__(self, name, formal_params, init_block, goal_block, routine_block):
        self.name = name
        self.formal_params = formal_params  # a list of Param nodes
        self.init_block = init_block
        self.goal_block = goal_block
        self.routine_block = routine_block

class BehaviorList(AST):
    def __init__(self):
        self.children = []

class Task(AST):
    def __init__(self, name, formal_params, compound_statement):
        self.name = name
        self.formal_params = formal_params  # a list of Param nodes
        self.compound_statement = compound_statement

class TaskList(AST):
    def __init__(self):
        self.children = []

class TaskCall(AST):
    def __init__(self, name, actual_params, token):
        self.name = name
        self.actual_params = actual_params  # a list of AST nodes
        self.token = token
        self.symbol = None          # a reference to task symbol
        
class MainTask(AST):
    def __init__(self, compound_statement):
        self.compound_statement = compound_statement

class Program(AST):
    def __init__(self, port, action_list, agent, behavior, task, mainTask):
        self.port = port
        self.action_list = action_list
        self.agent = agent
        self.behavior = behavior
        self.task = task
        self.mainTask = mainTask

class Param(AST):
    def __init__(self, var_node):   #, type_node):
        self.var_node = var_node
        # self.type_node = type_node