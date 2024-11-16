from dataclasses import dataclass

@dataclass
class TaskSet:
    tasks: list


@dataclass
class Task:
    task_id = 0  # static member that keeps track of count of instances
    offset: int
    computation_time: int
    deadline: int
    period: int
    priority: int = None  # Only used in Audsley's algorithm!

    def __init__(self, offset: int, computation_time: int, deadline: int, period: int):
        Task.task_id += 1
        self.task_id = Task.task_id
        self.offset = offset
        self.computation_time = computation_time
        self.deadline = deadline
        self.period = period
        self.jobs = []
        self.job_count = 0
        self.priority = 0  # Default to 0, only used in Audsley's algorithm!

    def release_job(self, release_time: int):
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

    def has_unfinished_jobs(self):
        return any([not job.is_finished() for job in self.jobs])

    def finish_job(self, job):
        self.jobs.remove(job)

    def __str__(self):
        return f"T{self.task_id} with period {self.period}, deadline {self.deadline}, priority {self.priority}"

    # These are just so that we can add Tasks to sets
    def __hash__(self):
        return hash(self.task_id)  # Use task_id as the hash key

    def __eq__(self, other):
        if isinstance(other, Task):
            return self.task_id == other.task_id
        return False


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
        print(f"Current time: {current_time}, release time: {self.release_time}, deadline: {self.get_deadline()}")
        return current_time > self.release_time + self.task.deadline and not self.is_finished()

    def get_deadline(self):
        return self.release_time + self.task.deadline

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

    # These are just so that we can add Tasks to sets
    def __hash__(self):
        return hash(self.job_id + self.task.task_id)  # Use task_id as the hash key

    def __eq__(self, other):
        # Ensure equality is based on both job_id and the associated task
        if isinstance(other, Job):
            return self.job_id == other.job_id and self.task.task_id == other.task.task_id
        return False

