from pydantic import BaseModel, Field
from typing import Dict, Optional


class SubmitTaskRequest(BaseModel):
	qc: str = Field(..., description="Serialized quantum circuit in QASM3")


class SubmitTaskResponse(BaseModel):
	task_id: str
	message: str = "Task submitted successfully."


class TaskCompletedResponse(BaseModel):
	status: str = "completed"
	result: Dict[str, int]


class TaskPendingResponse(BaseModel):
	status: str = "pending"
	message: str = "Task is still in progress."


class TaskErrorResponse(BaseModel):
	status: str = "error"
	message: str
