from base.error import SemanticError, ErrorCode
from base.nodeVisitor import NodeVisitor
from lexer.token import TokenType
from semanticAnalyzer.symbolTable import *


class SemanticAnalyzer(NodeVisitor):
	def __init__(self, log_or_not=False):
		self.current_scope = None
		self.global_scope = None
		self.log_or_not = log_or_not

	def visit_Program(self, node):
		self.log('Enter scope: global')
		program_scope = ScopedSymbolTable(
			scope_name='global',
			scope_level=1,
			enclosing_scope=self.current_scope,  # None
			log_or_not=self.log_or_not
		)
		program_scope._init_builtins()
		self.global_scope = program_scope
		self.current_scope = self.global_scope

		# visit subtree
		self.visit(node.action_list)
		self.visit(node.agent_list)
		self.visit(node.behavior_list)
		self.visit(node.task_list)
		self.visit(node.main)

		self.log(self.current_scope)
		self.current_scope = self.current_scope.enclosing_scope
		self.log('Leave scope: global')

	def visit_Port(self, node):
		pass

	def visit_ActionList(self, node):
		for child in node.children:
			self.visit(child)

	def visit_Action(self, node):
		action_name = node.name
		if self.global_scope.lookup(action_name) is not None:
			self.error(error_code=ErrorCode.DUPLICATE_ID, token=node.token)
		action_symbol = ActionSymbol(action_name)
		# Insert parameters into the action_symbol.formal_params
		for param in node.formal_params.children:
			param_name = param.value
			param_category = None
			var_symbol = VarSymbol(param_name, param_category)
			action_symbol.formal_params.append(var_symbol)
		self.global_scope.insert(action_symbol)

		self.log('Enter ACTION scope: %s' % action_name)
		# Scope for parameters and local variables
		action_scope = ScopedSymbolTable(
			scope_name=action_name,
			scope_level=self.current_scope.scope_level + 1,
			enclosing_scope=self.current_scope,
			log_or_not=self.log_or_not
		)
		self.current_scope = action_scope

		# Insert parameters into the action scope
		for param in node.formal_params.children:
			param_name = param.value
			param_category = None  # self.current_scope.lookup(param_name)
			var_symbol = VarSymbol(param_name, param_category)
			self.current_scope.insert(var_symbol)

		self.visit(node.compound_statement)
		self.log(action_scope)
		self.current_scope = self.current_scope.enclosing_scope
		self.log('Leave ACTION scope: %s \n\n' % action_name)
		action_symbol.ast = node

	def visit_AgentList(self, node):
		for child in node.children:
			self.visit(child)

	def visit_Agent(self, node):
		agent_name = node.name
		if self.global_scope.lookup(agent_name) is not None:
			self.error(error_code=ErrorCode.DUPLICATE_ID, token=node.token)
		agent_symbol = AgentSymbol(agent_name)
		# Insert agent_symbol into the global scope
		for ability in node.abilities.children:
			ability_name = ability.value
			ability_category = None
			ability_symbol = self.global_scope.lookup(ability_name, log_or_not=False)
			if ability_symbol is None:
				self.error(error_code=ErrorCode.ID_NOT_FOUND, token=ability.token)
			agent_symbol.abilities.append(ability_symbol)
		self.global_scope.insert(agent_symbol)

		self.log('Enter AGENT scope: %s' % agent_name)
		# Scope for parameters and local variables
		agent_scope = ScopedSymbolTable(
			scope_name=agent_name,
			scope_level=self.current_scope.scope_level + 1,
			enclosing_scope=self.current_scope,
			log_or_not=self.log_or_not
		)
		self.current_scope = agent_scope
		# Don't need to insert abilities into the agent scope
		for ability in node.abilities.children:
			ability_name = ability.value
			ability_category = self.global_scope.lookup(ability_name, log_or_not=False)
			var_symbol = VarSymbol(ability_name, ability_category)
			self.current_scope.insert(var_symbol, log_or_not=False)

		self.log(agent_scope)
		# for ability in agent_symbol.abilities:
		#     self.log(ability)
		self.current_scope = self.current_scope.enclosing_scope
		self.log('Leave AGENT scope: %s \n\n' % agent_name)
		agent_symbol.ast = node

	def visit_AgentCall(self, node):
		agent_name = node.agent.value
		agent_symbol = self.global_scope.lookup(agent_name)
		if agent_symbol is None:
			self.error(error_code=ErrorCode.ID_NOT_FOUND, token=node.agent.token)
		self.current_scope.insert(agent_symbol)
		node.symbol = agent_symbol

	def visit_AgentCallList(self, node):
		for child in node.children:
			self.visit(child)

	def visit_BehaviorList(self, node):
		for child in node.children:
			self.visit(child)

	def visit_Behavior(self, node):
		behavior_name = node.name
		if self.global_scope.lookup(behavior_name) is not None:
			self.error(error_code=ErrorCode.DUPLICATE_ID, token=node.token)
		behavior_symbol = BehaviorSymbol(behavior_name)
		# Insert parameters into the behavior_symbol.formal_params.
		for param in node.formal_params.children:
			param_name = param.value
			param_category = None
			var_symbol = VarSymbol(param_name, param_category)
			behavior_symbol.formal_params.append(var_symbol)
		# Insert behavior_symbol into the global scope
		self.global_scope.insert(behavior_symbol)

		self.log('Enter BEHAVIOR scope: %s' % behavior_name)
		# Scope for parameters and local variables
		behavior_scope = ScopedSymbolTable(
			scope_name=behavior_name,
			scope_level=self.current_scope.scope_level + 1,
			enclosing_scope=self.current_scope,
			log_or_not=self.log_or_not
		)
		self.current_scope = behavior_scope

		# Insert parameters into the behavior scope
		for param in node.formal_params.children:
			param_name = param.value
			param_category = None  # self.current_scope.lookup(param_name)
			var_symbol = VarSymbol(param_name, param_category)
			self.current_scope.insert(var_symbol)

		# visit routine_block before goal_block,
		# because variables may be defined in routine_block
		self.visit(node.init_block)
		self.visit(node.routine_block)
		self.visit(node.goal_block)
		self.log(behavior_scope)
		self.current_scope = self.current_scope.enclosing_scope
		self.log('Leave BEHAVIOR scope: %s \n\n' % behavior_name)
		behavior_symbol.ast = node

	def visit_FunctionCall(self, node):
		function_name = node.name
		function_symbol = self.global_scope.lookup(function_name)
		if function_symbol is None:
			# Check whether it is an RPC call
			if_actionSymbol = self.global_scope.lookup(self.current_scope.scope_name, log_or_not=False)
			if isinstance(if_actionSymbol, ActionSymbol):
				self.log("%s is a RPC_call." % node.name)
				function_symbol = RpcCallSymbol(function_name)
				function_symbol.ast = None
			else:
				self.error(error_code=ErrorCode.ID_NOT_FOUND, token=node.token)
		actual_params = node.actual_params
		if not isinstance(function_symbol, RpcCallSymbol):
			formal_params = function_symbol.formal_params
			if len(actual_params) != len(formal_params):
				self.error(
					error_code=ErrorCode.WRONG_PARAMS_NUM,
					token=node.token,
				)
		for param_node in actual_params:
			self.visit(param_node)

		# accessed by the interpreter when executing procedure call
		node.symbol = function_symbol
		if isinstance(function_symbol, RpcCallSymbol) or isinstance(function_symbol, ActionSymbol):
			return function_symbol

	def visit_TaskList(self, node):
		for child in node.children:
			self.visit(child)

	def visit_Task(self, node):
		task_name = node.name
		if self.global_scope.lookup(task_name) is not None:
			self.error(error_code=ErrorCode.DUPLICATE_ID, token=node.token)
		task_symbol = TaskSymbol(task_name)
		# Insert task_symbol into the global scope
		for agent_range in node.formal_params_agent_list.children:
			agent_smbl = AgentRangeSymbol(agent_range.agent.value, agent_range.start.value, agent_range.end.value)
			task_symbol.formal_params_agent_list.append(agent_smbl)
		for param in node.formal_params.children:
			param_name = param.value
			param_category = None
			var_symbol = VarSymbol(param_name, param_category)
			task_symbol.formal_params.append(var_symbol)
		self.current_scope.insert(task_symbol)

		self.log('Enter TASK scope: %s' % task_name)
		# Scope for parameters and local variables
		task_scope = ScopedSymbolTable(
			scope_name=task_name,
			scope_level=self.current_scope.scope_level + 1,
			enclosing_scope=self.current_scope,
			log_or_not=self.log_or_not
		)
		self.current_scope = task_scope

		# Insert parameters into the procedure scope
		for agent_range in node.formal_params_agent_list.children:
			agt_smbl = VarSymbol(agent_range.agent.value, SymbolCategory.AGENT_RANGE)
			self.current_scope.insert(agt_smbl)
			st_smbl = VarSymbol(agent_range.start.value, None)
			self.current_scope.insert(st_smbl)
			nd_smbl = VarSymbol(agent_range.end.value, None)
			self.current_scope.insert(nd_smbl)
		for param in node.formal_params.children:
			param_name = param.value
			param_category = None  # self.current_scope.lookup(param_name)
			var_symbol = VarSymbol(param_name, param_category)
			self.current_scope.insert(var_symbol)

		# visit routine_block before goal_block,
		# because variables may be defined in routine_block
		self.visit(node.init_block)
		self.visit(node.routine_block)
		self.visit(node.goal_block)
		self.log(task_scope)
		self.current_scope = self.current_scope.enclosing_scope
		self.log('Leave TASK scope: %s \n\n' % task_name)
		task_symbol.ast = node

	def visit_TaskCall(self, node):
		task_name = node.name
		task_symbol = self.global_scope.lookup(task_name)
		if task_symbol is None:
			self.error(error_code=ErrorCode.ID_NOT_FOUND, token=node.token)

		for agt_range in node.actual_params_agent_list:
			agt_name = agt_range.agent.value
			agt_symbol = self.current_scope.lookup(name=agt_name, current_scope_only=True)
			if agt_symbol is None:
				self.error(error_code=ErrorCode.ID_NOT_FOUND, token=node.token)

		if len(node.actual_params_agent_list) != len(task_symbol.formal_params_agent_list):
			self.error(error_code=ErrorCode.WRONG_PARAMS_NUM, token=node.token)
		for agent_range_node in node.actual_params_agent_list:
			self.visit(agent_range_node)
		if len(node.actual_params) != len(task_symbol.formal_params):
			self.error(error_code=ErrorCode.WRONG_PARAMS_NUM, token=node.token)
		for param_node in node.actual_params:
			self.visit(param_node)

		# accessed by the interpreter when executing procedure call
		node.symbol = task_symbol

	def visit_TaskOrder(self, node):
		self.visit(node.agent_range)
		self.visit(node.function_call_statements)

	def visit_TaskEach(self, node):
		self.visit(node.agent_range)
		self.visit(node.function_call_statements)

	def visit_AgentRange(self, node):
		agent_symbol = self.visit(node.agent)
		if (agent_symbol.category != SymbolCategory.AGENT_RANGE) and (agent_symbol.category != SymbolCategory.AGENT):
			self.error(error_code=ErrorCode.DUPLICATE_ID, token=node.agent.token)
		self.visit(node.start)
		self.visit(node.end)

	def visit_Main(self, node):
		self.log('Enter MAIN scope')
		main_scope = ScopedSymbolTable(
			scope_name="Main",
			scope_level=self.current_scope.scope_level + 1,
			enclosing_scope=self.current_scope,
			log_or_not=self.log_or_not
		)
		self.current_scope = main_scope
		self.visit(node.agent_call_list)
		self.visit(node.task_call)
		self.current_scope = self.current_scope.enclosing_scope
		self.log('Leave MAIN scope')

	def visit_InitBlock(self, node):
		self.visit(node.compound_statement)

	def visit_GoalBlock(self, node):
		self.visit(node.statements)
		self.visit(node.goal)

	def visit_RoutineBlock(self, node):
		for child in node.children:
			self.visit(child)

	def visit_Compound(self, node):
		for child in node.children:
			self.visit(child)

	def visit_IfElse(self, node):
		self.visit(node.expression)
		self.visit(node.true_compound)
		if node.false_compound is not None:
			self.visit(node.false_compound)

	def visit_Return(self, node):
		self.visit(node.variable)

	def visit_Expression(self, node):
		self.visit(node.expr)

	def visit_Var(self, node):
		var_name = node.value
		var_symbol = self.current_scope.lookup(var_name)
		if var_symbol is None:
			self.error(error_code=ErrorCode.ID_NOT_FOUND, token=node.token)
		else:
			return var_symbol

	def visit_Num(self, node):
		if isinstance(node.value, int):
			return BuiltinTypeSymbol('INTEGER')
		else:
			return BuiltinTypeSymbol('FLOAT')

	def visit_String(self, node):
		return BuiltinTypeSymbol('STRING')

	def visit_BinOp(self, node):
		if node.op.category == TokenType.PLUS:
			left_symbol = self.visit(node.left)
			right_symbol = self.visit(node.right)
			if isinstance(left_symbol, BuiltinTypeSymbol):
				return left_symbol
			elif isinstance(left_symbol, VarSymbol) and left_symbol.category is not None:
				return left_symbol.category
			elif isinstance(right_symbol, BuiltinTypeSymbol):
				return right_symbol
			elif isinstance(right_symbol, VarSymbol) and right_symbol.category is not None:
				return right_symbol.category
			else:
				return None
		elif node.op.category == TokenType.MINUS:
			left_symbol = self.visit(node.left)
			right_symbol = self.visit(node.right)
			if isinstance(left_symbol, BuiltinTypeSymbol):
				return left_symbol
			elif isinstance(left_symbol, VarSymbol) and left_symbol.category is not None:
				return left_symbol.category
			elif isinstance(right_symbol, BuiltinTypeSymbol):
				return right_symbol
			elif isinstance(right_symbol, VarSymbol) and right_symbol.category is not None:
				return right_symbol.category
			else:
				return None
		elif node.op.category == TokenType.MUL:
			left_symbol = self.visit(node.left)
			right_symbol = self.visit(node.right)
			if isinstance(left_symbol, BuiltinTypeSymbol):
				return left_symbol
			elif isinstance(left_symbol, VarSymbol) and left_symbol.category is not None:
				return left_symbol.category
			elif isinstance(right_symbol, BuiltinTypeSymbol):
				return right_symbol
			elif isinstance(right_symbol, VarSymbol) and right_symbol.category is not None:
				return right_symbol.category
			else:
				return None
		elif node.op.category == TokenType.DIV:
			left_symbol = self.visit(node.left)
			right_symbol = self.visit(node.right)
			if isinstance(left_symbol, BuiltinTypeSymbol):
				return left_symbol
			elif isinstance(left_symbol, VarSymbol) and left_symbol.category is not None:
				return left_symbol.category
			elif isinstance(right_symbol, BuiltinTypeSymbol):
				return right_symbol
			elif isinstance(right_symbol, VarSymbol) and right_symbol.category is not None:
				return right_symbol.category
			else:
				return None
		elif node.op.category == TokenType.ASSIGN:
			left_var_name = node.left.value
			category_symbol = self.current_scope.lookup(left_var_name)
			if category_symbol is None:
				right_symbol = self.visit(node.right)
				if isinstance(right_symbol, BuiltinTypeSymbol):
					var_symbol = VarSymbol(left_var_name, right_symbol)
				else:
					var_symbol = VarSymbol(left_var_name, right_symbol.category)
				self.current_scope.insert(var_symbol)
			else:
				self.visit(node.right)	# node.right is a action_call, should visit it to set node.symbol.ast
		elif node.op.category == TokenType.RPC_CALL:
			left_var_name = node.left.value
			var_symbol = VarSymbol(left_var_name, self.visit(node.right))
			self.current_scope.insert(var_symbol)
		elif node.op.category == TokenType.PUT:
			expr_node = node.left
			expr_symbol = self.visit(expr_node)
			stigmergy_name = node.right.value
			stigmergy_symbol = self.global_scope.lookup(stigmergy_name)
			if stigmergy_symbol is None:
				var_symbol = VarSymbol(stigmergy_name, expr_symbol)
				self.global_scope.insert(var_symbol)
		elif node.op.category == TokenType.GET:
			var_node = node.left
			var_symbol = self.current_scope.lookup(var_node.value)
			# if var_symbol is not None:
			# 	self.error(error_code=ErrorCode.DUPLICATE_ID, token=node.left.token)
			stigmergy_name = node.right.value
			stigmergy_symbol = self.global_scope.lookup(stigmergy_name)
			# if stigmergy_symbol is None:
			# 	self.error(error_code=ErrorCode.ID_NOT_FOUND, token=node.right.token)
			# var_symbol = VarSymbol(var_node.value, stigmergy_symbol.category)
			var_symbol = VarSymbol(var_node.value, None)
			self.current_scope.insert(var_symbol)
		else:
			# do not need to check symbol category
			# because both side can be formal_param whose category is 'None' or anything
			return
		'''
		else: 
			  comparable symbol
			left_category = self.visit(node.left)
			if left_category is not None:
				while hasattr(left_category, 'category'):
					left_category = left_category.category
			right_category = self.visit(node.right)
			if right_category is not None :
				while hasattr(right_category, 'category'):
					right_category = right_category.category
			if type(left_category) == type(right_category):
				return left_category
			else:
				raise Exception("Different categorys on both sides of BinOp")
		'''

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
