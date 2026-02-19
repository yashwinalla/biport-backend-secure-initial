from fastapi import APIRouter, BackgroundTasks, Query, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
import uuid
from app.models_old.user import UserOld
from app.models.users import User
from app.schemas import *
from app.schemas.folders import ProjectCreate, ProjectUpdate, DeleteReportRequest, EditReportNameRequest
from app.services.server_configure.server_processor import ServerProcessor
from app.core.dependencies import get_current_user, get_current_new_user, check_if_admin
from typing import Optional
from pydantic import BaseModel

server_router = APIRouter()

@server_router.post("/server", response_model=dict)
async def add_server(request: AddServerRequest, background_tasks: BackgroundTasks, user: UserOld = Depends(get_current_user)):
    """API to add a new server."""
    response = ServerProcessor.process_add_server(request, user, background_tasks)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@server_router.post("/add-server")
async def add_tableau_server(
    request: AddTableauServerRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_new_user),
    _: None = Depends(check_if_admin)
):
    """API to add a new server to TableauServerDetail and start site discovery."""
    response = ServerProcessor.process_add_tableau_server(request, user, background_tasks)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@server_router.delete("/server", response_model=dict)
async def delete_server(server_id: uuid.UUID = Query(..., description="Server ID"), user: UserOld = Depends(get_current_user)):
    """API to delete a server."""
    response = await ServerProcessor.process_delete_server(server_id)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@server_router.put("/server", response_model=dict)
async def update_server(request: UpdateServerRequest, user: UserOld = Depends(get_current_user)):
    """API to update a server."""
    response = ServerProcessor.process_update_server(request, user)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@server_router.get("/server", response_model=GetServerResponse)
async def get_server(server_id: uuid.UUID = Query(..., description="Server ID"), user: UserOld = Depends(get_current_user)):
    """API to get a single server."""
    response = ServerProcessor.process_get_server(server_id)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@server_router.get("/servers", response_model=ServerListResponse)
async def get_servers(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), user: UserOld = Depends(get_current_user)):
    """API to get all servers with pagination."""
    response = ServerProcessor.process_get_servers(page=page, page_size=page_size)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@server_router.get("/list-servers", response_model=TableauServerResponse)
async def get_org_servers(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), user: User = Depends(get_current_new_user), _: None = Depends(check_if_admin)):
    """API to get all servers for the current user's organisation with pagination."""
    response = ServerProcessor.process_get_org_servers(user.organization_id, page=page, page_size=page_size)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@server_router.get("/get-root-projects")
async def get_root_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_new_user),
    _: None = Depends(check_if_admin)
):
    """API to get all root projects (parent_id is null) for the current user with pagination."""
    user_id = user.id
    if not isinstance(user_id, uuid.UUID):
        user_id = uuid.UUID(str(user_id))
    response = ServerProcessor.process_get_root_projects(user_id, page=page, page_size=page_size)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@server_router.get("/get-projects-by-parent")
async def get_projects_by_parent(
    parent_id: uuid.UUID = Query(..., description="Parent project ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_new_user),
    _: None = Depends(check_if_admin)
):
    """API to get all projects for the current user with a given parent_id, with pagination."""
    user_id = user.id
    if not isinstance(user_id, uuid.UUID):
        user_id = uuid.UUID(str(user_id))
    response = ServerProcessor.process_get_projects_by_parent(parent_id, user_id, page=page, page_size=page_size)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@server_router.post("/create-project")
async def create_project(
    request: ProjectCreate,
    user: User = Depends(get_current_new_user),
    _: None = Depends(check_if_admin)
):
    """API to create a new project for the current user, checking for duplicates as per requirements."""
    response = ServerProcessor.process_create_project(request, user)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)


@server_router.patch("/update_status")
async def update_server_status(request: UpdateServerStatusRequest, user: UserOld = Depends(get_current_user)):
    """API to update the status of a server."""
    response = ServerProcessor.process_update_server_status(request)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@server_router.patch("/update-status")
async def update_tableau_server_status(
    request: UpdateServerStatusRequest,
    current_user: User = Depends(get_current_new_user),
    _: None = Depends(check_if_admin)
):
    """Updates the status of a TableauServerDetail."""
    response = ServerProcessor().update_tableau_server_status(request)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@server_router.patch("/delete-server")
async def soft_delete_tableau_server(
    request: DeleteServerRequest,
    user: User = Depends(get_current_new_user),
    _: None = Depends(check_if_admin)
):
    """Soft deletes a TableauServerDetail by setting is_deleted=True."""
    response = ServerProcessor.process_soft_delete_tableau_server(request,user)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@server_router.patch("/update-project-name")
async def update_project_name(
    request: ProjectUpdate,
    user: User = Depends(get_current_new_user),
    _: None = Depends(check_if_admin)
):
    """API to update a project's name for the current user, checking for duplicates as per requirements."""
    response = ServerProcessor.process_update_project_name(request, user)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

class DeleteProjectRequest(BaseModel):
    project_id: uuid.UUID

@server_router.patch("/delete-project")
async def delete_project(
    request: DeleteProjectRequest,
    user: User = Depends(get_current_new_user),
    _: None = Depends(check_if_admin)
):
    """API to soft delete a project and all its children and reports."""
    response = ServerProcessor.process_delete_project(request.project_id,user)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@server_router.patch("/delete-report")
async def delete_report(
    request: DeleteReportRequest,
    user: User = Depends(get_current_new_user),
    _: None = Depends(check_if_admin)
):
    """API to soft delete a report (file) by its primary key. Accepts JSON body with report_id."""
    response = ServerProcessor.process_delete_report(request.report_id,user)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@server_router.patch("/edit-report-name")
async def edit_report_name(
    request: EditReportNameRequest,
    user: User = Depends(get_current_new_user),
    _: None = Depends(check_if_admin)
):
    """API to edit a report (file) name, update DB, and rename in S3. Accepts JSON body with report_id and new_name."""
    response = await ServerProcessor.process_edit_report_name(request.report_id, request.new_name, user)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@server_router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    project_id: Optional[uuid.UUID] = Form(None),
    user: User = Depends(get_current_new_user),
    _: None = Depends(check_if_admin)
):
    """API to upload a zip or twb/twbx file. Uses project_id as context for both scenarios. Delegates all logic to the processor."""
    response = await ServerProcessor.process_upload_file(file, project_id, user)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)
