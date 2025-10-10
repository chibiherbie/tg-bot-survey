from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/debug", tags=["debug"], route_class=DishkaRoute)


@router.get("")
async def debug_test():
    raise HTTPException(status_code=404)
