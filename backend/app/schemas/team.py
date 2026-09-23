from pydantic import BaseModel, ConfigDict, Field


class TeamFields(BaseModel):
    name: str = Field(min_length=1)
    interests: str | None = None
    skills: str | None = None
    technologies: str | None = None


class TeamCreate(TeamFields):
    pass


class TeamUpdate(BaseModel):
    name: str | None = None
    interests: str | None = None
    skills: str | None = None
    technologies: str | None = None


class TeamRead(TeamFields):
    model_config = ConfigDict(from_attributes=True)
    id: int
