from entities import TaskSet
from helpers import is_utilisation_lte_69, is_utilisation_lte_1
from scheduler import Scheduler

"""
TODO: use feasibility interval to schedule, so [Omax, 2P + Omax) is the interval we need

TODO: check if the existence of an idle point when there are no jobs in the queue implies schedulability (in EDF)

TODO: use multiprocessing
"""


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

    def is_schedulable(self):
        if is_utilisation_lte_69(self.task_set): #only for RM/DM
            # The task set is schedulable, and you took a shortcut
            return 1

        if not is_utilisation_lte_1(self.task_set):
            # The task set is not schedulable and you took a shortcut
            return 3

        schedulable = self.schedule_taskset()
        if schedulable==1:
            # The task set is schedulable, had to simulate the execution
            return 0
        elif schedulable==0:
            # The task set is not schedulable, had to simulate the execution
            return 2
        elif schedulable==5:
            # Took too long to simulate the execution, exclude the task set
            return 5

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

    def is_schedulable(self):
        # Use utilization-based shortcut (DM has the same utilization threshold as RM)
        if is_utilisation_lte_69(self.task_set):  # utilization check for DM
            return 1  # Schedulable by utilization shortcut

        if not is_utilisation_lte_1(self.task_set):
            return 3  # Not schedulable due to utilization exceeding 1

        # Simulate scheduling tasks within the feasibility interval
        schedulable = self.schedule_taskset()

        if schedulable == 1:
            # The task set is schedulable after simulation
            return 0
        elif schedulable == 0:
            # The task set is not schedulable after simulation
            return 2
        elif schedulable == 5:
            # Simulation took too long, exclude the task set
            return 5

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

    def is_schedulable(self):
        # Try assigning priorities from lowest to highest using Audsley's algorithm, but first:
        if is_utilisation_lte_69(self.task_set):
            return 1  # Schedulable by utilization shortcut

        if not is_utilisation_lte_1(self.task_set):
            return 3  # Not schedulable due to utilization exceeding 1

        tasks = self.task_set.tasks[:]

        for task in tasks:
            task.priority = 0  # Reset priority assignments

        result = self.try_assign_lowest_priority(tasks)
        return result

    """
    Try to assign the lowest priority to a task and recurse with the remaining tasks till we find a schedulable set
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
            elif simulation_result == 5:
                # If simulation took too long, exclude the task set
                return 5
            # If not schedulable, reset priority and try the next task
            task.priority = 0

        return 2  # Not schedulable if no task can be assigned

    """
    Simulates scheduling with param 'task' at the lowest priority.
    Returns True if the set is schedulable, False if not.
    """
    def simulate_with_custom_priority(self, task, remaining_tasks):
        # Clear task state for a fresh simulation
        for t in self.task_set.tasks:
            t.clear_state()

        # Create a TaskSet with the remaining tasks, ignoring their order, and use priority attribute in scheduling
        custom_priority_task_set = TaskSet(remaining_tasks + [task])  # Add task to the set

        temp_scheduler = _CustomPriorityAudsley(custom_priority_task_set)

        schedulable = temp_scheduler.schedule_taskset()
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

    def is_schedulable(self):
        if is_utilisation_lte_69(self.task_set):  # utilization check for DM
            return 1  # Schedulable by utilization shortcut

        if not is_utilisation_lte_1(self.task_set):
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
        if len(active_tasks) == 0:
            return None

        # Filter out the active tasks to get the tasks that are not finished
        sorted_tasks = sorted(active_tasks, key=lambda x: x.get_first_job().deadline)
        if sorted_tasks is None:
            return None
        return sorted_tasks[0]

    def is_schedulable(self):
        # EDF is optimal and will always be able to schedule the tasks if the utilisation is less than 1
        # There is no need to simulate the execution, ever!
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
        pass

    def get_top_priority(self, active_tasks):
        pass

    def is_schedulable(self):
        pass