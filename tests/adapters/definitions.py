import uuid

import zodchy
import dataclasses
import enum
import datetime


class TaskState(str, enum.Enum):
    new = "new"
    in_progress = "in_progress"
    done = "done"
    canceled = "canceled"


@dataclasses.dataclass
class GetTasks(zodchy.codex.cqea.Query):
    owner_id: zodchy.codex.query.ClauseBit[uuid.UUID] | None = None
    name: zodchy.codex.query.ClauseBit[str] | None = None
    state: zodchy.codex.query.ClauseBit[TaskState] | None = None
    created_at: zodchy.codex.query.ClauseBit[datetime.datetime] | None = None
    limit: zodchy.operators.Limit | None = None


class DWM:
    def __init__(self, data: dict[int, enum.Enum]):
        self._data = data

    def __call__(self, value: enum.Enum) -> int | None:
        for k, v in self._data.items():
            if v == value:
                return k


task_state_reference = DWM({
    1: TaskState.new,
    2: TaskState.in_progress,
    3: TaskState.done,
    4: TaskState.canceled
})
