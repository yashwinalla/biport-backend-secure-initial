import uuid
from sqlalchemy import Column, Integer, ForeignKey, Enum, text, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.session import Base
from app.models.base import AuditMixin
from app.core.enums import ComplexityTypeEnum
from app.core.session import scoped_context
from app.core.logger_setup import logger
from sqlalchemy import Column, Integer, ForeignKey, Enum, text, Boolean, String
from app.core.enums import ComplexityTypeEnum, PriorityEnum
from app.schemas import  ReportAnalysisUpdate
from app.core.session import scoped_context
 
class ReportAnalysis(Base, AuditMixin):
    __tablename__ = "report_analysis"
    __table_args__ = {"schema": "biporttest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    dashboard_count = Column(Integer, server_default=text("0"))
    worksheet_count = Column(Integer, server_default=text("0"))
    datasource_count = Column(Integer, server_default=text("0"))
    calculation_count = Column(Integer, server_default=text("0"))
    manual_migration_count = Column(Integer, server_default=text("0"))
    native_visuals = Column(Integer, server_default=text("0"))
    customVisuals = Column(Integer, server_default=text("0"))
    parameters = Column(Integer, server_default=text("0"))
    filters = Column(Integer, server_default=text("0"))
    migration = Column(String(10), server_default=text("Yes"))

    complexity_type = Column(Enum(ComplexityTypeEnum), nullable=True)
    priority = Column(String, nullable=True)

    report_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.report_details.id"), nullable=False)


    # Relationship
    report = relationship("ReportDetail", backref="analysis")


class ReportAnalysisManager:

    @staticmethod
    def update_report_analysis_counts(
        num_datasources=0,
        num_worksheets=0,
        num_dashboards=0,
        num_calculated_fields=0,
        num_native_visuals=0,
        num_custom_visuals=0,
        num_parameters=0,
        num_filters=0,
        report_id=None,
        complexity_type=None
    ):
        """Add or update report analysis with Tableau metadata counts based on report_id."""
        if not report_id:
            raise ValueError("report_id is required")

        with scoped_context() as session:
            try:
                report_analysis = session.query(ReportAnalysis).filter_by(
                    report_id=report_id
                ).first()

                if report_analysis:
                    # Update existing record
                    report_analysis.datasource_count = num_datasources
                    report_analysis.worksheet_count = num_worksheets
                    report_analysis.dashboard_count = num_dashboards
                    report_analysis.calculation_count = num_calculated_fields
                    report_analysis.native_visuals = num_native_visuals
                    report_analysis.customVisuals = num_custom_visuals  # keep camelCase since DB uses it
                    report_analysis.parameters = num_parameters
                    report_analysis.filters = num_filters
                    if complexity_type:
                        report_analysis.complexity_type = complexity_type
                else:
                    # Insert new record
                    report_analysis = ReportAnalysis(
                        report_id=report_id,
                        datasource_count=num_datasources,
                        worksheet_count=num_worksheets,
                        dashboard_count=num_dashboards,
                        calculation_count=num_calculated_fields,
                        native_visuals=num_native_visuals,
                        customVisuals=num_custom_visuals,  # camelCase preserved
                        parameters=num_parameters,
                        filters=num_filters,
                        complexity_type=complexity_type
                    )
                    session.add(report_analysis)

                session.commit()

                logger.info(
                    f"[ReportAnalysis] Updated counts for report_id={report_id}: "
                    f"datasources={num_datasources}, worksheets={num_worksheets}, dashboards={num_dashboards}, "
                    f"calculated_fields={num_calculated_fields}, native_visuals={num_native_visuals}, "
                    f"customVisuals={num_custom_visuals}, parameters={num_parameters}, filters={num_filters}, "
                    f"complexity_type={complexity_type}"
                )

                return True

            except Exception as e:
                session.rollback()
                logger.error(
                    f"[ReportAnalysis] Failed to update counts for report_id={report_id}: {e}",
                    exc_info=True
                )
                return False


    
    @staticmethod
    def update_migration_status(report_id: UUID, migration_status: str, session) -> bool:
        """
        Update migration status for a given report_id.

        Args:
            report_id (UUID): ID of the report to update
            migration_status (str): 'Yes' or 'No'
            session: SQLAlchemy session

        Returns:
            bool: True if update successful, False if no rows updated
        """
        try:
            # Normalize status (keep DB consistent)
            normalized_status = migration_status.strip().capitalize()  # Yes / No

            updated_rows = (
                session.query(ReportAnalysis)
                .filter(ReportAnalysis.report_id == report_id)
                .update({"migration": normalized_status})
            )
            session.commit()

            return updated_rows > 0
        except Exception as e:
            session.rollback()
            logger.error(f"[ReportAnalysisManager] Failed to update migration status for report {report_id}: {e}")
            raise

    @staticmethod
    def get_report(report_id):
        from app.models.report_analysis import ReportAnalysis
        from app.core.session import scoped_context

        with scoped_context() as session:
            return session.query(ReportAnalysis).filter(
                ReportAnalysis.report_id == report_id,
                ReportAnalysis.is_deleted == False
            ).first()
 
    @staticmethod
    def update_report(report, payload):
        from app.core.session import scoped_context
        from app.models.report_analysis import ReportAnalysis

        with scoped_context() as session:
            # Re-fetch the report in the current session context
            report_in_session = session.query(ReportAnalysis).filter(
                ReportAnalysis.report_id == report.report_id,
                ReportAnalysis.is_deleted == False
            ).first()
            
            if not report_in_session:
                raise ValueError("Report not found in current session")
            
            updated = False
 
            if payload.complexity_type is not None and payload.complexity_type != report_in_session.complexity_type:
                report_in_session.complexity_type = payload.complexity_type.value if hasattr(payload.complexity_type, 'value') else payload.complexity_type
                updated = True
 
            if payload.migration is not None and payload.migration != report_in_session.migration:
                report_in_session.migration = payload.migration.value if hasattr(payload.migration, 'value') else payload.migration
                updated = True
 
            if payload.priority is not None and payload.priority != report_in_session.priority:
                report_in_session.priority = payload.priority.value if hasattr(payload.priority, 'value') else payload.priority
                updated = True
 
            if updated:
                session.commit()
                session.refresh(report_in_session)

            return report_in_session
    
    @staticmethod
    def get_lookup_options():
        from app.models.report_analysis import ReportAnalysis
        from app.core.session import scoped_context

        with scoped_context() as session:
            complexity_options = session.query(
                ReportAnalysis.complexity_type
            ).distinct().all()

            priority_options = session.query(
                ReportAnalysis.priority
            ).distinct().all()

        complexity_options = [c[0] for c in complexity_options if c[0] is not None]
        priority_options = [p[0] for p in priority_options if p[0] is not None]

        return {
            "complexity_options": complexity_options,
            "priority_options": priority_options
        }
    
    @staticmethod
    def soft_delete_by_report_ids(report_ids):
        """Soft delete all ReportAnalysis objects for a list of report_ids."""
        if not report_ids:
            return
        from app.models.report_analysis import ReportAnalysis
        from app.core.session import scoped_context
        with scoped_context() as session:
            session.query(ReportAnalysis).filter(ReportAnalysis.report_id.in_(report_ids)).update({"is_deleted": True}, synchronize_session=False)
            session.commit()
    