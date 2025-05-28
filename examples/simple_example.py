from qiskit import QuantumCircuit
from qiskit.transpiler import CouplingMap, PassManager
from multilevel_sabre import MultiLevelSabre
import time

def run_simple_example():
    # Create a simple quantum circuit
    circuit = QuantumCircuit(5)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.cx(2, 3)
    circuit.cx(3, 4)
    circuit.cx(4, 0)  # Create a cycle to make it more interesting

    # Define a simple hardware topology (linear chain)
    coupling_map = CouplingMap.from_line(5)

    # Create and run the MultiLevel SABRE pass
    start_time = time.time()
    pass_manager = PassManager([
        MultiLevelSabre(
            coupling_graph=coupling_map,
            cycles=10,
            random_seed=1,
            coarsest_solving_trials=50,
            num_interpolation=10,
            use_initial_embedding=True,
            verbose=1  # Show basic progress
        )
    ])

    # Run the pass
    optimized_circuit = pass_manager.run(circuit)
    end_time = time.time()

    # Print results
    print("\nOriginal circuit:")
    print(circuit)
    print("\nOptimized circuit:")
    print(optimized_circuit)
    print(f"\nCompilation time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    run_simple_example() 