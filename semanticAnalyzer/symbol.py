from enum import Enum


class SymbolCategory(Enum):  # Symbol Category for Procedure
	PROGRAM = 'PROGRAM'
	MAIN = 'MAIN'
	TASK = 'TASK'
	BEHAVIOR = 'BEHAVIOR'
	ACTION = 'ACTION'
	AGENT = 'AGENT'
	LIBRARY = 'LIBRARY'
	LIBRARY_CALL = 'LIBRARY_CALL'
	AGENT_RANGE = 'AGENT_RANGE'


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


class LibrarySymbol(VarSymbol):
	def __init__(self, name):
		super().__init__(name, SymbolCategory.LIBRARY)


class LibraryCallSymbol(Symbol):
	def __init__(self, library, postfixes, arguments):
		super().__init__(library.value, SymbolCategory.LIBRARY_CALL)
		self.postfixes = [postfix.value for postfix in postfixes]
		if arguments is not None:
			self.arguments = [argument.value for argument in arguments if argument is not None]
		else:
			self.arguments = []


	def __repr__(self):
		postfixes_string = '.'.join(self.postfixes)
		arguments_string = '(' + ','.join(self.arguments) +')'
		return '<{class_name} {library}{postfixes}{arguments}>'.format(
			class_name=self.__class__.__name__,
			library = self.name,
			postfixes = postfixes_string,
			arguments = arguments_string
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
	def __init__(self, name, category, formal_params=None):
		super().__init__(name=name, category=category)
		# a list of formal parameters
		self.formal_params = [] if formal_params is None else formal_params
		# a reference to procedure's body (AST sub-tree)
		self.ast = None

	def __repr__(self):
		return '<{class_name}(name={name}, formal_parameters={formal_params})>'.format(
			class_name=self.__class__.__name__,
			name=self.name,
			formal_params=[prm.name for prm in self.formal_params]
		)


class ActionSymbol(ProcedureSymbol):
	def __init__(self, name, formal_params=None):
		super().__init__(name=name, category=SymbolCategory.ACTION)


class AgentSymbol(Symbol):
	def __init__(self, name):
		super().__init__(name, category=SymbolCategory.AGENT)
		self.abilities = []
		self.ast = None

	def __repr__(self):
		return '<{class_name}(name={name}, abilities={abilities})>'.format(
			class_name=self.__class__.__name__,
			name=self.name,
			abilities=[ab.name for ab in self.abilities],
		)


class AgentRangeSymbol(Symbol):
	def __init__(self, agent, start, end):
		self.agent = agent
		self.start = start
		self.end = end

	def __repr__(self):
		return '{agent}[{start}~{end}]'.format(
			agent=self.agent,
			start=self.start,
			end=self.end
		)


class BehaviorSymbol(ProcedureSymbol):
	def __init__(self, name, formal_params=None):
		super().__init__(name=name, category=SymbolCategory.BEHAVIOR)


class TaskSymbol(Symbol):
	def __init__(self, name, formal_params_agent_list=None, formal_params=None):
		super().__init__(name=name, category=SymbolCategory.TASK)
		self.formal_params_agent_list = [] if formal_params_agent_list is None else formal_params_agent_list
		self.formal_params = [] if formal_params is None else formal_params
		# a reference to procedure's body (AST sub-tree)
		self.ast = None

	def __repr__(self):
		return '<{class_name}(name={name}, formal_params_agent_list={formal_params_agent_list}, formal_params={formal_params})>'.format(
			class_name=self.__class__.__name__,
			name=self.name,
			formal_params_agent_list=self.formal_params_agent_list,
			formal_params=[prm.name for prm in self.formal_params]
		)
