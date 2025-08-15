import json
import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from .celery_app import celery
from .db import SessionLocal, Task, TaskStatus
from .quantum import circuit_from_qasm3, run_circuit

logger = logging.getLogger("worker_tasks")


@celery.task(autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def execute_quantum_task(task_id: str) -> dict[str, Any]:
	session = SessionLocal()
	logger.info("task_received", extra={"task_id": task_id})
	try:
		task = session.get(Task, task_id)
		if task is None:
			raise RuntimeError(f"Task {task_id} not found")

		task.status = TaskStatus.RUNNING
		session.commit()
		logger.info("task_running", extra={"task_id": task_id})

		qc = circuit_from_qasm3(task.qc_qasm3)
		counts = run_circuit(qc)

		task.result_json = counts
		task.status = TaskStatus.COMPLETED
		session.commit()
		logger.info("task_completed", extra={"task_id": task_id, "result_keys": list(counts.keys())})

		return {"task_id": task_id, "result": counts}

	except Exception as exc:  # noqa: BLE001
		logger.exception("task_error", extra={"task_id": task_id})
		session.rollback()
		try:
			task = session.get(Task, task_id)
			if task is not None:
				task.status = TaskStatus.ERROR
				task.error_msg = str(exc)
				session.commit()
		except SQLAlchemyError:
			pass
		raise
	finally:
		session.close()
