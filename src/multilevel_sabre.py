from .multilevel import *
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler import PassManager, CouplingMap
from qiskit.converters import dag_to_circuit, circuit_to_dag
from typing import List, Tuple

class MultiCyclesSwapPass(TransformationPass):
    def __init__(
        self,
        coupling_graph: CouplingMap,
        cycles: int = 10,
        random_seed: int = 1,
        coarsest_solving_trials: int = 50,
        num_interpolation: int = 10,
        use_initial_embedding: bool = True
    ):
        super().__init__()
        self.coupling_graph = coupling_graph
        self.cycles = cycles
        self.random_seed = random_seed
        self.coarsest_solving_trials = coarsest_solving_trials
        self.num_interpolation = num_interpolation
        self.use_initial_embedding = use_initial_embedding

    def run(self, dag):
        circuit = dag_to_circuit(dag)

        # multi_cycles returns (num_swaps, mapping, compiled_circuit)
        _, _, optimized_circuit = multi_cycles(
            cycles=self.cycles,
            circuit=circuit,
            coupling_graph=self.coupling_graph.get_edges(),
            random_seed=self.random_seed,
            coarsest_solving_trials=self.coarsest_solving_trials,
            num_interpolation=self.num_interpolation,
            use_initial_embedding=self.use_initial_embedding
        )

        return circuit_to_dag(optimized_circuit)