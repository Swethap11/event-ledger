import os
from langchain_openai import ChatOpenAI


def get_llm(temperature: float = 0.1) -> ChatOpenAI:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("GITHUB_TOKEN environment variable not set.")

    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key=token,
        base_url="https://models.inference.ai.azure.com",
        temperature=temperature,
        timeout=120,
        max_retries=1,
    )
