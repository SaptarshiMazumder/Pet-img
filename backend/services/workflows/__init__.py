"""
Workflow registry — maps workflow_type strings to strategy instances.
Add new workflows here without touching any other code.
"""
from backend.services.workflow_strategy import WorkflowStrategy
from backend.services.workflows.zturbo import ZTurboWorkflow
from backend.services.workflows.uso import USOWorkflow

_REGISTRY: dict[str, WorkflowStrategy] = {
    "zturbo": ZTurboWorkflow(),
    "uso": USOWorkflow(),
}


def get_workflow(workflow_type: str) -> WorkflowStrategy:
    strategy = _REGISTRY.get(workflow_type)
    if strategy is None:
        available = ", ".join(_REGISTRY)
        raise ValueError(f"Unknown workflow type '{workflow_type}'. Available: {available}")
    return strategy


__all__ = ["get_workflow", "WorkflowStrategy", "ZTurboWorkflow", "USOWorkflow"]
