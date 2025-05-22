import networkx as nx
from qiskit import QuantumCircuit

def clustering(program_to_physical, physical_edges, circuit_gates):
    """
    Given:
      - program_to_physical: a mapping (dictionary) from program qubits to physical qubits 
        in the refined graph.
      - physical_edges: list of tuples (p_a, p_b) representing edges (coupling) in the refined 
        physical graph.
      - circuit_gates: list of two-qubit gates (q_a, q_b) on program qubits.
      
    Returns:
      A 4-tuple:
        (coarse_physical_nodes, coarse_program_nodes, coarse_circuit, coarse_coupling_graph)
      
      where:
        - coarse_physical_nodes: a list of lists, each inner list is a group of physical qubits.
          Every physical qubit in the refined graph appears in exactly one group. If a node is
          not matched with any other, it appears as a singleton list.
        - coarse_program_nodes: a list of lists, where each group is obtained by collecting 
          the program qubits assigned to the physical qubits in the corresponding coarse physical node.
          (The ordering is chosen so that the coarse–level mapping is trivial: coarse program node i 
          corresponds to coarse physical node i.)
        - coarse_circuit: a list of two–qubit gates (i,j) between coarse program nodes. For each gate
          (q_a, q_b) in the original circuit, if the program qubits lie in different coarse program nodes,
          then a coarse gate (i, j) is added. Gates between qubits in the same coarse node are dropped.
        - coarse_coupling_graph: a list of edges (i,j) between coarse physical nodes. Two coarse nodes are 
          connected if any refined edge connects a physical qubit in one group with a physical qubit in the other.
    """
    temp_list=[(qargs[0]._index,qargs[1]._index) for _,qargs,_ in circuit_gates.data if len(qargs)==2]
    circuit_gates=temp_list

    # Step 1. Build the inverse mapping: physical qubit -> program qubit.
#    print(program_to_physical)
    physical_to_program = {}
    for prog_q, phys_q in program_to_physical.items():
        physical_to_program[phys_q] = prog_q

    # Step 2. Build the refined physical graph with weights.
    # For each edge (p_a, p_b), assign its weight equal to the number of two-qubit gates 
    # in the circuit whose endpoints are assigned to p_a and p_b (in either order).
    G_phys = nx.Graph()
    for p1, p2 in physical_edges:
        G_phys.add_edge(p1, p2, weight=0)
    
    for q1, q2 in circuit_gates:
        # Find physical qubits holding these program qubits.
        p1 = program_to_physical.get(q1)
        p2 = program_to_physical.get(q2)
        if p1 is None or p2 is None:
            continue  # Skip if one program qubit is not mapped.
        if p1 == p2:
            continue  # Skip if both program qubits are mapped to the same physical node.
        if G_phys.has_edge(p1, p2):
            G_phys[p1][p2]['weight'] += 1

    # Step 3. Compute a maximum cardinality matching with maximum weight.
    # This matching groups together physical qubits (nodes) that will form a coarse node.
    matching = nx.max_weight_matching(G_phys, maxcardinality=True, weight='weight')
    # 'matching' is a set of frozensets (or 2-tuples) where each pair indicates two physical qubits to merge.
    
    # Step 4. Form the coarse physical nodes.
    # First, include all groups from the matching.
    matched_nodes = set()
    coarse_physical_nodes = []
    for edge in matching:
        group = sorted(list(edge))
        coarse_physical_nodes.append(group)
        matched_nodes.update(group)
    
    # Now, add any physical node that was not matched as a singleton group.
    all_physical_nodes = set()
    # Collect nodes from the refined connectivity.
    for p1, p2 in physical_edges:
        all_physical_nodes.add(p1)
        all_physical_nodes.add(p2)
    # Also include any physical node that might be present in the mapping.
    all_physical_nodes.update(program_to_physical.values())
    
    for p in all_physical_nodes:
        if p not in matched_nodes:
            coarse_physical_nodes.append([p])
    
    # Optional: sort the coarse physical nodes (e.g., by the smallest node in each group).
    coarse_physical_nodes = sorted(coarse_physical_nodes, key=lambda group: group[0])
    
    # Step 5. Build the coarse program nodes.
    # For each coarse physical node, collect the program qubits assigned to any physical qubit in that group.
    coarse_program_nodes = []
    for group in coarse_physical_nodes:
        prog_group = []
        for p in group:
            if p in physical_to_program:
                prog_group.append(physical_to_program[p])
        prog_group = sorted(prog_group)  # sort for consistency
        coarse_program_nodes.append(prog_group)
    
    # Step 6. Create a mapping from program qubit to its coarse program node index.
    program_to_coarse = {}
    for i, group in enumerate(coarse_program_nodes):
        for q in group:
            program_to_coarse[q] = i

    # Step 7. Build the coarse circuit.
    # For each two-qubit gate in the original circuit, if the program qubits belong
    # to different coarse nodes, add a gate between those coarse nodes.
    coarse_circuit = QuantumCircuit(len(coarse_program_nodes))
    for q1, q2 in circuit_gates:
        i = program_to_coarse.get(q1)
        j = program_to_coarse.get(q2)
        if i is None or j is None:
            continue  # Skip if a program qubit wasn't grouped (should not happen)
        if i != j:
            coarse_circuit.cx(i,j)
    
    # Step 8. Build the coarse coupling graph.
    # Map each physical node to its coarse group.
    physical_to_coarse = {}
    for i, group in enumerate(coarse_physical_nodes):
        for p in group:
            physical_to_coarse[p] = i
    coarse_edges_set = set()
    for p1, p2 in physical_edges:
        i = physical_to_coarse.get(p1)
        j = physical_to_coarse.get(p2)
        if i is None or j is None:
            continue
        if i != j:
            # Use an unordered tuple (sorted) to avoid duplicate edges.
            coarse_edge = tuple(sorted((i, j)))
            coarse_edges_set.add(coarse_edge)
    coarse_coupling_graph = list(coarse_edges_set)

    assert len(coarse_program_nodes)==len(coarse_physical_nodes)
    coarser_mapping={}
    
    for i in range(len(coarse_program_nodes)):
        coarser_mapping[i]=i


    
    return coarse_physical_nodes, coarse_program_nodes, coarse_circuit, coarse_coupling_graph, coarser_mapping

# -----------------------
# Example usage:
if __name__ == '__main__':
    # Example refined mapping: program qubit -> physical qubit.
    program_to_physical = {0: 1, 2: 2, 1: 3, 3: 4}
    
    # Refined physical coupling graph (edges between physical qubits).
    physical_edges = [
        (1, 2),
        (2, 3),
        (3, 4),
        (1, 4)
    ]
    
    # A quantum circuit with only two-qubit gates on program qubits.
    circuit_gates = [
        (1, 0),  # Gate between program qubits 5 and 4.
        (1, 2),  # Gate between program qubits 5 and 8.
        (0, 2),  # Gate between program qubits 4 and 8.
        (0, 3)   # Gate between program qubits 4 and 9.
    ]
    qc=QuantumCircuit(4)
    for i,j in circuit_gates:
        qc.cz(i,j)
    
    circuit_gates=qc
    
    cp_nodes, cq_nodes, coarse_circ, coarse_coup, coarse_map = clustering (
        program_to_physical,
        physical_edges,
        circuit_gates
    )
    
    print("Coarse Physical Nodes:", cp_nodes)
    print("Coarse Program Nodes: ", cq_nodes)
    print("Coarse Circuit:       ")
    print(coarse_circ)
    print("Coarse Coupling Graph:", coarse_coup)