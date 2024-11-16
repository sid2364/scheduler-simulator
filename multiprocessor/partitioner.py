from abc import ABC, abstractmethod
from dataclasses import dataclass

from entities import TaskSet
from multiprocessor.cluster import Cluster
from utils.metrics import sort_tasks_by_utilization

"""
Main class for partitioning heuristics
"""
@dataclass
class PartitionHeuristic(ABC):
    decreasing_utilisation: bool = True

    def __init__(self, decreasing_utilisation=True):
        self.decreasing_utilisation = decreasing_utilisation

    @abstractmethod
    def partition(self, task_set: TaskSet, clusters: list[Cluster]):
        pass

"""
First Fit, Best Fit, Worst Fit, Next Fit partitioning heuristics
"""
class BestFit(PartitionHeuristic):
    def partition(self, task_set: TaskSet, clusters: list[Cluster]):
        # Sort tasks by utilization
        sorted_tasks = sort_tasks_by_utilization(task_set.tasks, self.decreasing_utilisation) # Decreasing utilization is from the parent class
        print(f"Sorted tasks: {sorted_tasks}")
        for task in sorted_tasks:
            # Find the cluster with the least utilization
            min_utilization_clusters = sorted(clusters, key=lambda x: x.get_utilisation())
            # Check if the task can fit in the clusters in this order
            found_fit = False
            for cluster in min_utilization_clusters:
                if cluster.can_fit(task):
                    cluster.add_task(task)
                    print(f"Task {task.task_id} added to cluster {cluster.cluster_id}")
                    found_fit = True
                    break
            if not found_fit:
                # If the task cannot fit in any cluster, no partitioning is possible, task set is not schedulable
                print(f"Task {task.task_id} cannot fit in any cluster")
                return None
        return clusters

class WorstFit(PartitionHeuristic):
    def partition(self, task_set: TaskSet, clusters: list[Cluster]):
        # Sort tasks by utilization
        sorted_tasks = sort_tasks_by_utilization(task_set.tasks, self.decreasing_utilisation) # Decreasing utilization is from the parent class
        for task in sorted_tasks:
            # Find the cluster with the most utilization
            max_utilization_clusters = sorted(clusters, key=lambda x: x.get_utilisation(), reverse=True)
            # Check if the task can fit in the clusters in this order
            found_fit = False
            for cluster in max_utilization_clusters:
                if cluster.can_fit(task):
                    cluster.add_task(task)
                    # print(f"Task {task.task_id} added to cluster {max_utilization_cluster.cluster_id}")
                    found_fit = True
                    break
            if not found_fit:
                # If the task cannot fit in any cluster, no partitioning is possible, task set is not schedulable
                return None
        return clusters

class FirstFit(PartitionHeuristic):
    def partition(self, task_set: TaskSet, clusters: list[Cluster]):
        # Sort tasks by utilization
        sorted_tasks = sort_tasks_by_utilization(task_set.tasks, self.decreasing_utilisation) # Decreasing utilization is from the parent class
        for task in sorted_tasks:
            # Find the first cluster that can fit the task
            found_fit = False
            for cluster in clusters: # Here we don't need to sort the clusters
                if cluster.can_fit(task):
                    cluster.add_task(task)
                    # print(f"Task {task.task_id} added to cluster {cluster.cluster_id}")
                    found_fit = True
                    break
            if not found_fit:
                # If the task cannot fit in any cluster, no partitioning is possible, task set is not schedulable
                return None
        return clusters

class NextFit(PartitionHeuristic):
    def partition(self, task_set: TaskSet, clusters: list[Cluster]):
        # Sort tasks by utilization
        sorted_tasks = sort_tasks_by_utilization(task_set.tasks, self.decreasing_utilisation) # Decreasing utilization is from the parent class
        current_cluster = 0
        for task in sorted_tasks:
            # Find the next cluster that can fit the task
            found_fit = False
            for i in range(len(clusters)):
                cluster = clusters[(current_cluster + i) % len(clusters)]
                if cluster.can_fit(task):
                    cluster.add_task(task)
                    # print(f"Task {task.task_id} added to cluster {cluster.cluster_id}")
                    current_cluster = (current_cluster + i) % len(clusters)
                    found_fit = True
                    break
            if not found_fit:
                # If the task cannot fit in any cluster, no partitioning is possible, task set is not schedulable
                return None
        return clusters
