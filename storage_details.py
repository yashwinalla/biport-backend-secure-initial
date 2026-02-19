import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.session import Base
from app.models.base import AuditMixin

class StorageDetail(Base, AuditMixin):
    __tablename__ = "storage_details"
    __table_args__ = {"schema": "biporttest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storage_type = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    secret_key = Column(String, nullable=False)
    bucket_name = Column(String, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.organization_details.id"), nullable=False)
