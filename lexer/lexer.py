from base.error import LexerError
from lexer.token import Token, TokenType


def _build_reserved_keywords():
	"""Build a dictionary of reserved keywords.

	The function relies on the fact that in the TokenType
	enumeration the beginning of the block of reserved keywords is
	marked with PROGRAM and the end of the block is marked with
	the END keyword.

	Result: {
		'Port': Token('PORT', 'PORT'),
		'Action': Token('ACTION', 'ACTION'),
		'Agent': Token('AGENT', 'AGENT'),
		'Behavior': Token('BEHAVIOR', 'BEHAVIOR'),
		'Task': Token('TASK', 'TASK'),
		'Main': Token('MAIN', 'MAIN')
	}
	"""
	# enumerations support iteration, in definition order
	tt_list = list(TokenType)
	start_index = tt_list.index(TokenType.PORT)
	end_index = tt_list.index(TokenType.EOF)  # NOT include EOF
	reserved_keywords = {
		token_type.value: token_type
		for token_type in tt_list[start_index:end_index]
	}
	return reserved_keywords


RESERVED_KEYWORDS = _build_reserved_keywords()


class Lexer(object):
	def __init__(self, text):
		# client string input, e.g. "4 + 2 * 3 - 6 / 2"
		self.text = text
		# self.pos is an index into self.text
		self.pos = 0
		self.current_char = self.text[self.pos]
		# token line number and column number
		self.lineno = 1
		self.column = 1

	def error(self):
		s = "Lexer error on '{lexeme}' line: {lineno} column: {column}".format(
			lexeme=self.current_char,
			lineno=self.lineno,
			column=self.column,
		)
		raise LexerError(message=s)

	def advance(self):
		"""Advance the `pos` pointer and set the `current_char` variable."""
		if self.current_char == '\n':
			self.lineno += 1
			self.column = 0

		self.pos += 1
		if self.pos > len(self.text) - 1:
			self.current_char = None  # Indicates end of input
		else:
			self.current_char = self.text[self.pos]
			self.column += 1

	def peek(self):
		peek_pos = self.pos + 1
		if peek_pos > len(self.text) - 1:
			return None
		else:
			return self.text[peek_pos]

	def skip_whitespace(self):
		while self.current_char is not None and self.current_char.isspace():
			self.advance()

	def _id(self):
		"""Handle identifiers and reserved keywords"""
		# Create a new token with current line and column number
		token = Token(category=None, value=None, lineno=self.lineno, column=self.column)

		value = ''
		while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
			value += self.current_char
			self.advance()

		token_type = RESERVED_KEYWORDS.get(value.upper())
		if token_type is None:
			token.category = TokenType.ID
			token.value = value
		else:
			# reserved keyword
			token.category = token_type
			token.value = value.upper()

		return token

	def number(self):
		"""Return a (multidigit) integer or float consumed from the input."""

		# Create a new token with current line and column number
		token = Token(category=None, value=None, lineno=self.lineno, column=self.column)

		result = ''
		while self.current_char is not None and self.current_char.isdigit():
			result += self.current_char
			self.advance()

		if self.current_char == '.':
			result += self.current_char
			self.advance()

			while self.current_char is not None and self.current_char.isdigit():
				result += self.current_char
				self.advance()

			token.category = TokenType.FLOAT
			token.value = float(result)
		else:
			token.category = TokenType.INTEGER
			token.value = int(result)
		return token

	def string(self):
		"""Return a string consumed from the input."""

		# Create a new token with current line and column number
		token = Token(category=None, value=None, lineno=self.lineno, column=self.column)

		quote = self.current_char  # " or '
		self.advance()
		result = ''
		while (self.current_char is not None) and (self.current_char != quote):
			if self.current_char == '\\':
				self.advance()  # Skip the backslash
				if self.current_char is None:  # Handle the case where the backslash is at the end of the input
					break
				elif self.current_char == 'n':
					result += '\n'
				elif self.current_char == 't':
					result += '\t'
				elif self.current_char == 'r':
					result += '\r'
				else:  # For other escape sequences, simply include the escaped character
					result += self.current_char
				self.advance()  # Skip the character after the escape sequence
			else:
				result += self.current_char
				self.advance()

		# Check if the closing quote was found
		if self.current_char != quote:
			self.error()

		self.advance()  # Move past the closing quote

		token.category = TokenType.STRING
		token.value = str(result)
		return token

	def get_next_token(self):
		"""Lexical analyzer (also known as scanner or tokenizer)

		This method is responsible for breaking a sentence
		apart into tokens. One token at a time.
		"""
		while self.current_char is not None:

			if self.current_char.isspace():
				self.skip_whitespace()
				continue

			if self.current_char.isalpha():
				return self._id()

			if self.current_char.isdigit():
				return self.number()

			if self.current_char == '@':
				self.advance()
				return self._id()

			if self.current_char == '"' or self.current_char == "'":
				return self.string()

			# multi-character token
			try:
				peek_char = self.peek()
				if peek_char is None:
					raise ValueError
				multi_char = self.current_char + peek_char
				# get enum member by value, e.g.
				# TokenType('<<') --> TokenType.DOUBLE_LESS
				token_type = TokenType(multi_char)
			except ValueError:
				# no enum member with value equal to multi_char
				# check for single-character token
				try:
					# get enum member by value, e.g.
					# TokenType(';') --> TokenType.SEMI
					token_type = TokenType(self.current_char)
				except ValueError:
					# no enum member with value equal to self.current_char
					self.error()
				else:
					# create a token with a single-character lexeme as its value
					token = Token(
						category=token_type,
						value=token_type.value,  # e.g. ';', '.', etc
						lineno=self.lineno,
						column=self.column,
					)
					self.advance()
					return token
			else:
				# create a token with a multi-character lexeme as its value
				token = Token(
					category=token_type,
					value=token_type.value,  # e.g. '<<', '>>', etc
					lineno=self.lineno,
					column=self.column,
				)
				self.advance()
				self.advance()
				return token

		# EOF (end-of-file) token indicates that there is no more
		# input left for lexical analysis
		return Token(category=TokenType.EOF, value=None)

	def peek_next_token(self):
		"""Peek at the next token without consuming it."""
		pos = self.pos
		current_char = self.current_char
		lineno = self.lineno
		column = self.column

		next_token = self.get_next_token()

		# Restore the original state of the lexer
		self.pos = pos
		self.current_char = current_char
		self.lineno = lineno
		self.column = column

		return next_token
