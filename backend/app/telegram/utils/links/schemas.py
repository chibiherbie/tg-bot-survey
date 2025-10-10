from shared.schemas.base import ResponseModel


class StartParamSchema(ResponseModel):
    pg: str | None = None
    utm: str | None = None
    ref: int | None = None

    def get_start_param(self) -> str:
        json_obj = self.model_dump(mode="json")
        return "-".join(f"{key}_{value}" for key, value in json_obj.items())
