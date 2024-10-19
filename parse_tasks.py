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