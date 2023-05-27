import sys 
import os
import struct
import random 
from tqdm import tqdm
from networkx.generators.random_graphs import erdos_renyi_graph
import time

break_edges = 1
graph = None
deg = None


home_dir: str = os.path.expanduser('~')
scratch_dir: str = os.path.join(home_dir, 'scratch')


def generate_sorted_random_numbers(length, start, end):
    random_numbers = [random.randint(start, end) for _ in range(length)]
    random_numbers.sort()
    return random_numbers

def generate_random_withoutlib(nodes, degree_lower, degree_upper):
    print (f'Generating graph without any library use..')
    global graph, deg 
    graph = [set() for i in range(nodes)]
    deg = [0 for i in range(nodes)]

    for node in tqdm(range(0, nodes)):
        d = random.randint(degree_lower, degree_upper)
        childs = generate_sorted_random_numbers(d, 0, nodes - 1)
        for child in childs: 
            graph[node].add(child) 

        for child in graph[node]:
            graph[child].add(node)
    
    print (f'compute degree')
    for i in tqdm(range(nodes)):
        graph[i] = list(graph[i])
        deg[i] = len(graph[i])
    
    print (f'Generated graph of total number of edges = {sum(deg) / 2} and node = {nodes}')
    

def generate_random_graph(nodes, comp):
    global graph
    global deg 
    print ("Started generating graph...")
    local_nodes = nodes // comp
    offset = 0
    total_edges = 0
    print (local_nodes * comp)
    for _ in tqdm(range(comp)):
        p = random.uniform(0.1, 0.4)
        print (f"Generating {local_nodes} number of nodes with edge prob of {p}")
        g = erdos_renyi_graph(local_nodes, p)
        edges_count = len(g.edges())
        print (f'Offset {offset}')
        total_edges += edges_count
        for (u, v) in g.edges():
            u += offset
            v += offset
            assert(u < nodes)
            assert(v < nodes)
            if (u not in graph[v]) and (v not in graph[u]):
                graph[u].append(v)
                graph[v].append(u)
                deg[u] += 1
                deg[v] += 1
        offset += local_nodes
        del g
    
    ''' Add edges randomly across components'''
    extra_edges = 0;
    for _ in tqdm(range(nodes // 10)):
        comp_id1 = random.randint(0, comp)
        comp_id2 = random.randint(0, comp)
        u = comp_id1 * local_nodes + random.randint(0, local_nodes)
        v = comp_id2 * local_nodes + random.randint(0, local_nodes)
        if (u < nodes and v < nodes and u != v):
            if (u not in graph[v]) and (v not in graph[u]):
                extra_edges += 1
                graph[u].append(v)
                graph[v].append(u)
                deg[u] += 1
                deg[v] += 1
    
    for u in range(nodes):
        before = len(graph[u])
        graph[u] = list(set(graph[u]))
        after = len(graph[u])
        if before != after: 
            print ("issue!")

    print (f'Total number {extra_edges} extra edges are added across different component')
    for adj_list in graph:
        adj_list.sort()
    print ("Total edges: ", total_edges)

def write_binary_file(filename, graph):
    with open(filename, 'wb') as f:
        f.write(struct.pack('i', len(graph)))
        for node in graph:
            f.write(struct.pack('i', len(node)))
            for edge in node:
                f.write(struct.pack('i', edge))

def read_binary_file(filename):
    meta = []
    with open('header.txt', 'r') as f: 
        lines = f.readlines()
        for line in lines:
            meta.append(int(line))
    
    with open(filename, 'rb') as f: 
        f.seek(meta[1])
        for _ in range((meta[4] - meta[1]) // 4):
            val = f.read(4)
            print (int.from_bytes(val, 'little'), end=' ')
        print ()

def read_text_file(filename):
    pref = 0
    with open ('header.txt', 'w') as f1: 
        with open(filename, 'r') as f:
            lines = f.readlines()
            for line in lines: 
                size = len(line.split(' '))
                f1.write(str(pref) + '\n')
                pref += size * 4
            del lines
        f.close()
    f1.close()

def convert(filename, outname):
    with open (outname, 'wb') as f1:
        with open(filename, 'r') as f:
            while True:
                line = f.readline()
                if not line:
                    break
                words = line.split(' ')
                for word in words:
                    if (word != '\n'):
                        word = int(word)
                        f1.write(word.to_bytes(4, byteorder='little'))
                del words
                del line
        f.close()
    f1.close()

def make_txt_input(graph,filename):
    n = len(graph)
    m = 0
    for i in range(n):
        m += len(graph[i])
    m //= 2
    with open (filename, 'w') as f:
        f.write(str(n) + ' ' + str(m) + '\n')
        for i in range(n):
            f.write(str(i) + ' ' + str(len(graph[i])) + ' ')
            for j in range(len(graph[i])):
                f.write(str(graph[i][j]) + ' ')
            f.write('\n')
        f.close()
        
def generate_header(outname, deg):
    with open (outname, 'wb') as f:
        srt = 8
        f.write(srt.to_bytes(4, byteorder='little'))
        for i in range(1,len(deg)):
            srt += (deg[i-1] + 2) * 4
            f.write(srt.to_bytes(4, byteorder='little'))
            print(" ")

def get_degree(test_case):
    deg = []
    with open(os.path.join(scratch_dir, f'test{test_case}/test-input-{test_case}.txt', 'r')) as f:
        which = -1
        while True:
            line = f.readline()
            which += 1
            if (which == 0):
                continue
            if not line:
                break
            line = line.split(' ')[:-1]
            deg.append(int(line[1]))
        f.close()
    return deg

def main():
    if len(sys.argv) < 3:
        print("Missing argument (test_id, number of nodes, number of components)")
        exit(0)
    test_case = sys.argv[1]
    nodes = int(sys.argv[2]) # Total number nodes in graph 
    comp = int(sys.argv[3])

    global graph
    graph = [[] for i in range(nodes)]
    global deg
    deg = [0 for _ in range(nodes)]

    print (f'Test case: {test_case}, nodes: {nodes}')
    if not ( os.path.exists(os.path.join(scratch_dir, f'test{test_case}'))):
        os.mkdir(os.path.join(scratch_dir, f'test{test_case}'))

    print (f'Building the graph...')
    t1 = time.time()
    generate_random_graph(nodes, comp)
    degree_lower, degree_upper = 100, 300
    t2 = time.time()
    delta = t2 - t1
    print ("Total time taken to generate graph : ", delta / 60)

    print ('Making the txt file...')
    t1 = time.time()
    make_txt_input(graph, os.path.join(scratch_dir, f'test{test_case}/test-input-{test_case}.txt'))
    del graph
    t2 = time.time()
    delta = t2 - t1
    print ("Total time taken to make text file: ", delta / 60)

    print ('Making binary file...')
    t1 = time.time()
    convert(os.path.join(scratch_dir, f'test{test_case}/test-input-{test_case}.txt'),os.path.join(scratch_dir, f'test{test_case}/test-input-{test_case}.gra'))
    t2 = time.time()
    delta = t2 - t1
    print ("Total time taken to generate binary file", delta / 60)

    print ('Making the header file...')
    #test_case = 10
    #deg = get_degree(test_case)
    t1 = time.time()
    generate_header(os.path.join(scratch_dir, f'test{test_case}/test-header-{test_case}.dat'), deg)
    t2 = time.time()
    delta = t2 - t1 
    del deg 
    print ("Total time in making header file ", delta / 60)

if __name__ == '__main__':
    main()



