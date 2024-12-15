from abc import ABC
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from dataclasses import dataclass
from enum import Enum
from tabnanny import verbose
from time import time, sleep
import multiprocessing

from entities import TaskSet
from multiprocessor.edfcluster import EDFCluster
from multiprocessor.partitioner import PartitionHeuristic
from utils.metrics import get_feasibility_interval, get_delta_t_tasks, get_first_idle_point

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
                 num_workers: int,
                 verbose=False,
                 force_simulation=False):
        self.task_set = task_set

        assert num_clusters <= num_processors, "Number of clusters must be less than or equal to the number of processors"
        self.k = num_clusters
        self.m = num_processors
        # print(f"Number of clusters: {self.k}, Number of processors: {self.m}")

        self.heuristic = heuristic
        self.clusters = []

        self.verbose = verbose
        self.force_simulation = force_simulation

        self.num_workers = num_workers
        # print(f"Number of workers: {self.num_workers}")

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
    
    If k = m, this is partitioned EDF
    If k = 1, this is global EDF
    Otherwise, it is a hybrid of the two, EDF(k)
    """
    def init_clusters(self):
        # Divide processors into clusters of size k
        if self.k == 1:
            # Global EDF
            self.clusters.append(EDFCluster(self.m))

        elif self.k == self.m:
            # Partitioned EDF, create m clusters
            for _ in range(self.m):
                self.clusters.append(EDFCluster(1))
        else:
            # EDF(k)
            num_clusters = self.m // self.k
            # print(f"Number of clusters: {num_clusters}")
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
        if self.k == 1 or self.heuristic is None:
            # Global EDF
            # print("Clusters=", self.clusters)
            if len(self.clusters) == 1:
                cluster = self.clusters[0]
            else:
                raise ValueError("Global EDF should only have 'one' theoretical cluster")

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
    We get the feasibility interval for each cluster
    """
    def get_simulation_interval_for_cluster(self, cluster):
        feasibility_interval = get_feasibility_interval(cluster.tasks)
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
    Calculate m_min for the EDF-k scheduler
    
    This is a necessary condition for the schedulability of the task set
    """
    def calculate_m_min(self):
        # Sort tasks by decreasing utilisation
        sorted_tasks = sorted(self.task_set.tasks, key=lambda t: t.computation_time / t.period, reverse=True)

        # Calculate cumulative utilisations
        utilisations = [task.computation_time / task.period for task in sorted_tasks]
        cumulative_utilisations = [sum(utilisations[:i + 1]) for i in range(len(utilisations))]

        # Initialize m_min to absurdly large value
        m_min = float('inf')

        # Iterate over possible k values
        for k in range(1, len(sorted_tasks) + 1):
            U_taskset_k = cumulative_utilisations[k - 1]  # U(tau_k)
            U_taskset_k_plus_1 = sum(utilisations[k:]) if k < len(utilisations) else 0  # U(tau^(k+1))

            # Avoid division by zero for fully loaded k
            if U_taskset_k >= 1:
                continue

            # Calculate m_min for this k
            m_k = (k - 1) + U_taskset_k_plus_1 / (1 - U_taskset_k)
            m_min = min(m_min, m_k)

        return m_min

    """
    Utilisation Bound 
    
    U(i) ≤ m/k - (m/k - 1) * max(Ui) 
    
    This condition has been adapted from Global EDF to EDF(k)
    
    Sufficiency condition which can be applied to each cluster (i.e., all algorithms)
    How it works:
    - If the total utilisation of the tasks in the cluster is less than the number of processors
    - Then the cluster is schedulable
    - Otherwise, it is not schedulable
    """
    def check_utilisation_bound(self):
        if not self.is_partitioned:
            return False

        # Check Utilisation Bound for each cluster
        processors_per_cluster = self.m / self.k
        # print(f"Processors per cluster: {processors_per_cluster}")
        for cluster in self.clusters:
            total_utilization = sum(task.computation_time / task.period for task in cluster.tasks)
            max_utilization = max(task.computation_time / task.period for task in cluster.tasks)
            # print(f"Total utilization: {total_utilization}, max utilization: {max_utilization}")

            # Apply Utilisation Bound to this cluster
            bound = processors_per_cluster - (processors_per_cluster - 1) * max_utilization
            # print(f"Bound: {bound}")
            if self.verbose: print(f"Cluster {cluster.cluster_id}: Total utilization = {total_utilization}, bound = {bound}")
            if total_utilization > bound:
                if self.verbose:
                    print(f"Cluster {cluster.cluster_id}: Total utilization {total_utilization} exceeds bound {bound}.")
                return False
        # print("All clusters satisfy the bound")
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

            # For Partitioned EDF, each task must have density <= 1
            if self.k == self.m and density > 1:
                if self.verbose: print(f"Task {task.task_id} has density > 1 and cannot fit into any processor.")
                return False

        # For Global EDF - Could move this to GlobalEDF class!
        if self.k is None or self.k == 1:
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
                    if self.verbose: print(f"Task {task.task_id} density: {density}, computation time: {task.computation_time}, deadline: {task.deadline}, period: {task.period}")
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
        if not self.check_density():
            if self.verbose: print("Density condition not met")
            return 3

        # Check Utilisation Bound
        if not self.check_utilisation_bound():
            if self.verbose: print("Utilisation bound condition not met")
            return 3

        # Check that we have the minimum number of processors
        m_min = self.calculate_m_min()
        if m_min > self.m:
            if self.verbose: print(f"m_min {m_min} is greater than m {self.m}")
            return 3

        # Else we have to simulate the task set (in parallel)
        feasible = 4  # Initialize feasible as unknown
        # with multiprocessing.Pool(processes=self.num_workers) as pool:
        #     results = pool.map(self.simulate_taskset, self.clusters)
        #
        # for ret_val in results:
        #     if ret_val == 0:
        #         feasible = 0  # Schedulable, but we continue to check other clusters
        #     elif ret_val == 2:
        #         return 2  # Not schedulable, no need to check other clusters
        #     elif ret_val == 4:
        #         return 4  # Timeout/Unknown, no need to check other clusters

        # print(f"Using {self.num_workers} workers, with {len(self.clusters)} clusters")
        # User multiprocessing.Process instead of multiprocessing.Pool
        # with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
        #     futures = [executor.submit(self.simulate_taskset, cluster) for cluster in self.clusters]
        #     for future in as_completed(futures):
        #         ret_val = future.result()
        #         if ret_val == 0:
        #             feasible = 0
        #         elif ret_val == 2:
        #             return 2
        #         elif ret_val == 4:
        #             return 4

        # Do everything sequentially
        for cluster in self.clusters:
            ret_val = self.simulate_taskset(cluster)
            if ret_val == 0:
                feasible = 0
            elif ret_val == 2:
                return 2
            elif ret_val == 4:
                return 4

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
        if self.verbose: print(f"Time max: {time_max}")

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
    def __init__(self, task_set, num_processors, num_workers, verbose=False, force_simulation=False):
        super().__init__(task_set,
                         num_clusters=1,
                         num_processors=num_processors,
                         heuristic=None,
                         num_workers=num_workers,
                         verbose=verbose,
                         force_simulation=force_simulation)


    def verify_pessimistic_sufficient_condition(self):
        # Check if the total utilisation of the tasks in the task set is less than m - (m - 1) * max(Ui)
        total_utilisation = sum(task.computation_time / task.period for task in self.task_set.tasks)
        max_utilisation = max(task.computation_time / task.period for task in self.task_set.tasks)
        processors = self.m
        bound = processors - (processors - 1) * max_utilisation
        if total_utilisation <= bound:
            return True

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
            if self.verbose: print("Density condition not met")
            return 3

        # Check pessimistic sufficient condition
        if self.verify_pessimistic_sufficient_condition():
            return 1

        # Check Utilisation Bound
        if self.check_utilisation_bound():
            return 1

        # Else we have to simulate the task set (in parallel)
        feasible = 4  # Initialize feasible as unknown

        # Can use multiprocessing.cpu_count()
        # with multiprocessing.Pool(processes=2) as pool:
        #     results = pool.map(self.simulate_taskset, self.clusters)
        #
        # for ret_val in results:
        #     if ret_val == 0:
        #         feasible = 0  # Schedulable, but we continue to check other clusters
        #     elif ret_val == 2:
        #         return 2  # Not schedulable, no need to check other clusters
        #     elif ret_val == 4:
        #         return 4  # Timeout/Unknown, no need to check other clusters

        # Note: This logic is not used because we realised parallelising cluster scheduling is not useful
        # as the overhead of creating new processes is too high for the small amount of work done in each process

        # Also we are using parallel processing in the simulate_taskset method at taskset level
        # Since daemon processes are not allowed to create child processes, we can't use multiprocessing.Pool again here

        # Do everything sequentially
        for cluster in self.clusters:
            ret_val = self.simulate_taskset(cluster)
            if ret_val == 0:
                feasible = 0
            elif ret_val == 2:
                return 2
            elif ret_val == 4:
                return 4

        return feasible

"""
Partitioned EDF Scheduler

