class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
        if self.type == 'PLUS':
           self.value = '+'
        if self.type == 'MINUS':
           self.value = '-'
        if self.type == 'MUL':
           self.value = '*'
        if self.type == 'DIV':
           self.value = '/'
        if self.type == 'TT_DELETE':
           self.value = 'delete'   
        if self.type == 'LPAREN':
           self.value = '('
        if self.type == 'RPAREN':
           self.value = ')'
    def __repr__(self):
        return f'Token({self.type}, {repr(self.value)})'
    def matches(self, type_, value):
        
        #print(self.type == type_ and self.value == value)
        return self.type == type_ and self.value == value