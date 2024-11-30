side project of creating a windows based assembly compiler for a new programming language that i invented.    

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

author of this experiment: ignacio savi


example program:


i = 0
j = 1
arr = new[10] # heap alloc to 10 integers from 0 -9
threaded function reset_i() #threaded function
    
   i = 9
   
end

# Start the threaded function
reset_i()

# Main thread increments i from 0 to 1000
while j < 1000
    i = i + 1
    j = j + 1
    print i # i = 10 or 11 depending on thread speed on other thread
    reset_i()
end
delete arr
