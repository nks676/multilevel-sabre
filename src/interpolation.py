import networkx as nx
import numpy as np
from scipy.optimize import linear_sum_assignment

def interpolator(program_coarse, physical_coarse, coarse_mapping, connectivity_edges, random_seed, num_trials=10, delta=0.2):
    """
    Refines a mapping from program qubits to physical qubits based on a multi-level framework.
    
    Inputs:
      - program_coarse: list of lists of program qubits. For example, [[0,1,3], [4,5], [2]]
                        indicates that the program qubits are partitioned into coarse nodes.
      - physical_coarse: list of lists of physical qubits. The grouping of physical qubits
                         into coarse nodes follows a similar definition as for program_coarse.
      - coarse_mapping: a list where each entry maps a program coarse node (by index) to a
                        physical coarse node (by index). (This is a one-to-one mapping.)
      - connectivity_edges: list of tuples (u, v) representing edges in the refined (physical)
                            connectivity graph. **Note:** This graph can be any connected graph.
    
    Returns:
      A dictionary mapping each program qubit to a physical qubit in the refined graph.
      
    Cost function details:
      For each program qubit 'q':
         - Let Q be the program coarse node that contains 'q'.
         - Let P = coarse_mapping[Q] be the expected physical coarse node.
         - Let expected_set = set(physical_coarse[P]).
         - For any candidate physical qubit 'r':
             • If r is in expected_set, then cost = 0.
             • Otherwise, cost = min{ distance(r, s) for s in expected_set },
               where distances are computed on the refined connectivity graph.
               
      The assignment algorithm then finds a one-to-one mapping of program qubits to physical qubits
      that minimizes the total cost.
    """
    # Build a mapping from each program qubit to its coarse node index.
    np.random.seed(random_seed)
    prog_to_coarse = {}
    for coarse_idx, qubits in enumerate(program_coarse):
        for q in qubits:
            prog_to_coarse[q] = coarse_idx

    # Collect all physical qubits as defined by the physical coarse nodes.
    phys_from_coarse = set()
    for qubits in physical_coarse:
        phys_from_coarse.update(qubits)


    # Additionally, extract physical qubits that appear in the connectivity graph.
    phys_from_graph = set()
    for u, v in connectivity_edges:
        phys_from_graph.add(u)
        phys_from_graph.add(v)
    all_physical_qubits = sorted(phys_from_coarse.union(phys_from_graph))

    # Build the refined connectivity graph.
    # Note: connectivity_edges can define any connected graph.
    G = nx.Graph()
    G.add_edges_from(connectivity_edges)
    
    # Precompute all pairs shortest path distances on the connected graph.
    distances = dict(nx.all_pairs_shortest_path_length(G))
    
    # Create an ordered list of program qubits (flattening the program coarse nodes).
    prog_nodes = sorted(q for qs in program_coarse for q in qs)
    
    # Build the cost matrix:
    #   Rows: program qubits.
    #   Columns: candidate physical qubits (from all_physical_qubits).
    INF = float('inf')
    num_prog = len(prog_nodes)
    num_phys = len(all_physical_qubits)
    cost_matrix = np.zeros((num_prog, num_phys))
    
    for i, prog_q in enumerate(prog_nodes):
        # Identify the program coarse node for prog_q and the corresponding expected physical coarse node.
        expected_phys_coarse_idx = coarse_mapping[prog_to_coarse[prog_q]]
        expected_set = set(physical_coarse[expected_phys_coarse_idx])
        
        for j, candidate in enumerate(all_physical_qubits):
            if candidate in expected_set:
                cost = 0
            else:
                # Compute the minimum distance from 'candidate' to any node in the expected_set.
                dists = [distances[candidate].get(target, INF) for target in expected_set]
                cost = min(dists) if dists else INF
            cost_matrix[i, j] = cost

    # Solve the minimum cost assignment problem using the Hungarian algorithm.
#    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    
    # Build the final refined mapping: program qubit -> physical qubit.

    mapping_list=[]
    
    for _ in range(num_trials):
        mapping = {}
        cur_cost_matrix=cost_matrix+np.random.uniform(0, delta, cost_matrix.shape)
        row_ind, col_ind = linear_sum_assignment(cur_cost_matrix)
        
        for r, c in zip(row_ind, col_ind):
            mapping[prog_nodes[r]] = all_physical_qubits[c]
        
        rep=False
        for existing_mapping in mapping_list:
            if existing_mapping==mapping:
                rep=True
                break
        
        if not rep:
            mapping_list.append(mapping)
    
    return mapping_list
