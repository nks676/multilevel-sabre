import networkx as nx
from collections import deque
from qiskit.transpiler import CouplingMap
from qiskit.transpiler.passes import DenseLayout
from qiskit.transpiler import PassManager
from qiskit import QuantumCircuit

def is_line(G):
    degree_counts = dict(G.degree())
    line_nodes = [node for node, degree in degree_counts.items() if degree == 1]

    if len(line_nodes) == 2 and all(degree == 2 for degree in degree_counts.values() if degree != 1):
        return True, line_nodes
    
    else:
        return False, None


def is_star_like(G):
    degree_counts = dict(G.degree())
    center_node = [node for node, degree in degree_counts.items() if degree >= len(G)/2]

    if len(center_node) >= 1 :
        return True, center_node
    else:
        return  False, None

def build_dfs_tree(graph, root):
    """
    Build a tree from a connected undirected graph using DFS.
    
    Args:
        graph: A NetworkX undirected graph
        root: The node to use as the root of the tree
    
    Returns:
        A NetworkX directed graph representing the DFS tree
    """
    # Ensure the root node exists in the graph
    if root not in graph:
        raise ValueError(f"Root node {root} not found in graph")
    
    # Create a new directed graph for the tree
    tree = nx.DiGraph()
    
    # Add the root node to the tree
    tree.add_node(root)
    
    # Keep track of visited nodes
    visited = {root}
    
    # Run DFS starting from the root
    dfs_visit(graph, tree, root, visited)
    
    return tree

def dfs_visit(graph, tree, current, visited):
    """
    Helper function for DFS traversal.
    
    Args:
        graph: Original undirected graph
        tree: Tree being built
        current: Current node being visited
        visited: Set of already visited nodes
    """
    for neighbor in graph.neighbors(current):
        if neighbor not in visited:
            # Mark as visited
            visited.add(neighbor)
            
            # Add to the tree
            tree.add_node(neighbor)
            tree.add_edge(current, neighbor)
            
            # Recursively visit the neighbor
            dfs_visit(graph, tree, neighbor, visited)

def find_diameter_path(graph):
    """
    Find a path with length equal to the diameter of a connected, undirected, 
    unweighted graph using two passes of BFS.
    
    Parameters:
    graph (networkx.Graph): The input connected undirected graph.
    
    Returns:
    list: Nodes in the path with length equal to the diameter.
    int: Length of the diameter (number of edges in the path).
    """
    if not graph.nodes():
        return [], 0
    
    # Step 1: Pick any node and find the farthest node from it
    start_node = list(graph.nodes())[0]  # Start with any node
    farthest_node, _, predecessors = bfs_with_path(graph, start_node)
    
    # Step 2: Find the farthest node from the previously found farthest node
    end_node, distances, predecessors = bfs_with_path(graph, farthest_node)
    
    # Step 3: Reconstruct the path from farthest_node to end_node
    path = reconstruct_path(predecessors, farthest_node, end_node)
    
    return path, len(path) - 1  # Return path and diameter (number of edges)

def bfs_with_path(graph, start_node):
    """
    Perform BFS from a start node and track distances and predecessors.
    
    Returns:
    node: The farthest node from start_node.
    dict: Distances from start_node to all other nodes.
    dict: Predecessors dictionary for path reconstruction.
    """
    distances = {start_node: 0}
    predecessors = {start_node: None}
    queue = deque([start_node])
    max_distance = 0
    farthest_node = start_node
    
    while queue:
        current = queue.popleft()
        
        for neighbor in graph.neighbors(current):
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                
                # Update farthest node if this one is farther
                if distances[neighbor] > max_distance:
                    max_distance = distances[neighbor]
                    farthest_node = neighbor
                    
                predecessors[neighbor] = current
                queue.append(neighbor)
    
    return farthest_node, distances, predecessors

def reconstruct_path(predecessors, start, end):
    """
    Reconstruct the path from start to end using predecessors dictionary.
    """
    path = [end]
    current = end
    
    while current != start:
        current = predecessors[current]
        path.append(current)
    
    return path[::-1]  # Reverse to get path from start to end

