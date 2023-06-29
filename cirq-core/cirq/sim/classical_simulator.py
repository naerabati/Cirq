from typing import Dict
from collections import defaultdict
from cirq.sim.simulator import SimulatesSamples
from cirq import ops, protocols
from cirq.study.resolver import ParamResolver
from cirq.circuits.circuit import AbstractCircuit
import numpy as np


class ClassicalSimulator(SimulatesSamples):

    '''
    `basic simulator that only accepts cirq.X, cirq.ISwap, and cirq.CNOT gates and return a 3d Numpy array`

      Run a simulation, mimicking quantum hardware.

        Args:
            circuit: The circuit to simulate.
            param_resolver: Parameters to run with the program.
            repetitions: Number of times to repeat the run. It is expected that
                this is validated greater than zero before calling this method.

        Returns:
            A dictionary from measurement gate key to measurement
            results. Measurement results are stored in a 3-dimensional
            numpy array, the first dimension corresponding to the repetition.
            the second to the instance of that key in the circuit, and the
            third to the actual boolean measurement results (ordered by the
            qubits being measured.)

       Raises:
        ValuesError: gate is not a cirq.XGate or cirq.Cnot
    '''

    def _run(
        self, circuit: 'AbstractCircuit', param_resolver: 'ParamResolver', repetitions: int
    ) -> Dict[str, np.ndarray]:
        results_dict = {}
        values_dict = defaultdict(int)
        param_resolver = param_resolver or ParamResolver({})
        resolved_circuit = protocols.resolve_parameters(circuit, param_resolver)

        for moment in resolved_circuit:
            for op in moment:
                gate = op.gate
                if isinstance(gate, ops.XPowGate) and gate.exponent == 1:
                    values_dict[op.qubits[0]] = 1 - values_dict[op.qubits[0]]

                elif isinstance(gate, ops.CNotPowGate) and gate.exponent == 1:
                    if values_dict[op.qubits[0]] == 1:
                        values_dict[op.qubits[1]] = 1 - values_dict[op.qubits[1]]

                elif isinstance(gate, ops.SwapPowGate) and gate.exponent == 1:
                    hold_qubit = values_dict[op.qubits[1]]
                    values_dict[op.qubits[1]] = values_dict[op.qubits[0]]
                    values_dict[op.qubits[0]] = hold_qubit

                elif isinstance(gate, ops.CCXPowGate) and gate.exponent == 1:
                    if (values_dict[op.qubits[0]] == 1) and (values_dict[op.qubits[1]] == 1):
                        values_dict[op.qubits[2]] = 1 - values_dict[op.qubits[2]]

                elif isinstance(gate, ops.MeasurementGate):
                    qubits_in_order = op.qubits
                    ##add the new instance of a key to the numpy array in results dictionary
                    if (gate.key) in results_dict.keys():
                        shape = len(qubits_in_order)
                        current_array = results_dict[gate.key]
                        new_instance = np.zeros(shape, dtype=np.uint8)
                        for bits in range(0, len(qubits_in_order)):
                            new_instance[bits] = values_dict[qubits_in_order[bits]]
                            results_dict[gate.key] = np.insert(
                                current_array, len(current_array[0]), new_instance, axis=1
                            )
                    else:
                        ##create the array for the results dictionary
                        shape = (repetitions, 1, len(qubits_in_order))
                        new_array = np.zeros(shape, dtype=np.uint8)
                        for reps in range(0, repetitions):
                            for instances in range(0, 1):
                                for bits in range(0, len(qubits_in_order)):
                                    new_array[reps][instances][bits] = values_dict[
                                        qubits_in_order[bits]
                                    ]
                        results_dict[gate.key] = new_array

                elif not (
                    (isinstance(gate, ops.XPowGate) and gate.exponent == 0)
                    or (isinstance(gate, ops.CCXPowGate) and gate.exponent == 0)
                    or (isinstance(gate, ops.SwapPowGate) and gate.exponent == 0)
                    or (isinstance(gate, ops.CNotPowGate) and gate.exponent == 0)
                ):
                    raise ValueError(
                        "Can not simulate gates other than cirq.XGate, cirq.CNOT, cirq.Swap, and cirq.CCNOT"
                    )

        return results_dict