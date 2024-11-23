from abc import ABC
from dataclasses import dataclass
from enum import Enum
from tabnanny import verbose
from time import time, sleep
import multiprocessing

from entities import TaskSet
from multiprocessor.edfcluster import EDFCluster
from multiprocessor.partitioner import PartitionHeuristic
from utils.metrics import get_feasibility_interval, get_delta_t_tasks

MAX_ITERATIONS_LIMIT = 50_000_000  # Saves some time by exiting if we already know it's going to take too long
MAX_SECONDS_LIMIT = 30  # Likely too high, but we can adjust this later!

class MultiprocessorSchedulerType(Enum):
    GLOBAL_EDF = "Global EDF"
    PARTITIONED_EDF = "Partitioned EDF"
    EDF_K = "EDF(k)"

"""
EDF(k) Scheduler

When k is between 1 and m, we have a hybrid of partitioned and global EDF
There are k clusters, each with m/k processors, and tasks can migrate between clusters
"""
@dataclass
class EDFk(ABC):
    task_set: TaskSet
    k: int # Number of clusters
    m: int # Number of processors
    heuristic: PartitionHeuristic # Heuristic used for partitioning tasks into clusters
    clusters: list[EDFCluster] # List of clusters
    scheduler_type: MultiprocessorSchedulerType = MultiprocessorSchedulerType.EDF_K

    def __init__(self,
                 task_set: TaskSet,
                 num_clusters: int,
                 num_processors: int,
                 heuristic: PartitionHeuristic or None,
                 verbose=False,
                 force_simulation=False):
        self.task_set = task_set

        assert num_clusters <= num_processors, "Number of clusters must be less than or equal to the number of processors"
        self.k = num_clusters
        self.m = num_processors

        self.heuristic = heuristic
        self.clusters = []

        self.verbose = verbose
        self.force_simulation = force_simulation

        self.__post_init__()

    def __post_init__(self):
        self.init_clusters()

        # Partitioning indirectly verifies that utilisation
        self.is_partitioned = self.partition_taskset()

        if self.is_partitioned:
            # Validate the partitioning
            self.remove_empty_clusters()
            if self.verbose: self.pretty_print_clusters(self.clusters)

    """
    Creates m/k clusters for the EDF(k) scheduler
    
    If k = 1, this is partitioned EDF
    If k = m, this is global EDF
    Otherwise, it is a hybrid of the two, EDF(k)
    """
    def init_clusters(self):
        # Divide processors into clusters of size k
        num_clusters = self.m // self.k
        remaining_processors = self.m % self.k # Except, we also have sometimes an uneven division

        self.clusters.clear()
        for _ in range(num_clusters):
            self.clusters.append(EDFCluster(self.k))

        if remaining_processors > 0:
            self.clusters.append(EDFCluster(remaining_processors))
        if self.verbose: print(f"Initialized {len(self.clusters)} clusters")

    """
    Pretty print the clusters, their utilisation, and the tasks in each cluster
    """
    def pretty_print_clusters(self, clusters):
        if self.verbose:
            for cluster in clusters:
                tasks = [f"T{task.task_id}" for task in cluster.tasks]
                print(f"Cluster {cluster.cluster_id}: Utilisation = {cluster.get_utilisation()}"
                      f"; Tasks = {', '.join(tasks)}")

    """
    Use the heuristic to partition the task set into the clusters
    
    Handles all the cases of global EDF, partitioned EDF, and EDF(k)
    """
    def partition_taskset(self):
        # Partition the task set into the clusters based on k and m
        if self.k == self.m or self.heuristic is None:
            # Global EDF
            if len(self.clusters) == 1:
                cluster = self.clusters[0]
            else:
                raise ValueError("Global EDF should only have one cluster")

            for task in self.task_set.tasks:
                found_fit = cluster.add_task(task)
                if not found_fit:
                    return False

            return True
        else:
            # Partitioned EDF or EDF(k)
            self.clusters = self.heuristic.partition(self.task_set, self.clusters)
            if self.clusters is None:
                if self.verbose: print("Partitioning failed!")
                return False
            return True

    """
    We get the feasibility interval from each cluster
    """
    def get_simulation_interval_for_cluster(self, cluster):
        feasibility_interval = 0
        hyper_period = get_feasibility_interval(cluster.tasks)
        if hyper_period > feasibility_interval:
            feasibility_interval = hyper_period
        if self.verbose: print(f"Feasibility interval: {feasibility_interval}")
        return feasibility_interval

    @staticmethod
    def is_task_set_too_long(time_max: int) -> bool:
        return time_max > MAX_ITERATIONS_LIMIT

    """
    If any cluster is empty, remove it
    
    This might happen in case of using first-fit or next-fit heuristics
    """
    def remove_empty_clusters(self):
        self.clusters = [cluster for cluster in self.clusters if cluster.get_utilisation() != 0]

    """
    Goossens's Bound 
    
    Sufficiency condition which can be applied to each cluster (i.e., all algorithms)
    """
    def goossens_bound(self):
        if not self.is_partitioned:
            return False

        # Check Goossens's Bound for each cluster
        processors_per_cluster = self.m / self.k
        for cluster in self.clusters:
            total_utilization = sum(task.computation_time / task.period for task in cluster.tasks)
            max_utilization = max(task.computation_time / task.period for task in cluster.tasks)

            # Apply Goossens's Bound to this cluster
            bound = processors_per_cluster - (processors_per_cluster - 1) * max_utilization
            print(f"Cluster {cluster.cluster_id}: Total utilization = {total_utilization}, bound = {bound}")
            if total_utilization > bound:
                if self.verbose:
                    print(f"Cluster {cluster.cluster_id}: Total utilization {total_utilization} exceeds bound {bound}.")
                return False

        # If all clusters satisfy the bound
        return True

    """
    Verify necessary (but not sufficient) condition of density
    """
    def check_density(self):
        total_density = 0

        # Calculate total density across all tasks
        for task in self.task_set.tasks:
            density = task.computation_time / min(task.deadline, task.period)
            total_density += density

            # For Partitioned EDF, each task must have density ≤ 1
            if self.k == 1 and density > 1:
                if self.verbose: print(f"Task {task.task_id} has density > 1 and cannot fit into any processor.")
                return False

        # For Global EDF - Could move this to GlobalEDF class!
        if self.k is None or self.k == self.m:
            if total_density <= self.m:
                return True
            else:
                if self.verbose: print(f"Total density {total_density} exceeds the capacity of {self.m} processors.")
                return False

        # For EDF-k: Partition tasks and check cluster densities
        if self.k is not None:
            # Check per-cluster density
            for cluster in self.clusters:
                cluster_density = 0
                #cluster_density = sum(task.computation_time / min(task.deadline, task.period) for task in cluster.tasks)
                for task in cluster.tasks:
                    density = task.computation_time / min(task.deadline, task.period)
                    print(f"Task {task.task_id} density: {density}, computation time: {task.computation_time}, deadline: {task.deadline}, period: {task.period}")
                    cluster_density =+ density

                if cluster_density > 1.0 * cluster.num_processors:  # "Local" processor capacity
                    if self.verbose:
                        print(f"Cluster {cluster.cluster_id} density {cluster_density} exceeds "
                              f"its capacity {cluster.num_processors}.")
                    return False
            return True

        return False

    """
    Main method to determine if the task set is schedulable or not
    
    Return codes:
    0 Schedulable and simulation was required.
    1 Schedulable because some sufficient condition is met.
    2 Not schedulable and simulation was required.
    3 Not schedulable because a necessary condition does not hold.
    4 You can not tell.
    """
    def is_feasible(self):
        # If partitioning the task set into the clusters didn't work
        # This implies the utilisation of the tasks is too high for the number of processors
        if not self.is_partitioned:
            return 3

        # Check density
        # self.verbose = True
        if not self.check_density():
            print("Density condition not met")
            return 3

        # Check Goossens's Bound
        if self.goossens_bound():
            return 1

        # Else we have to simulate the task set (in parallel)
        feasible = 4  # Initialize feasible as unknown
        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            results = pool.map(self.simulate_taskset, self.clusters)

        for ret_val in results:
            if ret_val == 0:
                feasible = 0  # Schedulable, but we continue to check other clusters
            elif ret_val == 2:
                return 2  # Not schedulable, no need to check other clusters
            elif ret_val == 4:
                return 4  # Timeout/Unknown, no need to check other clusters
        return feasible


    """
    Simulate the task set and check if it is schedulable
       
    Return codes (same as is_feasible):
    0 Schedulable and simulation was required.
    1 Schedulable because some sufficient condition is met.
    2 Not schedulable and simulation was required.
    3 Not schedulable because a necessary condition does not hold.
    4 You can not tell.
    """
    def simulate_taskset(self, cluster):
        t = 0
        time_step = get_delta_t_tasks(cluster.tasks)

        time_max = self.get_simulation_interval_for_cluster(cluster)
        if self.is_task_set_too_long(time_max):
            return 4

        time_started = time()

        while t < time_max:
            if self.verbose: print(f"******* Time {t}-{t + time_step} *******")

            # Check if we're taking too long to run this function
            if time() - time_started > MAX_SECONDS_LIMIT:
                if self.verbose: print(f"Took more than {MAX_SECONDS_LIMIT} seconds, timing out!")
                return 4

            # Check for deadline misses in this cluster
            for task in cluster.tasks:
                for job in task.jobs:
                    if job.deadline_missed(t):
                        if self.verbose: print(f"Deadline missed for job {job} at time {t}, it had {job.computation_time_remaining} remaining")
                        return 2

            # Check if previous cycle jobs finished
            previous_cycle_jobs = cluster.previous_cycle_jobs
            for job in previous_cycle_jobs:
                if job.is_finished():
                    if self.verbose: print(f"{job} is finished")
                    task = job.task
                    if job in cluster.current_jobs:
                        cluster.current_jobs.remove(job)
                    task.finish_job(job)
                    if not task.has_unfinished_jobs() and task in cluster.active_tasks:
                        cluster.active_tasks.remove(task)

            # Check for new job releases in this cluster
            for task in cluster.tasks:
                job = task.release_job(t)
                if job is not None:
                    if task not in cluster.active_tasks:
                        cluster.active_tasks.append(task)
                    if job not in cluster.current_jobs:
                        cluster.current_jobs.append(job)
                    if self.verbose: print(f"Released {job} at time {t}")

            # Get the highest priority m jobs within this cluster that will each execute for one time_unit
            top_tasks = cluster.get_top_priorities(cluster.active_tasks)
            cluster.previous_cycle_jobs.clear()
            # cluster.previous_cycle_tasks.clear()
            if not top_tasks:
                if self.verbose: print(f"No tasks to schedule in cluster {cluster.cluster_id} at time {t}")
            else:
                if self.verbose: print(f"Top tasks in cluster {cluster}: {top_tasks}")
                for task in top_tasks:
                    job = task.get_first_job()
                    job.schedule(time_step)
                    if self.verbose: print(f"Scheduled {job} in cluster {cluster.cluster_id} for time {time_step}, remaining time: {job.computation_time_remaining}")

                    cluster.previous_cycle_jobs.append(job)
                    # cluster.previous_cycle_tasks.append(task) # Not needed!

            # for task in cluster.active_tasks:
            #     if self.verbose: print(f"Cluster {cluster.cluster_id} active tasks: T{task.task_id}")
            # for job in cluster.current_jobs:
            #     if self.verbose: print(f"Cluster {cluster.cluster_id} current jobs: T{job.task.task_id}-J{job.job_id}")
            # for job in cluster.previous_cycle_jobs:
            #     if self.verbose: print(f"Cluster {cluster.cluster_id} previous cycle jobs: T{job.task.task_id}-J{job.job_id}")
            # for task in cluster.previous_cycle_tasks:
            #     if self.verbose: print(f"Cluster {cluster.cluster_id} previous cycle tasks: T{task.task_id}")

            t += time_step

        return 0

    def __str__(self):
        if self.clusters is None:
            return (f"{self.scheduler_type} with {self.k} cluster(s),"
                    f" and {self.m} total processors using heuristic {self.heuristic}")
        return (f"{self.scheduler_type} with {len(self.clusters)} cluster(s),"
                f" and {self.m} total processors using heuristic {self.heuristic}")

