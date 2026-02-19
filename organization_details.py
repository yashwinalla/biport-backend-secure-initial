import uuid
from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.session import Base
from app.models.base import AuditMixin
from app.core import scoped_context

class OrganizationDetail(Base, AuditMixin):
    __tablename__ = "organization_details"
    __table_args__ = {"schema": "biporttest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    credits = Column(Integer, default=0)
    contact_person_name = Column(String, nullable=False)
    mobile_number = Column(String, unique=True, nullable=False)
    address = Column(String, nullable=True)
    service_type = Column(String, nullable=True)

    # Relationships
    users = relationship("User", back_populates="organization")

class OrganizationDetailManager:
    @staticmethod
    def check_existing_mobile_or_name(mobile_number: str, name: str):
        """
        Check if an organization with the provided mobile number OR name (case-insensitive) exists.
        Returns the first matching organization, or None.
        """
        with scoped_context() as session:
            return session.query(OrganizationDetail).filter(
                (OrganizationDetail.mobile_number == mobile_number) |
                (OrganizationDetail.name.ilike(name))
            ).first()

    @staticmethod
    def create_new_organization(org_detail: OrganizationDetail):
        """Create a new organization record."""
        with scoped_context() as session:
            session.add(org_detail)
            session.commit()
            session.refresh(org_detail)
            return org_detail

    @staticmethod
    def get_name_by_id(org_id):
        from app.models.organization_details import OrganizationDetail
        from app.core.session import scoped_context
        with scoped_context() as session:
            org = session.query(OrganizationDetail).filter_by(id=org_id).first()
            return org.name if org else "unknown"
