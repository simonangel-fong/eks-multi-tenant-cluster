# schemas.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str


class PollCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    options: list[str] = Field(min_length=2, max_length=20)
    closes_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def _strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be blank")
        return v

    @field_validator("options")
    @classmethod
    def _strip_options(cls, v: list[str]) -> list[str]:
        cleaned = [s.strip() for s in v]
        if any(not s for s in cleaned):
            raise ValueError("option labels must not be blank")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("option labels must be unique")
        return cleaned

    @model_validator(mode="after")
    def _closes_at_future(self) -> "PollCreate":
        if self.closes_at is not None and self.closes_at <= datetime.now(
            self.closes_at.tzinfo
        ):
            raise ValueError("closes_at must be in the future")
        return self


class PollSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    closes_at: datetime | None


class PollDetail(PollSummary):
    options: list[OptionOut]
