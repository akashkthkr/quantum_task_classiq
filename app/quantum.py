from typing import Dict, Tuple
from qiskit import QuantumCircuit, transpile
from qiskit.qasm3 import loads as qasm3_loads, dumps as qasm3_dumps
from qiskit_aer import AerSimulator

from .config import settings

def circuit_from_qasm3(qasm3_str: str) -> QuantumCircuit:
    try:
        qc = qasm3_loads(qasm3_str)
    except Exception as e:
        raise ValueError(f"QASM3 parse error: {e}")  # surfaces real parser error
    return qc

def _ensure_measurements(qc: QuantumCircuit) -> Tuple[QuantumCircuit, bool]:
    """Add measure_all if the circuit has no classical bits or no measure ops."""
    has_measure = any(instr.operation.name == "measure" for instr in qc.data)
    if not qc.num_clbits or not has_measure:
        qc = qc.copy()
        qc.measure_all()
        return qc, True
    return qc, False

def circuit_to_qasm3(qc: QuantumCircuit) -> str:
    try:
        return qasm3_dumps(qc)
    except Exception as e:
        raise ValueError(f"QASM3 dump error: {e}")

def run_circuit(qc: QuantumCircuit) -> Dict[str, int]:
    try:
        simulator = AerSimulator()  # optionally: AerSimulator(method="statevector")
        qc, added_meas = _ensure_measurements(qc)
        tqc = transpile(qc, simulator, optimization_level=0)  # no smart rewrites
        job = simulator.run(tqc, shots=settings.num_shots)
        result = job.result()
        counts = result.get_counts()
        # Ensure dict[str,int]
        return {str(k): int(v) for k, v in counts.items()}
    except Exception as e:
        # Bubble up a clear message to your API
        raise RuntimeError(f"Execution error: {e}")


def circuit_to_text_diagram(qc: QuantumCircuit) -> str:
    """Render a simple ASCII diagram for the circuit.

    This avoids heavyweight deps (e.g., Matplotlib) and works in headless envs.
    """
    try:
        drawing = qc.draw(output="text")
        single = getattr(drawing, "single_string", None)
        if callable(single):
            return single()
        return str(drawing)
    except Exception as e:
        raise ValueError(f"Diagram render error: {e}")


def circuit_to_png_bytes(qc: QuantumCircuit) -> bytes:
    """Render the circuit to a PNG image and return its bytes.

    Uses Matplotlib backend in headless mode.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # headless
        import matplotlib.pyplot as plt

        fig = qc.draw(output="mpl")  # returns a Matplotlib Figure
        # Save to an in-memory buffer
        import io

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=200)
        plt.close(fig)
        return buf.getvalue()
    except Exception as e:
        raise ValueError(f"PNG render error: {e}")
