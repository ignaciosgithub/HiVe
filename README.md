# Assembly Compiler for a New Programming Language

Side project of creating a windows based assembly compiler for a new programming language that I invented.    

## Overview

This project is a Windows-based assembly compiler for a programming language I invented. It's an experimental side project aiming to combine modern features like functional programming, multithreading, and memory management using a stack and heap model.

## Key Features

- Stack and Heap Memory: Supports dynamic memory allocation for efficient program execution.
- Multithreading: Allows the creation of threaded functions to perform concurrent operations.
- Functional Programming: Encourages clean, modular, and reusable code.

## Current Limitations
- Bugs: Many 
- This is an experimental phase, so don't expect it to be production-ready yet!

## Requirements
To get started, ensure you have the following tools installed:

- NASM: The Netwide Assembler for assembling your code.
- GCC: For compiling and linking.
- Python: Powers parts of the compiler and tooling.

## Example Program

Below is a sample program written in the language:

```
i = 0  
j = 1  

arr = new[10] # Heap allocation for an array of 10 integers (0-9).  

threaded function reset_i() # Threaded function.  
    i = 9  
end  

reset_i()  

while j < 1000  
    i = i + 1  
    j = j + 1  

    print i # Value of 'i' depends on thread speed (10 or 11).  

    reset_i()  
end  

delete arr # Unallocate memory for 'arr'.  
```

## About the Author

This experimental project is brought to you by Ignacio Savi, who is combining creativity with systems programming to explore the limits of language design.

## Author

Ignacio Savi


## Aditional authors 
tetzgabriel

💡 Disclaimer: This project is still in development.