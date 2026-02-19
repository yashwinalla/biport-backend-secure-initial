from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, UploadFile, Form, File as UploadFileType, Depends
from fastapi.responses import JSONResponse
from fastapi import Query

from app.schemas.folders import FolderCreate, FolderResponse, FolderTree, FolderUpdate
from app.services import convert_uuid_to_string, FolderProcessor
from app.models_old.user import UserOld
from app.core.dependencies import get_current_user
from app.core.exceptions import BadRequestError

folder_router = APIRouter(
    dependencies=[Depends(get_current_user)]
)

@folder_router.get("/folders", response_model=List[FolderTree])
async def get_all_folders() -> JSONResponse:
    """Retrieve all folders organized in a hierarchical tree structure."""
    response = await FolderProcessor.process_get_all_folders()
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@folder_router.post("/folders", response_model=FolderResponse)
async def create_folder(folder: FolderCreate) -> JSONResponse:
    """Create a new folder with the specified name and optional parent."""
    response = await FolderProcessor.process_create_folder(folder)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@folder_router.get("/folders/by-parent", response_model=List[FolderResponse])
async def get_by_parent(parent_id: Optional[str] = Query(default=None)) -> JSONResponse:
    """
    Retrieve folders by their parent folder ID.
    
    If no parent ID is provided, returns top-level folders.
    """
    uuid_parent_id = None if parent_id in (None, "null") else UUID(parent_id)
    response = await FolderProcessor.process_get_folders_by_parent(uuid_parent_id)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@folder_router.get("/folders/base", response_model=List[FolderResponse])
async def get_null_folders() -> JSONResponse:
    """Retrieve all root-level folders that have no parent assigned."""
    response = await FolderProcessor.process_get_root_folders()
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@folder_router.delete("/folders/{folder_id}", response_model=dict)
async def delete_folder(folder_id: str) -> JSONResponse:
    """Soft-delete a folder by marking it as inactive using its unique ID."""
    response = await FolderProcessor.process_soft_delete(folder_id)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@folder_router.put("/folders/{folder_id}", response_model=FolderResponse)
async def update_folder(folder_id: UUID, folder_update: FolderUpdate) -> JSONResponse:
    """Update the metadata of an existing folder using its UUID."""
    response = await FolderProcessor.process_update_folder(folder_id, folder_update)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@folder_router.post("/upload-file")
async def upload_file(
    uploaded_file: List[UploadFile] = UploadFileType(...),
    parent_id: Optional[str] = Form(None),
    user: UserOld = Depends(get_current_user)
) -> JSONResponse:
    """
    Upload one or more files to a specific folder.
    
    - Files are stored and linked to the folder by parent ID.
    - Returns updated folder structure.
    """
    if parent_id in [None, '', 'null', 'None']:
        parent_id = None
    else:
        try:
            parent_id = UUID(parent_id)
        except ValueError:
            raise BadRequestError(detail="Invalid parent_id format. Expected UUID or null.")
    response = await FolderProcessor.process_upload_file(uploaded_file, parent_id)
    response_data = convert_uuid_to_string(response.data)
    return JSONResponse(content={"data": response_data, "error": response.error}, status_code=response.status_code)

@folder_router.get("/folders/tree/{folder_id}", response_model=FolderTree)
async def get_folder_tree(folder_id: UUID) -> JSONResponse:
    """
    Get a folder and all its nested subfolders as a tree.
    
    Useful for visualizing folder structure recursively.
    """
    response = await FolderProcessor.process_get_folder_tree(folder_id)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@folder_router.get("/workspace/upload-files")
async def get_folder_summary() -> JSONResponse:
    """
    Get a flat summary of all folders and files across the workspace.
    
    Useful for file listings in project dashboards.
    """
    response = await FolderProcessor.process_get_folder_summary()
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@folder_router.get("/workspace/upload-files/{project_id}")
async def get_folder_summary_by_project_id(project_id: UUID) -> JSONResponse:
    """
    Get a flat summary of folders and files under a specific project.
    
    - Returns all associated file and folder metadata.
    """
    response = await FolderProcessor.process_get_folder_summary_by_project_id(project_id)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)
