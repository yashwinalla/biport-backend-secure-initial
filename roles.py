import uuid
from sqlalchemy import Column, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.core.session import Base, scoped_context
from app.models.base import AuditMixin
from app.core.enums import RoleEnum
from app.core.exceptions import NotFoundError



class Role(Base, AuditMixin):
    __tablename__ = "roles"
    __table_args__ = {"schema": "biporttest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Enum(RoleEnum), nullable=False, unique=True)

class RoleManager:

    @staticmethod
    def get_role_name(role_id):
        with scoped_context() as session:
            row = session.query(Role.name).filter_by(id=role_id).first()
            if not row:
                raise NotFoundError(detail= "Role not found")
            return row[0].value
        

    @staticmethod
    def get_all_roles():
        with scoped_context() as session:
            return session.query(Role).all()
    
    @staticmethod
    def create_role(role_name):
        with scoped_context() as session:
            new_role = Role(name=role_name)
            session.add(new_role)
            session.commit()
            session.refresh(new_role)
            return new_role

    @staticmethod
    def get_role_info():
        with scoped_context() as session:
            return (
                session.query(Role)
                .filter(Role.name.notin_([RoleEnum.ADMIN]))
                .all()
            )
    
