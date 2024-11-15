import argparse
from pathlib import Path
from time import time

from uniprocessor.feasibility.review import review_task_set, review_task_sets_in_parallel
from utils.parse import parse_task_file
from utils.metrics import calculate_success_rate
from utils.plotters import plot_primary_categories

def parse_arguments():
    parser = argparse.ArgumentParser(description='Select a scheduling algorithm and specify a task set file.')
    parser.add_argument('algorithm', choices=['rm', 'dm', 'audsley', 'edf', 'rr'],
                        help='Scheduling algorithm to use: dm, audsley, edf, or rr.')
    parser.add_argument('task_set_location', type=str, help='Path to the task set file.')
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose mode for detailed output.")
    parser.add_argument('-f', '--force-simulation', action='store_true', help="Force simulation even if the utilization is less than 69%.")
    return parser.parse_args()

def main():
    args = parse_arguments()

    start_time = time()

    # Check if the address corresponds to a single dataset or if it is a folder containing many
    path = Path(args.task_set_location)
    if path.is_dir():
        # Multiple task sets from a folder
        print(f"Checking task sets in folder: {path}, for {args.algorithm}")
        schedule_stats = review_task_sets_in_parallel(args.algorithm, args.task_set_location, verbose=args.verbose, force_simulation=args.force_simulation)
        print(f"Time taken: {int(time() - start_time)} seconds")

        plot_primary_categories(schedule_stats) # Plot only the primary categories
        print(f"Success Rate: {calculate_success_rate(schedule_stats) * 100}%")
    else:
        # Single task set
        task_set = parse_task_file(path)
        ret_val = review_task_set(args.algorithm, task_set, verbose=args.verbose, force_simulation=args.force_simulation, task_file=path)
        print(f"Time taken: {int(time() - start_time)} seconds")
        print(f"Return value: {ret_val}")
        exit(ret_val)

if __name__ == "__main__":
    main()