Windows and Linux targets with default to Windows x86_64

This repository now detects OS/architecture and selects a code generator automatically:
- Windows -> Windows x86_64
- Linux -> Linux x86_64
- Unknown or detection failure -> defaults to Windows x86_64

You can override the target explicitly:
python3 compiler.py --target windows-x86_64
python3 compiler.py --target linux-x86_64
python3 compiler.py --target arm64

The compiler prints:
- Tokens
- AST
- Generated assembly
- Machine code: after assembling, the object file bytes are printed in hex before linking.

Windows build requirements:
- NASM
- MinGW (x86_64-w64-mingw32-gcc) or a GCC on Windows environment
On Windows:
python compiler.py --target windows-x86_64
This will assemble to a .obj, print machine code, and attempt to link an .exe using MinGW or GCC if available.

Linux build requirements:
- NASM
- GCC
On Linux:
python3 compiler.py --target linux-x86_64
This will assemble to .o, print machine code, and link an executable if gcc is present.

ARM64 (RISC) requirements:
- aarch64-linux-gnu-as
- aarch64-linux-gnu-gcc
On Linux (with cross toolchain installed):
python3 compiler.py --target arm64

Notes:
- If the toolchain for the selected target is not installed, assembly/linking will be skipped with a clear message after printing what was attempted.
- Windows codegen stores the process heap handle in .bss (heap_handle) and uses Windows API calls for allocation and threading.


update: heap arrays are now accessable

Side project of creating a windows based assembly compiler for a new programming language that i invented.    

features:
stack and heap 
multithreading
functional

bugs:
many

Requirements:
Nasm
gcc
python

author of this experiment: Ignacio Savi
aditional author after first commit: tetzgabriel

example program:


i = 0

j = 1

arr = new[10] # heap alloc to 10 integers from 0 -9

threaded function reset_i() #threaded function, could also be just function. but then it would not be threaded
    
   i = 9
   
end


reset_i()


while j < 1000

    i = i + 1

    j = j + 1
    
    print i # i = 10 or 11 depending on thread speed on other thread
    
    reset_i()

end

delete arr # unallocate arr
another example




li = new[9]
i = 10

while i < 18

 li[i-11] = i
 print i
 print li[i-11]
 i = i+1
end
delete li
i = 0
j = 1
threaded function reset_i()
    # Wait for a moment to ensure the main thread has started incrementing
   i = 9
   
end

# Start the threaded function

function reset()
 i = 9
end
i = 0
# Main thread increments i from 0 to 10,000
while j < 10
    i = i + 1
    j = j + 1
    reset_i()
    print i

end

j = 0

i = 0
while j < 10
    i = i + 1
    j = j + 1
    reset()
    print i

end
