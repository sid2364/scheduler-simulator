from entities import TaskSet, Task
import math

"""
Enum class for the status of the task set in uniprocessor systems
"""
class UniprocessorFeasibility:
    FEASIBLE_SHORTCUT = 0
    FEASIBLE_SIMULATION = 1
    NOT_SCHEDULABLE_BY_A_SHORTCUT = 2
    NOT_SCHEDULABLE_BY_A_SIMULATION = 3
    SCHEDULABLE_BY_OPTIMAL_BUT_NOT_BY_A = 4
    INFEASIBLE = 5
    TIMED_OUT = 6

    # get string representation of the status
    @staticmethod
    def get_status_string(status) -> str:
        if status == UniprocessorFeasibility.FEASIBLE_SHORTCUT:
            return "Feasible, took a shortcut"
        elif status == UniprocessorFeasibility.FEASIBLE_SIMULATION:
            return "Feasible, had to simulate"
        elif status == UniprocessorFeasibility.NOT_SCHEDULABLE_BY_A_SHORTCUT:
            return "Not Schedulable by A, took a shortcut"
        elif status == UniprocessorFeasibility.NOT_SCHEDULABLE_BY_A_SIMULATION:
            return "Not Schedulable by A, had to simulate"
        elif status == UniprocessorFeasibility.SCHEDULABLE_BY_OPTIMAL_BUT_NOT_BY_A:
            return "Schedulable by Optimal (EDF) but not by A"
        elif status == UniprocessorFeasibility.INFEASIBLE:
            return "Infeasible (both A and Optimal)"
        elif status == UniprocessorFeasibility.TIMED_OUT:
            return "Timed Out"
        return "Unknown"

"""
Enum class for the status of the task set in multiprocessor systems
"""
class MultiprocessorFeasibility:
    SCHEDULABLE_SIMULATION = 0
    SCHEDULABLE_SHORTCUT = 1
    NOT_SCHEDULABLE_SIMULATION = 2
    NOT_SCHEDULABLE_SHORTCUT = 3
    CANNOT_TELL = 4

    # get string representation of the status
    @staticmethod
    def get_status_string(status) -> str:
        if status == MultiprocessorFeasibility.SCHEDULABLE_SIMULATION:
            return "Schedulable, had to simulate"
        elif status == MultiprocessorFeasibility.SCHEDULABLE_SHORTCUT:
            return "Schedulable, took a shortcut"
        elif status == MultiprocessorFeasibility.NOT_SCHEDULABLE_SIMULATION:
            return "Not Schedulable, had to simulate"
        elif status == MultiprocessorFeasibility.NOT_SCHEDULABLE_SHORTCUT:
            return "Not Schedulable, took a shortcut"
        elif status == MultiprocessorFeasibility.CANNOT_TELL:
            return "Cannot tell if schedulable or not"

"""
Utilisation factor functions
"""
def utilisation(task_set: TaskSet) -> float:
    # Calculate the utilization factor
    utilization_factor = 0
    for task in task_set.tasks:
        utilization_factor += task.computation_time / task.period
    print(f"Utilization factor: {utilization_factor}")
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
Worst-case response time for explicit-deadline tasks
"""
def calculate_worst_case_response_time(task: Task, sorted_by_prio_tasks: list) -> int:
    response_time_current = task.computation_time  # Initialize with task's own computation time
    task_index = sorted_by_prio_tasks.index(task)  # Position in sorted list

    while True:
        # Interference from higher-priority tasks
        interference = sum(
            math.ceil(response_time_current / higher_task.period) * higher_task.computation_time
            for higher_task in sorted_by_prio_tasks[:task_index]
        )
        response_time_next = task.computation_time + interference
        # # If the response time converges or exceeds the deadline, update and stop the calculation
        if response_time_next == response_time_current or response_time_next > task.deadline:
            response_time_current = response_time_next  # Update before breaking, so that the last value is saved!
            break
        # print(f"Response time current: {response_time_current}, response time next: {response_time_next}")
        response_time_current = response_time_next
    # print(f"Response time for task {task.task_id}: {response_time_current}")
    return response_time_current


"""
Worst-case response time but also taking into consideration the priorities; Handy for Audsley!
"""
def calculate_worst_case_response_time_with_priorities(task: Task, sorted_tasks: list, priorities: dict):
    wcrt = task.computation_time
    while True:
        interference = 0
        for higher_priority_task in sorted_tasks:
            if priorities[higher_priority_task.task_id] < priorities[task.task_id]:
                # Add interference from higher-priority tasks
                interference += math.ceil(wcrt / higher_priority_task.period) * higher_priority_task.computation_time

        next_wcrt = task.computation_time + interference

        # Check for convergence or deadline violation
        if next_wcrt == wcrt:
            return wcrt
        elif next_wcrt > task.deadline:
            return float('inf')  # Task can't meet its deadline

        wcrt = next_wcrt

"""
Demand Bound Function (DBF) for a task
"""
def demand_bound_function(task: Task, till_time: int) -> int:
    # Calculate the demand bound function for a task
    workload_contribution = math.floor(till_time - task.deadline / task.period) + 1
    return max(0, workload_contribution) * task.computation_time

"""
DBF for a task set

