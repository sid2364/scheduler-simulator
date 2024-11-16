from abc import ABC, abstractmethod
from dataclasses import dataclass
from time import time

from entities import TaskSet
from multiprocessor.edfcluster import EDFCluster
from multiprocessor.partitioner import PartitionHeuristic
from utils.metrics import get_delta_t, sort_tasks_by_utilization, get_feasibility_interval

MAX_ITERATIONS_LIMIT = 50000000  # Saves some time by exiting if we already know it's going to take too long
MAX_SECONDS_LIMIT = 5  # 5 seconds per task set can actually be a lot of time!

"""
EDF(k) Scheduler
"""
@dataclass
class EDFk(ABC):
    task_set: TaskSet
    k: int
    m: int

    def __init__(self,
                 task_set: TaskSet,
                 num_clusters: int,
                 num_processors: int,
                 heuristic: PartitionHeuristic,
                 verbose=False,
                 force_simulation=False):
        self.task_set = task_set
        self.k = num_clusters
        self.m = num_processors
        self.heuristic = heuristic
        self.clusters = []

        self.verbose = verbose
        self.print = lambda *args: print(*args) if self.verbose else None
        self.force_simulation = force_simulation

        self.init_clusters()

    """
    Create m/k clusters for the EDF(k) scheduler
    
    If k = 1, this is partitioned EDF
    If k = m, this is global EDF
    Otherwise, it is a hybrid of the two - EDF(k)
    """
    def init_clusters(self):
        # Divide processors into clusters of size k
        num_clusters = self.m // self.k
        remaining_processors = self.m % self.k # Except, we also have sometimes an uneven division

        for _ in range(num_clusters):
            self.clusters.append(EDFCluster(self.k))

        if remaining_processors > 0:
            self.clusters.append(EDFCluster(remaining_processors))
        # self.print(f"Initialized {len(self.clusters)} clusters: {self.clusters}")

    def is_task_set_too_long(self, time_max=None) -> bool:
        if time_max is None:
            time_max = self.get_simulation_interval()
        return time_max > MAX_ITERATIONS_LIMIT

    def partition_taskset(self):
        # Partition the task set into the clusters
        self.clusters = self.heuristic.partition(self.task_set, self.clusters)
        if self.clusters is None:
            return False
        return True

    def get_simulation_interval(self):
        feasibility_interval = 0
        for cluster in self.clusters:
            hyper_period = get_feasibility_interval(cluster.tasks)
            if hyper_period > feasibility_interval:
                feasibility_interval = hyper_period
        print(f"Feasibility interval: {feasibility_interval}")
        return feasibility_interval

    """
    Simulate the task set and check if it is schedulable
       
    Exit code Description
    0 Schedulable and simulation was required.
    1 Schedulable because some sufficient condition is met.
    2 Not schedulable and simulation was required.
    3 Not schedulable because a necessary condition does not hold.
    4 You can not tell.
    """
    def simulate_taskset(self):
        t = 0
        time_step = get_delta_t(task_set=self.task_set)

        # Partition the task set into the clusters
        if not self.partition_taskset():
            return 3

        time_max = self.get_simulation_interval() # TODO
        if self.is_task_set_too_long(time_max): # TODO
            return 4

        time_started = time()

        while t < time_max:
            self.print(f"******* Time {t}-{t + time_step} *******")

            # Check if we're taking too long to run this function
            if time() - time_started > MAX_SECONDS_LIMIT:
                self.print(f"Took more than {MAX_SECONDS_LIMIT}, timing out!")
                return 4

            # Check for deadline misses in all clusters
            for cluster in self.clusters:
                for task in cluster.tasks:
                    for job in task.jobs:
                        if job.deadline_missed(t):
                            self.print(f"Deadline missed for job {job} at time {t}, it had {job.computation_time_remaining} remaining")
                            return 2

            # Check if previous cycle jobs finished
            for cluster in self.clusters:
                previous_cycle_jobs = cluster.previous_cycle_jobs
                for job in previous_cycle_jobs:
                    if job.is_finished():
                        self.print(f"{job} is finished")
                        task = job.task
                        cluster.current_jobs.remove(job)
                        task.finish_job(job)
                        if not task.has_unfinished_jobs():
                            cluster.active_tasks.remove(task)

            # Check for new job releases in all clusters
            for cluster in self.clusters:
                for task in cluster.tasks:
                    job = task.release_job(t)
                    if job is not None:
                        cluster.active_tasks.append(task)
                        cluster.current_jobs.append(job)
                        self.print(f"Released {job} at time {t}")

            # Get the highest priority m jobs within each cluster that will each execute for one time_unit
            for cluster in self.clusters:
                top_tasks = cluster.get_top_priorities(cluster.active_tasks)
                cluster.previous_cycle_jobs.clear()
                cluster.previous_cycle_tasks.clear()
                if not top_tasks:
                    self.print(f"No tasks to schedule in cluster {cluster.cluster_id} at time {t}")
                    continue
                else:
                    self.print(f"Top tasks in cluster {cluster}: {top_tasks}")
                    for task in top_tasks:
                        job = task.get_first_job()
                        job.schedule(time_step)
                        self.print(f"Scheduled {job} in cluster {cluster.cluster_id} for time {time_step}, remaining time: {job.computation_time_remaining}")

                        cluster.previous_cycle_tasks.append(task)
                        cluster.previous_cycle_jobs.append(job)

            # for cluster in self.clusters:
            #     for task in cluster.active_tasks:
            #         self.print(f"Cluster {cluster.cluster_id} active tasks: T{task.task_id}")
            #     for job in cluster.current_jobs:
            #         self.print(f"Cluster {cluster.cluster_id} current jobs: T{job.task.task_id}-J{job.job_id}")
            #     for job in cluster.previous_cycle_jobs:
            #         self.print(f"Cluster {cluster.cluster_id} previous cycle jobs: T{job.task.task_id}-J{job.job_id}")
            #     for task in cluster.previous_cycle_tasks:
            #         self.print(f"Cluster {cluster.cluster_id} previous cycle tasks: T{task.task_id}")

            t += time_step

        return 0

