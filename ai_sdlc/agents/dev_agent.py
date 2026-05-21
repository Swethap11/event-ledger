from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from ai_sdlc.agents.client import get_llm
from ai_sdlc.agents.guardrails import get_callbacks

MODULE = Literal["core", "models", "repositories", "services", "routes", "main"]

_PROMPTS = Path(__file__).parent.parent / "prompts"
PROMPT_FILES: dict[str, Path] = {
    "core":         _PROMPTS / "dev_agent_core.md",
    "models":       _PROMPTS / "dev_agent_models.md",
    "repositories": _PROMPTS / "dev_agent_repositories.md",
    "services":     _PROMPTS / "dev_agent_services.md",
    "routes":       _PROMPTS / "dev_agent_routes.md",
    "main":         _PROMPTS / "dev_agent_main.md",
}

OUTPUT_FILES: dict[str, list[Path]] = {
    "core":         [
        Path("app/core/__init__.py"),
        Path("app/core/database.py"),
        Path("app/core/logging_config.py"),
        Path("app/core/exceptions.py"),
    ],
    "models":       [
        Path("app/models/__init__.py"),
        Path("app/models/orm.py"),
        Path("app/models/schemas.py"),
    ],
    "repositories": [
        Path("app/repositories/__init__.py"),
        Path("app/repositories/event_repo.py"),
    ],
    "services":     [
        Path("app/services/__init__.py"),
        Path("app/services/event_service.py"),
    ],
    "routes":       [
        Path("app/routes/__init__.py"),
        Path("app/routes/events.py"),
        Path("app/routes/accounts.py"),
    ],
    "main":         [Path("app/__init__.py"), Path("app/main.py")],
}


class GeneratedFile(BaseModel):
    file_path: str = Field(description="Relative file path e.g. app/core/database.py")
    content: str = Field(description="Complete Python file content — no placeholders, no TODOs")
    commit_message: str = Field(description="Conventional commit message for this file")


class ModuleOutput(BaseModel):
    module: str
    files: list[GeneratedFile]
    summary: str = Field(description="1-2 sentence summary of what was generated and why")


def run(
    module: MODULE,
    spec_content: str,
    architecture_content: str,
    existing_code: dict[str, str],
    feedback: str = "",
) -> ModuleOutput:
    prompt_file = PROMPT_FILES[module]
    prompt_template = prompt_file.read_text(encoding="utf-8")
    llm = get_llm(temperature=0.05)

    existing_str = "\n\n".join(
        f"### {path}\n```python\n{code}\n```"
        for path, code in existing_code.items()
    ) if existing_code else "No existing code yet."

    feedback_str = f"\n\nPrevious attempt failed. Fix these issues:\n{feedback}" if feedback else ""

    # System prompt is passed as one variable so JSON/code braces are not parsed as templates.
    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        ("human", (
            "Specification:\n{spec}\n\n"
            "Architecture:\n{architecture}\n\n"
            "Existing code context:\n{existing}\n\n"
            "Generate the `{module}` module now. Return complete, runnable Python files."
        )),
    ])

    callbacks = get_callbacks(agent_name="dev_agent", enable_code_guardrails=True)
    chain = prompt | llm.with_structured_output(ModuleOutput)
    return chain.invoke(
        {
            "system_prompt": prompt_template + feedback_str,
            "spec": spec_content,
            "architecture": architecture_content,
            "existing": existing_str,
            "module": module,
        },
        config={"callbacks": callbacks},
    )


def save(output: ModuleOutput) -> dict[str, str]:
    saved: dict[str, str] = {}
    for f in output.files:
        path = Path(f.file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f.content, encoding="utf-8")
        saved[f.file_path] = f.content
        print(f"[Dev Agent] Written: {f.file_path}")
    return saved
