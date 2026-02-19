from fastapi import APIRouter, Depends, Query, Body
from fastapi.responses import JSONResponse

from app.schemas import *
from app.services import DiscoverService, DiscoverServerService
from app.models_old.user import UserOld
from app.models.users import User
from app.core.dependencies import get_current_user
from uuid import UUID

from app.models.users import User
from app.core import get_current_user
from app.services.discovery import DiscoverProcessor,DuplicateAnalysisProcessor, StaleProcessor
from app.services.discovery.stale_update_processor import StaleUpdateProcessor
discover_router = APIRouter()
from app.schemas.discover import AssignUserRequest
from app.schemas.discover import  ReportAnalysisUpdate, DiscoverReportsRequest, StaleReportsRequest


@discover_router.post("/discover/server", response_model=dict)
async def discover_server(request: DiscoverServerRequest, page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
                          user: UserOld = Depends(get_current_user)):
    """API to get a discover server."""
    response = await DiscoverServerService.execute(DiscoverServerService()._discover_server, request, page, page_size)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@discover_router.post("/discover/servers", response_model=dict)
async def get_all_servers(page: int = Query(1),page_size: int = Query(10),
                             user: User = Depends(get_current_user)):
    
    """API to get all active servers for the user's organization."""
    response = DiscoverProcessor().process_get_all_servers(user.organization_id, page, page_size)
    return JSONResponse(content={"data": response.data, "error": response.error},status_code=response.status_code)

@discover_router.post("/discover/sites", response_model=dict)
async def get_all_sites(server_id: UUID = Query(...),page: int = Query(1),page_size: int = Query(10),
                        user: User = Depends(get_current_user)):
    """API to get all sites for a given server ID."""
    response = DiscoverProcessor().process_get_all_sites(server_id, page, page_size)
    return JSONResponse(content={"data": response.data, "error": response.error},status_code=response.status_code)

@discover_router.post("/discover/managers", response_model=dict)
async def get_all_managers(organization_id: UUID = Query(...),page: int = Query(1, ge=1),page_size: int = Query(10, ge=1, le=100),
                           user: User = Depends(get_current_user)):
    """ API to get all managers by organization ID with pagination"""
    response = DiscoverProcessor().process_get_all_managers(organization_id=organization_id,page=page,page_size=page_size)
    return JSONResponse(content={"data": response.data, "error": response.error},status_code=response.status_code)

@discover_router.post("/discover/developers", response_model=dict)
async def get_all_developers(organization_id: UUID = Query(...),manager_id: UUID = Query(...),page: int = Query(1, ge=1),page_size: int = Query(10, ge=1, le=100),
                            user: User = Depends(get_current_user)):
    """API to get all developers by organization ID and manager ID with pagination"""
    response = DiscoverProcessor().process_get_all_developers(organization_id=organization_id,manager_id=manager_id,page=page,page_size=page_size)
    return JSONResponse(content={"data": response.data, "error": response.error},status_code=response.status_code)

@discover_router.post("/discover/root-projects", response_model=dict)
async def get_all_root_projects(page: int = Query(1, ge=1),page_size: int = Query(10, ge=1, le=100),
                                user: User = Depends(get_current_user)):
    """API to get all root projects where is_upload = True for the user's organization"""
    response = DiscoverProcessor().process_get_all_root_projects(page=page, page_size=page_size, user=user)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@discover_router.patch("/discover/project/assign", response_model=dict)
async def update_project_assigned_to(project_id: UUID = Query(...),user_id: UUID = Query(...),
                                    user: User = Depends(get_current_user)):
    """API to assign user to project via query params"""
    response = DiscoverProcessor().process_update_assign_to(project_id, user_id)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@discover_router.post("/discover/projects/by-site", response_model=dict)
async def get_all_projects_by_site(site_id: UUID = Query(...), user: User = Depends(get_current_user)):
    """API to get all projects by site including subprojects and files"""
    response = DiscoverProcessor().process_get_all_projects_by_site(site_id)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@discover_router.post("/discover/project/by-parent", response_model=dict)
async def get_projects_by_parent(project_id: UUID = Query(...), user: User = Depends(get_current_user)):
    """Get all sub-projects by parent project ID along with files and assigned user."""
    response = DiscoverProcessor().process_get_projects_by_parent(project_id)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@discover_router.post("/discover/developers/by-org", response_model=dict)
async def get_all_developers_org_id(organization_id: UUID = Query(...), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
                         user: User = Depends(get_current_user)):
    """API to get all developers by organization ID with pagination"""
    response = DiscoverProcessor().process_get_all_developers_by_orgid( organization_id=organization_id, page=page, page_size=page_size)
    return JSONResponse(content={"data": response.data, "error": response.error},status_code=response.status_code)

@discover_router.post("/discover/projects/by-parent", response_model=dict)
async def get_projects_by_parent_id(project_id: UUID = Query(...),user: User = Depends(get_current_user)):
    """Get all sub-projects (including nested) by parent ID with files & assigned info."""
    response = DiscoverProcessor.process_get_projects_by_parent_id(project_id)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@discover_router.post("/discover/projects/search", response_model=dict)
async def get_report_details_by_search(keyword: str = Query(...),user: User = Depends(get_current_user)):
    response = DiscoverProcessor().process_get_projects_by_search(
        keyword=keyword,
        org_id=str(user.organization_id),
        user_id=str(user.id),
        role_name=user.role_name
    )
    return JSONResponse(content={"data": response.data, "error": response.error},status_code=response.status_code)

