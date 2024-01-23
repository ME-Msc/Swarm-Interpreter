""" Swarm Interpreter """
from lexer.lexer import Lexer
from parser.parser import Parser
from semanticAnalyzer.semanticAnalyzer import SemanticAnalyzer
from interpreter.interpreter import Interpreter
from base.error import LexerError, ParserError, SemanticError
import sys

def main():
    SHOULD_LOG_SCOPE = False
    try:
        # text = input('swarm > ')
        text = """
            Port : 14457

            Action getGPS():
            
            Agent testUav():

            Behavior reach_Behavior():

            Task add_task(a, b):

            Main :
                add_task(1, 2)
        """
    except EOFError:
        sys.exit(1)
    
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

    interpreter = Interpreter(tree)
    interpreter.interpret()

    print('')
    print('Run-time GLOBAL_MEMORY contents:')
    for k, v in sorted(interpreter.GLOBAL_MEMORY.items()):
        print('{} = {}'.format(k, v))


if __name__ == '__main__':
    main()
