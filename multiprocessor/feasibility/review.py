from sympy.series.limits import heuristics

from entities import TaskSet
from multiprocessor.partitioner import BestFit
from multiprocessor.scheduler import EDFk


def review_task_set(algorithm: str, task_set: TaskSet, m: int, k: int, verbose=False, force_simulation=False, task_file=None) -> int:
    if task_set is None:
        print("Task set could not be parsed.")
        return 5

    heuristic = BestFit()
    edf_scheduler = EDFk(task_set, k, m, heuristic, verbose, force_simulation)

    scheduler_return_val = edf_scheduler.simulate_taskset() # call is_feasible() method instead
    return scheduler_return_val
