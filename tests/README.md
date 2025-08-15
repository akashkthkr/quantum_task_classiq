# Tests

This suite validates the Qiskit example circuit and QASM3 round‑trip behavior.

## Run inside Docker (recommended)
```bash
# build API image (with deps) and start services
docker compose build api && docker compose up -d

# copy tests into the running API container (image contains /app only)
CID=$(docker compose ps -q api)
docker cp tests "$CID":/app/

# run all tests
docker compose exec -T api python -m pytest -q /app/tests

# run a single file
docker compose exec -T api python -m pytest -q /app/tests/test_qiskit_example.py

# run QASM3 round-trip test only
docker compose exec -T api python -m pytest -q /app/tests/test_qasm3_roundtrip.py


docker compose exec -T api python -m pytest -q /app/tests/test_heavy_qasm_cases.py | cat

```

## Run locally (no Docker)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q tests
```

## What’s covered
- `test_qiskit_example.py`: builds the Bell circuit, runs with `AerSimulator`,
  asserts total shots and roughly balanced counts across "00" and "11".
- `test_qasm3_roundtrip.py`: serializes a circuit with `qiskit.qasm3.dumps`,
  deserializes with `qiskit.qasm3.loads`, and checks structure is preserved.
