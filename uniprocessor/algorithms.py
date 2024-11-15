from entities import TaskSet
from utils.metrics import is_utilisation_lte_1, get_feasibility_interval, get_busy_period, \
    calculate_worst_case_response_time, get_first_idle_point, calculate_worst_case_response_time_with_priorities
from uniprocessor.scheduler import Scheduler

OPTIMAL_ALGORITHM = "edf"

"""
Return an instance of the scheduler based on the algorithm selected
"""
def get_uni_scheduler(algorithm: str, task_set: TaskSet, verbose: bool, force_simulation: bool):
    algorithm = algorithm.lower()
    if algorithm == 'rm':
        return RateMonotonic(task_set, verbose, force_simulation)
    elif algorithm == 'dm':
        return DeadlineMonotonic(task_set, verbose, force_simulation)
    elif algorithm == 'audsley':
        return Audsley(task_set, verbose, force_simulation)
    elif algorithm == 'edf':
        return EarliestDeadlineFirst(task_set, verbose, force_simulation)
    elif algorithm == 'rr':
        return RoundRobin(task_set, verbose, force_simulation)
    else:
        print("Invalid algorithm selected!") # Won't happen because of argparse but why not
        return None

"""
Return an instance of EDF
"""
def get_optimal_scheduler(task_set: TaskSet, verbose: bool, force_simulation: bool) -> Scheduler:
    return get_uni_scheduler(OPTIMAL_ALGORITHM, task_set, verbose, force_simulation)

"""
Deadline Monotonic
"""
class DeadlineMonotonic(Scheduler):
    def __post_init__(self):
        # self.sorted_tasks = sorted(self.task_set.tasks, key=lambda x: x.deadline)
        self.sorted_tasks = sorted(
            self.task_set.tasks,
            key=lambda x: (x.deadline, x.period)
        )

    def get_top_priority(self, active_tasks):
        raise NotImplementedError("DM does not use get_top_priority!")

    def get_simulation_interval(self):
        raise NotImplementedError("DM does not use get_simulation_interval!")

    def is_feasible(self):
        # Use utilization-based shortcut (DM has the same utilization threshold as RM)
        # if is_utilisation_within_ll_bound(self.task_set) and not self.force_simulation:  # utilization check for DM
        #     return 1  # Schedulable by utilization shortcut

        if not is_utilisation_lte_1(self.task_set) and not self.force_simulation:
            return 3  # Not schedulable due to utilization exceeding 1

        # Simulate scheduling tasks within the feasibility interval, but we never need to for DM!
        # schedulable = self.simulate_taskset()

        # WCRT analysis for each task, same as RM
        for task in self.sorted_tasks:
            wcrt = calculate_worst_case_response_time(task, self.sorted_tasks)
            if wcrt > task.deadline:  # Check against period as implicit deadline
                self.print(f"Task {task.task_id} is not schedulable; WCRT = {wcrt} exceeds deadline = {task.deadline}")
                return 3  # Not schedulable due to deadline miss in WCRT analysis

        # If WCRT analysis passes, the task set is schedulable
        return 1

"""
Earliest Deadline First
"""
class EarliestDeadlineFirst(Scheduler):
    def __post_init__(self):
        pass

    """
    EDF is a fixed job priority algo, so we use the priority of the job, not the task!
    """
    def get_top_priority(self, active_tasks):
        # Get all jobs from active tasks
        jobs = [job for task in active_tasks for job in task.jobs if job is not None]

        # Return the task associated with the job that has the earliest deadline!
        return min(jobs, key=lambda job: job.get_deadline()).task if jobs else None

    def get_simulation_interval(self):
        # Either use feasibility interval or busy period if the interval is too long
        return get_first_idle_point(self.task_set)

    def is_feasible(self):
        # EDF is optimal and will always be able to schedule the tasks if the utilisation is less than 1
        # But since we're dealing with constrained systems, we need to simulate the execution to be sure!

        if not is_utilisation_lte_1(self.task_set) and not self.force_simulation:
            # Utilization exceeds 1, so the task set is immediately unschedulable
            return 3

        result = self.simulate_taskset()
        if result == 1:
            # Both utilization check and deadline check pass
            return 0  # Schedulable
        else:
            return 2  # Not schedulable due to deadline miss!

