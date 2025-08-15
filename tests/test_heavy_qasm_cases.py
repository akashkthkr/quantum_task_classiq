import time
import requests


BASE = "http://localhost:8000"


HEAVY_8Q_QASM = (
    "OPENQASM 3.0;\n"
    "include \"stdgates.inc\";\n\n"
    "qubit[8] q;\n"
    "bit[8] c;\n\n"
    "// Initialize with single-qubit non-Cliffords\n"
    "h q[0]; h q[1]; h q[2]; h q[3]; h q[4]; h q[5]; h q[6]; h q[7];\n"
    "t q[0]; t q[2]; t q[4]; t q[6];\n"
    "tdg q[1]; tdg q[3]; tdg q[5]; tdg q[7];\n\n"
    "// ====== BEGIN HEAVY BLOCK (repeat this whole block many times) ======\n"
    "barrier q;\n"
    "// Entangle in a ladder\n"
    "cx q[0], q[1]; cx q[1], q[2]; cx q[2], q[3]; cx q[3], q[4];\n"
    "cx q[4], q[5]; cx q[5], q[6]; cx q[6], q[7]; cx q[7], q[0];\n\n"
    "// Non-Clifford single-qubit rotations\n"
    "rz(3.141592653589793/3) q[0];\n"
    "rz(3.141592653589793/5) q[1];\n"
    "rz(3.141592653589793/7) q[2];\n"
    "rz(3.141592653589793/9) q[3];\n"
    "rz(3.141592653589793/11) q[4];\n"
    "rz(3.141592653589793/13) q[5];\n"
    "rz(3.141592653589793/15) q[6];\n"
    "rz(3.141592653589793/17) q[7];\n\n"
    "// More entanglement to frustrate simulators\n"
    "cx q[0], q[2]; cx q[2], q[4]; cx q[4], q[6]; cx q[6], q[0];\n"
    "cx q[1], q[3]; cx q[3], q[5]; cx q[5], q[7]; cx q[7], q[1];\n\n"
    "// Toffoli chain introduces costly non-Cliffords\n"
    "ccx q[0], q[1], q[2];\n"
    "ccx q[2], q[3], q[4];\n"
    "ccx q[4], q[5], q[6];\n"
    "ccx q[6], q[7], q[0];\n\n"
    "// Phase sprinkling\n"
    "t q[0]; t q[1]; t q[2]; t q[3]; t q[4]; t q[5]; t q[6]; t q[7];\n"
    "tdg q[0]; tdg q[2]; tdg q[4]; tdg q[6];\n\n"
    "barrier q;\n"
    "// ====== END HEAVY BLOCK ======\n\n"
    "// Final measurements\n"
    "measure q[0] -> c[0];\n"
    "measure q[1] -> c[1];\n"
    "measure q[2] -> c[2];\n"
    "measure q[3] -> c[3];\n"
    "measure q[4] -> c[4];\n"
    "measure q[5] -> c[5];\n"
    "measure q[6] -> c[6];\n"
    "measure q[7] -> c[7];\n"
)


HEAVY_3Q_QASM = (
    "OPENQASM 3.0;\n"
    "include \"stdgates.inc\";\n\n"
    "qubit[3] q;\n"
    "bit[3] c;\n\n"
    "// Repeat this block by copy paste to increase runtime\n"
    "h q[0]; t q[0];\n"
    "cx q[0], q[1]; t q[1];\n"
    "cx q[1], q[2]; tdg q[2];\n"
    "cx q[2], q[0]; rz(3.141592653589793/3) q[0];\n"
    "cx q[0], q[2]; s q[2];\n"
    "cx q[2], q[1]; rz(3.141592653589793/5) q[1];\n\n"
    "measure q[0] -> c[0];\n"
    "measure q[1] -> c[1];\n"
    "measure q[2] -> c[2];\n"
)


def _submit(qasm: str) -> str:
    r = requests.post(f"{BASE}/tasks", json={"qc": qasm})
    assert r.status_code in (200, 202)
    return r.json()["task_id"]


def _poll(task_id: str, deadline_s: float = 30.0) -> dict:
    deadline = time.time() + deadline_s
    while time.time() < deadline:
        g = requests.get(f"{BASE}/tasks/{task_id}")
        assert g.status_code in (200, 404)
        data = g.json()
        if data.get("status") != "pending":
            return data
        time.sleep(0.5)
    return {"status": "pending"}


def test_heavy_8q_observe_pending_or_complete():
    task_id = _submit(HEAVY_8Q_QASM)
    data = _poll(task_id, deadline_s=20.0)
    # Either we saw pending (common) or it completed; both are acceptable
    assert data.get("status") in {"pending", "completed"}
    if data.get("status") == "completed":
        assert isinstance(data.get("result"), dict)
        # If completed, keys should be 8-bit strings
        assert all(len(k) == 8 for k in data["result"].keys())


def test_heavy_3q_completes_or_pending_short_window():
    task_id = _submit(HEAVY_3Q_QASM)
    data = _poll(task_id, deadline_s=30.0)
    assert data.get("status") in {"pending", "completed"}
    if data.get("status") == "completed":
        assert isinstance(data.get("result"), dict)
        assert all(len(k) == 3 for k in data["result"].keys())


