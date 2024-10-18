from entities import TaskSet, Task, Job
from algorithms import RateMonotonic, DeadlineMonotonic, Audsley, EarliestDeadlineFirst, RoundRobin
from helpers import pie_plot

import csv
import argparse
import os

def parse_task_file(file_path):
    tasks = []
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) == 4:
                offset = int(row[0])
                computation_time = int(row[1])
                deadline = int(row[2])
                period = int(row[3])
                task = Task(offset, computation_time, deadline, period)
                tasks.append(task)
    task_set = TaskSet(tasks)
    return task_set

def parse_task_folder(folder_path):
    task_files = []
    files = os.listdir(folder_path)

    # Filter only files (ignoring directories)
    files = [f for f in files if os.path.isfile(os.path.join(folder_path, f))]
    # Print the list of files
    for file in files:
        task_files.append(file)
    return task_files

def main():
    # Set up command line argument parser
    parser = argparse.ArgumentParser(description='Select a scheduling algorithm and specify a task set file.')

    # Add the scheduling algorithm argument (mandatory)
    parser.add_argument('algorithm', choices=['rm', 'dm', 'audsley', 'edf', 'rr'],
                        help='Scheduling algorithm to use: dm, audsley, edf, or rr.')

    # Optional flag for verbose mode
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Enable verbose mode for detailed output.")
    
    # Add the task set file argument (mandatory)
    parser.add_argument('task_set_file', type=str,
                        help='Path to the task set file.')
    
    name = parser.parse_args().task_set_file
    algorithm = parser.parse_args().algorithm.lower()
    # Check if the address corresponds to a single dataset or if it is a folder containing many
    if (os.path.isfile(name)):
        review_task(algorithm = algorithm, task_set_file=name)
    else:
        review_multiple_tasks(algorithm = algorithm, folder_name=name)
        
        
def review_task(algorithm, task_set_file):
    # Parse the arguments
    # Access the parameters
    task_set = parse_task_file(task_set_file)

    if algorithm == 'rm':
        task_scheduler = RateMonotonic(task_set)
    elif algorithm == 'dm' or algorithm == 'audsley':
        task_scheduler = DeadlineMonotonic(task_set)
    elif algorithm == 'audsley':
        task_scheduler = Audsley(task_set)
    elif algorithm == 'edf':
        task_scheduler = EarliestDeadlineFirst(task_set)
    elif algorithm == 'rr':
        task_scheduler = RoundRobin(task_set)
    else:
        print("Invalid algorithm selected.") # Won't happen because of argparse but why not
        return

    ret_val = task_scheduler.is_schedulable()
    print(ret_val)

def review_multiple_tasks(algorithm, folder_name):
    infeasible = 0
    not_schedulable_by_a = 0
    schedulable_by_a = 0
    task_files = parse_task_folder(folder_name)
    for task_file in task_files:
        full_taskset_address = folder_name + task_file
        value = review_task(algorithm, full_taskset_address)
        if value == 0 or value == 1:
            schedulable_by_a += 1
        if value == 2 or value == 3:
            not_schedulable_by_a += 1
    infeasible = not_schedulable_by_a + schedulable_by_a
    pie_plot([infeasible, not_schedulable_by_a, schedulable_by_a])

if __name__ == "__main__":
    #test_release_job()
    #test_rate_monotonic_schedule() #use argparse for passing in a task_set

    main()