from abc import ABC, abstractmethod
from dataclasses import dataclass
from time import time

from entities import TaskSet, Task, Job
from utils.metrics import get_delta_t


"""
EDF(k) Scheduler
"""
@dataclass
class EDFk(ABC):
    task_set: TaskSet
    k: int
    m: int

    def __init__(self, task_set: TaskSet, num_clusters: int, num_processors: int, verbose=False, force_simulation=False):
        self.task_set = task_set
        self.k = num_clusters
        self.m = num_processors
        self.clusters = []

        self.verbose = verbose
        self.print = lambda *args: print(*args) if self.verbose else None
        self.force_simulation = force_simulation

        self.init_clusters()

    """
    Create m/k clusters for the EDF(k) scheduler
    
    If k = 1, this is partitioned EDF
    If k = m, this is global EDF
    Otherwise, it is a hybrid of the two!
    """
    def init_clusters(self):
        # Divide processors into clusters of size k
        num_clusters = self.m // self.k
        self.clusters = [[] for _ in range(num_clusters)]
        self.print(f"Initialized {num_clusters} clusters for EDF-{self.k}")

    """
    Heuristic to fit a task into a cluster
    
    Child classes should pass their custom heuristic to this method
    """
    @abstractmethod
    def fit(self, task, cluster):
        pass

    @staticmethod
    def get_top_priority(active_tasks, cluster):
        jobs = [job for task in active_tasks for job in task.jobs if job is not None]
        jobs = [job for job in jobs if job.task in cluster] # FIXME: This is not correct
        return min(jobs, key=lambda job: job.get_deadline()).task if jobs else None

    """
    Assign tasks to clusters based on fit() heuristic
    
    This is not used in Global EDF!
    """
    def assign_task_to_cluster(self, task):
        for cluster in self.clusters:
            if self.fit(task, cluster):  # Custom heuristic to check if task fits
                cluster.append(task)
                self.print(f"Assigned T{task.task_id} to Cluster {self.clusters.index(cluster)}")
                return True
        return False

    """
    Simulate
    """
    def simulate_taskset(self):
        t = 0
        time_step = get_delta_t(task_set=self.task_set)

        time_max = self.get_simulation_interval() # TODO
        if self.is_task_set_too_long(time_max): # TODO
            return 2

        time_started = time()

        while t < time_max:
            # TODO
            # Check for deadline misses in all clusters

            # Check if previous cycle jobs finished

            # Check for new job releases in all clusters

            # Get the highest priority job in each cluster that will execute for one time_unit

            # Reassign current_cycle_jobs for each cluster

            # Schedule these jobs!

            # Reassign previous_cycle_tasks to be the highest priority tasks for the next round

            pass

        return 1


"""
Within each cluster, tasks can migrate between processors
"""
class Cluster:
    num_processors: int
    tasks: list[Task]
    current_jobs: list = []
    active_tasks: list = []
    previous_cycle_jobs: list = []
    previous_cycle_tasks: list = []

    def __init__(self, tasks, num_processors):
        self.tasks = tasks
        self.num_processors = num_processors
        self.current_jobs = []
        self.active_tasks = []
