from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
from services.health import HealthCheckService
from shared.schemas.health import HealthStatusResponse

router = APIRouter(prefix="/health", tags=["health"], route_class=DishkaRoute)


@router.get("")
async def health():
    return Response(status_code=status.HTTP_200_OK, content="OK")


@router.get("/overall")
async def health_overall(
    health_check_service: FromDishka[HealthCheckService],
) -> HealthStatusResponse:
    result = await health_check_service.check()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=result.model_dump(),
    )
