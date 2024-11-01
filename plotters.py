import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from helpers import Feasibility

"""
Plotters for the stats from just one algorithm
"""
def plot_primary_categories(category_frequency_dict):
    primary_categories = {
        Feasibility.FEASIBLE_SHORTCUT: category_frequency_dict.get(Feasibility.FEASIBLE_SHORTCUT, 0),
        Feasibility.FEASIBLE_SIMULATION: category_frequency_dict.get(Feasibility.FEASIBLE_SIMULATION, 0),
        Feasibility.NOT_SCHEDULABLE_BY_A_SHORTCUT: category_frequency_dict.get(Feasibility.NOT_SCHEDULABLE_BY_A_SHORTCUT, 0),
        Feasibility.NOT_SCHEDULABLE_BY_A_SIMULATION: category_frequency_dict.get(Feasibility.NOT_SCHEDULABLE_BY_A_SIMULATION, 0),
        Feasibility.TIMED_OUT: category_frequency_dict.get(Feasibility.TIMED_OUT, 0)
    }

    labels = [Feasibility.get_status_string(k) for k in primary_categories.keys()]
    sizes = list(primary_categories.values())
    colors = list(mcolors.TABLEAU_COLORS.values())[:len(primary_categories)]
    explode = [0.05] * len(sizes)

    plt.figure(figsize=(8, 6))
    wedges, texts, autotexts = plt.pie(sizes, explode=explode, colors=colors,
                                       autopct="%1.1f%%", shadow=True, startangle=140,
                                       wedgeprops={"edgecolor": "black"})

    plt.title("Schedulability Categories", fontsize=14, fontweight="bold")
    plt.axis("equal")
    plt.legend(wedges, labels, title="Categories", loc="upper right",
               bbox_to_anchor=(1, 1), fontsize=10)
    plt.tight_layout()
    plt.show()

def plot_non_schedulable_breakdown_grouped(category_frequency_dict,
                                                      target_algorithm_name="Target Algorithm"):
    # Define the simplified categories
    categories = ["Not Schedulable by " + target_algorithm_name,
                  "Schedulable by Optimal but Not by " + target_algorithm_name,
                  "Infeasible"]

    # Combine the shortcut and simulation counts for the target algorithm
    not_schedulable_target = (
            category_frequency_dict.get(Feasibility.NOT_SCHEDULABLE_BY_A_SHORTCUT, 0) +
            category_frequency_dict.get(Feasibility.NOT_SCHEDULABLE_BY_A_SIMULATION, 0)
    )

    # Define the values for each algorithm (target and optimal)
    target_values = [
        not_schedulable_target,
        category_frequency_dict.get(Feasibility.SCHEDULABLE_BY_OPTIMAL_BUT_NOT_BY_A, 0),
        category_frequency_dict.get(Feasibility.INFEASIBLE, 0)
    ]

    # Optimal algorithm values only apply to the last two categories
    optimal_values = [
        0,  # No combined non-schedulable category for optimal
        category_frequency_dict.get(Feasibility.SCHEDULABLE_BY_OPTIMAL_BUT_NOT_BY_A, 0),
        category_frequency_dict.get(Feasibility.INFEASIBLE, 0)
    ]

    # Generate the grouped bar chart
    x = np.arange(len(categories))
    bar_width = 0.25
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - bar_width / 2, target_values, bar_width, label=target_algorithm_name) # - bar_width / 2 to shift left
    ax.bar(x + bar_width / 2, optimal_values, bar_width, label="Optimal Scheduler (EDF)") # + bar_width / 2 to shift right

    # Add labels, title, and legend
    ax.set_xlabel("Non-Schedulable Categories")
    ax.set_ylabel("Number of Task Sets")
    ax.set_title(
        f"Comparison of Non-Schedulable Categories between {target_algorithm_name} and Optimal Scheduler (EDF)")
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45)
    ax.legend()

    plt.tight_layout()
    plt.show()

"""
Plots for the report, comparing multiple algorithms
"""
def plot_feasibility_ratio(feasibility_dict, plot_title, xlabel):
    """
    Plot the ratio of feasible task sets according to the number of tasks. This will just be for EDF!
    """
    tasks = sorted(feasibility_dict.keys())
    ratios = [feasibility_dict[task] for task in tasks]

    plt.figure(figsize=(10, 6))
    plt.bar(tasks, ratios, color="skyblue", edgecolor="black", width=0.5)

    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel("Feasibility Ratio", fontsize=14)
    plt.title(plot_title, fontsize=16)
    plt.ylim(-0.1, 1.1)  # Ratio ranges from 0 to 1, so extend a bit

    plt.xticks(tasks)
    plt.grid(axis="y", alpha=1)
    plt.tight_layout()
    plt.show()

def plot_success_rate(success_rates, plot_title, xlabel):
    """
    Plots success rates of each algorithm as a line chart, with utilization on the x-axis and success rate on the y-axis.
    """
    plt.figure(figsize=(10, 6))

    # Plot success rate for each algorithm
    for alg, rates in success_rates.items():
        utilization_levels = sorted(rates.keys())
        success_values = [rates[util] for util in utilization_levels]
        plt.plot(utilization_levels, success_values, marker="o", label=alg)

    plt.xlabel(xlabel)
    plt.ylabel("Success Rate")
    plt.title(plot_title)
    plt.legend(title="Algorithm")
    plt.grid(True)
    plt.tight_layout()
    plt.show()