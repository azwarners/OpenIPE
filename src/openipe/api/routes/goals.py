"""Goal routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from openipe.api.dependencies import get_connection, get_current_user
from openipe.api.schemas.goal import GoalCreateRequest, GoalResponse, GoalUpdateRequest
from openipe.application.goal_service import UNSET, GoalService
from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.goal import Goal, GoalStatus
from openipe.core.models.user import User

router = APIRouter(prefix="/goals", tags=["goals"])


async def get_goal_service(connection=Depends(get_connection)) -> GoalService:
    return GoalService(connection)


@router.get("", response_model=list[GoalResponse])
async def list_goals(
    goal_status: GoalStatus | None = Query(default=None, alias="status"),
    user: User = Depends(get_current_user),
    service: GoalService = Depends(get_goal_service),
):
    return [_response(service, user.id, goal) for goal in service.list(user.id, goal_status)]


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    request: GoalCreateRequest,
    user: User = Depends(get_current_user),
    service: GoalService = Depends(get_goal_service),
):
    try:
        return _response(
            service, user.id, service.create(
                user.id,
                request.title,
                request.description,
                request.target_date,
                request.source_inbox_item_id,
            )
        )
    except (NotFoundError, ValidationError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: int,
    user: User = Depends(get_current_user),
    service: GoalService = Depends(get_goal_service),
):
    try:
        return _response(service, user.id, service.get(user.id, goal_id))
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found") from error


@router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: int,
    request: GoalUpdateRequest,
    user: User = Depends(get_current_user),
    service: GoalService = Depends(get_goal_service),
):
    try:
        return _response(
            service, user.id, service.update(
                user.id,
                goal_id,
                request.title if "title" in request.model_fields_set else UNSET,
                request.description if "description" in request.model_fields_set else UNSET,
                request.status if "status" in request.model_fields_set else UNSET,
                request.target_date if "target_date" in request.model_fields_set else UNSET,
                request.source_inbox_item_id
                if "source_inbox_item_id" in request.model_fields_set
                else UNSET,
            )
        )
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found") from error
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/{goal_id}/projects/{project_id}", response_model=GoalResponse)
async def associate_project(goal_id: int, project_id: int, user: User = Depends(get_current_user), service: GoalService = Depends(get_goal_service)):
    return _associate(lambda: service.associate_project(user.id, goal_id, project_id), service, user.id)


@router.delete("/{goal_id}/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project(goal_id: int, project_id: int, user: User = Depends(get_current_user), service: GoalService = Depends(get_goal_service)):
    return _remove(lambda: service.remove_association(user.id, goal_id, project_id, "project"))


@router.post("/{goal_id}/tasks/{task_id}", response_model=GoalResponse)
async def associate_task(goal_id: int, task_id: int, user: User = Depends(get_current_user), service: GoalService = Depends(get_goal_service)):
    return _associate(lambda: service.associate_task(user.id, goal_id, task_id), service, user.id)


@router.delete("/{goal_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_task(goal_id: int, task_id: int, user: User = Depends(get_current_user), service: GoalService = Depends(get_goal_service)):
    return _remove(lambda: service.remove_association(user.id, goal_id, task_id, "task"))


@router.post("/{goal_id}/habits/{habit_id}", response_model=GoalResponse)
async def associate_habit(goal_id: int, habit_id: int, user: User = Depends(get_current_user), service: GoalService = Depends(get_goal_service)):
    return _associate(lambda: service.associate_habit(user.id, goal_id, habit_id), service, user.id)


@router.delete("/{goal_id}/habits/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_habit(goal_id: int, habit_id: int, user: User = Depends(get_current_user), service: GoalService = Depends(get_goal_service)):
    return _remove(lambda: service.remove_association(user.id, goal_id, habit_id, "habit"))


def _response(service: GoalService, user_id: int, goal: Goal) -> GoalResponse:
    associations = service.associated_ids(user_id, goal.id)
    return GoalResponse(
        id=goal.id,
        title=goal.title,
        description=goal.description,
        status=goal.status,
        target_date=goal.target_date,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
        achieved_at=goal.achieved_at,
        archived_at=goal.archived_at,
        source_inbox_item_id=goal.source_inbox_item_id,
        **associations,
        evidence=service.evidence(user_id, goal.id),
    )


def _associate(action, service, user_id):
    try:
        goal = action()
        return _response(service, user_id, goal)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


def _remove(action):
    try:
        action()
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
