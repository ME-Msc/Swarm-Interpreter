""" Swarm Interpreter """
from lexer.lexer import Lexer
from parser.parser import Parser
from interpreter.interpreter import Interpreter
from symbols.symbolTable import *

def main():
    while True:
        try:
            # text = input('swarm > ')
            text = "Main : x = -1 ; y = x + 5; z = (y*3 - 2) %3"
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
