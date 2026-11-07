from typing import Literal

from pydantic import BaseModel, Field


class AgentDecision(BaseModel):
    """What the model must return on every turn."""

    action: Literal["ask", "estimate"] = Field(
        description="'ask' to ask one clarifying question, 'estimate' when you know which jobs fit."
    )
    question: str | None = Field(
        default=None,
        description="One short clarifying question in the user's language. Only when action is 'ask'.",
    )
    job_codes: list[str] = Field(
        default_factory=list,
        description="Job codes from the catalogue, most likely first. Only when action is 'estimate'. "
        "Empty if nothing in the catalogue fits.",
    )
    explanation: str = Field(
        default="",
        description="Two to four sentences, in the user's language: the likely cause and why these jobs.",
    )
    safety_warnings: list[str] = Field(
        default_factory=list,
        description="Short warnings if the car may be unsafe to drive, in the user's language.",
    )
