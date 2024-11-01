from entities import TaskSet
from helpers import is_utilisation_lte_1, is_utilisation_within_ll_bound, get_feasibility_interval, get_busy_period
from scheduler import Scheduler

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

    def is_schedulable(self):
        if is_utilisation_within_ll_bound(self.task_set) and not self.force_simulation: # only for RM/DM
            # The task set is schedulable, and you took a shortcut
            return 1

        if not is_utilisation_lte_1(self.task_set) and not self.force_simulation:
            # The task set is not schedulable and you took a shortcut
            return 3

        schedulable = self.schedule_taskset()
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

    def is_schedulable(self):
        # Use utilization-based shortcut (DM has the same utilization threshold as RM)
        if is_utilisation_within_ll_bound(self.task_set) and not self.force_simulation:  # utilization check for DM
            return 1  # Schedulable by utilization shortcut

        if not is_utilisation_lte_1(self.task_set) and not self.force_simulation:
            return 3  # Not schedulable due to utilization exceeding 1

        # Simulate scheduling tasks within the feasibility interval
        schedulable = self.schedule_taskset()

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

    def is_schedulable(self):
        # Try assigning priorities from lowest to highest using Audsley's algorithm, but first:
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


    """
    Try to assign the lowest priority to a task and recurse with the remaining tasks till we find a schedulable set
    
    Returns 0 if not schedulable, 1 if the task set is schedulable, 2 if the simulation took too long
    """
    def try_assign_lowest_priority(self, tasks):
        if not tasks:
            return 1  # Schedulable

        for task in tasks:
            # Clear task state for a fresh simulation
            for t in self.task_set.tasks:
                t.clear_state()

            # Check if task can be assigned the lowest priority
            remaining_tasks = [t for t in tasks if t != task]
            task.priority = len(tasks)  # Temporarily assign the lowest priority to this task

            simulation_result = self.simulate_with_custom_priority(task, remaining_tasks)
            if simulation_result == 1:
                """
                If we wanted to know the priorities assigned to the tasks, we could have used the commented code below.
                But we don't really care about the priorities, we only need to know if the task set is schedulable!
                
                # self.assigned_priorities.append(task)
                # return self.try_assign_lowest_priority(remaining_tasks)
                """
                return 1
            elif simulation_result == 2:
                # If simulation took too long, exclude the task set
                return 4
            # If not schedulable, reset priority and try the next task
            task.priority = 0

        return 0  # Not schedulable if no task can be assigned

    """
    Simulates scheduling with param 'task' at the lowest priority.
    Returns True if the set is schedulable, False if not.
    """
    def simulate_with_custom_priority(self, task, remaining_tasks):
        # Clear task state for a fresh simulation
        for t in self.task_set.tasks:
            t.clear_state()

        self.print(f"Trying to schedule task {task} with priority {task.priority}")
        self.print(f"Remaining tasks: {[t for t in remaining_tasks]}")

        # Create a TaskSet with the remaining tasks, ignoring their order, and use priority attribute in scheduling
        custom_priority_task_set = TaskSet(remaining_tasks + [task])  # Add task to the set

        temp_scheduler = _CustomPriorityAudsley(custom_priority_task_set)

        schedulable = temp_scheduler.schedule_taskset()
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
        sorted_tasks = sorted(active_tasks,
                              key=lambda task: task.priority if task.priority is not None else float('inf'))
        top_task = sorted_tasks[0]
        return top_task

    def get_simulation_interval(self):
        # Implementing priority aware busy period is out of scope,
        # but also slightly more complex than just using feasibility interval
        return get_feasibility_interval(self.task_set)

    def is_schedulable(self):
        if is_utilisation_within_ll_bound(self.task_set) and not self.force_simulation:  # utilization check for DM
            return 1  # Schedulable by utilization shortcut

        if not is_utilisation_lte_1(self.task_set) and not self.force_simulation:
            return 3  # Not schedulable due to utilization exceeding 1

        # Custom scheduler just runs based on the assigned priorities
        return self.schedule_taskset()


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

    def is_schedulable(self):
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
        self.task_queue = self.task_set.tasks
        # Initialise the queue to keep track of incoming tasks
        # This queue is not necessarily a priority queue, it's just a representation of the order he tasks will execute in
        pass

    def get_top_priority(self, active_tasks):
        # Round Robin is a preemptive algorithm, so we just return the first task in the list
        if len(active_tasks) == 0:
            return None
        self.print("Queue: ", [t.task_id for t in self.task_queue])
        # Iterate through job_queue and return the first task which is active
        for task in self.task_queue:
            if task in active_tasks:
                t = self.task_queue.pop(0) # Remove from the "front"
                self.task_queue.append(t) # Add to the "back"
                return t

    def get_simulation_interval(self):
        # Can't use busy period here
        return get_feasibility_interval(self.task_set)

    def is_schedulable(self):
        # Round Robin is not optimal (at all), so we have to simulate the execution, no shortcuts here
        ret_val = self.schedule_taskset()
        if ret_val == 1:
            # The task set is schedulable, and you had to simulate the execution.
            return 0
        elif ret_val == 0:
            # The task set is not schedulable, and you had to simulate the execution.
            return 2
        elif ret_val == 2:
            # Took too long to simulate the execution, exclude the task set.
            return 4
