from typing import Dict, List, Tuple, Optional
from qiskit.transpiler.basepasses import TransformationPass
from .initial_embedding import *
from .interpolation import *
from .clustering import *
from .sabre import *
import time
import random
import numpy as np

def multilevel_cycle_sabre(
    circuit: List,
    coupling_graph: List[Tuple[int, int]],
    initial_mapping: Dict[int, int],
    random_seed: int,
    coarser_rep: int = 50,
    num_interpolation: int = 10
) -> Tuple[Tuple[int, Dict[int, int], List], Tuple[int, Dict[int, int], List]]:
    """
    Perform a single cycle of multilevel SABRE algorithm.
    
    Args:
        circuit: The quantum circuit to optimize
        coupling_graph: Physical coupling graph of the device
        initial_mapping: Initial qubit mapping
        random_seed: Random seed for reproducibility
        clustering_protocol: Protocol for clustering ('current' or 'until no swap')
        coarser_rep: Number of repetitions at coarser level
        num_interpolation: Number of interpolation steps
        
    Returns:
        Tuple containing (best_result, current_result)
    """
    start_time = time.time()
    random.seed(random_seed)
    
    # Initialize current level variables
    current_coupling = coupling_graph
    current_circuit = circuit
    current_mapping = initial_mapping

    # Run initial SABRE pass
    num_swaps, current_mapping, compiled_circuit = sabre(
        current_circuit, 
        current_coupling, 
        1, 
        random_seed, 
        [current_mapping]
    )
    best_result = (num_swaps, current_mapping, compiled_circuit)
    print("Initial mapping quality:", num_swaps)

    if num_swaps == 0:
        return best_result, best_result

    # Coarsening phase
    levels = []
    while True:
        # Perform clustering
        physical_coarser, program_coarser, current_circuit, current_coupling, current_mapping = clustering(
            current_mapping,
            current_coupling,
            current_circuit
        )
        
        # Check if further coarsening is needed
        cluster_num_swaps, _, _ = sabre(
            current_circuit,
            current_coupling,
            0,
            random_seed,
            [current_mapping]
        )

        clustering_protocol="current"
        
        if cluster_num_swaps > 0:
            if clustering_protocol in ["current", "until no swap"]:
                levels.append((physical_coarser, program_coarser, current_circuit, current_coupling, current_mapping))
            else:
                levels.append((physical_coarser, program_coarser, current_circuit, current_coupling, current_mapping))
                break
        else:
            if clustering_protocol == "until no swap":
                levels.append((physical_coarser, program_coarser, current_circuit, current_coupling, current_mapping))
            print("No more swaps needed at this level")
            break

    print("Number of coarser levels:", len(levels))
    print("Finished coarsening in", time.time() - start_time)

    # Process coarser levels if they exist
    if len(levels) > 0:
        # Solve coarsest level
        _, _, current_circuit, current_coupling, current_mapping = levels[-1]
        result = sabre(
            current_circuit,
            current_coupling,
            coarser_rep,
            random_seed,
            [current_mapping]
        )
        current_mapping = result[1]
        print("Coarser level solved in", time.time() - start_time)

        # Process intermediate levels
        if len(levels) > 1:
            for i in reversed(range(1, len(levels))):
                print("Processing level", i)
                program_c, physical_c, _, _, _ = levels[i]
                _, _, prev_circuit, prev_coupling, _ = levels[i-1]
                
                # Perform interpolation
                interpolation_results = interpolator(
                    program_c,
                    physical_c,
                    current_mapping,
                    prev_coupling,
                    random_seed,
                    num_interpolation
                )
                print("Interpolation finished in", time.time() - start_time)
                
                # Refine solution
                current_result = sabre(
                    prev_circuit,
                    prev_coupling,
                    coarser_rep,
                    random_seed,
                    interpolation_results
                )
                print("Refinement finished in", time.time() - start_time)
                current_mapping = current_result[1]

        # Final level processing
        physical_coarser, program_coarser, _, _, _ = levels[0]
        final_interpolation = interpolator(
            program_coarser,
            physical_coarser,
            current_mapping,
            coupling_graph,
            random_seed
        )
        
        compilation_result = sabre(
            circuit,
            coupling_graph,
            1,
            random_seed,
            final_interpolation
        )
        print("Final level compilation finished in", time.time() - start_time)

        if compilation_result[0] < best_result[0]:
            best_result = compilation_result
        
        return best_result, compilation_result

    else:
        # If no coarser levels, just run SABRE on original circuit
        compilation_result = sabre(
            circuit,
            coupling_graph,
            coarser_rep,
            random_seed,
            [current_mapping]
        )

        if compilation_result[0] < best_result[0]:
            best_result = compilation_result

        return best_result, compilation_result

