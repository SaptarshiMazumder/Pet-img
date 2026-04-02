"""
ZTurbo workflow strategy.
Uses Gemini to analyze the pet image, loads style + template from templates.json,
and builds a fully composed prompt with LoRA config for the ZTurbo ComfyUI workflow.
"""
from backend.services.workflow_strategy import WorkflowStrategy, BuildResult
from backend.services.prompt_builder import (
    build_animal_edo_prompt,
    load_style,
    load_template,
)
from backend.services.image_quality import review_image, fix_image


class ZTurboWorkflow(WorkflowStrategy):
    @property
    def workflow_name(self) -> str:
        return "zturbo"

    def load_template(self, template_key: str) -> dict:
        return load_template(template_key)

    def build(
        self,
        template_key: str,
        *,
        image_path: str,
        style_key: str,
        overrides: dict,
    ) -> BuildResult:
        style = load_style(style_key)
        result = build_animal_edo_prompt(
            image_path=image_path,
            style=style,
            style_key=style_key,
            template_key=template_key,
        )

        lora_cfg = style.get("lora", {})
        job_input: dict = {
            "prompt": result["positive_prompt"],
            "negative_prompt": result["negative_prompt"],
            "lora_name": lora_cfg.get("lora_name", "wetInkZTurbo.safetensors"),
            "lora_strength": lora_cfg.get("lora_strength", 0.3),
            "lora2_name": lora_cfg.get("lora2_name", "ukiyoeZTurbo.safetensors"),
            "lora2_strength": lora_cfg.get("lora2_strength", 0.0),
            "width": 1216,
            "height": 832,
        }
        job_input.update(overrides)

        return BuildResult(
            job_input=job_input,
            positive_prompt=result["positive_prompt"],
            negative_prompt=result["negative_prompt"],
            animal_data=result["animal_data"],
            style_key=style_key,
        )

    def review_and_fix(self, image_bytes: bytes) -> bytes | None:
        fix_prompt = review_image(image_bytes)
        if not fix_prompt:
            return None
        print(f"[review/zturbo] fix prompt: {fix_prompt[:80]}...")
        return fix_image(image_bytes, fix_prompt)
