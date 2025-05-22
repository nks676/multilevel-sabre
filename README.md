# MultiLevel SABRE

A Qiskit transpiler pass that implements a multi-level SABRE algorithm for quantum circuit optimization. This package provides the `MultiCyclesSwapPass` which can be used as a custom transpiler pass in Qiskit to optimize quantum circuits for specific device topologies.

## Installation

Clone the repository and install from source:

```bash
git clone https://github.com/nks676/multilevel-sabre.git
cd multilevel-sabre
pip install .
```

For development installation (changes to source code will be reflected immediately):

```bash
pip install -e .
```

## Usage

```python
from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager, CouplingMap
from multilevel_sabre import MultiCyclesSwapPass

# Create your quantum circuit
circuit = QuantumCircuit(...)

# Define your coupling map
coupling_map = CouplingMap(...)

# Create the pass
pass_ = MultiCyclesSwapPass(
    coupling_graph=coupling_map,
    cycles=10,                    # Number of optimization cycles
    random_seed=1,               # Random seed for reproducibility
    coarser_rep=50,              # Coarser representation parameter
    num_interpolation=10,        # Number of interpolation steps
    stuck_sabre_trial=500,       # Number of trials for stuck SABRE
    use_initial_embedding=True   # Whether to use initial embedding
)

# Create a pass manager and run the pass
pm = PassManager(pass_)
optimized_circuit = pm.run(circuit)
```

## Parameters

- `coupling_graph`: The coupling map of the quantum device
- `cycles`: Number of optimization cycles (default: 10)
- `random_seed`: Random seed for reproducibility (default: 1)
- `coarser_rep`: Coarser representation parameter (default: 50)
- `num_interpolation`: Number of interpolation steps (default: 10)
- `stuck_sabre_trial`: Number of trials for stuck SABRE (default: 500)
- `use_initial_embedding`: Whether to use initial embedding (default: True)

## License

MIT License 