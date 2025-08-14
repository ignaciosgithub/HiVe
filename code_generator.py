from token_types import (
    TT_PLUS, TT_MINUS, TT_MUL, TT_DIV,
    TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE
)
import itertools
from nodes import *
import platform

class CodeGenerator:
    def __init__(self):
        self.asm_code = []
        self.functions = {}
        self.labels = 0
        self.variables = {}
        self.string_constants = []
        self.current_function_end_label = None
        self.variable_scopes = [{}]

    def setup(self):
        """Set up the initial assembly code."""
        self.asm_code.append('global main')
        self.asm_code.append('extern printf')
        self.asm_code.append('extern ExitProcess')
        self.asm_code.append('extern GetProcessHeap')
        self.asm_code.append('extern HeapAlloc')
        self.asm_code.append('extern HeapFree')
        self.asm_code.append('extern CreateThread')
        self.asm_code.append('extern CloseHandle')

        self.asm_code.append('section .data')
        self.asm_code.append('format db "%lld", 10, 0')

        self.asm_code.append('HEAP_ZERO_MEMORY equ 0x00000008')
        self.asm_code.append('section .bss')
        self.asm_code.append('heap_handle: resq 1')

        self.asm_code.append('section .text')
        self.asm_code.append('main:')
        self.asm_code.append('    sub rsp, 40')

        self.asm_code.append('    call GetProcessHeap')
        self.asm_code.append('    mov [heap_handle], rax')

    def cleanup(self):
        self.asm_code.append('    mov ecx, 0')
        self.asm_code.append('    call ExitProcess')

    def generate(self, nodes):
        """Generate assembly code for the AST."""
        self.setup()

        # Initialize symbol tables
        self.variables = {}
        self.variable_scopes = [{}]

        # Visit each node in the AST
        for node in nodes:
            self.visit(node)

        # Add cleanup code
        self.cleanup()

        bss_vars = []
        for var_name, var_info in self.variables.items():
            if var_info['type'] == 'scalar':
                bss_vars.append(f'{var_name}: resq 1')
            elif var_info['type'] == 'array':
                total_size = var_info.get('size', 1)
                bss_vars.append(f'{var_name}: resq {total_size}')
            elif var_info['type'] == 'dynamic_array':
                bss_vars.append(f'{var_name}: resq 1')
        if bss_vars:
            text_idx = self.asm_code.index('section .text')
            self.asm_code = self.asm_code[:text_idx] + bss_vars + self.asm_code[text_idx:]

        # Join all assembly code
        return '\n'.join(self.asm_code)


    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.no_visit_method)
        return visitor(node)

    def no_visit_method(self, node):
        raise Exception(f"No visit_{type(node).__name__} method defined")

    def visit_NumberNode(self, node):
        self.asm_code.append(f'    mov rax, {node.token.value}')
        return 'rax'

    def visit_VarAssignNode(self, node):
       if isinstance(node.left_node, VarAccessNode):
           var_name = node.left_node.var_name_token.value
           # Check if variable exists in any scope
           for scope in reversed(self.variable_scopes):
               if var_name in scope:
                   # Variable already exists; use it
                   break

               # Variable not found; declare it in current scope
               print("declaring scalar")
               self.variable_scopes[-1][var_name] = {'type': 'scalar'}
               self.variables[var_name] = {'type': 'scalar'}
           self.visit(node.value_node)
           self.asm_code.append(f'    mov qword [{var_name}], rax')  # Use qword for 64-bit
       elif isinstance(node.left_node, ArrayAccessNode):
           # Assignment to array element
           self.visit_ArrayAssignNode(node.left_node, node.value_node)
       else:
           raise Exception(f"Invalid left-hand side in assignment")

    def visit_VarAccessNode(self, node):
       var_name = node.var_name_token.value
       for scope in reversed(self.variable_scopes):
           if var_name in scope:
               break
           elif var_name not in self.variables:
               self.variables[var_name] = {'type': 'scalar'}
       var_info = self.variables[var_name]
       if var_info['type'] == 'scalar':
           self.asm_code.append(f'    mov rax, qword [{var_name}]')
       elif var_info['type'] == 'dynamic_array':
           self.asm_code.append(f'    mov rax, [{var_name}]')
       else:
           raise Exception(f"Cannot access variable of type '{var_info['type']}'")
       return 'rax'
    def visit_WhileNode(self, node):
        label_start = f'WHILE_START_{self.labels}'
        label_end = f'WHILE_END_{self.labels}'
        self.labels += 1

        self.asm_code.append(f'{label_start}:')
        self.visit(node.condition_node)
        self.asm_code.append('    cmp rax, 0')
        self.asm_code.append(f'    je {label_end}')
        for stmt in node.body_node:
            self.visit(stmt)
        self.asm_code.append(f'    jmp {label_start}')
        self.asm_code.append(f'{label_end}:')



    def visit_BinOpNode(self, node):
        if node.op_token.type in (TT_PLUS, TT_MINUS, TT_MUL, TT_DIV):
            self.visit(node.left_node)
            self.asm_code.append('    push rax')  # Save left operand
            self.visit(node.right_node)
            self.asm_code.append('    mov rbx, rax')  # Move right operand to rbx
            self.asm_code.append('    pop rax')   # Restore left operand to rax

            if node.op_token.type == TT_PLUS:
                self.asm_code.append('    add rax, rbx')  # rax (left) = left + right
            elif node.op_token.type == TT_MINUS:
                self.asm_code.append('    sub rax, rbx')  # rax (left) = left - right
            elif node.op_token.type == TT_MUL:
                self.asm_code.append('    imul rax, rbx')  # rax (left) = left * right
            elif node.op_token.type == TT_DIV:
                self.asm_code.append('    mov rdx, rax')   # Copy dividend to rdx
                self.asm_code.append('    sar rdx, 63')    # Sign extend RAX into RDX
                self.asm_code.append('    idiv rbx')       # rax = rax / rbx (left / right)
        elif node.op_token.type in (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE):
            self.visit(node.left_node)
            self.asm_code.append('    push rax')
            self.visit(node.right_node)
            self.asm_code.append('    pop rbx')
            self.asm_code.append('    cmp rbx, rax')
            if node.op_token.type == TT_EE:
                self.asm_code.append('    sete al')
            elif node.op_token.type == TT_NE:
                self.asm_code.append('    setne al')
            elif node.op_token.type == TT_LT:
                self.asm_code.append('    setl al')
            elif node.op_token.type == TT_GT:
                self.asm_code.append('    setg al')
            elif node.op_token.type == TT_LTE:
                self.asm_code.append('    setle al')
            elif node.op_token.type == TT_GTE:
                self.asm_code.append('    setge al')
            self.asm_code.append('    movzx rax, al')  # Zero-extend al to rax
        else:
            raise Exception(f"Unknown binary operator {node.op_token.type}")

    def visit_PrintNode(self, node):
        value_reg = self.visit(node.value_node)
        self.asm_code.append('    sub rsp, 32')
        self.asm_code.append('    lea rcx, [rel format]')
        self.asm_code.append(f'    mov rdx, {value_reg}')
        self.asm_code.append('    call printf')
        self.asm_code.append('    add rsp, 32')
        return None

    def visit_IfNode(self, node):
        label_else = f"ELSE_{self.labels}"
        label_end = f"ENDIF_{self.labels}"
        self.labels += 1

        # Evaluate condition
        self.visit(node.condition_node)
        self.asm_code.append('    cmp rax, 0')
        if node.false_statements is not None:
            self.asm_code.append(f'    je {label_else}')
        else:
            self.asm_code.append(f'    je {label_end}')

        # True branch
        for stmt in node.true_statements:
            self.visit(stmt)
        self.asm_code.append(f'    jmp {label_end}')

        if node.false_statements is not None:
            # Else label
            self.asm_code.append(f'{label_else}:')
            # False branch
            for stmt in node.false_statements:
                self.visit(stmt)

        # End if label
        self.asm_code.append(f'{label_end}:')
    def visit_UnaryOpNode(self, node):
        self.visit(node.node)
        if node.op_token.type == TT_MINUS:
            self.asm_code.append('    neg rax')
        elif node.op_token.type == TT_PLUS:
            pass  # Unary plus doesn't change the value
        else:
            raise Exception(f"Unknown unary operator {node.op_token.type}")
    def visit_ArrayDeclarationNode(self, node):
        var_name = node.var_name_token.value
        # Calculate total size
        total_size = 1
        for size in node.sizes:
            total_size *= size
        self.variables[var_name] = {'type': 'array', 'size': total_size, 'dimensions': node.sizes}

    def visit_ArrayAssignNode(self, node, value_node=None):
        var_name = node.var_name_token.value
        if var_name == '[':
            return
        for scope in reversed(self.variable_scopes):
            if var_name in scope:
                print(var_name)

                break
            else:
                self.variables[var_name] = {'type': 'dynamic_array'}#raise Exception(f"Undefined array '{var_name}' assigned to")
        self.variables[var_name] = {'type': 'dynamic_array'}
        var_info = self.variables[var_name]
        if var_info['type'] == 'dynamic_array':
            if len(node.indexes) != 1:
                raise Exception("Dynamic arrays are one-dimensional")

            # Compute index
            self.visit(node.indexes[0])
            self.asm_code.append('    push rax')  # Save index on stack

            if value_node:
                # Assignment to array element
                self.visit(value_node)
                self.asm_code.append('    mov rcx, rax')      # Value to assign
                self.asm_code.append('    pop rdx')           # Restore index
                self.asm_code.append(f'    mov r8, [{var_name}]')  # Base address of array
                self.asm_code.append('    mov [r8 + rdx*8], rcx')  # Store value at address
            else:
            # Reading from array (though assign node typically doesn't read)
                self.asm_code.append('    pop rdx')           # Restore index
                self.asm_code.append(f'    mov r8, [{var_name}]')  # Base address of array
                self.asm_code.append('    mov rax, [r8 + rdx*8]')  # Load value at index into rax
        else:
            raise Exception(f"Unsupported array type '{var_info['type']}'")

    def visit_ArrayAccessNode(self, node):
        var_name = node.var_name_token.value
        if var_name == '[':
            return

        for scope in reversed(self.variable_scopes):
            if var_name in scope:
                print(var_name)
                break


        self.variables[var_name] = {'type': 'dynamic_array'}
        var_info = self.variables[var_name]
        if var_info['type'] == 'dynamic_array':
            # Compute index
            self.visit(node.indexes[0])
            self.asm_code.append('    push rax')  # Save index on stack
            self.asm_code.append(f'    mov rax, [{var_name}]')  # Base address of array
            self.asm_code.append('    pop rdx')   # Restore index
            self.asm_code.append('    mov rax, [rax + rdx*8]')  # Load value at index into rax
        else:
            raise Exception(f"Cannot access variable of type '{var_info['type']}'")

    def calculate_array_offset(self, node, var_info):
        # Calculate the linear offset for multi-dimensional arrays
        self.asm_code.append('    mov rax, 0')  # Initialize offset
        for i, index_expr in enumerate(node.indexes):
            self.asm_code.append('    push rax')  # Save current offset
            self.visit(index_expr)                # Compute index value in rax
            # Multiply index by the size of the remaining dimensions
            remaining_size = 1
            for size in var_info['dimensions'][i+1:]:
                remaining_size *= size
            self.asm_code.append(f'    imul rax, {remaining_size}')
            self.asm_code.append('    pop rbx')   # Retrieve previous offset
            self.asm_code.append('    add rax, rbx')  # Update total offset
    def visit_DynamicArrayAllocNode(self, node):
        var_name = node.var_name_token.value
        # Check if variable exists in any scope
        for scope in reversed(self.variable_scopes):
          if var_name in scope:
              # Variable already exists; update type
              scope[var_name]['type'] = 'dynamic_array'
              break
          else:
          # Variable not found; declare it in current scope
            self.variable_scopes[-1][var_name] = {'type': 'dynamic_array'}
            self.variables[var_name] = {'type': 'dynamic_array'}

      # Evaluate size expression
        self.visit(node.size_expr)
        self.asm_code.append('    mov rcx, [heap_handle]')  # Heap handle
        self.asm_code.append('    mov rdx, HEAP_ZERO_MEMORY')  # Heap allocation flags
        self.asm_code.append('    imul rax, 8')
        self.asm_code.append('    mov r8, rax')  # Size of allocation
        self.asm_code.append('    call HeapAlloc')
        self.asm_code.append(f'    mov [{var_name}], rax')  # Store pointer in variable
    def visit_DeleteNode(self, node):
        var_name = node.var_name_token.value
        if var_name not in self.variables or self.variables[var_name]['type'] != 'dynamic_array':
            raise Exception(f"Variable '{var_name}' is not a dynamic array")
        self.asm_code.append('    mov rcx, [heap_handle]')   # Heap handle
        self.asm_code.append(f'    mov rdx, [{var_name}]')   # Pointer to free
        self.asm_code.append('    mov r8, 0')                # HeapFree flags
        self.asm_code.append('    call HeapFree')
        # Optionally, remove the variable
        #del self.variables[var_name]
    def visit_FunctionDefNode(self, node):
        print(self.functions)
        try:

            func_name = node.func_name_token.value
        except:
            return
        print(func_name)

        self.functions[func_name] = {'threaded': node.threaded}
        label_func_start = f"FUNC_{func_name}"
        label_func_end = f"FUNC_{func_name}_END"


        # Store the current asm_code to restore after function definition
        main_asm_code = self.asm_code
        self.asm_code = []

        # Function label
        self.asm_code.append(f'{label_func_start}:')
        self.current_function_end_label = label_func_end

        # Threaded functions need a different prologue
        if node.threaded:
            self.asm_code.append('    mov rdx, rcx')  # Thread parameter is in rcx
            self.asm_code.append('    push rbp')
            self.asm_code.append('    mov rbp, rsp')
            # Handle parameters if needed
            # ... (similar to normal functions) ...
        else:
            # Prologue
            self.asm_code.append('    push rbp')
            self.asm_code.append('    mov rbp, rsp')
            # Handle parameters
            num_params = len(node.param_tokens)
            param_registers = ['rcx', 'rdx', 'r8', 'r9']
            for i, param_token in enumerate(node.param_tokens):
                self.variables[param_token.value] = {'type': 'scalar'}
                print(param_token.value)
                if i < 4:
                    reg = param_registers[i]
                    self.asm_code.append(f'    mov qword [{param_token.value}], {reg}')
                else:
                    offset = (i - 4) * 8 + 16
                    self.asm_code.append(f'    mov rax, qword [rbp + {offset}]')
                    self.asm_code.append(f'    mov qword [{param_token.value}], rax')
                if param_token.value not in self.variables:
                    self.variables[param_token.value] = {'type': 'scalar'}

    # Function body
        for stmt in node.body_nodes:
            self.visit(stmt)

    # Epilogue
        self.asm_code.append(f'{label_func_end}:')
        self.asm_code.append('    mov rsp, rbp')
        self.asm_code.append('    pop rbp')
        if node.threaded:
            self.asm_code.append('    ret')  # Return to thread exit
        else:
            self.asm_code.append('    ret')

        # Save the function code
        func_code = self.asm_code

        # Restore the main asm_code
        self.asm_code = main_asm_code
        # Insert the function code at the beginning (or appropriate place)
        self.asm_code = func_code + self.asm_code
        self.current_function_end_label = label_func_end
    def visit_FunctionDefNode(self, node):
       func_name = node.func_name_token.value
       self.functions[func_name] = {'threaded': node.threaded}
       label_func_start = f"FUNC_{func_name}"
       label_func_end = f"FUNC_{func_name}_END"

       # Store the current asm_code to restore after function definition
       main_asm_code = self.asm_code
       self.asm_code = []

       # Function label
       self.asm_code.append(f'{label_func_start}:')
       self.current_function_end_label = label_func_end

       # Push a new variable scope for the function
       self.variable_scopes.append({})

       # Prologue
       self.asm_code.append('    push rbp')
       self.asm_code.append('    mov rbp, rsp')
       # Handle parameters
       num_params = len(node.param_tokens)
       param_registers = ['rcx', 'rdx', 'r8', 'r9']
       for i, param_token in enumerate(node.param_tokens):
           if i < 4:
               reg = param_registers[i]
               self.asm_code.append(f'    mov qword [{param_token.value}], {reg}')
           else:
               offset = (i - 4) * 8 + 16
               self.asm_code.append(f'    mov rax, qword [rbp + {offset}]')
               self.asm_code.append(f'    mov qword [{param_token.value}], rax')
           # Declare parameter in the function's scope
           self.variable_scopes[-1][param_token.value] = {'type': 'scalar'}
           self.variables[param_token.value] = {'type': 'scalar'}
       # Function body
       for stmt in node.body_nodes:
           self.visit(stmt)

       # Epilogue
       self.asm_code.append(f'{label_func_end}:')
       self.asm_code.append('    mov rsp, rbp')
       self.asm_code.append('    pop rbp')
       self.asm_code.append('    ret')

       # Pop the function's scope
       self.variable_scopes.pop()

       # Save the function code
       func_code = self.asm_code

       # Restore the main asm_code
       self.asm_code = main_asm_code
       # Insert the function code at the beginning (or appropriate place)
       self.asm_code = func_code + self.asm_code
       self.current_function_end_label = label_func_end

    def visit_FunctionCallNode(self, node):
        func_name = node.func_name_token.value
        # Check if the function is threaded
        is_threaded = self.functions.get(func_name, {}).get('threaded', False)
        # You might need to keep track of function definitions and whether they are threaded
        print(is_threaded)
        # Evaluate arguments


        if not is_threaded:
            arg_registers = ['rcx', 'rdx', 'r8', 'r9']
            num_args = len(node.arg_nodes)
            # Normal function call
            if num_args > 4:
                raise Exception("More than 4 arguments not yet supported")
            for i in range(num_args):
                self.visit(node.arg_nodes[i])
                self.asm_code.append(f'    mov {arg_registers[i]}, rax')
            self.asm_code.append(f'    call FUNC_{func_name}')
        else:
            # Threaded function call
            # For simplicity, we won't pass arguments to threaded functions in this example
            # Alternatively, you can pass parameters via a structure allocated on the heap

            # Create the thread
            self.asm_code.append('    sub rsp, 40')  # Allocate 40 bytes (32 for shadow space + 8 for alignment)

        # Set stack parameters (dwCreationFlags and lpThreadId)
            self.asm_code.append('    mov dword [rsp + 32], 0')    # dwCreationFlags = 0
            self.asm_code.append('    mov qword [rsp + 40], 0')    # lpThreadId = NULL

        # Set register parameters
            self.asm_code.append('    mov rcx, 0')                 # lpThreadAttributes = NULL
            self.asm_code.append('    mov rdx, 0')                 # dwStackSize = 0 (default size)
            self.asm_code.append(f'    lea r8, [rel FUNC_{func_name}]')  # lpStartAddress (function address)
            self.asm_code.append('    mov r9, 0')                  # lpParameter = NULL

        # Call CreateThread
            self.asm_code.append('    call CreateThread')

        # Clean up the stack
            self.asm_code.append('    add rsp, 40')                # Restore stack pointer

        # Close the thread handle
            self.asm_code.append('    mov rcx, rax')               # Thread handle returned in rax
            self.asm_code.append('    call CloseHandle')  # Close the thread handle
    def visit_ReturnNode(self, node):
        self.visit(node.value_node)
        # RAX already contains the return value
        self.asm_code.append('    jmp ' + self.current_function_end_label)

