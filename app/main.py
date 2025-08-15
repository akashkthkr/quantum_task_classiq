import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import init_db, SessionLocal, Task, TaskStatus
from .schemas import (
	SubmitTaskRequest,
	SubmitTaskResponse,
	TaskCompletedResponse,
	TaskPendingResponse,
	TaskErrorResponse,
)
from .celery_app import celery
from .worker_tasks import execute_quantum_task

app = FastAPI(title="Quantum Task API")


@app.on_event("startup")
def on_startup() -> None:
	init_db()


@app.get("/healthz")
def healthz() -> dict:
	return {"status": "ok"}


@app.post("/tasks", response_model=SubmitTaskResponse, status_code=202)
def submit_task(payload: SubmitTaskRequest) -> SubmitTaskResponse:
	if not payload.qc or len(payload.qc) > 200_000:
		raise HTTPException(status_code=400, detail="Invalid qc payload")

	task_id = str(uuid.uuid4())
	session = SessionLocal()
	try:
		task = Task(id=task_id, status=TaskStatus.PENDING, qc_qasm3=payload.qc)
		session.add(task)
		session.commit()
	finally:
		session.close()

	execute_quantum_task.delay(task_id)
	return SubmitTaskResponse(task_id=task_id)


@app.get("/tasks/{task_id}", responses={
	200: {"model": TaskCompletedResponse},
	202: {"model": TaskPendingResponse},
	404: {"model": TaskErrorResponse},
})
def get_task(task_id: str):
	session = SessionLocal()
	try:
		task = session.get(Task, task_id)
		if task is None:
			return JSONResponse(status_code=404, content=TaskErrorResponse(status="error", message="Task not found.").model_dump())

		if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
			return JSONResponse(status_code=200, content=TaskPendingResponse().model_dump())

		if task.status == TaskStatus.COMPLETED:
			return JSONResponse(status_code=200, content=TaskCompletedResponse(result=task.result_json or {}).model_dump())

		return JSONResponse(status_code=200, content=TaskErrorResponse(status="error", message=task.error_msg or "Unknown error").model_dump())
	finally:
		session.close()


# Serve the UI at /ui
app.mount("/ui", StaticFiles(directory="app/static", html=True), name="ui")
