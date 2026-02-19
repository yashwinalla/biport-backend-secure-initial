from fastapi import APIRouter, Depends, Header, Query, Body, BackgroundTasks
from fastapi.responses import JSONResponse

from app.core import get_verified_user_email, check_blocked_email
from app.services.auth import AuthService
from app.schemas.auth import UserCreate, UserLogin, ResetPassword, RefreshToken, AddUserRequest
from app.models.users import User, UserManager
from app.core.dependencies import check_if_admin, get_current_user
from app.core.enums import RoleEnum
from passlib.hash import bcrypt
import uuid
from app.core.exceptions import ConflictError
from app.services.auth import decode_base

auth_router = APIRouter()
auth_service = AuthService()



@auth_router.post("/register", dependencies=[Depends(check_blocked_email)])
def register_user(data: UserCreate):
    response = auth_service.execute(auth_service.register_user, data)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)


@auth_router.post("/login")
def login_user(data: UserLogin, background_tasks: BackgroundTasks):
    response = auth_service.execute(auth_service.login_user, data)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)


@auth_router.post("/refresh-token")
def refresh_token(data: RefreshToken):
    response = auth_service.execute(auth_service.refresh_token, data)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)


@auth_router.post("/reset-password")
def reset_password(
    data: ResetPassword,
    user_email: str = Depends(get_verified_user_email)
):
    response = auth_service.execute(auth_service.reset_password, data, user_email)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)


@auth_router.post("/logout")
def logout_user(
    email: str = Header(..., alias="X-User-Email"),
    authorization: str = Header(..., alias="Authorization"),
    x_refresh_token: str = Header(..., alias="X-Refresh-Token")
):
    access_token = authorization.strip()
    refresh_token = x_refresh_token.strip()
    if authorization.lower().startswith("bearer "):
        access_token = authorization[7:].strip()
    if x_refresh_token.lower().startswith("bearer "):
        refresh_token = x_refresh_token[7:].strip()

    response = auth_service.execute(
        auth_service.logout_user,
        (email, access_token, refresh_token)
    )
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@auth_router.post("/add-user-details")
def add_user_details(
    data: AddUserRequest,
    current_user: User = Depends(check_if_admin)
):
    response = auth_service.execute(auth_service.add_user_service, data)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@auth_router.post("/add-user-test")
def add_user_test(data: AddUserRequest):
    response = auth_service.execute(auth_service.add_user_test, data)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@auth_router.post("/role-info", dependencies=[Depends(check_if_admin)])
def get_role_info():
    response = auth_service.execute(auth_service.get_all_roles)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@auth_router.post("/get-managers", dependencies=[Depends(check_if_admin)])
def get_managers(organization_id: str = Query(...)):
    response = auth_service.get_organization_managers(organization_id)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@auth_router.post("/get-users", dependencies=[Depends(check_if_admin)])
def get_users(organization_id: str = Query(...)):
    response = auth_service.get_organization_users(organization_id)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)

@auth_router.patch("/update-user", dependencies=[Depends(check_if_admin)])
def update_user(user_id: str = Query(...), request_body: dict = Body(...), current_user: User = Depends(get_current_user)):
    response = auth_service.update_user_details(user_id, request_body, current_user)
    return JSONResponse(content={"data": response.data, "error": response.error}, status_code=response.status_code)
