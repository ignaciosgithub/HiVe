import token
import platform
from lexer import Lexer
import token_types
from parser import Parser
from code_generator import CodeGenerator, LinuxCodeGenerator, RISCCodeGenerator
import subprocess

def get_code_generator():
    """Get the appropriate code generator based on platform."""
    # Force RISC generation for testing
    return RISCCodeGenerator()
    # Original platform check code:
    # system = platform.system()
    # if system == 'Windows':
    #     return CodeGenerator()
    # elif system == 'Linux':
    #     return LinuxCodeGenerator()
    # else:
    #     return RISCCodeGenerator()

def compile_to_asm(source_code, output_filename='outputtest.asm'):
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    print("Tokens:", tokens)
    parser = Parser(tokens)
    ast = parser.parse()
    print("AST:", ast)
    generator = get_code_generator()
    asm_code = generator.generate(ast)
    with open(output_filename, 'w') as f:
        f.write(asm_code)
    print(asm_code)

def assemble_and_link(asm_filename='outputtest.asm', obj_filename='outputtest.o', exe_filename='outputtest'):
    """Assemble and link the generated code using appropriate tools."""
    try:
        # Always use ARM64 toolchain since we're forcing RISC generation
        subprocess.run(['aarch64-linux-gnu-as', '-o', obj_filename, asm_filename], check=True)
        subprocess.run(['aarch64-linux-gnu-gcc', '-static', '-o', exe_filename, obj_filename], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during assembly/linking: {e}")
        raise
    except FileNotFoundError as e:
        print(f"Required tool not found: {e}")
        print("Please ensure aarch64-linux-gnu-as and aarch64-linux-gnu-gcc are installed.")
        raise

def main():
    source_code = """
a = 5
b = 3
c = a + b
print c
    """
    compile_to_asm(source_code)
    assemble_and_link()

if __name__ == '__main__':
    main()
