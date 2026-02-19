import json
from app.core.enums import RoleEnum
from app.models.roles import RoleManager
from app.models.users import User, UserManager
from app.core import AuthenticationError, AuthorizationError, BLOCKED_EMAILS, logger
from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth import decode_secure_jwt, decode_base


from app.core import scoped_context
from app.core.enums import RoleEnum
from app.models.users import User
from app.models.roles import RoleManager
from app.core.exceptions import AuthorizationError
from sqlalchemy.orm import joinedload

security = HTTPBearer(auto_error=True)

async def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    encoded_email: str = Header(..., alias="X-User-Email")
):
    try:

        if not authorization.startswith("Bearer "):
            logger.error(f"[get_current_user] Invalid Authorization header format")
            raise AuthorizationError("Invalid Authorization header")

        token = authorization.split(" ")[1]

        email = decode_base(encoded_email)

        jwt_result = decode_secure_jwt(token, email)

        payload = json.loads(jwt_result.get("sub"))
        if not payload:
            logger.error(f"[get_current_user] Invalid token payload")
            raise AuthenticationError("Invalid token")


        # Extract role from payload
        role_name = payload.get("role")
        if not role_name:
            logger.error(f"[get_current_user] Role not found in token")
            raise AuthenticationError("Role not found in token")


        # Fetch user with role eagerly loaded
        user = UserManager.get_user_by_email(email, load_role=True)
        if not user:
            logger.error(f"[get_current_user] User not found: {email}")
            raise AuthenticationError("User not found")


        # Attach role_name from login response
        user.role_name = role_name
        return user
    except AuthenticationError as e:
        logger.error(f"[get_current_user] AuthenticationError: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except AuthorizationError as e:
        logger.error(f"[get_current_user] AuthorizationError: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"[get_current_user] Unexpected error: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Authentication failed")

async def get_current_new_user(
    authorization: str = Header(..., alias="Authorization"),
    encoded_email: str = Header(..., alias="X-User-Email")
):
    try:
        if not authorization.startswith("Bearer "):
            raise AuthorizationError("Invalid Authorization header")

        token = authorization.split(" ")[1]
        email = decode_base(encoded_email)
        payload = json.loads(decode_secure_jwt(token, email).get("sub"))
        if not payload:
            raise AuthenticationError("Invalid token")

        # Extract role from payload
        role_name = payload.get("role")
        if not role_name:
            logger.error(f"[get_current_new_user] Role not found in token")
            raise AuthenticationError("Role not found in token")

        # Fetch user with role eagerly loaded
        user = UserManager.get_user_by_email(email, load_role=True)
        if not user:
            logger.error(f"[get_current_new_user] User not found: {email}")
            raise AuthenticationError("User not found")

        # Attach role_name from login response
        user.role_name = role_name
        return user
    except Exception as e:
        logger.error(f"[get_current_new_user] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=str(e))

def get_verified_user_email(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    encoded_email: str = Header(..., alias="X-User-Email")
) -> str:
    token = credentials.credentials
    try:
        email = decode_base(encoded_email)
        payload = json.loads(decode_secure_jwt(token, email).get("sub"))

        if payload.get("email") != email:
            raise AuthenticationError("Token/email mismatch")

        return email
    except Exception as e:
        raise AuthenticationError(str(e))

async def check_blocked_email(request: Request):
    email = request.headers.get("X-User-Email") or request.query_params.get("email")
    if email and email in BLOCKED_EMAILS:
        logger.warning(f"Blocked email access attempt: {email}")
        raise AuthorizationError("Access denied. This email is blocked.")

async def check_if_admin(
    user: User = Depends(get_current_user)
):
    role_name = RoleManager.get_role_name(user.role_id)
    if role_name != RoleEnum.ADMIN:
        raise AuthorizationError("Only Admins are authorized to access this endpoint.")
    return user