from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Level(str, Enum):
    ERROR = "error"
    WARN = "warn"
    INFO = "info"


@dataclass(frozen=True)
class Finding:
    code: str
    level: Level
    message: str
    hint: str | None = None
    tool: str | None = None
    weight: int = 0


@dataclass
class ToolSpec:
    name: str
    description: str = ""
    input_schema: dict = field(default_factory=dict)


@dataclass
class ServerSnapshot:
    name: str
    version: str
    protocol_version: str
    tools: list[ToolSpec] = field(default_factory=list)
    prompts: list = field(default_factory=list)
    resources: list = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "ServerSnapshot":
        tools = [ToolSpec(t["name"], t.get("description", ""), t.get("input_schema", {}))
                 for t in d.get("tools", [])]
        return cls(
            name=d.get("name", ""),
            version=d.get("version", ""),
            protocol_version=d.get("protocol_version", ""),
            tools=tools,
            prompts=d.get("prompts", []),
            resources=d.get("resources", []),
            raw=d.get("raw", {}),
        )


@dataclass
class Report:
    score: int
    grade: str
    findings: list[Finding] = field(default_factory=list)
    extras: dict = field(default_factory=dict)
