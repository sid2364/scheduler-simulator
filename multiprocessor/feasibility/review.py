from sympy.series.limits import heuristics

from entities import TaskSet
from multiprocessor.partitioner import BestFit, PartitionHeuristic
from multiprocessor.scheduler import EDFk, SchedulerType, PartitionedEDF, GlobalEDF


def review_task_set(algorithm: SchedulerType,
                    task_set: TaskSet,
                    m: int,
                    k: int,
                    heuristic: PartitionHeuristic,
                    verbose=False,
                    force_simulation=False,
                    task_file=None) -> int:
    if task_set is None:
        print("Task set could not be parsed.")
        return 5

    if algorithm == SchedulerType.GLOBAL_EDF:
        edf_scheduler = GlobalEDF(task_set, m, verbose, force_simulation)
    elif algorithm == SchedulerType.PARTITIONED_EDF:
        edf_scheduler = PartitionedEDF(task_set, m, heuristic, verbose, force_simulation)
    elif algorithm == SchedulerType.EDF_K:
        edf_scheduler = EDFk(task_set, k, m, heuristic, verbose, force_simulation)
    else:
        raise ValueError("Invalid algorithm type")

    print(f"Scheduler type: {edf_scheduler.scheduler_type} {edf_scheduler}")

    scheduler_return_val = edf_scheduler.simulate_taskset() # call is_feasible() method instead
    return scheduler_return_val
