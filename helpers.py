from entities import TaskSet

"""
Utilisation factor functions
"""
def utilisation(task_set: TaskSet) -> bool:
    # Calculate the utilization factor
    utilization_factor = 0
    for task in task_set.tasks:
        utilization_factor += task.computation_time / task.period
    n = len(task_set.tasks)
    upper_bound = n * (2 ** (1 / n) - 1)
    return utilization_factor <= upper_bound

def is_utilisation_lt_69(task_set: TaskSet) -> bool:
    # Check if the utilization factor is below 69%
    return utilisation(task_set) <= 0.69

def is_utilisation_gt_1(task_set: TaskSet) -> bool:
    # Check if the utilization factor is above 100%
    return utilisation(task_set) > 1

"""
GCD and LCM functions for calculating the hyper period and delta_t
"""
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    return a * b // gcd(a, b)

def get_lcm(time_period_list: list) -> int:
    # Calculate the least common multiple of a list of numbers
    lcm_value = time_period_list[0]
    for i in time_period_list[1:]:
        lcm_value = lcm(lcm_value, i)
    return lcm_value

def get_gcd(time_value_list: list) -> int:
    # Calculate the greatest common divisor of a list of numbers
    gcd_value = time_value_list[0]
    for i in time_value_list[1:]:
        gcd_value = gcd(gcd_value, i)
    return gcd_value

def get_hyper_period(task_set: TaskSet) -> int:
    # Calculate the hyper period of a task set
    time_period_list = [task.period for task in task_set.tasks]
    return get_lcm(time_period_list)

def get_delta_t(task_set: TaskSet) -> int:
    # Calculate the greatest common divisor of the time periods of the tasks
    time_period_list = []
    for task in task_set.tasks:
        time_period_list.append(task.offset)
        time_period_list.append(task.computation_time)
        time_period_list.append(task.deadline)
        time_period_list.append(task.period)

    # Only unique values
    return get_gcd(list(set(time_period_list)))