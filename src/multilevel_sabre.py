from .multilevel import *
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler import PassManager, CouplingMap
from qiskit.converters import dag_to_circuit, circuit_to_dag
from typing import List, Tuple

class MultiCyclesSwapPass(TransformationPass):
    """A transpiler pass that implements the MultiLevel SABRE algorithm for quantum circuit optimization.
    
    This pass optimizes quantum circuits by finding efficient SWAP gate insertions to satisfy
    hardware connectivity constraints. It uses a multi-level approach where the circuit is
    coarsened to reduce complexity, solved at the coarsest level, and then refined back to
    the original circuit size.
    
    Parameters
    ----------
    coupling_graph : CouplingMap
        The hardware topology defining which qubits can interact directly.
        This is used to determine valid SWAP operations between connected qubits.
        
    cycles : int, optional
        Number of times to run the multi-level algorithm. Each cycle may produce
        different results due to randomization. The best result (fewest SWAPs) is kept.
        Default is 10 cycles.
        
    random_seed : int, optional
        Seed for the random number generator. Use this for reproducible results.
        Default is 1.
        
    coarsest_solving_trials : int, optional
        Number of trials to attempt at the coarsest level of the circuit.
        More trials may find better solutions but take longer to run.
        Default is 50 trials.
        
    num_interpolation : int, optional
        Number of interpolation steps used when refining the circuit from the
        coarsest level back to the original size. More steps may produce
        better results but take longer to compute.
        Default is 10 steps.
        
    use_initial_embedding : bool, optional
        Whether to use an initial qubit mapping/embedding before starting
        the optimization. If True, uses a simple heuristic to find an initial
        mapping. If False, starts with a random mapping.
        Default is True.
        
    verbose : bool, optional
        If True, print progress information during optimization.
        Default is False.
    """

    def __init__(
        self,
        coupling_graph: CouplingMap,
        cycles: int = 10,
        random_seed: int = 1,
        coarsest_solving_trials: int = 50,
        num_interpolation: int = 10,
        use_initial_embedding: bool = True,
        verbose: bool = False
    ):
        super().__init__()
        self.coupling_graph = coupling_graph
        self.cycles = cycles
        self.random_seed = random_seed
        self.coarsest_solving_trials = coarsest_solving_trials
        self.num_interpolation = num_interpolation
        self.use_initial_embedding = use_initial_embedding
        self.verbose = verbose

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
            use_initial_embedding=self.use_initial_embedding,
            verbose=self.verbose
        )

        return circuit_to_dag(optimized_circuit)