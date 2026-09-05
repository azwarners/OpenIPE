"""HTTP translation for project operations."""
from fastapi import APIRouter,Depends,HTTPException
from openipe.api.REST.dependencies import get_current_user,get_internal_api
from openipe.api.REST.schemas.project import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest
from openipe.api.REST.schemas.task import TaskResponse
from openipe.api.internal import InternalAPI
from openipe.api.internal.errors import InternalNotFoundError as NotFoundError, InternalValidationError as ValidationError
from openipe.api.internal.contracts import ProjectCreateContract, ProjectUpdateContract
router=APIRouter(prefix="/projects",tags=["projects"])
@router.get("",response_model=list[ProjectResponse])
async def list_projects(context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.projects.list(context)
@router.post("",response_model=ProjectResponse,status_code=201)
async def create_project(request:ProjectCreateRequest,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:return internal.projects.create(context,ProjectCreateContract(request.title,request.description,request.source_inbox_item_id))
 except (NotFoundError,ValidationError) as e:raise HTTPException(400,str(e)) from e
@router.get("/{project_id}",response_model=ProjectResponse)
async def get_project(project_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:return internal.projects.get(context,project_id)
 except NotFoundError as e:raise HTTPException(404,"Project not found") from e
@router.patch("/{project_id}",response_model=ProjectResponse)
async def update_project(project_id:int,request:ProjectUpdateRequest,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:
  f=request.model_fields_set
  return internal.projects.update(context,project_id,ProjectUpdateContract(request.title,request.description,request.status,request.source_inbox_item_id,frozenset(f)))
 except NotFoundError as e:raise HTTPException(404,"Project not found") from e
 except ValidationError as e:raise HTTPException(400,str(e)) from e
@router.get("/{project_id}/tasks",response_model=list[TaskResponse])
async def project_tasks(project_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.projects.tasks(context,project_id)
@router.post("/{project_id}/next-action/{task_id}",response_model=ProjectResponse)
async def set_next_action(project_id:int,task_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:return internal.projects.set_next_action(context,project_id,task_id)
 except NotFoundError as e:raise HTTPException(404,"Project not found") from e
 except ValidationError as e:raise HTTPException(400,str(e)) from e
@router.delete("/{project_id}/next-action",response_model=ProjectResponse)
async def clear_next_action(project_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.projects.clear_next_action(context,project_id)
