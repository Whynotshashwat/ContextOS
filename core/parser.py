import json
from pathlib import Path
from pydantic import BaseModel, ValidationError
from typing import Optional, List
from datetime import datetime


# --- Models ---

class SubTask(BaseModel):
    id: str
    title: str
    status: str = "pending"
    priority: str = "medium"
    notes: Optional[str] = None
    subtasks: Optional[List["SubTask"]] = []
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

SubTask.model_rebuild()


class Task(BaseModel):
    id: str
    title: str
    status: str = "pending"
    priority: str = "medium"
    notes: Optional[str] = None
    subtasks: Optional[List[SubTask]] = []
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class ProjectModel(BaseModel):
    name: str
    goal: str
    description: Optional[str] = ""


class StateModel(BaseModel):
    phase: str = "Planning"
    current_task: str = ""
    current_subtask: Optional[str] = ""


class RulesModel(BaseModel):
    max_subtasks: int = 5
    execute_one_subtask_only: bool = True
    always_use_context: bool = True


class ConfigModel(BaseModel):
    provider: Optional[str] = ""
    model: Optional[str] = ""
    api_key_env: Optional[str] = ""


class AICFModel(BaseModel):
    aicf_version: str = "1.0"
    project: ProjectModel
    state: StateModel
    tasks: List[Task] = []
    rules: RulesModel = RulesModel()
    config: Optional[ConfigModel] = ConfigModel()


# --- Parser ---

class Parser:

    def __init__(self, context_path: Path):
        self.context_path = context_path

    def load(self) -> AICFModel:
        if not self.context_path.exists():
            raise FileNotFoundError(
                f"AICF file not found at {self.context_path}"
            )
        with open(self.context_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        try:
            return AICFModel(**raw)
        except ValidationError as e:
            raise ValueError(f"Invalid AICF format:\n{e}")

    def save(self, model: AICFModel) -> None:
        with open(self.context_path, "w", encoding="utf-8") as f:
            json.dump(model.model_dump(), f, indent=2)

    def load_raw(self) -> dict:
        with open(self.context_path, "r", encoding="utf-8") as f:
            return json.load(f)