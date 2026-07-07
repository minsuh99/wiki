import multiprocessing as mp

items = ["red", "green", "blue", "black"]
queue = mp.Queue()
cnt = 0

print("pushing items to queue:")

for item in items:
    queue.put(item)
    cnt += 1
    print(f"item no: {cnt} {item}")

queue.put(None) # queue의 끝지점에 None을 추가

cnt = 0
print("popping items from queue:")
# while not queue.empty(): 
# Queue.empty()가 공식문서상 unreliable 하다고 되어 있어, None을 pop하게 되면 while문을 종료하도록 설정
# unreliable -> 해당 코드를 여러번 실행했을 때, 원하는 만큼 popping 하지 않고 종료되는 것을 확인함.
while True:
    item = queue.get()
    if item is None:
        break
    print(f"item no: {cnt} {item}")
    cnt += 1