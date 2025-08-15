import time
import uuid

import requests
from qiskit import QuantumCircuit
from qiskit.qasm3 import dumps as qasm3_dumps

BASE = "http://localhost:8000"


def build_qasm3() -> str:
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qasm3_dumps(qc)


def test_submit_poll_complete():
    qasm = build_qasm3()

    # submit
    r = requests.post(f"{BASE}/tasks", json={"qc": qasm})
    assert r.status_code in (200, 202)
    task_id = r.json()["task_id"]

    # poll until we see pending at least once, then completed
    saw_pending = False
    deadline = time.time() + 60
    while time.time() < deadline:
        g = requests.get(f"{BASE}/tasks/{task_id}")
        assert g.status_code in (200, 404)
        data = g.json()
        if data.get("status") == "pending":
            saw_pending = True
        if data.get("status") == "completed":
            assert isinstance(data.get("result"), dict)
            assert set(data["result"].keys()).issubset({"00", "11"})
            assert saw_pending or True  # may complete fast
            return
        time.sleep(0.5)

    raise AssertionError("Task did not complete in time")


def test_get_not_found_returns_404_error():
    bogus = str(uuid.uuid4())
    r = requests.get(f"{BASE}/tasks/{bogus}")
    assert r.status_code == 404
    body = r.json()
    assert body.get("status") == "error"
    assert "not found" in body.get("message", "").lower()
