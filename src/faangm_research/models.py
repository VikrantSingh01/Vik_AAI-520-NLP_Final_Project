"""Sequential local-model runtimes with validated structured output."""

from __future__ import annotations

import gc
import json
import re
from dataclasses import dataclass
from typing import Any

import torch
from pydantic import TypeAdapter, ValidationError

from faangm_research.agents.planner import build_research_plan
from faangm_research.schemas import PlanStep


@dataclass(frozen=True, slots=True)
class ModelMeasurement:
    model: str
    device: str
    load_seconds: float
    inference_seconds: float
    rss_before_mb: float
    rss_after_mb: float
    records: int


def preferred_device() -> str:
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def release_model(*objects: Any) -> None:
    for item in objects:
        del item
    gc.collect()
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


class FinBertSentiment:
    model_name = "ProsusAI/finbert"

    def __init__(self, device: str | None = None) -> None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.device = device or preferred_device()
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()

    def predict(
        self, texts: list[str], batch_size: int = 8
    ) -> list[dict[str, float | str]]:
        results: list[dict[str, float | str]] = []
        labels = {
            int(key): value.lower() for key, value in self.model.config.id2label.items()
        }
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            inputs = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(self.device)
            with torch.inference_mode():
                probabilities = self.model(**inputs).logits.softmax(dim=-1).cpu()
            for row in probabilities:
                scores = {
                    labels[index]: float(score) for index, score in enumerate(row)
                }
                label = max(scores, key=scores.get)
                results.append({"label": label, **scores})
        return results


class QwenStructuredPlanner:
    model_name = "Qwen/Qwen2.5-1.5B-Instruct"

    def __init__(self, device: str | None = None) -> None:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.device = device or preferred_device()
        dtype = torch.float16 if self.device in {"mps", "cuda"} else torch.float32
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            dtype=dtype,
            low_cpu_mem_usage=True,
        )
        self.model.to(self.device)
        self.model.eval()

    def generate(self, prompt: str, max_new_tokens: int = 700) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a financial-research planner. Return only valid JSON. "
                    "Never provide investment advice or invent source results."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        with torch.inference_mode():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                repetition_penalty=1.03,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        generated = output[0, inputs.input_ids.shape[1] :]
        return self.tokenizer.decode(generated, skip_special_tokens=True).strip()

    def plan(self, query: str) -> tuple[list[PlanStep], dict[str, Any]]:
        fallback = build_research_plan(query)
        prompt = planning_prompt(query, fallback)
        raw = self.generate(prompt)
        try:
            plan = parse_plan_json(raw)
            return plan, {"schema_valid": True, "fallback_used": False, "raw": raw}
        except (json.JSONDecodeError, ValidationError, ValueError) as error:
            fallback_json = json.dumps(
                [step.model_dump(mode="json") for step in fallback], indent=2
            )
            repair = self.generate(
                "Repair the following output into the required JSON array. "
                "Return JSON only.\n"
                f"Validation error: {error}\nRequired example:\n"
                f"{fallback_json}\n"
                f"Invalid output:\n{raw}"
            )
            try:
                plan = parse_plan_json(repair)
                return plan, {
                    "schema_valid": True,
                    "fallback_used": False,
                    "repair_used": True,
                    "raw": raw,
                    "repair": repair,
                }
            except (json.JSONDecodeError, ValidationError, ValueError) as repair_error:
                return fallback, {
                    "schema_valid": False,
                    "fallback_used": True,
                    "raw": raw,
                    "repair": repair,
                    "error": str(repair_error),
                }


def planning_prompt(query: str, baseline: list[PlanStep]) -> str:
    example = [step.model_dump(mode="json") for step in baseline]
    return (
        "Create a query-specific research plan using only the allowed agents and "
        "tools shown in the baseline. Omit market or macro steps when the query does "
        "not need them. Keep the final evaluator_optimizer step. Return a JSON array "
        "with exactly these fields per step: step_id, objective, agent, "
        "candidate_tools, selected_tool, "
        "dependencies, success_criteria, fallback, status. status must be pending.\n\n"
        f"Query: {query}\n\nBaseline allowed plan:\n{json.dumps(example, indent=2)}"
    )


def parse_plan_json(text: str) -> list[PlanStep]:
    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE
    )
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start < 0 or end < start:
        raise ValueError("No JSON array found")
    payload = json.loads(cleaned[start : end + 1])
    plan = TypeAdapter(list[PlanStep]).validate_python(payload)
    if not plan or plan[-1].selected_tool != "evaluator_optimizer":
        raise ValueError("Plan must end with evaluator_optimizer")
    return plan
