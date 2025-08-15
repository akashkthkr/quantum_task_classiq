from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, Enum as SAEnum, Text, JSON, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import settings


class Base(DeclarativeBase):
	pass


class TaskStatus:
	PENDING = "pending"
	RUNNING = "running"
	COMPLETED = "completed"
	ERROR = "error"


class Task(Base):
	__tablename__ = "tasks"

	id: Mapped[str] = mapped_column(primary_key=True)
	status: Mapped[str] = mapped_column(
		SAEnum(
			TaskStatus.PENDING,
			TaskStatus.RUNNING,
			TaskStatus.COMPLETED,
			TaskStatus.ERROR,
			name="task_status",
		),
		default=TaskStatus.PENDING,
	)
	submitted_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
	updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
	qc_qasm3: Mapped[str] = mapped_column(Text)
	result_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
	error_msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

	__table_args__ = (
		Index("idx_tasks_status_submitted", "status", "submitted_at"),
	)


engine = create_engine(settings.sqlalchemy_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
	Base.metadata.create_all(bind=engine)
