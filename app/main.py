import uuid
import logging
from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

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
logger = logging.getLogger("api")


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
		logger.info("task_enqueued", extra={"task_id": task_id})
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
			logger.info("task_not_found", extra={"task_id": task_id})
			return JSONResponse(status_code=404, content=TaskErrorResponse(status="error", message="Task not found.").model_dump())

		if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
			logger.info("task_pending", extra={"task_id": task_id, "status": task.status})
			return JSONResponse(status_code=200, content=TaskPendingResponse().model_dump())

		if task.status == TaskStatus.COMPLETED:
			logger.info("task_result", extra={"task_id": task_id})
			return JSONResponse(status_code=200, content=TaskCompletedResponse(result=task.result_json or {}).model_dump())

		logger.info("task_error_state", extra={"task_id": task_id})
		return JSONResponse(status_code=200, content=TaskErrorResponse(status="error", message=task.error_msg or "Unknown error").model_dump())
	finally:
		session.close()


# Serve the UI at /ui
app.mount("/ui", StaticFiles(directory="app/static", html=True), name="ui")


@app.get("/admin/tasks")
def list_tasks(x_admin_password: str | None = Header(default=None, alias="x-admin-password"), password: str | None = Query(default=None)):
	secret = x_admin_password or password
	if secret != "classiq":
		raise HTTPException(status_code=401, detail="Unauthorized")

	session = SessionLocal()
	try:
		stmt = select(Task).order_by(Task.submitted_at.desc())
		tasks = session.execute(stmt).scalars().all()
		data = []
		for t in tasks:
			data.append({
				"id": t.id,
				"status": t.status,
				"submitted_at": t.submitted_at.isoformat() if t.submitted_at else None,
				"updated_at": t.updated_at.isoformat() if t.updated_at else None,
				"has_result": bool(t.result_json),
				"error_msg": t.error_msg,
			})
		return {"tasks": data}
	finally:
		session.close()


@app.get("/admin", include_in_schema=False)
def admin_page():
	return FileResponse("app/static/admin.html", media_type="text/html")


@app.get("/admin/tasks/{task_id}/qasm3")
def download_task_qasm3(task_id: str, x_admin_password: str | None = Header(default=None, alias="x-admin-password"), password: str | None = Query(default=None)):
	secret = x_admin_password or password
	if secret != "classiq":
		raise HTTPException(status_code=401, detail="Unauthorized")

	session = SessionLocal()
	try:
		task = session.get(Task, task_id)
		if task is None:
			raise HTTPException(status_code=404, detail="Task not found")
		content = task.qc_qasm3 or ""
		filename = f"{task_id}.qasm"
		return PlainTextResponse(content, media_type="text/plain", headers={
			"Content-Disposition": f"attachment; filename=\"{filename}\""
		})
	finally:
		session.close()
