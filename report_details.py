import uuid
import asyncio
import os
from datetime import datetime
from fastapi import BackgroundTasks
from sqlalchemy import Column, DateTime, Enum, String, Boolean, Integer, ForeignKey, func, text, or_, case
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Query, joinedload, aliased
from sqlalchemy import Enum as PgEnum
from app.core.session import scoped_context
from app.core.enums import ReportStatusEnum, RoleEnum, OperationStatus
from app.models.users import User
from app.core.session import Base, logger
from app.models.base import AuditMixin
from app.models.project_details import ProjectDetail
from app.models.tableau_server import TableauServerDetailManager, TableauSiteDetail
import asyncio
from app.services.analysis.dashboard import determine_report_complexity
from app.core.session import scoped_context
from app.models.report_analysis import ReportAnalysis
from app.models.duplicate_analysis import DuplicateAnalysisManager
from app.models.report_logs import ReportLog
import threading
import queue

class ReportDetail(Base, AuditMixin):
    __tablename__ = "report_details"
    __table_args__ = {"schema": "biporttest"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    report_id = Column(UUID(as_uuid=True), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("biporttest.project_details.id"), nullable=False)
    report_type = Column(String(5), nullable=True)

    is_analyzed = Column(Boolean, server_default=text("false"))
    analyzed_status = Column(String, nullable=True)
    is_converted = Column(Boolean, server_default=text("false"))
    converted_status = Column(String, nullable=True)
    is_migrated = Column(Boolean, server_default=text("false"))
    migrated_status = Column(String, nullable=True)
    is_semantic = Column(Boolean, server_default=text("false"))
    semantic_status = Column(String, nullable=True)
    unit_tested = Column(Boolean, server_default=text("false"))
    uat_tested = Column(Boolean, server_default=text("false"))
    deployed = Column(Boolean, server_default=text("false"))
    is_scoped = Column(Boolean, server_default=text("false"))
    semantic_type = Column(String, nullable=True)
    has_semantic_model = Column(Boolean, server_default=text("false"))
    view_count = Column(Integer, server_default=text("0"))
    tableau_usercount = Column(Integer, server_default=text("0"))
    tableau_report_createdat = Column(DateTime, nullable=True)
    tableau_report_updatedat = Column(DateTime, nullable=True)
    tableau_report_last_viewed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    tableau_report_createdat = Column(DateTime, nullable=True)
    tableau_report_updatedat = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("biporttest.users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("biporttest.users.id"), nullable=True)
    is_deleted = Column(Boolean, server_default=text("false"))
    report_status = Column(
        PgEnum(
            ReportStatusEnum,
            name="report_status_enum",
            values_callable=lambda enum: [e.value for e in enum],
            create_type=False,
        ),
        nullable=True,
    )

    project = relationship("ProjectDetail", back_populates="reports")
    logs = relationship("ReportLog", back_populates="report", cascade="all, delete-orphan")

    @staticmethod
    def get_reports_by_user_role(session, user, role_name: str) -> Query:
        query = session.query(ReportDetail).join(ProjectDetail, ReportDetail.project_id == ProjectDetail.id).options(joinedload(ReportDetail.project))

        Creator = aliased(User)

        if role_name.lower() == RoleEnum.ADMIN.value.lower():
            pass
        elif role_name.lower() == RoleEnum.MANAGER.value.lower():
            subordinate_ids = session.query(User.id).filter(User.manager_id == user.id).all()
            subordinate_ids = [sid[0] for sid in subordinate_ids]
            query = query.filter(
                or_(
                    ProjectDetail.assigned_to == user.id,
                    ProjectDetail.assigned_to.in_(subordinate_ids)
                )
            )
        elif role_name.lower() == RoleEnum.DEVELOPER.value.lower():
            query = query.filter(ProjectDetail.assigned_to == user.id)

        query = query.join(Creator, ProjectDetail.creator).filter(
            Creator.organization_id == user.organization_id
        )

        return query.distinct()

class ReportDetailManager:
    @staticmethod
    def add_report(id, name, report_id, project_id, created_by=None, updated_by=None, view_count=0, created_at=None, updated_at=None, tableau_report_createdat=None,tableau_report_updatedat=None, report_type=None, session=None):
        from app.models.report_details import ReportDetail
        from app.core.session import scoped_context
        import pytz
        
        # Convert string timestamps to datetime objects if provided
        if created_at and isinstance(created_at, str):
            try:
                # Parse ISO format timestamp from Tableau (e.g., "2025-08-15T08:57:58Z")
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError as e:
                logger.warning(f"Failed to parse created_at timestamp '{created_at}': {e}")
                created_at = None
                
        if updated_at and isinstance(updated_at, str):
            try:
                # Parse ISO format timestamp from Tableau (e.g., "2025-08-15T08:57:59Z")
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            except ValueError as e:
                logger.warning(f"Failed to parse updated_at timestamp '{updated_at}': {e}")
                updated_at = None
        
        if session is None:
            with scoped_context() as session:
                report = ReportDetail(
                    id=id,
                    name=name,
                    report_id=report_id,
                    project_id=project_id,
                    created_by=created_by,
                    updated_by=updated_by,
                    view_count=view_count,
                    report_type=report_type,
                    tableau_report_createdat=tableau_report_createdat,
                    tableau_report_updatedat=tableau_report_updatedat
                )
                
                # Set custom timestamps if provided, otherwise let database handle defaults
                if created_at:
                    report.created_at = created_at
                if updated_at:
                    report.updated_at = updated_at
                
                session.add(report)
                session.commit()
                session.refresh(report)
                return report
        else:
            report = ReportDetail(
                id=id,
                name=name,
                report_id=report_id,
                project_id=project_id,
                created_by=created_by,
                updated_by=updated_by,
                view_count=view_count,
                report_type=report_type,
                tableau_report_createdat=tableau_report_createdat,
                tableau_report_updatedat=tableau_report_updatedat
            )
            
            # Set custom timestamps if provided, otherwise let database handle defaults
            if created_at:
                report.created_at = created_at
            if updated_at:
                report.updated_at = updated_at
            
            session.add(report)
            session.flush()
            session.refresh(report)
            return report
        

    @staticmethod
    def update_last_viewed_dates(updates: list[dict]):
        """
        Updates the tableau_report_last_viewed column for a list of reports.
        
        Args:
            updates: List of dictionaries containing 'report_id' and 'last_viewed'.
        """
        
        if not updates:
            return 0

        logger.info(f"Updating last viewed dates for {len(updates)} reports.")
        updated_count = 0
        
        with scoped_context() as session:
            for item in updates:
                try:
                    report_id_val = item.get("report_id")
                    last_viewed_val = item.get("last_viewed")
                    
                    if not report_id_val or not last_viewed_val:
                        continue
                        
                    result = session.query(ReportDetail).filter(
                        ReportDetail.report_id == report_id_val
                    ).update(
                        {ReportDetail.tableau_report_last_viewed: last_viewed_val},
                        synchronize_session=False
                    )
                    updated_count += result
                except ValueError:
                    logger.warning(f"Invalid UUID format for report_id: {item.get('report_id')}")
                except Exception as e:
                    logger.error(f"Error updating report {item.get('report_id')}: {e}")
            
            session.commit()
            
        logger.info(f"Successfully updated {updated_count} reports with last viewed dates.")
        return updated_count

    @staticmethod
    def update_tableau_usercount(updates: list[dict]):
        """
        Updates the tableau_usercount column for a list of reports.
        
        Args:
            updates: List of dictionaries containing 'report_id' and 'tableau_usercount'.
        """
        
        if not updates:
            return 0

        logger.info(f"Updating tableau_usercount for {len(updates)} reports.")
        updated_count = 0
        
        with scoped_context() as session:
            for item in updates:
                try:
                    report_id_val = item.get("report_id")
                    tableau_usercount_val = item.get("tableau_usercount")
                    
                    if not report_id_val or tableau_usercount_val is None:
                        continue
                        
                    result = session.query(ReportDetail).filter(
                        ReportDetail.report_id == report_id_val
                    ).update(
                        {ReportDetail.tableau_usercount: tableau_usercount_val},
                        synchronize_session=False
                    )
                    updated_count += result
                except ValueError:
                    logger.warning(f"Invalid UUID format for report_id: {item.get('report_id')}")
                except Exception as e:
                    logger.error(f"Error updating report {item.get('report_id')}: {e}")
                    raise e
            
            session.commit()
            
        logger.info(f"Successfully updated {updated_count} reports with last viewed dates.")
        return updated_count

    # @staticmethod
    # def soft_delete_by_project_ids(project_ids):
    #     if not project_ids:
    #         return
    #     from app.models.report_details import ReportDetail
    #     from app.core.session import scoped_context
    #     with scoped_context() as session:
    #         session.query(ReportDetail).filter(ReportDetail.project_id.in_(project_ids)).update({"is_deleted": True}, synchronize_session=False)
    #         session.commit()

    @staticmethod
    def soft_delete_by_project_ids(project_ids):
        """
        Delete all reports for given projects.
        """
        # from app.models.report_details import ReportDetail

        if not project_ids:
            return

        session = scoped_context()

        reports = session.query(ReportDetail).filter(ReportDetail.project_id.in_(project_ids)).all()
        for report in reports:
            ReportDetailManager.soft_delete_report(report.id, db=session)
            session.commit()

    @staticmethod
    def get_report_ids_by_project_ids(project_ids):
        """Get all report IDs for the given project IDs."""
        if not project_ids:
            return []
        from app.models.report_details import ReportDetail
        from app.core.session import scoped_context
        with scoped_context() as session:
            reports = session.query(ReportDetail.id).filter(ReportDetail.project_id.in_(project_ids)).all()
            return [report[0] for report in reports]

           

      
    @staticmethod
    def get_report_hierarchy_path(project_id: UUID, report_name: str) -> str:
        """
        Recursively builds the project path from root to leaf using parent_id chain,
        and appends the report name at the end.
        Example output: "RootFolder/SubFolder/ProjectName/ReportName"
        """
        try:
            with scoped_context() as session:
                path_parts = []
                current_project = session.query(ProjectDetail).filter(ProjectDetail.id == project_id).first()
                while current_project:
                    path_parts.insert(0, current_project.name)
                    if not current_project.parent_id:
                        break
                    current_project = session.query(ProjectDetail).filter(ProjectDetail.id == current_project.parent_id).first()

                # Append report name at the end
                if report_name:
                    path_parts.append(report_name.strip())

                return "/".join(path_parts)
        except Exception as e:
            logger.exception(f"Failed to build project path for project_id {project_id}: {e}")
            return ""
    
    @staticmethod
    def get_root_project_name(project_id: UUID) -> str:
        """
        Returns only the root project name for the given project_id.
        Walks up the parent_id chain until it finds the root.
        """
        try:
            with scoped_context() as session:
                current_project = session.query(ProjectDetail).filter(ProjectDetail.id == project_id).first()
                if not current_project:
                    return ""

                # Walk up to the root
                while current_project.parent_id:
                    current_project = session.query(ProjectDetail).filter(
                        ProjectDetail.id == current_project.parent_id
                    ).first()

                return current_project.name.strip() if current_project else ""
        except Exception as e:
            logger.exception(f"Failed to get root project name for project_id {project_id}: {e}")
            return ""


    @staticmethod
    def mark_analyzed(report_id: str, status: OperationStatus = OperationStatus.SUCCESS, message: str = ""):
        try:
            with scoped_context() as session:
                db_report = session.query(ReportDetail).filter(ReportDetail.id == report_id).first()
                if db_report:
                    if status == OperationStatus.SUCCESS:
                        db_report.is_analyzed = True
                        db_report.analyzed_status = ReportStatusEnum.ANALYSIS_COMPLETED.value
                        db_report.report_status = ReportStatusEnum.ANALYSIS_COMPLETED.value
                    else:
                        db_report.is_analyzed = False
                        db_report.analyzed_status = ReportStatusEnum.ANALYSIS_FAILED.value
                        db_report.report_status = ReportStatusEnum.ANALYSIS_FAILED.value

                    session.commit()
                    logger.info(f"Report {report_id} marked as analyzed: {status.value}")
        except Exception as e:
            logger.exception(f"Failed to update analyzed status for report {report_id}: {e}")


    @staticmethod
    def mark_converted(report_id: str, status: OperationStatus = OperationStatus.SUCCESS, message: str = ""):
        try:
            with scoped_context() as session:
                db_report = session.query(ReportDetail).filter(ReportDetail.id == report_id).first()
                if db_report:
                    db_report.is_converted = (status == OperationStatus.SUCCESS)
                    db_report.converted_status = ReportStatusEnum.DAX_CALCULATION_COMPLETED.value

                    if status == OperationStatus.SUCCESS:
                        db_report.report_status = ReportStatusEnum.DAX_CALCULATION_COMPLETED.value
                    else:
                        db_report.report_status = ReportStatusEnum.DAX_CALCULATION_FAILED.value

                    session.commit()
                    logger.info(f"Report {report_id} marked as converted (DAX): {status.value}")
        except Exception as e:
            logger.exception(f"Failed to update converted status for report {report_id}: {e}")


    @staticmethod
    def mark_migrated(report_id: str, status: OperationStatus = OperationStatus.SUCCESS, message: str = ""):
        try:
            with scoped_context() as session:
                db_report = session.query(ReportDetail).filter(ReportDetail.id == report_id).first()
                if db_report:
                    db_report.is_migrated = (status == OperationStatus.SUCCESS)
                    db_report.migrated_status = ReportStatusEnum.MIGRATED.value

                    if status == OperationStatus.SUCCESS:
                        db_report.report_status = ReportStatusEnum.MIGRATED.value
                    else:
                        db_report.report_status = ReportStatusEnum.MIGRATION_FAILED.value

                    session.commit()
                    logger.info(f"Report {report_id} marked as migrated: {status.value}")
        except Exception as e:
            logger.exception(f"Failed to update migrated status for report {report_id}: {e}")


    @staticmethod
    def mark_semantic(report_id: str, status: OperationStatus = OperationStatus.SUCCESS, message: str = ""):
        try:
            with scoped_context() as session:
                db_report = session.query(ReportDetail).filter(ReportDetail.id == report_id).first()
                if db_report:
                    db_report.is_semantic = (status == OperationStatus.SUCCESS)
                    db_report.semantic_status = ReportStatusEnum.SEMANTIC_MODEL_COMPLETED.value

                    if status == OperationStatus.SUCCESS:
                        db_report.report_status = ReportStatusEnum.SEMANTIC_MODEL_COMPLETED
                    else:
                        db_report.report_status = ReportStatusEnum.SEMANTIC_MODEL_FAILED

                    session.commit()
                    logger.info(f"Report {report_id} marked as semantic: {status.value}")
        except Exception as e:
            logger.exception(f"Failed to update semantic status for report {report_id}: {e}")


    # @staticmethod
    # def soft_delete_report(report_id):
    #     from app.models.report_details import ReportDetail
    #     from app.core.session import scoped_context
    #     with scoped_context() as session:
    #         session.query(ReportDetail).filter(ReportDetail.id == report_id).update({"is_deleted": True}, synchronize_session=False)
    #         session.commit()

    # @staticmethod
    # def soft_delete_report(report_id,org_name):
    #     """
    #     Hard delete a report along with its analysis and logs.
    #     Archives all S3 objects under the report's prefix to a central archive folder, then deletes originals.
    #     """
    #     from app.models.report_details import ReportDetail
    #     from app.models.report_analysis import ReportAnalysis
    #     from app.models.report_logs import ReportLog
    #     from app.core.config import S3Config
    #     from app.core.session import scoped_context
    #     import asyncio

    #     logger.info(f"[soft_delete_report] Starting delete process for report_id={report_id}")

    #     with scoped_context() as session:
    #         # Fetch report
    #         report = session.query(ReportDetail).filter(ReportDetail.id == report_id).first()
    #         if not report:
    #             logger.warning(f"[soft_delete_report] Report not found in DB for report_id={report_id}")
    #             return {"message": "Report not found", "report_id": report_id}

    #         logger.info(f"[soft_delete_report] Found report in DB: id={report.id}, name={report.name}")

    #         # Delete Report Logs
    #         deleted_logs = session.query(ReportLog).filter(
    #             ReportLog.report_id == report_id
    #         ).delete(synchronize_session=False)
    #         logger.info(f"[soft_delete_report] Deleted {deleted_logs} logs for report_id={report_id}")

    #         # Delete Report Analysis
    #         deleted_analysis = session.query(ReportAnalysis).filter(
    #             ReportAnalysis.report_id == report_id
    #         ).delete(synchronize_session=False)
    #         logger.info(f"[soft_delete_report] Deleted {deleted_analysis} analysis rows for report_id={report_id}")
    #         DuplicateAnalysisManager.delete_duplicate_analysis(report.id)

    #         # Archive and delete S3 objects
    #         if report.name:
    #             logger.info(f"[soft_delete_report] Preparing to archive S3 objects for report {report_id}")
    #             s3_config = S3Config()

    #             async def archive_and_delete():
    #                 try:
    #                     async with s3_config.get_s3_client() as s3_client:
    #                         # Prefix for all objects of this report
    #                         source_prefix = f"BI-Portfinal/{org_name}/{report.report_id}/"
    #                         archive_prefix = f"BI-Portfinal/Archive/{org_name}/{report.report_id}/"

    #                         logger.info(f"[soft_delete_report] Source prefix = {source_prefix}")
    #                         logger.info(f"[soft_delete_report] Archive prefix = {archive_prefix}")

    #                         # List all objects under the source prefix
    #                         continuation_token = None
    #                         objects_found = False

    #                         while True:
    #                             list_kwargs = {"Bucket": s3_config.bucket_name, "Prefix": source_prefix}
    #                             if continuation_token:
    #                                 list_kwargs["ContinuationToken"] = continuation_token

    #                             resp = await s3_client.list_objects_v2(**list_kwargs)
    #                             contents = resp.get("Contents", [])

    #                             if not contents:
    #                                 logger.warning(f"[soft_delete_report] No objects found under prefix {source_prefix}")

    #                             for obj in contents:
    #                                 objects_found = True
    #                                 key = obj["Key"]
    #                                 dest_key = key.replace(source_prefix, archive_prefix, 1)

    #                                 logger.info(f"[soft_delete_report] Copying {key} → {dest_key}")
    #                                 await s3_client.copy_object(
    #                                     Bucket=s3_config.bucket_name,
    #                                     CopySource={"Bucket": s3_config.bucket_name, "Key": key},
    #                                     Key=dest_key
    #                                 )

    #                                 logger.info(f"[soft_delete_report] Deleting original S3 object: {key}")
    #                                 await s3_client.delete_object(Bucket=s3_config.bucket_name, Key=key)

    #                             if resp.get("IsTruncated"):
    #                                 continuation_token = resp.get("NextContinuationToken")
    #                             else:
    #                                 break

    #                         if objects_found:
    #                             logger.info(f"[soft_delete_report] Archived all objects under {source_prefix} to {archive_prefix}")
    #                         else:
    #                             logger.warning(f"[soft_delete_report] No objects to archive for report {report_id}")

    #                 except Exception as e:
    #                     logger.exception(f"[soft_delete_report] ERROR while archiving/deleting S3 objects: {e}")
    #                     raise

    #             try:
    #                 loop = asyncio.get_event_loop()
    #                 if loop.is_running():
    #                     loop.create_task(archive_and_delete())   # FastAPI case
    #                 else:
    #                     loop.run_until_complete(archive_and_delete())  # script case
    #             except Exception as e:
    #                 logger.error(f"[soft_delete_report] Skipping S3 archive/delete due to error for report_id={report_id}: {e}")
    #         # Delete ReportDetail (main report row)
    #         logger.info(f"[soft_delete_report] Deleting report record from DB for report_id={report_id}")
    #         session.delete(report)
    #         session.commit()
    #         logger.info(f"[soft_delete_report] Successfully deleted report_id={report_id} from DB")

    #         return {"message": "Report deleted successfully", "report_id": report_id}



    @staticmethod
    def soft_delete_report(report_id, org_name, background_tasks: BackgroundTasks = None):
        """
        Hard delete a report along with its analysis and logs.
        Archives all storage objects to an archive folder and deletes originals.
        Works for AWS S3 and Azure Blob based on CLOUD_PROVIDER.
        """

        class StorageManager:
            def __init__(self):
                self.provider = os.getenv("CLOUD_PROVIDER", "aws").lower().strip()
                if self.provider == "aws":
                    from app.core.config import S3Config
                    self.config = S3Config()
                elif self.provider == "azure":
                    from app.core.config import BlobConfig
                    self.config = BlobConfig()
                else:
                    raise ValueError(f"Unsupported CLOUD_PROVIDER={self.provider}")

            async def archive_and_delete(self, org_name, report_id):
                if self.provider == "aws":
                    await self._archive_and_delete_s3(org_name, report_id)
                else:
                    await self._archive_and_delete_blob(org_name, report_id)

            async def _archive_and_delete_s3(self, org_name, report_id):
                import aioboto3

                bucket = self.config.bucket_name
                source_prefix = f"BI-Portfinal/{org_name}/{report_id}/"
                archive_prefix = f"BI-Portfinal/Archive/{org_name}/{report_id}/"

                session = aioboto3.Session()
                async with session.client("s3") as s3:
                    paginator = s3.get_paginator("list_objects_v2")
                    async for result in paginator.paginate(Bucket=bucket, Prefix=source_prefix):
                        for obj in result.get("Contents", []):
                            source_key = obj["Key"]
                            dest_key = source_key.replace(source_prefix, archive_prefix, 1)

                            logger.info(f"[S3] Copy {source_key} → {dest_key}")
                            await s3.copy_object(
                                Bucket=bucket,
                                CopySource={"Bucket": bucket, "Key": source_key},
                                Key=dest_key,
                            )

                            logger.info(f"[S3] Delete {source_key}")
                            await s3.delete_object(Bucket=bucket, Key=source_key)

            async def _archive_and_delete_blob(self, org_name, report_id):
                from azure.storage.blob.aio import BlobServiceClient
                try:
                    blob_service: BlobServiceClient = self.config.get_blob_client()
                    container_client = blob_service.get_container_client(self.config.container_name)
                except Exception as e:
                    logger.error(f"[Blob] Failed to connect to Azure Blob Storage: {e}")
                    raise

                source_prefix = f"BI-Portfinal/{org_name}/{report_id}/"
                archive_prefix = f"BI-Portfinal/Archive/{org_name}/{report_id}/"

                failed_blobs = []
                
                async for blob in container_client.list_blobs(name_starts_with=source_prefix):
                    source_blob = blob.name
                    dest_blob = source_blob.replace(source_prefix, archive_prefix, 1)

                    try:
                        source_client = container_client.get_blob_client(source_blob)
                        source_url = source_client.url
                        dest_client = container_client.get_blob_client(dest_blob)

                        # Start the copy
                        try:
                            await dest_client.start_copy_from_url(source_url)

                            # Poll copy status with timeout
                            max_wait = 30  # 30 seconds max
                            waited = 0
                            props = await dest_client.get_blob_properties()
                            
                            while props.copy.status == "pending" and waited < max_wait:
                                await asyncio.sleep(1)
                                waited += 1
                                props = await dest_client.get_blob_properties()

                        except Exception:
                            pass

                        await container_client.delete_blob(source_blob)
                        
                    except Exception:
                        failed_blobs.append(source_blob)
                        continue
                    
                if failed_blobs:
                    raise Exception(f"Failed to delete {len(failed_blobs)} blob(s)")


        with scoped_context() as session:
            report = session.query(ReportDetail).filter(ReportDetail.id == report_id).first()
            if not report:
                logger.warning(f"[soft_delete_report] Report not found in DB for report_id={report_id}")
                return {"message": "Report not found", "report_id": report_id}

            # Delete logs and analysis
            session.query(ReportLog).filter(ReportLog.report_id == report_id).delete(synchronize_session=False)
            session.query(ReportAnalysis).filter(ReportAnalysis.report_id == report_id).delete(synchronize_session=False)
            DuplicateAnalysisManager.delete_duplicate_analysis(report.id)

            storage = StorageManager()

            async def run_storage_tasks():
                try:
                    await storage.archive_and_delete(org_name, report.report_id)
                except Exception as e:
                    logger.error(f"[soft_delete_report] Archive/delete failed: {e}")

            # Run async safely
            if background_tasks:
                background_tasks.add_task(run_storage_tasks)
            else:
                # When called synchronously (e.g., from delete-server), run archive in a new thread
                error_queue = queue.Queue()

                def run_in_thread():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            new_loop.run_until_complete(run_storage_tasks())
                        finally:
                            new_loop.close()
                    except Exception as e:
                        logger.error(f"[soft_delete_report] Thread execution failed: {e}")
                        logger.exception(e)
                        error_queue.put(e)
                
                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join(timeout=300)  # Wait for archive to complete before continuing

                if thread.is_alive():
                    logger.error(f"[soft_delete_report] Archive/delete operation timed out...")
                    raise TimeoutError(f"Archive/delete operation timed out for report {report.report_id}")

                # Check if there were any errors in the thread
                if not error_queue.empty():
                    error = error_queue.get()
                    logger.error(f"[soft_delete_report] Archive/delete failed with error: {error}")
                    raise error

            # Delete report record
            session.delete(report)
            session.commit()
            logger.info(f"[soft_delete_report] Successfully deleted report_id={report_id} from DB")

            return {"message": "Report deleted successfully", "report_id": report_id}

    @staticmethod
    def update_report_name(report_id: uuid.UUID, new_name: str):
        from app.models.report_details import ReportDetail
        from app.core.session import scoped_context
        with scoped_context() as session:
            report = session.query(ReportDetail).filter(ReportDetail.id == report_id).first()
            if not report:
                return None
            report.name = new_name
            session.commit()
            session.refresh(report)
            return report

    @staticmethod
    def is_duplicate_report(name: str, project_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from app.models.report_details import ReportDetail
        from app.core.session import scoped_context
        with scoped_context() as session:
            return session.query(ReportDetail).filter(
                ReportDetail.name == name,
                ReportDetail.project_id == project_id,
                ReportDetail.is_deleted == False
            ).first() is not None

    @staticmethod
    def get_report_by_id(report_id: uuid.UUID):
        from app.models.report_details import ReportDetail
        from app.core.session import scoped_context
        with scoped_context() as session:
            return session.query(ReportDetail).filter(ReportDetail.id == report_id).first()

    @staticmethod
    def get_reports_with_context(parent_ids: list[UUID]):
        with scoped_context() as session:
            admin_user = session.query(User).join(User.role)\
                .filter(User.role.has(name=RoleEnum.ADMIN.value)).first()
            admin_name = admin_user.name if admin_user else RoleEnum.ADMIN.value
            admin_id = admin_user.id if admin_user else None

            projects = session.query(
                ProjectDetail.id,
                ProjectDetail.name.label("project_name"),
                ProjectDetail.is_upload,
                ProjectDetail.site_id,
                case((ProjectDetail.assigned_to == None, admin_id), else_=ProjectDetail.assigned_to).label("assigned_to"),
                case((ProjectDetail.assigned_to == None, admin_name), else_=User.name).label("assigned_user")
            ).outerjoin(User, User.id == ProjectDetail.assigned_to)\
             .filter(ProjectDetail.parent_id.in_(parent_ids) if parent_ids else True,
                     ProjectDetail.is_deleted == False).all()

            project_ids = [p.id for p in projects] + parent_ids

            reports = session.query(
            ReportDetail.id.label("report_id"),
            ReportDetail.name.label("report_name"),
            ReportDetail.view_count,
            ReportDetail.is_analyzed,
            ProjectDetail.is_upload,
            ProjectDetail.name.label("project_name"),
            func.coalesce(TableauSiteDetail.site_name, "N/A").label("site_name"),
            case((ProjectDetail.assigned_to == None, admin_name), else_=User.name).label("assigned_user"),
            ReportAnalysis.complexity_type.label("complexity_type"),
            ReportAnalysis.dashboard_count,
            ReportAnalysis.worksheet_count,
            ReportAnalysis.datasource_count,
            ReportAnalysis.calculation_count
            ).join(ProjectDetail, ReportDetail.project_id == ProjectDetail.id)\
             .outerjoin(User, User.id == ProjectDetail.assigned_to)\
             .outerjoin(ReportAnalysis, ReportAnalysis.report_id == ReportDetail.id)\
             .outerjoin(TableauSiteDetail, TableauSiteDetail.id == ProjectDetail.site_id)\
             .filter(ReportDetail.is_deleted == False,
                     ReportDetail.project_id.in_(project_ids)).all()

            return reports

    