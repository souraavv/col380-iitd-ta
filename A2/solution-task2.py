import sys 
import networkx as nx
from tqdm import tqdm
from pathlib import Path
from pprint import pprint
sys.setrecursionlimit(1000000)

if __name__ == '__main__':
    graph = None
    n, m = None, None
    test_id, k, p = None, None, None
    if len(sys.argv) < 4:
        print("Missing argument test_id, k, p")
        exit(0)
    else:
        test_id = int(sys.argv[1])
        k = int(sys.argv[2]) + 2
        p = int(sys.argv[3])
        print (f'For test: {test_id}, k = {k - 2}, p = {p}')

    G = nx.Graph()
    n, m = 0, 0
    with open(f'test{test_id}/test-input-{test_id}.txt', 'r') as f:
        line = f.readline()
        n, m = [int(x) for x in line.split(' ')]
        print (f' N = {n}, M = {m}')
        while True:
            line = f.readline()
            if not line:
                break 
            line = line.split(' ')[:-1]
            adj_list = [int(x) for x in line]
            node_idx = int(line[0])
            assert(len(adj_list[2:]) == int(adj_list[1]))
            for v in adj_list[2:]:
                G.add_edge(node_idx, v)
            del line 
            del adj_list
        f.close()

    def find_max_truss_possible():
        min_k, max_k = 0, n + 1
        limit_k = max_k
        while min_k <= max_k:
            mid = (min_k + max_k) // 2 
            print (f"Testing for mid: {mid}")
            H = nx.algorithms.core.k_truss(G, mid)
            if len(H.nodes()) == 0:
                max_k = mid - 1
            else:
                limit_k = mid
                min_k = mid + 1    
        print ("Max truss can be of ", limit_k)
    

    output_files = [f'task2_output{test_id}.txt', f'task2_output{test_id}_verbose.txt']
    ''' Setup files '''  
    for file in output_files:
        path = Path(f'test{test_id}/{file}')        
        if not path.is_file():
            open(f'test{test_id}/{file}', 'x')        
        with open(f'test{test_id}/{file}', 'r+') as f: 
            f.truncate(0)

    ''' setup info file '''
    info_file = Path(f'test{test_id}/task2_info.txt')
    if not info_file.is_file():
        open(f'test{test_id}/task2_info.txt', 'x')
    with open(f'test{test_id}/task2_info.txt', 'r+') as f:
        f.write(f'k = {k - 2}, p = {p}')
        f.close()

    store = []

    H = nx.algorithms.core.k_truss(G, k)  # find all the k-groups  
    groups = list(H.subgraph(c) for c in nx.connected_components(H)) # Get all the components
    no_of_groups:int = nx.number_connected_components(H)
    print (f'For {k - 2}-group, there are total {no_of_groups} connected-components')
    candidate_influencer = dict()
    groups_connected_to_inflencer = dict()

    def get_influencer_vertices():
        for group_id, group in enumerate(groups):
            visited = {}
            for u in group.nodes():
                if u not in visited:
                    visited[u] = True 
                    if u not in candidate_influencer:
                        candidate_influencer[u] = 0
                        groups_connected_to_inflencer[u] = set()

                    candidate_influencer[u] += 1 
                    groups_connected_to_inflencer[u].add(group_id)

                for v in G[u]:
                    if v not in visited:
                        visited[v] = True
                        if v not in candidate_influencer:
                            candidate_influencer[v] = 0
                            groups_connected_to_inflencer[v] = set()
                        candidate_influencer[v] += 1
                        groups_connected_to_inflencer[v].add(group_id)

        influencer_vertices = []
        
        print (f'Candidate for influencer nodes : {len(candidate_influencer)}')
        for u, influencing_to in candidate_influencer.items():
            if influencing_to >= p:
                influencer_vertices.append(u)
        print (f'Only {len(influencer_vertices)} are actually!')
        return influencer_vertices 
    
    influencer_vertices = get_influencer_vertices()
    no_of_influencer_vertices = len(influencer_vertices)
    
    '''
    Output to file format:
    number of influencer vertices
    influencer vertex
    Vertices of all the groups which are influenced
    '''
    print (f'Writing output to the files...')
    for file in tqdm(output_files):
        print (f'Writing to the file {file}')
        with open(f'test{test_id}/{file}', 'a+') as f: 
            if len(influencer_vertices) == 0:
                f.write('0') # if no influecer vertex is found
            else:
                f.write(f'{no_of_influencer_vertices}\n') # number of influencer vertices
                for influencer in tqdm(influencer_vertices):
                    end_with = '\n' if 'verbose' in file else ' '
                    f.write(f'{influencer}{end_with}') # Influencer vertex
                    if 'verbose' in file:
                        for group_id in groups_connected_to_inflencer[influencer]:
                            nodes = groups[group_id].nodes()
                            nodes = [str(v) for v in nodes]
                            f.write(' '.join(nodes)) # all nodes which are present in the groups connected to influecer vertex
                            f.write(' ')
                        f.write('\n')
                        
            f.close()
                
