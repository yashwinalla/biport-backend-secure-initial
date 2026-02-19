import uuid
from datetime import datetime, timezone
from app.core.session import scoped_context
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.session import scoped_context,Base
from typing import Optional
from app.models.base import AuditMixin
from app.core.exceptions import AuthenticationError, AuthorizationError, ConflictError
from passlib.hash import bcrypt
from app.core.enums import RoleEnum, UserStatus
from app.models.roles import Role
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import psycopg2


class User(Base, AuditMixin):
    __tablename__ = "users"
    __table_args__ = {"schema": "biporttest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    phone_number = Column(String, nullable=False, unique=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    status = Column(String, nullable=True, default=UserStatus.ACTIVE.value)
    last_login = Column(DateTime, nullable=True)

    organization_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.organization_details.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.roles.id"), nullable=False)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.users.id"), nullable=True)

    # Relationships
    organization = relationship("OrganizationDetail", back_populates="users")
    role = relationship("Role")
    manager = relationship("User", remote_side="User.id", backref="subordinates")

    # Project relationships
    created_projects = relationship("ProjectDetail", foreign_keys="ProjectDetail.user_id", back_populates="creator")
    assigned_projects = relationship("ProjectDetail", foreign_keys="ProjectDetail.assigned_to", back_populates="assignee")

