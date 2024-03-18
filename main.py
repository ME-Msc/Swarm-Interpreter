""" Swarm Interpreter """
import argparse
from lexer.lexer import Lexer
from parser.parser import Parser
from semanticAnalyzer.semanticAnalyzer import SemanticAnalyzer
from interpreter.interpreter import Interpreter
from base.error import LexerError, ParserError, SemanticError, InterpreterError
import sys

def main():
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

    interpreter = Interpreter(tree, log_or_not=SHOULD_LOG_STACK)
    try:
        interpreter.interpret()
    except InterpreterError as e:
        print(e.message)
        sys.exit(1)



if __name__ == '__main__':
    main()
