from pydantic import BaseModel, ConfigDict

class RegionSchema(BaseModel):
    id: int
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)