from fastapi import BackgroundTasks

@discover_router.post("/discover/reports/all", response_model=dict)
async def get_all_reports(
    background_tasks: BackgroundTasks,
    request: DiscoverReportsRequest,
    user: User = Depends(get_current_user)
):
    """
    Get all reports with advanced filtering and sorting.
    
    Features:
    - Search by report name and project name (partial match)
    - Filter by complexity (multiple values with OR logic within complexity)
    - Filter by priority (multiple values with OR logic within priority)
    - AND logic when both complexity and priority filters are present
    - Multi-field sorting: site, project_name, report_name, complexity, priority
    - Pagination support
    - Background analysis for unanalyzed reports
    
    Default behavior: Returns all reports (paginated) if no filters/search provided.
    """
    response = DiscoverProcessor.process_get_all_reports(user, request)

    service = DiscoverService()
    unanalyzed_ids = [r["id"] for r in response["data"] if not r["is_analyzed"]]
    if unanalyzed_ids:
        background_tasks.add_task(service.run_analysis_sync, unanalyzed_ids, user.id)

    return JSONResponse(
        content={
            "data": response["data"],
            "error": response["error"],
            "total": response["total"],
            "total_files_fetched": response["total_files_fetched"],
            "page": request.page,
            "page_size": request.page_size,
            "total_pages": response["total_pages"]
        },
        status_code=response["status_code"]
    )


@discover_router.patch("/discover/update", response_model=dict)
async def update_report_analysis(
    report_id: UUID = Query(...),
    payload: ReportAnalysisUpdate = Body(...),
    user: User = Depends(get_current_user)
):
    response = DiscoverProcessor.process_update_report(report_id, payload)
    return JSONResponse(
        content={"data": response.data, "error": response.error},
        status_code=response.status_code
    )

@discover_router.post("/discover/status", response_model=dict)
async def get_lookup_options(user: User = Depends(get_current_user)):
    response = DiscoverProcessor.process_get_lookup_options()
    return JSONResponse(
        content={"data": response.data, "error": response.error},
        status_code=response.status_code
    )

# DEPRECATED: Use /app_api/filter-options/complexity instead
# @discover_router.get("/discover/filter-options/complexity", response_model=dict)
# async def get_discover_filter_complexity(user: User = Depends(get_current_user)):
#     """Get list of complexity options available for filtering in discover"""
#     response = DiscoverProcessor.process_get_filter_complexity_options()
#     return JSONResponse(
#         content={"data": response.data, "error": response.error},
#         status_code=response.status_code
#     )

@discover_router.get("/discover/filter-options/priority", response_model=dict)
async def get_discover_filter_priority(user: User = Depends(get_current_user)):
    """Get list of priority options available for filtering in discover"""
    response = DiscoverProcessor.process_get_filter_priority_options()
    return JSONResponse(
        content={"data": response.data, "error": response.error},
        status_code=response.status_code
    )

# DEPRECATED: Use /app_api/filter-options/sites?context=discover instead
# @discover_router.get("/discover/filter-options/sites", response_model=dict)
# async def get_discover_filter_sites(user: User = Depends(get_current_user)):
#     """Get list of sites available for filtering in discover"""
#     response = DiscoverProcessor.process_get_filter_sites(user)
#     return JSONResponse(
#         content={"data": response.data, "error": response.error},
#         status_code=response.status_code
#     )

# DEPRECATED: Use /app_api/filter-options/projects?context=discover instead
# @discover_router.get("/discover/filter-options/projects", response_model=dict)
# async def get_discover_filter_projects(user: User = Depends(get_current_user)):
#     """Get list of projects available for filtering in discover"""
#     response = DiscoverProcessor.process_get_filter_projects(user)
#     return JSONResponse(
#         content={"data": response.data, "error": response.error},
#         status_code=response.status_code
#     )

# ==================== Duplicate Analysis Endpoints ====================

@discover_router.get("/duplicate-analysis", response_model=dict)
async def get_org_report_duplicates(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    user: User = Depends(get_current_user)
):
    """
    Get paginated report duplicates and match percentage for the given organization.
    """
    response = DuplicateAnalysisProcessor.process_get_org_report_duplicates(user.organization_id, page, page_size)
    return JSONResponse(
        content={"data": response.data, "error": response.error},
        status_code=response.status_code
    )

@discover_router.post("/stale-reports", response_model=dict)
async def get_stale_reports(
    request: StaleReportsRequest = Body(...),
    user: User = Depends(get_current_user)
):
    """
    Get all stale reports for the user's organization.
    Stale reports are from server-discovered projects, have low view counts,
    and have not been updated recently.
    """
    response = StaleProcessor.process_get_stale_reports(user, request.page, request.page_size, request.days)
    return JSONResponse(content={"data": response.data, "error": response.error},status_code=response.status_code)


@discover_router.post("/stale-update", response_model=dict)
def update_stale_reports(
    user: User = Depends(get_current_user)
):
    """
    Trigger the stale report update process for the user's organization.
    This connects to Tableau servers, downloads site content, and updates last viewed dates in the database.
    """
    response = StaleUpdateProcessor.process_stale_update(user.organization_id)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)
