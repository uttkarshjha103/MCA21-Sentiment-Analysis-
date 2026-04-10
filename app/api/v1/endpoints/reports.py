"""
Report generation and export endpoints.
"""
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.api.v1.endpoints.auth import get_current_user
from app.models.report import ReportCreate, ReportFilters, ReportResponse
from app.models.user import User
from app.services.reports import ReportService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_report_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ReportService:
    return ReportService(db)


@router.post("/excel", response_model=ReportResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_excel_report(
    request: ReportCreate,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    """Generate an Excel report. Returns download_url when complete."""
    user_id = str(current_user.id) if current_user.id else str(current_user.email)
    result = await service.generate_excel_report(request, user_id)
    if result.status == "failed":
        raise HTTPException(status_code=500, detail=result.error_message or "Report generation failed")
    return result


@router.get("/export/csv")
async def export_csv(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sentiment: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    include_metadata: bool = Query(True),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    """Stream a CSV export of raw comment data."""
    filters = ReportFilters(date_from=date_from, date_to=date_to, sentiment=sentiment, language=language, source=source)
    csv_bytes = await service.export_csv(filters, include_metadata=include_metadata)
    filename = f"mca21_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report_status(
    report_id: str,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    """Get report status by ID."""
    report = await service.get_report_status(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    if report.status == "completed":
        report.download_url = f"/api/v1/reports/{report_id}/download"
    return report


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    """Download a completed report file."""
    file_path = await service.get_report_file_path(report_id)
    if not file_path:
        report = await service.get_report_status(report_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
        raise HTTPException(status_code=409, detail=f"Report not ready (status: {report.status})")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=410, detail="Report file no longer available")
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(file_path),
    )
