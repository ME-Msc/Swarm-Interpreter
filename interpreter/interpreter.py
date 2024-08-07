import threading
import importlib

from base.error import InterpreterError, ErrorCode
from base.nodeVisitor import NodeVisitor
from interpreter.memory import ARType, ActivationRecord, CallStack
from interpreter.wrapper import Wrapper
from lexer.token import TokenType
from parser.element import FunctionCall, Knowledge, KnowledgeQueue
from parser.operator import BinOp
from semanticAnalyzer.symbol import SymbolCategory

# import concurrent.futures

LogLock = threading.Lock()


class Interpreter(NodeVisitor):
	def __init__(self, tree, log_or_not=False):
		self.tree = tree
		self.agent_abilities = {}
		self.log_or_not = log_or_not
		self.call_stack = CallStack()
		self.return_value = None
		self.wrapper = Wrapper()

	def log(self, msg):
		if self.log_or_not:
			print(msg)

	def error(self, error_code, token):
		raise InterpreterError(
			error_code=error_code,
			token=token,
			message=f'{error_code.value} -> {token}',
		)

	def visit_Program(self, node):
		self.visit(node.platform)
		CALL_STACK = self.call_stack

		self.log(f'ENTER: Program')
		ar = ActivationRecord(
			name="Program",
			category=ARType.PROGRAM,
			nesting_level=0,
		)
		CALL_STACK.push(ar)
		self.visit(node.main, wrapper=self.wrapper)

		self.log(str(CALL_STACK))
		CALL_STACK = CALL_STACK.pop()
		LogLock.acquire()
		self.log(f'LEAVE: Program')
		self.log(str(CALL_STACK))
		LogLock.release()

	def visit_Platform(self, node):
		platform = importlib.import_module(f'libs.{node.name.value}')
		platform_wrapper = getattr(platform, node.name.value+"Wrapper")()
		self.wrapper = platform_wrapper

	def visit_LibraryCall(self, node, **kwargs):
		CALL_STACK = self.call_stack
		if "call_stack" in kwargs:
			CALL_STACK = kwargs["call_stack"]

		wrapper = kwargs["wrapper"]

		goal_caller = None
		for ar in CALL_STACK.peek_all():
			if ar.category == ARType.BEHAVIOR:
				goal_caller = ('Behaviors', ar.name)
				break
			elif ar.category == ARType.TASK:
				goal_caller = ('Tasks', ar.name)
				break

		library = importlib.import_module(f'libs.{node.library.value}')
		attr = getattr(library, node.postfixes[0].value, wrapper)
		for postfix_item in node.postfixes[1:]:
			attr = getattr(attr, postfix_item.value, wrapper)
		if node.arguments is not None:
			args = []
			for arg in node.arguments:
				actual_arg = self.visit(arg, **kwargs)
				args.append(actual_arg)
			attr = attr(*args, goal_caller=goal_caller, **kwargs)
		return attr

	def visit_Action(self, node, **kwargs):
		self.visit(node.compound_statement, **kwargs)

	def visit_Agent(self, node, **kwargs):
		abilities = []
		for child in node.abilities.children:
			abilities.append(child.value)
		return abilities

	def visit_AgentCall(self, node, **kwargs):
		CALL_STACK = self.call_stack
		if "call_stack" in kwargs:
			CALL_STACK = kwargs["call_stack"]

		agt_smbl = node.symbol
		agt_name = agt_smbl.name
		self.agent_abilities[agt_name] = self.visit(agt_smbl.ast, **kwargs)
		cnt = self.visit(node.count, **kwargs)
		ar:ActivationRecord = CALL_STACK.peek()

		if agt_name not in ar:
			ar[agt_name] = (agt_name, 0, cnt)
		else:
			self.error(error_code=ErrorCode.DUPLICATE_ID, token=node.agent.token)
		agents_list = [f"{agt_name}_{i}" for i in range(cnt)]
		kwargs["wrapper"].set_home(agents_list=agents_list)

	def visit_Behavior(self, node, **kwargs):
		CALL_STACK = self.call_stack
		if "call_stack" in kwargs:
			CALL_STACK = kwargs["call_stack"]
		behavior_name = node.name
		vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'

		goal_reached = kwargs["goal_reached"]
		if behavior_name not in goal_reached["Behaviors"]:
			goal_reached["Behaviors"][behavior_name] = {}
		my_goal_reached = threading.Event()
		goal_reached["Behaviors"][behavior_name][vehicle_name] = my_goal_reached
		kwargs["goal_reached"] = goal_reached

		self.visit(node.init_block, **kwargs)

		def execute_child(child, goal_block, cs: CallStack, exception_list:list):
			try:
				kwargs["call_stack"] = cs				# update call_stack for parallel child node in compound

				self.visit(child, **kwargs)
				while not my_goal_reached.is_set():
					kwargs["call_stack"] = CALL_STACK	# recover call_stack for checking goal in behavior goal level
					if self.visit(goal_block, **kwargs):
						my_goal_reached.set()				# set shared flag True
						break							# terminate this parallel child node when goal_reached is set
					kwargs["call_stack"] = cs			# update call_stack for parallel child node in compound
					self.visit(child, **kwargs)
			except InterpreterError as e:
				exception_list.append(e)

		parent_call_stack = CALL_STACK
		if "call_stack" in kwargs:  # for sub-behavior
			parent_call_stack = kwargs['call_stack']
		threads = []
		exception_list = []
		for child in node.routine_block.children:
			child_call_stack = parent_call_stack.create_child(vehicle_name)
			thread = threading.Thread(target=execute_child, args=(child, node.goal_block, child_call_stack, exception_list))
			threads.append(thread)

		# start all threads
		for thread in threads:
			thread.start()

		# wait for all threads finish
		for thread in threads:
			thread.join()

		if exception_list:
			for exception in exception_list:
				LogLock.acquire()
				print(exception.message)
				LogLock.release()

	def visit_FunctionCall(self, node, **kwargs):
		CALL_STACK = self.call_stack
		if "call_stack" in kwargs:
			CALL_STACK = kwargs["call_stack"]

		# push ar into the call_stack
		function_name = node.name
		function_symbol = node.symbol
		ar_category_switch_case = {
			SymbolCategory.BEHAVIOR: ARType.BEHAVIOR,
			SymbolCategory.ACTION: ARType.ACTION
		}
		ar = ActivationRecord(
			name=function_name,
			category=ar_category_switch_case[function_symbol.category],
			nesting_level=CALL_STACK.get_base_level() + len(CALL_STACK._records),
		)

		# BehaviorCall or ActionCall
		formal_params = function_symbol.formal_params
		actual_params = node.actual_params
		for param_symbol, argument_node in zip(formal_params, actual_params):
			ar[param_symbol.name] = self.visit(argument_node, **kwargs)

		CALL_STACK.push(ar)

		log_switch_case = {
			SymbolCategory.BEHAVIOR: "Behavior",
			SymbolCategory.ACTION: "Action"
		}
		LogLock.acquire()
		self.log(f'{kwargs["agent"]}_{kwargs["id"]} ENTER: {log_switch_case[function_symbol.category]} {function_name}')
		self.log(str(CALL_STACK))
		LogLock.release()

		# check the abilities of agent
		if function_symbol.category == SymbolCategory.ACTION:
			if function_name not in self.agent_abilities[kwargs["agent"]]:
				self.error(error_code=ErrorCode.ABILITIY_NOT_DEFINE_IN_AGENT, token=node.token)

		# evaluate function body
		self.visit(function_symbol.ast, **kwargs)

		# self.log(str(CALL_STACK))
		CALL_STACK = CALL_STACK.pop()
		LogLock.acquire()
		self.log(f'LEAVE: {log_switch_case[function_symbol.category]} {function_name}')
		self.log(str(CALL_STACK))
		LogLock.release()

	def visit_Task(self, node, **kwargs):
		CALL_STACK = self.call_stack
		if "call_stack" in kwargs:
			CALL_STACK = kwargs["call_stack"]
		task_name = node.name
		
		goal_reached = kwargs["goal_reached"]
		my_goal_reached = threading.Event()
		goal_reached["Tasks"][task_name] = my_goal_reached
		kwargs["goal_reached"] = goal_reached

		self.visit(node.init_block, **kwargs)
		def execute_child(child, goal_block, cs: CallStack, exception_list:list):
			try:
				kwargs["call_stack"] = cs				# update call_stack for parallel child node in compound
				self.visit(child, **kwargs)
				while not my_goal_reached.is_set():
					kwargs["call_stack"] = CALL_STACK	# recover call_stack for checking goal in behavior goal level
					if self.visit(goal_block, **kwargs):
						my_goal_reached.set()				# set shared flag True
						break							# terminate this parallel child node when goal_reached is set
					kwargs["call_stack"] = cs			# update call_stack for parallel child node in compound
					self.visit(child, **kwargs)
			except InterpreterError as e:
				exception_list.append(e)

		parent_call_stack = CALL_STACK
		if "call_stack" in kwargs:  # for sub-behavior
			parent_call_stack = kwargs['call_stack']
		threads = []
		exception_list = []
		for child in node.routine_block.children:
			child_call_stack = parent_call_stack.create_child(task_name)
			thread = threading.Thread(target=execute_child, args=(child, node.goal_block, child_call_stack, exception_list))
			threads.append(thread)

		# start all threads
		for thread in threads:
			thread.start()

		# wait for all threads finish
		for thread in threads:
			thread.join()

		if exception_list:
			for exception in exception_list:
				LogLock.acquire()
				print(exception.message)
				LogLock.release()

	def visit_TaskCall(self, node, **kwargs):
		CALL_STACK = self.call_stack
		if "call_stack" in kwargs:
			CALL_STACK = kwargs["call_stack"]

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
			name=task_name,
			category=ARType.TASK,
			nesting_level=CALL_STACK.get_base_level() + len(CALL_STACK._records),
		)

		formal_params_agent_list = task_symbol.formal_params_agent_list
		actual_params_agent_list = node.actual_params_agent_list

		formal_params = task_symbol.formal_params
		actual_params = node.actual_params

		vehicle_name_list = [] # for setting task environment
		for param_agent_symbol, argument_agent_node in zip(formal_params_agent_list, actual_params_agent_list):
			ar[param_agent_symbol.agent] = self.visit(argument_agent_node.agent, **kwargs)
			ar[param_agent_symbol.start] = self.visit(argument_agent_node.start, **kwargs)
			ar[param_agent_symbol.end] = self.visit(argument_agent_node.end, **kwargs)
			for now in range(ar[param_agent_symbol.start], ar[param_agent_symbol.end]):
				vehicle_name_list.append(f'{ar[param_agent_symbol.agent][0]}_{now}')

		for param_symbol, argument_node in zip(formal_params, actual_params):
			ar[param_symbol.name] = self.visit(argument_node, **kwargs)

		CALL_STACK.push(ar)

		self.log(f'ENTER: Task {task_name}')
		self.log(str(CALL_STACK))

		# getattr(self.wrapper, node.name)(vehicle_name_list = vehicle_name_list)
		# evaluate task body
		self.visit(task_symbol.ast, **kwargs)

		self.log(str(CALL_STACK))
		CALL_STACK = CALL_STACK.pop()
		LogLock.acquire()
		self.log(f'LEAVE: Task {task_name}')
		self.log(str(CALL_STACK))
		LogLock.release()

	def visit_TaskOrder(self, node, **kwargs):
		agent_s_e, start, end = self.visit(node.agent_range, **kwargs)
		now = start
		while now < end:
			self.visit(node.function_call_statements, agent=agent_s_e[0], id=now, **kwargs)
			now += 1

	def visit_TaskEach(self, node, **kwargs):
		CALL_STACK = self.call_stack
		if "call_stack" in kwargs:
			CALL_STACK = kwargs["call_stack"]

		agent_s_e, start, end = self.visit(node.agent_range, **kwargs)

		def agent_work(agent_id, cs: CallStack, wpr:Wrapper, exception_list:list):
			try:
				kwargs["call_stack"] = cs
				self.visit(node.function_call_statements, agent=agent_s_e[0], id=agent_id, **kwargs)
				kwargs["call_stack"] = CALL_STACK
			except InterpreterError as e:
				exception_list.append(e)

		parent_call_stack = CALL_STACK
		if "call_stack" in kwargs:  # for sub-each_statement
			parent_call_stack = kwargs['call_stack']
		threads = []
		exception_list = []
		for now in range(start, end):
			child_call_stack = parent_call_stack.create_child(f'{agent_s_e[0]}:{now}')
			child_wrapper = kwargs["wrapper"].copy()
			thread = threading.Thread(target=agent_work, args=(now, child_call_stack, child_wrapper, exception_list))
			threads.append(thread)

		# start all threads
		for thread in threads:
			thread.start()

		# wait for all threads finish
		for thread in threads:
			thread.join()

		if exception_list:
			for exception in exception_list:
				LogLock.acquire()
				print(exception.message)
				LogLock.release()
	"""
	with concurrent.futures.ThreadPoolExecutor() as executor:
	    futures = []
	    # submit agent_work to thread pool
	    for now in range(start, end):
	        child_call_stack = parent_call_stack.create_child(f'{agent_s_e[0]}:{now}')
	        future = executor.submit(agent_work, now, child_call_stack)
	        futures.append(future)
	    # wait for all futures done
	    for future in concurrent.futures.as_completed(futures):
	        # check if the future is completed
	        if future.exception() is not None:
	            print(f'Task failed: {future.exception()}')
	        else:
	            print(f'Task result: {future.result()}')
	"""

	def visit_AgentRange(self, node, **kwargs):
		agent_s_e = self.visit(node.agent, **kwargs)
		start = self.visit(node.start, **kwargs)
		end = self.visit(node.end, **kwargs)
		return (agent_s_e, start, end)

	def visit_Main(self, node, **kwargs):
		CALL_STACK = self.call_stack
		if "call_stack" in kwargs:
			CALL_STACK = kwargs["call_stack"]

		ar = ActivationRecord(
			name="Main",
			category=ARType.MAIN,
			nesting_level=CALL_STACK.get_base_level() + len(CALL_STACK._records),
		)

		CALL_STACK.push(ar)

		self.log(f'ENTER: Main')

		for agent_call_node in node.agent_call_list.children:
			self.visit(agent_call_node, **kwargs)
		self.log(str(CALL_STACK))

		goal_reached = {"Tasks":{}, "Behaviors":{}}
		self.visit(node.task_call, goal_reached = goal_reached, **kwargs)

		self.log(str(CALL_STACK))
		CALL_STACK = CALL_STACK.pop()
		LogLock.acquire()
		self.log(f'LEAVE: Main')
		self.log(str(CALL_STACK))
		LogLock.release()

	def visit_InitBlock(self, node, **kwargs):
		self.visit(node.compound_statement, **kwargs)

	def visit_GoalBlock(self, node, **kwargs):
		self.visit(node.statements, **kwargs)
		result = self.visit(node.goal, **kwargs)
		if result == None:
			return True
		return result

	def visit_RoutineBlock(self, node, **kwargs):
		# each child is a parallel block as compound, should not use for statement
		# for child in node.children:
		# 	self.visit(child, **kwargs)
		pass

	def visit_Compound(self, node, **kwargs):
		CALL_STACK = self.call_stack
		if "call_stack" in kwargs:
			CALL_STACK = kwargs["call_stack"]

		# acquire knowledge lock
		ar:ActivationRecord = CALL_STACK.bottom()
		knowledge_locks = {}
		for statement in node.children:
			if isinstance(statement, BinOp):
				if isinstance(statement.right, Knowledge):
					knowledge_name = statement.right.value
					knowledge_locks[knowledge_name] = ar.get_lock(knowledge_name)
		sorted_knowledge_locks = sorted(knowledge_locks.items())
		for knowledge_lock_pair in sorted_knowledge_locks:
			knowledge_lock_pair[1].acquire()

		# multi parallel routine in Behavior or Task
		for child in node.children:
			current_level:ActivationRecord = CALL_STACK.peek()
			if current_level.category == ARType.TASK:
				GOAL_REACHED:threading.Event = kwargs["goal_reached"]["Tasks"][current_level.name]
				if GOAL_REACHED.is_set():
					break
			elif current_level.category == ARType.BEHAVIOR:
				vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
				GOAL_REACHED:threading.Event = kwargs["goal_reached"]["Behaviors"][current_level.name][vehicle_name]
				if GOAL_REACHED.is_set():
					break
			self.visit(child, **kwargs)
			LogLock.acquire()
			self.log(str(CALL_STACK))
			LogLock.release()

		for knowledge_lock_pair in sorted_knowledge_locks:
			knowledge_lock_pair[1].release()

	def visit_IfElse(self, node, **kwargs):
		expr_result = self.visit(node.expression, **kwargs)
		if expr_result:
			self.visit(node.true_compound, **kwargs)
		else:
			if node.false_compound is not None:
				self.visit(node.false_compound, **kwargs)

	def visit_Return(self, node, **kwargs):
		self.return_value = self.visit(node.expression, **kwargs)

	def visit_Expression(self, node, **kwargs):
		return self.visit(node.expr, **kwargs)

	def visit_Var(self, node, **kwargs):
		CALL_STACK = self.call_stack
		if "call_stack" in kwargs:
			CALL_STACK = kwargs["call_stack"]

		var_name = node.value
		ar:ActivationRecord = CALL_STACK.peek()
		var_value = ar[var_name]
		if var_value is None:
			# raise NameError(repr(var_name))
			self.error(error_code=ErrorCode.ID_NOT_FOUND, token=node.token)
		else:
			return var_value

	def visit_Boolean(self, node, **kwargs):
		return node.value

	def visit_Num(self, node, **kwargs):
		return node.value

	def visit_String(self, node, **kwargs):
		return node.value

	def visit_BinOp(self, node, **kwargs):
		CALL_STACK = self.call_stack
		if "call_stack" in kwargs:
			CALL_STACK = kwargs["call_stack"]

		if node.op.category == TokenType.PLUS:
			return self.visit(node.left, **kwargs) + self.visit(node.right, **kwargs)
		elif node.op.category == TokenType.MINUS:
			return self.visit(node.left, **kwargs) - self.visit(node.right, **kwargs)
		elif node.op.category == TokenType.MUL:
			return self.visit(node.left, **kwargs) * self.visit(node.right, **kwargs)
		elif node.op.category == TokenType.DIV:
			return self.visit(node.left, **kwargs) // self.visit(node.right, **kwargs)
		elif node.op.category == TokenType.MOD:
			return self.visit(node.left, **kwargs) % self.visit(node.right, **kwargs)
		elif node.op.category == TokenType.ASSIGN:
			var_name = node.left.value
			if not isinstance(node.right, FunctionCall):
				var_value = self.visit(node.right, **kwargs)
			else:
				self.visit(node.right, **kwargs)
				var_value = self.return_value
			ar:ActivationRecord = CALL_STACK.peek()
			ar[var_name] = var_value
		elif node.op.category == TokenType.PUT:
			knowledge_name = node.right.value
			expr_value = self.visit(node.left, **kwargs)
			ar:ActivationRecord = CALL_STACK.bottom()
			if isinstance(node.right, Knowledge):
				ar.put_knowledge(knowledge=knowledge_name, value=expr_value)
			else:	# isinstance(node.right, KnowledgeQueue)
				ar.put_knowledge_queue_item(knowledge_queue=knowledge_name, value=expr_value)
		elif node.op.category == TokenType.GET:
			var_name = node.left.value
			knowledge_name = node.right.value
			ar:ActivationRecord = CALL_STACK.bottom()
			if isinstance(node.right, Knowledge):
				var_value = ar.get_knowledge(knowledge=knowledge_name)
			else:	# isinstance(node.right, KnowledgeQueue)
				var_value = ar.get_knowledge_queue_item(knowledge_queue=knowledge_name)
			if var_value is None:
				self.error(error_code=ErrorCode.ID_NOT_FOUND, token=node.right.token)
			cur_ar:ActivationRecord = CALL_STACK.peek()
			cur_ar[var_name] = var_value
		elif node.op.category == TokenType.LESS:
			return self.visit(node.left, **kwargs) < self.visit(node.right, **kwargs)
		elif node.op.category == TokenType.GREATER:
			return self.visit(node.left, **kwargs) > self.visit(node.right, **kwargs)
		elif node.op.category == TokenType.LESS_EQUAL:
			return self.visit(node.left, **kwargs) <= self.visit(node.right, **kwargs)
		elif node.op.category == TokenType.GREATER_EQUAL:
			return self.visit(node.left, **kwargs) >= self.visit(node.right, **kwargs)
		elif node.op.category == TokenType.IS_EQUAL:
			left_value = self.visit(node.left, **kwargs)
			right_value = self.visit(node.right, **kwargs)
			res = (left_value == right_value)
			return res
		elif node.op.category == TokenType.NOT_EQUAL:
			return self.visit(node.left, **kwargs) != self.visit(node.right, **kwargs)

	def visit_UnaryOp(self, node, **kwargs):
		op = node.op.category
		if op == TokenType.PLUS:
			return +self.visit(node.expr, **kwargs)
		elif op == TokenType.MINUS:
			return -self.visit(node.expr, **kwargs)
		elif op == TokenType.NOT:
			return not self.visit(node.expr, **kwargs)

	def visit_NoOp(self, node, **kwargs):
		pass

	def interpret(self):
		tree = self.tree
		if tree is None:
			return ''
		return self.visit(tree)
