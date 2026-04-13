"""
WorkerPayment Model - Munkás kifizetések
"""
from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Text, Date, Numeric, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.base import BaseModelMixin


class WorkerPayment(db.Model, BaseModelMixin):
    __tablename__ = 'worker_payment'

    payment_id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('tenant.tenant_id'), nullable=True, index=True)
    worker_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.user_id'), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default='HUF')
    payment_source: Mapped[str] = mapped_column(String(50), nullable=False)  # cash / bank / loan / advance
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)

    worker: Mapped["User"] = relationship("User", foreign_keys=[worker_id])

    def to_dict(self):
        return {
            'payment_id': self.payment_id,
            'worker_name': f"{self.worker.first_name} {self.worker.last_name}" if self.worker else 'N/A',
            'amount': float(self.amount),
            'currency': self.currency,
            'payment_source': self.payment_source,
            'notes': self.notes or '',
            'payment_date': self.payment_date.strftime('%Y. %m. %d.') if self.payment_date else 'N/A',
        }


class PerformanceConfirmation(db.Model, BaseModelMixin):
    __tablename__ = 'performance_confirmation'

    confirmation_id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('tenant.tenant_id'), nullable=True, index=True)
    worker_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.user_id'), nullable=False)
    month: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='Beadva')  # Beadva / Jóváhagyva
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    job_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('job.job_id'), nullable=True)

    worker: Mapped["User"] = relationship("User", foreign_keys=[worker_id])
    job: Mapped[Optional["Job"]] = relationship("Job", foreign_keys=[job_id])


from app.models.user import User
from app.models.job import Job
