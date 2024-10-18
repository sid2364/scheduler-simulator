from entities import TaskSet
from scheduler import Scheduler
from helpers import get_delta_t, get_hyper_period, is_utilisation_lt_69, is_utilisation_gt_1


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
        if is_utilisation_lt_69(self.task_set): #only for RM/DM
            # The task set is schedulable, and you took a shortcut
            pass
            #return 1 # this is wrong because it's not always schedulable!!! FIXME

        if is_utilisation_gt_1(self.task_set):
            # The task set is not schedulable and you took a shortcut
            return 3

        schedulable = self.schedule()
        if schedulable:
            # The task set is schedulable, had to simulate the execution
            return 0
        else:
            # The task set is not schedulable, had to simulate the execution
            return 2

"""
Audsley
"""
class Audsley(Scheduler):
    def get_top_priority(self, active_tasks):
        pass

    def is_schedulable(self):
        pass

    def __post_init__(self):
        pass


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
        pass


"""
Earliest Deadline First
"""
class EarliestDeadlineFirst(Scheduler):
    def __post_init__(self):
        pass

    def get_top_priority(self, active_tasks):
        if len(active_tasks) == 0:
            return None

        # Filter out the active tasks to get the tasks that are not finished
        sorted_tasks = sorted(active_tasks, key=lambda x: x.get_first_job().deadline)
        if sorted_tasks is None:
            return None
        return sorted_tasks[0]

    def is_schedulable(self):
        pass


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