def find_longest_path(graph):
    """
    Find a long path in a graph using DFS tree, diameter finding, and refinement.
    
    Args:
        graph: Original undirected graph
        starting_node: Node to use as root for DFS tree (optional)
    
    Returns:
        list: A refined long path in the graph
    """
    # Choose a starting node if not provided
#    path,_=find_diameter_path(graph)
    longest_path=[]
    for start_node in graph.nodes:
        dfs_tree=build_dfs_tree(graph,start_node)
        candidate_path=nx.dag_longest_path(dfs_tree)
        if len(candidate_path)>len(longest_path):
            longest_path=candidate_path
    
    return longest_path

def find_next_center(coupling_graph, node, extended_set):
    next_node = None
    best_extend_set = extended_set.copy()

    for neighbor in coupling_graph.neighbors(node):
        new_extend = extended_set | {neighbor} | set(coupling_graph.neighbors(neighbor))
        if len(new_extend) > len(best_extend_set):
            best_extend_set = new_extend
            next_node = neighbor

    return next_node, best_extend_set

def insert_node_midway(coupling_graph, path, extend_set, visited_path, num_of_nodes):
    """
    Attempt to repeatedly insert nodes into the middle of the path until the extended set
    (path nodes + their neighbors) has at least num_of_nodes elements.

    Parameters:
    - coupling_graph: networkx Graph representing device topology
    - path: current path (list of nodes)
    - extend_set: current extended set (nodes in path + their neighbors)
    - visited_path: set of nodes already in path
    - num_of_nodes: target size for the extended set

    Returns:
    - updated path
    - updated extended set
    - updated visited path
    - True if any insertion was made, False if stuck
    """
    made_progress = False

    while len(extend_set) < num_of_nodes:
        candidates = list(extend_set - visited_path)
        best_candidate = None
        best_extend = extend_set

        for candidate in candidates:
            candidate_extend = extend_set | {candidate} | set(coupling_graph.neighbors(candidate))
            if len(candidate_extend) > len(best_extend):
                best_candidate = candidate
                best_extend = candidate_extend

        if best_candidate is None:
            break  # No more progress can be made

        # Try inserting the candidate after a neighbor in the path
        inserted = False
        for i in range(len(path) - 1):
            if path[i] in coupling_graph.neighbors(best_candidate):
                path = path[:i + 1] + [best_candidate] + path[i + 1:]
                inserted = True
                break
        if not inserted:
            path.append(best_candidate)

        extend_set = best_extend
        visited_path.add(best_candidate)
        made_progress = True

    return path, extend_set, visited_path, made_progress


def deform_star(coupling_graph, num_of_nodes):
    best_area = (float('inf'), None, None)

    for starting_node in coupling_graph.nodes:
#        print(starting_node)
        path = [starting_node]
        extend_set = set(path) | set(coupling_graph.neighbors(starting_node))
        if len(extend_set) >= num_of_nodes:
            return (1, extend_set, path)

        start, end = starting_node, starting_node
        visited_path = set(path)

        while len(extend_set) < num_of_nodes:
#            print(len(extend_set))
            next_node_start, extend_start = find_next_center(coupling_graph, start, extend_set)
            next_node_end, extend_end = find_next_center(coupling_graph, end, extend_set)

            if next_node_start is None and next_node_end is None:
                path, extend_set, visited_path, success = insert_node_midway(
                    coupling_graph, path, extend_set, visited_path, num_of_nodes
                )
                start, end = path[0], path[-1]
                if not success:
                    break
                continue

            if not next_node_start is None and ((next_node_end is None) or len(extend_start) >= len(extend_end)):
                path = [next_node_start] + path
                extend_set = extend_start
                start = next_node_start
                visited_path.add(start)
            
            else:
                path = path + [next_node_end]
                extend_set = extend_end
                end = next_node_end
                visited_path.add(end)

        if len(extend_set) >= num_of_nodes and len(path) < best_area[0]:
            best_area = (len(path), extend_set, path)

    return best_area