"""
Global EDF(k) Scheduler

This is the EDF(k) scheduler where k = m, everything else is the same
"""
class GlobalEDF(EDFk):
    scheduler_type = MultiprocessorSchedulerType.GLOBAL_EDF
    def __init__(self, task_set, num_processors, verbose=False, force_simulation=False):
        super().__init__(task_set,
                         num_clusters=num_processors,
                         num_processors=num_processors,
                         heuristic=None,
                         verbose=verbose,
                         force_simulation=force_simulation)

"""
Partitioned EDF Scheduler

When k = 1, there are as many clusters as there are processors, i.e. no migration is possible
"""
class PartitionedEDF(EDFk):
    scheduler_type = MultiprocessorSchedulerType.PARTITIONED_EDF
    def __init__(self, task_set, num_processors, heuristic, verbose=False, force_simulation=False):
        super().__init__(task_set,
                         num_clusters=1,
                         num_processors=num_processors,
                         heuristic=heuristic,
                         verbose=verbose,
                         force_simulation=force_simulation)

"""
Get the scheduler object based on the algorithm type
"""
def get_multi_scheduler(algorithm: MultiprocessorSchedulerType, task_set: TaskSet, m: int, k: int, heuristic: PartitionHeuristic, verbose=False, force_simulation=False):
    if algorithm == MultiprocessorSchedulerType.GLOBAL_EDF:
        edf_scheduler = GlobalEDF(task_set, m, verbose, force_simulation)
    elif algorithm == MultiprocessorSchedulerType.PARTITIONED_EDF:
        edf_scheduler = PartitionedEDF(task_set, m, heuristic, verbose, force_simulation)
    elif algorithm == MultiprocessorSchedulerType.EDF_K:
        edf_scheduler = EDFk(task_set, k, m, heuristic, verbose, force_simulation)
    else:
        raise ValueError("Invalid algorithm type")
    return edf_scheduler