class UserManager:
    def __init__(
            self,
            name: str, 
            email: str, 
            password: str, 
            phone_number: str, 
            organization_id: UUID, 
            role_id: UUID, 
            manager_id: UUID
        ):
        self.name = name
        self.email = email
        self.password = password
        self.phone_number = phone_number
        self.organization_id = organization_id
        self.role_id = role_id
        self.manager_id = manager_id
    
    def add_user_details(self) -> None:
        """Add a new user or raise if email/phone already exists."""
        with scoped_context() as session:
            existing_user = (
                session.query(User)
                .filter((User.email == self.email) | (User.phone_number == self.phone_number))
                .first()
            )

            if existing_user:
                if existing_user.email == self.email:
                    raise ConflictError("Email already exists")
                if existing_user.phone_number == self.phone_number:
                    raise ConflictError("Phone number already exists")

            new_user = User(
                name=self.name,
                email=self.email,
                password=bcrypt.hash(self.password),
                phone_number=self.phone_number,
                organization_id=self.organization_id,
                role_id=self.role_id,
                manager_id=self.manager_id
                
            )
            session.add(new_user)
            session.commit()
    
    @staticmethod
    def get_user_by_email(email: str, load_role: bool = False) -> Optional[User]:
        """Fetch a user by their email (case-insensitive)."""
        with scoped_context() as session:
            query = session.query(User).filter(User.email.ilike(email))
            if load_role:
                from sqlalchemy.orm import joinedload
                query = query.options(joinedload(User.role), joinedload(User.organization))
            return query.first()

    @staticmethod
    def get_user_by_id_with_relations(user_id: str, session) -> Optional[User]:
        """Fetch a user by ID with role and organization loaded in the given session."""
        from sqlalchemy.orm import joinedload
        return session.query(User).options(
            joinedload(User.role),
            joinedload(User.organization)
        ).filter(User.id == user_id).first()
    
    @staticmethod
    def login_user(email: str, password: str) -> Optional[User]:
        """Authenticate user and update last_login timestamp."""
        with scoped_context() as session:
            user = session.query(User).filter(User.email.ilike(email)).first()
            if user is None:
                raise AuthenticationError("User not found.")
            if bcrypt.verify(password, user.password_hash):
                # Update last_login timestamp
                user.last_login = datetime.now(timezone.utc)
                session.commit()
                session.refresh(user)
                return user
            raise AuthenticationError("Incorrect password. Please try again.")

    @staticmethod
    def check_exists_email_mobile(data):
        with scoped_context() as session:
            email = data.email
            phone_number = data.phone_number
            return session.query(User).filter(
                (User.phone_number == phone_number) | (User.email.ilike(email))
            ).first()

    @staticmethod
    def add_user(data):
        with scoped_context() as session:
            # Get first_name and last_name from the request body
            first_name = getattr(data, 'first_name', None)
            last_name = getattr(data, 'last_name', None)
            
            # Combine first_name and last_name for the name column
            full_name = f"{first_name} {last_name}".strip() if first_name and last_name else None
            if not full_name:
                # Fallback: if either is missing, use what's available
                full_name = first_name or last_name or "Unknown User"
            
            user = User(
                id=uuid.uuid4(),
                name=full_name,
                email=data.email,
                password_hash=bcrypt.hash(data.password),
                phone_number=data.phone_number,
                first_name=first_name,
                last_name=last_name,
                organization_id=uuid.UUID(data.organization_id),
                role_id=uuid.UUID(data.role_id),
                manager_id=uuid.UUID(data.manager_id) if data.manager_id else None
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    @staticmethod
    def get_managers_by_organization(org_id: str):
        with scoped_context() as session:
            results = session.query(User.id, User.name).join(
                Role, User.role_id == Role.id
            ).filter(
                User.organization_id == org_id,
                Role.name == RoleEnum.MANAGER
            ).all()

            return results

    @staticmethod
    def get_managers_by_org_id(organization_id: UUID,page: int,page_size: int):
        offset = (page - 1) * page_size
        with scoped_context() as session:
            return (
                session.query(User)
                .filter(
                    User.organization_id == organization_id,
                    User.role.has(name=RoleEnum.MANAGER.value),
                    User.is_deleted == False
                )
                .order_by(User.name.asc())
                .offset(offset)
                .limit(page_size)
                .all()
            )
        
    @staticmethod
    def get_developers_by_org_and_manager_id(organization_id: UUID,manager_id: UUID,page: int,page_size: int):
        offset = (page - 1) * page_size
        with scoped_context() as session:
            return (
                session.query(User)
                .filter(
                    User.organization_id == organization_id,
                    User.manager_id == manager_id,
                    User.role.has(name=RoleEnum.DEVELOPER.value),
                    User.is_deleted == False
                )
                .order_by(User.name.asc())
                .offset(offset)
                .limit(page_size)
                .all()
            )

    @staticmethod
    def get_users_by_organization(org_id: str):
        with scoped_context() as session:
            results = session.query(
                User.id.label("id"),
                User.name.label("name"),
                User.email.label("email"),
                User.phone_number.label("phone_number"),
                User.first_name.label("first_name"),
                User.last_name.label("last_name"),
                User.status.label("status"),
                User.last_login.label("last_login"),
                User.role_id.label("role_id"),
                Role.name.label("role_name"),
                User.manager_id.label("manager_id"),
                User.organization_id.label("organization_id")
            ).join(
                Role, User.role_id == Role.id
            ).filter(
                User.organization_id == org_id
            ).all()

            return results

    @staticmethod
    def get_organization_counts(org_id: str):
        """Get user counts by role for an organization."""
        with scoped_context() as session:
            # Total users in organization
            total_users = session.query(User).filter(
                User.organization_id == org_id,
                User.is_deleted == False
            ).count()

            # Count by role
            admin_count = session.query(User).join(
                Role, User.role_id == Role.id
            ).filter(
                User.organization_id == org_id,
                Role.name == RoleEnum.ADMIN,
                User.is_deleted == False
            ).count()

            manager_count = session.query(User).join(
                Role, User.role_id == Role.id
            ).filter(
                User.organization_id == org_id,
                Role.name == RoleEnum.MANAGER,
                User.is_deleted == False
            ).count()

            developer_count = session.query(User).join(
                Role, User.role_id == Role.id
            ).filter(
                User.organization_id == org_id,
                Role.name == RoleEnum.DEVELOPER,
                User.is_deleted == False
            ).count()

            return {
                "total_users": total_users,
                "admins": admin_count,
                "managers": manager_count,
                "developers": developer_count
            }

    @staticmethod
    def update_user(user_id: str, user_data: dict, current_user: User):
        """Update user details with validation for self-update prevention."""
        with scoped_context() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise AuthenticationError("User not found")

            # Prevent users from updating their own details
            if str(user.id) == str(current_user.id):
                raise AuthorizationError("You are not authorized to update your own user details.")

            errors = []

            if "phone_number" in user_data:
                existing_phone_user = (
                    session.query(User)
                    .filter(User.phone_number == user_data["phone_number"], User.id != user_id)
                    .first()
                )
                if existing_phone_user:
                    errors.append("Phone number already exists")
                else:
                    user.phone_number = user_data["phone_number"]

            # Handle first_name and last_name updates
            first_name_updated = False
            last_name_updated = False
            
            if "first_name" in user_data:
                user.first_name = user_data["first_name"]
                first_name_updated = True

            if "last_name" in user_data:
                user.last_name = user_data["last_name"]
                last_name_updated = True

            # Update the combined name field if first_name or last_name changed
            if first_name_updated or last_name_updated:
                first_name = user.first_name or ""
                last_name = user.last_name or ""
                full_name = f"{first_name} {last_name}".strip()
                if full_name:
                    user.name = full_name
                else:
                    user.name = "Unknown User"

            if "role_id" in user_data:
                role = session.query(Role).filter(Role.id == user_data["role_id"]).first()
                if not role:
                    raise ValueError("Invalid role_id: Role not found")
                user.role_id = user_data["role_id"]

            if "manager_id" in user_data:
                manager = session.query(User).filter(User.id == user_data["manager_id"]).first()
                if not manager:
                    raise ValueError("Invalid manager_id: Manager not found")
                user.manager_id = user_data["manager_id"]

            if "status" in user_data:
                # Validate status value
                valid_statuses = [status.value for status in UserStatus]
                if user_data["status"] not in valid_statuses:
                    errors.append(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
                else:
                    user.status = user_data["status"]

            if errors:
                raise HTTPException(status_code=400, detail=errors)
            try:
                session.commit()
            except IntegrityError as e:
                session.rollback()
                raise HTTPException(status_code=400, detail=f"Database error: {str(e.orig)}")

    @staticmethod
    def get_developers_by_org_id(organization_id: UUID, page: int, page_size: int):
        offset = (page - 1) * page_size
        with scoped_context() as session:
            return (
                session.query(User)
                .filter(
                    User.organization_id == organization_id,
                    User.role.has(name=RoleEnum.DEVELOPER.value),
                    User.is_deleted == False
                )
                .order_by(User.name.asc())
                .offset(offset)
                .limit(page_size)
                .all()
            )
 
    @staticmethod
    def get_developers_by_orgid(organization_id: UUID, page: int, page_size: int):
        offset = (page - 1) * page_size
        with scoped_context() as session:
            return (
                session.query(User)
                .filter(
                    User.organization_id == organization_id,
                    User.role.has(name=RoleEnum.DEVELOPER.value),
                    User.is_deleted == False
                )
                .order_by(User.name.asc())
                .offset(offset)
                .limit(page_size)
                .all()
            )

    @staticmethod
    def get_total_managers_by_org_id(organization_id: UUID) -> int:
        with scoped_context() as session:
            return session.query(User).filter(
                User.organization_id == organization_id,
                User.role.has(name=RoleEnum.MANAGER.value),
                User.is_deleted == False
            ).count()

    @staticmethod
    def get_total_developers_by_org_id(organization_id: UUID) -> int:
        with scoped_context() as session:
            return session.query(User).filter(
                User.organization_id == organization_id,
                User.role.has(name=RoleEnum.DEVELOPER.value),
                User.is_deleted == False
            ).count()

    @staticmethod
    def get_total_developers_by_org_and_manager_id(organization_id: UUID, manager_id: UUID) -> int:
        with scoped_context() as session:
            return session.query(User).filter(
                User.organization_id == organization_id,
                User.manager_id == manager_id,
                User.role.has(name=RoleEnum.DEVELOPER.value),
                User.is_deleted == False
            ).count()

        
    @staticmethod
    def get_all_developer_ids_by_org_and_manager(organization_id: UUID, manager_id: UUID) -> list[str]:
        """
        Fetch all developer user IDs under a given manager within an organization.
        This method does NOT use pagination and returns all matching user IDs.
        """
        with scoped_context() as session:
            dev_ids = (
                session.query(User.id)
                .filter(
                    User.organization_id == organization_id,
                    User.manager_id == manager_id,
                    User.role.has(name=RoleEnum.DEVELOPER.value),
                    User.is_deleted == False
                )
                .all()
            )
            return [str(dev_id[0]) for dev_id in dev_ids]