When k = 1, there are as many clusters as there are processors, i.e. no migration is possible
"""
class PartitionedEDF(EDFk):
    scheduler_type = MultiprocessorSchedulerType.PARTITIONED_EDF
    def __init__(self, task_set, num_processors, heuristic, num_workers, verbose=False, force_simulation=False):
        super().__init__(task_set,
                         num_clusters=num_processors,
                         num_processors=num_processors,
                         heuristic=heuristic,
                         num_workers=num_workers,
                         verbose=verbose,
                         force_simulation=force_simulation)

    def get_simulation_interval_for_cluster(self, cluster):
        # Use get_feasibility_interval() to get the first idle point in the task set for this cluster
        return get_feasibility_interval(cluster.tasks)

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
        if not self.check_density():
            if self.verbose: print("Density condition not met")
            return 3

        # Check Utilisation Bound
        if not self.utilisation_bound_partitioned():
            if self.verbose: print("Utilisation Bound not met")
            return 3

        # Else we have to simulate the task set (in parallel)
        feasible = 4  # Initialize feasible as unknown

        # Note: This logic is not used because we realised parallelising cluster scheduling is not useful
        # as the overhead of creating new processes is too high for the small amount of work done in each process

        # Also we are using parallel processing in the simulate_taskset method at taskset level
        # Since daemon processes are not allowed to create child processes, we can't use multiprocessing.Pool again here

        # with multiprocessing.Pool(processes=self.num_workers) as pool:
        #     results = pool.map(self.simulate_taskset, self.clusters)
        #
        # for ret_val in results:
        #     if ret_val == 0:
        #         feasible = 0  # Schedulable, but we continue to check other clusters
        #     elif ret_val == 2:
        #         return 2  # Not schedulable, no need to check other clusters
        #     elif ret_val == 4:
        #         return 4  # Timeout/Unknown, no need to check other clusters

        # Do everything sequentially
        for cluster in self.clusters:
            ret_val = self.simulate_taskset(cluster)
            if ret_val == 0:
                feasible = 0
            elif ret_val == 2:
                return 2
            elif ret_val == 4:
                return 4

        return feasible

    def utilisation_bound_partitioned(self):
        # Check that every cluster has total utilisation less than 1
        for cluster in self.clusters:
            total_utilisation = sum(task.computation_time / task.period for task in cluster.tasks)
            if total_utilisation > 1:
                if self.verbose: print(f"Cluster {cluster.cluster_id} has total utilisation {total_utilisation} > 1")
                return False
        return True


"""
Get the scheduler object based on the algorithm type
"""
def get_multi_scheduler(algorithm: MultiprocessorSchedulerType, task_set: TaskSet, m: int, k: int, heuristic: PartitionHeuristic, num_workers: int, verbose=False, force_simulation=False):
    if algorithm == MultiprocessorSchedulerType.GLOBAL_EDF:
        edf_scheduler = GlobalEDF(task_set, m, num_workers, verbose, force_simulation)
    elif algorithm == MultiprocessorSchedulerType.PARTITIONED_EDF:
        edf_scheduler = PartitionedEDF(task_set, m, heuristic, num_workers,  verbose, force_simulation)
    elif algorithm == MultiprocessorSchedulerType.EDF_K:
        edf_scheduler = EDFk(task_set, k, m, heuristic, num_workers, verbose, force_simulation)
    else:
        raise ValueError("Invalid algorithm type")
    return edf_scheduler