class NumberNode:
    def __init__(self, token):
        self.token = token

class BinOpNode:
    def __init__(self, left_node, op_token, right_node):
        self.left_node = left_node
        self.op_token = op_token
        self.right_node = right_node

class VarAccessNode:
    def __init__(self, var_name_token):
        self.var_name_token = var_name_token
    def __repr__(self):
        return "["+str(self.var_name_token).replace("Token(IDENTIFIER, '","").replace("')","")+']'

class VarAssignNode:
    def __init__(self, left_node, value_node):
        self.left_node = left_node  # Can be VarAccessNode or ArrayAccessNode
        self.value_node = value_node
        self.var_name_token = left_node
        self.value = value_node

class PrintNode:
    def __init__(self, value_node):
        self.value_node = value_node

class IfNode:
    def __init__(self, condition_node, true_statements, false_statements=None):
        self.condition_node = condition_node
        self.true_statements = true_statements
        self.false_statements = false_statements
class UnaryOpNode:
      def __init__(self, op_token, node):
          self.op_token = op_token
          self.node = node
class WhileNode:
    def __init__(self, condition_node, body_node):
        self.condition_node = condition_node
        self.body_node = body_node
class ArrayDeclarationNode:
    def __init__(self, var_name_token, sizes):
        self.var_name_token = var_name_token
        self.sizes = sizes  # List of sizes for each dimension

class ArrayAssignNode:
    def __init__(self, var_name_token, indexes, value_node):
        self.var_name_token = var_name_token
        self.indexes = indexes  # Index expressions
        self.value_node = value_node

class ArrayAccessNode:
    def __init__(self, var_name_token, indexes):
        self.var_name_token = var_name_token
        self.indexes = indexes  # Index expressions

class DynamicArrayAllocNode:
    def __init__(self, var_name_token, size_expr):
        self.var_name_token = var_name_token
        self.size_expr = size_expr  # Size expression
class DeleteNode:
    def __init__(self, var_name_token):
        self.var_name_token = var_name_token

class FunctionDefNode:
    def __init__(self, func_name_token, param_tokens, body_nodes, threaded=False):
        self.func_name_token = func_name_token
        self.param_tokens = param_tokens
        self.body_nodes = body_nodes
        self.threaded = threaded

class FunctionCallNode:
    def __init__(self, func_name_token, arg_nodes):
        self.func_name_token = func_name_token
        self.arg_nodes = arg_nodes

class ReturnNode:
    def __init__(self, value_node):
        self.value_node = value_node