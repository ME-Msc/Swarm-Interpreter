""" Swarm Interpreter """
import argparse
from queue import Queue
import sys
import threading

from base.error import LexerError, ParserError, SemanticError, InterpreterError
from interpreter.interpreter import Interpreter
from lexer.lexer import Lexer
from parser.parser import Parser
from semanticAnalyzer.semanticAnalyzer import SemanticAnalyzer


def swarm_producer(q:Queue, sem_dic:dict):
	parser = argparse.ArgumentParser(
		description='Swarm Interpreter'
	)
	parser.add_argument('inputfile', help='Pascal source file')
	parser.add_argument(
		'--scope',
		help='Print scope information',
		action='store_true',
	)
	parser.add_argument(
		'--stack',
		help='Print call stack',
		action='store_true',
	)
	args = parser.parse_args()

	SHOULD_LOG_SCOPE, SHOULD_LOG_STACK = args.scope, args.stack
	text = open(args.inputfile, 'r').read()

	if not text:
		print("Text is None.")
		sys.exit(1)

	lexer = Lexer(text)
	try:
		parser = Parser(lexer)
		tree = parser.parse()
	except (LexerError, ParserError) as e:
		print(e.message)
		sys.exit(1)

	semantic_analyzer = SemanticAnalyzer(log_or_not=SHOULD_LOG_SCOPE)
	try:
		semantic_analyzer.visit(tree)
	except SemanticError as e:
		print(e.message)
		sys.exit(1)

	interpreter = Interpreter(tree, rpc_queue=q, sem_dic=sem_dic,  log_or_not=SHOULD_LOG_STACK)
	try:
		interpreter.interpret()
	except InterpreterError as e:
		print(e.message)
		sys.exit(1)


def rpc_consumer(q:Queue, sem_dic:dict):
	while True:
		rpc_call, vehicle_name = q.get()
		try:
			rpc_call()
		except Exception as e:
			print(e)
		finally:
			sem_dic[vehicle_name].release()
		q.task_done()

if __name__ == '__main__':
	rpc_queue = Queue()
	semaphore_dict = {}
	
	rpc_thread = threading.Thread(target=rpc_consumer, args=(rpc_queue, semaphore_dict))
	rpc_thread.start()
	
	main_thread = threading.Thread(target=swarm_producer, args=(rpc_queue, semaphore_dict))
	main_thread.start()

	rpc_thread.join()
	main_thread.join()
