"""
Strategy pattern for generation workflows.
Each workflow (ZTurbo, USO, …) implements WorkflowStrategy and is fully self-contained:
it knows how to load its templates and build the RunPod job input.
The execution harness in generation.py is shared.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class BuildResult:
    """Output of WorkflowStrategy.build() — everything the harness needs to submit the job."""
    job_input: dict
    positive_prompt: str
    negative_prompt: str = ""
    animal_data: dict | None = None
    style_key: str | None = None   # written to DB; falls back to workflow_name if None


class WorkflowStrategy(ABC):
    """
    Encapsulates what differs between generation workflows:
      - which template file to read
      - how to build the RunPod job_input from those templates + caller inputs
    Everything else (RunPod submit/poll, Gemini review, autoscaler, DB) lives in the harness.
    """

    @property
    @abstractmethod
    def workflow_name(self) -> str:
        """Short identifier, e.g. 'zturbo' or 'uso'. Used in DB records."""
        ...

    @abstractmethod
    def load_template(self, template_key: str) -> dict:
        """Load and return the template config dict for the given key."""
        ...

    @abstractmethod
    def build(self, template_key: str, **kwargs) -> BuildResult:
        """
        Build the full RunPod job_input and prompt metadata.
        kwargs are workflow-specific (image_path for ZTurbo, subject_url/style_url for USO, etc.)
        """
        ...

    @abstractmethod
    def review_and_fix(self, image_bytes: bytes) -> bytes | None:
        """
        Review the generated image and return fixed bytes if issues are found, else None.
        Each workflow defines what counts as an issue and how aggressively to fix it.
        """
        ...
