import string
import uuid
from sqlalchemy import Column, DateTime, Enum, String, Boolean, Integer, ForeignKey, func, text, or_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.session import Base
from app.models.base import AuditMixin
from app.core.enums import ComplexityTypeEnum, ReportStatusEnum
from app.core.session import scoped_context
from app.core.logger_setup import logger
from datetime import datetime
from typing import Optional, List
from uuid import UUID as PyUUID
from datetime import datetime

class ReportLog(Base):
    __tablename__ = "report_logs"
    __table_args__ = {"schema": "biporttest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.report_details.id"), nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    status = Column(String(50), nullable=False)
    message = Column(String(500), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("biporttest.users.id"), nullable=False)
    is_deleted = Column(Boolean, server_default=text("false"))
 
    # relationships
    report = relationship("ReportDetail", back_populates="logs")
    user = relationship("User")
  

def add_report_log(session, report_id, status: str, message: str, created_by):
    log = ReportLog(
        report_id=report_id,
        timestamp=datetime.utcnow(),
        status=status,
        message=message,
        created_by=created_by
    )
    session.add(log)
    session.commit()


class ReportLogManager:
    """Manager class for handling report logs in the database"""
    
    @staticmethod
    def _normalize_status(status: str) -> str:
        """Normalize any incoming status to one of: info, success, error.

        This ensures consistent log types in the database regardless of
        where logs are written from (analysis, dax, migrate, workspace).
        """
        if not status:
            return "info"
        s = str(status).strip().lower()

        success_aliases = {
            "success", "succeeded", "ok", "completed", "complete", "done", "SUCCESS"
            "analysis_completed", "dax_calculation_completed", "migration_completed", "migrated"
        }
        error_aliases = {
            "error", "failure", "failed",
            "analysis_failed", "dax_calculation_failed"
        }
        info_aliases = {
            "info", "in_progress", "progress", "started", "start",
            "migration_started", "analysis_started", "dax_calculation_in_progress"
        }

        if s in success_aliases:
            return "success"
        if s in error_aliases:
            return "error"
        if s in info_aliases:
            return "info"
        return "info"
    
    
    @staticmethod
    def create_log(
        report_id: PyUUID,
        status: str,
        message: str,
        created_by: Optional[PyUUID] = None,
        session=None
    ) -> ReportLog:
        try:
            normalized_status = ReportLogManager._normalize_status(status)
            if session is None:
                with scoped_context() as db_session:
                    log_entry = ReportLog(
                        report_id=report_id,
                        timestamp=datetime.utcnow(),
                        status=normalized_status,
                        message=message,
                        created_by=created_by
                    )
                    db_session.add(log_entry)
                    db_session.commit()
                    logger.info(f"Created report log: {normalized_status} - {message} for report {report_id}")
                    return log_entry
            else:
                log_entry = ReportLog(
                    report_id=report_id,
                    timestamp=datetime.utcnow(),
                    status=normalized_status,
                    message=message,
                    created_by=created_by
                )
                session.add(log_entry)
                session.commit()
                logger.info(f"Created report log: {normalized_status} - {message} for report {report_id}")
                return log_entry
        except Exception as e:
            logger.error(f"Failed to create report log: {e}", exc_info=True)
            if session:
                session.rollback()
            raise

    @staticmethod
    def get_report_logs(
        report_id: PyUUID,
        limit: int = 100,
        session=None
    ) -> List[ReportLog]:
        """
        Get all logs for a specific report, ordered by timestamp (latest first)
        
        Args:
            report_id: UUID of the report
            limit: Maximum number of logs to return
            session: Database session (optional)
        
        Returns:
            List[ReportLog]: List of log entries
        """
        try:
            if session is None:
                session = scoped_context()
            
            logs = session.query(ReportLog).filter(
                ReportLog.report_id == report_id
            ).order_by(
                ReportLog.timestamp.desc()
            ).limit(limit).all()
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get report logs: {e}", exc_info=True)
            raise

    @staticmethod
    def log_migration_start(
        report_id: PyUUID,
        user_id: Optional[PyUUID] = None,
        session=None
    ) -> ReportLog:
        """Log the start of migration process"""
        return ReportLogManager.create_log(
            report_id=report_id,
            status="MIGRATION_STARTED",
            message="Migration process initiated",
            created_by=user_id,
            session=session
        )
    
    @staticmethod
    def log_migration_success(
        report_id: PyUUID,
        user_id: Optional[PyUUID] = None,
        details: str = "Migration completed successfully",
        session=None
    ) -> ReportLog:
        """Log successful migration completion"""
        # If details is the default value, just use it directly
        if details == "Migration completed successfully":
            message = details
        else:
            message = f"Migration completed: {details}"
        return ReportLogManager.create_log(
            report_id=report_id,
            status="SUCCESS",
            message=message,
            created_by=user_id,
            session=session
        )
    
    @staticmethod
    def log_migration_failure(
        report_id: PyUUID,
        error_message: str,
        user_id: Optional[PyUUID] = None,
        session=None
    ) -> ReportLog:
        """Log migration failure"""
        return ReportLogManager.create_log(
            report_id=report_id,
            status="FAILURE",
            message=f"Migration failed: {error_message}",
            created_by=user_id,
            session=session
        )
    
    @staticmethod
    def log_migration_progress(
        report_id: PyUUID,
        progress_message: str,
        user_id: Optional[PyUUID] = None,
        session=None
    ) -> ReportLog:
        """Log migration progress updates"""
        return ReportLogManager.create_log(
            report_id=report_id,
            status="IN_PROGRESS",
            message=f"Migration progress: {progress_message}",
            created_by=user_id,
            session=session
        )
    
    @staticmethod
    def log_dax_conversion_start(
        report_id: PyUUID,
        user_id: Optional[PyUUID] = None,
        session=None
    ) -> ReportLog:
        """Log the start of DAX conversion process"""
        return ReportLogManager.create_log(
            report_id=report_id,
            status="DAX_CALCULATION_IN_PROGRESS",
            message="DAX conversion process initiated",
            created_by=user_id,
            session=session
        )
    
    @staticmethod
    def log_dax_conversion_success(
        report_id: PyUUID,
        user_id: Optional[PyUUID] = None,
        details: str = "DAX conversion completed successfully",
        session=None
    ) -> ReportLog:
        """Log successful DAX conversion completion"""
        # If details is the default value, just use it directly
        if details == "DAX conversion completed successfully":
            message = details
        else:
            message = f"DAX conversion completed: {details}"
        return ReportLogManager.create_log(
            report_id=report_id,
            status="DAX_CALCULATION_COMPLETED",
            message=message,
            created_by=user_id,
            session=session
        )
    
    @staticmethod
    def log_dax_conversion_failure(
        report_id: PyUUID,
        error_message: str,
        user_id: Optional[PyUUID] = None,
        session=None
    ) -> ReportLog:
        """Log DAX conversion failure"""
        return ReportLogManager.create_log(
            report_id=report_id,
            status="DAX_CALCULATION_FAILED",
            message=f"DAX conversion failed: {error_message}",
            created_by=user_id,
            session=session
        )
    
    @staticmethod
    def log_analysis_start(
        report_id: PyUUID,
        user_id: Optional[PyUUID] = None,
        session=None
    ) -> ReportLog:
        """Log the start of analysis process"""
        return ReportLogManager.create_log(
            report_id=report_id,
            status="ANALYSIS_STARTED",
            message="Analysis process initiated",
            created_by=user_id,
            session=session
        )
    
    @staticmethod
    def log_analysis_success(
        report_id: PyUUID,
        user_id: Optional[PyUUID] = None,
        details: str = "Analysis completed successfully",
        session=None
    ) -> ReportLog:
        """Log successful analysis completion"""
        # If details is the default value, just use it directly
        if details == "Analysis completed successfully":
            message = details
        else:
            message = f"Analysis completed: {details}"
        return ReportLogManager.create_log(
            report_id=report_id,
            status="ANALYSIS_COMPLETED",
            message=message,
            created_by=user_id,
            session=session
        )
    
    @staticmethod
    def log_analysis_failure(
        report_id: PyUUID,
        error_message: str,
        user_id: Optional[PyUUID] = None,
        session=None
    ) -> ReportLog:
        """Log analysis failure"""
        return ReportLogManager.create_log(
            report_id=report_id,
            status="ANALYSIS_FAILED",
            message=f"Analysis failed: {error_message}",
            created_by=user_id,
            session=session
        )

    @staticmethod
    def log_semantic_model_start(
        report_id: PyUUID,
        user_id: Optional[PyUUID] = None,
        session=None
    ) -> ReportLog:
        """Log the start of semantic model process"""
        return ReportLogManager.create_log(
            report_id=report_id,
            status="SEMANTIC_MODEL_STARTED",
            message="Semantic model generation initiated",
            created_by=user_id,
            session=session
        )
    
    @staticmethod
    def log_semantic_model_success(
        report_id: PyUUID,
        user_id: Optional[PyUUID] = None,
        details: str = "Semantic model completed successfully",
        session=None
    ) -> ReportLog:
        """Log successful semantic model completion"""
        return ReportLogManager.create_log(
            report_id=report_id,
            status="SEMANTIC_MODEL_COMPLETED",
            message=f"Semantic model completed successfully: {details}",
            created_by=user_id,
            session=session
        )
    
    @staticmethod
    def log_semantic_model_failure(
        report_id: PyUUID,
        error_message: str,
        user_id: Optional[PyUUID] = None,
        session=None
    ) -> ReportLog:
        """Log semantic model failure"""
        return ReportLogManager.create_log(
            report_id=report_id,
            status="SEMANTIC_MODEL_FAILED",
            message=f"Semantic model generation failed: {error_message}",
            created_by=user_id,
            session=session
        )

    @staticmethod
    def soft_delete_by_report_ids(report_ids):
        """Soft delete all ReportLog objects for a list of report_ids."""
        if not report_ids:
            return
        from app.models.report_logs import ReportLog
        from app.core.session import scoped_context
        with scoped_context() as session:
            session.query(ReportLog).filter(ReportLog.report_id.in_(report_ids)).update({"is_deleted": True}, synchronize_session=False)
            session.commit()
