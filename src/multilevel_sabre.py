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
        coarser_rep: int = 50,
        num_interpolation: int = 10,
        stuck_sabre_trial: int = 500,
        use_initial_embedding: bool = True
    ):
        super().__init__()
        self.coupling_graph = coupling_graph
        self.cycles = cycles
        self.random_seed = random_seed
        self.coarser_rep = coarser_rep
        self.num_interpolation = num_interpolation
        self.stuck_sabre_trial = stuck_sabre_trial
        self.use_initial_embedding = use_initial_embedding

    def run(self, dag):
        circuit = dag_to_circuit(dag)

        # multi_cycles returns (num_swaps, mapping, compiled_circuit)
        _, _, optimized_circuit = multi_cycles(
            cycles=self.cycles,
            circuit=circuit,
            coupling_graph=self.coupling_graph.get_edges(),
            random_seed=self.random_seed,
            coarser_rep=self.coarser_rep,
            num_interpolation=self.num_interpolation,
            stuck_sabre_trial=self.stuck_sabre_trial,
            use_initial_embedding=self.use_initial_embedding
        )

        return circuit_to_dag(optimized_circuit)