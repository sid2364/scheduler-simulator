from entities import TaskSet
from helpers import is_utilisation_lte_1, is_utilisation_within_ll_bound, get_feasibility_interval, get_busy_period
from scheduler import Scheduler

"""
Deadline Monotonic
"""
class DeadlineMonotonic(Scheduler):
    def __post_init__(self):
        self.sorted_tasks = sorted(self.task_set.tasks, key=lambda x: x.deadline)

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
        if is_utilisation_within_ll_bound(self.task_set) and not self.force_simulation:  # utilization check for DM
            return 1  # Schedulable by utilization shortcut

        if not is_utilisation_lte_1(self.task_set) and not self.force_simulation:
            return 3  # Not schedulable due to utilization exceeding 1

        # Simulate scheduling tasks within the feasibility interval
        schedulable = self.simulate_taskset()

        if schedulable == 1:
            # The task set is schedulable after simulation
            return 0
        elif schedulable == 0:
            # The task set is not schedulable after simulation
            return 2
        elif schedulable == 2:
            # Simulation took too long, exclude the task set
            return 4


"""
Earliest Deadline First
"""
class EarliestDeadlineFirst(Scheduler):
    def __post_init__(self):
        pass

    """
    get_top_priority() won't be used because we never get to the point of scheduling, 
    we can tell if it's schedulable by the utilisation
    """
    def get_top_priority(self, active_tasks):
        raise NotImplementedError("Earliest Deadline First does not use get_top_priority(), you should never see this!")

    def get_simulation_interval(self):
        raise NotImplementedError("Earliest Deadline First does not use get_simulation_interval(), you should never see this!")

    def is_feasible(self):
        # EDF is optimal and will always be able to schedule the tasks if the utilisation is less than 1
        # There is no need to simulate the execution, ever!

        # BUT since we should not include task sets if they take too long, we will exclude this if lcm of periods is too large
        # just as we exclude other task sets for other algorithms, this allows us to compare the algorithms fairly
        # if self.is_task_set_too_long():
        #     return 4

        # If not, then we can just check the utilisation
        if is_utilisation_lte_1(self.task_set):
            # The task set is schedulable, and you took a shortcut
            return 1
        else:
            # The task set is not schedulable and you took a shortcut
            return 3

"""
Round Robin
"""
class RoundRobin(Scheduler):
    def __post_init__(self):
        self.task_queue = sorted(self.task_set.tasks, key=lambda x: x.deadline)
        # Initialise the queue to keep track of incoming tasks, can initially be sorted by deadline
        # This queue is not necessarily a priority queue, it's just a representation of the order the tasks will execute in

    def get_top_priority(self, active_tasks):
        # Round Robin is a preemptive algorithm, so we just return the first task in the list
        if len(active_tasks) == 0:
            return None
        # Iterate through job queue and return the first task which is active
        for task in self.task_queue:
            if task in active_tasks:
                self.task_queue.remove(task) # Remove from the "front"
                self.task_queue.append(task) # Add to the "back"
                return task

    def get_simulation_interval(self):
        # Can't use busy period here
        return get_feasibility_interval(self.task_set)

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

        schedulable = self.simulate_taskset()
        if schedulable == 1:
            # The task set is schedulable, had to simulate the execution
            return 0
        elif schedulable == 0:
            # The task set is not schedulable, had to simulate the execution
            return 2
        elif schedulable == 2:
            # Took too long to simulate the execution, exclude the task set
            return 4

"""
Audsley
"""
class Audsley(Scheduler):
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