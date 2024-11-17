import argparse
from pathlib import Path
from time import time

from nbformat.sign import algorithms

#from uniprocessor.feasibility.review import review_task_set, review_task_sets_in_parallel
from multiprocessor.feasibility.review import review_task_set
from multiprocessor.partitioner import FirstFit, NextFit, BestFit, WorstFit
from multiprocessor.scheduler import SchedulerType
from utils.parse import parse_task_file
from utils.metrics import calculate_success_rate
from utils.plotters import plot_primary_categories

def parse_arguments_uniprocessor():
    parser = argparse.ArgumentParser(description='Select a scheduling algorithm and specify a task set file.')
    parser.add_argument('algorithm', choices=['rm', 'dm', 'audsley', 'edf', 'rr'],
                        help='Scheduling algorithm to use: dm, audsley, edf, or rr.')
    parser.add_argument('task_set_location', type=str, help='Path to the task set file.')
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose mode for detailed output.")
    parser.add_argument('-f', '--force-simulation', action='store_true', help="Force simulation even if the utilization is less than 69%.")
    return parser.parse_args()

"""
$ python main.py <task_file> <m> -v global|partitioned|<k> [-w <w>] [-h ff|nf|bf|wf] [-s iu|du]
"""
def parse_arguments_multiprocessor():
    parser = argparse.ArgumentParser(description='Select a scheduling algorithm and specify a task set file.')

    parser.add_argument('task_set_location', type=str, help='Path to the task set file.')
    parser.add_argument('m', type=int, help='Number of processors.')

    # EDF(k) scheduling algorithm to use
    parser.add_argument(
        '-v',
        '--version',
        type=str,
        required=True,
        help="EDF scheduling algorithm to use: 'global', 'partitioned', or specify a numeric k for EDF(k).",
    )

    # Other optional arguments
    parser.add_argument('-w', type=int, help="Number of workers w to run the simulation.") # Number of cores by default
    parser.add_argument('-H', choices=['ff', 'nf', 'bf', 'wf'], help="Heuristic to use for partitioning.")
    parser.add_argument('-s', choices=['iu', 'du'], help="Sort tasks by increasing or decreasing utilization.")

    args = parser.parse_args()
    # Validate 'version' argument for global, partitioned, or numeric k
    if args.version not in ['global', 'partitioned']:
        try:
            args.k = int(args.version)  # Parse k as an integer if not global/partitioned
            if args.k <= 0:
                raise ValueError
        except ValueError:
            parser.error(
                "Invalid value for '-v/--version': must be 'global', 'partitioned', or a positive integer for EDF(k).")
    else:
        args.k = None  # No k-value if 'global' or 'partitioned' is selected

    if args.version == 'partitioned' or args.k is not None and args.H is None:
        parser.error("Heuristic [-H] must be specified for this algorithm.")
    return args

# def main_uniprocessor():
#     args = parse_arguments_uniprocessor()
#
#     start_time = time()
#
#     # Check if the address corresponds to a single dataset or if it is a folder containing many
#     path = Path(args.task_set_location)
#     if path.is_dir():
#         # Multiple task sets from a folder
#         print(f"Checking task sets in folder: {path}, for {args.algorithm}")
#         schedule_stats = review_task_sets_in_parallel(args.algorithm, args.task_set_location, verbose=args.verbose, force_simulation=args.force_simulation)
#         print(f"Time taken: {int(time() - start_time)} seconds")
#
#         plot_primary_categories(schedule_stats) # Plot only the primary categories
#         print(f"Success Rate: {calculate_success_rate(schedule_stats) * 100}%")
#     else:
#         # Single task set
#         task_set = parse_task_file(path)
#         ret_val = review_task_set(args.algorithm, task_set, verbose=args.verbose, force_simulation=args.force_simulation, task_file=path)
#         print(f"Time taken: {int(time() - start_time)} seconds")
#         print(f"Return value: {ret_val}")
#         exit(ret_val)

def main():
    args = parse_arguments_multiprocessor()

    start_time = time()

    # Check if the address corresponds to a single dataset or if it is a folder containing many
    path = Path(args.task_set_location)
    if path.is_file():
        # Single task set
        task_set = parse_task_file(path)

        # Parse the scheduling algorithm
        if args.version == 'global':
            algorithm = SchedulerType.GLOBAL_EDF
        elif args.version == 'partitioned':
            algorithm = SchedulerType.PARTITIONED_EDF
        else:
            algorithm = SchedulerType.EDF_K

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

        ret_val = review_task_set(algorithm, task_set, args.m, args.k, heuristic, True)
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


if __name__ == "__main__":
    main()