"""
Round Robin
"""
class RoundRobin(Scheduler):
    def __post_init__(self):
        # Initialize the time quantum using a trick to get the average computation time! :)
        avg_computation_time = sum(task.computation_time for task in self.task_set.tasks) / len(self.task_set.tasks)
        self.quantum = int(avg_computation_time)

        # Initialize the ready queue and quantum remaining for each task
        self.ready_queue = []
        self.quantum_remaining = {}

        # Initialize a set to keep track of active tasks
        self.active_task_set = set()

    def get_top_priority(self, active_tasks):
        # Remove tasks that are no longer active
        for task in list(self.ready_queue):
            if task not in active_tasks:
                self.ready_queue.remove(task)
                self.quantum_remaining.pop(task.task_id, None)

        # Add new active tasks to the ready queue
        for task in active_tasks:
            if task not in self.ready_queue:
                self.ready_queue.append(task)
                self.quantum_remaining[task.task_id] = self.quantum

        # If the ready queue is empty, return None
        if not self.ready_queue:
            return None

        # Return the task at the front of the ready queue
        return self.ready_queue[0]

    def get_simulation_interval(self):
        feasibility_interval = get_feasibility_interval(self.task_set)
        if self.is_task_set_too_long(feasibility_interval):
            return get_busy_period(self.task_set)
        return feasibility_interval

    def is_feasible(self):
        # Round Robin is not optimal (at all), so we have to simulate the execution, no shortcuts here
        ret_val = self.simulate_taskset()
        if ret_val == 1:
            # The task set is schedulable, and you had to simulate the execution.
            return 0
        elif ret_val == 0:
            # The task set is not schedulable, and you had to simulate the execution.
            return 2
        elif ret_val == 2:
            # Took too long to simulate the execution, exclude the task set.
            return 4

"""
Rate Monotonic
"""
class RateMonotonic(Scheduler):
    def __post_init__(self):
        self.sorted_tasks = sorted(self.task_set.tasks, key=lambda x: x.period)

    def get_top_priority(self, active_tasks):
        raise NotImplementedError("RM does not use get_top_priority!")

    def get_simulation_interval(self):
        raise NotImplementedError("RM does not use get_simulation_interval!")

    def is_feasible(self):
        if not is_utilisation_lte_1(self.task_set) and not self.force_simulation:
            # The task set is not schedulable and you took a shortcut
            return 3

        # WCRT analysis for each task
        for task in self.sorted_tasks:
            wcrt = calculate_worst_case_response_time(task, self.sorted_tasks)
            if wcrt > task.deadline:
                self.print(f"Task {task.task_id} is not schedulable; WCRT = {wcrt} exceeds deadline = {task.deadline}")
                return 3  # Not schedulable due to deadline miss in WCRT analysis

        # If WCRT analysis passes, the task set is schedulable
        return 1 # We never have to "simulate", since we check the WCRT

"""
Audsley
"""
class Audsley(Scheduler):
    def __init__(self, task_set: TaskSet, verbose=False, force_simulation=False):
        super().__init__(task_set, verbose, force_simulation)
        self.assigned_priorities = {}

    def __post_init__(self):
        self.assigned_priorities = {}

    def get_top_priority(self, active_tasks: list):
        raise NotImplementedError("Audsley does not use get_top_priority!")

    def get_simulation_interval(self):
        raise NotImplementedError("Audsley does not use get_simulation_interval!")

    def is_feasible(self):
        if not is_utilisation_lte_1(self.task_set) and not self.force_simulation:
            return 3  # Not schedulable due to utilization exceeding 1

        # Initialize priorities to zero (unassigned) for each task
        self.assigned_priorities = {task.task_id: 0 for task in self.task_set.tasks}

        # Make a copy of the tasks to work with
        tasks_to_assign = self.task_set.tasks[:]

        # Start assigning priorities from lowest to highest
        priority_level = len(tasks_to_assign)  # Start with the lowest priority level

        while tasks_to_assign:
            task_found = False  # Track if a task can be assigned this priority
            for task in tasks_to_assign:
                # Temporarily assign the current lowest priority to this task
                self.assigned_priorities[task.task_id] = priority_level

                # Check if the task is schedulable with this priority level
                if self.is_task_schedulable_with_priority(task, self.assigned_priorities):
                    # Lock in this priority for the task
                    tasks_to_assign.remove(task)
                    priority_level -= 1  # Move to the next higher priority level
                    task_found = True
                    break  # Move on to the next priority level

                # Reset priority if task is not schedulable at this level
                self.assigned_priorities[task.task_id] = 0

            if not task_found:
                # If no task could be assigned the current lowest priority level, it's unschedulable
                return 2  # Not schedulable, but here since it could "recurse" many levels, we consider it a simulation

        return 0  # All tasks successfully assigned priorities; schedulable

    def is_task_schedulable_with_priority(self, task, temp_priorities):
        # Sort tasks by temporary priorities (lower number = higher priority)
        sorted_tasks = sorted(
            self.task_set.tasks,
            key=lambda x: temp_priorities.get(x.task_id, float('inf'))
        )

        sorted_tasks = self.task_set.tasks
        # order these by the priorities in temp_priorities
        sorted_tasks = sorted(sorted_tasks, key=lambda x: temp_priorities.get(x.task_id, 0))

        # Calculate the worst-case response time for the given task
        wcrt = calculate_worst_case_response_time_with_priorities(task, sorted_tasks, temp_priorities)

        # Return True if the worst-case response time is within the task's deadline
        return wcrt <= task.deadline
