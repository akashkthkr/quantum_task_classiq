from qiskit import QuantumCircuit
from app.quantum import circuit_to_qasm3, circuit_from_qasm3


def create_bell() -> QuantumCircuit:
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def test_qasm3_roundtrip_structure():
    original = create_bell()
    qasm = circuit_to_qasm3(original)
    restored = circuit_from_qasm3(qasm)

    # Same number of qubits/clbits
    assert restored.num_qubits == original.num_qubits
    assert restored.num_clbits == original.num_clbits

    # Basic instruction sequence length matches
    assert len(restored.data) == len(original.data)
