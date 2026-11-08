from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

Indicator = Literal[
    "sla",
    "t0",
    "shipping",
    "capotamento",
    "sem_mov",
    "retidos",
    "1bd",
    "5cd",
    "csat",
    "avaria",
    "extravio",
    "pnr",
]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Filters(Strict):
    indicator: Indicator = "sla"
    start: date | None = None
    end: date | None = None
    base_code: str | None = Field(None, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    manager: str | None = Field(None, max_length=120)

    @model_validator(mode="after")
    def period(self):
        if (self.start is None) != (self.end is None):
            raise ValueError("Informe ambas as datas.")
        if self.start and (self.end < self.start or (self.end - self.start).days > 92):
            raise ValueError("Período deve ter de 1 a 93 dias.")
        return self


class Chat(Strict):
    conversation_id: str | None = Field(None, max_length=36)
    message: str = Field(min_length=1, max_length=6000)
    mode: Literal["operational", "development"] = "operational"
    auto_route: bool = False
    filters: Filters = Field(default_factory=Filters)


class MemoryCreate(Strict):
    base_code: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    indicator: Indicator
    occurred_on: date
    explanation: str = Field(min_length=5, max_length=6000)
    evidence: list[str] = Field(default_factory=list, max_length=15)
    actions: str = Field(default="", max_length=3000)
    outcome: str = Field(default="", max_length=3000)
    metrics: dict[str, float] = Field(default_factory=dict, max_length=20)


class MemoryChange(Strict):
    version: int = Field(ge=1)
    reason: str = Field(min_length=5, max_length=1000)
    explanation: str | None = Field(default=None, min_length=5, max_length=6000)
    status: Literal["hypothesis", "confirmed", "rejected"] = "hypothesis"
    evidence: list[str] = Field(default_factory=list, max_length=15)
    actions: str | None = Field(default=None, max_length=3000)
    outcome: str | None = Field(default=None, max_length=3000)


class Investigation(Strict):
    city: str = Field(min_length=2, max_length=100, pattern=r"^[^<>\n\r]+$")
    state: str = Field(pattern=r"^[A-Z]{2}$")
    start: date
    end: date

    @model_validator(mode="after")
    def dates(self):
        if self.end < self.start or (self.end - self.start).days > 31:
            raise ValueError("Máximo 32 dias.")
        return self
