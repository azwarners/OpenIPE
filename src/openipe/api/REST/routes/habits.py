"""HTTP translation for habit operations."""
from datetime import date
from fastapi import APIRouter,Depends,HTTPException,Query
from openipe.api.REST.dependencies import get_current_user,get_internal_api
from openipe.api.REST.schemas.habit import HabitCheckInRequest, HabitCheckInResponse, HabitCreateRequest, HabitResponse, HabitUpdateRequest
from openipe.api.internal import InternalAPI
from openipe.api.internal.contracts import CheckInCreateContract, HabitCreateContract, HabitUpdateContract
from openipe.api.internal.errors import InternalNotFoundError as NotFoundError, InternalValidationError as ValidationError
router=APIRouter(prefix="/habits",tags=["habits"])
@router.get("",response_model=list[HabitResponse])
async def list_habits(active:bool|None=None,context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.habits.list(context,active)
@router.post("",response_model=HabitResponse,status_code=201)
async def create_habit(request:HabitCreateRequest,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:return internal.habits.create(context,HabitCreateContract(request.title,request.description,request.frequency_type,request.frequency_config,request.minimum_version,request.source_inbox_item_id))
 except (NotFoundError,ValidationError) as e:raise HTTPException(400,str(e)) from e
@router.get("/{habit_id}",response_model=HabitResponse)
async def get_habit(habit_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.habits.get(context,habit_id)
@router.patch("/{habit_id}",response_model=HabitResponse)
async def update_habit(habit_id:int,request:HabitUpdateRequest,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:
  if request.archived:return internal.habits.lifecycle(context,habit_id,"archive")
  f=request.model_fields_set
  return internal.habits.update(context,habit_id,HabitUpdateContract(request.title,request.description,request.frequency_type,request.frequency_config,request.minimum_version,request.active,request.archived,request.source_inbox_item_id,frozenset(f)))
 except NotFoundError as e:raise HTTPException(404,"Habit not found") from e
 except ValidationError as e:raise HTTPException(400,str(e)) from e
@router.post("/{habit_id}/check-ins",response_model=HabitCheckInResponse)
async def check_in(habit_id:int,request:HabitCheckInRequest,context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.habits.check_in(context,habit_id,CheckInCreateContract(request.date,request.status,request.note))
@router.get("/{habit_id}/check-ins",response_model=list[HabitCheckInResponse])
async def recent_check_ins(habit_id:int,limit:int=Query(30,ge=1,le=100),context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.habits.recent_check_ins(context,habit_id,limit)
@router.delete("/{habit_id}/check-ins/{checkin_date}",status_code=204)
async def delete_check_in(habit_id:int,checkin_date:date,context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.habits.delete_check_in(context,habit_id,checkin_date)
