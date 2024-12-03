from token import Token
from token_types import *
from nodes import *

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_index = -1
        self.advance()

    def advance(self):
        """Advances to the next token."""
        self.token_index += 1
        if self.token_index < len(self.tokens):
            self.current_token = self.tokens[self.token_index]
        return self.current_token

    def retreat(self):
        """Advances to the next token."""
        self.token_index -= 1
        if self.token_index < len(self.tokens):
            self.current_token = self.tokens[self.token_index]
        return self.current_token
    def parse(self):
        statements = []
        while self.current_token.type != TT_EOF:
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
        return statements
    def peek_token(self):
        peek_index = self.token_index + 1
        if peek_index < len(self.tokens):
            return self.tokens[peek_index]
        else:
            return Token(TT_EOF)
    
    def statement(self):
        if self.current_token.matches(TT_KEYWORD, 'return'):
            return self.return_statement()
        elif self.current_token.matches(TT_KEYWORD, 'function'):
            return self.function_definition()
        elif self.current_token.matches(TT_KEYWORD, 'threaded'):
            return self.threaded_function_definition()
        elif self.current_token.matches(TT_KEYWORD, 'print'):
            return self.print_statement()
        elif self.current_token.type == TT_IDENTIFIER:
            next_token = self.peek_token()
            if next_token.type == TT_EQ or next_token.type == TT_LBRACKET:
                return self.assignment()
            elif next_token.type == TT_LPAREN:
                # Function call statement
                func_name_token = self.current_token
                self.advance()  # Skip the function name
                return self.function_call(func_name_token)
            else:
            # Variable access or expression
                return self.expression()
        elif self.current_token.matches(TT_KEYWORD, 'if'):
            return self.if_statement()
        elif self.current_token.matches(TT_KEYWORD, 'delete'):
            return self.delete_statement()
        elif self.current_token.matches(TT_KEYWORD, 'while'):
            return self.while_statement()
        else:
            return self.expression()

    def return_statement(self):
        self.advance()  # Skip 'return'
        expr = self.expression()
        return ReturnNode(expr)
    def function_definition(self, threaded=False):
        if not self.current_token.matches(TT_KEYWORD, 'function'):
            raise Exception("Expected 'function' keyword in function definition")
        self.advance()
        
        
        print(self.current_token)
        func_name = self.current_token
        print(func_name)
        if func_name.type != TT_IDENTIFIER:
            raise Exception("Expected function name")
        self.advance()
        if self.current_token.type != TT_LPAREN:
            raise Exception("Expected '(' after function name")
        self.advance()

        param_tokens = self.parse_parameter_list()

        if self.current_token.type != TT_RPAREN:
            raise Exception("Expected ')' after parameters")
        self.advance()
        # Function body
        statements = []
        while not self.current_token.matches(TT_KEYWORD, 'end'):
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
        self.advance()  # Skip 'end'

        return FunctionDefNode(func_name, param_tokens, statements, threaded)

    def threaded_function_definition(self):
        self.advance()  # Skip 'threaded'
        if not self.current_token.matches(TT_KEYWORD, 'function'):
            raise Exception("Expected 'function' after 'threaded'")

        
        
        print(self.current_token)
        self.advance()
        func_name = self.current_token
        print(func_name)
        if func_name.type != TT_IDENTIFIER:
            raise Exception("Expected function name")
        self.advance()
        if self.current_token.type != TT_LPAREN:
            raise Exception("Expected '(' after function name")
        self.advance()

        param_tokens = self.parse_parameter_list()

        if self.current_token.type != TT_RPAREN:
            raise Exception("Expected ')' after parameters")
        self.advance()
        # Function body
        statements = []
        while not self.current_token.matches(TT_KEYWORD, 'end'):
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
        self.advance()  # Skip 'end'

        return FunctionDefNode(func_name, param_tokens, statements, True)        
        return self.function_definition(threaded=True)
    
    def parse_parameter_list(self):
        params = []
        if self.current_token.type == TT_IDENTIFIER:
            params.append(self.current_token)
            self.advance()
            while self.current_token.type == TT_COMMA:
                self.advance()
                if self.current_token.type != TT_IDENTIFIER:
                    raise Exception("Expected parameter name")
                params.append(self.current_token)
                self.advance()
        elif self.current_token.type == TT_RPAREN:
            # Empty parameter list
            pass
        else:
            # If the next token is not ')' or an identifier, raise an exception
            raise Exception("Expected parameter or ')'")
        return params
    def print_statement(self):
        self.advance()
        expr = self.expression()
        return PrintNode(expr)
    def while_statement(self):
        self.advance()  # Skip 'while'
        condition = self.expression()
        body_statements = []
        while not (self.current_token.type == TT_KEYWORD and self.current_token.value == 'end'):
            stmt = self.statement()
            if stmt:
                body_statements.append(stmt)
        self.advance()  # Skip 'end'
        return WhileNode(condition, body_statements)
    def variable_or_array_access(self):
        var_name_token = self.current_token  # Should be an identifier
        self.advance()
        if self.current_token.type == TT_LBRACKET:
            return self.array_access(var_name_token)
        else:
            return VarAccessNode(var_name_token)
    def assignment(self):
        # Check if the current token is an identifier
        if self.current_token.type == TT_IDENTIFIER:
            left_node = self.variable_or_array_access()
        
            if self.current_token.type == TT_EQ:
                self.advance()  # Skip '='
            
            # Check if 'new' keyword follows for dynamic array allocation
                if self.current_token.matches(TT_KEYWORD, 'new'):
                    self.advance()  # Skip 'new'
                    if self.current_token.type != TT_LBRACKET:
                        raise Exception("Expected '[' after 'new'")
                    self.advance()  # Skip '['
                    size_expr = self.expression()
                    if self.current_token.type != TT_RBRACKET:
                        raise Exception("Expected ']'")
                    self.advance()  # Skip ']'
                    # Ensure left_node is a variable, not an array access
                    if not isinstance(left_node, VarAccessNode):
                        raise Exception("Dynamic array allocation must assign to a variable")
                    # Return DynamicArrayAllocNode
                    return DynamicArrayAllocNode(left_node.var_name_token, size_expr)
                else:
                    # Regular assignment
                    right_node = self.expression()
                    return VarAssignNode(left_node, right_node)
            else:
                # Not an assignment; return the left_node (variable or array access)
                return left_node
        else:
            # Not an assignment; could be a statement or expression
            expr = self.expression()
            return expr

    def if_statement(self):
        self.advance()  # Skip 'if'
        condition = self.expression()

    # Parse the true branch statements
        true_statements = []
        while self.current_token is not None and not self.current_token.matches(TT_KEYWORD, 'else') and not self.current_token.matches(TT_KEYWORD, 'end'):
            stmt = self.statement()
            if stmt:
                true_statements.append(stmt)
            else:
                self.advance()

        false_statements = None

        # Check if there's an 'else' clause
        if self.current_token.matches(TT_KEYWORD, 'else'):
            self.advance()  # Skip 'else'
            false_statements = []
            while self.current_token is not None and not self.current_token.matches(TT_KEYWORD, 'end'):
                stmt = self.statement()
                if stmt:
                    false_statements.append(stmt)
                else:
                    self.advance()

        # Expect 'end' to close the if statement
        if not self.current_token.matches(TT_KEYWORD, 'end'):
            raise Exception("Expected 'end' after if statement")
        self.advance()  # Skip 'end'

        return IfNode(condition, true_statements, false_statements)
    def array_access(self, var_name_token):
        indexes = []
        while self.current_token.type == TT_LBRACKET:
            self.advance()  # Skip '['
            index_expr = self.expression()
            indexes.append(index_expr)
            if self.current_token.type != TT_RBRACKET:
                raise Exception("Expected ']'")
            self.advance()  # Skip ']'
        return ArrayAccessNode(var_name_token, indexes)

        return ArrayAccessNode(var_token, indexes)
    def expression(self):
        # Handle comparison expressions
        return self.binary_operation(self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE))

    def arith_expr(self):
        return self.binary_operation(self.term, (TT_PLUS, TT_MINUS))

    def term(self):
        return self.binary_operation(self.factor, (TT_MUL, TT_DIV))

    def factor(self):
        token = self.current_token
        if token.type in (TT_PLUS, TT_MINUS):
            self.advance()
            factor = self.factor()
            return UnaryOpNode(token, factor)
        if token.type == TT_INT:
            self.advance()
            return NumberNode(token)
        elif token.type == TT_IDENTIFIER:
            self.advance()
            if self.current_token.type == TT_LBRACKET:
                # Array access
                self.advance()
                index_expr = self.expression()
                if self.current_token.type != TT_RBRACKET:
                    raise Exception("Expected ']'")
                self.advance()
                return ArrayAccessNode(token, [index_expr])
            elif self.current_token.type == TT_LPAREN:
                # Function call
                self.advance()  # Skip '('
                arg_nodes = []
                if self.current_token.type != TT_RPAREN:
                    arg_nodes.append(self.expression())
                    while self.current_token.type == TT_COMMA:
                        self.advance()
                        arg_nodes.append(self.expression())
                if self.current_token.type != TT_RPAREN:
                    raise Exception("Expected ')' after function arguments")
                self.advance()  # Skip ')'
                return FunctionCallNode(token, arg_nodes)
            else:
                return VarAccessNode(token)
        elif token.type == TT_LPAREN:
            self.advance()
            expr = self.expression()
            if self.current_token.type == TT_RPAREN:
                self.advance()
                return expr
            else:
                raise Exception("Expected ')'")
        else:
            raise Exception(f"Unexpected token {token.type}")
    def function_call(self, func_name_token):
        self.advance()  # Skip '('
        arg_nodes = []
        if self.current_token.type != TT_RPAREN:
            arg_nodes.append(self.expression())
            while self.current_token.type == TT_COMMA:
                self.advance()
                arg_nodes.append(self.expression())
        if self.current_token.type != TT_RPAREN:
            raise Exception("Expected ')' after function arguments")
        self.advance()  # Skip ')'
        return FunctionCallNode(func_name_token, arg_nodes)

    def binary_operation(self, func, ops):
        left = func()
        while self.current_token.type in ops:
            op_token = self.current_token
            self.advance()
            right = func()
            left = BinOpNode(left, op_token, right)
        return left
    def while_statement(self):
        self.advance()  # Skip 'while'
        condition = self.expression()
        body_statements = []
        while not (self.current_token.type == TT_KEYWORD and self.current_token.value == 'end'):
            stmt = self.statement()
            if stmt:
                body_statements.append(stmt)
        self.advance()  # Skip 'end'
        return WhileNode(condition, body_statements)
    def delete_statement(self):
        self.advance()  # Skip 'delete'
        var_name_token = self.current_token
        if var_name_token.type != TT_IDENTIFIER:
            raise Exception("Expected identifier after 'delete'")
        self.advance()
        return DeleteNode(var_name_token)
