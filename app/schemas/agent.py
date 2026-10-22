from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class AgentRequest(BaseModel):
    request: str = Field(min_length=1, max_length=12000)
    @field_validator("request")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("request must not be blank")
        return value.strip()

class PlanStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,39}$")
    description: str = Field(min_length=3, max_length=500)
    tool: str = Field(min_length=1, max_length=80)
    expected_output: str = Field(min_length=3, max_length=300)

class AgentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_type: str = Field(min_length=2, max_length=100)
    title: str = Field(min_length=2, max_length=180)
    objective: str = Field(min_length=5, max_length=1000)
    assumptions: list[str] = Field(default_factory=list, max_length=20)
    tasks: list[PlanStep] = Field(min_length=1, max_length=20)

class StepResult(BaseModel):
    step_id: str
    description: str
    tool: str
    status: Literal["succeeded", "failed", "skipped"]
    output: Any = None
    error: str | None = None

class AgentResponse(BaseModel):
    summary: str
    plan: AgentPlan
    assumptions: list[str]
    steps: list[StepResult]
    document_id: str | None = None
    download_url: str | None = None
    status: Literal["succeeded", "partial", "failed"]
    provider_mode: Literal["xai", "groq", "fallback"]
    planner_status: Literal["succeeded", "fallback"]
    fallback_reason: str | None = None
