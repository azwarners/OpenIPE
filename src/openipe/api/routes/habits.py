"""Habit and check-in routes."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from openipe.api.dependencies import get_connection, get_current_user
from openipe.api.schemas.habit import HabitCheckInRequest, HabitCheckInResponse, HabitCreateRequest, HabitResponse, HabitUpdateRequest
from openipe.application.habit_service import UNSET, HabitService
from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.user import User

router = APIRouter(prefix="/habits", tags=["habits"])


async def get_habit_service(connection=Depends(get_connection)) -> HabitService:
    return HabitService(connection)


@router.get("", response_model=list[HabitResponse])
async def list_habits(active: bool | None = None, user: User = Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    return [_habit_response(habit) for habit in service.list(user.id, active)]


@router.post("", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
async def create_habit(request: HabitCreateRequest, user: User = Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    try:
        return _habit_response(service.create(user.id, request.title, request.description, request.frequency_type,
                                              request.frequency_config, request.minimum_version, request.source_inbox_item_id))
    except (NotFoundError, ValidationError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/{habit_id}", response_model=HabitResponse)
async def get_habit(habit_id: int, user: User = Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    try:
        return _habit_response(service.get(user.id, habit_id))
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found") from error


@router.patch("/{habit_id}", response_model=HabitResponse)
async def update_habit(habit_id: int, request: HabitUpdateRequest, user: User = Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    try:
        fields = request.model_fields_set
        if request.archived:
            return _habit_response(service.archive(user.id, habit_id))
        return _habit_response(service.update(
            user.id, habit_id,
            request.title if "title" in fields else UNSET,
            request.description if "description" in fields else UNSET,
            request.frequency_type if "frequency_type" in fields else UNSET,
            request.frequency_config if "frequency_config" in fields else UNSET,
            request.minimum_version if "minimum_version" in fields else UNSET,
            request.active if "active" in fields else UNSET,
            request.source_inbox_item_id if "source_inbox_item_id" in fields else UNSET,
        ))
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found") from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/{habit_id}/check-ins", response_model=HabitCheckInResponse)
async def check_in(habit_id: int, request: HabitCheckInRequest, user: User = Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    try:
        return _checkin_response(service.check_in(user.id, habit_id, request.date, request.status, request.note))
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found") from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/{habit_id}/check-ins", response_model=list[HabitCheckInResponse])
async def recent_check_ins(habit_id: int, limit: int = Query(default=30, ge=1, le=100), user: User = Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    try:
        return [_checkin_response(item) for item in service.recent_check_ins(user.id, habit_id, limit)]
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found") from error


@router.delete("/{habit_id}/check-ins/{checkin_date}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_check_in(habit_id: int, checkin_date: date, user: User = Depends(get_current_user), service: HabitService = Depends(get_habit_service)):
    try:
        service.delete_check_in(user.id, habit_id, checkin_date)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit check-in not found") from error


def _habit_response(habit) -> HabitResponse:
    return HabitResponse(id=habit.id, title=habit.title, description=habit.description, frequency_type=habit.frequency_type,
                         frequency_config=habit.frequency_config, minimum_version=habit.minimum_version, stack_id=habit.stack_id,
                         position=habit.position, active=habit.active, source_inbox_item_id=habit.source_inbox_item_id,
                         created_at=habit.created_at, updated_at=habit.updated_at, archived_at=habit.archived_at)


def _checkin_response(item) -> HabitCheckInResponse:
    return HabitCheckInResponse(id=item.id, habit_id=item.habit_id, date=item.date, status=item.status,
                                note=item.note, created_at=item.created_at, updated_at=item.updated_at)
