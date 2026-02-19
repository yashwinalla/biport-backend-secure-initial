from typing import Optional
from fastapi import APIRouter, Depends, Path, HTTPException, UploadFile, File
from fastapi.params import Query
from fastapi.responses import JSONResponse
from uuid import UUID

from app.models.users import User
from app.core.dependencies import get_current_user
from app.core.logger_setup import logger
from app.core.response import ServiceResponse
from app.services.workspace import WorkspaceProcessor
from app.schemas.workspace import (
    ReportStatusUpdateRequest, 
    SuccessResponse,
    ErrorResponse,
    ReportDetailsResponse,
    FileUploadResponse,
    AnalysisDownloadResponse,
    WorkspaceReportsRequest
)

workspace_router = APIRouter()


# GET Reports

@workspace_router.post("/workspace/reports", response_model=dict)
async def get_workspace_reports(
    request: WorkspaceReportsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Get workspace reports with advanced filtering and sorting.
    
    Features:
    - Search by report name and project name (partial match)
    - Filter by status (multiple values with OR logic within status)
    - Filter by complexity (multiple values with OR logic within complexity)
    - AND logic when both status and complexity filters are present
    - Multi-field sorting with customizable order
    - Pagination support
    
    Default behavior: Returns all reports (paginated) if no filters/search provided.
    """
    try:
        logger.info(f"[WORKSPACE_API] Endpoint hit: POST /workspace/reports by user {current_user.id}")

        response = WorkspaceProcessor.process_get_reports_with_filters(current_user, request)
        logger.info(f"[WORKSPACE_API] Response from processor: success={response.success}, status={response.status_code}")

        return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)
    except Exception as e:
        logger.error(f"[WORKSPACE_API] Exception in workspace endpoint: {e}", exc_info=True)
        return JSONResponse(content={"data": None, "error": str(e)}, status_code=500)




# PATCH Report Status

@workspace_router.patch(
    "/workspace/reports/{report_id}/status",
    response_model=SuccessResponse,
    summary="Update report status flags (unit_tested, uat_tested, deployed)"
)
def update_report_status(
    status_update: ReportStatusUpdateRequest,
    report_id: UUID = Path(..., description="UUID of the report to update"),
    user: User = Depends(get_current_user)
):
    logger.info(f"[WORKSPACE_API] Update report status endpoint hit for report {report_id} by user {user.id}")

    result = WorkspaceProcessor.process_update_report_status(report_id, status_update, user)

    if not result.success:
        logger.warning(f"[WORKSPACE_API] Report status update failed: {result.error}")
        return ErrorResponse(success=False, message=result.error, code=result.status_code)

    if not result.data:
        return ErrorResponse(success=False, message="Processor returned no data", code=500)

    return SuccessResponse(**result.data)


# GET Report Details

@workspace_router.get(
    "/workspace/{report_id}",
    response_model=ReportDetailsResponse,
    summary="Get detailed report information including metrics and migration logs"
)
async def get_report_details(
    report_id: UUID = Path(..., description="UUID of the report to fetch details for"),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"[WORKSPACE_API] Get report details endpoint hit for report {report_id} by user {current_user.id}")
        
        response = WorkspaceProcessor.process_get_report_details(report_id, current_user)
        
        if not response.success:
            logger.warning(f"[WORKSPACE_API] Failed to get report details: {response.error}")
            raise HTTPException(status_code=response.status_code, detail=response.error)

        if not response.data:
            raise HTTPException(status_code=500, detail="Processor returned no data")

        return ReportDetailsResponse(**response.data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKSPACE_API] Exception in get report details endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# POST Upload Semantic Model

@workspace_router.post(
    "/workspace/{report_id}/upload/semantic",
    response_model=FileUploadResponse,
    summary="Upload semantic model as a zip file to S3"
)
async def upload_semantic_model(
    report_id: UUID,
    file: UploadFile = File(..., description="Semantic model zip file"),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"[WORKSPACE_API] Upload semantic model endpoint hit for report {report_id} by user {current_user.id}")

        response = await WorkspaceProcessor.process_upload_semantic_model(report_id, file, current_user)

        if not response.success:
            logger.warning(f"[WORKSPACE_API] Failed to upload semantic model: {response.error}")
            raise HTTPException(status_code=response.status_code, detail=response.error)

        if not response.data:
            raise HTTPException(status_code=500, detail="Processor returned no data")

        return FileUploadResponse(**response.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKSPACE_API] Exception in upload semantic model endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))




# POST Upload Final PBI

@workspace_router.post(
    "/workspace/{report_id}/upload/final-pbi",
    response_model=FileUploadResponse,
    summary="Upload final PBI file as a zip file to S3"
)
async def upload_final_pbi(
    report_id: UUID,
    file: UploadFile = File(..., description="Final PBI zip file"),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"[WORKSPACE_API] Upload final PBI endpoint hit for report {report_id} by user {current_user.id}")

        # Let the service handle validation + logging
        response = await WorkspaceProcessor.process_upload_final_pbi(report_id, file, current_user)

        if not response.success:
            logger.warning(f"[WORKSPACE_API] Failed to upload final PBI: {response.error}")
            raise HTTPException(status_code=response.status_code, detail=response.error)

        if not response.data:
            raise HTTPException(status_code=500, detail="Processor returned no data")

        return FileUploadResponse(**response.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKSPACE_API] Exception in upload final PBI endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



# GET Download Semantic Model

@workspace_router.get(
    "/workspace/{report_id}/download/semantic",
    response_model=dict,
    summary="Download uploaded semantic model zip file"
)
async def download_semantic_model(
    report_id: UUID,
    current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"[WORKSPACE_API] Download semantic model endpoint hit for report {report_id} by user {current_user.id}")
        
        response = await WorkspaceProcessor.process_download_semantic_model(report_id, current_user)
        
        if not response.success:
            logger.warning(f"[WORKSPACE_API] Failed to download semantic model: {response.error}")
            raise HTTPException(status_code=response.status_code, detail=response.error)

        return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKSPACE_API] Exception in download semantic model endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# GET Download Final PBI

@workspace_router.get(
    "/workspace/{report_id}/download/final-pbi",
    response_model=dict,
    summary="Download uploaded final PBI zip file"
)
async def download_final_pbi(
    report_id: UUID,
    current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"[WORKSPACE_API] Download final PBI endpoint hit for report {report_id} by user {current_user.id}")
        
        response = await WorkspaceProcessor.process_download_final_pbi(report_id, current_user)
        
        if not response.success:
            logger.warning(f"[WORKSPACE_API] Failed to download final PBI: {response.error}")
            raise HTTPException(status_code=response.status_code, detail=response.error)

        return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKSPACE_API] Exception in download final PBI endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# GET Download Analysis Report

@workspace_router.get(
    "/workspace/{report_id}/analysis/download",
    response_model=AnalysisDownloadResponse,
    summary="Download detailed analysis {report_name}.zip from analyzed_outputs"
)
async def download_analysis_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"[WORKSPACE_API] Download analysis endpoint hit for report {report_id} by user {current_user.id}")
        
        response = await WorkspaceProcessor.process_download_analysis(report_id, current_user)
        
        if response.error:
            logger.warning(f"[WORKSPACE_API] Failed to download analysis: {response.error}")
            raise HTTPException(status_code=response.status_code, detail=response.error)

        if not response.data:
            raise HTTPException(status_code=500, detail="Processor returned no data")

        return AnalysisDownloadResponse(**response.data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKSPACE_API] Exception in download analysis endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))




# GET Available Sites for Filtering (Role-based)
# DEPRECATED: Use /app_api/filter-options/sites?context=workspace instead

# @workspace_router.get(
#     "/workspace/filter-options/sites",
#     response_model=dict,
#     summary="Get list of sites available for filtering based on user role"
# )
# async def get_workspace_filter_sites(
#     current_user: User = Depends(get_current_user)
# ):
#     try:
#         logger.info(f"[WORKSPACE_API] Get filter sites endpoint hit by user {current_user.id}")
#         
#         response = WorkspaceProcessor.process_get_filter_sites(current_user)
#         
#         if not response.success:
#             logger.warning(f"[WORKSPACE_API] Failed to get filter sites: {response.error}")
#             raise HTTPException(status_code=response.status_code, detail=response.error)
# 
#         return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)
#         
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"[WORKSPACE_API] Exception in get filter sites endpoint: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))


# GET Available Projects for Filtering (Role-based)
# DEPRECATED: Use /app_api/filter-options/projects?context=workspace instead

# @workspace_router.get(
#     "/workspace/filter-options/projects",
#     response_model=dict,
#     summary="Get list of projects available for filtering based on user role"
# )
# async def get_workspace_filter_projects(
#     current_user: User = Depends(get_current_user)
# ):
#     try:
#         logger.info(f"[WORKSPACE_API] Get filter projects endpoint hit by user {current_user.id}")
#         
#         response = WorkspaceProcessor.process_get_filter_projects(current_user)
#         
#         if not response.success:
#             logger.warning(f"[WORKSPACE_API] Failed to get filter projects: {response.error}")
#             raise HTTPException(status_code=response.status_code, detail=response.error)
# 
#         return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)
#         
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"[WORKSPACE_API] Exception in get filter projects endpoint: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))


# GET Available Status Options for Filtering

@workspace_router.get(
    "/workspace/filter-options/status",
    response_model=dict,
    summary="Get list of status options available for filtering"
)
async def get_workspace_filter_status(
    current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"[WORKSPACE_API] Get filter status options endpoint hit by user {current_user.id}")
        
        response = WorkspaceProcessor.process_get_filter_status_options()
        
        if not response.success:
            logger.warning(f"[WORKSPACE_API] Failed to get filter status options: {response.error}")
            raise HTTPException(status_code=response.status_code, detail=response.error)

        return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKSPACE_API] Exception in get filter status options endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# GET Available Complexity Options for Filtering
# DEPRECATED: Use /app_api/filter-options/complexity instead

# @workspace_router.get(
#     "/workspace/filter-options/complexity",
#     response_model=dict,
#     summary="Get list of complexity options available for filtering"
# )
# async def get_workspace_filter_complexity(
#     current_user: User = Depends(get_current_user)
# ):
#     try:
#         logger.info(f"[WORKSPACE_API] Get filter complexity options endpoint hit by user {current_user.id}")
#         
#         response = WorkspaceProcessor.process_get_filter_complexity_options()
#         
#         if not response.success:
#             logger.warning(f"[WORKSPACE_API] Failed to get filter complexity options: {response.error}")
#             raise HTTPException(status_code=response.status_code, detail=response.error)
# 
#         return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)
#         
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"[WORKSPACE_API] Exception in get filter complexity options endpoint: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))


# DELETE Report (Soft Delete)

@workspace_router.delete(
    "/workspace/delete/{repot_id}",
    response_model=SuccessResponse,
    summary="Soft delete a report (mark as deleted without removing from database)"
)
async def soft_delete_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"[WORKSPACE_API] Soft delete endpoint hit for report {report_id} by user {current_user.id}")
        
        response = WorkspaceProcessor.process_soft_delete_report(report_id, current_user)
        
        if not response.success:
            logger.warning(f"[WORKSPACE_API] Failed to soft delete report: {response.error}")
            raise HTTPException(status_code=response.status_code, detail=response.error)

        if not response.data:
            raise HTTPException(status_code=500, detail="Processor returned no data")
        
        return SuccessResponse(**response.data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKSPACE_API] Exception in soft delete endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
