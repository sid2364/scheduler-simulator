from pathlib import Path
from time import time

from multiprocessor.feasibility.review import review_task_set_multi, review_task_sets_in_parallel_multi
from multiprocessor.partitioner import FirstFit, NextFit, BestFit, WorstFit
from multiprocessor.scheduler import MultiprocessorSchedulerType
from utils.metrics import MultiprocessorFeasibility
from utils.parse import parse_arguments_multiprocessor, parse_task_file

"""
Main function for multiprocessor systems
"""
def execute_multiprocessor_system_experiments():
    args = parse_arguments_multiprocessor()
    # Parse the scheduling algorithm
    if args.version == 'global':
        algorithm = MultiprocessorSchedulerType.GLOBAL_EDF
    elif args.version == 'partitioned':
        algorithm = MultiprocessorSchedulerType.PARTITIONED_EDF
    else:
        algorithm = MultiprocessorSchedulerType.EDF_K

    # Parse the sorting order for the tasks in the heuristic
    is_decreasing_utilisation = True
    if args.s is not None:
        if args.s == 'iu':
            is_decreasing_utilisation = False
        elif args.s == 'du':
            is_decreasing_utilisation = True

    # Parse the heuristic
    heuristic = None
    if args.H is not None:
        if args.H == 'ff':
            heuristic = FirstFit(is_decreasing_utilisation)
        elif args.H == 'nf':
            heuristic = NextFit(is_decreasing_utilisation)
        elif args.H == 'bf':
            heuristic = BestFit(is_decreasing_utilisation)
        elif args.H == 'wf':
            heuristic = WorstFit(is_decreasing_utilisation)

    workers = args.w if args.w is not None else 8

    start_time = time()

    # Check if the address corresponds to a single dataset or if it is a folder containing many
    path = Path(args.task_set_location)
    if path.is_dir():
        # Multiple task sets from a folder
        print(f"Checking task sets in folder: {path}, for {algorithm}")
        schedule_stats = review_task_sets_in_parallel_multi(algorithm=algorithm,
                                                            folder_name=args.task_set_location,
                                                            num_processors=args.m,
                                                            num_clusters=args.k,
                                                            heuristic=heuristic,
                                                            number_of_workers=workers,
                                                            verbose=args.verbose,
                                                            force_simulation=args.force_simulation)
        print(f"Time taken: {int(time() - start_time)} seconds")

        # Just print the results for now
        for key, value in schedule_stats.items():
            print(f"{MultiprocessorFeasibility.get_status_string(key)}: {value}")

    else:
        # Single task set
        task_set = parse_task_file(path)

        ret_val = review_task_set_multi(algorithm, task_set, args.m, args.k, heuristic, args.verbose, args.force_simulation, path)
        print(f"Time taken: {int(time() - start_time)} seconds")
        print(f"Return value: {ret_val}")

        if ret_val == 0:
            print(f"The task set {path} is schedulable and you had to simulate the execution.")
        elif ret_val == 1:
            print(f"The task set {path} is schedulable because some sufficient condition is met.")
        elif ret_val == 2:
            print(f"The task set {path} is not schedulable and you had to simulate the execution.")
        elif ret_val == 3:
            print(f"The task set {path} is not schedulable because a necessary condition does not hold.")
        elif ret_val == 4:
            print(f"Took too long to simulate the execution for {path}, exclude the task set.")
        exit(ret_val)
