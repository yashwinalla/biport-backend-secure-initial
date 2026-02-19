import uuid
from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.session import Base
from app.models.base import AuditMixin

class DatasourceDetail(Base, AuditMixin):
    __tablename__ = "datasource_details"
    __table_args__ = {"schema": "biporttest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.organization_details.id"), nullable=False)
    credentials = Column(JSON, nullable=True)
