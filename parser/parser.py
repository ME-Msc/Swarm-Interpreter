from base.error import ParserError, ErrorCode
from lexer.token import *
from parser.element import *
from parser.operator import NoOp, UnaryOp, BinOp, Assign

class Parser(object):
    def __init__(self, lexer):
        self.lexer = lexer
        # set current token to the first token taken from the input
        self.current_token = self.lexer.get_next_token()

    def get_next_token(self):
        return self.lexer.get_next_token()

    def error(self, error_code, token):
        raise ParserError(
            error_code=error_code,
            token=token,
            message=f'{error_code.value} -> {token}',
        )

    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        if self.current_token.type == token_type:
            self.current_token = self.get_next_token()
        else:
            self.error(
                error_code=ErrorCode.UNEXPECTED_TOKEN,
                token=self.current_token,
            )

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
        self.eat(TokenType.PORT)
        self.eat(TokenType.COLON)
        node = Num(self.current_token)
        self.eat(TokenType.INTEGER)
        return node

    def action(self):
        """ 
        action_defination ::= "Action" action_name "(" ")" ":" compound_statement
        action_name ::= variable
        """
        self.eat(TokenType.ACTION)
        var_node = self.variable()
        action_name = var_node.value
        self.eat(TokenType.LPAREN)
        parameters_nodes = self.formal_parameters()
        self.eat(TokenType.RPAREN)
        self.eat(TokenType.COLON)
        compound_statement_node = self.compound_statement()
        node = Action(name=action_name, params=parameters_nodes, compound_statement=compound_statement_node)
        return node
 
    def agent(self):
        """ 
        agent_defination ::= "Agent" agent_name "(" ")" ":" compound_statement
        agent_name ::= variable
        """
        self.eat(TokenType.AGENT)
        var_node = self.variable()
        agent_name = var_node.value
        self.eat(TokenType.LPAREN)
        parameters_nodes = self.formal_parameters()
        self.eat(TokenType.RPAREN)
        self.eat(TokenType.COLON)
        compound_statement_node = self.compound_statement()
        node = Agent(name=agent_name, params=parameters_nodes, compound_statement=compound_statement_node)
        return node
 
    def behavior(self):
        """
        behavior_defination ::= "Behavior" behavior_name "(" ")" ":" compound_statement
        behavior_name ::= variable
        """
        self.eat(TokenType.BEHAVIOR)
        var_node = self.variable()
        behavior_name = var_node.value
        self.eat(TokenType.LPAREN)
        parameters_nodes = self.formal_parameters()
        self.eat(TokenType.RPAREN)
        self.eat(TokenType.COLON)
        compound_statement_node = self.compound_statement()
        node = Behavior(name=behavior_name, params=parameters_nodes, compound_statement=compound_statement_node)
        return node
 

    def task(self):
        """
        task_defination ::= "Task" task_name "(" ")" ":" compound_statement
        task_name ::= variable
        """
        self.eat(TokenType.TASK)
        var_node = self.variable()
        task_name = var_node.value
        self.eat(TokenType.LPAREN)
        parameters_nodes = self.formal_parameters()
        self.eat(TokenType.RPAREN)
        self.eat(TokenType.COLON)
        compound_statement_node = self.compound_statement()
        node = Task(name=task_name, params=parameters_nodes, compound_statement=compound_statement_node)
        return node
 
    def main_task(self):
        """main_task : compound_statement"""
        self.eat(TokenType.MAIN)
        self.eat(TokenType.COLON)
        compound_statement_node = self.compound_statement()
        node = MainTask(compound_statement_node)   #TODO:Agent declaration
        return node

    def formal_parameters(self):
        """ 
        agent_defination ::= "Agent" variable "(" formal_parameters? ")" ":" compound_statement
        formal_parameters ::= variable ( "," variable )* 
        """
        # Agent testUav():
        if not self.current_token.type == TokenType.ID:
            return []

        param_nodes = []
        param_node = Param(Var(self.current_token))
        param_nodes.append(param_node)
        self.eat(TokenType.ID)
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            param_node = Param(Var(self.current_token))
            param_nodes.append(param_node)
            self.eat(TokenType.ID)

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

        while self.current_token.type == TokenType.SEMI:
            self.eat(TokenType.SEMI)
            results.append(self.statement())

        if self.current_token.type == TokenType.ID:
            self.error(
                error_code=ErrorCode.UNEXPECTED_TOKEN,
                token=self.current_token,
            )

        return results

    def statement(self):
        """
        statement : assignment_statement
                  | empty
        """
        if self.current_token.type == TokenType.ID:
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
        self.eat(TokenType.ASSIGN)
        right = self.expr()
        node = Assign(left, token, right)
        return node

    def variable(self):
        """
        variable : ID
        """
        node = Var(self.current_token)
        self.eat(TokenType.ID)
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
        if token.type == TokenType.PLUS:
            self.eat(TokenType.PLUS)
            node = UnaryOp(token, self.factor())
            return node
        elif token.type == TokenType.MINUS:
            self.eat(TokenType.MINUS)
            node = UnaryOp(token, self.factor())
            return node
        elif token.type == TokenType.INTEGER:
            self.eat(TokenType.INTEGER)
            return Num(token)
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expr()
            self.eat(TokenType.RPAREN)
            return node
        else:
            node = self.variable()
            return node

    def term(self):
        """term : factor ((MUL | DIV | MOD) factor)*"""
        node = self.factor()

        while self.current_token.type in (TokenType.MUL, TokenType.DIV, TokenType.MOD):
            token = self.current_token
            if token.type == TokenType.MUL:
                self.eat(TokenType.MUL)
            elif token.type == TokenType.DIV:
                self.eat(TokenType.DIV)
            elif token.type == TokenType.MOD:
                self.eat(TokenType.MOD)

            node = BinOp(left=node, op=token, right=self.factor())

        return node

    def expr(self):
        """
        expr   : term ((PLUS | MINUS) term)*
        term   : factor ((MUL | DIV | MOD) factor)*
        factor : (PLUS | MINUS) factor | INTEGER | LPAREN expr RPAREN
        """
        node = self.term()

        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            token = self.current_token
            if token.type == TokenType.PLUS:
                self.eat(TokenType.PLUS)
            elif token.type == TokenType.MINUS:
                self.eat(TokenType.MINUS)

            node = BinOp(left=node, op=token, right=self.term())

        return node

    def parse(self):
        node = self.program()
        if self.current_token.type != TokenType.EOF:
            self.error(
                error_code=ErrorCode.UNEXPECTED_TOKEN,
                token=self.current_token,
            )
        return node
