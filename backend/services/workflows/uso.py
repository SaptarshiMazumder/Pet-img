"""
USO (Flux1-Dev style-transfer) workflow strategy.
Runs Gemini on the subject image to get the animal description,
then combines it with the scene template to build the prompt.
"""
from backend.services.workflow_strategy import WorkflowStrategy, BuildResult
from backend.services.prompt_builder import load_uso_template, compose_uso_prompt


class USOWorkflow(WorkflowStrategy):
    @property
    def workflow_name(self) -> str:
        return "uso"

    def load_template(self, template_key: str) -> dict:
        return load_uso_template(template_key)

    def build(
        self,
        template_key: str,
        *,
        subject_url: str,
        subject_image_path: str,
        style_url: str,
        overrides: dict,
    ) -> BuildResult:
        template = self.load_template(template_key)
        prompt = compose_uso_prompt(template, subject_image_path)

        job_input: dict = {
            "workflow_type": "uso",
            "prompt": prompt,
            "subject_image": subject_url,
            "style_image_1": style_url,
            "width": 1024,
            "height": 1024,
        }
        job_input.update(overrides)

        return BuildResult(
            job_input=job_input,
            positive_prompt=prompt,
            style_key="uso",
        )
