from pathlib import Path
from time import time

from uniprocessor.feasibility.review import review_task_sets_in_parallel_uni, review_task_set_uni
from utils.metrics import calculate_success_rate
from utils.parse import parse_arguments_uniprocessor, parse_task_file
from utils.plotters import plot_primary_categories

"""
Main function for uniprocessor systems
"""
def execute_uniprocessor_system_experiments():
    args = parse_arguments_uniprocessor()

    start_time = time()

    # Check if the address corresponds to a single dataset or if it is a folder containing many
    path = Path(args.task_set_location)
    if path.is_dir():
        # Multiple task sets from a folder
        print(f"Checking task sets in folder: {path}, for {args.algorithm}")
        schedule_stats = review_task_sets_in_parallel_uni(args.algorithm, args.task_set_location, verbose=args.verbose, force_simulation=args.force_simulation)
        print(f"Time taken: {int(time() - start_time)} seconds")

        plot_primary_categories(schedule_stats) # Plot only the primary categories
        print(f"Success Rate: {calculate_success_rate(schedule_stats) * 100}%")
    else:
        # Single task set
        task_set = parse_task_file(path)
        ret_val = review_task_set_uni(args.algorithm, task_set, verbose=args.verbose, force_simulation=args.force_simulation, task_file=path)
        print(f"Time taken: {int(time() - start_time)} seconds")
        print(f"Return value: {ret_val}")
        exit(ret_val)