If total_demand > m * t, the task set is not schedulable
"""
def demand_bound_function_tasks(tasks: list[Task], till_time: int) -> int:
    # Calculate the demand bound function for a task set
    return sum(demand_bound_function(task, till_time) for task in tasks)

"""
Critical points for a task set
"""
def compute_critical_points(tasks: list[Task], t_max: int) -> list[int]:
    critical_points = set()
    for task in tasks:
        k = 0
        while task.offset + k * task.period <= t_max:
            critical_points.add(task.offset + k * task.period)  # Release time
            critical_points.add(task.offset + k * task.period + task.deadline)  # Deadline
            k += 1
    return sorted(list(critical_points))

"""
Iterative demand bound function for a task set, also calculates for each critical instant
"""
def demand_bound_function_iterative(tasks: list, till_time: int, num_processors: int) -> bool:
    # Calculate the demand bound function for a task set
    critical_points = compute_critical_points(tasks, till_time)
    for t in critical_points:
        total_demand = demand_bound_function_tasks(tasks, t)
        print(f"DBF at time {t}: {total_demand}")
        if total_demand > num_processors * t:
            return False
    return True

"""
GCD and LCM functions for calculating the hyper period and delta_t
"""
def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a

def lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)

def get_lcm(time_period_list: list) -> int:
    # Calculate the least common multiple of a list of numbers
    lcm_value = time_period_list[0]
    for i in time_period_list[1:]:
        lcm_value = lcm(lcm_value, i)
    # print(f"LCM: {lcm_value}")
    return lcm_value

def get_gcd(time_value_list: list) -> int:
    # Calculate the greatest common divisor of a list of numbers
    gcd_value = time_value_list[0]
    for i in time_value_list[1:]:
        gcd_value = gcd(gcd_value, i)
    return gcd_value

def get_hyper_period(tasks: list) -> int:
    # Calculate the hyper period of a task set
    time_period_list = [task.period for task in tasks]
    # print(f"Time periods: {time_period_list}")
    return get_lcm(list(set(time_period_list)))

def get_feasibility_interval(tasks: list[Task]) -> int:
    # Calculate the maximum time for simulation
    o_max = max([task.offset for task in tasks])
    # print(f"Offset max: {o_max}")
    return o_max + 2 * get_hyper_period(tasks)

"""
First idle point in simulation, after 0
"""
def get_first_idle_point(tasks: list[Task]) -> int:
    # Initialize w with the sum of all computation times
    w = sum(task.computation_time for task in tasks)

    # Calculate the hyper-period to set an upper bound
    hyper_period = get_hyper_period(tasks)

    # Set an upper limit to prevent infinite loops
    upper_bound = min(hyper_period, 50_000_000)

    while w <= upper_bound:
        w_next = 0
        for task in tasks:
            # For each task, consider the number of releases within [0, w]
            # Using the minimum of deadline and period for accurate calculation
            interval = min(task.deadline, task.period)
            num_releases = math.ceil(w / interval)
            w_next += num_releases * task.computation_time

        # If the interval stabilizes, we have found the first idle point
        if w_next == w:
            return w_next

        # Update w for the next iteration
        w = w_next

    # If no idle point is found within the upper bound, return the upper bound
    return upper_bound

"""
Smallest time increment, used to make simulation step through quicker
"""
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

"""
Smallest time increment for a list of tasks
"""
def get_delta_t_tasks(tasks: list[Task]) -> int:
    # Calculate the greatest common divisor of the time periods of the tasks
    task_set = TaskSet(tasks)
    return get_delta_t(task_set)

def get_busy_period(task_set: TaskSet) -> int:
    # Calculate the busy period for the given task set if feasibility interval is too large
    current_busy_period = sum(task.computation_time for task in task_set.tasks)
    hyper_period = get_hyper_period(task_set.tasks)

    while True:
        # Calculate the next busy period
        busy_period_next = sum(math.ceil(current_busy_period / task.period) * task.computation_time for task in task_set.tasks)

        # Check if the busy period has "converged"
        if busy_period_next == current_busy_period:
            break
        current_busy_period = busy_period_next

        # Break if the busy period is too long!
        if current_busy_period > hyper_period:
            break

    #print(f"Busy period: {current_busy_period}")
    return current_busy_period * 2

"""
Calculate the success rate of the algorithm
"""
def calculate_success_rate(schedule_stats) -> float:
    """
    Success Rate = (FEASIBLE_SHORTCUT + FEASIBLE_SIMULATION) /
               (FEASIBLE_SHORTCUT + FEASIBLE_SIMULATION + NOT_SCHEDULABLE_BY_A_SHORTCUT + NOT_SCHEDULABLE_BY_A_SIMULATION)
    """
    success = schedule_stats.get(UniprocessorFeasibility.FEASIBLE_SHORTCUT, 0) + schedule_stats.get(UniprocessorFeasibility.FEASIBLE_SIMULATION, 0)

    failure = schedule_stats.get(UniprocessorFeasibility.NOT_SCHEDULABLE_BY_A_SHORTCUT, 0) + schedule_stats.get(UniprocessorFeasibility.NOT_SCHEDULABLE_BY_A_SIMULATION, 0)

    total = success + failure

    if total == 0:
        return 0

    success_rate = success / total * 1.0
    return success_rate

"""
Return the tasks sorted by their utilization for our bin packing exercise
"""
def sort_tasks_by_utilization(tasks: list, decreasing=True) -> list:
    # Sort the tasks by their utilization
    return sorted(tasks, key=lambda x: x.computation_time / x.period, reverse=decreasing)