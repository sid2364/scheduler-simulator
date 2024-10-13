from dataclasses import dataclass

@dataclass
class TaskSet:
    tasks: list


@dataclass
class Task:
    task_id = 0 # static member that keeps track of count of instances
    offset: int
    computation_time: int
    deadline: int
    period: int

    def __init__(self, offset, computation_time, deadline, period):
        Task.task_id += 1
        self.task_id = Task.task_id
        self.offset = offset
        self.computation_time = computation_time
        self.deadline = deadline
        self.period = period
        self.jobs = []
        self.job_count = 0

    def release_job(self, release_time):
        if release_time < self.offset:
            return None
        if (release_time - self.offset) % self.period == 0:
            job = Job(self, release_time)
            self.job_count += 1
            self.jobs.append(job)
            return job
    def get_first_job(self):
        if len(self.jobs) == 0:
            return None
        return self.jobs[0]
    def finish_job(self, job):
        self.jobs.remove(job)

    def __str__(self):
        return f"T{self.task_id} with period {self.period} and deadline {self.deadline}"

@dataclass
class Job:
    job_id: int
    task: Task
    computation_time_remaining: int
    release_time: int

    def __init__(self, task, release_time):
        self.job_id = task.job_count + 1
        self.task = task
        self.computation_time_remaining = task.computation_time
        self.release_time = release_time

    def deadline_missed(self, current_time):
        return current_time > self.release_time + self.task.deadline

    def schedule(self, for_time):
        # just subtract the computation time from the job, "executing" it for that time
        self.computation_time_remaining -= for_time

    def get_absolute_period(self):
        return self.task.period + self.release_time

    def is_finished(self):
        return self.computation_time_remaining <= 0 # equals should be enough but why not

    def __str__(self):
        #return f"Job {self.job_id} of Task {self.task.task_id} released at {self.release_time}"
        return f"T{self.task.task_id} - J{self.job_id}"

