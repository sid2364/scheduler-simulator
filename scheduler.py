from abc import ABC, abstractmethod
from dataclasses import dataclass

from entities import TaskSet
from helpers import get_delta_t, get_hyper_period


@dataclass
class Scheduler(ABC):
    task_set: TaskSet

    """
    Initialize the scheduler with the task set
    """
    def __init__(self, task_set: TaskSet, verbose=False):
        self.task_set = task_set
        self.verbose = verbose
        self.__post_init__()

    @abstractmethod
    def __post_init__(self):
        pass
    """
    Abstract method to get the top priority task, based on the scheduling algorithm
    Should be implemented in the child classes!
    """
    @abstractmethod
    def get_top_priority(self, active_tasks):
        pass

    """
    Check if the task set is schedulable
    
    Return values:
        0 The task set is schedulable and you had to simulate the execution.
        1 The task set is schedulable and you took a shortcut.
        2 The task set is not schedulable and you had to simulate the execution.
        3 The task set is not schedulable and you took a shortcut
    """
    @abstractmethod
    def is_schedulable(self):
        pass

    """
    Main scheduling algorithm
        1. Check for deadline misses
        2. Check if the previous cycle job is finished, if so, remove it from the active tasks
        3. Check for new job releases
        4. Execute the highest priority job that is released and not finished for one time_unit
            This will depend on the scheduling algorithm
        5. Exclude the task set if the simulation takes too long
        
    Return values:
        1 if all jobs finish on time till time_max
        0 if a deadline is missed

    """
    def schedule_taskset(self):
        t = 0
        time_step = get_delta_t(self.task_set)
        o_max = max([task.offset for task in self.task_set.tasks])
        time_max = o_max + 2 * get_hyper_period(self.task_set) # Omax + 2 * Hyperperiod
        # print(f"Time max: {time_max}")

        if time_max > 50000:
            # Too long to simulate!
            return 5

        current_jobs = []
        active_tasks = []

        # Since we're dealing with uni-processors, we can only execute one job at a time!
        previous_cycle_job = None
        previous_cycle_task = None

        while t < time_max:
            # Check for deadline misses
            # print(f"Time {t}-{t + time_step}:")
            for task in self.task_set.tasks:
                for job in task.jobs:
                    if job.deadline_missed(t):
                        #print(f"Deadline missed for job {job} at time {t}")
                        return 0

            # Check if the previous cycle job is finished
            # print(f"Active tasks: {[f'T{task.task_id}' for task in active_tasks]}")
            # print(f"Current jobs: {[f'{job}' for job in current_jobs]}")
            # print(f"Previous cycle job: {previous_cycle_job}")
            # print(f"Previous cycle task: {previous_cycle_task}")
            if previous_cycle_job is not None and previous_cycle_task is not None:
                if previous_cycle_job.is_finished():
                    #print(f"Finished {previous_cycle_job} at time {t}")
                    active_tasks.remove(previous_cycle_job.task)
                    current_jobs.remove(previous_cycle_job)
                    previous_cycle_task.finish_job(previous_cycle_job)
                    previous_cycle_job = None

            # Check for new job releases
            for task in self.task_set.tasks:
                job = task.release_job(t)
                if job is not None:
                    active_tasks.append(task)
                    current_jobs.append(job)

            # Execute the highest priority job that is released and not finished for one time_unit
            highest_priority_task = self.get_top_priority(active_tasks)
            if highest_priority_task is None:
                # print(f"No tasks to schedule at time {t}, idle time!\n")
                t += time_step
                continue

            # #print(f"Active tasks: {[f"T{task.task_id}" for task in active_tasks]}")
            # #print(f"Highest priority task: T{highest_priority_task.task_id}")
            current_cycle_job = highest_priority_task.get_first_job()
            if current_cycle_job is None:
                # print(f"No jobs to schedule at time {t}, idle time!\n")
                t += time_step
                continue

            current_cycle_job.schedule(time_step)

            previous_cycle_task = highest_priority_task

            if current_cycle_job == previous_cycle_job:
                pass
                # print(f"Same {current_cycle_job} running at time {t}")
            else:
                # print(f"Running {current_cycle_job} at time {t}")
                # print(f"Current cycle job which is now previous cycle job: {current_cycle_job}")
                previous_cycle_job = current_cycle_job

            t += time_step

        return 1  # All jobs finished on time till time_max
