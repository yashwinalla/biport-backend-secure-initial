from app.models.organization_details import OrganizationDetail, OrganizationDetailManager
from pydantic import BaseModel
from fastapi import HTTPException, Depends
from app.core.dependencies import get_current_user, check_if_admin
from app.models.users import User
from fastapi import APIRouter, UploadFile, File
from app.schemas.organization_details import OrganizationDetailRequest
from fastapi.responses import JSONResponse
from app.services.organization.organization_service import OrganizationDetailsService
from app.services.organization.organization_processor import OrganizationProcessor

organization_router = APIRouter()


@organization_router.post("/add-organization-test")
async def organization_details(organization: OrganizationDetailRequest):
    """Create and return a new organization detail."""
    response = OrganizationProcessor.create_organization_details(organization)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code = response.status_code)

@organization_router.post("/upload-logo")
async def upload_logo(
    logo: UploadFile = File(...),
    _: None = Depends(check_if_admin)  # Admin-only
):
    """
    Upload global application logo.
    Replaces the existing logo every time.
    Stored at: BI-Portfinal/global/assets/logo.png
    """
    response = await OrganizationProcessor.upload_organization_logo(logo)
    return JSONResponse(
        content={"data": response.data, "error": response.error},
        status_code=response.status_code
    )


@organization_router.get("/logo")
async def get_organization_logo():
    """
    Fetch global application logo.
    Public endpoint.
    """
    response = await OrganizationProcessor.get_organization_logo()
    return JSONResponse(
        content={"data": response.data, "error": response.error},
        status_code=response.status_code
    )
