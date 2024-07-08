import uuid

import zodchy
import datetime

from .definitions import TaskState, GetTasks


def test_query(adapter):
    owner_id = uuid.uuid4()
    query = GetTasks(
        owner_id=zodchy.operators.EQ(owner_id),
        name=zodchy.operators.EQ("test"),
        state=zodchy.operators.SET(TaskState.new, TaskState.done),
        created_at=zodchy.operators.RANGE(
            zodchy.operators.GE(datetime.datetime(2022, 1, 1)),
            zodchy.operators.LE(datetime.datetime(2022, 11, 2))
        ) + zodchy.operators.DESC(),
        limit=zodchy.operators.Limit(10),
    )
    g = adapter(query)
    assert len(list(g)) == 6
