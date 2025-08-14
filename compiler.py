import token
import platform
from lexer import Lexer
import token_types
from parser import Parser
from code_generator import CodeGenerator, LinuxCodeGenerator, RISCCodeGenerator
import subprocess
import argparse
import shutil
import os

def _norm_target(t):
    if not t:
        return None
    t = str(t).lower()
    if t in ("windows", "windows-x86_64", "win64"):
        return "windows-x86_64"
    if t in ("linux", "linux-x86_64", "elf64", "x86_64"):
        return "linux-x86_64"
    if t in ("arm64", "aarch64", "risc"):
        return "arm64"
    return None

def get_code_generator(target: str | None = None):
    system_target = _norm_target(target)
    if system_target is None:
        system = platform.system()
        if system == 'Windows':
            system_target = "windows-x86_64"
        elif system == 'Linux':
            system_target = "linux-x86_64"
        else:
            system_target = "windows-x86_64"
    if system_target == "windows-x86_64":
        return CodeGenerator()
    if system_target == "linux-x86_64":
        return LinuxCodeGenerator()
    return RISCCodeGenerator()

def compile_to_asm(source_code, output_filename='outputtest.asm', target: str | None = None):
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    print("Tokens:", tokens)
    parser = Parser(tokens)
    ast = parser.parse()
    print("AST:", ast)
    generator = get_code_generator(target)
    asm_code = generator.generate(ast)
    with open(output_filename, 'w') as f:
        f.write(asm_code)
    print(asm_code)

def assemble_and_link(asm_filename='outputtest.asm', obj_filename='outputtest.o', exe_filename='outputtest', target: str | None = None):
    system_target = _norm_target(target)
    if system_target is None:
        sysname = platform.system()
        if sysname == "Windows":
            system_target = "windows-x86_64"
        elif sysname == "Linux":
            system_target = "linux-x86_64"
        else:
            system_target = "windows-x86_64"
    try:
        if system_target == "windows-x86_64":
            asm = shutil.which("nasm")
            if not asm:
                raise FileNotFoundError("nasm not found for Windows target")
            obj_filename = os.path.splitext(obj_filename)[0] + ".obj"
            subprocess.run([asm, "-f", "win64", "-o", obj_filename, asm_filename], check=True)
            with open(obj_filename, "rb") as f:
                data = f.read()
            print("=== Machine code (object bytes) ===")
            print(data.hex())
            mingw = shutil.which("x86_64-w64-mingw32-gcc")
            if mingw:
                exe_filename = os.path.splitext(exe_filename)[0] + ".exe"
                subprocess.run([mingw, "-o", exe_filename, obj_filename], check=True)
            else:
                gcc = shutil.which("gcc")
                if platform.system() == "Windows" and gcc:
                    exe_filename = os.path.splitext(exe_filename)[0] + ".exe"
                    subprocess.run([gcc, "-o", exe_filename, obj_filename], check=True)
                else:
                    print("Skipping link: no MinGW (x86_64-w64-mingw32-gcc) or Windows gcc found.")
        elif system_target == "linux-x86_64":
            asm = shutil.which("nasm")
            if not asm:
                raise FileNotFoundError("nasm not found for Linux target")
            subprocess.run([asm, "-f", "elf64", "-o", obj_filename, asm_filename], check=True)
            with open(obj_filename, "rb") as f:
                data = f.read()
            print("=== Machine code (object bytes) ===")
            print(data.hex())
            gcc = shutil.which("gcc")
            if gcc:
                subprocess.run([gcc, "-o", exe_filename, obj_filename], check=True)
            else:
                print("Skipping link: gcc not found.")
        else:
            as64 = shutil.which("aarch64-linux-gnu-as")
            gcc64 = shutil.which("aarch64-linux-gnu-gcc")
            if not as64 or not gcc64:
                raise FileNotFoundError("aarch64-linux-gnu toolchain not found")
            subprocess.run([as64, "-o", obj_filename, asm_filename], check=True)
            with open(obj_filename, "rb") as f:
                data = f.read()
            print("=== Machine code (object bytes) ===")
            print(data.hex())
            subprocess.run([gcc64, "-static", "-o", exe_filename, obj_filename], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during assembly/linking: {e}")
        raise
    except FileNotFoundError as e:
        print(f"Required tool not found: {e}")
        print("Please install the toolchain for the selected target.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default=None, help="windows-x86_64|linux-x86_64|arm64")
    args = parser.parse_args()
    source_code = """
a = 5
b = 3
c = a + b
print c
    """
    compile_to_asm(source_code, target=args.target)
    assemble_and_link(target=args.target)

if __name__ == '__main__':
    main()
