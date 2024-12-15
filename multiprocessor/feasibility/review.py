import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from hashlib import algorithms_available
from pathlib import Path

from matplotlib import pyplot as plt

from entities import TaskSet
from multiprocessor.partitioner import PartitionHeuristic, BestFit, FirstFit, NextFit, WorstFit
from multiprocessor.scheduler import MultiprocessorSchedulerType, get_multi_scheduler
from utils.metrics import MultiprocessorFeasibility
from utils.parse import parse_task_file

"""
Check if a task set is schedulable by the specified algorithm for multiprocessor systems
"""
def review_task_set_multi(algorithm: MultiprocessorSchedulerType,
                          task_set: TaskSet,
                          m: int,
                          k: int,
                          heuristic: PartitionHeuristic = BestFit(),
                          num_workers: int = 8,
                          verbose=False,
                          force_simulation=False,
                          task_file=None) -> int:
    if task_set is None:
        print("Task set could not be parsed.")
        return 4

    edf_task_scheduler = get_multi_scheduler(algorithm, task_set, m, k, heuristic, num_workers, verbose, force_simulation)

    if verbose:
        print(f"Scheduler: {edf_task_scheduler}")
        print(f"Checking task set: {task_file}")

    scheduler_return_val = edf_task_scheduler.is_feasible()
    # verbose = True
    if verbose:
        if scheduler_return_val == 0:
            print(f"The task set {task_file} is schedulable and you had to simulate the execution.")
        elif scheduler_return_val == 1:
            print(f"The task set {task_file} is schedulable because some sufficient condition is met.")
        elif scheduler_return_val == 2:
            print(f"The task set {task_file} is not schedulable and you had to simulate the execution.")
        elif scheduler_return_val == 3:
            print(f"The task set {task_file} is not schedulable because a necessary condition does not hold.")
        elif scheduler_return_val == 4:
            print(f"You can not tell if the task set {task_file} is schedulable or not.")

    return scheduler_return_val

"""
Check if a heuristic can partition the task set
"""
def review_heuristic_multi(algorithm: MultiprocessorSchedulerType,
                          task_set: TaskSet,
                          m: int,
                          k: int,
                          heuristic: PartitionHeuristic = BestFit(),
                          num_workers: int = 8,
                          verbose=False,
                          force_simulation=False,
                          task_file=None) -> int:
    if task_set is None:
        print("Task set could not be parsed.")
        return 4

    edf_task_scheduler = get_multi_scheduler(algorithm, task_set, m, k, heuristic, num_workers, verbose, force_simulation)

    partition_possible = edf_task_scheduler.is_partitioned
    print(f"Partition possible: {partition_possible}")

    return partition_possible

