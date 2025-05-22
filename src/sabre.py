from qiskit.transpiler import CouplingMap, Layout
from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import SabreLayout, SetLayout, SabreSwap
from qiskit.converters import *
import qiskit.qasm2
import random

def read_qasm(file_name):
    qc = QuantumCircuit.from_qasm_file(file_name)
    num_of_qubits=qc.num_qubits
    num_of_clbits=qc.num_clbits
    result_qc=QuantumCircuit(num_of_qubits,num_of_clbits)
    two_qubit_qc=QuantumCircuit(num_of_qubits,num_of_clbits)

    print("Number of gates",len(qc.data))

    qubits_correspondence_dict = {q: i for i, q in enumerate(qc.qubits)}
    clbits_correspondence_dict = {c: i for i, c in enumerate(qc.clbits)}

    for instr, qargs, cargs in qc.data:
        new_qargs = [result_qc.qubits[qubits_correspondence_dict[q]] for q in qargs]
        new_cargs = [result_qc.clbits[clbits_correspondence_dict[c]] for c in cargs]
        if instr.num_qubits<=2 and instr.name!="barrier":
            result_qc.append(instr, new_qargs, new_cargs)

            if instr.num_qubits==2:  # Ensure it's a two-qubit gate
                two_qubit_qc.append(instr, new_qargs)

    return result_qc, two_qubit_qc

   
def sabre(circuit, coupling, number_of_trial, random_seed, initial_layout_list=None):
    qc=circuit
    device = CouplingMap(couplinglist=coupling, description="sabre_test")
#    physical_qubit_list=list(set([n for edge in coupling for n in edge]))
    num_program_qubit=qc.num_qubits
    num_classical_bits=qc.num_clbits
    num_physical_qubit=max(max(i) for i in coupling)+1
    if num_physical_qubit>num_program_qubit:
        temp_qc=QuantumCircuit(num_physical_qubit,num_classical_bits)
        temp_qc.compose(qc,inplace=True)
        qc=temp_qc

#    sabre_layout = SabreSwap(coupling_map = device, seed = 0, layout_trials=number_of_trial, skip_routing=False)
    sabre_layout = SabreLayout(coupling_map = device, seed = random_seed, layout_trials=number_of_trial, skip_routing=False)
    if not initial_layout_list is None:
      layout_list=[]
      for mapping in initial_layout_list:
        layout = Layout({qc.qubits[logical]: physical for logical, physical in mapping.items()})
        layout_list.append(layout)
      sabre_layout.property_set['sabre_starting_layouts'] = layout_list

    out_dag = sabre_layout.run(circuit_to_dag(qc))
    sabre_cir = dag_to_circuit(out_dag)
    initial_layout = sabre_layout.property_set["layout"]
    initial_mapping={}
    for program, physical in initial_layout.get_virtual_bits().items():
        initial_mapping[program._index]=physical


#    print(initial_layout)



    count_swap = 0
    for gate in sabre_cir.data:
        if gate[0].name == 'swap':
            count_swap += 1

    return count_swap, initial_mapping, sabre_cir    

    """
#    list_gate = circuit_info
    print(list_gate)
#    print(len(list_gate))
    print("Preprocessing finished")
    qc = QuantumCircuit(count_physical_qubit)
    two_qubit_gate = 0
    single_qubit_gate = 0
    for gate in list_gate:
        if len(gate) == 2:
            qc.cx(gate[0], gate[1])
            two_qubit_gate += 1
        elif len(gate) == 1:
            qc.h(gate[0])
            single_qubit_gate += 1
        else:
            raise TypeError("Currently only support one and two-qubit gate.")
    print("gate num: {}".format(len(list_gate)))
    print("2Q gate num: {}".format(two_qubit_gate))
    print("1Q gate num: {}".format(single_qubit_gate))
    """
    """
def read_qasm(file_name):
  circuit=[]
  with open(file_name, 'r') as f:
      contents = f.readlines()
  f.close()
  for line in range(4,len(contents)):
    gate=contents[line]
    gate=gate.replace("\n", "")
    split_result=gate.split(" ")
    if len(split_result)==2:
      operation,qubit=split_result
      q=""
      for letter in qubit:
        if letter.isdigit():
          q=q+letter
      circuit.append((int(q),))
    else:
      print(split_result)
      operation,qubit1,qubit2=split_result
      q1,q2="",""
      for letter in qubit1:
        if letter.isdigit():
          q1=q1+letter
      for letter in qubit2:
        if letter.isdigit():
          q2=q2+letter
      circuit.append((int(q1),int(q2)))
  return circuit

def read_qasm(file_name):
    two_qubit_gates=[]
    with open(file_name, 'r') as file:
        for line in file:
            # Remove comments and strip whitespace
            line = line.split("//")[0].strip()
 #           print(line)
            # Skip irrelevant lines
            if not line or line.startswith(("OPENQASM", "include", "qreg", "creg", "measure", "barrier")):
                continue

            # Count the number of qubits in the line
            if "q[" in line:
                # Extract qubit parts
                qubit_parts = line.split("q[")[1:]  # Split on "q[" and process the rest
                qubits = [part.split("]")[0] for part in qubit_parts]  # Extract indices before "]"

                if len(qubits) == 2:  # Check if it is a two-qubit gate
                    try:
                        # Convert to integers and add as a tuple
                        qubit_indices = tuple(map(int, qubits))
                        two_qubit_gates.append(qubit_indices)
                    except ValueError:
                        # Ignore malformed lines
                        pass

    return two_qubit_gates
"""