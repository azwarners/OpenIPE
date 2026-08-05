"""Today dashboard route."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from openipe.api.dependencies import get_connection, get_current_user
from openipe.api.schemas.today import TodayResponse
from openipe.application.today_service import TodayService
from openipe.core.models.user import User

router = APIRouter(prefix="/today", tags=["today"])


async def get_today_service(connection=Depends(get_connection)) -> TodayService:
    return TodayService(connection)


@router.get("", response_model=TodayResponse)
async def today(
    selected_date: date | None = Query(default=None, alias="date"),
    include_completed: bool = False,
    user: User = Depends(get_current_user),
    service: TodayService = Depends(get_today_service),
):
    return service.get(user.id, selected_date, include_completed)
