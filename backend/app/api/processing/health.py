from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from services.health import HealthCheckService

router = APIRouter(prefix="/health", tags=["health"], route_class=DishkaRoute)


@router.post("")
async def process_health_overall(
    health_check_service: FromDishka[HealthCheckService],
):
    await health_check_service.process_health_overall()
