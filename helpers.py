from entities import TaskSet
import math

"""
Enum class for the status of the task set 
"""
class Feasibility:
    FEASIBLE_SHORTCUT = 0
    FEASIBLE_SIMULATION = 1
    NOT_SCHEDULABLE_BY_A_SHORTCUT = 2
    NOT_SCHEDULABLE_BY_A_SIMULATION = 3
    SCHEDULABLE_BY_OPTIMAL_BUT_NOT_BY_A = 4
    INFEASIBLE = 5
    TIMED_OUT = 6

    # get string representation of the status
    @staticmethod
    def get_status_string(status):
        if status == Feasibility.FEASIBLE_SHORTCUT:
            return "Feasible, took a shortcut"
        elif status == Feasibility.FEASIBLE_SIMULATION:
            return "Feasible, had to simulate"
        elif status == Feasibility.NOT_SCHEDULABLE_BY_A_SHORTCUT:
            return "Not Schedulable by A, took a shortcut"
        elif status == Feasibility.NOT_SCHEDULABLE_BY_A_SIMULATION:
            return "Not Schedulable by A, had to simulate"
        elif status == Feasibility.SCHEDULABLE_BY_OPTIMAL_BUT_NOT_BY_A:
            return "Schedulable by Optimal (EDF) but not by A"
        elif status == Feasibility.INFEASIBLE:
            return "Infeasible (both A and Optimal)"
        elif status == Feasibility.TIMED_OUT:
            return "Timed Out"

"""
Utilisation factor functions
"""
def utilisation(task_set: TaskSet) -> bool:
    # Calculate the utilization factor
    utilization_factor = 0
    for task in task_set.tasks:
        utilization_factor += task.computation_time / task.period
    # print(f"Utilization factor: {utilization_factor}")
    return utilization_factor

def is_utilisation_lte_69(task_set: TaskSet) -> bool:
    # Check if the utilization factor is below 69%
    return utilisation(task_set) <= 0.69

def is_utilisation_lte_1(task_set: TaskSet) -> bool:
    # Check if the utilization factor is above 100%
    return utilisation(task_set) <= 1

def is_utilisation_within_ll_bound(task_set: TaskSet) -> bool:
    # Check if the utilization factor is within the Liu and Layland bound
    n = len(task_set.tasks)
    total_utilization = utilisation(task_set)

    utilization_bound = n * (2 ** (1 / n) - 1)

    return total_utilization <= utilization_bound


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
    return get_lcm(list(set(time_period_list)))

def get_feasibility_interval(task_set: TaskSet) -> int:
    # Calculate the maximum time for simulation
    o_max = max([task.offset for task in task_set.tasks])
    return o_max + 2 * get_hyper_period(task_set)

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


def get_busy_period(task_set: TaskSet):
    # Calculate the busy period for the given task set if feasibility interval is too large
    current_busy_period = sum(task.computation_time for task in task_set.tasks)

    while True:
        # Calculate the next busy period
        busy_period_next = sum(math.ceil(current_busy_period / task.period) * task.computation_time for task in task_set.tasks)

        # Check if the busy period has "converged"
        if busy_period_next == current_busy_period:
            break
        current_busy_period = busy_period_next

    #print(f"Busy period: {current_busy_period}")
    return current_busy_period * 10


"""
Calculate the success rate of the algorithm
"""
def calculate_success_rate(schedule_stats):
    """
    Success Rate = (FEASIBLE_SHORTCUT + FEASIBLE_SIMULATION) /
               (FEASIBLE_SHORTCUT + FEASIBLE_SIMULATION + NOT_SCHEDULABLE_BY_A_SHORTCUT + NOT_SCHEDULABLE_BY_A_SIMULATION)
    """
    success = schedule_stats.get(Feasibility.FEASIBLE_SHORTCUT, 0) + schedule_stats.get(Feasibility.FEASIBLE_SIMULATION, 0)

    failure = schedule_stats.get(Feasibility.NOT_SCHEDULABLE_BY_A_SHORTCUT, 0) + schedule_stats.get(Feasibility.NOT_SCHEDULABLE_BY_A_SIMULATION, 0)

    total = success + failure

    if total == 0:
        return 0

    success_rate = success / total * 1.0
    return success_rate

