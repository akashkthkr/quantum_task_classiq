import time
import requests


BASE = "http://localhost:8000"


SIZE_MISMATCH_QASM = (
    "OPENQASM 3.0;\n"
    "include \"stdgates.inc\";\n\n"
    "qubit[3] q; bit[2] c;\n"
    "measure q -> c;\n"
)


OUT_OF_RANGE_QASM = (
    "OPENQASM 3.0;\n"
    "include \"stdgates.inc\";\n\n"
    "qubit[2] q; bit[2] c; h q[0];\n"
    "measure q[0] -> c[2];\n"
)

INVALID_CONST_QASM = (
    "OPENQASM 3.0;\n"
    "include \"stdgates.inc\";\n\n"
    "qubit q; bit c;\n"
    "rz(pi/0) q;\n"  # division by zero during constant folding
    "measure q -> c;\n"
)

UNSUPPORTED_CONTROL_FLOW_QASM = (
    "OPENQASM 3.0;\n"
    "include \"stdgates.inc\";\n\n"
    "qubit q; bit c;\n"
    "for (int i = 0; i < 2; i++) { h q; }\n"  # deliberately non-QASM3 syntax
    "measure q -> c;\n"
)

UNKNOWN_GATE_QASM = (
    "OPENQASM 3.0;\n"
    "include \"stdgates.inc\";\n\n"
    "qubit q; bit c;\n"
    "cu1(pi/2) q, q;\n"
    "measure q -> c;\n"
)


def _submit(qasm: str) -> str:
    r = requests.post(f"{BASE}/tasks", json={"qc": qasm})
    assert r.status_code in (200, 202)
    return r.json()["task_id"]


def _wait_for_terminal(task_id: str, timeout_s: float = 20.0) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        g = requests.get(f"{BASE}/tasks/{task_id}")
        assert g.status_code in (200, 202, 404)
        data = g.json()
        if data.get("status") != "pending":
            return data
        time.sleep(0.5)
    return {"status": "pending"}


def test_qasm_size_mismatch_returns_error():
    tid = _submit(SIZE_MISMATCH_QASM)
    data = _wait_for_terminal(tid)
    assert data.get("status") == "error"
    assert "register size" in data.get("message", "").lower() or "parse" in data.get("message", "").lower()


def test_qasm_out_of_range_returns_error():
    tid = _submit(OUT_OF_RANGE_QASM)
    data = _wait_for_terminal(tid)
    assert data.get("status") == "error"
    assert "out of range" in data.get("message", "").lower() or "parse" in data.get("message", "").lower()


def test_qasm_invalid_constant_expression_returns_error():
    tid = _submit(INVALID_CONST_QASM)
    data = _wait_for_terminal(tid)
    assert data.get("status") == "error"
    # message may vary; look for divide/zero or parse
    msg = data.get("message", "").lower()
    assert any(k in msg for k in ["divide", "division", "zero", "parse"])


def test_qasm_unsupported_control_flow_returns_error():
    tid = _submit(UNSUPPORTED_CONTROL_FLOW_QASM)
    data = _wait_for_terminal(tid)
    assert data.get("status") == "error"
    assert "parse" in data.get("message", "").lower() or "unsupported" in data.get("message", "").lower()


def test_qasm_unknown_gate_returns_error():
    tid = _submit(UNKNOWN_GATE_QASM)
    data = _wait_for_terminal(tid)
    assert data.get("status") == "error"
    assert "cu1" in data.get("message", "").lower() or "unknown" in data.get("message", "").lower()