def add_missing_index(mapping,unused_program_index):
    current_index=0
    for k in mapping.keys():
        if mapping[k]==-1:
            mapping[k]=unused_program_index[current_index]
            current_index+=1


def initial_embedding(coupling_graph, circuit):
    coupling_g=nx.Graph()
    coupling_g.add_edges_from(coupling_graph)
    circuit_g=nx.Graph()
    circuit_list=[(x.qubits[0]._index,x.qubits[1]._index) for x in circuit.data if len(x.qubits)==2]
    circuit_g.add_edges_from(circuit_list)

    isline,edge_nodes=is_line(circuit_g)
    isStarLike,centers=is_star_like(circuit_g)
    number_of_physical_qubit=coupling_g.number_of_nodes()
    number_of_program_qubits=circuit_g.number_of_nodes()
    mapping={i:-1 for i in range(number_of_physical_qubit)}
    remaining_physical_index=[i for i in range(number_of_physical_qubit)]

    if isline:
        longest_device_path=find_longest_path(coupling_g)
        circuit_path_list=find_diameter_path(circuit_g)[0]
        if len(longest_device_path)>=number_of_program_qubits:
            for i in range(number_of_program_qubits):
                mapping[circuit_path_list[i]]=longest_device_path[i]
                remaining_physical_index.remove(longest_device_path[i])
            
            add_missing_index(mapping,remaining_physical_index)
            return mapping
        else:
            queue = deque([(i,i) for i in longest_device_path])
            neighbor_on_path={i:[] for i in longest_device_path}
            visited={i:False for i in range(number_of_physical_qubit)}
            for i in longest_device_path:
                visited[i]=True
            num_missing_index=number_of_program_qubits-len(longest_device_path)
            
            while num_missing_index>0:
                expand_node,path_node=queue.popleft()
                for neighbor in coupling_g.neighbors(expand_node):
                    if not visited[neighbor]:
                        neighbor_on_path[path_node].append(neighbor)
                        queue.append((neighbor,path_node))
                        num_missing_index-=1
                        visited[neighbor]=True
            
            deformed_path=[]
            for i in longest_device_path:
                deformed_path=deformed_path+[i]+neighbor_on_path[i]

            for i in range(number_of_program_qubits):
                mapping[circuit_path_list[i]]=deformed_path[i]
                remaining_physical_index.remove(deformed_path[i])
            
            add_missing_index(mapping,remaining_physical_index)
            return mapping
    
    if isStarLike:
        _, _, center_path= deform_star(coupling_g,number_of_program_qubits)
        print(center_path)
        first_center=None
        ordered_nodes=deque()
        for q0,q1 in circuit_list:
            if q0 in centers:
                first_center=q0
                break
            if q1 in centers:
                first_center=q1
                break
        
        for q0,q1 in circuit_list:
            if not q0 in ordered_nodes and q0!=first_center:
                ordered_nodes.append(q0)
            if not q1 in ordered_nodes and q1!=first_center:
                ordered_nodes.append(q1)
        
        mapping[first_center]=center_path[0]
        remaining_physical_index.remove(center_path[0])

        for next_node in center_path:
            for neighbor in coupling_g.neighbors(next_node):
                if neighbor in remaining_physical_index:
                    if len(ordered_nodes)>0:
                        program_node=ordered_nodes.popleft()
                        mapping[program_node]=neighbor
                        remaining_physical_index.remove(neighbor)

                    else:
                        break
        
        add_missing_index(mapping,remaining_physical_index)
        return mapping
    
    coupling_map=CouplingMap(coupling_graph)
    dense_layout = DenseLayout(coupling_map=coupling_map)
    pm = PassManager(dense_layout)
    new_circuit = pm.run(circuit)
    layout = dense_layout.property_set['layout']
    physical_candidate_list=[]
    for _,physical in layout.get_virtual_bits().items():
        physical_candidate_list.append(physical)

    for program,physical in layout.get_virtual_bits().items():
        mapping[program._index]=physical
        remaining_physical_index.remove(physical)
    
    add_missing_index(mapping, remaining_physical_index)
    return mapping