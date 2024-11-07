from entities import TaskSet
from helpers import is_utilisation_lte_1, is_utilisation_within_ll_bound, get_feasibility_interval, get_busy_period, \
    calculate_worst_case_response_time, get_first_idle_point
from scheduler import Scheduler

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
        if len(active_tasks) == 0:
            return None

        # Filter out the active tasks to get the tasks that are not finished
        sorted_tasks = [task for task in self.sorted_tasks if task in active_tasks]
        if sorted_tasks is None:
            return None
        return sorted_tasks[0]

    def get_simulation_interval(self):
        time_max = get_feasibility_interval(self.task_set)
        if self.is_task_set_too_long(time_max):
            return get_busy_period(self.task_set)
        return time_max

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
                return 2  # Not schedulable due to deadline miss in WCRT analysis

        # If WCRT analysis passes, the task set is schedulable
        return 0

"""
Earliest Deadline First
"""
class EarliestDeadlineFirst(Scheduler):
    def __post_init__(self):
        pass

    """
    EDF is a fixed job priority algorithm, so we use the priority of the job, not the task!
    """
    def get_top_priority(self, active_tasks):
        # Gather all jobs from active tasks
        jobs = [job for task in active_tasks for job in task.jobs if job is not None]

        # Return the task associated with the job that has the earliest deadline, or None if no jobs are available
        return min(jobs, key=lambda job: job.get_deadline()).task if jobs else None

    def get_simulation_interval(self):
        # Either use feasibility interval or busy period if the interval is too long
        feasibility_interval = get_first_idle_point(self.task_set)
        if self.is_task_set_too_long(feasibility_interval):
            return get_busy_period(self.task_set)
        return feasibility_interval

    def is_feasible(self):
        # EDF is optimal and will always be able to schedule the tasks if the utilisation is less than 1
        # But since we're dealing with constrained systems, we need to simulate the execution to be sure!

        if not is_utilisation_lte_1(self.task_set):
            # Utilization exceeds 1, so the task set is immediately unschedulable
            return 3

        result = self.simulate_taskset()
        #result = self.verify_deadlines()
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
        # Initialize the time quantum
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
        if len(active_tasks) == 0:
            return None

        # Filter out the active tasks to get the tasks that are not finished
        sorted_tasks = [task for task in self.sorted_tasks if task in active_tasks]
        if sorted_tasks is None:
            return None
        return sorted_tasks[0]

    def get_simulation_interval(self):
        time_max = get_feasibility_interval(self.task_set)
        if self.is_task_set_too_long(time_max):
            return get_busy_period(self.task_set)
        return time_max

    def is_feasible(self):
        if is_utilisation_within_ll_bound(self.task_set) and not self.force_simulation: # only for RM/DM
            # The task set is schedulable, and you took a shortcut
            return 1

        if not is_utilisation_lte_1(self.task_set) and not self.force_simulation:
            # The task set is not schedulable and you took a shortcut
            return 3

        # WCRT analysis for each task
        for task in self.sorted_tasks:
            wcrt = calculate_worst_case_response_time(task, self.sorted_tasks)
            if wcrt > task.deadline:  # Check against period as implicit deadline
                self.print(f"Task {task.task_id} is not schedulable; WCRT = {wcrt} exceeds deadline = {task.deadline}")
                return 2  # Not schedulable due to deadline miss in WCRT analysis

        # If WCRT analysis passes, the task set is schedulable
        return 0

"""
Audsley
"""
class Audsley(Scheduler):
    def __post_init__(self):
        self.assigned_priorities = {}  # task_id: priority
        self.print("Initialized Audsley Scheduler.")

    def get_top_priority(self, active_tasks: list):
        # In Audsley, priorities are assigned iteratively, so this method may not be used.
        return None

    def get_simulation_interval(self):
        raise NotImplementedError("Audsley does not use get_simulation_interval.")

    def is_feasible(self):
        # Reset assigned priorities
        self.assigned_priorities.clear()

        # Utilization shortcut only for implicit-deadline task sets
        if all(task.deadline == task.period for task in self.task_set.tasks):
            if is_utilisation_within_ll_bound(self.task_set) and not self.force_simulation:
                self.print("Schedulable by utilization shortcut (LL bound).")
                return 1  # Schedulable by utilization shortcut

        # Check total utilization
        if not is_utilisation_lte_1(self.task_set) and not self.force_simulation:
            self.print("Not schedulable: Utilization exceeds 1.")
            return 3  # Not schedulable due to utilization exceeding 1

        # Copy of tasks to assign priorities
        tasks_to_assign = self.task_set.tasks[:]

        # Assign priorities from lowest to highest (highest numerical value to lowest priority)
        for priority in range(len(tasks_to_assign), 0, -1):
            task_found = False
            for task in tasks_to_assign:
                # Temporarily assign the current priority to the task
                temp_priorities = self.assigned_priorities.copy()
                temp_priorities[task.task_id] = priority

                # Sort tasks by temporary priority (lower number = higher priority)
                sorted_tasks = sorted(
                    self.task_set.tasks,
                    key=lambda x: temp_priorities.get(x.task_id, float('inf'))
                )

                # Perform WCRT analysis
                wcrt = calculate_worst_case_response_time(task, sorted_tasks)

                if wcrt <= task.deadline:
                    # Assign the priority
                    self.assigned_priorities[task.task_id] = priority
                    self.print(f"Assigned priority {priority} to Task {task.task_id}")
                    tasks_to_assign.remove(task)
                    task_found = True
                    break  # Move to the next priority level

            if not task_found:
                # No task could be assigned the current priority without violating deadlines
                self.print("No schedulable priority assignment found.")
                return 2  # Not schedulable

        self.print("All tasks have been assigned priorities successfully.")
        return 0  # Schedulable

    def simulate_taskset(self):
        # Simulation is not required for Audsley if WCRT analysis is used
        return 0

