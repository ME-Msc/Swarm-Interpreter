class Symbol(object):
    def __init__(self, name, category=None):
        self.name = name
        self.category = category
        self.scope_level = 0
    
    def __str__(self):
        return self.__repr__()

class VarSymbol(Symbol):
    def __init__(self, name, category):
        super().__init__(name, category)

    def __repr__(self):
        return "<{class_name}(name='{name}', category='{category}')>".format(
            class_name=self.__class__.__name__,
            name=self.name,
            category=self.category,
        )

class BuiltinTypeSymbol(object):
    def __init__(self, name):
        self.name = name
        # Don't need category

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<{class_name}(name='{name}')>".format(
            class_name=self.__class__.__name__,
            name=self.name,
        )

class ProcedureSymbol(Symbol):
    def __init__(self, name, formal_params=None):
        super().__init__(name)
        # a list of formal parameters
        self.formal_params = [] if formal_params is None else formal_params
        # a reference to procedure's body (AST sub-tree)
        self.ast = None

    def __repr__(self):
        return '<{class_name}(name={name}, formal_parameters={formal_params})>'.format(
            class_name=self.__class__.__name__,
            name=self.name,
            formal_params=self.formal_params,
        )

class ActionSymbol(ProcedureSymbol):
    def __init__(self, name, formal_params=None):
        super().__init__(name)

class AgentSymbol(Symbol):
    def __init__(self, name):
        super().__init__(name)
        self.abilities = []
        self.ast = None

    def __repr__(self):
        return '<{class_name}(name={name}, abilities={abilities})>'.format(
            class_name=self.__class__.__name__,
            name=self.name,
            abilities=[ab.name for ab in self.abilities],
        )

class BehaviorSymbol(ProcedureSymbol):
    def __init__(self, name, formal_params=None):
        super().__init__(name)

class TaskSymbol(ProcedureSymbol):
    def __init__(self, name, formal_params=None):
        super().__init__(name)