import sys 
import networkx as nx
from pathlib import Path
from tqdm import tqdm
sys.setrecursionlimit(10000000)
import os 

home_dir: str = os.path.expanduser('~')
scratch_dir: str = os.path.join(home_dir, 'scratch')


def print_file(output_file):
    print ("Printing Output file:")
    with open(f'test{test_id}/{output_file}', 'r') as f:
        lines = f.readlines()
        for line in lines: 
            print (line, end='')
    print ('\n')

if __name__ == '__main__':
    graph = None
    n, m = None, None
    start_k, end_k = None, None 
    test_id = None 
    # par_dir = f'/COL380/A2'
    if len(sys.argv) < 3:
        print("Missing argument (test_id, start_k, end_k)")
        exit(0)
    else:
        test_id = int(sys.argv[1])
        start_k = int(sys.argv[2]) + 2 # Since group is asked 
        end_k = int(sys.argv[3]) + 2

    G = nx.Graph()
    n, m = 0, 0
    with open(os.path.join(scratch_dir, f'test{test_id}/test-input-{test_id}.txt'), 'r') as f:
        line = f.readline()
        n, m = [int(x) for x in line.split(' ')]
        print (f' N = {n}, M = {m}')
        while True:
            line = f.readline()
            if not line:
                break 
            line = line.split(' ')[:-1]
            node_idx = int(line[0])
            adj_list = list(map(lambda u: int(u), line))
            assert(len(adj_list[2:]) == adj_list[1])
            for v in adj_list[2:]:
                G.add_edge(node_idx, v)
            del line 
            del adj_list
        f.close()
            
    output_files = [f'task1_output{test_id}.txt', f'task1_output{test_id}_verbose.txt']
        
    for file in output_files:
        path = Path(os.path.join(scratch_dir, f'test{test_id}/{file}'))
        info_file = Path(os.path.join(scratch_dir, f'test{test_id}/task1_info.txt'))
        if not path.is_file():
            open(os.path.join(scratch_dir, f'test{test_id}/{file}'), 'x')
        if not info_file.is_file():
            open(os.path.join(scratch_dir, f'test{test_id}/task1_info.txt'), 'x')

        with open(os.path.join(scratch_dir, f'test{test_id}/{file}'), 'r+') as f: 
            f.truncate(0)
        
        with open(os.path.join(scratch_dir, f'test{test_id}/task1_info.txt'), 'r+') as f:
            f.write(f'start_k = {start_k - 2}, end_k = {end_k - 2}\n')
            f.close()

    for k in tqdm(range(start_k, end_k + 1)):
        print (f"Running for k = {k}")
        H = nx.algorithms.core.k_truss(G, k)
        print (f'Finding groups...')
        groups = list(H.subgraph(c) for c in nx.connected_components(H))
        print (f'Finding connected components..')
        no_of_groups = nx.number_connected_components(H)
        for file in output_files:
            print (f'Writing to the {file} ...')
            with open(os.path.join(scratch_dir, f'test{test_id}/{file}'), 'a+') as f: 
                verbose = 'verbose' in file
                if verbose:
                    if no_of_groups >= 1:
                        f.write(str(1) + '\n')
                        if verbose:
                            f.write(str(no_of_groups) + '\n')
                            for idx, group in enumerate(groups):
                                nodes = list(set(list(group.nodes())))
                                nodes.sort()
                                if len(nodes) == 1:
                                    continue
                                nodes = [str(v) for v in nodes]
                                f.write(' '.join(nodes))
                                if idx + 1 != len(groups):
                                    f.write('\n')
                    else:
                        f.write(str(0))
                    if k != end_k:
                        f.write('\n')
                else:
                    if no_of_groups >= 1:
                        f.write(str(1))
                    else:
                        f.write(str(0))
                    if k != end_k:
                        f.write(' ')
                    
                f.close()
        del H
        del groups
                
