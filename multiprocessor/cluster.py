from dataclasses import dataclass

from entities import Task


"""
Logical grouping of processors in a multiprocessor system
For example, for EDF(k) scheduling, we divide the processors into k clusters

Within each cluster, tasks can migrate between processors

This class uses deadline as a priority metric (meant just for EDF)
"""
@dataclass
class Cluster:
    cluster_id = 0
    num_processors: float
    tasks: list[Task]
    current_jobs: list
    active_tasks: list
    previous_cycle_jobs: list
    previous_cycle_tasks: list

    def __init__(self, num_processors):
        Cluster.cluster_id += 1
        self.cluster_id = Cluster.cluster_id
        self.num_processors = num_processors
        self.tasks = []
        self.current_jobs = []
        self.active_tasks = []
        self.previous_cycle_jobs = []
        self.previous_cycle_tasks = []

    def get_utilisation(self):
        # Calculate utilisation of each task in the cluster
        if not self.tasks:
            return 0
        return sum(task.computation_time / task.period for task in self.tasks)

    def add_task(self, task):
        self.tasks.append(task)

    def can_fit(self, task):
        # Check if task + current utilisation <= num_processors
        potential_utilisation = self.get_utilisation() + task.computation_time / task.period
        return potential_utilisation <= self.num_processors

    """
    Returns the top k priority tasks in the cluster based on its active jobs
    """
    def get_top_priorities(self, active_tasks):
        active_task_jobs = [job for task in active_tasks for job in task.jobs if job is not None]
        unfinished_jobs = [job for job in active_task_jobs if not job.is_finished()]
        jobs_in_this_cluster = [job for job in unfinished_jobs if job.task in self.tasks]

        # return k number of jobs because that's how many we can process
        top_jobs = sorted(jobs_in_this_cluster, key=lambda job: job.get_deadline())
        top_tasks = [job.task for job in top_jobs]
        return top_tasks[:self.num_processors]

    def __str__(self):
        return f"Cluster with {self.num_processors} processors and {len(self.tasks)} tasks"
