import time
import threading

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


def submit(qasm: str) -> str:
    r = requests.post(f"{BASE}/tasks", json={"qc": qasm})
    r.raise_for_status()
    data = r.json()
    assert "task_id" in data
    return data["task_id"]


def get(task_id: str) -> dict:
    r = requests.get(f"{BASE}/tasks/{task_id}")
    assert r.status_code in (200, 202, 404)
    return r.json()


def test_concurrent_submissions_complete_without_loss():
    qasm = build_qasm3()

    num_tasks = 8
    task_ids: list[str] = []

    # submit concurrently
    def worker():
        tid = submit(qasm)
        task_ids.append(tid)

    threads = [threading.Thread(target=worker) for _ in range(num_tasks)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(task_ids) == num_tasks

    # poll until all complete
    deadline = time.time() + 60
    done: set[str] = set()
    while time.time() < deadline and len(done) < num_tasks:
        for tid in task_ids:
            if tid in done:
                continue
            data = get(tid)
            if data.get("status") == "completed":
                done.add(tid)
        time.sleep(0.5)

    assert len(done) == num_tasks
