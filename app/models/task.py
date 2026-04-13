"""
Task Model - Feladatok kezelése
"""
from datetime import date
from typing import Optional
from sqlalchemy import String, Text, Date, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.base import BaseModelMixin


class Task(db.Model, BaseModelMixin):
    __tablename__ = 'task'

    task_id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('tenant.tenant_id'), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigned_worker_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('user.user_id'), nullable=True)
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    job_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('job.job_id'), nullable=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_date: Mapped[date] = mapped_column(Date, nullable=False)

    assigned_worker: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_worker_id])
    job: Mapped[Optional["Job"]] = relationship("Job", foreign_keys=[job_id])

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description or '',
            'assigned_worker': f"{self.assigned_worker.first_name} {self.assigned_worker.last_name}" if self.assigned_worker else 'N/A',
            'deadline': self.deadline.strftime('%Y. %m. %d.') if self.deadline else 'N/A',
            'job_id': self.job_id,
            'done': self.done,
            'created_date': self.created_date.strftime('%Y. %m. %d.') if self.created_date else 'N/A',
        }


from app.models.user import User
from app.models.job import Job
