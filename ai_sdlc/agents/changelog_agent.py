from pathlib import Path
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from ai_sdlc.agents.client import get_llm
import subprocess

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "changelog_agent.md"


class ChangelogOutput(BaseModel):
    changelog: str = Field(description="Complete CHANGELOG.md in Keep a Changelog format")


def get_git_log() -> str:
    result = subprocess.run(
        ["git", "log", "--oneline", "--no-decorate"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return "No git history available."
    return result.stdout.strip()


def run(git_log: str) -> ChangelogOutput:
    prompt_template = PROMPT_FILE.read_text(encoding="utf-8")
    llm = get_llm(temperature=0.2)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        ("human", "Git log:\n\n{log}\n\nGenerate a structured CHANGELOG.md."),
    ])

    chain = prompt | llm.with_structured_output(ChangelogOutput)
    return chain.invoke({"system_prompt": prompt_template, "log": git_log})


def save(output: ChangelogOutput, output_path: Path = Path("CHANGELOG.md")) -> None:
    output_path.write_text(output.changelog, encoding="utf-8")
    print(f"[Changelog Agent] CHANGELOG.md written to {output_path}")
