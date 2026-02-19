from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from uuid import UUID
from typing import List

from app.models.users import User
from app.services.analysis import AnalysisProcessor
from app.core.dependencies import get_current_user
from app.core import logger
from app.schemas.analyse import ReportAnalysisRequest


analysis_router = APIRouter()   


@analysis_router.post("/generate_report")
async def generate_report_analysis(
    request: ReportAnalysisRequest,
    user: User = Depends(get_current_user)
):
    """
    Triggers report analysis for one or multiple reports.
    - If single report ID: processes single report and returns result
    - If multiple report IDs: processes all reports and returns consolidated results
    - Returns pre-signed URLs if already analyzed, or performs analysis if needed

    Args:
        request (ReportAnalysisRequest): JSON body containing list of report IDs (can be single or multiple).
        user (User): Authenticated user.

    Returns:
        JSONResponse: Contains status, message, and data with analysis results.
                     For single report: direct result data
                     For multiple reports: consolidated results with success/failure counts
    """
    logger.info(f"[Analysis API] Starting analysis for {len(request.report_ids)} report(s), user: {user.email}")
    
    try:
        response = await AnalysisProcessor.analyse_processor(request.report_ids, user)
        
        # Determine status based on response
        if response.status_code == 200:
            status = "Success"
            message = response.error or "Analysis completed successfully"
        elif response.status_code == 207:  # Multi-Status for partial success
            status = "Partial Success"
            message = response.error or "Some reports completed successfully"
        else:
            status = "Failed"
            message = response.error or "Analysis failed"
        
        logger.info(f"[Analysis API] Analysis completed with status {status} for {len(request.report_ids)} report(s)")
        
        return JSONResponse(
            status_code=response.status_code,
            content={
                "status": status,
                "message": message,
                "data": response.data
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Analysis API] Analysis failed for {len(request.report_ids)} report(s), error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "Failed",
                "message": f"Analysis failed: {str(e)}",
                "data": None
            }
        )
