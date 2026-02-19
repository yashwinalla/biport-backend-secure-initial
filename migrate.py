from fastapi import (
    APIRouter,
    HTTPException,
    Depends
)
from fastapi.responses import JSONResponse
from uuid import UUID
from app.services.migrate.migration_processor import MigrateProcessor
from app.models.users import User
from app.core.dependencies import get_current_user
from app.core import logger


migrate_router = APIRouter()

@migrate_router.post("/tableau-to-powerbi/{report_id}")
async def migrate_report_to_powerbi(
    report_id: UUID,
    user: User = Depends(get_current_user)
):
    """
    API for migrating a single report from Tableau to Power BI.
    """
    logger.info(f"[Migration API] Starting migration for report_id: {report_id}, user: {user.email}")

    try:
        response = await MigrateProcessor.migrate_single_report(report_id, user)
        
        # Determine status and message based on response
        if response.status_code == 200:
            status = "Success"
            message = "Migration completed successfully"
        else:
            status = "Failed"
            message = response.error or "Migration failed"
        
        logger.info(f"[Migration API] Migration completed with status {status} for report_id: {report_id}")
        
        return JSONResponse(
            status_code=response.status_code,
            content={
                "status": status,
                "message": message,
                "data": response.data
            }
        )

    except HTTPException as he:
        logger.error(f"[Migration API] HTTPException for report_id: {report_id}, error: {str(he)}", exc_info=True)
        return JSONResponse(
            status_code=he.status_code,
            content={
                "status": "Failed",
                "message": str(he.detail),
                "data": None
            }
        )
    except Exception as e:
        logger.error(f"[Migration API] Migration failed for report_id: {report_id}, error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "Failed",
                "message": f"Migration failed: {str(e)}",
                "data": None
            }
        )
