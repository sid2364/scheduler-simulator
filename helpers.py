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
Plotter
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