class LinuxCodeGenerator(CodeGenerator):
    def __init__(self):
        super().__init__()

    def setup(self):
        """Linux-specific setup"""
        self.asm_code.append('global main')
        self.asm_code.append('extern printf')
        self.asm_code.append('extern malloc')
        self.asm_code.append('extern free')
        self.asm_code.append('extern pthread_create')
        self.asm_code.append('extern pthread_join')

        self.asm_code.append('section .data')
        self.asm_code.append('format: db "%lld", 10, 0')  # format string for printing

        self.asm_code.append('section .bss')
        self.asm_code.append('section .text')

        self.asm_code.append('main:')
        self.asm_code.append('    push rbp')
        self.asm_code.append('    mov rbp, rsp')
        self.asm_code.append('    sub rsp, 32')  # Maintain 16-byte alignment

    def cleanup(self):
        """Linux-specific cleanup"""
        self.asm_code.append('    mov rsp, rbp')
        self.asm_code.append('    pop rbp')
        self.asm_code.append('    xor eax, eax')  # Return 0
        self.asm_code.append('    ret')

    def generate(self, nodes):
        """Override generate to use Linux cleanup"""
        self.asm_code = []
        self.setup()

        for node in nodes:
            if isinstance(node, FunctionDefNode):
                self.visit(node)
        for node in nodes:
            if not isinstance(node, FunctionDefNode):
                self.visit(node)

        self.cleanup()

        bss_section = ['section .bss']
        for var_name, var_info in self.variables.items():
            if var_info['type'] == 'scalar':
                bss_section.append(f'{var_name}: resq 1')
            elif var_info['type'] == 'array':
                total_size = var_info['size']
                bss_section.append(f'{var_name}: resq {total_size}')
            elif var_info['type'] == 'dynamic_array':
                bss_section.append(f'{var_name}: resq 1')

        data_section_end = self.asm_code.index('section .text')
        self.asm_code = self.asm_code[:data_section_end] + bss_section + self.asm_code[data_section_end:]

        return '\n'.join(self.asm_code)

    def visit_PrintNode(self, node):
        """Linux x64 calling convention for printf"""
        self.visit(node.value_node)
        self.asm_code.append('    mov rsi, rax')        # Second argument (value)
        self.asm_code.append('    lea rdi, [rel format]')  # First argument (format string)
        self.asm_code.append('    xor eax, eax')        # No floating point arguments
        self.asm_code.append('    call printf')

    def visit_DynamicArrayAllocNode(self, node):
        """Linux implementation of dynamic array allocation using malloc"""
        var_name = node.var_name_token.value
        # Update variable type in scopes
        for scope in reversed(self.variable_scopes):
            if var_name in scope:
                scope[var_name]['type'] = 'dynamic_array'
                break
            else:
                self.variable_scopes[-1][var_name] = {'type': 'dynamic_array'}
                self.variables[var_name] = {'type': 'dynamic_array'}

        # Evaluate size expression and allocate memory
        self.visit(node.size_expr)
        self.asm_code.append('    imul rax, 8')         # Multiply by 8 for 64-bit integers
        self.asm_code.append('    mov rdi, rax')        # Size argument for malloc
        self.asm_code.append('    call malloc')         # Call malloc
        self.asm_code.append('    test rax, rax')       # Check if allocation failed
        self.asm_code.append('    jz allocation_failed')
        self.asm_code.append(f'    mov [{var_name}], rax')  # Store pointer in variable

    def visit_DeleteNode(self, node):
        """Linux implementation of memory deallocation using free"""
        var_name = node.var_name_token.value
        if var_name not in self.variables or self.variables[var_name]['type'] != 'dynamic_array':
            raise Exception(f"Variable '{var_name}' is not a dynamic array")


        self.asm_code.append(f'    mov rdi, [{var_name}]')   # Pointer argument for free
        self.asm_code.append('    call free')                # Call free

    def visit_FunctionDefNode(self, node):
        """Linux implementation of function definitions"""
        try:
            func_name = node.func_name_token.value
        except:
            return

        self.functions[func_name] = {'threaded': node.threaded}
        label_func_start = f"FUNC_{func_name}"
        label_func_end = f"FUNC_{func_name}_END"

        # Store current asm_code
        main_asm_code = self.asm_code
        self.asm_code = []

        # Function label
        self.asm_code.append(f'{label_func_start}:')
        self.current_function_end_label = label_func_end

        if node.threaded:
            # Thread function receives a single void* parameter in rdi
            self.asm_code.append('    push rbp')
            self.asm_code.append('    mov rbp, rsp')
            self.asm_code.append('    push rdi')  # Save thread parameter
        else:
            # Regular function prologue
            self.asm_code.append('    push rbp')
            self.asm_code.append('    mov rbp, rsp')
            # Handle parameters using Linux calling convention
            param_registers = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
            for i, param_token in enumerate(node.param_tokens):
                self.variables[param_token.value] = {'type': 'scalar'}
                if i < 6:
                    reg = param_registers[i]
                    self.asm_code.append(f'    mov qword [{param_token.value}], {reg}')

        # Function body
        for stmt in node.body_nodes:
            self.visit(stmt)

        # Epilogue
        self.asm_code.append(f'{label_func_end}:')
        self.asm_code.append('    mov rsp, rbp')
        self.asm_code.append('    pop rbp')
        if node.threaded:
            self.asm_code.append('    ret')  # Return to thread exit
        else:
            self.asm_code.append('    ret')

        # Save the function code
        func_code = self.asm_code

        # Restore the main asm_code
        self.asm_code = main_asm_code
        # Insert the function code at the beginning (or appropriate place)
        self.asm_code = func_code + self.asm_code
        self.current_function_end_label = label_func_end

    def visit_FunctionCallNode(self, node):
        func_name = node.func_name_token.value

        if func_name in self.functions and self.functions[func_name]['threaded']:
            thread_var = f'thread_{self.labels}'
            self.labels += 1
            self.asm_code.append('    sub rsp, 8')
            self.asm_code.append('    mov [rsp], rsp')

            self.asm_code.append('    mov rdi, rsp')
            self.asm_code.append('    xor rsi, rsi')
            self.asm_code.append(f'    lea rdx, [rel FUNC_{func_name}]')
            self.asm_code.append('    xor rcx, rcx')

            self.asm_code.append('    call pthread_create')
            self.asm_code.append('    test rax, rax')
            self.asm_code.append('    jnz thread_error')

            self.asm_code.append('    add rsp, 8')
        else:
            registers = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
            stack_args = []

            for i, arg in enumerate(node.arg_nodes):
                self.visit(arg)
                if i < 6:
                    self.asm_code.append(f'    mov {registers[i]}, rax')
                else:
                    stack_args.append(arg)

            if stack_args:
                for arg in reversed(stack_args):
                    self.visit(arg)
                    self.asm_code.append('    push rax')

            if len(stack_args) % 2 != 0:
                self.asm_code.append('    sub rsp, 8')

            self.asm_code.append(f'    call FUNC_{func_name}')

            if stack_args:
                cleanup_size = len(stack_args) * 8
                if len(stack_args) % 2 != 0:
                    cleanup_size += 8
                self.asm_code.append(f'    add rsp, {cleanup_size}')

    def thread_error(self):
        self.asm_code.append('thread_error:')
        self.asm_code.append('    mov rax, -1')

