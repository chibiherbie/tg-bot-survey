from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ResponseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(serialization_alias=to_camel),
    )


class FormModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(validation_alias=to_camel),
        validate_by_name=True,
    )