def multi_cycles(
    cycles: int,
    circuit: List,
    coupling_graph: List[Tuple[int, int]],
    random_seed: int,
    coarser_rep: int = 50,
    num_interpolation: int = 10,
    stuck_sabre_trial: int = 500,
    use_initial_embedding: bool = True
) -> Tuple[int, Dict[int, int], List]:
    """
    Perform multiple cycles of multilevel SABRE algorithm.
    
    Args:
        cycles: Number of cycles to perform
        circuit: The quantum circuit to optimize
        coupling_graph: Physical coupling graph of the device
        random_seed: Random seed for reproducibility
        clustering_protocol: Protocol for clustering
        coarser_rep: Number of repetitions at coarser level
        num_interpolation: Number of interpolation steps
        stuck_sabre_trial: Number of trials when stuck
        use_initial_embedding: Whether to use initial embedding
        
    Returns:
        Best result tuple containing (num_swaps, mapping, compiled_circuit)
    """
    best_result = (np.inf, None, None)

    # Initialize mapping
    if use_initial_embedding:
        current_mapping = initial_embedding(coupling_graph, circuit)
    else:
        random.seed(random_seed)
        physical_qubits = list(set([j for i in coupling_graph for j in i]))
        current_mapping = {i: physical_qubits[i] for i in range(len(physical_qubits))}

    history_mapping = []
    current_seed = random_seed

    for cycle in range(cycles):
        print("Cycle:", cycle)
        current_best, last_result = multilevel_cycle_sabre(
            circuit,
            coupling_graph,
            current_mapping,
            random_seed,
            coarser_rep,
            num_interpolation
        )
        current_mapping = last_result[1]

        # Check for stuck condition
        for prev_map in history_mapping:
            if current_mapping == prev_map:
                print("Stuck condition detected")
                break

        if current_best[0] < best_result[0]:
            best_result = current_best
        
        if best_result[0] == 0:
            break
        
        print("Current best result:", best_result[0])
        print("Last result:", last_result[0])

    return best_result

# Device coupling graphs
EAGLE_COUPLING = [
    (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8),
    (9, 10), (10, 11), (11, 12), (12, 13),
    (0, 14), (14, 18), (4, 15), (15, 22), (8, 16), (16, 26), (12, 17), (17, 30),
    (18, 19), (19, 20), (20, 21), (21, 22), (22, 23), (23, 24), (24, 25), (25, 26),
    (26, 27), (27, 28), (28, 29), (29, 30), (30, 31), (31, 32),
    (20, 33), (33, 39), (24, 34), (34, 43), (28, 35), (35, 47), (32, 36), (36, 51),
    (37, 38), (38, 39), (39, 40), (40, 41), (41, 42), (42, 43), (43, 44), (44, 45),
    (45, 46), (46, 47), (47, 48), (48, 49), (49, 50), (50, 51),
    (37, 52), (52, 56), (41, 53), (53, 60), (45, 54), (54, 64), (49, 55), (55, 68),
    (56, 57), (57, 58), (58, 59), (59, 60), (60, 61), (61, 62), (62, 63), (63, 64),
    (64, 65), (65, 66), (66, 67), (67, 68), (68, 69), (69, 70),
    (58, 71), (71, 77), (62, 72), (72, 81), (66, 73), (73, 85), (70, 74), (74, 89),
    (75, 76), (76, 77), (77, 78), (78, 79), (79, 80), (80, 81), (81, 82), (82, 83),
    (83, 84), (84, 85), (85, 86), (86, 87), (87, 88), (88, 89),
    (75, 90), (90, 94), (79, 91), (91, 98), (83, 92), (92, 102), (87, 93), (93, 106),
    (94, 95), (95, 96), (96, 97), (97, 98), (98, 99), (99, 100), (100, 101), (101, 102),
    (102, 103), (103, 104), (104, 105), (105, 106), (106, 107), (107, 108),
    (96, 109), (100, 110), (110, 118), (104, 111), (111, 112), (108, 112), (112, 126),
    (113, 114), (114, 115), (115, 116), (116, 117), (117, 118), (118, 119), (119, 120),
    (120, 121), (121, 122), (122, 123), (123, 124), (124, 125), (125, 126)
]

WILLOW_COUPLING = [
    (0,1), (1,2),
    (3,4), (4,5), (5,6), (0,5), (1,4), (2,3),
    (7,8), (8,9), (9,10), (10,11), (11,12), (12,13), (6,8), (5,9), (4,10), (3,11),
    (14,15), (15,16), (16,17), (17,18), (18,19), (19,20), (20,21), (13,14), (15,12),
    (16,11), (17,10), (18,9), (19,8), (20,7),
    (22,23), (23,24), (24,25), (25,26), (26,27), (27,28), (28,29), (29,30), (30,31),
    (31,32), (23,21), (24,20), (25,19), (26,18), (27,17), (28,16), (29,15), (30,14),
    (33,34), (34,35), (35,36), (36,37), (37,38), (38,39), (39,40), (40,41), (41,42),
    (42,43), (43,44), (33,32), (34,31), (35,30), (36,29), (37,28), (38,27), (39,26),
    (40,25), (41,24), (42,23), (43,22),
    (45,46), (46,47), (47,48), (48,49), (49,50), (50,51), (51,52), (52,53), (53,54),
    (54,55), (55,56), (56,57), (57,58), (58,59), (46,44), (47,43), (48,42), (49,41),
    (50,40), (51,39), (52,38), (53,37), (54,36), (55,35), (56,34), (57,33),
    (60,61), (61,62), (62,63), (63,64), (64,65), (65,66), (66,67), (67,68), (68,69),
    (69,70), (70,71), (60,58), (61,57), (62,56), (63,55), (64,54), (65,53), (66,52),
    (67,51), (68,50), (69,49), (70,48), (71,47),
    (72,73), (73,74), (74,75), (75,76), (76,77), (77,78), (78,79), (79,80), (80,81),
    (81,82), (72,71), (73,70), (74,69), (75,68), (76,67), (77,66), (78,65), (79,64),
    (80,63), (81,62), (82,61),
    (83,84), (84,85), (85,86), (86,87), (87,88), (88,89), (89,90), (83,81), (84,80),
    (85,79), (86,78), (87,77), (88,76), (89,75), (90,74),
    (91,92), (92,93), (93,94), (94,95), (95,96), (96,97), (91,90), (92,89), (93,88),
    (94,87), (95,86), (96,85), (97,84),
    (98,99), (99,100), (100,101), (98,96), (99,95), (100,94), (101,93),
    (102,103), (103,104), (102,101), (103,100), (104,99)
]