import threading
from enum import Enum


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
		self.members = {}
		self.locks = {}

	def __setitem__(self, key, value):
		if (self.category == ARType.PROGRAM) and (key not in self.members):
			self.locks[key] = threading.Lock()
		self.members[key] = value

	def __getitem__(self, key):
		if key in self.members:
			return self.members[key]
		else:
			return None
	
	def __contains__(self, key):
		return key in self.members
	
	def get_lock(self, knowledge):
		if knowledge in self.locks:
			return self.locks[knowledge]
		else:
			return None
		
	def add_lock(self, knowledge):
		if knowledge not in self.locks:
			self.locks[knowledge] = threading.Lock()
		return self.locks[knowledge]

	def __str__(self):
		lines = [
			'{level}: {category} {name}'.format(
				level=self.nesting_level,
				category=self.category.value,
				name=self.name,
			)
		]
		for name, val in self.members.items():
			if isinstance(val, str):
				val = '"' + val.replace('\\', '\\\\') + '"'  # Escape backslashes
			lines.append(f'   {name:<20}: {val}')

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
				return self.parent._records[-1]
		return self._records[-1]

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
