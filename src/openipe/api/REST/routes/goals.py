"""HTTP translation for goal operations."""
from fastapi import APIRouter,Depends,HTTPException,Query
from openipe.api.REST.dependencies import get_current_user,get_internal_api
from openipe.api.REST.schemas.goal import GoalCreateRequest, GoalResponse, GoalUpdateRequest
from openipe.api.internal import InternalAPI,InternalContext
from openipe.api.internal.errors import InternalNotFoundError as NotFoundError, InternalValidationError as ValidationError
from openipe.api.internal.contracts import GoalStatus
from openipe.api.internal.contracts import GoalCreateContract, GoalUpdateContract
router=APIRouter(prefix="/goals",tags=["goals"])
@router.get("",response_model=list[GoalResponse])
async def list_goals(goal_status:GoalStatus|None=Query(None,alias="status"),context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.goals.list(context,goal_status)
@router.post("",response_model=GoalResponse,status_code=201)
async def create_goal(request:GoalCreateRequest,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:return internal.goals.create(context,GoalCreateContract(request.title,request.description,request.target_date,request.source_inbox_item_id))
 except (NotFoundError,ValidationError) as e:raise HTTPException(400,str(e)) from e
@router.get("/{goal_id}",response_model=GoalResponse)
async def get_goal(goal_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:return internal.goals.get(context,goal_id)
 except NotFoundError as e:raise HTTPException(404,"Goal not found") from e
@router.patch("/{goal_id}",response_model=GoalResponse)
async def update_goal(goal_id:int,request:GoalUpdateRequest,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:
  f=request.model_fields_set
  return internal.goals.update(context,goal_id,GoalUpdateContract(request.title,request.description,request.status,request.target_date,request.source_inbox_item_id,frozenset(f)))
 except NotFoundError as e:raise HTTPException(404,"Goal not found") from e
 except ValidationError as e:raise HTTPException(400,str(e)) from e
async def _associate(kind,goal_id,related_id,context,internal):
 try:return internal.goals.associate(context,goal_id,related_id,kind)
 except NotFoundError as e:raise HTTPException(404,str(e)) from e
async def _remove(kind,goal_id,related_id,context,internal):
 try:internal.goals.remove(context,goal_id,related_id,kind)
 except NotFoundError as e:raise HTTPException(404,str(e)) from e
@router.post("/{goal_id}/projects/{project_id}",response_model=GoalResponse)
async def associate_project(goal_id:int,project_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):return await _associate("project",goal_id,project_id,context,internal)
@router.delete("/{goal_id}/projects/{project_id}",status_code=204)
async def remove_project(goal_id:int,project_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):return await _remove("project",goal_id,project_id,context,internal)
@router.post("/{goal_id}/tasks/{task_id}",response_model=GoalResponse)
async def associate_task(goal_id:int,task_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):return await _associate("task",goal_id,task_id,context,internal)
@router.delete("/{goal_id}/tasks/{task_id}",status_code=204)
async def remove_task(goal_id:int,task_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):return await _remove("task",goal_id,task_id,context,internal)
@router.post("/{goal_id}/habits/{habit_id}",response_model=GoalResponse)
async def associate_habit(goal_id:int,habit_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):return await _associate("habit",goal_id,habit_id,context,internal)
@router.delete("/{goal_id}/habits/{habit_id}",status_code=204)
async def remove_habit(goal_id:int,habit_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):return await _remove("habit",goal_id,habit_id,context,internal)
