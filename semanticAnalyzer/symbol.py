class Symbol(object):
    def __init__(self, name, type=None):
        self.name = name
        self.type = type
        self.scope_level = 0

class VarSymbol(Symbol):
    def __init__(self, name, type):
        super().__init__(name, type)

    def __str__(self):
        return "<{class_name}(name='{name}', type='{type}')>".format(
            class_name=self.__class__.__name__,
            name=self.name,
            type=self.type,
        )

    __repr__ = __str__

class BuiltinTypeSymbol(Symbol):
    def __init__(self, name):
        super().__init__(name=name, type=name)

    def __str__(self):
        return self.name

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

    def __str__(self):
        return '<{class_name}(name={name}, formal_parameters={formal_params})>'.format(
            class_name=self.__class__.__name__,
            name=self.name,
            formal_params=self.formal_params,
        )

    __repr__ = __str__

class ActionSymbol(ProcedureSymbol):
    def __init__(self, name, formal_params=None):
        super().__init__(name)

class AgentSymbol(Symbol):
    def __init__(self, name):
        super().__init__(name)
        self.abilities = []

class BehaviorSymbol(ProcedureSymbol):
    def __init__(self, name, formal_params=None):
        super().__init__(name)

class TaskSymbol(ProcedureSymbol):
    def __init__(self, name, formal_params=None):
        super().__init__(name)