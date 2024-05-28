import zodchy

from hermitage.adapters import transformers

from .definitions import GetTasks, TaskState, task_state_reference


def test_replace_range(adapter):
    query = GetTasks(
        state=zodchy.operators.SET(TaskState.new, TaskState.done),
    )
    state_clause = None
    for clause in adapter(
        query,
        transformers.Replace("state", "state_id", task_state_reference)
    ):
        if clause.name == "state_id":
            state_clause = clause
            break
    assert state_clause is not None
    assert state_clause.operation == zodchy.operators.SET(1, 3)
