"""Habit stack routes."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from openipe.api.dependencies import get_connection, get_current_user
from openipe.api.routes.habits import _habit_response
from openipe.api.schemas.habit_stack import HabitStackCreateRequest, HabitStackResponse, HabitStackUpdateRequest, ReorderRequest
from openipe.application.habit_stack_service import UNSET, HabitStackService
from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.user import User

router = APIRouter(prefix="/habit-stacks", tags=["habit-stacks"])


async def get_stack_service(connection=Depends(get_connection)) -> HabitStackService:
    return HabitStackService(connection)


@router.get("", response_model=list[HabitStackResponse])
async def list_stacks(active: bool | None = None, selected_date: date | None = Query(default=None, alias="date"),
                      user: User = Depends(get_current_user), service: HabitStackService = Depends(get_stack_service)):
    selected_date = selected_date or date.today()
    return [_response(service, user.id, stack, selected_date) for stack in service.list(user.id, active)]


@router.post("", response_model=HabitStackResponse, status_code=status.HTTP_201_CREATED)
async def create_stack(request: HabitStackCreateRequest, user: User = Depends(get_current_user), service: HabitStackService = Depends(get_stack_service)):
    try:
        stack = service.create(user.id, request.name, request.description)
        return _response(service, user.id, stack, date.today())
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/{stack_id}", response_model=HabitStackResponse)
async def get_stack(stack_id: int, selected_date: date | None = Query(default=None, alias="date"),
                    user: User = Depends(get_current_user), service: HabitStackService = Depends(get_stack_service)):
    try:
        return _response(service, user.id, service.get(user.id, stack_id), selected_date or date.today())
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit stack not found") from error


@router.patch("/{stack_id}", response_model=HabitStackResponse)
async def update_stack(stack_id: int, request: HabitStackUpdateRequest, user: User = Depends(get_current_user), service: HabitStackService = Depends(get_stack_service)):
    try:
        if request.archived:
            stack = service.archive(user.id, stack_id)
        else:
            fields = request.model_fields_set
            stack = service.update(user.id, stack_id,
                                   request.name if "name" in fields else UNSET,
                                   request.description if "description" in fields else UNSET,
                                   request.active if "active" in fields else UNSET)
        return _response(service, user.id, stack, date.today())
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit stack not found") from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_stacks(request: ReorderRequest, user: User = Depends(get_current_user), service: HabitStackService = Depends(get_stack_service)):
    try:
        service.reorder_stacks(user.id, request.ids)
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/{stack_id}/habits/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_habits(stack_id: int, request: ReorderRequest, user: User = Depends(get_current_user), service: HabitStackService = Depends(get_stack_service)):
    try:
        service.reorder_habits(user.id, stack_id, request.ids)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit stack not found") from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/{stack_id}/habits/{habit_id}", response_model=HabitStackResponse)
async def add_habit(stack_id: int, habit_id: int, user: User = Depends(get_current_user), service: HabitStackService = Depends(get_stack_service)):
    try:
        service.add_habit(user.id, stack_id, habit_id)
        return _response(service, user.id, service.get(user.id, stack_id), date.today())
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/{stack_id}/habits/{habit_id}", response_model=HabitStackResponse)
async def remove_habit(stack_id: int, habit_id: int, user: User = Depends(get_current_user), service: HabitStackService = Depends(get_stack_service)):
    try:
        service.remove_habit(user.id, stack_id, habit_id)
        return _response(service, user.id, service.get(user.id, stack_id), date.today())
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


def _response(service, user_id, stack, selected_date):
    habits = service.habits_in_stack(user_id, stack.id)
    completed, scheduled = service.progress(user_id, stack.id, selected_date)
    return HabitStackResponse(id=stack.id, name=stack.name, description=stack.description, position=stack.position,
                              active=stack.active, created_at=stack.created_at, updated_at=stack.updated_at,
                              archived_at=stack.archived_at, completed_count=completed, scheduled_count=scheduled,
                              habits=[_habit_response(habit) for habit in habits])
