"""
Expense Model - Kiadások nyilvántartása
"""
from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Text, Date, Numeric, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.base import BaseModelMixin


class Expense(db.Model, BaseModelMixin):
    __tablename__ = 'expense'

    expense_id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('tenant.tenant_id'), nullable=True, index=True)
    worker_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('user.user_id'), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default='HUF')
    payment_source: Mapped[str] = mapped_column(String(50), nullable=False)  # magánpénztár / kölcsön / előleg
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)

    worker: Mapped[Optional["User"]] = relationship("User", foreign_keys=[worker_id])

    @property
    def worker_name(self):
        if self.worker:
            return getattr(self.worker, 'username', None) or \
                   f"{getattr(self.worker,'first_name','')} {getattr(self.worker,'last_name','')}".strip() or 'Ismeretlen'
        return '—'

    def to_dict(self):
        return {
            'expense_id': self.expense_id,
            'worker_name': self.worker_name,
            'amount': float(self.amount),
            'currency': self.currency,
            'payment_source': self.payment_source or '',
            'category': self.category or '',
            'notes': self.notes or '',
            'expense_date': self.expense_date.strftime('%Y. %m. %d.') if self.expense_date else 'N/A',
        }


from app.models.user import User
