from helpers import pie_plot
import argparse
from pathlib import Path
import multiprocessing
import concurrent.futures

from algorithms import RateMonotonic, DeadlineMonotonic, Audsley, EarliestDeadlineFirst, RoundRobin
from parse_tasks import parse_task_file

def get_scheduler(algorithm, task_set, verbose):
    if algorithm == 'rm':
        return RateMonotonic(task_set, verbose)
    elif algorithm == 'dm':
        return DeadlineMonotonic(task_set, verbose)
    elif algorithm == 'audsley':
        return Audsley(task_set, verbose)
    elif algorithm == 'edf':
        return EarliestDeadlineFirst(task_set, verbose)
    elif algorithm == 'rr':
        return RoundRobin(task_set, verbose)
    else:
        print("Invalid algorithm selected.") # Won't happen because of argparse but why not
        return None

def review_task_set(algorithm, task_set, verbose=False):
    # print(f"Reviewing task set")

    if task_set is None:
        print("Task set could not be parsed.")
        return

    task_scheduler = get_scheduler(algorithm, task_set, verbose)

    ret_val = task_scheduler.is_schedulable()
    if ret_val == 0:
        print(f"The task set is schedulable and you had to simulate the execution.")
    elif ret_val == 1:
        print(f"The task set is schedulable and you took a shortcut.")
    elif ret_val == 2:
        print(f"The task set is not schedulable and you had to simulate the execution.")
    elif ret_val == 3:
        print(f"The task set is not schedulable and you took a shortcut.")
    elif ret_val == 5:
        print(f"Took too long to simulate the execution, exclude the task set.")
    return ret_val

def review_task_sets(algorithm, folder_name, verbose=False):
    infeasible = 0
    not_schedulable_by_a = 0
    schedulable_by_a = 0
    directory = Path(folder_name)

    # Recursively get all the task files in the directory
    task_files = [str(task_file) for task_file in directory.rglob("*") if task_file.is_file()]

    task_sets = []
    for task_file in task_files:
        task_sets.append(parse_task_file(task_file))

    # Now check if these task files are schedulable or not
    for task_set in task_sets:
        value = review_task_set(algorithm, task_set, verbose)
        if value is not None:
            if value == 0:
                schedulable_by_a += 1
            elif value == 1:
                schedulable_by_a += 1
            elif value == 2:
                not_schedulable_by_a += 1
            elif value == 3:
                not_schedulable_by_a += 1
            elif value == 5:
                infeasible += 1
    return {"infeasible": infeasible, "not_schedulable_by_a": not_schedulable_by_a, "schedulable_by_a": schedulable_by_a}

def review_task_sets_in_parallel(algorithm, folder_name, verbose=False, timeout=10):
    infeasible = 0
    not_schedulable_by_a = 0
    schedulable_by_a = 0
    directory = Path(folder_name)

    # Recursively get all the task files in the directory
    task_files = [str(task_file) for task_file in directory.rglob("*") if task_file.is_file()]

    task_sets = []
    for task_file in task_files:
        task_sets.append(parse_task_file(task_file))

    # Now check in parallel if these task files are schedulable or not
    with multiprocessing.Pool(processes=8) as pool:
        results = [(task_set, pool.apply_async(review_task_set, args=(algorithm, task_set, verbose))) for task_set in task_sets]
        pool.close()
        pool.join() # TODO check if this actually works!

    # Count the results
    total_files = len(task_sets)
    for task_set, async_result in results:
        try:
            value = async_result.get(timeout=timeout)
            # print(f"Value: {value}")
        except multiprocessing.TimeoutError:
            print(f"Timeout error occurred for set: {task_set}")
            value = 5
        if value is not None:
            if value == 0:
                schedulable_by_a += 1
            elif value == 1:
                schedulable_by_a += 1
            elif value == 2:
                not_schedulable_by_a += 1
            elif value == 3:
                not_schedulable_by_a += 1
            elif value == 5:
                total_files -= 1 #??? FIXME

    print(f"Total files considered: {total_files}")
    infeasible = 1

    return {"infeasible": infeasible, "not_schedulable_by_a": not_schedulable_by_a, "schedulable_by_a": schedulable_by_a}

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
    
    task_set_location = parser.parse_args().task_set_file
    algorithm = parser.parse_args().algorithm.lower()
    verbose = parser.parse_args().verbose

    # Check if the address corresponds to a single dataset or if it is a folder containing many
    path = Path(task_set_location)
    if path.is_dir():
        stats = review_task_sets_in_parallel(algorithm, task_set_location, verbose)
        #stats = review_task_sets(algorithm, task_set_location, verbose)
        pie_plot(stats)
    else:
        # Left in for debugging purposes
        task_set = parse_task_file(path)
        review_task_set(algorithm, task_set, verbose)

if __name__ == "__main__":
    main()