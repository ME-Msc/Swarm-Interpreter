import threading
import queue
from enum import Enum
import geopandas
import geopandas.geodataframe


class ARType(Enum):  # Activation Record Type
	PROGRAM = 'PROGRAM'
	MAIN = 'MAIN'
	TASK = 'TASK'
	BEHAVIOR = 'BEHAVIOR'
	ACTION = 'ACTION'
	AGENT = 'AGENT'


class ActivationRecord:
	def __init__(self, name, category, nesting_level):
		self.name = name
		self.category = category
		self.nesting_level = nesting_level
		# members[] is for Var type, members. put/get() is for Knowledge/KnowledgeQueue type
		self.members = {}
		self.locks = {}		# only for Knowledge, not for KnwoledgeQueue

	def __setitem__(self, key, value):
		self.members[key] = value

	def __getitem__(self, key):
		if key in self.members:
			return self.members[key]
		else:
			return None
	
	def __contains__(self, key):
		return key in self.members
	
	def get_lock(self, knowledge):
		if knowledge not in self.locks:
			self.locks[knowledge] = threading.Lock()
		return self.locks[knowledge]
	
	def put_knowledge_queue_item(self, knowledge_queue, value):
		assert self.category == ARType.PROGRAM
		if knowledge_queue not in self.members:
			self.members[knowledge_queue] = queue.Queue()
		self.members[knowledge_queue].put(value)

	def get_knowledge_queue_item(self, knowledge_queue):
		assert self.category == ARType.PROGRAM
		if knowledge_queue not in self.members:
			self.members[knowledge_queue] = queue.Queue()
		value = self.members[knowledge_queue].get()
		return value
	
	def put_knowledge(self, knowledge, value):
		assert self.category == ARType.PROGRAM
		assert self.locks[knowledge].locked() == True
		self.members[knowledge] = value

	def get_knowledge(self, knowledge):
		assert self.category == ARType.PROGRAM
		if knowledge not in self.members:
			return None
		assert self.locks[knowledge].locked() == True
		value = self.members[knowledge]
		return value

	def _format_value(self, val):
		if isinstance(val, str):
			val = '"' + val.replace('\\', '\\\\') + '"'  # Escape backslashes
		elif isinstance(val, list):
			lines = []
			for item in val:
				lines.append(str(item))
			val =  ('\n' + ' ' * 26).join(lines)
		elif isinstance(val, queue.Queue):
			val = str(list(val.queue))
		elif isinstance(val, geopandas.geodataframe.GeoDataFrame):
			val = str(type(val))
		return val

	def __str__(self):
		lines = [
			'{level}: {category} {name}'.format(
				level=self.nesting_level,
				category=self.category.value,
				name=self.name,
			)
		]
		for name, val in self.members.items():
			formatted_val = self._format_value(val)
			lines.append(f'   {name:<20} : {formatted_val}')

		s = '\n'.join(lines)
		return s

	def __repr__(self):
		return self.__str__()


class CallStack:
	def __init__(self):
		self.name = None
		self._records = []
		self.parent = None
		self.children = []

	def push(self, ar):
		self._records.append(ar)

	def pop(self):
		if len(self._records) == 0:
			if self.parent is None:
				raise Exception("CallStack has no parent.")
			else:
				self.parent.pop()
				return self.parent
		else:
			self._records.pop()
			return self

	def peek(self):
		if len(self._records) == 0:
			if self.parent is None:
				raise Exception("CallStack has no parent.")
			else:
				return self.parent.peek()
		return self._records[-1]
	
	def peek_all(self):
		peek_results = []
		stage = self
		while hasattr(stage, "parent"):
			for ar in stage._records[::-1]:
				peek_results.append(ar)
			if stage.parent is not None:
				stage = stage.parent
			else:
				break
		return peek_results

	def bottom(self):
		p = self
		while p.parent is not None:
			p = p.parent
		return p._records[0]

	def create_child(self, nm):
		child = CallStack()
		child.name = nm
		child.parent = self
		self.children.append(child)
		return child

	def back_to_parent(self):
		if not self.parent:
			raise MemoryError("Call stack node has no parent.")
		else:
			parent = self.parent
			parent.children.remove(self)
			return parent

	def get_base_level(self):
		p = self.parent
		cnt = 0
		while p is not None:
			cnt += len(p._records)
			p = p.parent
		return cnt

	def __str__(self):
		minus = '-' * 60
		equal = '=' * 60
		node = self
		s = '\n'.join(repr(ar) for ar in reversed(node._records))
		while node.parent is not None:
			node = node.parent
			parent_s = '\n'.join(repr(ar) for ar in reversed(node._records))
			s = f'{s}\n{parent_s}'
		if self.name is None:
			s = f'{equal}\nCALL STACK\n{minus}\n{s}\n{equal}\n\n'
		else:
			s = f'{equal}\nCALL STACK\t\t\t\tAgent< {self.name} >\n{minus}\n{s}\n{equal}\n\n'
		return s

	def __repr__(self):
		return self._records


if __name__ == '__main__':

	call_stack = CallStack()

	ar1 = ActivationRecord("AR1", ARType.MAIN, call_stack.get_base_level() + len(call_stack._records))
	ar1['a'] = 0
	ar1['b'] = 1
	call_stack.push(ar1)
	ar2 = ActivationRecord("AR2", ARType.TASK, call_stack.get_base_level() + len(call_stack._records))
	ar2['c'] = 2
	call_stack.push(ar2)
	print(call_stack)

	parent_call_stack = call_stack


	def agent_work(agent_id, cs: CallStack):
		# if agent_id==1:
		ar3 = ActivationRecord("AR2", ARType.BEHAVIOR, call_stack.get_base_level() + len(call_stack._records))
		ar3['d'] = cs.peek()['c'] + agent_id
		cs.push(ar3)
		print(cs)
		cs.back_to_parent()


	threads = []
	for now in range(0, 3):
		child_call_stack = parent_call_stack.create_child(str(now))
		thread = threading.Thread(target=agent_work, args=(now, child_call_stack,))
		threads.append(thread)

	# start all threads
	for thread in threads:
		thread.start()

	# wait for all threads finish
	for thread in threads:
		thread.join()
