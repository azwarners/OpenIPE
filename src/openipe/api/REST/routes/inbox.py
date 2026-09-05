"""HTTP translation for inbox operations."""
from fastapi import APIRouter,Depends,HTTPException,Query
from openipe.api.REST.dependencies import get_current_user,get_internal_api
from openipe.api.REST.schemas.inbox import CreateHabitFromInboxRequest, CreateProjectFromInboxRequest, CreateTaskFromInboxRequest, InboxCreateRequest, InboxResponse, InboxUpdateRequest
from openipe.api.REST.schemas.project import ProjectResponse
from openipe.api.REST.schemas.task import TaskResponse
from openipe.api.REST.schemas.habit import HabitResponse
from openipe.api.internal import InternalAPI,InternalContext
from openipe.api.internal.contracts import InboxCreateContract, InboxHabitConversionContract, InboxTaskConversionContract, InboxUpdateContract
from openipe.api.internal.errors import InternalNotFoundError as NotFoundError, InternalValidationError as ValidationError
from openipe.api.internal.contracts import InboxStatus
router=APIRouter(prefix="/inbox",tags=["inbox"])
@router.get("",response_model=list[InboxResponse])
async def list_inbox(item_status:InboxStatus|None=Query(None,alias="status"),context:InternalContext=Depends(get_current_user),internal:InternalAPI=Depends(get_internal_api)): return internal.inbox.list(context,item_status)
@router.post("",response_model=InboxResponse,status_code=201)
async def create_inbox_item(request:InboxCreateRequest,context=Depends(get_current_user),internal:InternalAPI=Depends(get_internal_api)):
 try:return internal.inbox.create(context,InboxCreateContract(request.text))
 except ValidationError as e:raise HTTPException(400,str(e)) from e
@router.get("/{item_id}",response_model=InboxResponse)
async def get_inbox_item(item_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:return internal.inbox.get(context,item_id)
 except NotFoundError as e:raise HTTPException(404,"Inbox item not found") from e
@router.patch("/{item_id}",response_model=InboxResponse)
async def update_inbox_item(item_id:int,request:InboxUpdateRequest,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:return internal.inbox.update(context,item_id,InboxUpdateContract(request.text,request.status))
 except NotFoundError as e:raise HTTPException(404,"Inbox item not found") from e
 except ValidationError as e:raise HTTPException(400,str(e)) from e
@router.delete("/{item_id}",status_code=204)
async def delete_inbox_item(item_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:internal.inbox.delete(context,item_id)
 except NotFoundError as e:raise HTTPException(404,"Inbox item not found") from e
@router.post("/{item_id}/create-task",response_model=TaskResponse,status_code=201)
async def create_task_from_inbox(item_id:int,request:CreateTaskFromInboxRequest,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:return internal.inbox.create_task(context,item_id,InboxTaskConversionContract(request.description,request.project_id,request.priority,request.due_date,request.is_today))
 except NotFoundError as e:raise HTTPException(404,"Inbox item not found") from e
 except ValidationError as e:raise HTTPException(400,str(e)) from e
@router.post("/{item_id}/create-project",response_model=ProjectResponse,status_code=201)
async def create_project_from_inbox(item_id:int,request:CreateProjectFromInboxRequest,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:return internal.inbox.create_project(context,item_id,request.description)
 except NotFoundError as e:raise HTTPException(404,"Inbox item not found") from e
 except ValidationError as e:raise HTTPException(400,str(e)) from e
@router.post("/{item_id}/create-habit",response_model=HabitResponse,status_code=201)
async def create_habit_from_inbox(item_id:int,request:CreateHabitFromInboxRequest,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:return internal.inbox.create_habit(context,item_id,InboxHabitConversionContract(request.description,request.frequency_type,request.frequency_config,request.minimum_version))
 except NotFoundError as e:raise HTTPException(404,"Inbox item not found") from e
 except ValidationError as e:raise HTTPException(400,str(e)) from e
