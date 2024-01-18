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
    def __init__(self, name, compound_statement):
        self.name = name
        self.compound_statement = compound_statement

class Agent(AST):
    def __init__(self, name, compound_statement):
        self.name = name
        self.compound_statement = compound_statement
    
class Behavior(AST):
    def __init__(self, name, compound_statement):
        self.name = name
        self.compound_statement = compound_statement
  
class Task(AST):
    def __init__(self, name, compound_statement):
        self.name = name
        self.compound_statement = compound_statement

class MainTask(AST):
    def __init__(self, compound_statement):
        self.compound_statement = compound_statement

class Program(AST):
    def __init__(self, port, action, agent, behavior, task, mainTask):
        self.port = port
        self.action = action
        self.agent = agent
        self.behavior = behavior
        self.task = task
        self.mainTask = mainTask