class AudsleyOld(Scheduler):
    def __post_init__(self):
        self.sorted_tasks = self.task_set.tasks  # Start without sorting
        self.assigned_priorities = []  # Store tasks that have been assigned priorities

    def get_top_priority(self, active_tasks):
        # Return the task with the highest assigned priority (lowest number means highest priority)
        if len(active_tasks) == 0:
            return None

        # Sort the active tasks based on their assigned priority
        active_tasks_sorted = sorted(active_tasks, key=lambda task: task.priority)
        top_task = active_tasks_sorted[0]
        return top_task

    def get_simulation_interval(self):
        raise NotImplementedError("Audsley does not directly (!) use get_simulation_interval(), you should never see this!")

    def is_feasible(self):
        # Reset assigned priorities to ensure a fresh start
        self.assigned_priorities.clear()

        # Try assigning priorities from lowest to highest using Audsley's algorithm
        if is_utilisation_within_ll_bound(self.task_set) and not self.force_simulation:
            return 1  # Schedulable by utilization shortcut

        if not is_utilisation_lte_1(self.task_set) and not self.force_simulation:
            return 3  # Not schedulable due to utilization exceeding 1

        tasks = self.task_set.tasks[:]

        for task in tasks:
            task.priority = 0  # Reset priority assignments

        result = self.try_assign_lowest_priority(tasks)
        if result == 1:
            # The task set is schedulable after simulation
            return 0
        elif result == 0:
            # The task set is not schedulable after simulation
            return 2
        elif result == 2:
            # Simulation took too long, exclude the task set
            return 4

    def try_assign_lowest_priority(self, tasks):
        # Helper list to track temporary assigned priorities within the recursion
        temp_priorities = self.assigned_priorities.copy()

        if not tasks:
            return 1  # Schedulable, since no remaining tasks!

        for task in tasks:
            # Skip tasks that have already been assigned a priority
            if task in temp_priorities:
                continue

            # Clear state only for tasks not in temp_priorities
            for t in self.task_set.tasks:
                if t not in temp_priorities:
                    t.clear_state(self.assigned_priorities)

            # Try assigning the lowest priority to the current task
            remaining_tasks = [t for t in tasks if t != task]
            task.priority = len(tasks)  # Temporarily assign the lowest priority

            simulation_result = self.simulate_with_custom_priority(task, remaining_tasks)
            if simulation_result == 1:
                # If schedulable, add task to temp_priorities
                temp_priorities.append(task)
                # Recurse with the remaining tasks
                result = self.try_assign_lowest_priority(remaining_tasks)
                if result == 1:
                    # If recursion confirms schedulability, merge temp_priorities
                    self.assigned_priorities = temp_priorities
                    return 1
                else:
                    # Remove task from temp_priorities if subsequent tasks are not schedulable
                    temp_priorities.remove(task)

            # Reset the task priority if not schedulable
            task.priority = 0

        return 0  # Return not schedulable if no task can be assigned

    def simulate_with_custom_priority(self, task, remaining_tasks):
        # Ensure simulate_with_custom_priority is only called for tasks without assigned priorities
        if task in self.assigned_priorities:
            return 1  # Task already has an assigned priority, should not reach here

        # Clear state for tasks not yet in assigned_priorities
        for t in self.task_set.tasks:
            if t not in self.assigned_priorities:
                t.clear_state(self.assigned_priorities)

        self.print(f"Trying to schedule task {task} with priority {task.priority}")
        self.print(f"Remaining tasks: {[t for t in remaining_tasks]}")

        # Create a TaskSet with remaining tasks and the current task
        custom_priority_task_set = TaskSet(remaining_tasks + [task])

        temp_scheduler = _CustomPriorityAudsley(custom_priority_task_set)
        schedulable = temp_scheduler.is_feasible()
        self.print(f"Simulation result: {schedulable}")
        return schedulable

class _CustomPriorityAudsley(Scheduler):
    def __post_init__(self):
        # Tasks will be sorted by the assigned priorities here, so no initial sorting will apply
        pass

    def get_top_priority(self, active_tasks):
        if len(active_tasks) == 0:
            return None

        # Sort tasks by their manually assigned priorities (lower priority number means higher importance)
        sorted_tasks = sorted(active_tasks, key=lambda task: task.priority if task.priority is not None else float('inf'))
        top_task = sorted_tasks[0]
        return top_task

    def get_simulation_interval(self):
        # Implementing priority-aware busy period is out of scope,
        # but also slightly more complex than just using feasibility interval
        time_max = get_feasibility_interval(self.task_set)
        if self.is_task_set_too_long(time_max):
            return get_busy_period(self.task_set)
        return time_max

    def is_feasible(self):
        if is_utilisation_within_ll_bound(self.task_set) and not self.force_simulation:  # utilization check for DM
            return 1  # Schedulable by utilization shortcut

        if not is_utilisation_lte_1(self.task_set) and not self.force_simulation:
            return 3  # Not schedulable due to utilization exceeding 1

        # Custom scheduler just runs based on the assigned priorities
        return self.simulate_taskset()