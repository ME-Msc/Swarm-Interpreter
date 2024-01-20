""" Swarm Interpreter """
from lexer.lexer import Lexer
from parser.parser import Parser
from semanticAnalyzer.semanticAnalyzer import SemanticAnalyzer
from interpreter.interpreter import Interpreter

def main():
    while True:
        try:
            # text = input('swarm > ')
            text = """
                Port : 14457

                Action getGPS(test_param):
                    a = 1
                
                Agent testUav():
                    b = a + 2

                Behavior reach_Behavior():
                    c = b + 3

                Task reach_in_order_Task():
                    d  = c + 4 

                Main :
                    e = d + 5
            """
        except EOFError:
            break
        if not text:
            continue

        lexer = Lexer(text)
        parser = Parser(lexer)
        tree = parser.parse()
        
        semantic_analyzer = SemanticAnalyzer()
        try:
            semantic_analyzer.visit(tree)
        except Exception as e:
            print(e)

        print(semantic_analyzer.symtab)

        interpreter = Interpreter(tree)
        result = interpreter.interpret()

        print('')
        print('Run-time GLOBAL_MEMORY contents:')
        for k, v in sorted(interpreter.GLOBAL_MEMORY.items()):
            print('{} = {}'.format(k, v))


if __name__ == '__main__':
    main()
