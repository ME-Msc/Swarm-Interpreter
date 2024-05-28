from enum import Enum


class ErrorCode(Enum):
	UNEXPECTED_TOKEN = 'Unexpected token'
	ID_NOT_FOUND = 'Identifier not found'
	DUPLICATE_ID = 'Duplicate id found'
	WRONG_PARAMS_NUM = 'Wrong number of arguments'
	OUT_OF_RANGE = 'Out of range'
	ABILITIY_NOT_DEFINE_IN_AGENT = 'Ability not define in agent'
	LIBRARY_CANNOT_BE_ASSIGNED = 'Library cannot be assigned'

class Error(Exception):
	def __init__(self, error_code=None, token=None, message=None):
		self.error_code = error_code
		self.token = token
		# add exception class name before the message
		self.message = f'{self.__class__.__name__}: {message}'


class LexerError(Error):
	pass


class ParserError(Error):
	pass


class SemanticError(Error):
	pass


class InterpreterError(Error):
	pass