class RISCCodeGenerator(CodeGenerator):
    def __init__(self):
        super().__init__()
        # ARM64 register mapping
        self.register_map = {
            'x0': 'return value/first argument',
            'x1': 'second argument',
            'x2': 'third argument',
            'x3': 'fourth argument',
            'x4': 'fifth argument',
            'x5': 'sixth argument',
            'x6': 'seventh argument',
            'x7': 'eighth argument',
            'x8': 'indirect result location register',
            'x9': 'temporary register',
            'x10': 'temporary register',
            'x11': 'temporary register',
            'x12': 'temporary register',
            'x13': 'temporary register',
            'x14': 'temporary register',
            'x15': 'temporary register',
            'x16': 'intra-procedure-call temporary register',
            'x17': 'intra-procedure-call temporary register',
            'x18': 'platform register',
            'x19': 'callee-saved register',
            'x20': 'callee-saved register',
            'x21': 'callee-saved register',
            'x22': 'callee-saved register',
            'x23': 'callee-saved register',
            'x24': 'callee-saved register',
            'x25': 'callee-saved register',
            'x26': 'callee-saved register',
            'x27': 'callee-saved register',
            'x28': 'callee-saved register',
            'x29': 'frame pointer',
            'x30': 'link register',
            'sp': 'stack pointer',
        }
        # Special registers for code generation
        self.result_register = 'x0'
        self.temp_registers = ['x9', 'x10', 'x11', 'x12', 'x13', 'x14', 'x15']
        self.argument_registers = ['x0', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7']
        self.callee_saved = ['x19', 'x20', 'x21', 'x22', 'x23', 'x24', 'x25', 'x26', 'x27', 'x28']

    def setup(self):
        """Initialize ARM64 assembly code with proper sections and external declarations."""
        self.asm_code = []

        # Data section for format strings and constants
        self.asm_code.append('.data')
        self.asm_code.append('format_int: .string "%ld\\n"')
        self.asm_code.append('.align 3')  # 8-byte alignment

        # BSS section for uninitialized data
        self.asm_code.append('.bss')
        self.asm_code.append('.align 3')

        # Text section for code
        self.asm_code.append('.text')
        self.asm_code.append('.align 2')  # 4-byte alignment for instructions
        self.asm_code.append('.global main')
        self.asm_code.append('.type main, %function')

        # External functions
        self.asm_code.append('.extern printf')

        # Program entry point
        self.asm_code.append('main:')
        self.asm_code.append('    stp x29, x30, [sp, #-16]!')  # Save frame pointer and link register
        self.asm_code.append('    mov x29, sp')                 # Set up frame pointer

    def cleanup(self):
        """ARM64-specific cleanup"""
        # Restore stack and frame pointer
        self.asm_code.append('    mov sp, x29')                # Restore stack pointer
        self.asm_code.append('    ldp x29, x30, [sp], #16')   # Restore FP and LR

        # Exit program
        self.asm_code.append('    mov x0, #0')                 # Return code 0
        self.asm_code.append('    mov x8, #93')               # exit syscall number
        self.asm_code.append('    svc #0')                    # Make syscall

    def visit_BinOpNode(self, node):
        """Generate ARM64 assembly for binary operations."""
        # Visit left and right nodes to get their values in registers
        left_reg = self.visit(node.left_node)
        self.asm_code.append(f'    mov x2, {left_reg}')  # Save left value
        right_reg = self.visit(node.right_node)
        self.asm_code.append(f'    mov x3, {right_reg}')  # Save right value

        result_reg = 'x0'
        # Perform the operation based on the operator
        if node.op_token.type == TT_PLUS:
            self.asm_code.append(f'    add {result_reg}, x2, x3')
        elif node.op_token.type == TT_MINUS:
            self.asm_code.append(f'    sub {result_reg}, x2, x3')
        elif node.op_token.type == TT_MUL:
            self.asm_code.append(f'    mul {result_reg}, x2, x3')
        elif node.op_token.type == TT_DIV:
            # Check for division by zero
            self.asm_code.append(f'    cmp x3, #0')
            self.asm_code.append('    b.eq division_by_zero')
            self.asm_code.append(f'    sdiv {result_reg}, x2, x3')

        # Return the register containing the result
        return result_reg

    def visit_VarAssignNode(self, node):
        """Generate ARM64 assembly for variable assignment."""
        # Get the value into a register
        value_reg = self.visit(node.value_node)

        # Get the variable name from the left node
        var_name = node.left_node.var_name_token.value

        # If this is a new variable, declare it in BSS
        if var_name not in self.variables[0]:
            self.variables[0][var_name] = {'type': 'scalar'}
            # Find BSS section and add variable declaration
            bss_index = self.asm_code.index('.bss') + 2  # Skip .bss and .align
            self.asm_code.insert(bss_index, f'{var_name}: .skip 8')

        # Store the value in memory
        self.asm_code.append(f'    adrp x1, {var_name}')
        self.asm_code.append(f'    add x1, x1, :lo12:{var_name}')
        self.asm_code.append(f'    str {value_reg}, [x1]')

        return value_reg

    def visit_VarAccessNode(self, node):
        """Generate ARM64 assembly for variable access."""
        if node.var_name_token.value not in self.variables[0]:
            raise Exception(f"Variable '{node.var_name_token.value}' not defined")

        # Load the value from memory into a register
        result_reg = 'x0'
        self.asm_code.append(f'    adrp x1, {node.var_name_token.value}')
        self.asm_code.append(f'    add x1, x1, :lo12:{node.var_name_token.value}')
        self.asm_code.append(f'    ldr {result_reg}, [x1]')

        return result_reg

    def visit_PrintNode(self, node):
        """Generate ARM64 assembly for print statement."""
        # Get the value to print in a register
        value_reg = self.visit(node.value_node)
        self.asm_code.append(f'    mov x1, {value_reg}')  # Value to print goes in x1
        self.asm_code.append('    adrp x0, format_int')   # Format string address in x0
        self.asm_code.append('    add x0, x0, :lo12:format_int')
        self.asm_code.append('    bl printf')             # Call printf
        return None
    def visit_DynamicArrayAllocNode(self, node):
        var_name = node.var_name_token.value

        for scope in reversed(self.variable_scopes):
            if var_name in scope:
                scope[var_name]['type'] = 'dynamic_array'
                break
        else:
            self.variable_scopes[-1][var_name] = {'type': 'dynamic_array'}
            self.variables[var_name] = {'type': 'dynamic_array'}
            self.asm_code.append(f'.lcomm {var_name}, 8')

        self.visit(node.size_expr)
        self.asm_code.append('    lsl x0, x0, #3')

        self.asm_code.append('    bl malloc')
        self.asm_code.append('    cbz x0, allocation_failed')

        self.asm_code.append(f'    adrp x1, {var_name}@PAGE')
        self.asm_code.append(f'    add x1, x1, {var_name}@PAGEOFF')
        self.asm_code.append('    str x0, [x1]')

    def visit_DeleteNode(self, node):
        var_name = node.var_name_token.value
        if var_name not in self.variables or self.variables[var_name]['type'] != 'dynamic_array':
            raise Exception(f"Variable '{var_name}' is not a dynamic array")

        self.asm_code.append(f'    adrp x1, {var_name}@PAGE')
        self.asm_code.append(f'    add x1, x1, {var_name}@PAGEOFF')
        self.asm_code.append('    ldr x0, [x1]')
        self.asm_code.append('    bl free')

