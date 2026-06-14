"""Analytics dashboard routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentUser
from app.models.dashboard import DashboardSummary
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def summary(current_user: CurrentUser) -> DashboardSummary:
    """Return aggregated analytics for the current user."""
    return await dashboard_service.get_summary(current_user.id)
