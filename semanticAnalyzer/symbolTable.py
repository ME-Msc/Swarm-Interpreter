from semanticAnalyzer.symbol import *


class ScopedSymbolTable(object):
	def __init__(self, scope_name, scope_level, enclosing_scope=None, log_or_not=False):
		self._symbols = {}
		self.scope_name = scope_name
		self.scope_level = scope_level
		self.enclosing_scope = enclosing_scope
		self.log_or_not = log_or_not

	def _init_builtins(self):
		self.insert(BuiltinTypeSymbol('INTEGER'))
		self.insert(BuiltinTypeSymbol('FLOAT'))
		self.insert(BuiltinTypeSymbol('STRING'))

	def __str__(self):
		h1 = 'SCOPE (SCOPED SYMBOL TABLE)'
		h2 = 'Scope (Scoped symbol table) contents'
		lines = ['=' * max(len(h1), len(h2)), h1, '-' * max(len(h1), len(h2))]
		for header_name, header_value in (
				('Scope name', self.scope_name),
				('Scope level', self.scope_level),
				('Enclosing scope',
				 self.enclosing_scope.scope_name if self.enclosing_scope else None
				 )
		):
			lines.append('%-15s: %s' % (header_name, header_value))
		h2 = 'Scope (Scoped symbol table) contents'
		lines.extend([h2, '-' * max(len(h1), len(h2))])
		lines.extend(
			('%-15s: %r' % (key, value))
			for key, value in self._symbols.items()
		)
		lines.extend(['=' * max(len(h1), len(h2))])
		# lines.append('\n')
		s = '\n'.join(lines)
		return s

	__repr__ = __str__

	def log(self, msg):
		if self.log_or_not:
			print(msg)

	def insert(self, symbol, log_or_not=True):
		if log_or_not:
			self.log('Insert: %s' % symbol)
		symbol.scope_level = self.scope_level
		self._symbols[symbol.name] = symbol

	def lookup(self, name, current_scope_only=False, log_or_not=True):
		if log_or_not:
			self.log('Lookup: %s. (Scope name: %s)' % (name, self.scope_name))
		# 'symbol' is either an instance of the Symbol class or None
		symbol = self._symbols.get(name)

		if symbol is not None:
			return symbol

		if current_scope_only:
			return None

		# recursively go up the chain and lookup the name
		if self.enclosing_scope is not None:
			return self.enclosing_scope.lookup(name)
