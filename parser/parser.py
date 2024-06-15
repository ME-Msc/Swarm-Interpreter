from base.error import ParserError, ErrorCode
from lexer.token import *
from parser.element import *
from parser.operator import NoOp, UnaryOp, BinOp


class BaseParser(object):
	def __init__(self, lexer):
		self.lexer = lexer
		# set current token to the first token taken from the input
		self.current_token = self.lexer.get_next_token()

	def get_next_token(self):
		return self.lexer.get_next_token()

	def peek_next_token(self):
		return self.lexer.peek_next_token()

	def error(self, error_code, token):
		raise ParserError(
			error_code=error_code,
			token=token,
			message=f'{error_code.value} -> {token}',
		)

	def eat(self, token_type):
		# compare the current token type with the passed token
		# type and if they match then "eat" the current token
		# and assign the next token to the self.current_token,
		# otherwise raise an exception.
		if self.current_token.category == token_type:
			self.current_token = self.get_next_token()
		else:
			self.error(
				error_code=ErrorCode.UNEXPECTED_TOKEN,
				token=self.current_token,
			)


class Parser(BaseParser):
	def __init__(self, lexer):
		super().__init__(lexer)

	def program(self):
		# program ::= library_list action_list agent_list behavior_list task_list main
		library_list = self.library_list()
		action_list = self.action_list()
		agent_list = self.agent_list()
		behavior_list = self.behavior_list()
		task_list = self.task_list()
		main_node = self.main()
		program_node = Program(library_list=library_list, action_list=action_list, agent_list=agent_list,
							   behavior_list=behavior_list, task_list=task_list, main=main_node)
		return program_node

	def library_list(self):
		# library_list ::= library+
		root = LibraryList()
		while self.current_token.category == TokenType.IMPORT:
			root.children.append(self.library())
		return root

	def library(self):
		# library ::= "Import" variable
		self.eat(TokenType.IMPORT)
		node = self.variable()
		node = Library(node)
		return node
	
	def library_call(self):
		# library_call ::= variable ( "." variable )* ( '(' actual_parameters ')' )?
		library = self.variable()
		postfixes = []
		while self.current_token.category == TokenType.DOT:
			self.eat(TokenType.DOT)
			postfix = self.variable()
			postfixes.append(postfix)
		actual_params = None	# variable in library
		if self.current_token.category == TokenType.L_PAREN:
			actual_params = []	# function in library
			self.eat(TokenType.L_PAREN)
			if self.current_token.category != TokenType.R_PAREN:
				actual_params = self.actual_parameters()
			self.eat(TokenType.R_PAREN)
		node = LibraryCall(library=library, postfixes=postfixes, arguments=actual_params)
		return node

	def action_list(self):
		# action_list ::= action+
		root = ActionList()
		while self.current_token.category == TokenType.ACTION:
			root.children.append(self.action())
		return root

	def action(self):
		# action ::= "Action" variable "(" formal_parameters? ")" action_compound
		self.eat(TokenType.ACTION)
		var_node = self.variable()
		action_name = var_node.value
		self.eat(TokenType.L_PAREN)
		formal_params_nodes = FormalParams()  # No formal parameters
		if self.current_token.category != TokenType.R_PAREN:
			formal_params_nodes = self.formal_parameters()
		self.eat(TokenType.R_PAREN)
		action_compound_node = self.action_compound()
		node = Action(name=action_name, formal_params=formal_params_nodes, compound_statement=action_compound_node)
		return node

	def action_compound(self):
		# action_compound ::= "{" action_statement* "}"
		self.eat(TokenType.L_BRACE)
		root = Compound()
		while self.current_token.category != TokenType.R_BRACE:
			node = self.action_statement()
			if not isinstance(node, NoOp):
				root.children.append(node)
		self.eat(TokenType.R_BRACE)
		return root

	def action_statement(self):
		# action_statement ::= action_if_else
		# 					| action_return_statement
		# 					| library_call ";"
		# 					| assignment_statement
		# 					| put_statement
		# 					| get_statement
		# 					| empty_statement 
		if self.current_token.category == TokenType.IF:
			node = self.action_if_else()
		elif self.current_token.category == TokenType.RETURN:
			node = self.action_return_statement()
		elif self.current_token.category == TokenType.ID and self.peek_next_token().category == TokenType.DOT:
			node = self.library_call()
			self.eat(TokenType.SEMI)
		elif self.current_token.category == TokenType.ID and self.peek_next_token().category == TokenType.ASSIGN:
			node = self.assignment_statement()
		elif self.current_token.category == TokenType.PUT:
			node = self.put_statement()
		elif self.current_token.category == TokenType.GET:
			node = self.get_statement()
		else:
			node = self.empty_statement()
		return node

	def action_if_else(self):
		# action_if_else ::= "if" "(" expression ")" action_compound ( "else" action_compound )?
		self.eat(TokenType.IF)
		self.eat(TokenType.L_PAREN)
		expr_node = self.expression()
		self.eat(TokenType.R_PAREN)
		true_cmpd_node = self.action_compound()
		false_cmpd_node = None
		if self.current_token.category == TokenType.ELSE:
			self.eat(TokenType.ELSE)
			false_cmpd_node = self.action_compound()
		node = IfElse(expr=expr_node, true_cmpd=true_cmpd_node, false_cmpd=false_cmpd_node)
		return node

	def action_return_statement(self):
		# action_return_statement ::= "return" expression ";"
		self.eat(TokenType.RETURN)
		expr_node = self.expression()
		self.eat(TokenType.SEMI)
		node = Return(expr=expr_node)
		return node

	def agent_list(self):
		# agent_list ::= agent+
		root = AgentList()
		while self.current_token.category == TokenType.AGENT:
			root.children.append(self.agent())
		return root

	def agent(self):
		# agent ::= "Agent" variable "{" ( variable ( "," variable )* )? ";" "}"
		self.eat(TokenType.AGENT)
		var_node = self.variable()
		agent_name = var_node.value
		self.eat(TokenType.L_BRACE)
		ability_root = Compound()
		node = self.variable()
		if not isinstance(node, NoOp):
			ability_root.children.append(node)
			while self.current_token.category != TokenType.SEMI:
				self.eat(TokenType.COMMA)
				node = self.variable()
				ability_root.children.append(node)
			self.eat(TokenType.SEMI)
		agent_node = Agent(name=agent_name, abilities=ability_root)
		self.eat(TokenType.R_BRACE)
		return agent_node

	def agent_call_statement(self):
		# agent_call_statement ::= "Agent" variable integer ";"
		self.eat(TokenType.AGENT)
		agt_node = self.variable()
		cnt_node = self.integer()
		node = AgentCall(agent=agt_node, count=cnt_node)
		self.eat(TokenType.SEMI)
		return node

	def behavior_list(self):
		# behavior_list ::= behavior+
		root = BehaviorList()
		while self.current_token.category == TokenType.BEHAVIOR:
			root.children.append(self.behavior())
		return root

	def behavior(self):
		# behavior ::= "Behavior" variable "(" formal_parameters? ")" "{" behavior_init_block behavior_goal_block behavior_routine_block "}"
		self.eat(TokenType.BEHAVIOR)
		var_node = self.variable()
		behavior_name = var_node.value
		self.eat(TokenType.L_PAREN)
		formal_params_nodes = FormalParams()  # No formal parameters
		if self.current_token.category != TokenType.R_PAREN:
			formal_params_nodes = self.formal_parameters()
		self.eat(TokenType.R_PAREN)
		self.eat(TokenType.L_BRACE)
		init_node = self.behavior_init_block()
		goal_node = self.behavior_goal_block()
		routine_node = self.behavior_routine_block()
		node = Behavior(name=behavior_name, formal_params=formal_params_nodes,
						init_block=init_node, goal_block=goal_node, routine_block=routine_node)
		self.eat(TokenType.R_BRACE)
		return node

	def behavior_init_block(self):
		# behavior_init_block ::= "@init" behavior_compound
		self.eat(TokenType.INIT)
		behavior_compound_node = self.behavior_compound()
		node = InitBlock(compound_statement=behavior_compound_node)
		return node

	def behavior_goal_block(self):
		# behavior_goal_block ::= "@goal" "{" ( behavior_statement* "$" expression )? "}"
		self.eat(TokenType.GOAL)
		self.eat(TokenType.L_BRACE)
		statements_root = Compound()
		if self.current_token.category != TokenType.R_BRACE:
			while self.current_token.category != TokenType.DOLLAR:
				node = self.behavior_statement()
				if not isinstance(node, NoOp):
					statements_root.children.append(node)
			self.eat(TokenType.DOLLAR)
			goal_node = Expression(self.expression())
		else:
			goal_node = Expression(NoOp())
		node = GoalBlock(statements=statements_root, goal=goal_node)
		self.eat(TokenType.R_BRACE)
		return node

	def behavior_routine_block(self):
		# behavior_routine_block ::= "@routine" behavior_compound ( "||" behavior_compound )*
		self.eat(TokenType.ROUTINE)
		root = RoutineBlock()
		node = self.behavior_compound()
		root.children.append(node)
		while self.current_token.category == TokenType.PARALLEL:
			self.eat(TokenType.PARALLEL)
			node = self.behavior_compound()
			root.children.append(node)
		return root

	def behavior_compound(self):
		# behavior_compound ::= "{" behavior_statement* "}"
		self.eat(TokenType.L_BRACE)
		root = Compound()
		while self.current_token.category != TokenType.R_BRACE:
			node = self.behavior_statement()
			if not isinstance(node, NoOp):
				root.children.append(node)
		self.eat(TokenType.R_BRACE)
		return root

	def behavior_statement(self):
		# behavior_statement ::= behavior_if_else
		# 						| function_call_statement
		# 						| assignment_statement
		# 						| put_statement
		# 						| get_statement
		# 						| empty_statement
		if self.current_token.category == TokenType.IF:
			node = self.behavior_if_else()
		elif self.current_token.category == TokenType.ID and self.peek_next_token().category == TokenType.L_PAREN:
			node = self.function_call_statement()
		elif self.current_token.category == TokenType.ID and self.peek_next_token().category == TokenType.ASSIGN:
			node = self.assignment_statement()
		elif self.current_token.category == TokenType.PUT:
			node = self.put_statement()
		elif self.current_token.category == TokenType.GET:
			node = self.get_statement()
		else:
			node = self.empty_statement()
		return node

	def behavior_if_else(self):
		# behavior_if_else ::= "if" "(" expression ")" behavior_compound ( "else" behavior_compound )?
		self.eat(TokenType.IF)
		self.eat(TokenType.L_PAREN)
		expr_node = self.expression()
		self.eat(TokenType.R_PAREN)
		true_cmpd_node = self.behavior_compound()
		false_cmpd_node = None
		if self.current_token.category == TokenType.ELSE:
			self.eat(TokenType.ELSE)
			false_cmpd_node = self.behavior_compound()
		node = IfElse(expr=expr_node, true_cmpd=true_cmpd_node, false_cmpd=false_cmpd_node)
		return node

	def function_call_statement(self):
		# function_call_statement ::= variable "(" actual_parameters? ")" ";"
		function_call = self.variable()
		self.eat(TokenType.L_PAREN)
		actual_params = []
		if self.current_token.category != TokenType.R_PAREN:
			actual_params = self.actual_parameters()
		self.eat(TokenType.R_PAREN)
		self.eat(TokenType.SEMI)
		node = FunctionCall(
			name=function_call.value,
			actual_params=actual_params,
			token=function_call.token
		)
		return node

	def task_list(self):
		# task_list ::= task+
		root = TaskList()
		while self.current_token.category == TokenType.TASK:
			root.children.append(self.task())
		return root

	def task(self):
		# task ::= "Task" variable "(" formal_parameters_agent_range_list ( "," formal_parameters )? ")" "{" task_init_block task_goal_block task_routine_block "}"
		self.eat(TokenType.TASK)
		var_node = self.variable()
		task_name = var_node.value
		self.eat(TokenType.L_PAREN)
		formal_params_agent_list = self.formal_parameters_agent_range_list()
		formal_params_nodes = FormalParams()  # No formal parameters
		if self.current_token.category != TokenType.R_PAREN:
			self.eat(TokenType.COMMA)
			formal_params_nodes = self.formal_parameters()
		self.eat(TokenType.R_PAREN)
		self.eat(TokenType.L_BRACE)
		init_node = self.task_init_block()
		goal_node = self.task_goal_block()
		routine_node = self.task_routine_block()
		node = Task(name=task_name, formal_params_agent_list=formal_params_agent_list,
					formal_params=formal_params_nodes,
					init_block=init_node, goal_block=goal_node, routine_block=routine_node)
		self.eat(TokenType.R_BRACE)
		return node

	def task_init_block(self):
		# task_init_block ::= "@init" task_compound
		self.eat(TokenType.INIT)
		task_compound_node = self.task_compound()
		node = InitBlock(compound_statement=task_compound_node)
		return node

	def task_goal_block(self):
		# task_goal_block ::= "@goal" "{" ( task_statement* "$" expression )? "}"
		self.eat(TokenType.GOAL)
		self.eat(TokenType.L_BRACE)
		statements_root = Compound()
		if self.current_token.category != TokenType.R_BRACE:
			while self.current_token.category != TokenType.DOLLAR:
				node = self.task_statement()
				if not isinstance(node, NoOp):
					statements_root.children.append(node)
			self.eat(TokenType.DOLLAR)
			goal_node = Expression(self.expression())
		else:
			goal_node = Expression(NoOp())
		node = GoalBlock(statements=statements_root, goal=goal_node)
		self.eat(TokenType.R_BRACE)
		return node

	def task_routine_block(self):
		# task_routine_block ::= "@routine" task_compound ( "||" task_compound )*
		self.eat(TokenType.ROUTINE)
		root = RoutineBlock()
		node = self.task_compound()
		root.children.append(node)
		while self.current_token.category == TokenType.PARALLEL:
			self.eat(TokenType.PARALLEL)
			node = self.task_compound()
			root.children.append(node)
		return root

	def task_compound(self):
		# task_compound ::= "{" task_statement* "}"
		self.eat(TokenType.L_BRACE)
		root = Compound()
		while self.current_token.category != TokenType.R_BRACE:
			node = self.task_statement()
			if not isinstance(node, NoOp):
				root.children.append(node)
		self.eat(TokenType.R_BRACE)
		return root

	def task_statement(self):
		# task_statement ::= task_order
		# 					| task_each
		# 					| task_if_else
		# 					| task_call_statement
		# 					| assignment_statement
		# 					| put_statement
		# 					| get_statement
		# 					| empty_statement
		if self.current_token.category == TokenType.ORDER:
			node = self.task_order()
		elif self.current_token.category == TokenType.EACH:
			node = self.task_each()
		elif self.current_token.category == TokenType.IF:
			node = self.task_if_else()
		elif self.current_token.category == TokenType.ID and self.peek_next_token().category == TokenType.L_PAREN:
			node = self.task_call_statement()
		elif self.current_token.category == TokenType.ID and self.peek_next_token().category == TokenType.ASSIGN:
			node = self.assignment_statement()
		elif self.current_token.category == TokenType.PUT:
			node = self.put_statement()
		elif self.current_token.category == TokenType.GET:
			node = self.get_statement()
		else:
			node = self.empty_statement()
		return node

	def task_order(self):
		# task_order ::= "order" actual_parameters_agent_range "{" function_call_statement* "}"
		self.eat(TokenType.ORDER)
		agt_range = self.actual_parameters_agent_range()
		self.eat(TokenType.L_BRACE)
		func_call_statements = Compound()
		while self.current_token.category != TokenType.R_BRACE:
			func_call_node = self.function_call_statement()
			func_call_statements.children.append(func_call_node)
		self.eat(TokenType.R_BRACE)
		root = TaskOrder(
			agent_range=agt_range,
			function_call_statements=func_call_statements
		)
		return root

	def task_each(self):
		# task_each ::= "each" actual_parameters_agent_range "{" function_call_statement* "}"
		self.eat(TokenType.EACH)
		agt_range = self.actual_parameters_agent_range()
		self.eat(TokenType.L_BRACE)
		func_call_statements = Compound()
		while self.current_token.category != TokenType.R_BRACE:
			func_call_node = self.function_call_statement()
			func_call_statements.children.append(func_call_node)
		self.eat(TokenType.R_BRACE)
		root = TaskEach(
			agent_range=agt_range,
			function_call_statements=func_call_statements
		)
		return root

	def task_if_else(self):
		# task_if_else ::= "if" "(" expression ")" task_compound ( "else" task_compound )?
		self.eat(TokenType.IF)
		self.eat(TokenType.L_PAREN)
		expr_node = self.expression()
		self.eat(TokenType.R_PAREN)
		true_cmpd_node = self.task_compound()
		false_cmpd_node = None
		if self.current_token.category == TokenType.ELSE:
			self.eat(TokenType.ELSE)
			false_cmpd_node = self.task_compound()
		node = IfElse(expr=expr_node, true_cmpd=true_cmpd_node, false_cmpd=false_cmpd_node)
		return node

	def task_call_statement(self):
		# task_call_statement ::= variable "(" actual_parameters_agent_range_list ( "," actual_parameters )? ")" ";"
		task_call = self.variable()
		self.eat(TokenType.L_PAREN)
		actual_params_agent_list = self.actual_parameters_agent_range_list()
		actual_params = []
		if self.current_token.category != TokenType.R_PAREN:
			self.eat(TokenType.COMMA)
			actual_params = self.actual_parameters()
		self.eat(TokenType.R_PAREN)
		self.eat(TokenType.SEMI)
		node = TaskCall(
			name=task_call.value,
			actual_params_agent_list=actual_params_agent_list,
			actual_params=actual_params,
			token=task_call.token
		)
		return node

	def main(self):
		# main ::= "Main" "{" agent_call_statement+ task_call_statement "}"
		self.eat(TokenType.MAIN)
		self.eat(TokenType.L_BRACE)
		agentCallRoot = AgentCallList()
		while self.current_token.category == TokenType.AGENT:
			agent_call_node = self.agent_call_statement()
			agentCallRoot.children.append(agent_call_node)
		task_call_node = self.task_call_statement()
		node = Main(agent_call_list=agentCallRoot, task_call=task_call_node)
		self.eat(TokenType.R_BRACE)
		return node

	def assignment_statement(self):
		# assignment_statement ::= variable "=" ( ( string  ";" ) 
		# 											| function_call_statement
		# 											| ( expression ";" ) )
		left = self.variable()
		token = self.current_token
		self.eat(TokenType.ASSIGN)
		if self.current_token.category == TokenType.STRING:
			right = self.string()
			self.eat(TokenType.SEMI)
		elif self.current_token.category == TokenType.ID and self.peek_next_token().category == TokenType.L_PAREN:
			right = self.function_call_statement()
		else:
			right = self.expression()
			self.eat(TokenType.SEMI)
		node = BinOp(left, token, right)
		return node

	def put_statement(self):
		# put_statement ::= "put" ( string | expression ) "to" variable ";"
		token = self.current_token
		self.eat(TokenType.PUT)
		if self.current_token.category == TokenType.STRING:
			value = self.string()
		else:
			value = self.expression()
		self.eat(TokenType.TO)
		key = self.variable()
		self.eat(TokenType.SEMI)
		node = BinOp(value, token, key)
		return node

	def get_statement(self):
		# get_statement ::= "get" variable "from" variable ";"
		token = self.current_token
		self.eat(TokenType.GET)
		var = self.variable()
		self.eat(TokenType.FROM)
		key = self.variable()
		self.eat(TokenType.SEMI)
		node = BinOp(var, token, key)
		return node

	def empty_statement(self):
		# empty_statement ::= ";"
		self.eat(TokenType.SEMI)
		return NoOp()

	def formal_parameters_agent_range_list(self):
		# formal_parameters_agent_range_list ::= "{" formal_parameters_agent_range ( "," formal_parameters_agent_range )* "}"
		root = AgentRangeList()
		self.eat(TokenType.L_BRACE)
		agent_range_node = self.formal_parameters_agent_range()
		root.children.append(agent_range_node)
		while self.current_token.category == TokenType.COMMA:
			self.eat(TokenType.COMMA)
			agent_range_node = self.formal_parameters_agent_range()
			root.children.append(agent_range_node)
		self.eat(TokenType.R_BRACE)
		return root

	def actual_parameters_agent_range_list(self):
		# actual_parameters_agent_range_list ::= "{" actual_parameters_agent_range ( "," actual_parameters_agent_range )* "}"
		actual_params_agent_list = []
		self.eat(TokenType.L_BRACE)
		agent_range_node = self.actual_parameters_agent_range()
		actual_params_agent_list.append(agent_range_node)
		while self.current_token.category != TokenType.R_BRACE:
			self.eat(TokenType.COMMA)
			agent_range_node = self.actual_parameters_agent_range()
			actual_params_agent_list.append(agent_range_node)
		self.eat(TokenType.R_BRACE)
		return actual_params_agent_list

	def formal_parameters_agent_range(self):
		# formal_parameters_agent_range ::= variable "[" variable "~" variable "]"
		agent = self.variable()
		self.eat(TokenType.L_BRACKET)
		start = self.variable()
		self.eat(TokenType.TILDE)
		end = self.variable()
		self.eat(TokenType.R_BRACKET)
		root = AgentRange(agent=agent, start=start, end=end)
		return root

	def actual_parameters_agent_range(self):
		# actual_parameters_agent_range ::= variable "[" additive_expression "~" additive_expression "]"
		agent = self.variable()
		self.eat(TokenType.L_BRACKET)
		start = self.additive_expression()
		self.eat(TokenType.TILDE)
		end = self.additive_expression()
		self.eat(TokenType.R_BRACKET)
		root = AgentRange(agent=agent, start=start, end=end)
		return root

	def formal_parameters(self):
		# formal_parameters ::= variable ( "," variable )*
		root = FormalParams()
		param_node = self.variable()
		root.children.append(param_node)
		while self.current_token.category == TokenType.COMMA:
			self.eat(TokenType.COMMA)
			param_node = self.variable()
			root.children.append(param_node)
		return root

	def actual_parameters(self):
		# actual_parameters ::= additive_expression ( "," additive_expression )*
		actual_params = []
		node = self.additive_expression()
		actual_params.append(node)
		while self.current_token.category == TokenType.COMMA:
			self.eat(TokenType.COMMA)
			node = self.additive_expression()
			actual_params.append(node)
		return actual_params

	def expression(self):
		# expression ::= logical_not_expression
		return self.logical_not_expression()

	def logical_not_expression(self):
		# logical_not_expression ::= "not"? logical_or_expression
		if self.current_token.category == TokenType.NOT:
			token = self.current_token
			self.eat(TokenType.NOT)
			node = self.logical_or_expression()
			node = UnaryOp(op=token, expr=node)
		else:
			node = self.logical_or_expression()
		return node

	def logical_or_expression(self):
		# logical_or_expression ::= logical_and_expression
		# 							| logical_and_expression "or" logical_or_expression
		node = self.logical_and_expression()
		if self.current_token.category == TokenType.OR:
			token = self.current_token
			self.eat(TokenType.OR)
			node = BinOp(left=node, op=token, right=self.logical_or_expression())
		return node

	def logical_and_expression(self):
		# logical_and_expression ::= equality_expression
		# 						| equality_expression "and" logical_and_expression
		node = self.equality_expression()
		if self.current_token.category == TokenType.AND:
			token = self.current_token
			self.eat(TokenType.AND)
			node = BinOp(left=node, op=token, right=self.equality_expression())
		return node

	def equality_expression(self):
		# equality_expression ::= relational_expression
		# 						| relational_expression "==" equality_expression
		# 						| relational_expression "!=" equality_expression
		node = self.relational_expression()
		if self.current_token.category == TokenType.IS_EQUAL:
			token = self.current_token
			self.eat(TokenType.IS_EQUAL)
			node = BinOp(left=node, op=token, right=self.equality_expression())
		elif self.current_token.category == TokenType.NOT_EQUAL:
			token = self.current_token
			self.eat(TokenType.NOT_EQUAL)
			node = BinOp(left=node, op=token, right=self.equality_expression())
		return node

	def relational_expression(self):
		# relational_expression ::= additive_expression
		# 							| additive_expression "<" relational_expression
		# 							| additive_expression "<=" relational_expression
		# 							| additive_expression ">" relational_expression
		# 							| additive_expression ">=" relational_expression
		node = self.additive_expression()
		if self.current_token.category == TokenType.LESS:
			token = self.current_token
			self.eat(TokenType.LESS)
			node = BinOp(left=node, op=token, right=self.relational_expression())
		elif self.current_token.category == TokenType.LESS_EQUAL:
			token = self.current_token
			self.eat(TokenType.LESS_EQUAL)
			node = BinOp(left=node, op=token, right=self.relational_expression())
		elif self.current_token.category == TokenType.GREATER:
			token = self.current_token
			self.eat(TokenType.GREATER)
			node = BinOp(left=node, op=token, right=self.relational_expression())
		elif self.current_token.category == TokenType.GREATER_EQUAL:
			token = self.current_token
			self.eat(TokenType.GREATER_EQUAL)
			node = BinOp(left=node, op=token, right=self.relational_expression())
		return node

	def additive_expression(self):
		# additive_expression ::= multiplicative_expression ( ( "+" | "-" ) multiplicative_expression )*
		node = self.multiplicative_expression()
		while self.current_token.category in (TokenType.PLUS, TokenType.MINUS):
			token = self.current_token
			if token.category == TokenType.PLUS:
				self.eat(TokenType.PLUS)
			elif token.category == TokenType.MINUS:
				self.eat(TokenType.MINUS)
			node = BinOp(left=node, op=token, right=self.multiplicative_expression())
		return node

	def multiplicative_expression(self):
		# multiplicative_expression ::= primary_expression ( ( "*" | "/" | "%" ) primary_expression )*
		node = self.primary_expression()
		while self.current_token.category in (TokenType.MUL, TokenType.DIV, TokenType.MOD):
			token = self.current_token
			if token.category == TokenType.MUL:
				self.eat(TokenType.MUL)
			elif token.category == TokenType.DIV:
				self.eat(TokenType.DIV)
			elif token.category == TokenType.MOD:
				self.eat(TokenType.MOD)
			node = BinOp(left=node, op=token, right=self.primary_expression())
		return node

	def primary_expression(self):
		# primary_expression ::= ( ( "+" | "-" ) primary_expression )
		# 						| "(" additive_expression ")"
		# 						| library_call
		# 						| variable
		# 						| integer
		# 						| float
		token = self.current_token
		next_token = self.peek_next_token()
		if token.category == TokenType.PLUS:
			self.eat(TokenType.PLUS)
			node = UnaryOp(token, self.primary_expression())
		elif token.category == TokenType.MINUS:
			self.eat(TokenType.MINUS)
			node = UnaryOp(token, self.primary_expression())
		elif token.category == TokenType.L_PAREN:
			self.eat(TokenType.LPAREN)
			node = self.additive_expression()
			self.eat(TokenType.RPAREN)
		elif token.category == TokenType.ID and next_token.category == TokenType.DOT:
			node = self.library_call()
		elif token.category == TokenType.ID:
			node = self.variable()
		elif token.category == TokenType.INTEGER:
			node = self.integer()
		elif token.category == TokenType.FLOAT:
			node = self.float()

		return node

	def variable(self):
		# variable ::= [a-zA-Z] ( [a-zA-Z0-9] | "_" )*
		node = Var(self.current_token)
		self.eat(TokenType.ID)
		return node

	def integer(self):
		# integer ::= "0" | ( [1-9] [0-9]* )
		node = Num(self.current_token)
		self.eat(TokenType.INTEGER)
		return node

	def float(self):
		# float ::= integer "." integer
		node = Num(self.current_token)
		self.eat(TokenType.FLOAT)
		return node

	def string(self):
		# string ::= ( "'" | '"' ) ( #x0009 | #x000A | #x000D | [#x0020-#xFFFF] )*  ( "'" | '"' )
		node = String(self.current_token)
		self.eat(TokenType.STRING)
		return node

	def parse(self):
		node = self.program()
		if self.current_token.category != TokenType.EOF:
			self.error(
				error_code=ErrorCode.UNEXPECTED_TOKEN,
				token=self.current_token,
			)
		return node
