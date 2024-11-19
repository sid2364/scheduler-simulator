import multiprocessing
from pathlib import Path

from entities import TaskSet
from multiprocessor.partitioner import PartitionHeuristic
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
                          heuristic: PartitionHeuristic,
                          verbose=False,
                          force_simulation=False,
                          task_file=None) -> int:
    if task_set is None:
        print("Task set could not be parsed.")
        return 4

    edf_task_scheduler = get_multi_scheduler(algorithm, task_set, m, k, heuristic, verbose, force_simulation)

    if verbose:
        print(f"Scheduler: {edf_task_scheduler}")
    print(f"Checking task set: {task_file}")

    scheduler_return_val = edf_task_scheduler.is_feasible()
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
Evaluate multiple task sets in a folder in parallel for multiprocessor systems!
"""
def review_task_sets_in_parallel_multi(algorithm: MultiprocessorSchedulerType,
                                       folder_name: str,
                                       num_processors: int,
                                       num_clusters: int,
                                       heuristic: PartitionHeuristic,
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

    # Run the tasks in parallel and get the results
    with multiprocessing.Pool(processes=number_of_workers) as pool:
        results = [(task_set[0], # TaskSet
                    task_set[1], # Path
                    pool.apply_async(review_task_set_multi, args=(algorithm, task_set[0], num_processors, num_clusters, heuristic, verbose, force_simulation, task_set[1])))  # Scheduler result
                   for task_set in tasks]
        pool.close()
        pool.join()

    total_files = len(tasks)
    for task_set, task_file, async_result in results:
        try:
            scheduler_return_val = async_result.get(timeout=timeout)
        except multiprocessing.TimeoutError:
            print(f"Timeout for task set: {task_file}")
            scheduler_return_val = 4

        if scheduler_return_val is not None:
            if scheduler_return_val == 0:
                schedulable_simulation += 1
            elif scheduler_return_val == 1:
                schedulable_no_simulation += 1
            elif scheduler_return_val == 2:
                not_schedulable_simulation += 1
            elif scheduler_return_val == 3:
                not_schedulable_no_simulation += 1
            elif scheduler_return_val == 4:
                cannot_tell += 1

    print(f"Total files considered: {total_files}")

    return {
        MultiprocessorFeasibility.SCHEDULABLE_SIMULATION: schedulable_simulation,
        MultiprocessorFeasibility.SCHEDULABLE_SHORTCUT: schedulable_no_simulation,
        MultiprocessorFeasibility.NOT_SCHEDULABLE_SIMULATION: not_schedulable_simulation,
        MultiprocessorFeasibility.NOT_SCHEDULABLE_SHORTCUT: not_schedulable_no_simulation,
        MultiprocessorFeasibility.CANNOT_TELL: cannot_tell
    }