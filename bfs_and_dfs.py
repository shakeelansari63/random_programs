from queue import Queue
graph = {
    'a': ['b', 'e'],
    'b': ['c', 'd', 'g', 'f'],
    'c': ['i', 'k'],
    'd': ['g'],
    'e': ['d', 'g'],
    'f': ['i', 'j'],
    'g': ['h'],
    'h': ['j', 'f'],
    'i': ['k'],
    'j': ['i'],
    'k': ['e']
}

bfs_output = []
dfs_output = []

# Interim Variables
bfs_visited = {}
for node in graph.keys():
    bfs_visited[node] = False

dfs_visited = {}
for node in graph.keys():
    dfs_visited[node] = False

# Queue for BFS
bfs_queue = Queue()

# BFS Function
def bfs(node):
    # Take current Node and Set it as visited and add to Queue
    bfs_visited[node] = True
    bfs_queue.put(node)

    # Check queue till there is no item in queue
    while not bfs_queue.empty():
        cur_node = bfs_queue.get()

        # Create Output Traversal
        bfs_output.append(cur_node)

        # Check children of node and set them to visited and Add to queue if they weren't already visited
        for child in graph[cur_node]:
            if not bfs_visited[child]:
                bfs_visited[child] = True
                bfs_queue.put(child)

def dfs(node):
    # Change current Note as Visited
    dfs_visited[node] = True
    
    # Append it to output
    dfs_output.append(node)

    # Recursively traverse the childrren
    for child in graph[node]:
        if not dfs_visited[child]:
            dfs(child)

bfs('a')
dfs('a')

print(f"BFS: {bfs_output}")
print(f"DFS: {dfs_output}")