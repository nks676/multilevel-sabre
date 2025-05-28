# MultiLevel SABRE

A Python implementation of the MultiLevel SABRE algorithm for quantum circuit optimization.

## Installation

Since this package is not yet published on PyPI, you can install it locally using pip:

```bash
pip install -e .
```

## Usage

Check the `examples` directory for detailed example notebooks and scripts demonstrating how to use the MultiLevel SABRE algorithm. The examples include:

- Simple circuit optimization
- Comparison with the original SABRE algorithm
- Performance analysis and benchmarking

### Simple Example

Here's a basic example of how to use the MultiLevel SABRE algorithm with a simple circuit:

```python
from qiskit import QuantumCircuit
from qiskit.transpiler import CouplingMap
from multilevel_sabre import MultiLevelSabre

# Create a quantum circuit
circuit = QuantumCircuit(5)
circuit.h(0)
circuit.cx(0, 1)
circuit.cx(1, 2)
circuit.cx(2, 3)
circuit.cx(3, 4)

# Define the hardware topology (example: linear chain)
coupling_map = CouplingMap.from_line(5)

# Create and run the MultiLevel SABRE pass
pass_manager = PassManager([
    MultiLevelSabre(
        coupling_graph=coupling_map,
        cycles=10,                    # Number of optimization cycles
        random_seed=1,                # Random seed for reproducibility
        coarsest_solving_trials=50,   # Number of trials at coarsest level
        num_interpolation=10,         # Number of interpolation steps
        use_initial_embedding=True,   # Use initial qubit mapping
        verbose=0                     # Verbosity level (0: off, 1: minimal, 2: full)
    )
])

# Run the pass
optimized_circuit = pass_manager.run(circuit)
```

### Comparison with SABRE

The package includes a comparison example that demonstrates the performance difference between MultiLevel SABRE and the original SABRE algorithm. You can run it using:

```bash
python examples/comparison_example.py
```

This example:
1. Loads a QASM circuit
2. Runs both SABRE and MultiLevel SABRE on the same circuit
3. Compares the number of SWAP gates and compilation time
4. Shows the speedup and SWAP reduction achieved by MultiLevel SABRE

## Parameters

The `MultiLevelSabre` class accepts the following parameters:

- `coupling_graph` (CouplingMap): The hardware topology defining which qubits can interact directly.
- `cycles` (int, default=10): Number of times to run the multi-level algorithm. Each cycle may produce different results due to randomization. The best result (fewest SWAPs) is kept.
- `random_seed` (int, default=1): Seed for the random number generator. Use this for reproducible results.
- `coarsest_solving_trials` (int, default=50): Number of trials to attempt at the coarsest level of the circuit. More trials may find better solutions but take longer to run.
- `num_interpolation` (int, default=10): Number of interpolation steps used when refining the circuit from the coarsest level back to the original size. More steps may produce better results but take longer to compute.
- `use_initial_embedding` (bool, default=True): Whether to use an initial qubit mapping/embedding before starting the optimization. If True, uses a simple heuristic to find an initial mapping. If False, starts with a random mapping.
- `verbose` (int, default=0): Controls the verbosity level of the output:
  - 0: No output (off)
  - 1: Minimal output (basic progress information)
  - 2: Full output (detailed progress and statistics)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# citation section

# add docstring of parameters