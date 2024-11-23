import argparse
import csv
from entities import Task, TaskSet

"""
Parse a CSV file with tasks and return a TaskSet object
"""
def parse_task_file(file_path):
    tasks = []
    try:
        with open(file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) == 4:
                    offset = int(row[0])
                    computation_time = int(row[1])
                    deadline = int(row[2])
                    period = int(row[3])
                    task = Task(offset, computation_time, deadline, period)
                    tasks.append(task)
        task_set = TaskSet(tasks)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except PermissionError:
        print(f"Permission denied: {file_path}")
        return None
    except csv.Error as e:
        print(f"Error reading CSV file: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    return task_set


"""
$ python main.py <task_file> <algorithm> [-v] [-f]
"""
def parse_arguments_uniprocessor():
    parser = argparse.ArgumentParser(description='Select a scheduling algorithm and specify a task set file.')
    parser.add_argument('algorithm', choices=['rm', 'dm', 'audsley', 'edf', 'rr'],
                        help='Scheduling algorithm to use: dm, audsley, edf, or rr.')
    parser.add_argument('task_set_location', type=str, help='Path to the task set file.')
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose mode for detailed output.")
    parser.add_argument('-f', '--force-simulation', action='store_true', help="Force simulation even if the utilization is less than 69%.")
    return parser.parse_args()

"""
$ python main.py <task_file> <m> global|partitioned|<k> [-v|--verbose] [-w <w>] [-H ff|nf|bf|wf] [-s iu|du]
"""
def parse_arguments_multiprocessor():
    class CustomArgumentParser(argparse.ArgumentParser):
        def format_usage(self):
            usage = f"usage: {self.prog} task_set_location <m> global|partitioned|<k> [-v|--verbose] [-w W] [-H {{ff,nf,bf,wf}}] [-s {{iu,du}}] [-f]\n"
            return usage

    parser = CustomArgumentParser(description='Select a multiprocessor scheduling algorithm '
                                                 'and specify a task set file.')

    parser.add_argument('task_set_location', type=str, help='Path to the task set file.')
    parser.add_argument('m', type=int, help='Number of processors.')

    # Scheduling algorithm to use
    parser.add_argument(
        'algorithm',
        type=str,
        help="EDF scheduling algorithm to use: 'global', 'partitioned', or specify a numeric k for EDF(k).",
    )

    # Verbose
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose mode for detailed output.")

    # Other optional arguments
    parser.add_argument('-w', '--workers', type=int, help="Number of workers w to run the simulation.") # Number of cores by default

    # Can't use -h because it's already used for help!
    parser.add_argument('-H', '--heuristic', choices=['ff', 'nf', 'bf', 'wf'], help="Heuristic to use for partitioning.")
    parser.add_argument('-s', '--sorting', choices=['iu', 'du'], help="Sort tasks by increasing or decreasing utilization.")

    # Force simulation
    parser.add_argument('-f', '--force-simulation', action='store_true', help="Force simulation if possible.")

    args = parser.parse_args()
    # Validate 'algorithm' argument for global, partitioned, or numeric k
    if args.algorithm not in ['global', 'partitioned']:
        try:
            args.k = int(args.algorithm)  # Parse k as an integer if not global/partitioned
            if args.k <= 0:
                raise ValueError
        except ValueError:
            parser.error(
                "Invalid value for 'algorithm': must be 'global', 'partitioned', or a positive integer for EDF(k)."
            )
    else:
        args.k = None  # No k-value if 'global' or 'partitioned' is selected

    # Validate heuristic argument, it throws AttributeError if not specified
    try:
        if args.algorithm == 'partitioned' or args.k is not None and args.heuristic is None:
            parser.error("Heuristic [-H] must be specified for this algorithm.")
    except AttributeError:
        parser.error("Heuristic [-H] must be specified for this algorithm. 2")
    return args
