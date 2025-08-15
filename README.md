# Quantum Task API

Asynchronous API to submit and execute Quantum Circuits (QASM3) using Qiskit. It provides:
- POST `/tasks` to submit a circuit
- GET `/tasks/{id}` to poll status/result
- Web UI at `/ui` to paste QASM3 and run interactively

## Tech stack
- FastAPI (API)
- Celery + Redis (async workers & broker)
- Postgres (task store)
- Qiskit + AerSimulator (execution)
- Docker Compose (orchestration)

## Quick start

Prereqs: Docker Desktop running.

```bash
# from repo root
docker compose build
docker compose up -d
# check health
curl http://localhost:8000/healthz
```

Open the UI: http://localhost:8000/ui

## Submit the example circuit (CLI)

We ship an example QASM3 at `examples/basic.qasm3`.

```bash
QASM=$(tr -d '\n' < examples/basic.qasm3 | sed 's/"/\\"/g')
# submit
curl -s -X POST http://localhost:8000/tasks \
  -H 'content-type: application/json' \
  --data-binary "{\"qc\": \"$QASM\"}"
# => {"task_id":"<uuid>","message":"Task submitted successfully."}

# poll
ID=<paste-task-id>
curl -s http://localhost:8000/tasks/$ID
```

## Testing

See the detailed test guide in [tests/README.md](tests/README.md).


## Endpoints
- POST `/tasks`
  - body: `{ "qc": "<QASM3 string>" }`
  - 202: `{ "task_id": "<uuid>", "message": "Task submitted successfully." }`
- GET `/tasks/{id}`
  - completed 200: `{ "status": "completed", "result": {"0": 512, "1": 512} }`
  - pending 200: `{ "status": "pending", "message": "Task is still in progress." }`
  - not found 404: `{ "status": "error", "message": "Task not found." }`

## Environment
Defaults are embedded in `docker-compose.yml`. If you need overrides, export env vars before `docker compose up`:
- `POSTGRES_*`, `REDIS_URL`, `CELERY_*`, `NUM_SHOTS` (default 1024)

## Local dev without Docker (optional)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export POSTGRES_HOST=localhost REDIS_URL=redis://localhost:6379/0 \
       CELERY_BROKER_URL=$REDIS_URL CELERY_RESULT_BACKEND=$REDIS_URL
# run API
uvicorn app.main:app --reload
# run worker (new shell)
celery -A app.celery_app.celery worker -l info
```

## Troubleshooting
- API not responding: `docker compose logs api | tail -n 200`
- Worker errors: `docker compose logs worker | tail -n 200`
- Rebuild after code changes: `docker compose build && docker compose up -d`

## Project layout
- `app/` – API, Celery worker, DB models, quantum helpers
- `app/static/` – UI served at `/ui`
- `examples/` – sample QASM3
- `docker-compose.yml`, `Dockerfile.api`, `Dockerfile.worker`

## License
MIT (exercise code).
