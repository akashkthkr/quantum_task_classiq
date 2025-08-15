from math import isclose

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

NUM_SHOTS = 1024


def create_basic_quantum_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def execute_circuit(qc: QuantumCircuit) -> dict:
    simulator = AerSimulator()
    job = simulator.run(qc, shots=NUM_SHOTS)
    result = job.result()
    return result.get_counts()


def test_basic_circuit_counts_sum_and_distribution():
    qc = create_basic_quantum_circuit()
    counts = execute_circuit(qc)

    # Outcomes should be only 00 and 11 for a Bell state measurement
    assert set(counts.keys()).issubset({"00", "11"})

    total = sum(counts.values())
    assert total == NUM_SHOTS

    # Roughly balanced distribution (within 30%)
    c00 = counts.get("00", 0)
    c11 = counts.get("11", 0)
    assert abs(c00 - c11) <= int(NUM_SHOTS * 0.30)
