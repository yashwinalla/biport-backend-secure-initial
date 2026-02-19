import uuid
from typing import Optional
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.core.session import Base
from app.core.session import scoped_context
from app.core.config import logger
import base64

class StaleCredentials(Base):
    __tablename__ = "stale_credentials"
    __table_args__ = {"schema": "biporttest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    server_id = Column(UUID(as_uuid=True), nullable=False)
    pat_name = Column(String, nullable=False)
    pat_secret = Column(String, nullable=False)
    server_url = Column(String, nullable=False)
    site_name = Column(String, nullable=True)


class StaleCredentialsManager:

    @staticmethod
    def _encrypt_pat_secret(pat_secret: str) -> str:
        """Encodes the PAT secret using Base64 for simple obfuscation."""
        return base64.b64encode(pat_secret.encode('utf-8')).decode('utf-8')

    @staticmethod
    def _decrypt_pat_secret(encrypted_pat_secret: str) -> str:
        """Decodes the PAT secret from Base64."""
        return base64.b64decode(encrypted_pat_secret.encode('utf-8')).decode('utf-8')

    @staticmethod
    def add_record(
        id: uuid.UUID,
        server_id: uuid.UUID,
        pat_name: str,
        pat_secret: str,
        server_url: str,
        site_name: str = ""
    ) -> StaleCredentials:
        with scoped_context() as session:
            encrypted_pat_secret = StaleCredentialsManager._encrypt_pat_secret(pat_secret)
            record = StaleCredentials(
                id=id,
                server_id=server_id,
                pat_name=pat_name,
                pat_secret=encrypted_pat_secret,
                server_url=server_url,
                site_name=site_name
            )
            session.add(record)
            session.commit()
            logger.info(f"Added stale credential record for server_id: {server_id}")
            session.refresh(record)
            return record
    
    @staticmethod
    def get_record_by_server_id(server_id: uuid.UUID) -> Optional[StaleCredentials]:
        """Retrieves the first stale credential record for a given server ID and decrypts its secret."""
        with scoped_context() as session:
            record = session.query(StaleCredentials).filter(StaleCredentials.server_id == server_id).first()
            if record and record.pat_secret:
                record.pat_secret = StaleCredentialsManager._decrypt_pat_secret(record.pat_secret)
                return record
            logger.warning(f"No stale credential record found for server_id: {server_id}")
            return None
        
    @staticmethod
    def soft_delete_by_server_id(server_id: uuid.UUID):
        """Soft-delete credentials (but actually hard delete)"""
        with scoped_context() as session:
            creds = session.query(StaleCredentials).filter_by(server_id=server_id).all()
            if creds:
                logger.info(f"Deleting {len(creds)} stale credential records for server_id: {server_id}")
                for cred in creds:
                    session.delete(cred)
                session.commit()
            else:
                logger.info(f"No stale credentials to delete for server_id: {server_id}")

    @staticmethod
    def update_site_name(server_id: uuid.UUID, site_name: str):
        """Updates the site_name for a stale credential record."""
        with scoped_context() as session:
            record = session.query(StaleCredentials).filter(StaleCredentials.server_id == server_id).first()
            if record:
                record.site_name = site_name
                session.commit()
                logger.info(f"Updated site_name for stale credential record for server_id: {server_id}")
