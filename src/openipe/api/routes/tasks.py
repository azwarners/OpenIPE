"""Task routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from openipe.api.dependencies import get_connection, get_current_user
from openipe.api.routes.projects import _task_response
from openipe.api.schemas.task import TaskCreateRequest, TaskResponse, TaskUpdateRequest
from openipe.application.task_service import UNSET, TaskService
from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.task import TaskStatus
from openipe.core.models.user import User

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def get_task_service(connection=Depends(get_connection)) -> TaskService:
    return TaskService(connection)


@router.get("", response_model=list[TaskResponse])
async def list_tasks(status_filter: TaskStatus | None = Query(default=None, alias="status"), project_id: int | None = None,
                     user: User = Depends(get_current_user), service: TaskService = Depends(get_task_service)):
    return [_task_response(task) for task in service.list(user.id, status_filter, project_id)]


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(request: TaskCreateRequest, user: User = Depends(get_current_user), service: TaskService = Depends(get_task_service)):
    try:
        return _task_response(service.create(user.id, request.title, request.description, request.project_id,
                                             request.priority, request.due_date, request.is_today, request.source_inbox_item_id))
    except (NotFoundError, ValidationError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, user: User = Depends(get_current_user), service: TaskService = Depends(get_task_service)):
    try:
        return _task_response(service.get(user.id, task_id))
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from error


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, request: TaskUpdateRequest, user: User = Depends(get_current_user), service: TaskService = Depends(get_task_service)):
    try:
        fields = request.model_fields_set
        return _task_response(service.update(
            user.id, task_id,
            request.title if "title" in fields else UNSET,
            request.description if "description" in fields else UNSET,
            request.project_id if "project_id" in fields else UNSET,
            request.status if "status" in fields else UNSET,
            request.priority if "priority" in fields else UNSET,
            request.due_date if "due_date" in fields else UNSET,
            request.is_today if "is_today" in fields else UNSET,
            request.source_inbox_item_id if "source_inbox_item_id" in fields else UNSET,
        ))
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: int, user: User = Depends(get_current_user), service: TaskService = Depends(get_task_service)):
    return _lifecycle(lambda: service.complete(user.id, task_id), service, task_id)


@router.post("/{task_id}/reopen", response_model=TaskResponse)
async def reopen_task(task_id: int, user: User = Depends(get_current_user), service: TaskService = Depends(get_task_service)):
    return _lifecycle(lambda: service.reopen(user.id, task_id), service, task_id)


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(task_id: int, user: User = Depends(get_current_user), service: TaskService = Depends(get_task_service)):
    return _lifecycle(lambda: service.cancel(user.id, task_id), service, task_id)


def _lifecycle(action, service, task_id):
    try:
        return _task_response(action())
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
