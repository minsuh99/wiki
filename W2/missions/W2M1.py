import random
import time
import multiprocessing


def work_log(work_data):
    name, duration = work_data
    print(f"Process {name} waiting {duration} seconds")
    time.sleep(duration)
    print(f"Process {name} finished.")


if __name__ == '__main__':
    num_tasks = random.randint(3, 7)
    work = [(chr(ord("A") + i), random.randint(1, 5))  for i in range(num_tasks)]
    # W2M1 예시 검증 데이터
    # work = [("A", 5), ("B", 2), ("C", 1), ("D", 3)]
    with multiprocessing.Pool(processes=2) as pool:
        results = pool.map(work_log, work)
