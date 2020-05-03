import time

from multiprocessing import Process

def segfault(pid, skip=False):
    try:
        time.sleep(10)

        if not skip:
            import ctypes
            ctypes.string_at(0)
        print(f'Process id: {pid} pass')
    except Exception:
        print(f'Process id: {pid} failure caught')

# Failing process
p1 = Process(target=segfault, args=(1,))
p1.start()
time.sleep(2)

# Passing process
p2 = Process(target=segfault, args=(2, True,))
p2.start()

time.sleep(2)

processes = [p1, p2]

for i in range(3):
    for id, process in enumerate(processes):
        print(f'Process: {process} Process id: {id} Alive: {process.is_alive()}\nExit code: {process.exitcode}')
        if process.exitcode and process.exitcode < 0:
            print(f'CRASH DETECTED - Process: {process} Process id: {id}')

    print('\n')
    time.sleep(5)

print('DONE')
