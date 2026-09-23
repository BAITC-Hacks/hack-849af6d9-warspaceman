from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProposalCreate(BaseModel):
    team_id: int
    idea: str = Field(min_length=1)
    plan: str | None = None
    deadline: str | None = None
    link: str | None = None


class ProposalUpdate(BaseModel):
    status: str = Field(pattern="^(pending|accepted|rejected)$")


class ProposalRead(ProposalCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    task_id: int
    status: str
    created_at: datetime | None = None
