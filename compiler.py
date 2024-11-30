import token

from lexer import Lexer
#from token_types import TT_PLUS, TT_MINUS, TT_MUL, TT_DIV, TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE
import token_types
from parser import Parser
from code_generator import CodeGenerator

def compile_to_asm(source_code, output_filename='outputtest.asm'):
    
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    print("Tokens:", tokens)
    parser = Parser(tokens)
    ast = parser.parse()
    print("AST:", ast)
    code_generator = CodeGenerator()
    asm_code = code_generator.generate(ast)
    with open(output_filename, 'w') as f:
        f.write(asm_code)
    print(asm_code)

import subprocess

def assemble_and_link(asm_filename='outputtest.asm', obj_filename='outputtest.obj', exe_filename='outputtest.exe'):
    # Assemble
    subprocess.run(['nasm', '-f', 'win64', asm_filename, '-o', obj_filename], check=True)
    
    # Link
    subprocess.run(['gcc', '-o',exe_filename , obj_filename ], check=True)
def main():
    source_code = """
i = 0
j = 1
threaded function reset_i()
    # Wait for a moment to ensure the main thread has started incrementing
   i = 9
   
end

# Start the threaded function
reset_i()

# Main thread increments i from 0 to 10,000
while j < 1000
    i = i + 1
    j = j + 1
    print i
    reset_i()
end

    """
    compile_to_asm(source_code)
    assemble_and_link()

if __name__ == '__main__':
    main()