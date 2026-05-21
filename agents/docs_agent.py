from pathlib import Path
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from agents.client import get_llm
import httpx

PROMPT_FILE = Path(".prompts/docs_agent.md")


class DocsOutput(BaseModel):
    api_guide: str = Field(description="Complete API guide in Markdown with endpoint descriptions, examples, and curl commands")


def fetch_openapi_spec(base_url: str = "http://localhost:8000") -> dict:
    try:
        r = httpx.get(f"{base_url}/openapi.json", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise RuntimeError(f"Could not fetch OpenAPI spec from {base_url}/openapi.json: {e}")


def run(openapi_spec: dict, spec_content: str) -> DocsOutput:
    prompt_template = PROMPT_FILE.read_text(encoding="utf-8")
    llm = get_llm(temperature=0.2)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        ("human", (
            "Original specification:\n{spec}\n\n"
            "OpenAPI spec from live app:\n{openapi}\n\n"
            "Generate a complete developer-facing API guide."
        )),
    ])

    chain = prompt | llm.with_structured_output(DocsOutput)
    return chain.invoke({"system_prompt": prompt_template, "spec": spec_content, "openapi": str(openapi_spec)})


def save(output: DocsOutput, output_path: Path = Path("docs/api-guide.md")) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output.api_guide, encoding="utf-8")
    print(f"[Docs Agent] API guide written to {output_path}")
