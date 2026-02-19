# Dashboard API endpoints fetching from database views

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from app.services.dashboard_service import DashboardService

from app.models.users import User
from app.core.dependencies import get_current_user

from pydantic import BaseModel
from typing import Optional

dashboard_router = APIRouter()

# Chart endpoints
@dashboard_router.get("/charts/kpi-cards")
async def get_kpi_cards(user:User=Depends(get_current_user)):
    """Get KPI cards data from database."""
    response = DashboardService.get_kpi_cards(user)
    return JSONResponse(content=response, status_code=200)

@dashboard_router.get("/charts/complexity")
async def get_complexity_chart(user: User = Depends(get_current_user)):
    """Get complexity distribution from database."""
    response = DashboardService.get_complexity_chart(user)
    return JSONResponse(content=response, status_code=200)

@dashboard_router.get("/charts/priority")
async def get_priority_chart(user: User = Depends(get_current_user)):
    """Get priority distribution from database."""
    response = DashboardService.get_priority_chart(user)
    return JSONResponse(content=response, status_code=200)

@dashboard_router.get("/charts/migration-status")
async def get_migration_status_chart():
    """Get migration status from database."""
    response = DashboardService.get_migration_status()
    return JSONResponse(content=response, status_code=200)

@dashboard_router.get("/charts/assigned")
async def get_assigned_chart(user: User = Depends(get_current_user)):
    """Get assigned vs unassigned from database."""
    response = DashboardService.get_assigned_chart(user)
    return JSONResponse(content=response, status_code=200)

@dashboard_router.get("/charts/user-roles")
async def get_user_roles_chart(user :User=Depends(get_current_user)):
    """Get user roles from database."""
    response = DashboardService.get_user_roles(user)
    return JSONResponse(content=response, status_code=200)

@dashboard_router.get("/charts/report-types")
async def get_report_types_chart(user :User=Depends(get_current_user)):
    """Get report types from database."""
    response = DashboardService.get_report_types(user)
    return JSONResponse(content=response, status_code=200)

@dashboard_router.get("/charts/work-status")
async def get_work_status_chart(user: User=Depends(get_current_user)):
    """Get work status from database."""
    response = DashboardService.get_work_status(user)
    return JSONResponse(content=response, status_code=200)

@dashboard_router.get("/charts/inventory-heatmap")
async def get_inventory_heatmap(user:User=Depends(get_current_user)):
    """Get inventory heatmap from database."""
    response = DashboardService.get_inventory_heatmap(user)
    return JSONResponse(content=response, status_code=200)
    
@dashboard_router.get("/charts/project-inventory-heatmap")
async def get_project_inventory_heatmap(user:User=Depends(get_current_user)):
    """Get project inventory heatmap from database."""
    response = DashboardService.get_project_inventory_heatmap(user)
    return JSONResponse(content=response, status_code=200)

class VisualsRequest(BaseModel):
    visual: Optional[str] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 10
    sort_order: Optional[str] = "desc"

@dashboard_router.post("/charts/visuals", response_model=dict)
async def get_visuals_post(
    request: VisualsRequest,
    user: User = Depends(get_current_user)
):
    """
    Get visuals summary for the user's organization with optional filter by type.
    Supports pagination and sorting.
    """
    offset = (request.page - 1) * request.page_size
    
    # Call service method to get paginated, sorted summary
    response = DashboardService.get_visuals_summary(
        user,
        visual=request.visual.lower() if request.visual else None, 
        limit=request.page_size,
        offset=offset, 
        sort_order=request.sort_order
    )
    return JSONResponse(content=response, status_code=200)

@dashboard_router.get("/charts/visuals/counts", response_model=dict)
async def get_visuals_counts(
    user: User = Depends(get_current_user)
):
    """
    Get total count of native and custom visuals for the user's organization.
    """
    response = DashboardService.get_visual_counts(user)
    return JSONResponse(content=response, status_code=200)

@dashboard_router.get("/charts/reports-timeline")
async def get_reports_timeline():
    """Get reports timeline."""
    response = DashboardService.get_reports_timeline()
    return JSONResponse(content=response, status_code=200)