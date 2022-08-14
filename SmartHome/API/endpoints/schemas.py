from uuid import UUID
from pydantic import BaseModel
from API.models import DeviceModelParameter


class Parameter(BaseModel):
    id: UUID
    name: str
    value_type: str

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj):
        if isinstance(obj, DeviceModelParameter):
            return super().from_orm(obj.parameter)
        else:
            return super().from_orm(obj)

class DeviceParameter(Parameter):
    value: int

class DeviceModel(BaseModel):
    id: UUID
    name: str
    parameters: list[Parameter]

    class Config:
        orm_mode = True
