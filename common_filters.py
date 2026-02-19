from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import JSONResponse

from app.models.users import User
from app.core.dependencies import get_current_user
from app.core.logger_setup import logger
from app.services.workspace import WorkspaceProcessor
from app.services.discovery import DiscoverProcessor

common_filters_router = APIRouter()


@common_filters_router.get(
    "/filter-options/sites",
    response_model=dict,
    summary="Get list of sites for filtering based on context (workspace=role-based, discover=all)"
)
async def get_filter_sites(
    context: str = Query(..., description="Context for filtering: 'workspace' or 'discover'"),
    current_user: User = Depends(get_current_user)
):
    """
    Get available sites for filtering.
    - workspace: Returns sites based on user role (Admin sees all, Manager sees assigned + subordinates, Developer sees assigned only)
    - discover: Returns all sites in the organization
    """
    try:
        logger.info(f"[COMMON_FILTERS_API] Get filter sites endpoint hit with context={context} by user {current_user.id}")
        
        if context == "workspace":
            # Use role-based filtering for workspace
            response = WorkspaceProcessor.process_get_filter_sites(current_user)
        elif context == "discover":
            # Show all sites for discover
            response = DiscoverProcessor.process_get_filter_sites(current_user)
        else:
            raise HTTPException(status_code=400, detail="Invalid context. Must be 'workspace' or 'discover'")
        
        if not response.success:
            logger.warning(f"[COMMON_FILTERS_API] Failed to get filter sites: {response.error}")
            raise HTTPException(status_code=response.status_code, detail=response.error)

        return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[COMMON_FILTERS_API] Exception in get filter sites endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@common_filters_router.get(
    "/filter-options/projects",
    response_model=dict,
    summary="Get list of projects for filtering based on context (workspace=role-based, discover=all)"
)
async def get_filter_projects(
    context: str = Query(..., description="Context for filtering: 'workspace' or 'discover'"),
    current_user: User = Depends(get_current_user)
):
    """
    Get available projects for filtering.
    - workspace: Returns projects based on user role (Admin sees all, Manager sees assigned + subordinates, Developer sees assigned only)
    - discover: Returns all projects in the organization
    """
    try:
        logger.info(f"[COMMON_FILTERS_API] Get filter projects endpoint hit with context={context} by user {current_user.id}")
        
        if context == "workspace":
            # Use role-based filtering for workspace
            response = WorkspaceProcessor.process_get_filter_projects(current_user)
        elif context == "discover":
            # Show all projects for discover
            response = DiscoverProcessor.process_get_filter_projects(current_user)
        else:
            raise HTTPException(status_code=400, detail="Invalid context. Must be 'workspace' or 'discover'")
        
        if not response.success:
            logger.warning(f"[COMMON_FILTERS_API] Failed to get filter projects: {response.error}")
            raise HTTPException(status_code=response.status_code, detail=response.error)

        return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[COMMON_FILTERS_API] Exception in get filter projects endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@common_filters_router.get(
    "/filter-options/complexity",
    response_model=dict,
    summary="Get list of complexity options for filtering (same for both workspace and discover)"
)
async def get_filter_complexity(
    current_user: User = Depends(get_current_user)
):
    """
    Get available complexity options for filtering.
    Returns the same values for both workspace and discover contexts.
    """
    try:
        logger.info(f"[COMMON_FILTERS_API] Get filter complexity options endpoint hit by user {current_user.id}")
        
        # Complexity options are the same for both contexts
        response = WorkspaceProcessor.process_get_filter_complexity_options()
        
        if not response.success:
            logger.warning(f"[COMMON_FILTERS_API] Failed to get filter complexity options: {response.error}")
            raise HTTPException(status_code=response.status_code, detail=response.error)

        return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[COMMON_FILTERS_API] Exception in get filter complexity options endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))