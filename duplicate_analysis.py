import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import and_
from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.session import Base
from app.core.session import scoped_context

from app.models.project_details import ProjectDetail
from app.models.users import User


class DuplicateAnalysis(Base):
    __tablename__ = "duplicate_analysis"
    __table_args__ = {"schema": "biporttest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    report_id = Column(UUID(as_uuid=True), nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    workbook_name = Column(String, nullable=False)
    dashboard_name = Column(String, nullable=False)
    visual_name = Column(String, nullable=False)
    visual_type = Column(String, nullable=False)
    visual_datasource = Column(String, nullable=False)
    sheet_name = Column(String, nullable=False)
    datasource_type = Column(String, nullable=False)
    rows = Column(Text, nullable=True)      
    columns = Column(Text, nullable=True) 
    created_at = Column(DateTime, nullable=True)
    type = Column(String, nullable=False)


class DuplicateAnalysisManager:

    @staticmethod
    def is_duplicate(
        organization_id: uuid.UUID,
        report_id: uuid.UUID,
        workbook_name: str,
        dashboard_name: str,
        visual_name: str,
        sheet_name: str,
        visual_type: str,
        visual_datasource: str,
        datasource_type: str,
        type: str,
        rows: Optional[str] = None,
        columns: Optional[str] = None,
    ) -> bool:
        with scoped_context() as session:
            exists = session.query(DuplicateAnalysis).filter(
                and_(
                    DuplicateAnalysis.organization_id == organization_id,
                    DuplicateAnalysis.report_id == report_id,
                    DuplicateAnalysis.workbook_name == workbook_name,
                    DuplicateAnalysis.dashboard_name == dashboard_name,
                    DuplicateAnalysis.visual_name == visual_name,
                    DuplicateAnalysis.sheet_name == sheet_name,
                    DuplicateAnalysis.visual_type == visual_type,
                    DuplicateAnalysis.visual_datasource == visual_datasource,
                    DuplicateAnalysis.datasource_type == datasource_type,
                    DuplicateAnalysis.rows == rows,
                    DuplicateAnalysis.columns == columns,
                    DuplicateAnalysis.type == type
                )
            ).first()
            return exists is not None

    @staticmethod
    def add_record(
        id: uuid.UUID,
        organization_id: uuid.UUID,
        report_id: uuid.UUID,
        workbook_name: str,
        dashboard_name: str,
        visual_name: str,
        sheet_name: str,
        visual_type: str,
        visual_datasource: str,
        type: str,
        datasource_type: str,
        rows: Optional[str] = None,
        columns: Optional[str] = None,
        created_at: Optional[datetime] = None
    ) -> DuplicateAnalysis:
        with scoped_context() as session:
            record = DuplicateAnalysis(
                id=id,
                organization_id=organization_id,
                report_id=report_id,
                workbook_name=workbook_name,
                dashboard_name=dashboard_name,
                visual_name=visual_name,
                sheet_name=sheet_name,
                visual_type=visual_type,
                type=type,
                visual_datasource=visual_datasource,
                datasource_type=datasource_type,
                rows=rows,
                columns=columns,
                created_at=created_at
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        
    @staticmethod
    def delete_duplicate_analysis(report_id):
        """
        Delete duplicate analysis entries for a given report ID.
        """
        if not report_id:
            return
        
        with scoped_context() as session:
            duplicate_analyses = session.query(DuplicateAnalysis).filter(DuplicateAnalysis.report_id == report_id).all()
            for analysis in duplicate_analyses:
                session.delete(analysis)

            session.commit()

    @staticmethod
    def get_visual_counts_by_org(org_id: str) -> dict:
        """
        Get total count of native and custom visuals for the given organization.
        """

        with scoped_context() as session:
            counts = (
                session.query(DuplicateAnalysis.visual_type, DuplicateAnalysis.type, func.count(DuplicateAnalysis.id))
                .filter(DuplicateAnalysis.organization_id == org_id)
                .group_by(DuplicateAnalysis.visual_type,DuplicateAnalysis.type)
                .all()
            )

            counts_map = {t: c for _, t, c in counts}
            custom_items = [
                (visual_type, c)
                for visual_type, t, c in counts
                if t == "custom"
            ]
            ncustom_items = [
                (visual_type, c)
                for visual_type, t, c in counts
                if t == "native"
            ]
            visual_types = [v for v, c in custom_items]
            distinct_count = len(set(visual_types))
            native_count = len(ncustom_items)
            return {"native": native_count, "custom": distinct_count}
    
    @staticmethod
    def get_raw_visual_list(org_id: str) -> list:
        """
        Grouped by (workbook_name, visual_type, type)
        Returns project names and workbook names
        """
        from app.models.report_details import ReportDetail
        from app.models.project_details import ProjectDetail

        with scoped_context() as session:
            results = (
                session.query(
                    DuplicateAnalysis.visual_type,
                    DuplicateAnalysis.type,
                    DuplicateAnalysis.workbook_name,
                    func.array_agg(ProjectDetail.name).label("project_names"),
                    func.array_agg(DuplicateAnalysis.workbook_name).label("workbook_names"),
                )
                .join(
                    ReportDetail,
                    DuplicateAnalysis.report_id == ReportDetail.id
                )
                .join(
                    ProjectDetail,
                    ReportDetail.project_id == ProjectDetail.id
                )
                .filter(DuplicateAnalysis.organization_id == org_id)
                .group_by(
                    DuplicateAnalysis.visual_type,
                    DuplicateAnalysis.type,
                    DuplicateAnalysis.workbook_name
                )
                .all()
            )

            return results