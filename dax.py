from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from uuid import UUID

from app.models.users import User
from app.services.dax.dax_processor import DaxProcessor
from app.core.dependencies import get_current_user
from app.schemas.analyse import SuccessResponse

dax_router = APIRouter()

@dax_router.post("/calc-dax/{report_id}", response_model=SuccessResponse)
async def calc_dax_api( report_id: UUID, user: User = Depends(get_current_user)):
    response = await DaxProcessor.convert_dax(report_id, user)

    return JSONResponse(
        status_code=response.status_code,
        content=
        {
            "message": response.error or "Success",
            "data": response.data
        }
    )