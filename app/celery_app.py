from celery import Celery

from .config import settings

celery = Celery(
	"quantum_tasks",
	broker=settings.celery_broker_url,
	backend=settings.celery_result_backend,
)

celery.conf.update(
	task_serializer="json",
	result_serializer="json",
	accept_content=["json"],
	task_acks_late=True,
	worker_prefetch_multiplier=1,
)

# Import tasks to register
from . import worker_tasks  # noqa: E402,F401
