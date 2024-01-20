from lexer.token import *
from parser.element import *
from parser.operator import NoOp, UnaryOp, BinOp, Assign

class Parser(object):
    def __init__(self, lexer):
        self.lexer = lexer
        # set current token to the first token taken from the input
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise Exception('Invalid syntax')

    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def program(self):
        """ program ::= port_setting agent_defination action_defination behavior_defination task_defination main_task """
        port_node = self.port()
        port_num = port_node.value
        action_node = self.action()
        agent_node = self.agent()
        behavior_node = self.behavior()
        task_node = self.task()
        main_task_node = self.main_task()
        program_node = Program(port = port_num, action = action_node, agent = agent_node, 
                               behavior = behavior_node, task = task_node, mainTask = main_task_node)
        return program_node

    def port(self):
        """ port_setting ::= 'Port' ':' integer """
        self.eat(PORT)
        self.eat(COLON)
        node = Num(self.current_token)
        self.eat(INTEGER)
        return node

    def action(self):
        """ 
        action_defination ::= "Action" action_name "(" ")" ":" compound_statement
        action_name ::= variable
        """
        self.eat(ACTION)
        var_node = self.variable()
        action_name = var_node.value
        self.eat(LPAREN)
        parameters_nodes = self.formal_parameters()
        self.eat(RPAREN)
        self.eat(COLON)
        compound_statement_node = self.compound_statement()
        node = Action(name=action_name, params=parameters_nodes, compound_statement=compound_statement_node)
        return node
 
    def agent(self):
        """ 
        agent_defination ::= "Agent" agent_name "(" ")" ":" compound_statement
        agent_name ::= variable
        """
        self.eat(AGENT)
        var_node = self.variable()
        agent_name = var_node.value
        self.eat(LPAREN)
        parameters_nodes = self.formal_parameters()
        self.eat(RPAREN)
        self.eat(COLON)
        compound_statement_node = self.compound_statement()
        node = Agent(name=agent_name, params=parameters_nodes, compound_statement=compound_statement_node)
        return node
 
    def behavior(self):
        """
        behavior_defination ::= "Behavior" behavior_name "(" ")" ":" compound_statement
        behavior_name ::= variable
        """
        self.eat(BEHAVIOR)
        var_node = self.variable()
        behavior_name = var_node.value
        self.eat(LPAREN)
        parameters_nodes = self.formal_parameters()
        self.eat(RPAREN)
        self.eat(COLON)
        compound_statement_node = self.compound_statement()
        node = Behavior(name=behavior_name, params=parameters_nodes, compound_statement=compound_statement_node)
        return node
 

    def task(self):
        """
        task_defination ::= "Task" task_name "(" ")" ":" compound_statement
        task_name ::= variable
        """
        self.eat(TASK)
        var_node = self.variable()
        task_name = var_node.value
        self.eat(LPAREN)
        parameters_nodes = self.formal_parameters()
        self.eat(RPAREN)
        self.eat(COLON)
        compound_statement_node = self.compound_statement()
        node = Task(name=task_name, params=parameters_nodes, compound_statement=compound_statement_node)
        return node
 
    def main_task(self):
        """main_task : compound_statement"""
        self.eat(MAIN)
        self.eat(COLON)
        compound_statement_node = self.compound_statement()
        node = MainTask(compound_statement_node)   #TODO:Agent declaration
        return node

    def formal_parameters(self):
        """ 
        agent_defination ::= "Agent" variable "(" formal_parameters? ")" ":" compound_statement
        formal_parameters ::= variable ( "," variable )* 
        """
        # Agent testUav():
        if not self.current_token.type == ID:
            return []

        param_nodes = []
        param_node = Param(Var(self.current_token))
        param_nodes.append(param_node)
        self.eat(ID)
        while self.current_token.type == COMMA:
            self.eat(COMMA)
            param_node = Param(Var(self.current_token))
            param_nodes.append(param_node)
            self.eat(ID)

        return param_nodes

    def compound_statement(self):
        """
        compound_statement: statement_list
        """
        nodes = self.statement_list()

        root = Compound()
        for node in nodes:
            root.children.append(node)

        return root

    def statement_list(self):
        """
        statement_list : statement (SEMI statement)*
        """
        node = self.statement()

        results = [node]

        while self.current_token.type == SEMI:
            self.eat(SEMI)
            results.append(self.statement())

        if self.current_token.type == ID:
            self.error()

        return results

    def statement(self):
        """
        statement : assignment_statement
                  | empty
        """
        if self.current_token.type == ID:
            node = self.assignment_statement()
        else:
            node = self.empty()
        return node

    def assignment_statement(self):
        """
        assignment_statement : variable ASSIGN expr
        """
        left = self.variable()
        token = self.current_token
        self.eat(ASSIGN)
        right = self.expr()
        node = Assign(left, token, right)
        return node

    def variable(self):
        """
        variable : ID
        """
        node = Var(self.current_token)
        self.eat(ID)
        return node

    def empty(self):
        """An empty production"""
        return NoOp()

    def factor(self):
        """
        factor : (PLUS | MINUS) factor 
                    | INTEGER 
                    | LPAREN expr RPAREN
                    | variable
        """
        token = self.current_token
        if token.type == PLUS:
            self.eat(PLUS)
            node = UnaryOp(token, self.factor())
            return node
        elif token.type == MINUS:
            self.eat(MINUS)
            node = UnaryOp(token, self.factor())
            return node
        elif token.type == INTEGER:
            self.eat(INTEGER)
            return Num(token)
        elif token.type == LPAREN:
            self.eat(LPAREN)
            node = self.expr()
            self.eat(RPAREN)
            return node
        else:
            node = self.variable()
            return node

    def term(self):
        """term : factor ((MUL | DIV | MOD) factor)*"""
        node = self.factor()

        while self.current_token.type in (MUL, DIV, MOD):
            token = self.current_token
            if token.type == MUL:
                self.eat(MUL)
            elif token.type == DIV:
                self.eat(DIV)
            elif token.type == MOD:
                self.eat(MOD)

            node = BinOp(left=node, op=token, right=self.factor())

        return node

    def expr(self):
        """
        expr   : term ((PLUS | MINUS) term)*
        term   : factor ((MUL | DIV | MOD) factor)*
        factor : (PLUS | MINUS) factor | INTEGER | LPAREN expr RPAREN
        """
        node = self.term()

        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.eat(PLUS)
            elif token.type == MINUS:
                self.eat(MINUS)

            node = BinOp(left=node, op=token, right=self.term())

        return node

    def parse(self):
        node = self.program()
        if self.current_token.type != EOF:
            self.error()
        return node
