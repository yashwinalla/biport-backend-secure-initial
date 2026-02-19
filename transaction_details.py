import uuid
from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.core.session import Base
from app.models.base import AuditMixin

class TransactionDetail(Base, AuditMixin):
    __tablename__ = "transaction_details"
    __table_args__ = {"schema": "biporttest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.organization_details.id"), nullable=False)
    credits_purchased = Column(Integer, nullable=False)
    amount = Column(String, nullable=False)