"""
Evaluate multiple task sets in a folder in parallel for multiprocessor systems!
"""
def review_task_sets_in_parallel_multi(algorithm: MultiprocessorSchedulerType,
                                       folder_name: str,
                                       num_processors: int,
                                       num_clusters: int = 1,
                                       heuristic: PartitionHeuristic = BestFit(),
                                       number_of_workers: int = 8,
                                       verbose=False,
                                       timeout=10,
                                       force_simulation=False):
    schedulable_simulation = 0
    schedulable_no_simulation = 0
    not_schedulable_simulation = 0
    not_schedulable_no_simulation = 0
    cannot_tell = 0

    directory = Path(folder_name)

    # Recursively get all the files in the directory (though we just have a single level dir)
    task_files = [str(task_file) for task_file in directory.rglob("*") if task_file.is_file()]

    tasks = []
    for task_file in task_files:
        tasks.append((parse_task_file(task_file), task_file)) # (TaskSet, Path)

    # Calculate how many workers can go towards the algorithms and how many towards the task sets
    # This is because both the algorithms and the task sets can be parallelized, but
    # it doesn't make sense to give the algorithms more workers than the number of processors in all cases

    # NOTE: This logic is not used because we realised parallelising cluster scheduling is not useful
    # as the overhead of creating new processes is too high for the small amount of work done in each process

    # if algorithm == MultiprocessorSchedulerType.PARTITIONED_EDF:
    #     # We need at least m workers for the algorithms
    #     algorithm_workers = min(number_of_workers, num_processors)
    #     taskset_workers = number_of_workers - algorithm_workers
    # elif algorithm == MultiprocessorSchedulerType.GLOBAL_EDF:
    #     # We can't parallelize the algorithm, so just one for the algorithm and the rest for the task sets
    #     algorithm_workers = 1
    #     taskset_workers = number_of_workers - algorithm_workers
    # else:
    #     # At least k workers for the algorithms, and rest for the task sets
    #     algorithm_workers = max(number_of_workers, num_clusters)
    #     taskset_workers = number_of_workers - algorithm_workers

    # print(f"Number of workers for the task sets: {taskset_workers}")
    # print(f"Number of workers for the algorithms: {algorithm_workers}")

    with multiprocessing.Pool(processes=number_of_workers) as pool:
        results = [(task_set[0], # TaskSet
                    task_set[1], # Path
                    pool.apply_async(review_task_set_multi, args=(algorithm, task_set[0], num_processors, num_clusters, heuristic, number_of_workers, verbose, force_simulation, task_set[1])))  # Scheduler result
                    for task_set in tasks]
        pool.close()
        pool.join()

    for task_set, task_file, async_result in results:
        try:
            value = async_result.get(timeout=timeout)
        except multiprocessing.TimeoutError:
            print(f"Timeout error occurred for set: {task_file}")
            value = 4
        if value is not None:
            if value == 0:
                schedulable_simulation += 1
            elif value == 1:
                schedulable_no_simulation += 1
            elif value == 2:
                not_schedulable_simulation += 1
            elif value == 3:
                not_schedulable_no_simulation += 1
            elif value == 4:
                cannot_tell += 1

    total_files = len(tasks)
    print(f"Total files considered: {total_files}")

    return {
        MultiprocessorFeasibility.SCHEDULABLE_SIMULATION: schedulable_simulation,
        MultiprocessorFeasibility.SCHEDULABLE_SHORTCUT: schedulable_no_simulation,
        MultiprocessorFeasibility.NOT_SCHEDULABLE_SIMULATION: not_schedulable_simulation,
        MultiprocessorFeasibility.NOT_SCHEDULABLE_SHORTCUT: not_schedulable_no_simulation,
        MultiprocessorFeasibility.CANNOT_TELL: cannot_tell,
    }

def review_heuristics_multi(folder_name: str,
                            num_processors: int = 8,
                            num_clusters: int = 3,
                            verbose=False,
                            timeout=10,
                            force_simulation=False):
    # Counters for successes and failures for each heuristic
    results = {
        "FirstFit": {"success": 0, "failure": 0},
        "NextFit": {"success": 0, "failure": 0},
        "BestFit": {"success": 0, "failure": 0},
        "WorstFit": {"success": 0, "failure": 0},
    }

    directory = Path(folder_name)

    # Recursively get all task files
    task_files = [str(task_file) for task_file in directory.rglob("*") if task_file.is_file()]

    tasks = [(parse_task_file(task_file), task_file) for task_file in task_files]  # (TaskSet, Path)

    heuristics = [BestFit(), FirstFit(), NextFit(), WorstFit()]
    heuristic_names = ["BestFit", "FirstFit", "NextFit", "WorstFit"]

    for heuristic, heuristic_name in zip(heuristics, heuristic_names):
        # Partitioned EDF only
        algorithm = MultiprocessorSchedulerType.EDF_K
        # Evaluate each heuristic for all task sets
        for task_set, task_file in tasks:
            success = review_heuristic_multi(
                algorithm, task_set, num_processors, num_clusters, heuristic, verbose, force_simulation
            )

            # Update success or failure counts
            if success:
                results[heuristic_name]["success"] += 1
            else:
                results[heuristic_name]["failure"] += 1

    total_files = len(tasks)
    print(f"Total files considered: {total_files}")
    for heuristic_name, counts in results.items():
        print(f"{heuristic_name}: Success = {counts['success']}, Failure = {counts['failure']}")