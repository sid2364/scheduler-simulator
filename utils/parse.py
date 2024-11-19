import argparse
import csv
from entities import Task, TaskSet

"""
Parse a CSV file with tasks and return a TaskSet object

We can change the implementation of this function to read from a different file format, if needed.
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
$ python main.py <task_file> <m> -v global|partitioned|<k> [-w <w>] [-H ff|nf|bf|wf] [-s iu|du]
"""
def parse_arguments_multiprocessor():
    parser = argparse.ArgumentParser(description='Select a scheduling algorithm and specify a task set file.')

    parser.add_argument('task_set_location', type=str, help='Path to the task set file.')
    parser.add_argument('m', type=int, help='Number of processors.')

    # Scheduling algorithm to use
    parser.add_argument(
        '-v', # Not verbose!
        '--version',
        type=str,
        required=True,
        help="EDF scheduling algorithm to use: 'global', 'partitioned', or specify a numeric k for EDF(k).",
    )

    # Other optional arguments
    parser.add_argument('-w', type=int, help="Number of workers w to run the simulation.") # Number of cores by default
    # Can't use -h because it's already used for help!
    parser.add_argument('-H', choices=['ff', 'nf', 'bf', 'wf'], help="Heuristic to use for partitioning.")
    parser.add_argument('-s', choices=['iu', 'du'], help="Sort tasks by increasing or decreasing utilization.")

    # Verbose, but can't use -v because it's already used for version
    parser.add_argument('-V', '--verbose', action='store_true', help="Enable verbose mode for detailed output.")
    # Force simulation
    parser.add_argument('-f', '--force-simulation', action='store_true', help="Force simulation if possible.")

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
