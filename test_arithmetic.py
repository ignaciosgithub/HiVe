import subprocess
import platform
import os

def run_test(source_code):
    """Run a test case and return the output"""
    from compiler import compile_to_asm, assemble_and_link

    # Write source to temporary file
    with open('test_input.txt', 'w') as f:
        f.write(source_code)

    # Compile and assemble
    compile_to_asm(source_code, 'test.asm')

    # Platform-specific executable name
    exe_ext = '.exe' if platform.system() == 'Windows' else ''
    exe_name = f'test{exe_ext}'
    obj_ext = '.obj' if platform.system() == 'Windows' else '.o'
    obj_name = f'test{obj_ext}'

    try:
        assemble_and_link('test.asm', obj_name, exe_name)

        # Run the executable and capture output
        result = subprocess.run(f'./{exe_name}', capture_output=True, text=True)
        return result.stdout
    finally:
        # Cleanup
        for file in ['test_input.txt', 'test.asm', obj_name, exe_name]:
            if os.path.exists(file):
                os.remove(file)

def test_subtraction():
    """Test subtraction operations"""
    test_cases = [
        ("print 5 - 3", "2"),      # Basic subtraction
        ("print 3 - 5", "-2"),     # Negative result
        ("print -5 - 3", "-8"),    # Negative first operand
        ("print 5 - -3", "8"),     # Negative second operand
        ("print 10 - 7", "3"),     # Larger numbers
        ("print 0 - 5", "-5"),     # Zero first operand
        ("print 5 - 0", "5"),      # Zero second operand
        ("print -10 - -7", "-3"),  # Both operands negative
    ]

    for source, expected in test_cases:
        print(f"Testing: {source}")
        result = run_test(source)
        assert result.strip() == expected, f"Failed: {source} = {result.strip()}, expected {expected}"
        print("✓ Passed")

def test_arithmetic_operations():
    """Test various arithmetic operations"""
    test_cases = [
        # Addition
        ("print 5 + 3", "8"),
        ("print -5 + 3", "-2"),
        # Multiplication
        ("print 5 * 3", "15"),
        ("print -5 * 3", "-15"),
        # Division
        ("print 15 / 3", "5"),
        ("print -15 / 3", "-5"),
        # Complex expressions
        ("print 10 - 5 + 3", "8"),
        ("print 20 + -5 - 7", "8"),
        ("print 5 * 3 - 10", "5"),
    ]

    for source, expected in test_cases:
        print(f"Testing: {source}")
        result = run_test(source)
        assert result.strip() == expected, f"Failed: {source} = {result.strip()}, expected {expected}"
        print("✓ Passed")

if __name__ == '__main__':
    print("Running subtraction tests...")
    test_subtraction()
    print("\nRunning general arithmetic tests...")
    test_arithmetic_operations()
    print("\nAll tests passed!")
