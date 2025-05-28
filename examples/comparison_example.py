from qiskit import QuantumCircuit
from qiskit.transpiler import CouplingMap, PassManager
from multilevel_sabre import MultiLevelSabre
import time

from util import EAGLE_COUPLING, sabre, count_swaps

def run_comparison_example():
    # Load the QASM circuit
    circuit = QuantumCircuit.from_qasm_file("circuit.qasm")
    
    # Create the EAGLE coupling map
    coupling_map = CouplingMap(couplinglist=EAGLE_COUPLING)

    # Run SABRE
    print("\nRunning SABRE...")
    start_time = time.time()
    sabre_swaps, sabre_circuit = sabre(
        circuit=circuit,
        coupling=EAGLE_COUPLING,
        number_of_trial=2500, 
        random_seed=1
    )
    sabre_time = time.time() - start_time

    # Run MultiLevel SABRE
    print("\nRunning MultiLevel SABRE...")
    start_time = time.time()
    multilevel_pass = PassManager([
        MultiLevelSabre(
            coupling_graph=coupling_map,
            cycles=10,
            random_seed=1,
            coarsest_solving_trials=50,
            num_interpolation=10,
            use_initial_embedding=True,
            verbose=0
        )
    ])
    multilevel_circuit = multilevel_pass.run(circuit)
    multilevel_time = time.time() - start_time

    # Count SWAPs in MultiLevel SABRE result
    multilevel_swaps = count_swaps(multilevel_circuit)

    # Print comparison results
    print("\nComparison Results:")
    print(f"SABRE:")
    print(f"  - Number of SWAPs: {sabre_swaps}")
    print(f"  - Compilation time: {sabre_time:.2f} seconds")
    print(f"\nMultiLevel SABRE:")
    print(f"  - Number of SWAPs: {multilevel_swaps}")
    print(f"  - Compilation time: {multilevel_time:.2f} seconds")
    print(f"\nSpeedup: {sabre_time/multilevel_time:.2f}x")
    print(f"SWAP reduction: {((sabre_swaps - multilevel_swaps) / sabre_swaps * 100):.1f}%")

if __name__ == "__main__":
    run_comparison_example() 