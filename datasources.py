from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.services.data_sources.datasources_processor import DatasourceProcessor
from app.schemas.datasources import *
from app.models_old.user import UserOld
from app.core.dependencies import get_current_user

datasources_router = APIRouter()

@datasources_router.put("/adding-user-details", response_model = dict)
async def add_data_source_details(
                                request: AddDataSourceDetails,
                                user: UserOld = Depends(get_current_user)
                                ):
        """Add data sources for existing users."""
        response  =  DatasourceProcessor.add_data_source_details(request)
        return JSONResponse(
            {"data": response.data, "error": response.error},
            status_code = response.status_code,
        )


@datasources_router.delete("/remove-user-details", response_model = dict)
async def remove_user_details(
                            request: RemoveUserDetails,
                            user: UserOld = Depends(get_current_user)
                            ):
        """Remove user details."""
        response  =  DatasourceProcessor.remove_user_details(request)
        return JSONResponse(
            {"data": response.data, "error": response.error},
            status_code = response.status_code,
        )


@datasources_router.get("/get-user-details", response_model = dict)
async def get_all_ds_details(
                            request: GetUserDetails,
                            user: UserOld = Depends(get_current_user)
                            ):
        """Get all data source details for a user."""
        response  =  DatasourceProcessor.get_user_details(request)
        return JSONResponse(
            {"data": response.data, "error": response.error},
            status_code = response.status_code,
        )


@datasources_router.put("/update-existing-ds-details", response_model = dict)
async def update_existing_ds_details(
                                request: UpdateExistingDataSource,
                                user: UserOld = Depends(get_current_user)
                                ):
        """Update existing data source details."""
        response  =  DatasourceProcessor.update_existing_data_source(request)
        return JSONResponse(
            {"data": response.data, "error": response.error},
            status_code = response.status_code,
        )
