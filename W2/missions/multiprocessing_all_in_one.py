import multiprocessing as mp
from multiprocessing import Process, Queue
import time
import queue

def process_func(q1, q2):
    while True:
        try:
            data = q1.get_nowait()
        except queue.Empty:
            break

        process = mp.current_process()
        print(data)
        time.sleep(0.5)
        q2.put(f"{data} is done by {process.name}")


if __name__ == '__main__':
    tasks_to_accomplish = Queue()
    tasks_that_are_done = Queue()
    processes = [Process(
        target=process_func, args=(tasks_to_accomplish, tasks_that_are_done)) for _ in range(4)
        ]

    for i in range(10):
        tasks_to_accomplish.put(f'Task no {i}')

    for process in processes:
        process.start()

    for process in processes:
        process.join()
    
    while not tasks_that_are_done.empty():
        print(tasks_that_are_done.get())