""" Swarm Interpreter """
from lexer.lexer import Lexer
from parser.parser import Parser
from interpreter.interpreter import Interpreter
from symbols.symbolTable import *

def main():
    while True:
        try:
            # text = input('swarm > ')
            text = """
                Port : 14457

                Action getGPS():
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
        symtab_builder = SymbolTableBuilder()
        symtab_builder.visit(tree)
        print('')
        print('Symbol Table contents:')
        print(symtab_builder.symtab)

        interpreter = Interpreter(tree)
        result = interpreter.interpret()

        print('')
        print('Run-time GLOBAL_MEMORY contents:')
        for k, v in sorted(interpreter.GLOBAL_MEMORY.items()):
            print('{} = {}'.format(k, v))


if __name__ == '__main__':
    main()
