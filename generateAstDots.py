################################################################################################
#  AST visualizer - generates a DOT file for Graphviz.                                         #
#                                                                                              #
#  To generate an image from the DOT file run                                                  #
#                                                                                              #
#  $ python generateAstDots.py test_example.swarm > ast.dot && dot -Tpng -o ast.png ast.dot    #
#                                                                                              #
################################################################################################

import argparse
import subprocess
import textwrap
import re

from lexer.lexer import Lexer
from parser.parser import Parser
from base.nodeVisitor import NodeVisitor


class ASTVisualizer(NodeVisitor):
    def __init__(self, parser):
        self.parser = parser
        self.ncount = 1
        self.dot_header = [textwrap.dedent("""\
        digraph astgraph {
          node [shape=circle, fontsize=40, fontname="Arial", height=.1, fontweight="bold"];
          ranksep=.3;
          edge [arrowsize=2]

        """)]
        self.dot_body = []
        self.dot_footer = ['}']
    
    def visit_Program(self, node):
        s = '  node{} [label="Program"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1

        self.visit(node.port)
        s = '  node{} -> node{}\n'.format(node._num, node.port._num)
        self.dot_body.append(s)

        self.visit(node.action_list)
        s = '  node{} -> node{}\n'.format(node._num, node.action_list._num)
        self.dot_body.append(s)

        self.visit(node.agent_list)
        s = '  node{} -> node{}\n'.format(node._num, node.agent_list._num)
        self.dot_body.append(s)

        self.visit(node.behavior_list)
        s = '  node{} -> node{}\n'.format(node._num, node.behavior_list._num)
        self.dot_body.append(s)

        self.visit(node.task_list)
        s = '  node{} -> node{}\n'.format(node._num, node.task_list._num)
        self.dot_body.append(s)

        self.visit(node.main)
        s = '  node{} -> node{}\n'.format(node._num, node.main._num)
        self.dot_body.append(s)

    def visit_Port(self, node):
        s = '  node{} [label="Port:{}"]\n'.format(self.ncount, node.port.value)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1

    def visit_ActionList(self, node):
        s = '  node{} [label="ActionList"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        for child in node.children:
            self.visit(child)
            s = '  node{} -> node{}\n'.format(node._num, child._num)
            self.dot_body.append(s)

    def visit_Action(self, node):
        s = '  node{} [label="Action:{}"]\n'.format(
            self.ncount,
            node.name
        )
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1

        self.visit(node.formal_params)
        s = '  node{} -> node{}\n'.format(node._num, node.formal_params._num)
        self.dot_body.append(s)

        self.visit(node.compound_statement)
        s = '  node{} -> node{}\n'.format(node._num, node.compound_statement._num)
        self.dot_body.append(s)

    def visit_AgentList(self, node):
        s = '  node{} [label="AgentList"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        for child in node.children:
            self.visit(child)
            s = '  node{} -> node{}\n'.format(node._num, child._num)
            self.dot_body.append(s)

    def visit_Agent(self, node):
        s = '  node{} [label="Agent:{}"]\n'.format(
            self.ncount,
            node.name
        )
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        for ability_node in node.abilities.children:
            self.visit(ability_node)
            s = '  node{} -> node{}\n'.format(node._num, ability_node._num)
            self.dot_body.append(s)

    def visit_AgentCall(self, node):
        s = '  node{} [label="AgentCall"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1

        self.visit(node.agent)
        s = '  node{} -> node{}\n'.format(node._num, node.agent._num)
        self.dot_body.append(s)

        self.visit(node.count)
        s = '  node{} -> node{}\n'.format(node._num, node.count._num)
        self.dot_body.append(s)

    def visit_AgentCallList(self, node):
        s = '  node{} [label="AgentCallList"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        for child in node.children:
            self.visit(child)
            s = '  node{} -> node{}\n'.format(node._num, child._num)
            self.dot_body.append(s)

    def visit_AgentRange(self, node):
        s = '  node{} [label="AgentRange"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1

        self.visit(node.agent)
        s = '  node{} -> node{}\n'.format(node._num, node.agent._num)
        self.dot_body.append(s)

        self.visit(node.start)
        s = '  node{} -> node{}\n'.format(node._num, node.start._num)
        self.dot_body.append(s)

        self.visit(node.end)
        s = '  node{} -> node{}\n'.format(node._num, node.end._num)
        self.dot_body.append(s)

    def visit_BehaviorList(self, node):
        s = '  node{} [label="BehaviorList"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        for child in node.children:
            self.visit(child)
            s = '  node{} -> node{}\n'.format(node._num, child._num)
            self.dot_body.append(s)

    def visit_Behavior(self, node):
        s = '  node{} [label="Behavior:{}"]\n'.format(
            self.ncount,
            node.name
        )
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        
        self.visit(node.formal_params)
        s = '  node{} -> node{}\n'.format(node._num, node.formal_params._num)
        self.dot_body.append(s)
        
        self.visit(node.init_block)
        s = '  node{} -> node{}\n'.format(node._num, node.init_block._num)
        self.dot_body.append(s)

        self.visit(node.goal_block)
        s = '  node{} -> node{}\n'.format(node._num, node.goal_block._num)
        self.dot_body.append(s)

        self.visit(node.routine_block)
        s = '  node{} -> node{}\n'.format(node._num, node.routine_block._num)
        self.dot_body.append(s)

    def visit_FunctionCall(self, node):
        s = '  node{} [label="FunctionCall:\n{}"]\n'.format(
            self.ncount,
            node.name
        )
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        for param_node in node.actual_params:
            self.visit(param_node)
            s = '  node{} -> node{}\n'.format(node._num, param_node._num)
            self.dot_body.append(s)

    def visit_TaskList(self, node):
        s = '  node{} [label="TaskList"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        for child in node.children:
            self.visit(child)
            s = '  node{} -> node{}\n'.format(node._num, child._num)
            self.dot_body.append(s)

    def visit_Task(self, node):
        s = '  node{} [label="Task:{}"]\n'.format(
            self.ncount,
            node.name
        )
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        
        for agent_range in node.formal_params_agent_list.children:
            self.visit(agent_range)
            s = '  node{} -> node{}\n'.format(node._num, agent_range._num)
            self.dot_body.append(s)

        self.visit(node.formal_params)
        s = '  node{} -> node{}\n'.format(node._num, node.formal_params._num)
        self.dot_body.append(s)
        
        self.visit(node.init_block)
        s = '  node{} -> node{}\n'.format(node._num, node.init_block._num)
        self.dot_body.append(s)

        self.visit(node.goal_block)
        s = '  node{} -> node{}\n'.format(node._num, node.goal_block._num)
        self.dot_body.append(s)

        self.visit(node.routine_block)
        s = '  node{} -> node{}\n'.format(node._num, node.routine_block._num)
        self.dot_body.append(s)

    def visit_TaskOrder(self, node):
        s = '  node{} [label="TaskOrder"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1

        self.visit(node.agent_range)
        s = '  node{} -> node{}\n'.format(node._num, node.agent_range._num)
        self.dot_body.append(s)

        self.visit(node.function_call_statements)
        s = '  node{} -> node{}\n'.format(node._num, node.function_call_statements._num)
        self.dot_body.append(s)

    def visit_TaskCall(self, node):
        s = '  node{} [label="TaskCall:\n{}"]\n'.format(
            self.ncount,
            node.name
        )
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1

        # TODO: AST node for node.actual_params_agent_list
        for agent_range in node.actual_params_agent_list:
            self.visit(agent_range)
            s = '  node{} -> node{}\n'.format(node._num, agent_range._num)
            self.dot_body.append(s)

        for param_node in node.actual_params:
            self.visit(param_node)
            s = '  node{} -> node{}\n'.format(node._num, param_node._num)
            self.dot_body.append(s)

    def visit_Main(self, node):
        s = '  node{} [label="Main"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1

        self.visit(node.agent_call_list)
        s = '  node{} -> node{}\n'.format(node._num, node.agent_call_list._num)
        self.dot_body.append(s)

        self.visit(node.task_call)
        s = '  node{} -> node{}\n'.format(node._num, node.task_call._num)
        self.dot_body.append(s)

    def visit_InitBlock(self, node):
        s = '  node{} [label="InitBlock"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        self.visit(node.compound_statement)
        s = '  node{} -> node{}\n'.format(node._num, node.compound_statement._num)
        self.dot_body.append(s)

    def visit_GoalBlock(self, node):
        s = '  node{} [label="GoalBlock"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        
        self.visit(node.statements)
        s = '  node{} -> node{}\n'.format(node._num, node.statements._num)
        self.dot_body.append(s)

        self.visit(node.goal)
        s = '  node{} -> node{}\n'.format(node._num, node.goal._num)
        self.dot_body.append(s)

    def visit_RoutineBlock(self, node):
        s = '  node{} [label="RoutineBlock"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        for child in node.children:
            self.visit(child)
            s = '  node{} -> node{}\n'.format(node._num, child._num)
            self.dot_body.append(s)

    def visit_Compound(self, node):
        s = '  node{} [label="Compound"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        for child in node.children:
            self.visit(child)
            s = '  node{} -> node{}\n'.format(node._num, child._num)
            self.dot_body.append(s)

    def visit_Expression(self, node):
        s = '  node{} [label="Expression"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        self.visit(node.expr)
        s = '  node{} -> node{}\n'.format(node._num, node.expr._num)
        self.dot_body.append(s)

    def visit_FormalParams(self, node):
        s = '  node{} [label="FormalParams"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        for child in node.children:
            self.visit(child)
            s = '  node{} -> node{}\n'.format(node._num, child._num)
            self.dot_body.append(s)

    def visit_AgentRange(self, node):
        s = '  node{} [label="AgentRange"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1

        self.visit(node.agent)
        s = '  node{} -> node{}\n'.format(node._num, node.agent._num)
        self.dot_body.append(s)
        
        self.visit(node.start)
        s = '  node{} -> node{}\n'.format(node._num, node.start._num)
        self.dot_body.append(s)
        
        self.visit(node.end)
        s = '  node{} -> node{}\n'.format(node._num, node.end._num)
        self.dot_body.append(s)

    def visit_Var(self, node):
        s = '  node{} [label="{}"]\n'.format(self.ncount, node.value)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1

    def visit_Num(self, node):
        s = '  node{} [label="{}"]\n'.format(self.ncount, node.token.value)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1

    def visit_BinOp(self, node):
        s = '  node{} [label="{}"]\n'.format(self.ncount, node.op.value)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        self.visit(node.left)
        self.visit(node.right)
        for child_node in (node.left, node.right):
            s = '  node{} -> node{}\n'.format(node._num, child_node._num)
            self.dot_body.append(s)

    def visit_UnaryOp(self, node):
        s = '  node{} [label="unary {}"]\n'.format(self.ncount, node.op.value)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1
        self.visit(node.expr)
        s = '  node{} -> node{}\n'.format(node._num, node.expr._num)
        self.dot_body.append(s)

    def visit_NoOp(self, node):
        s = '  node{} [label="NoOp"]\n'.format(self.ncount)
        self.dot_body.append(s)
        node._num = self.ncount
        self.ncount += 1

    def gendot(self):
        tree = self.parser.parse()
        self.visit(tree)
        return ''.join(self.dot_header + self.dot_body + self.dot_footer)


def main():
    argparser = argparse.ArgumentParser(
        description='Generate an AST DOT file.'
    )
    argparser.add_argument(
        'fname',
        help='Pascal source file'
    )
    args = argparser.parse_args()
    fname = args.fname
    file_name = re.split(r'[./]', fname)[1]  # Extract file name without extension
    text = open(fname, 'r').read()

    lexer = Lexer(text)
    parser = Parser(lexer)
    viz = ASTVisualizer(parser)
    content = viz.gendot()

    # Write the DOT content to a file using args member variable
    with open("dot/" + file_name + '.dot', 'w') as f:
        f.write(content)
    # Generate the PNG file from the DOT file
    subprocess.run(["dot", "-Tpng", "-o", "dot/" + file_name + '.png', "dot/" + file_name + '.dot'])
    print("Done!")


if __name__ == '__main__':
    main()
