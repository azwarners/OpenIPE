"""Inbox idea-capture routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from openipe.api.dependencies import get_connection, get_current_user
from openipe.api.schemas.inbox import (
    CreateProjectFromInboxRequest,
    CreateHabitFromInboxRequest,
    CreateTaskFromInboxRequest,
    InboxCreateRequest,
    InboxResponse,
    InboxUpdateRequest,
)
from openipe.api.schemas.project import ProjectResponse
from openipe.api.schemas.task import TaskResponse
from openipe.api.schemas.habit import HabitResponse
from openipe.application.inbox_service import InboxService
from openipe.application.project_service import ProjectService
from openipe.application.task_service import TaskService
from openipe.application.habit_service import HabitService
from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.inbox import InboxStatus
from openipe.core.models.user import User

router = APIRouter(prefix="/inbox", tags=["inbox"])


async def get_inbox_service(connection=Depends(get_connection)) -> InboxService:
    return InboxService(connection)


async def get_project_service(connection=Depends(get_connection)) -> ProjectService:
    return ProjectService(connection)


async def get_task_service(connection=Depends(get_connection)) -> TaskService:
    return TaskService(connection)


async def get_habit_service(connection=Depends(get_connection)) -> HabitService:
    return HabitService(connection)


@router.get("", response_model=list[InboxResponse])
async def list_inbox(
    item_status: InboxStatus | None = Query(default=None, alias="status"),
    user: User = Depends(get_current_user),
    service: InboxService = Depends(get_inbox_service),
):
    return [_response(item) for item in service.list(user.id, item_status)]


@router.post("", response_model=InboxResponse, status_code=status.HTTP_201_CREATED)
async def create_inbox_item(
    request: InboxCreateRequest,
    user: User = Depends(get_current_user),
    service: InboxService = Depends(get_inbox_service),
):
    try:
        return _response(service.create(user.id, request.text))
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/{item_id}", response_model=InboxResponse)
async def get_inbox_item(
    item_id: int,
    user: User = Depends(get_current_user),
    service: InboxService = Depends(get_inbox_service),
):
    try:
        return _response(service.get(user.id, item_id))
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inbox item not found") from error


@router.patch("/{item_id}", response_model=InboxResponse)
async def update_inbox_item(
    item_id: int,
    request: InboxUpdateRequest,
    user: User = Depends(get_current_user),
    service: InboxService = Depends(get_inbox_service),
):
    try:
        return _response(service.update(user.id, item_id, request.text, request.status))
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inbox item not found") from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inbox_item(
    item_id: int,
    user: User = Depends(get_current_user),
    service: InboxService = Depends(get_inbox_service),
):
    try:
        service.delete(user.id, item_id)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inbox item not found") from error


@router.post("/{item_id}/create-task", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task_from_inbox(
    item_id: int,
    request: CreateTaskFromInboxRequest,
    user: User = Depends(get_current_user),
    inbox: InboxService = Depends(get_inbox_service),
    tasks: TaskService = Depends(get_task_service),
):
    try:
        item = inbox.get(user.id, item_id)
        return _task_response(tasks.create(user.id, item.text, request.description, request.project_id,
                                           request.priority, request.due_date, request.is_today, item.id))
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inbox item not found") from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/{item_id}/create-project", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project_from_inbox(
    item_id: int,
    request: CreateProjectFromInboxRequest,
    user: User = Depends(get_current_user),
    inbox: InboxService = Depends(get_inbox_service),
    projects: ProjectService = Depends(get_project_service),
):
    try:
        item = inbox.get(user.id, item_id)
        project = projects.create(user.id, item.text, request.description, item.id)
        return _project_response(projects, user.id, project)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inbox item not found") from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/{item_id}/create-habit", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
async def create_habit_from_inbox(
    item_id: int,
    request: CreateHabitFromInboxRequest,
    user: User = Depends(get_current_user),
    inbox: InboxService = Depends(get_inbox_service),
    habits: HabitService = Depends(get_habit_service),
):
    try:
        item = inbox.get(user.id, item_id)
        return _habit_response(habits.create(user.id, item.text, request.description, request.frequency_type,
                                             request.frequency_config, request.minimum_version, item.id))
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inbox item not found") from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


def _response(item) -> InboxResponse:
    return InboxResponse(
        id=item.id,
        text=item.text,
        status=item.status,
        created_at=item.created_at,
        updated_at=item.updated_at,
        processed_at=item.processed_at,
        archived_at=item.archived_at,
    )


def _task_response(task) -> TaskResponse:
    return TaskResponse(id=task.id, title=task.title, description=task.description, project_id=task.project_id,
                        status=task.status, priority=task.priority, due_date=task.due_date, is_today=task.is_today,
                        source_inbox_item_id=task.source_inbox_item_id, created_at=task.created_at,
                        updated_at=task.updated_at, completed_at=task.completed_at, archived_at=task.archived_at)


def _project_response(service, user_id, project) -> ProjectResponse:
    task_ids, total, completed, open_count = service.progress(user_id, project.id)
    return ProjectResponse(id=project.id, title=project.title, description=project.description, status=project.status,
                           next_action_task_id=project.next_action_task_id, source_inbox_item_id=project.source_inbox_item_id,
                           created_at=project.created_at, updated_at=project.updated_at, completed_at=project.completed_at,
                           archived_at=project.archived_at, task_ids=task_ids, total_task_count=total,
                           completed_task_count=completed, open_task_count=open_count)


def _habit_response(habit) -> HabitResponse:
    return HabitResponse(id=habit.id, title=habit.title, description=habit.description,
                         frequency_type=habit.frequency_type, frequency_config=habit.frequency_config,
                         minimum_version=habit.minimum_version, stack_id=habit.stack_id, position=habit.position,
                         active=habit.active, source_inbox_item_id=habit.source_inbox_item_id,
                         created_at=habit.created_at, updated_at=habit.updated_at, archived_at=habit.archived_at)
