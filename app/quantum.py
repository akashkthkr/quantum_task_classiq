from typing import Dict

from qiskit import QuantumCircuit
from qiskit.qasm3 import loads as qasm3_loads
from qiskit_aer import AerSimulator

from .config import settings


def circuit_from_qasm3(qasm3_str: str) -> QuantumCircuit:
	return qasm3_loads(qasm3_str)


def run_circuit(qc: QuantumCircuit) -> Dict[str, int]:
	simulator = AerSimulator()
	job = simulator.run(qc, shots=settings.num_shots)
	result = job.result()
	counts = result.get_counts()
	return {str(k): int(v) for k, v in counts.items()}
