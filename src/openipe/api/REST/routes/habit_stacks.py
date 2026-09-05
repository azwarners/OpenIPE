"""HTTP translation for habit-stack operations."""
from datetime import date
from fastapi import APIRouter,Depends,HTTPException,Query
from openipe.api.REST.dependencies import get_current_user,get_internal_api
from openipe.api.REST.schemas.habit_stack import HabitStackCreateRequest, HabitStackResponse, HabitStackUpdateRequest, ReorderRequest
from openipe.api.internal.contracts import ReorderContract, StackCreateContract, StackUpdateContract
from openipe.api.internal.errors import InternalNotFoundError as NotFoundError
router=APIRouter(prefix="/habit-stacks",tags=["habit-stacks"])
@router.get("",response_model=list[HabitStackResponse])
async def list_stacks(active:bool|None=None,selected_date:date|None=Query(None,alias="date"),context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.habit_stacks.list(context,active,selected_date)
@router.post("",response_model=HabitStackResponse,status_code=201)
async def create_stack(request:HabitStackCreateRequest,context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.habit_stacks.create(context,StackCreateContract(request.name,request.description))
@router.get("/{stack_id}",response_model=HabitStackResponse)
async def get_stack(stack_id:int,selected_date:date|None=Query(None,alias="date"),context=Depends(get_current_user),internal=Depends(get_internal_api)):
 try:return internal.habit_stacks.get(context,stack_id,selected_date)
 except NotFoundError as e: raise HTTPException(404,"Habit stack not found") from e
@router.patch("/{stack_id}",response_model=HabitStackResponse)
async def update_stack(stack_id:int,request:HabitStackUpdateRequest,context=Depends(get_current_user),internal=Depends(get_internal_api)):
 if request.archived:return internal.habit_stacks.lifecycle(context,stack_id,"archive")
 f=request.model_fields_set; return internal.habit_stacks.update(context,stack_id,StackUpdateContract(request.name,request.description,request.active,request.archived,frozenset(f)))
@router.post("/reorder",status_code=204)
async def reorder_stacks(request:ReorderRequest,context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.habit_stacks.reorder_stacks(context,ReorderContract(tuple(request.ids)))
@router.post("/{stack_id}/habits/reorder",status_code=204)
async def reorder_habits(stack_id:int,request:ReorderRequest,context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.habit_stacks.reorder_habits(context,stack_id,ReorderContract(tuple(request.ids)))
@router.post("/{stack_id}/habits/{habit_id}",response_model=HabitStackResponse)
async def add_habit(stack_id:int,habit_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.habit_stacks.add_habit(context,stack_id,habit_id)
@router.delete("/{stack_id}/habits/{habit_id}",response_model=HabitStackResponse)
async def remove_habit(stack_id:int,habit_id:int,context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.habit_stacks.remove_habit(context,stack_id,habit_id)
