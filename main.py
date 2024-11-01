import argparse
from pathlib import Path
import multiprocessing
from time import time
import concurrent.futures

from algorithms import RateMonotonic, DeadlineMonotonic, Audsley, EarliestDeadlineFirst, RoundRobin
from parse_tasks import parse_task_file
from helpers import calculate_success_rate, Feasibility
from plotters import plot_primary_categories, plot_non_schedulable_breakdown_grouped

OPTIMAL_ALGORITHM = "edf"

"""
Return an instance of the scheduler based on the algorithm selected
"""
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


"""
Return an instance of EDF
"""
def get_optimal_scheduler(task_set, verbose, force_simulation):
    return get_scheduler(OPTIMAL_ALGORITHM, task_set, verbose, force_simulation)

"""
Check if a task set is schedulable by the optimal algorithm
"""
def check_schedulable_by_optimal(task_set, verbose=False, force_simulation=False):
    optimal_scheduler = get_optimal_scheduler(task_set, verbose, force_simulation)
    return optimal_scheduler.is_schedulable()

"""
Check if a task set is schedulable by the specified algorithm
"""
def review_task_set(algorithm, task_set, verbose=False, force_simulation=False, task_file=None):
    if task_set is None:
        print("Task set could not be parsed.")
        return

    task_scheduler = get_scheduler(algorithm, task_set, verbose, force_simulation)

    scheduler_return_val = task_scheduler.is_schedulable()
    if verbose:
        if scheduler_return_val == 0:
            print(f"The task set {task_file} is schedulable and you had to simulate the execution.")
        elif scheduler_return_val == 1:
            print(f"The task set {task_file} is schedulable and you took a shortcut.")
        elif scheduler_return_val == 2:
            print(f"The task set {task_file} is not schedulable and you had to simulate the execution.")
        elif scheduler_return_val == 3:
            print(f"The task set {task_file} is not schedulable and you took a shortcut.")
        elif scheduler_return_val == 4:
            print(f"Took too long to simulate the execution for {task_file}, exclude the task set.")
    return scheduler_return_val

"""
Evaluate multiple task sets in a folder in parallel!
"""
def review_task_sets_in_parallel(algorithm, folder_name, verbose=False, timeout=10, force_simulation=False):
    infeasible = 0
    not_schedulable_by_a = 0
    schedulable_by_a = 0

    schedulable_by_a_shortcut = 0
    schedulable_by_a_simulated = 0
    not_schedulable_by_a_shortcut = 0
    not_schedulable_by_a_simulated = 0
    timed_out = 0
    schedulable_by_optimal_but_not_by_a = 0

    directory = Path(folder_name)

    # Recursively get all the task files in the directory
    task_files = [str(task_file) for task_file in directory.rglob("*") if task_file.is_file()]

    tasks = []
    for task_file in task_files:
        tasks.append((parse_task_file(task_file), task_file)) # (TaskSet, Path)

    # Now check in parallel if these task files are schedulable or not
    with multiprocessing.Pool(processes=8) as pool:
        results = [(task_set[0], # TaskSet
                    task_set[1], # Path
                    pool.apply_async(review_task_set, args=(algorithm, task_set[0], verbose, force_simulation, task_set[1]))) # Scheduler result
                   for task_set in tasks]
        pool.close()
        pool.join()

    # Count the results
    total_files = len(tasks)
    for task_set, task_file, async_result in results:
        try:
            value = async_result.get(timeout=timeout)
        except multiprocessing.TimeoutError:
            print(f"Timeout error occurred for set: {task_file}")
            value = 4
        if value is not None:
            if value == 0:
                schedulable_by_a += 1
                schedulable_by_a_simulated += 1
            elif value == 1:
                schedulable_by_a += 1
                schedulable_by_a_shortcut += 1
            elif value == 2:
                not_schedulable_by_a += 1
                not_schedulable_by_a_simulated += 1
            elif value == 3:
                not_schedulable_by_a += 1
                not_schedulable_by_a_shortcut += 1
            elif value == 4:
                timed_out += 1
                total_files -= 1

            if value == 2 or value == 3:
                feasible_if_scheduler_optimal = check_schedulable_by_optimal(task_set, verbose)
                if feasible_if_scheduler_optimal == 1:
                    schedulable_by_optimal_but_not_by_a += 1
                else:
                    infeasible += 1

    print(f"Total files considered: {total_files} out of {len(task_files)}")

    return {
        Feasibility.FEASIBLE_SHORTCUT: schedulable_by_a_shortcut,
        Feasibility.FEASIBLE_SIMULATION: schedulable_by_a_simulated,
        Feasibility.NOT_SCHEDULABLE_BY_A_SHORTCUT: not_schedulable_by_a_shortcut,
        Feasibility.NOT_SCHEDULABLE_BY_A_SIMULATION: not_schedulable_by_a_simulated,
        Feasibility.TIMED_OUT: timed_out,
        Feasibility.SCHEDULABLE_BY_OPTIMAL_BUT_NOT_BY_A: schedulable_by_optimal_but_not_by_a,
        Feasibility.INFEASIBLE: infeasible
    }


def parse_arguments():
    parser = argparse.ArgumentParser(description='Select a scheduling algorithm and specify a task set file.')
    parser.add_argument('algorithm', choices=['rm', 'dm', 'audsley', 'edf', 'rr'],
                        help='Scheduling algorithm to use: dm, audsley, edf, or rr.')
    parser.add_argument('task_set_location', type=str, help='Path to the task set file.')
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose mode for detailed output.")
    parser.add_argument('-f', '--force-simulation', action='store_true', help="Force simulation even if the utilization is less than 69%.")
    return parser.parse_args()

def main():
    args = parse_arguments()

    start_time = time()

    # Check if the address corresponds to a single dataset or if it is a folder containing many
    path = Path(args.task_set_location)
    if path.is_dir():
        # Multiple task sets from a folder
        schedule_stats = review_task_sets_in_parallel(args.algorithm, args.task_set_location, verbose=args.verbose, force_simulation=args.force_simulation)
        print(f"Time taken: {int(time() - start_time)} seconds")

        plot_primary_categories(schedule_stats) # Plot only the primary categories
        plot_non_schedulable_breakdown_grouped(schedule_stats, args.algorithm.upper()) # Plot the non-schedulable categories with optimal
        print(f"Success Rate: {calculate_success_rate(schedule_stats) * 100}%")
    else:
        # Single task set
        task_set = parse_task_file(path)
        ret_val = review_task_set(args.algorithm, task_set, verbose=args.verbose, force_simulation=args.force_simulation, task_file=path)
        print(f"Time taken: {int(time() - start_time)} seconds")
        print(f"Return value: {ret_val}")
        exit(ret_val)

if __name__ == "__main__":
    main()