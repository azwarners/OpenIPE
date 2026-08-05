"""Project routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from openipe.api.dependencies import get_connection, get_current_user
from openipe.api.schemas.project import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest
from openipe.api.schemas.task import TaskResponse
from openipe.application.project_service import UNSET, ProjectService
from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.project import Project
from openipe.core.models.user import User

router = APIRouter(prefix="/projects", tags=["projects"])


async def get_project_service(connection=Depends(get_connection)) -> ProjectService:
    return ProjectService(connection)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(user: User = Depends(get_current_user), service: ProjectService = Depends(get_project_service)):
    return [_response(service, user.id, project) for project in service.list(user.id)]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(request: ProjectCreateRequest, user: User = Depends(get_current_user), service: ProjectService = Depends(get_project_service)):
    try:
        return _response(service, user.id, service.create(user.id, request.title, request.description, request.source_inbox_item_id))
    except (NotFoundError, ValidationError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, user: User = Depends(get_current_user), service: ProjectService = Depends(get_project_service)):
    try:
        return _response(service, user.id, service.get(user.id, project_id))
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from error


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, request: ProjectUpdateRequest, user: User = Depends(get_current_user), service: ProjectService = Depends(get_project_service)):
    try:
        fields = request.model_fields_set
        project = service.update(
            user.id, project_id,
            request.title if "title" in fields else UNSET,
            request.description if "description" in fields else UNSET,
            request.status if "status" in fields else UNSET,
            request.source_inbox_item_id if "source_inbox_item_id" in fields else UNSET,
        )
        return _response(service, user.id, project)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/{project_id}/tasks", response_model=list[TaskResponse])
async def project_tasks(project_id: int, user: User = Depends(get_current_user), service: ProjectService = Depends(get_project_service)):
    try:
        return [_task_response(task) for task in service.task_list(user.id, project_id)]
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from error


@router.post("/{project_id}/next-action/{task_id}", response_model=ProjectResponse)
async def set_next_action(project_id: int, task_id: int, user: User = Depends(get_current_user), service: ProjectService = Depends(get_project_service)):
    try:
        return _response(service, user.id, service.set_next_action(user.id, project_id, task_id))
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/{project_id}/next-action", response_model=ProjectResponse)
async def clear_next_action(project_id: int, user: User = Depends(get_current_user), service: ProjectService = Depends(get_project_service)):
    try:
        return _response(service, user.id, service.clear_next_action(user.id, project_id))
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from error


def _response(service, user_id, project: Project) -> ProjectResponse:
    task_ids, total, completed, open_count = service.progress(user_id, project.id)
    return ProjectResponse(id=project.id, title=project.title, description=project.description, status=project.status,
                           next_action_task_id=project.next_action_task_id, source_inbox_item_id=project.source_inbox_item_id,
                           created_at=project.created_at, updated_at=project.updated_at, completed_at=project.completed_at,
                           archived_at=project.archived_at, task_ids=task_ids, total_task_count=total,
                           completed_task_count=completed, open_task_count=open_count)


def _task_response(task) -> TaskResponse:
    return TaskResponse(id=task.id, title=task.title, description=task.description, project_id=task.project_id,
                        status=task.status, priority=task.priority, due_date=task.due_date, is_today=task.is_today,
                        source_inbox_item_id=task.source_inbox_item_id, created_at=task.created_at,
                        updated_at=task.updated_at, completed_at=task.completed_at, archived_at=task.archived_at)
