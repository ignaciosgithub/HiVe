import re
from token import Token
from token_types import *

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = -1       # Start at -1 since advance() will increment it to 0
        self.current_char = None
        self.advance()


    def advance(self):
        """Advances the 'pos' and updates 'current_char'."""
        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def tokenize(self):
        """Tokenizes the entire text."""
        
        tokens = []
        while self.current_char is not None:
            print("tokening...")
            if self.current_char in ' \t':
                self.advance()
            if self.current_char in ' \t\n':
                self.advance()
            elif self.current_char == '#':
                self.skip_comment()
            elif self.current_char.isdigit():
                tokens.append(self.make_number())
            elif self.current_char.isalpha() or self.current_char == '_':
                tokens.append(self.make_identifier())
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS,"+"))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS,"-"))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TT_MUL,"*"))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN))
                self.advance()
            elif self.current_char == '{':
                tokens.append(Token(TT_LBRACE, '{'))
                self.advance()
            elif self.current_char == '}':
                tokens.append(Token(TT_RBRACE, '}'))
                self.advance()
            elif self.current_char == ',':
                tokens.append(Token(TT_COMMA, ','))
                self.advance()
            elif self.current_char == '-':
                # Check for '->'
                self.advance()
                if self.current_char == '>':
                    tokens.append(Token(TT_ARROW, '->'))
                    self.advance()
                else:
                    tokens.append(Token(TT_MINUS, '-'))
            elif self.current_char == '=':
                tokens.append(self.make_equals())
            elif self.current_char in '<>!':
                tokens.append(self.make_comparison_operator())
            elif self.current_char == '[':
                tokens.append(Token(TT_LBRACKET, '['))
                self.advance()
            elif self.current_char == ']':
                tokens.append(Token(TT_RBRACKET, ']'))
                self.advance()
            elif self.current_char == ',':
                tokens.append(Token(TT_COMMA, ','))
                self.advance()
            else:
                break
                #raise Exception(f"Illegal character '{self.current_char}'")
        tokens.append(Token(TT_EOF))
        return tokens

    def skip_comment(self):
        """Skips characters until the end of the line."""
        while self.current_char != '\n' and self.current_char is not None:
            self.advance()
        self.advance()

    def make_number(self):
        """Creates a number token (integer for simplicity)."""
        num_str = ''
        while self.current_char is not None and self.current_char.isdigit():
            num_str += self.current_char
            self.advance()
        return Token(TT_INT, int(num_str))

    def make_identifier(self):
        id_str = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            id_str += self.current_char
            self.advance()

        if id_str in {
            'print', 'if', 'else', 'end', 'while', 'new', 'delete', 'function', 'threaded', 'return'
        }:
            print(f"Tokenizing keyword: {id_str}")
            return Token(TT_KEYWORD, id_str)
        else:
            print(f"Tokenizing identifier: {id_str}")
            return Token(TT_IDENTIFIER, id_str)

    def make_equals(self):
        """Handles '=', '=='."""
        self.advance()
        if self.current_char == '=':
            self.advance()
            return Token(TT_EE, '==')  # Return a Token instance
        else:
            return Token(TT_EQ, '=')
    def make_comparison_operator(self):
        """Handles '!=', '<=', '>=', '<', '>'."""
        char = self.current_char
        self.advance()
        if self.current_char == '=':
            self.advance()
            if char == '<':
                return Token(TT_LTE, '<=')
            elif char == '>':
                return Token(TT_GTE, '>=')
            elif char == '!':
                return Token(TT_NE, '!=')
            elif char == '=':
                return Token(TT_EE, '==')
        else:
            if char == '<':
                return Token(TT_LT, '<')
            elif char == '>':
                return Token(TT_GT, '>')
            else:
                raise Exception(f"Invalid character '{char}'")