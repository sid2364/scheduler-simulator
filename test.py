import multiprocessing
import logging
import time

# Initialize logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def worker(task_id):
    log.info(f"Worker {task_id} started.")
    time.sleep(2)  # Simulate work
    log.info(f"Worker {task_id} finished.")
    return task_id * task_id

def main():
    tasks = [1, 2, 3, 4, 5]
    with multiprocessing.Pool(processes=2) as pool:
        results = [pool.apply_async(worker, args=(task,)) for task in tasks]
        for i, res in enumerate(results):
            try:
                value = res.get(timeout=5)
                print(f"Task {tasks[i]} result: {value}")
            except multiprocessing.TimeoutError:
                print(f"Task {tasks[i]} timed out.")

if __name__ == "__main__":
    main()
