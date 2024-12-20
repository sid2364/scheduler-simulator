from pathlib import Path
from tabnanny import verbose
from time import time

from nbformat.sign import algorithms

from multiprocessor.feasibility.review import review_task_set_multi, review_task_sets_in_parallel_multi
from multiprocessor.partitioner import FirstFit, NextFit, BestFit, WorstFit
from multiprocessor.scheduler import MultiprocessorSchedulerType
from utils.metrics import MultiprocessorFeasibility
from utils.parse import parse_arguments_multiprocessor, parse_task_file


NUMBER_OF_PARALLEL_PROCESSES = 8

"""
Main function for multiprocessor systems
"""
def execute_multiprocessor_system_experiments():
    args = parse_arguments_multiprocessor()
    # Parse the scheduling algorithm
    if args.algorithm == 'global':
        algorithm = MultiprocessorSchedulerType.GLOBAL_EDF
    elif args.algorithm == 'partitioned':
        algorithm = MultiprocessorSchedulerType.PARTITIONED_EDF
    else:
        algorithm = MultiprocessorSchedulerType.EDF_K

    # Parse the sorting order for the tasks in the heuristic
    is_decreasing_utilisation = True
    if args.sorting is not None:
        if args.sorting == 'iu':
            is_decreasing_utilisation = False
        elif args.sorting == 'du':
            is_decreasing_utilisation = True

    # Parse the heuristic
    heuristic = None
    if args.heuristic is not None:
        if args.heuristic == 'ff':
            heuristic = FirstFit(is_decreasing_utilisation, verbose=args.verbose)
        elif args.heuristic == 'nf':
            heuristic = NextFit(is_decreasing_utilisation, verbose=args.verbose)
        elif args.heuristic == 'bf':
            heuristic = BestFit(is_decreasing_utilisation, verbose=args.verbose)
        elif args.heuristic == 'wf':
            heuristic = WorstFit(is_decreasing_utilisation, verbose=args.verbose)

    workers = args.workers if args.workers is not None else NUMBER_OF_PARALLEL_PROCESSES

    start_time = time()

    # Check if the address corresponds to a single dataset or if it is a folder containing many
    path = Path(args.task_set_location)
    if path.is_dir():
        # Multiple task sets from a folder
        # print(f"Checking task sets in folder: {path}, for {algorithm}")
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

        ret_val = review_task_set_multi(algorithm, task_set, args.m, args.k, heuristic, workers, args.verbose, args.force_simulation, path)
        print(f"Time taken: {int(time() - start_time)} seconds")
        print(f"Return value: {ret_val}")

        if verbose:
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
