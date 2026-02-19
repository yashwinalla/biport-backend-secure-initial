import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.session import Base, scoped_context
from app.models.base import AuditMixin
from app.core.enums import ServerStatus, ServerType, ServerAuthType
from app.core.session import scoped_context
from sqlalchemy.orm import joinedload


class TableauServerDetail(Base, AuditMixin):
    __tablename__ = "tableau_server_details"
    __table_args__ = {"schema": "biporttest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.organization_details.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.users.id"), nullable=False)
    name = Column(String, nullable=False)
    server_url = Column(String, nullable=False)
    status = Column(Enum(ServerStatus), nullable=False)
    type = Column(Enum(ServerType), nullable=False)

    report_count = Column(Integer, server_default=text("0"), nullable=False)
    project_count = Column(Integer, server_default=text("0"), nullable=False)
    site_count = Column(Integer, server_default=text("0"), nullable=False)

    # Relationships
    user = relationship("User")
    credentials = relationship("TableauServerCredential", back_populates="server", cascade="all, delete-orphan")

class TableauServerDetailManager:
    @staticmethod
    def get_servers_by_org_id(organization_id: uuid.UUID, offset: int = 0, limit: int = 10):
        """Fetch active servers for the organisation with pagination, excluding deleted ones."""
        with scoped_context() as session:
            return session.query(TableauServerDetail).filter(
                TableauServerDetail.organization_id == organization_id,
                TableauServerDetail.is_deleted == False,
                TableauServerDetail.status == ServerStatus.ACTIVE
            ).order_by(TableauServerDetail.updated_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_total_servers_by_org_id(organization_id: uuid.UUID) -> int:
        """Fetch the total number of active servers for a specific organisation, excluding deleted ones."""
        with scoped_context() as session:
            return session.query(TableauServerDetail).filter(
                TableauServerDetail.organization_id == organization_id,
                TableauServerDetail.is_deleted == False,
                TableauServerDetail.status == ServerStatus.ACTIVE
            ).count()
        
    @staticmethod
    def get_servers_by_org(organization_id: uuid.UUID, offset: int = 0, limit: int = 10):
        """Fetch active servers for the organisation with pagination, excluding deleted ones."""
        with scoped_context() as session:
            return session.query(TableauServerDetail).options(
                joinedload(TableauServerDetail.credentials)
            ).filter(
                TableauServerDetail.organization_id == organization_id,
                TableauServerDetail.is_deleted == False,
            ).order_by(TableauServerDetail.updated_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_total_servers_by_org(organization_id: uuid.UUID) -> int:
        """Fetch the total number of active servers for a specific organisation, excluding deleted ones."""
        with scoped_context() as session:
            return session.query(TableauServerDetail).filter(
                TableauServerDetail.organization_id == organization_id,
                TableauServerDetail.is_deleted == False,
            ).count()        

    @staticmethod
    def get_server_by_id(server_id: uuid.UUID) -> TableauServerDetail:
        """Fetch a server by its ID, excluding deleted ones."""
        with scoped_context() as session:
            return session.query(TableauServerDetail).filter(
                TableauServerDetail.id == server_id,
                TableauServerDetail.is_deleted == False
            ).first()
        
    @staticmethod
    def get_server_by_name_or_url(organization_id: uuid.UUID, name: str, server_url: str) -> TableauServerDetail:
        """Fetch a server by its name or URL for a specific organization, excluding deleted ones."""
        with scoped_context() as session:
            return session.query(TableauServerDetail).filter(
                TableauServerDetail.organization_id == organization_id,
                TableauServerDetail.is_deleted == False,
                ((TableauServerDetail.name == name) | (TableauServerDetail.server_url == server_url))
            ).first()        

    @staticmethod
    def add_server(organization_id: uuid.UUID, user_id: uuid.UUID, name: str, server_url: str, server_type: ServerType, created_by=None, updated_by=None) -> uuid.UUID:
        """Adds a new TableauServerDetail to the database and returns the new server's UUID."""
        server_id = uuid.uuid4()
        with scoped_context() as session:
            new_server = TableauServerDetail(
                id=server_id,
                organization_id=organization_id,
                user_id=user_id,
                name=name,
                server_url=server_url,
                status=ServerStatus.ACTIVE,
                type=server_type,
                created_by=created_by,
                updated_by=updated_by
            )
            session.add(new_server)
            session.commit()
            return server_id

    @staticmethod
    def update_server_status(server_id: uuid.UUID, status: ServerStatus):
        """Updates the status of a server."""
        with scoped_context() as session:
            server = session.query(TableauServerDetail).filter(
                TableauServerDetail.id == server_id,
                TableauServerDetail.is_deleted == False
            ).first()
            if server:
                server.status = status.value
                session.commit()
            else:
                raise ValueError("Server not found")

    # @staticmethod
    # def soft_delete_server(server_id: uuid.UUID):
    #     """Soft deletes a server and all related records by setting is_deleted=True."""
    #     from app.models.tableau_server import TableauServerCredentialManager, TableauSiteDetailManager
    #     from app.models.project_details import ProjectDetailManager
    #     from app.models.report_details import ReportDetailManager
    #     from app.models.report_analysis import ReportAnalysisManager
    #     from app.models.report_logs import ReportLogManager
    #     from app.core.session import scoped_context

    #     with scoped_context() as session:
    #         # 1. Soft-delete the server
    #         server = session.query(TableauServerDetail).filter(
    #             TableauServerDetail.id == server_id,
    #             TableauServerDetail.is_deleted == False
    #         ).first()
    #         if not server:
    #             raise ValueError("Server not found")
    #         setattr(server, 'is_deleted', True)

    #         TableauServerCredentialManager.soft_delete_by_server_id(server_id)
    #         credential_ids = TableauServerCredentialManager.get_ids_by_server_id(server_id)
    #         TableauSiteDetailManager.soft_delete_by_credentials_ids(credential_ids)
    #         ProjectDetailManager.soft_delete_by_server_id(server_id)
    #         project_ids = ProjectDetailManager.get_ids_by_server_id(server_id)
    #         ReportDetailManager.soft_delete_by_project_ids(project_ids)
    #         report_ids = ReportDetailManager.get_report_ids_by_project_ids(project_ids)
    #         ReportAnalysisManager.soft_delete_by_report_ids(report_ids)
    #         ReportLogManager.soft_delete_by_report_ids(report_ids)
            
    #         session.commit()


    @staticmethod
    def soft_delete_server(server_id: uuid.UUID, org_name: str):
        """
        Hard deletes a server, all projects, reports, logs, analyses,
        credentials, and sites. Archives S3 report objects before deletion.
        """
        from app.models.tableau_server import (
            TableauServerCredentialManager,
            TableauSiteDetailManager,
            TableauServerDetail
        )
        from app.models.project_details import ProjectDetail, ProjectDetailManager
        from app.core.session import scoped_context

        with scoped_context() as session:
            #  Find the server
            server = session.query(TableauServerDetail).filter(
                TableauServerDetail.id == server_id
            ).first()
            if not server:
                raise ValueError("Server not found")

            #  Get all projects under this server
            project_ids = (
                session.query(ProjectDetail.id)
                .filter(ProjectDetail.server_id == server_id)
                .all()
            )

            #  Hard delete each project (handles reports + logs + analysis + S3 archive)
            for (pid,) in project_ids:
                ProjectDetailManager.soft_delete_project_and_children(pid, org_name)

            #  Delete credentials and related sites in correct order
            credential_ids = TableauServerCredentialManager.get_ids_by_server_id(server_id)
            if credential_ids:                
                try:
                    # Delete sites first
                    TableauSiteDetailManager.soft_delete_by_credentials_ids(credential_ids)
                    # Delete credentials
                    TableauServerCredentialManager.soft_delete_by_server_id(server_id)
                except Exception as e:
                    raise

            #  Finally, delete the server itself
            try:
                session.delete(server)
                session.commit()
            except Exception as e:
                raise



class TableauServerCredential(Base, AuditMixin):
    __tablename__ = "tableau_server_credentials"
    __table_args__ = {"schema": "biporttest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    server_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.tableau_server_details.id"), nullable=False)

    pat_name = Column(String, nullable=True)
    pat_secret = Column(String, nullable=True)

    username = Column(String, nullable=True)
    password = Column(String, nullable=True)

    server_auth_type = Column(Enum(ServerAuthType), nullable=False)

    # Relationship
    server = relationship("TableauServerDetail", back_populates="credentials")
    sites = relationship("TableauSiteDetail", back_populates="credentials")


class TableauServerCredentialManager:
    @staticmethod
    def add_server_credential(server_id: uuid.UUID, auth_type: ServerAuthType, username: str = None, 
                             password: str = None, pat_name: str = None, pat_secret: str = None, created_by=None, updated_by=None) -> "TableauServerCredential":
        """Adds credentials for a TableauServerDetail."""
        with scoped_context() as session:
            credential = TableauServerCredential(
                id=uuid.uuid4(),
                server_id=server_id,
                server_auth_type=auth_type,
                username=username,
                password=password,
                pat_name=pat_name,
                pat_secret=pat_secret,
                created_by=created_by,
                updated_by=updated_by
            )
            session.add(credential)
            session.commit()
            session.refresh(credential)
            return credential 

    @staticmethod
    def get_by_server_id(server_id: uuid.UUID):
        """Fetch the first TableauServerCredential by server_id, or None if not found."""
        with scoped_context() as session:
            return session.query(TableauServerCredential).filter_by(server_id=server_id).first()

    @staticmethod
    def get_credential_id_by_server_id(server_id: uuid.UUID):
        """Return the id of the first TableauServerCredential for the given server_id, or None if not found."""
        credential = TableauServerCredentialManager.get_by_server_id(server_id)
        return credential.id if credential else None

    @staticmethod
    def get_all_by_server_id(server_id: uuid.UUID):
        """Return all TableauServerCredential objects for a given server_id."""
        with scoped_context() as session:
            return session.query(TableauServerCredential).filter_by(server_id=server_id).all()

    # @staticmethod
    # def soft_delete_by_server_id(server_id: uuid.UUID):
    #     """Soft delete all TableauServerCredential objects for a given server_id."""
    #     with scoped_context() as session:
    #         session.query(TableauServerCredential).filter_by(server_id=server_id).update({"is_deleted": True})
    #         session.commit()
    @staticmethod
    def soft_delete_by_server_id(server_id: uuid.UUID):
        """Soft-delete credentials (but actually hard delete)"""
        from app.models.tableau_server import TableauServerCredential
        from app.core.session import scoped_context

        with scoped_context() as session:
            creds = session.query(TableauServerCredential).filter_by(server_id=server_id).all()
            for cred in creds:
                session.delete(cred)
            session.commit()

    @staticmethod
    def get_ids_by_server_id(server_id: uuid.UUID):
        """Return all ids of TableauServerCredential objects for a given server_id."""
        with scoped_context() as session:
            return [c.id for c in session.query(TableauServerCredential).filter_by(server_id=server_id).all()]


class TableauSiteDetail(Base, AuditMixin):
    __tablename__ = "tableau_site_details"
    __table_args__ = {"schema": "biporttest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credentials_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.tableau_server_credentials.id"), nullable=False)
    site_name = Column(String, nullable=False)
    site_id = Column(UUID(as_uuid=True), nullable=False)

    # Relationships
    credentials = relationship("TableauServerCredential", back_populates="sites")

