from pathlib import Path
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ai_sdlc.agents.client import get_llm

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "monitor_agent.md"


class MonitorOutput(BaseModel):
    classification: Literal["BUG", "SECURITY", "TEST_GAP", "TRANSIENT"]
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    affected_file: str = Field(description="Relative path to the file needing a fix")
    root_cause: str = Field(description="1-2 sentence diagnosis")
    fix: str = Field(description="Complete corrected file content, or empty string if TRANSIENT")
    fix_description: str = Field(description="What was changed and why")
    confidence: float = Field(ge=0.0, le=1.0)


def run(error_event: dict, source_files: dict[str, str]) -> MonitorOutput:
    prompt_template = PROMPT_FILE.read_text(encoding="utf-8")
    llm = get_llm(temperature=0.05)

    source_str = "\n\n".join(
        f"### {path}\n```python\n{code}\n```"
        for path, code in source_files.items()
    )

    import json
    error_str = json.dumps(error_event, indent=2)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        ("human", "Error event:\n```json\n{error}\n```\n\nSource files:\n{source}"),
    ])

    chain = prompt | llm.with_structured_output(MonitorOutput)
    return chain.invoke({
        "system_prompt": prompt_template,
        "error": error_str,
        "source": source_str,
    })
