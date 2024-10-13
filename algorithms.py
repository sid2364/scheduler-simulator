from entities import TaskSet
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

"""
Round Robin
"""
class RoundRobin(Scheduler):
    def __post_init__(self):
        pass
    def get_top_priority(self, active_tasks):
        pass
    # TODO!