class TableauSiteDetailManager:
    @staticmethod
    def get_sites_by_server_id(server_id: UUID, offset: int = 0, limit: int = 10):
        with scoped_context() as session:
            return (
                session.query(TableauSiteDetail)
                .join(TableauServerCredential)
                .options(joinedload(TableauSiteDetail.credentials))
                .filter(
                    TableauSiteDetail.is_deleted == False,
                    TableauServerCredential.server_id == server_id
                )
                .order_by(TableauSiteDetail.updated_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

    @staticmethod
    def get_total_sites_by_server_id(server_id: UUID) -> int:
        with scoped_context() as session:
            return (
                session.query(TableauSiteDetail)
                .join(TableauServerCredential)
                .filter(
                    TableauSiteDetail.is_deleted == False,
                    TableauServerCredential.server_id == server_id
                )
                .count()
            )

    @staticmethod
    def add_site_detail(id: uuid.UUID, credentials_id: uuid.UUID, site_name: str, site_id: uuid.UUID, created_by=None, updated_by=None):
        """Add a TableauSiteDetail record and return it."""
        with scoped_context() as session:
            site_detail = TableauSiteDetail(
                id=id,
                credentials_id=credentials_id,
                site_name=site_name,
                site_id=site_id,
                created_by=created_by,
                updated_by=updated_by
            )
            session.add(site_detail)
            session.commit()
            session.refresh(site_detail)
            return site_detail 

    # @staticmethod
    # def soft_delete_by_credentials_ids(credentials_ids):
    #     """Soft delete all TableauSiteDetail objects for a list of credentials_ids."""
    #     if not credentials_ids:
    #         return
    #     with scoped_context() as session:
    #         session.query(TableauSiteDetail).filter(TableauSiteDetail.credentials_id.in_(credentials_ids)).update({"is_deleted": True}, synchronize_session=False)
    #         session.commit()

    @staticmethod
    def soft_delete_by_credentials_ids(credentials_ids):
        """Soft-delete sites (but actually hard delete)"""
        if not credentials_ids:
            return
        from app.models.tableau_server import TableauSiteDetail
        from app.core.session import scoped_context

        with scoped_context() as session:
            sites = session.query(TableauSiteDetail).filter(
                TableauSiteDetail.credentials_id.in_(credentials_ids)
            ).all()
            for site in sites:
                session.delete(site)
            session.commit()



    