from __future__ import annotations

import os


def generate_llm_fraud_report(decisions_json: str, model: str | None = None) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install OpenAI SDK first: python3 -m pip install openai") from exc

    selected_model = model or os.environ.get("OPENAI_MODEL")
    if not selected_model:
        raise RuntimeError("Set OPENAI_MODEL to the model you want to use.")

    client = OpenAI()
    response = client.responses.create(
        model=selected_model,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a bank fraud analyst. Produce a concise Korean incident report "
                    "with risk summary, key patterns, recommended actions, and caveats."
                ),
            },
            {
                "role": "user",
                "content": f"Analyze these fraud decisions as JSON records:\n{decisions_json}",
            },
        ],
    )
    return response.output_text
