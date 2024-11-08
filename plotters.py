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
    wedges, texts, autotexts = plt.pie(sizes,
                                       explode=explode,
                                       colors=colors,
                                       autopct="%1.1f%%",
                                       shadow=True,
                                       startangle=140,
                                       wedgeprops={"edgecolor": "black"})

    plt.title("Schedulability Categories", fontsize=14, fontweight="bold")
    plt.axis("equal")

    legend_labels = [f"{label}: {count}" for label, count in zip(labels, sizes)]
    plt.legend(wedges, legend_labels, title="Categories", loc="upper right",
               bbox_to_anchor=(1, 1), fontsize=10)
    plt.tight_layout()
    plt.show()

"""
Show how the non-schedulable task sets compare with EDF
"""
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
Plots for the report, just for EDF!
"""
def plot_feasibility_ratio(feasibility_dict, plot_title, xlabel):
    # Get tasks as categories
    tasks = list(feasibility_dict.keys())
    ratios = [feasibility_dict[task] for task in tasks]

    plt.figure(figsize=(10, 6))

    # Define x positions for each category
    x_positions = range(len(tasks))

    # Plot bars with categorical x-axis
    plt.bar(x_positions, ratios, color="skyblue", edgecolor="black", width=0.5)

    # Set categorical labels for x-axis
    plt.xticks(x_positions, tasks)

    # Set labels and title
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel("Feasibility Ratio", fontsize=14)
    plt.title(plot_title, fontsize=16)
    plt.ylim(-0.1, 1.1)  # Ratio ranges from 0 to 1, so extend a bit

    # Add grid on y-axis only
    plt.grid(axis="y", alpha=0.75)
    plt.tight_layout()
    plt.show()

"""
Plots success rates of each algorithm as a line chart, with utilization on the x-axis and success rate on the y-axis.
"""
def plot_success_rate(success_rates, plot_title, xlabel):
    plt.figure(figsize=(12, 6))

    # Define categorical positions for each x-axis category
    categories = list(next(iter(success_rates.values())).keys())
    x_positions = np.arange(len(categories))  # Evenly spaced positions

    # Define a fixed width for the bars
    width = 0.15

    # Plot each algorithm
    for i, (alg, rates) in enumerate(success_rates.items()):
        success_values = [rates[util] for util in categories]

        # Offset each algorithm slightly on the categorical x-axis
        bar_positions = x_positions + i * width - (len(success_rates) - 1) * width / 2

        # Plot bars and use the same color for the line plot
        bars = plt.bar(bar_positions, success_values, width=width, label=alg)
        plt.plot(x_positions, success_values, marker="o", color=bars[0].get_facecolor())

    # Set the categorical labels
    plt.xticks(x_positions, categories)  # Use actual category values as labels
    plt.xlabel(xlabel)
    plt.ylabel("Success Rate")
    plt.title(plot_title)
    plt.legend(title="Algorithm", loc="best")
    plt.grid(True, axis="y")  # Only grid on y-axis for clarity
    plt.tight_layout()
    plt.show()
