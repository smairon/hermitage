import uuid

import zodchy
import datetime

from .definitions import TaskState, GetTasks


def test_query(adapter):
    owner_id = uuid.uuid4()
    query = GetTasks(
        owner_id=zodchy.codex.query.EQ(owner_id),
        name=zodchy.codex.query.EQ("test"),
        state=zodchy.codex.query.SET(TaskState.new, TaskState.done),
        created_at=zodchy.codex.query.RANGE(
            zodchy.codex.query.GE(datetime.datetime(2022, 1, 1)),
            zodchy.codex.query.LE(datetime.datetime(2022, 11, 2))
        ),
        limit=zodchy.codex.query.Limit(10),
    )
    g = adapter(query)
    assert len(list(g)) == 5
