import time
import multiprocessing as mp


def print_continent(continent="Asia"):
    print("The name of continent is : ", continent)


if __name__ == "__main__":
    names = ["America", "Europe", "Africa"]
    processes = []
    process = mp.Process(target=print_continent)
    processes.append(process)
    process.start()

    for name in names:
        process = mp.Process(target=print_continent, args=(name,))
        processes.append(process)
        process.start()

    for p in processes:
        p.join()