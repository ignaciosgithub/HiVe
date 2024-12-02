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
