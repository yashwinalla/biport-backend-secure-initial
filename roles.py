from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.schemas.roles import AddRoleRequest
from app.services.roles.role_processor import RoleProcessor


roles_router = APIRouter()


@roles_router.post("/add-role-test")
async def add_role(request: AddRoleRequest) -> JSONResponse:
    """
    Add a new role to the database.
    
    Accepts role data as input and stores it in the roles table.
    Input field: name (e.g., ADMIN, MANAGER, DEVELOPER).
    Uses the RoleEnum defined in the project as a reference.
    """
    response = RoleProcessor.process_add_role(request)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)
