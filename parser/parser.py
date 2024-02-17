from base.error import ParserError, ErrorCode
from lexer.token import *
from parser.element import *
from parser.operator import NoOp, UnaryOp, BinOp, Assign

class BaseParser(object):
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


class Parser(BaseParser):
    def __init__(self, lexer):
        super().__init__(lexer)

    def program(self):
        """ program ::= port_setting agent_defination action_defination behavior_defination task_defination main_task """
        port_node = self.port()
        port_num = port_node.value
        action_list = self.action_list()
        agent_list = self.agent_list()
        behavior_list = self.behavior_list()
        task_list = self.task_list()
        main_task_node = self.main_task()
        program_node = Program(port = port_num, action_list = action_list, agent_list = agent_list, 
                               behavior_list = behavior_list, task_list = task_list, mainTask = main_task_node)
        return program_node

    def port(self):
        """ port_setting ::= 'Port' ':' integer """
        self.eat(TokenType.PORT)
        self.eat(TokenType.COLON)
        node = Num(self.current_token)
        self.eat(TokenType.INTEGER)
        return node

    def action_list(self):
        root = ActionList()
        while self.current_token.type == TokenType.ACTION:
            root.children.append(self.action())
        return root

    def action(self):
        """ 
        action_defination ::= "Action" action_name "(" ")" ":" compound_statement
        action_name ::= variable
        """
        self.eat(TokenType.ACTION)
        var_node = self.variable()
        action_name = var_node.value
        self.eat(TokenType.L_PAREN)
        parameters_nodes = self.formal_parameters()
        self.eat(TokenType.R_PAREN)
        action_compound_statement_node = self.action_compound_statement()
        node = Action(name=action_name, formal_params=parameters_nodes, compound_statement=action_compound_statement_node)
        return node
    
    def action_compound_statement(self):
        self.eat(TokenType.L_BRACE)
        root = Compound()
        node = self.action_statement()
        root.children.append(node)
        while self.current_token.type == TokenType.SEMI:
            self.eat(TokenType.SEMI)
            root.children.append(self.action_statement())
        self.eat(TokenType.R_BRACE)
        return root

    def action_statement(self):
        if self.current_token.type == TokenType.ID:
            node = self.assignment_statement()
        else:
            node = self.empty()
        return node

    '''
    TODO:
    action_RPC_call_assignment_statement
    action_RPC_call_statement 
    action_return_statement 
    action_if_else 
    action_call
    '''

    def agent_list(self):
        root = AgentList()
        while self.current_token.type == TokenType.AGENT:
            root.children.append(self.agent())
        return root

    def agent(self):
        self.eat(TokenType.AGENT)
        var_node = self.variable()
        agent_name = var_node.value
        self.eat(TokenType.L_BRACE)
        ability_node = Compound()
        node = self.variable()
        ability_node.children.append(node)
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            ability_node.children.append(self.variable())
        self.eat(TokenType.SEMI)
        node = Agent(name=agent_name, ability=ability_node)
        self.eat(TokenType.R_BRACE)
        return node

    def behavior_list(self):
        root = BehaviorList()
        while self.current_token.type == TokenType.BEHAVIOR:
            root.children.append(self.behavior())
        return root

    def behavior(self):
        self.eat(TokenType.BEHAVIOR)
        var_node = self.variable()
        behavior_name = var_node.value
        self.eat(TokenType.L_PAREN)
        parameters_nodes = self.formal_parameters()
        self.eat(TokenType.R_PAREN)
        self.eat(TokenType.L_BRACE)
        init_node = self.behavior_init_block()
        goal_node = self.behavior_goal_block()
        routine_node = self.behavior_routine_block()
        node = Behavior(name = behavior_name, formal_params = parameters_nodes, 
                        init_block = init_node, goal_block = goal_node, routine_block = routine_node)
        self.eat(TokenType.R_BRACE)
        return node
    
    def behavior_init_block(self):
        self.eat(TokenType.INIT)
        node = self.behavior_compound_statement()
        return node

    def behavior_goal_block(self):
        self.eat(TokenType.GOAL)
        self.eat(TokenType.L_BRACE)
        root = Compound()
        while not self.current_token.type == TokenType.DOLLAR:
            root.children.append(self.behavior_statement())
        self.eat(TokenType.DOLLAR)
        root.children.append(self.expression())
        self.eat(TokenType.R_BRACE)
        return root

    def behavior_routine_block(self):
        self.eat(TokenType.ROUTINE)
        root = Compound()
        root.children.append(self.behavior_compound_statement())
        while self.current_token.type == TokenType.PARALLEL:
            self.eat(TokenType.PARALLEL)
            root.children.append(self.behavior_compound_statement())
        return root

    def behavior_compound_statement(self):
        self.eat(TokenType.L_BRACE)
        root = Compound()
        node = self.behavior_statement()
        root.children.append(node)
        while self.current_token.type == TokenType.SEMI:
            self.eat(TokenType.SEMI)
            root.children.append(self.behavior_statement())
        self.eat(TokenType.R_BRACE)
        return root

    # TODO: behavior_statement not finish yet
    def behavior_statement(self):
        '''
        behavior_statement ::= put_statement
                        | get_statement
                        | behavior_publish_statement
                        | behavior_subscribe_statement
                        | behavior_unsubscribe_statement
                        | behavior_assignment_statement
                        | behavior_if_else
                        | behavior_call
                        | action_call
                        | empty
        '''
        if self.current_token.type == TokenType.ID:
            node = self.assignment_statement()
        else:
            node = self.empty()
        return node
    
    def behavior_call(self):
        token = self.current_token
        behavior_name = self.current_token.value
        self.eat(TokenType.ID)
        self.eat(TokenType.L_PAREN)
        actual_params = []
        if self.current_token.type != TokenType.R_PAREN:
            node = self.additive_expression()
            actual_params.append(node)
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            node = self.additive_expression()
            actual_params.append(node)
        self.eat(TokenType.R_PAREN)
        node = BehaviorCall(
            name=behavior_name,
            actual_params=actual_params,
            token=token
        )
        return node

    def task_list(self):
        root = TaskList()
        while self.current_token.type == TokenType.TASK:
            root.children.append(self.task())
        return root

    def task(self):
        self.eat(TokenType.TASK)
        var_node = self.variable()
        task_name = var_node.value
        self.eat(TokenType.L_PAREN)
        parameters_nodes = self.formal_parameters()
        self.eat(TokenType.R_PAREN)
        self.eat(TokenType.L_BRACE)
        init_node = self.task_init_block()
        goal_node = self.task_goal_block()
        routine_node = self.task_routine_block()
        node = Task(name = task_name, formal_params = parameters_nodes, 
                        init_block = init_node, goal_block = goal_node, routine_block = routine_node)
        self.eat(TokenType.R_BRACE)
        return node
    
    def task_init_block(self):
        self.eat(TokenType.INIT)
        node = self.task_compound_statement()
        return node

    def task_goal_block(self):
        self.eat(TokenType.GOAL)
        self.eat(TokenType.L_BRACE)
        root = Compound()
        while not self.current_token.type == TokenType.DOLLAR:
            root.children.append(self.task_statement())
        self.eat(TokenType.DOLLAR)
        root.children.append(self.expression())
        self.eat(TokenType.R_BRACE)
        return root

    def task_routine_block(self):
        self.eat(TokenType.ROUTINE)
        root = Compound()
        # TODO: order each statement in task_routine
        # if order:
        # elif each:
        # else:
        root.children.append(self.task_compound_statement())
        while self.current_token.type == TokenType.PARALLEL:
            # TODO: parallel block root level
            self.eat(TokenType.PARALLEL)
            root.children.append(self.task_compound_statement())
        return root

    def task_compound_statement(self):
        self.eat(TokenType.L_BRACE)
        root = Compound()
        node = self.task_statement()
        root.children.append(node)
        while self.current_token.type == TokenType.SEMI:
            self.eat(TokenType.SEMI)
            root.children.append(self.task_statement())
        self.eat(TokenType.R_BRACE)
        return root

    # TODO: task_statement not finish yet
    def task_statement(self):
        if self.current_token.type == TokenType.ID and self.lexer.current_char == '(' and self.lexer.peek() == '{':
            node = self.task_call()
        if self.current_token.type == TokenType.ID and self.lexer.current_char == '(' :
            node = self.behavior_call()
        elif self.current_token.type == TokenType.ID:
            node = self.assignment_statement()
        else:
            node = self.empty()
        return node

    def task_call(self):
        token = self.current_token
        task_name = self.current_token.value
        self.eat(TokenType.ID)
        self.eat(TokenType.L_PAREN)
        self.eat(TokenType.L_BRACE)
        # TODO: formal_parameters_agent_list in task_call 
        self.eat(TokenType.R_BRACE)
        actual_params = []
        if self.current_token.type != TokenType.R_PAREN:
            node = self.actual_parameters()
            actual_params.append(node)
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            node = self.actual_parameters()
            actual_params.append(node)
        self.eat(TokenType.R_PAREN)
        node = TaskCall(
            name=task_name,
            actual_params=actual_params,
            token=token
        )
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
        formal_parameters ::= variable ( "," variable )* 
        """
        # No formal parameters
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

    def actual_parameters(self):
        return self.additive_expression()

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
        if self.current_token.type == TokenType.ID and self.lexer.current_char == '(':
            node = self.task_call()
        elif self.current_token.type == TokenType.ID:
            node = self.assignment_statement()
        else:
            node = self.empty()
        return node

    def assignment_statement(self):
        """
        assignment_statement : variable ASSIGN additive_expression
        """
        left = self.variable()
        token = self.current_token
        self.eat(TokenType.ASSIGN)
        right = self.additive_expression()
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

    def expression(self):
        """
        expression ::= logical_not_expression
        """
        return self.logical_not_expression()

    def logical_not_expression(self):
        """
        logical_not_expression ::= "not"? logical_or_expression
        """
        if self.current_token.type == TokenType.NOT :
            token = self.current_token
            self.eat(TokenType.NOT)
            node = self.logical_or_expression()
            node = UnaryOp(op=token, expr=node)
        else:
            node = self.logical_or_expression()
        return node

    def logical_or_expression(self):
        """
        logical_or_expression ::= logical_and_expression
                                | logical_and_expression "or" logical_or_expression
        """
        node = self.logical_and_expression()
        if self.current_token.type == TokenType.OR :
            token = self.current_token
            self.eat(TokenType.OR)
            node = BinOp(left=node, op=token, right=self.logical_or_expression())
        return node

    def logical_and_expression(self):
        """
        logical_and_expression ::= equality_expression
                        | equality_expression "and" logical_and_expression
        """
        node = self.equality_expression()
        if self.current_token.type == TokenType.AND :
            token = self.current_token
            self.eat(TokenType.AND)
            node = BinOp(left=node, op=token, right=self.equality_expression())
        return node

    def equality_expression(self) :
        """ 
        equality_expression ::= relational_expression
                            | relational_expression "==" equality_expression
                            | relational_expression "!=" equality_expression
        """
        node = self.relational_expression()

        if self.current_token.type == TokenType.IS_EQUAL :
            token = self.current_token
            self.eat(TokenType.IS_EQUAL)
            node = BinOp(left=node, op=token, right=self.equality_expression())
        elif self.current_token.type == TokenType.NOT_EQUAL :
            token = self.current_token
            self.eat(TokenType.NOT_EQUAL)
            node = BinOp(left=node, op=token, right=self.equality_expression())
        
        return node

    def relational_expression(self):
        """
        relational_expression ::= additive_expression
                        | additive_expression "<" relational_expression
                        | additive_expression "<=" relational_expression
                        | additive_expression ">" relational_expression
                        | additive_expression ">=" relational_expression
        """
        node = self.additive_expression()

        if self.current_token.type == TokenType.LESS :
            token = self.current_token
            self.eat(TokenType.LESS)
            node = BinOp(left=node, op=token, right=self.relational_expression())
        elif self.current_token.type == TokenType.LESS_EQUAL :
            token = self.current_token
            self.eat(TokenType.LESS_EQUAL)
            node = BinOp(left=node, op=token, right=self.relational_expression())
        elif self.current_token.type == TokenType.GREATER :
            token = self.current_token
            self.eat(TokenType.GREATER)
            node = BinOp(left=node, op=token, right=self.relational_expression())
        elif self.current_token.type == TokenType.GREATER_EQUAL :
            token = self.current_token
            self.eat(TokenType.GREATER_EQUAL)
            node = BinOp(left=node, op=token, right=self.relational_expression())

        return node
        
    def additive_expression(self):
        """
        additive_expression ::= multiplicative_expression ( ( "+" | "-" ) multiplicative_expression )*
        """
        node = self.multiplicative_expression()

        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            token = self.current_token
            if token.type == TokenType.PLUS:
                self.eat(TokenType.PLUS)
            elif token.type == TokenType.MINUS:
                self.eat(TokenType.MINUS)

            node = BinOp(left=node, op=token, right=self.multiplicative_expression())

        return node

    def multiplicative_expression(self):
        """
        multiplicative_expression ::= primary_expression ( ( "*" | "/" | "%" ) primary_expression )*
        """
        node = self.primary_expression()

        while self.current_token.type in (TokenType.MUL, TokenType.DIV, TokenType.MOD):
            token = self.current_token
            if token.type == TokenType.MUL:
                self.eat(TokenType.MUL)
            elif token.type == TokenType.DIV:
                self.eat(TokenType.DIV)
            elif token.type == TokenType.MOD:
                self.eat(TokenType.MOD)

            node = BinOp(left=node, op=token, right=self.primary_expression())

        return node

    def primary_expression(self):
        """
        primary_expression ::= integer
                        | ( "+" | "-" ) primary_expression
                        | "(" additive_expression ")"
                        | variable
        """
        token = self.current_token
        if token.type == TokenType.PLUS:
            self.eat(TokenType.PLUS)
            node = UnaryOp(token, self.primary_expression())
            return node
        elif token.type == TokenType.MINUS:
            self.eat(TokenType.MINUS)
            node = UnaryOp(token, self.primary_expression())
            return node
        elif token.type == TokenType.INTEGER:
            self.eat(TokenType.INTEGER)
            return Num(token)
        elif token.type == TokenType.L_PAREN:
            self.eat(TokenType.LPAREN)
            node = self.expression()
            self.eat(TokenType.RPAREN)
            return node
        else:
            node = self.variable()
            return node

    def parse(self):
        node = self.program()
        if self.current_token.type != TokenType.EOF:
            self.error(
                error_code=ErrorCode.UNEXPECTED_TOKEN,
                token=self.current_token,
            )
        return node
