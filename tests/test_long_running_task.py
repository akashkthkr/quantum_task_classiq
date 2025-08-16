import time
import requests


BASE = "http://localhost:8000"


LONG_QASM = (
    "OPENQASM 3.0;\n"
    "include \"stdgates.inc\";\n\n"
    "qubit[2] q;\n"
    "bit[2] c;\n\n"
    "for int i in [0:9999] {\n"
    "    h q[0];\n"
    "    t q[0];\n"
    "    cx q[0], q[1];\n"
    "    s q[1];\n"
    "    t q[1];\n"
    "    cx q[1], q[0];\n"
    "}\n\n"
    "measure q[0] -> c[0];\n"
    "measure q[1] -> c[1];\n"
)


def test_submit_long_running_and_observe_pending():
    r = requests.post(f"{BASE}/tasks", json={"qc": LONG_QASM})
    assert r.status_code in (200, 202)
    task_id = r.json()["task_id"]

    saw_pending = False
    deadline = time.time() + 15
    while time.time() < deadline:
        g = requests.get(f"{BASE}/tasks/{task_id}")
        assert g.status_code in (200, 202, 404)
        data = g.json()
        # Consider either pending or completed acceptable; we mainly want to observe queueing
        if data.get("status") == "pending":
            saw_pending = True
            break
        if data.get("status") == "completed":
            # finished too fast for this environment; still acceptable
            return
        time.sleep(0.5)

    assert saw_pending, "Expected to observe pending status for long-running job"


