"""
Lead Model - Érdeklődők követése
"""
from datetime import date
from typing import Optional
from sqlalchemy import String, Text, Date, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.base import BaseModelMixin


LEAD_STAGES = ['Új lead', 'Kapcsolatfelvétel', 'Ajánlat elküldve', 'Megnyert', 'Elveszett']


class Lead(db.Model, BaseModelMixin):
    __tablename__ = 'lead'

    lead_id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('tenant.tenant_id'), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    stage: Mapped[str] = mapped_column(String(50), default='Új lead')
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigned_worker_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('user.user_id'), nullable=True)
    created_date: Mapped[date] = mapped_column(Date, nullable=False)

    assigned_worker: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_worker_id])

    def to_dict(self):
        return {
            'lead_id': self.lead_id,
            'name': self.name,
            'phone': self.phone or '',
            'email': self.email or '',
            'source': self.source or '',
            'stage': self.stage,
            'notes': self.notes or '',
            'assigned_worker': f"{self.assigned_worker.first_name} {self.assigned_worker.last_name}" if self.assigned_worker else 'N/A',
            'created_date': self.created_date.strftime('%Y. %m. %d.') if self.created_date else 'N/A',
        }


from app.models.user import User
