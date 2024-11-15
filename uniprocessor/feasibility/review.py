from uniprocessor.algorithms import get_uni_scheduler, get_optimal_scheduler
from entities import TaskSet

from pathlib import Path
import multiprocessing

from utils.metrics import Feasibility
from utils.parse import parse_task_file

NUMBER_OF_PARALLEL_PROCESSES = 8

"""
Check if a task set is schedulable by the optimal algorithm
"""
def check_schedulable_by_optimal(task_set: TaskSet, verbose=False, force_simulation=False) -> bool:
    optimal_scheduler = get_optimal_scheduler(task_set, verbose, force_simulation)
    return optimal_scheduler.is_feasible()

"""
Check if a task set is schedulable by the specified algorithm
"""
def review_task_set(algorithm: str, task_set: TaskSet, verbose=False, force_simulation=False, task_file=None) -> int:
    if task_set is None:
        print("Task set could not be parsed.")
        return 5

    task_scheduler = get_uni_scheduler(algorithm, task_set, verbose, force_simulation)

    # print(f"Checking task set: {task_file}")
    scheduler_return_val = task_scheduler.is_feasible()
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
def review_task_sets_in_parallel(algorithm: str, folder_name: str, verbose=False, timeout=10, force_simulation=False):
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
    with multiprocessing.Pool(processes=NUMBER_OF_PARALLEL_PROCESSES) as pool:
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

