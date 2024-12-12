#!/bin/bash

# Loop through values from 1 to 32
for w in {1..32}
do
    #echo "Running with -w $w"
    
    # Capture and print only the execution time
    /usr/bin/time -f "Execution time for -w $w: %e seconds" python3 main.py tasksets-multiprocessor 8 3 -H bf -w "$w" 2>&1 | grep "Execution time"
done

