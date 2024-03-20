class NodeVisitor(object):
    def visit(self, node, **kwargs):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, **kwargs)

    def generic_visit(self, node, **kwargs):
        raise Exception('No visit_{} method'.format(type(node).__name__))
