import argparse
from pathlib import Path
import multiprocessing
from time import time
import concurrent.futures

from helpers import pie_plot_categories, Schedulable


from algorithms import RateMonotonic, DeadlineMonotonic, Audsley, EarliestDeadlineFirst, RoundRobin
from parse_tasks import parse_task_file

def get_scheduler(algorithm, task_set, verbose, force_simulation):
    if algorithm == 'rm':
        return RateMonotonic(task_set, verbose, force_simulation)
    elif algorithm == 'dm':
        return DeadlineMonotonic(task_set, verbose, force_simulation)
    elif algorithm == 'audsley':
        return Audsley(task_set, verbose, force_simulation)
    elif algorithm == 'edf':
        return EarliestDeadlineFirst(task_set, verbose, force_simulation)
    elif algorithm == 'rr':
        return RoundRobin(task_set, verbose, force_simulation)
    else:
        print("Invalid algorithm selected.") # Won't happen because of argparse but why not
        return None

def review_task_set(algorithm, task_set, verbose=False, force_simulation=False, task_file=None):
    if task_set is None:
        print("Task set could not be parsed.")
        return

    task_scheduler = get_scheduler(algorithm, task_set, verbose, force_simulation)

    ret_val = task_scheduler.is_schedulable()
    if verbose:
        if ret_val == 0:
            print(f"The task set {task_file} is schedulable and you had to simulate the execution.")
        elif ret_val == 1:
            print(f"The task set {task_file} is schedulable and you took a shortcut.")
        elif ret_val == 2:
            print(f"The task set {task_file} is not schedulable and you had to simulate the execution.")
        elif ret_val == 3:
            print(f"The task set {task_file} is not schedulable and you took a shortcut.")
        elif ret_val == 5:
            print(f"Took too long to simulate the execution for {task_file}, exclude the task set.")
    return ret_val

"""
Unused function, does the same as review_task_sets_in_parallel but without multiprocessing
"""
def review_task_sets(algorithm, folder_name, verbose=False):
    infeasible = 0
    not_schedulable_by_a = 0
    schedulable_by_a = 0
    timed_out = 0
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
                # TODO: fix this
            elif value == 3:
                not_schedulable_by_a += 1
            elif value == 5: # Tried to schedule but couldn't
                infeasible += 1
                timed_out += 1
    return {
        Schedulable.INFEASIBLE: infeasible,
        Schedulable.NOT_SCHEDULABLE_BY_A: not_schedulable_by_a,
        Schedulable.SCHEDULABLE: schedulable_by_a
    }

def review_task_sets_in_parallel(algorithm, folder_name, verbose=False, timeout=10, force_simulation=False):
    infeasible = 0
    not_schedulable_by_a = 0
    schedulable_by_a = 0
    directory = Path(folder_name)

    # Recursively get all the task files in the directory
    task_files = [str(task_file) for task_file in directory.rglob("*") if task_file.is_file()]

    task_sets = []
    for task_file in task_files:
        task_sets.append((parse_task_file(task_file), task_file))

    # Now check in parallel if these task files are schedulable or not
    with multiprocessing.Pool(processes=8) as pool:
        results = [(task_set[1],
                    pool.apply_async(review_task_set, args=(algorithm, task_set[0], verbose, force_simulation, task_set[1])))
                   for task_set in task_sets]
        pool.close()
        pool.join()

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
                infeasible += 1
            elif value == 3:
                infeasible += 1
            elif value == 5:
                total_files -= 1
                # FIXME: Do something else here! Check if the task set is schedulable by EDF or something

    print(f"Total files considered: {total_files} out of {len(task_files)}")

    return {
        Schedulable.INFEASIBLE: infeasible,
        Schedulable.NOT_SCHEDULABLE_BY_A: not_schedulable_by_a,
        Schedulable.SCHEDULABLE: schedulable_by_a
    }

def main():
    # Set up command line argument parser
    parser = argparse.ArgumentParser(description='Select a scheduling algorithm and specify a task set file.')

    # Add the scheduling algorithm argument (mandatory)
    parser.add_argument('algorithm', choices=['rm', 'dm', 'audsley', 'edf', 'rr'],
                        help='Scheduling algorithm to use: dm, audsley, edf, or rr.')

    # Add the task set file argument (mandatory)
    parser.add_argument('task_set_file', type=str,
                        help='Path to the task set file.')

    # Optional flag for verbose mode
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Enable verbose mode for detailed output.")

    # Optional flag to force simulation
    parser.add_argument('-f', '--force-simulation', action='store_true',
                        help="Force simulation even if the utilization is less than 69%.")

    task_set_location = parser.parse_args().task_set_file
    algorithm = parser.parse_args().algorithm.lower()
    verbose = parser.parse_args().verbose
    force_simulation = parser.parse_args().force_simulation


    start_time = time()
    # Check if the address corresponds to a single dataset or if it is a folder containing many
    path = Path(task_set_location)
    if path.is_dir():
        schedule_stats = review_task_sets_in_parallel(algorithm, task_set_location, verbose=verbose, force_simulation=force_simulation)
        print(f"Time taken: {int(time() - start_time)} seconds")
        # stats = review_task_sets(algorithm, task_set_location, verbose)

        pie_plot_categories(schedule_stats)
    else:
        # Left in for debugging purposes
        task_set = parse_task_file(path)
        review_task_set(algorithm, task_set, verbose=verbose, force_simulation=force_simulation, task_file=path)
        print(f"Time taken: {int(time() - start_time)} seconds")

if __name__ == "__main__":
    main()