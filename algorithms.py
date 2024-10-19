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
        pass

    def get_top_priority(self, active_tasks):
        pass

    def is_schedulable(self):
        pass


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