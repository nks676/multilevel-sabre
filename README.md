# MultiLevel SABRE

MultiLevel SABRE is a Qiskit transpiler pass that applies a multi-level approach to the
[SABRE](https://arxiv.org/abs/1809.02573) qubit routing algorithm. The algorithm
coarsens the circuit to a simplified representation, solves the routing problem
at the coarsest level and then refines the solution back to the original
circuit. This often yields fewer SWAP gates compared to running SABRE directly on
the full circuit.

## Installation

The package is not published on PyPI yet, so install it from the repository
root using `pip`:

```bash
pip install -e .
```

## Usage

Example notebooks and scripts are available in the `examples` directory. They
show how to optimise circuits and compare the results with the original SABRE
pass.

### Simple Example

```python
from qiskit import QuantumCircuit
from qiskit.transpiler import CouplingMap, PassManager
from multilevel_sabre import MultiLevelSabre

# Create a simple circuit
circuit = QuantumCircuit(5)
circuit.h(0)
circuit.cx(0, 1)
circuit.cx(1, 2)
circuit.cx(2, 3)
circuit.cx(3, 4)

# Linear chain hardware topology
coupling_map = CouplingMap.from_line(5)

# Run the MultiLevel SABRE optimisation
pass_manager = PassManager([
    MultiLevelSabre(
        coupling_graph=coupling_map,
        cycles=10,
        random_seed=1,
        coarsest_solving_trials=50,
        num_interpolation=10,
        use_initial_embedding=True,
        verbose=0,
    )
])
optimised = pass_manager.run(circuit)
```

### Comparison with SABRE

```
python examples/comparison_example.py
```

The script loads a benchmark circuit, runs both SABRE and MultiLevel SABRE and
prints the number of SWAP gates and compilation time for each.

## Parameters

The `MultiLevelSabre` class exposes the following arguments:

- **`coupling_graph`** (`CouplingMap`): hardware coupling map.
- **`cycles`** (`int`, default `10`): number of optimisation cycles. The best
  result across cycles is returned.
- **`random_seed`** (`int`, default `1`): seed for randomness.
- **`coarsest_solving_trials`** (`int`, default `50`): number of attempts at the
  coarsest level.
- **`num_interpolation`** (`int`, default `10`): number of interpolation steps
  during refinement.
- **`use_initial_embedding`** (`bool`, default `True`): whether to start from an
  initial heuristic mapping.
- **`verbose`** (`int`, default `0`): verbosity level (`0`, `1`, or `2`).

## Citation

If you use this code in your research, please cite the MultiLevel SABRE paper
and reference this repository.

## License

This project is licensed under the MIT License. See `LICENSE` for details.

