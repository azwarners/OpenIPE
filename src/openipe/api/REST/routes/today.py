"""HTTP translation for Today aggregation."""
from datetime import date
from fastapi import APIRouter,Depends,Query
from openipe.api.REST.dependencies import get_current_user,get_internal_api
from openipe.api.REST.schemas.today import TodayResponse
from openipe.api.internal.contracts import TodayQueryContract
router=APIRouter(prefix="/today",tags=["today"])
@router.get("",response_model=TodayResponse)
async def today(selected_date:date|None=Query(None,alias="date"),include_completed:bool=False,context=Depends(get_current_user),internal=Depends(get_internal_api)):return internal.today.get(context,TodayQueryContract(selected_date,include_completed))
