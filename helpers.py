from entities import TaskSet
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

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
    return utilization_factor

def is_utilisation_lte_69(task_set: TaskSet) -> bool:
    # Check if the utilization factor is below 69%
    return utilisation(task_set) <= 0.69

def is_utilisation_lte_1(task_set: TaskSet) -> bool:
    # Check if the utilization factor is above 100%
    return utilisation(task_set) <= 1

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

def get_time_max(task_set: TaskSet) -> int:
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

"""
Plotters
"""
def pie_plot_categories(category_frequency_dict):
    print([(Feasibility.get_status_string(k), v) for k, v in category_frequency_dict.items()])

    # Original data labels and values
    labels = []
    sizes = []

    # Dynamic color palette
    colors = list(mcolors.TABLEAU_COLORS.values())[:len(category_frequency_dict)]

    # Convert the dictionary to lists for plotting
    for key, value in category_frequency_dict.items():
        labels.append(Feasibility.get_status_string(key))
        sizes.append(value)

    explode = [0.05] * len(sizes)  # Slightly explode all slices

    # Adjust the figure size
    plt.figure(figsize=(8, 6))

    # Plot the pie chart without the labels directly on the slices
    wedges, texts, autotexts = plt.pie(sizes, explode=explode, colors=colors,
                                       autopct='%1.1f%%', shadow=True, startangle=140,
                                       wedgeprops={'edgecolor': 'black'})

    plt.title("Distribution of Categories", fontsize=14, fontweight='bold')
    plt.axis('equal')  # Equal aspect ratio ensures the pie is drawn as a circle.

    # Add a legend using the nice labels
    plt.legend(wedges, labels, title="Categories", loc="upper right",
               bbox_to_anchor=(1, 1), fontsize=10)

    # Adjust layout to prevent cutoff
    plt.tight_layout()

    plt.show()

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


def plot_success_rate(success_rate_dict, plot_title="Success Rate of Scheduling Algorithms", xlabel="Algorithm", ylabel="Success Rate (%)"):
    """
    Plot the success rates of different scheduling algorithms.

    Parameters:
    - success_rate_dict: dict where keys are algorithm names and values are success rates (0 to 1).
    - plot_title: Title of the plot.
    - xlabel: Label for the x-axis.
    - ylabel: Label for the y-axis.
    """
    algorithms = list(success_rate_dict.keys())
    success_rates = [rate * 100 for rate in success_rate_dict.values()]  # Convert to percentage

    colors = list(mcolors.TABLEAU_COLORS.values())[:len(algorithms)]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(algorithms, success_rates, color=colors, edgecolor='black')

    # Add percentage labels on top of the bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, height, f'{height:.1f}%', ha='center', va='bottom', fontsize=10)

    plt.title(plot_title, fontsize=16, fontweight='bold')
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.ylim(-10, 110)  # Since it's a percentage

    plt.tight_layout()
    plt.show()

def plot_feasibility_ratio_by_tasks(feasibility_dict, utilization, plot_title):
    """
    Plot the ratio of feasible task sets according to the number of tasks.

    Parameters:
    - feasibility_dict: dict with number of tasks as keys and feasibility ratios as values.
    - utilization: Utilization percentage (e.g., 80).
    - plot_title: Title for the plot.
    """
    tasks = sorted(feasibility_dict.keys())
    ratios = [feasibility_dict[task] for task in tasks]

    plt.figure(figsize=(10, 6))
    plt.bar(tasks, ratios, color='skyblue', edgecolor='black')

    plt.xlabel('Number of Tasks', fontsize=14)
    plt.ylabel('Feasibility Ratio', fontsize=14)
    plt.title(plot_title, fontsize=16)
    plt.ylim(-0.2, 1.2)  # Ratio ranges from 0 to 1

    plt.xticks(tasks)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def plot_success_rate_by_tasks(success_rate_dict, utilization, plot_title):
    """
    Plot the success rate of each scheduling algorithm according to the number of tasks.

    Parameters:
    - success_rate_dict: dict where keys are algorithm names and values are dicts with number of tasks as keys and success rates as values.
    - utilization: Utilization percentage (e.g., 80).
    - plot_title: Title for the plot.
    """
    # Extract the list of task numbers from the first algorithm's data
    algorithms = list(success_rate_dict.keys())
    tasks = sorted(next(iter(success_rate_dict.values())).keys())

    plt.figure(figsize=(12, 8))

    for algorithm, task_success in success_rate_dict.items():
        success_rates = [task_success[task] * 100 for task in tasks]
        plt.plot(tasks, success_rates, marker='o', label=algorithm)

    plt.xlabel('Number of Tasks', fontsize=14)
    plt.ylabel('Success Rate (%)', fontsize=14)
    plt.title(plot_title, fontsize=16)
    plt.ylim(-10, 110)
    plt.legend(title="Algorithms")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def plot_feasibility_ratio_by_utilization(feasibility_dict, num_tasks, plot_title):
    """
    Plot the ratio of feasible task sets according to utilization.

    Parameters:
    - feasibility_dict: dict with utilization levels as keys and feasibility ratios as values.
    - num_tasks: Number of tasks (e.g., 10).
    - plot_title: Title for the plot.
    """
    utilizations = sorted(feasibility_dict.keys())
    ratios = [feasibility_dict[u] for u in utilizations]

    plt.figure(figsize=(10, 6))
    plt.plot(utilizations, ratios, marker='s', linestyle='-', color='green')

    plt.xlabel('Utilization (%)', fontsize=14)
    plt.ylabel('Feasibility Ratio', fontsize=14)
    plt.title(plot_title, fontsize=16)
    plt.ylim(-0.2, 1.2)

    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def plot_success_rate_by_utilization(success_rate_dict, num_tasks, plot_title):
    """
    Plot the success rate of each scheduling algorithm according to utilization.

    Parameters:
    - success_rate_dict: dict where keys are algorithm names and values are dicts with utilization levels as keys and success rates as values.
    - num_tasks: Number of tasks (e.g., 10).
    - plot_title: Title for the plot.
    """
    algorithms = list(success_rate_dict.keys())
    utilizations = sorted(next(iter(success_rate_dict.values())).keys())

    plt.figure(figsize=(12, 8))

    for algorithm, util_success in success_rate_dict.items():
        success_rates = [util_success[u] * 100 for u in utilizations]
        plt.plot(utilizations, success_rates, marker='^', linestyle='-', label=algorithm)

    plt.xlabel('Utilization (%)', fontsize=14)
    plt.ylabel('Success Rate (%)', fontsize=14)
    plt.title(plot_title, fontsize=16)
    plt.ylim(-10, 110)
    plt.legend(title="Algorithms")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()