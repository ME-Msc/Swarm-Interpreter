from base.error import ParserError, ErrorCode
from lexer.token import *
from parser.element import *
from parser.operator import NoOp, UnaryOp, BinOp

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
        if self.current_token.category == token_type:
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
        port_node = self.port()
        action_list = self.action_list()
        agent_list = self.agent_list()
        behavior_list = self.behavior_list()
        task_list = self.task_list()
        main_node = self.main()
        program_node = Program(port = port_node, action_list = action_list, agent_list = agent_list, 
                               behavior_list = behavior_list, task_list = task_list, main = main_node)
        return program_node

    def port(self):
        """ port_setting ::= 'Port' ':' integer """
        self.eat(TokenType.PORT)
        self.eat(TokenType.COLON)
        node = self.integer()
        node = Port(node)
        return node

    def action_list(self):
        root = ActionList()
        while self.current_token.category == TokenType.ACTION:
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
        formal_params_nodes = FormalParams() # No formal parameters
        if self.current_token.category != TokenType.R_PAREN:
            formal_params_nodes = self.formal_parameters()
        self.eat(TokenType.R_PAREN)
        action_compound_node = self.action_compound()
        node = Action(name=action_name, formal_params=formal_params_nodes, compound_statement=action_compound_node)
        return node
    
    def action_compound(self):
        self.eat(TokenType.L_BRACE)
        root = Compound()
        while self.current_token.category != TokenType.R_BRACE:
            node = self.action_statement()
            if not isinstance(node, NoOp):
                root.children.append(node)
        self.eat(TokenType.R_BRACE)
        return root

    def action_statement(self):
        if self.current_token.category == TokenType.ID:
            node = self.assignment_statement()
        elif self.current_token.category == TokenType.RPC_CALL:
            node = self.action_RPC_call_statement()
        elif self.current_token.category == TokenType.PUT:
            node = self.put_statement()
        elif self.current_token.category == TokenType.GET:
            node = self.get_statement()
        elif self.current_token.category == TokenType.IF:
            node = self.action_if_else()
        else:
            node = self.empty_statement()
        return node

    def action_RPC_call_statement(self):
        self.eat(TokenType.RPC_CALL)
        node = self.function_call_statement()
        return node

    '''
    TODO:
    action_RPC_call_assignment_statement
    action_return_statement 
    '''
    def action_if_else(self):
        self.eat(TokenType.IF)
        self.eat(TokenType.L_PAREN)
        expr_node = self.expression()
        self.eat(TokenType.R_PAREN)
        true_cmpd_node = self.action_compound()
        false_cmpd_node = None
        if self.current_token.category == TokenType.ELSE:
            self.eat(TokenType.ELSE)
            false_cmpd_node = self.action_compound()
        node = IfElse(expr=expr_node, true_cmpd=true_cmpd_node, false_cmpd=false_cmpd_node)
        return node

    def agent_list(self):
        root = AgentList()
        while self.current_token.category == TokenType.AGENT:
            root.children.append(self.agent())
        return root

    def agent(self):
        self.eat(TokenType.AGENT)
        var_node = self.variable()
        agent_name = var_node.value
        self.eat(TokenType.L_BRACE)
        ability_root = Compound()
        node = self.variable()
        if not isinstance(node, NoOp):
            ability_root.children.append(node)
            while self.current_token.category != TokenType.SEMI:
                self.eat(TokenType.COMMA)
                node = self.variable()
                ability_root.children.append(node)
            self.eat(TokenType.SEMI)
        agent_node = Agent(name=agent_name, abilities=ability_root)
        self.eat(TokenType.R_BRACE)
        return agent_node

    def agent_call_statement(self):
        self.eat(TokenType.AGENT)
        agt_node = self.variable()
        cnt_node = self.integer()
        node = AgentCall(agent=agt_node, count=cnt_node)
        self.eat(TokenType.SEMI)
        return node

    def behavior_list(self):
        root = BehaviorList()
        while self.current_token.category == TokenType.BEHAVIOR:
            root.children.append(self.behavior())
        return root

    def behavior(self):
        self.eat(TokenType.BEHAVIOR)
        var_node = self.variable()
        behavior_name = var_node.value
        self.eat(TokenType.L_PAREN)
        formal_params_nodes = FormalParams() # No formal parameters
        if self.current_token.category != TokenType.R_PAREN:
            formal_params_nodes = self.formal_parameters()
        self.eat(TokenType.R_PAREN)
        self.eat(TokenType.L_BRACE)
        init_node = self.behavior_init_block()
        goal_node = self.behavior_goal_block()
        routine_node = self.behavior_routine_block()
        node = Behavior(name = behavior_name, formal_params = formal_params_nodes, 
                        init_block = init_node, goal_block = goal_node, routine_block = routine_node)
        self.eat(TokenType.R_BRACE)
        return node
    
    def behavior_init_block(self):
        self.eat(TokenType.INIT)
        behavior_compound_node = self.behavior_compound()
        node = InitBlock(compound_statement = behavior_compound_node)
        return node

    def behavior_goal_block(self):
        self.eat(TokenType.GOAL)
        self.eat(TokenType.L_BRACE)
        statements_root = Compound()
        if self.current_token.category != TokenType.R_BRACE:
            while self.current_token.category != TokenType.DOLLAR:
                node = self.behavior_statement()
                if not isinstance(node, NoOp):
                    statements_root.children.append(node)
                self.eat(TokenType.SEMI)
            self.eat(TokenType.DOLLAR)
            goal_node = Expression(self.expression())
        else:
            goal_node = Expression(NoOp())
        node = GoalBlock(statements = statements_root, goal = goal_node)
        self.eat(TokenType.R_BRACE)
        return node

    def behavior_routine_block(self):
        self.eat(TokenType.ROUTINE)
        root = RoutineBlock()
        node = self.behavior_compound()
        root.children.append(node)
        while self.current_token.category == TokenType.PARALLEL:
            self.eat(TokenType.PARALLEL)
            node = self.behavior_compound()
            root.children.append(node)
        return root

    def behavior_compound(self):
        self.eat(TokenType.L_BRACE)
        root = Compound()
        while self.current_token.category != TokenType.R_BRACE:
            node = self.behavior_statement()
            if not isinstance(node, NoOp):
                root.children.append(node)
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
                        | empty_statement
        '''
        if self.current_token.category == TokenType.ID and self.lexer.current_char == '(' :
            node = self.function_call_statement()
        elif self.current_token.category == TokenType.ID:
            node = self.assignment_statement()
        elif self.current_token.category == TokenType.PUT:
            node = self.put_statement()
        elif self.current_token.category == TokenType.GET:
            node = self.get_statement()
        elif self.current_token.category == TokenType.IF:
            node = self.behavior_if_else()
        else:
            node = self.empty_statement()
        return node
    
    """
    TODO: behavior_publish_statement
    behavior_subscribe_statement
    behavior_unsubscribe_statement
    behavior_assignment_statement
    """

    def behavior_if_else(self):
        self.eat(TokenType.IF)
        self.eat(TokenType.L_PAREN)
        expr_node = self.expression()
        self.eat(TokenType.R_PAREN)
        true_cmpd_node = self.behavior_compound()
        false_cmpd_node = None
        if self.current_token.category == TokenType.ELSE:
            self.eat(TokenType.ELSE)
            false_cmpd_node = self.behavior_compound()
        node = IfElse(expr=expr_node, true_cmpd=true_cmpd_node, false_cmpd=false_cmpd_node)
        return node

    def function_call_statement(self):
        function_call = self.variable()
        self.eat(TokenType.L_PAREN)
        actual_params = []
        if self.current_token.category != TokenType.R_PAREN:
            actual_params = self.actual_parameters()
        self.eat(TokenType.R_PAREN)
        self.eat(TokenType.SEMI)
        node = FunctionCall(
            name=function_call.value,
            actual_params=actual_params,
            token=function_call.token
        )
        return node

    def task_list(self):
        root = TaskList()
        while self.current_token.category == TokenType.TASK:
            root.children.append(self.task())
        return root

    def task(self):
        self.eat(TokenType.TASK)
        var_node = self.variable()
        task_name = var_node.value
        self.eat(TokenType.L_PAREN)
        formal_params_agent_list = self.formal_parameters_agent_range_list()
        formal_params_nodes = FormalParams() # No formal parameters
        if self.current_token.category != TokenType.R_PAREN:
            self.eat(TokenType.COMMA)
            formal_params_nodes = self.formal_parameters()
        self.eat(TokenType.R_PAREN)
        self.eat(TokenType.L_BRACE)
        init_node = self.task_init_block()
        goal_node = self.task_goal_block()
        routine_node = self.task_routine_block()
        node = Task(name = task_name, formal_params_agent_list = formal_params_agent_list ,formal_params = formal_params_nodes, 
                        init_block = init_node, goal_block = goal_node, routine_block = routine_node)
        self.eat(TokenType.R_BRACE)
        return node
    
    def task_init_block(self):
        self.eat(TokenType.INIT)
        task_compound_node = self.task_compound()
        node = InitBlock(compound_statement = task_compound_node)
        return node

    def task_goal_block(self):
        self.eat(TokenType.GOAL)
        self.eat(TokenType.L_BRACE)
        statements_root = Compound()
        if self.current_token.category != TokenType.R_BRACE:
            while self.current_token.category != TokenType.DOLLAR:
                node = self.task_statement()
                if not isinstance(node, NoOp):
                    statements_root.children.append(node)
                self.eat(TokenType.SEMI)
            self.eat(TokenType.DOLLAR)
            goal_node = Expression(self.expression())
        else:
            goal_node = Expression(NoOp())
        node = GoalBlock(statements = statements_root, goal = goal_node)
        self.eat(TokenType.R_BRACE)
        return node

    def task_routine_block(self):
        self.eat(TokenType.ROUTINE)
        root = RoutineBlock()
        node = self.task_compound()
        root.children.append(node)
        while self.current_token.category == TokenType.PARALLEL:
            self.eat(TokenType.PARALLEL)
            node = self.task_compound()
            root.children.append(node)
        return root

    """
    TODO: task_routine_parallel
    task_routine_order
    task_routine_each
    """

    def task_compound(self):
        self.eat(TokenType.L_BRACE)
        root = Compound()
        while self.current_token.category != TokenType.R_BRACE:
            node = self.task_statement()
            if not isinstance(node, NoOp):
                root.children.append(node)
        self.eat(TokenType.R_BRACE)
        return root

    # TODO: task_statement not finish yet
    def task_statement(self):
        if self.current_token.category == TokenType.ID and self.lexer.current_char == '(' :
            node = self.task_call_statement()
        elif self.current_token.category == TokenType.ORDER:
            node = self.task_order()
        elif self.current_token.category == TokenType.EACH:
            node = self.task_each()
        elif self.current_token.category == TokenType.ID:
            node = self.assignment_statement()
        elif self.current_token.category == TokenType.PUT:
            node = self.put_statement()
        elif self.current_token.category == TokenType.GET:
            node = self.get_statement()
        elif self.current_token.category == TokenType.IF:
            node = self.task_if_else()
        else:
            node = self.empty_statement()
        return node

    def task_order(self):
        self.eat(TokenType.ORDER)
        agt_range = self.actual_parameters_agent_range()
        self.eat(TokenType.L_BRACE)
        func_call_statements = Compound()
        while self.current_token.category != TokenType.R_BRACE:
            func_call_node = self.function_call_statement()
            func_call_statements.children.append(func_call_node)
        self.eat(TokenType.R_BRACE)
        root = TaskOrder(
            agent_range=agt_range,
            function_call_statements=func_call_statements
        )
        return root

    def task_each(self):
        self.eat(TokenType.EACH)
        agt_range = self.actual_parameters_agent_range()
        self.eat(TokenType.L_BRACE)
        func_call_statements = Compound()
        while self.current_token.category != TokenType.R_BRACE:
            func_call_node = self.function_call_statement()
            func_call_statements.children.append(func_call_node)
        self.eat(TokenType.R_BRACE)
        root = TaskEach(
            agent_range=agt_range,
            function_call_statements=func_call_statements
        )
        return root

    def task_if_else(self):
        self.eat(TokenType.IF)
        self.eat(TokenType.L_PAREN)
        expr_node = self.expression()
        self.eat(TokenType.R_PAREN)
        true_cmpd_node = self.task_compound()
        false_cmpd_node = None
        if self.current_token.category == TokenType.ELSE:
            self.eat(TokenType.ELSE)
            false_cmpd_node = self.task_compound()
        node = IfElse(expr=expr_node, true_cmpd=true_cmpd_node, false_cmpd=false_cmpd_node)
        return node

    def task_call_statement(self):
        task_call = self.variable()
        self.eat(TokenType.L_PAREN)
        actual_params_agent_list = self.actual_parameters_agent_range_list()
        actual_params = []
        if self.current_token.category != TokenType.R_PAREN:
            self.eat(TokenType.COMMA)
            actual_params = self.actual_parameters()
        self.eat(TokenType.R_PAREN)
        node = TaskCall(
            name=task_call.value,
            actual_params_agent_list=actual_params_agent_list,
            actual_params=actual_params,
            token=task_call.token
        )
        self.eat(TokenType.SEMI)
        return node

    def main(self):
        self.eat(TokenType.MAIN)
        self.eat(TokenType.L_BRACE)
        agentCallRoot = AgentCallList()
        while self.current_token.category == TokenType.AGENT:
            agent_call_node = self.agent_call_statement()
            agentCallRoot.children.append(agent_call_node)
        task_call_node = self.task_call_statement()
        node = Main(agent_call_list = agentCallRoot, task_call = task_call_node)
        self.eat(TokenType.R_BRACE)
        return node

    def put_statement(self):
        token = self.current_token
        self.eat(TokenType.PUT)
        expr = self.expression()
        self.eat(TokenType.TO)
        stigmergy = self.stigmergy()
        self.eat(TokenType.SEMI)
        node = BinOp(expr, token, stigmergy)
        return node
    
    def get_statement(self):
        token = self.current_token
        self.eat(TokenType.GET)
        var = self.variable()
        self.eat(TokenType.FROM)
        stigmergy = self.stigmergy()
        self.eat(TokenType.SEMI)
        node = BinOp(var, token, stigmergy)
        return node

    def assignment_statement(self):
        """
        assignment_statement : variable ASSIGN additive_expression
        """
        left = self.variable()
        token = self.current_token
        self.eat(TokenType.ASSIGN)
        right = self.additive_expression()
        self.eat(TokenType.SEMI)
        node = BinOp(left, token, right)
        return node

    def empty_statement(self):
        """An empty_statement production"""
        self.eat(TokenType.SEMI)
        return NoOp()

    def stigmergy(self):
        self.eat(TokenType.HASH)
        node = self.variable()
        self.eat(TokenType.HASH)
        return node

    """
    TODO: /* Basic Elements */
    topic_p2p ::= "<" variable ">"
    topic_multicast ::= "<<" variable ">>"
    """

    def formal_parameters_agent_range_list(self):
        root = AgentRangeList()
        self.eat(TokenType.L_BRACE)
        agent_range_node = self.formal_parameters_agent_range()
        root.children.append(agent_range_node)
        while self.current_token.category == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            agent_range_node = self.formal_parameters_agent_range()
            root.children.append(agent_range_node)
        self.eat(TokenType.R_BRACE)
        return root

    def actual_parameters_agent_range_list(self):
        actual_params_agent_list = []
        self.eat(TokenType.L_BRACE)
        agent_range_node = self.actual_parameters_agent_range()
        actual_params_agent_list.append(agent_range_node)
        while self.current_token.category != TokenType.R_BRACE:
            self.eat(TokenType.COMMA)
            agent_range_node = self.actual_parameters_agent_range()
            actual_params_agent_list.append(agent_range_node)
        self.eat(TokenType.R_BRACE)
        return actual_params_agent_list

    def formal_parameters_agent_range(self):
        agent = self.variable()
        self.eat(TokenType.L_BRACKET)
        start = self.variable()
        self.eat(TokenType.TILDE)
        end = self.variable()
        self.eat(TokenType.R_BRACKET)
        root = AgentRange(agent=agent, start=start, end=end)
        return root

    def actual_parameters_agent_range(self):
        agent = self.variable()
        self.eat(TokenType.L_BRACKET)
        start = self.additive_expression()
        self.eat(TokenType.TILDE)
        end = self.additive_expression()
        self.eat(TokenType.R_BRACKET)
        root = AgentRange(agent=agent, start=start, end=end)
        return root

    def formal_parameters(self):
        """
        formal_parameters ::= variable ( "," variable )* 
        """
        root = FormalParams()
        param_node = self.variable()
        root.children.append(param_node)
        while self.current_token.category == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            param_node = self.variable()
            root.children.append(param_node)
        return root

    def actual_parameters(self):
        actual_params = []
        node = self.additive_expression()
        actual_params.append(node)
        while self.current_token.category == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            node = self.additive_expression()
            actual_params.append(node)
        return actual_params

    def expression(self):
        """
        expression ::= logical_not_expression
        """
        return self.logical_not_expression()

    def logical_not_expression(self):
        """
        logical_not_expression ::= "not"? logical_or_expression
        """
        if self.current_token.category == TokenType.NOT :
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
        if self.current_token.category == TokenType.OR :
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
        if self.current_token.category == TokenType.AND :
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
        if self.current_token.category == TokenType.IS_EQUAL :
            token = self.current_token
            self.eat(TokenType.IS_EQUAL)
            node = BinOp(left=node, op=token, right=self.equality_expression())
        elif self.current_token.category == TokenType.NOT_EQUAL :
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
        if self.current_token.category == TokenType.LESS :
            token = self.current_token
            self.eat(TokenType.LESS)
            node = BinOp(left=node, op=token, right=self.relational_expression())
        elif self.current_token.category == TokenType.LESS_EQUAL :
            token = self.current_token
            self.eat(TokenType.LESS_EQUAL)
            node = BinOp(left=node, op=token, right=self.relational_expression())
        elif self.current_token.category == TokenType.GREATER :
            token = self.current_token
            self.eat(TokenType.GREATER)
            node = BinOp(left=node, op=token, right=self.relational_expression())
        elif self.current_token.category == TokenType.GREATER_EQUAL :
            token = self.current_token
            self.eat(TokenType.GREATER_EQUAL)
            node = BinOp(left=node, op=token, right=self.relational_expression())
        return node
        
    def additive_expression(self):
        """
        additive_expression ::= multiplicative_expression ( ( "+" | "-" ) multiplicative_expression )*
        """
        node = self.multiplicative_expression()
        while self.current_token.category in (TokenType.PLUS, TokenType.MINUS):
            token = self.current_token
            if token.category == TokenType.PLUS:
                self.eat(TokenType.PLUS)
            elif token.category == TokenType.MINUS:
                self.eat(TokenType.MINUS)
            node = BinOp(left=node, op=token, right=self.multiplicative_expression())
        return node

    def multiplicative_expression(self):
        """
        multiplicative_expression ::= primary_expression ( ( "*" | "/" | "%" ) primary_expression )*
        """
        node = self.primary_expression()
        while self.current_token.category in (TokenType.MUL, TokenType.DIV, TokenType.MOD):
            token = self.current_token
            if token.category == TokenType.MUL:
                self.eat(TokenType.MUL)
            elif token.category == TokenType.DIV:
                self.eat(TokenType.DIV)
            elif token.category == TokenType.MOD:
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
        if token.category == TokenType.PLUS:
            self.eat(TokenType.PLUS)
            node = UnaryOp(token, self.primary_expression())
            return node
        elif token.category == TokenType.MINUS:
            self.eat(TokenType.MINUS)
            node = UnaryOp(token, self.primary_expression())
            return node
        elif token.category == TokenType.INTEGER:
            node = self.integer()
            return node
        elif token.category == TokenType.L_PAREN:
            self.eat(TokenType.LPAREN)
            node = self.expression()
            self.eat(TokenType.RPAREN)
            return node
        else:
            node = self.variable()
            return node

    def variable(self):
        """
        variable : ID
        """
        node = Var(self.current_token)
        self.eat(TokenType.ID)
        return node
    
    def integer(self):
        node = Num(self.current_token)
        self.eat(TokenType.INTEGER)
        return node


    def parse(self):
        node = self.program()
        if self.current_token.category != TokenType.EOF:
            self.error(
                error_code=ErrorCode.UNEXPECTED_TOKEN,
                token=self.current_token,
            )
        return node
