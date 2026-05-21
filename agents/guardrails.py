"""
Guardrail hooks implemented as LangChain callback handlers.
Fire after every LLM call — before output reaches the pipeline.
"""

import re
import logging
from typing import Any, Union
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger("guardrails")

# Patterns that must never appear in generated code
CODE_FORBIDDEN: list[tuple[str, str]] = [
    (r"#\s*TODO", "TODO comment found — incomplete implementation"),
    (r"#\s*FIXME", "FIXME comment found — incomplete implementation"),
    (r"raise\s+NotImplementedError", "NotImplementedError — placeholder not replaced"),
    (r"^\s*\.\.\.\s*$", "Ellipsis body — function not implemented"),
    (r"your[_\s]code[_\s]here", "Placeholder text found"),
    (r"pass\s*$", "Bare pass — empty function body"),
    (r"<FILL[_\s]IN>", "Fill-in placeholder not replaced"),
]

# Patterns that must never appear in any agent output
UNIVERSAL_FORBIDDEN: list[tuple[str, str]] = [
    (r"I cannot|I am unable|I don't have access", "Agent refused to generate — retry with clearer prompt"),
    (r"As an AI|As a language model", "Agent broke character — adjust system prompt"),
]


class CodeGuardrailHandler(BaseCallbackHandler):
    """
    Validates LLM output after every call.
    Raises ValueError if a forbidden pattern is found — pipeline catches this and retries.
    Only active for Dev Agent calls (code generation).
    """

    def __init__(self, agent_name: str = "unknown"):
        super().__init__()
        self.agent_name = agent_name

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        for generations in response.generations:
            for gen in generations:
                text = gen.text if hasattr(gen, "text") else str(gen)
                self._check_universal(text)
                if self.agent_name == "dev_agent":
                    self._check_code(text)

    def _check_universal(self, text: str) -> None:
        for pattern, message in UNIVERSAL_FORBIDDEN:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"[Guardrail:{self.agent_name}] {message}")
                raise ValueError(f"Guardrail blocked output — {message}")

    def _check_code(self, text: str) -> None:
        for pattern, message in CODE_FORBIDDEN:
            if re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
                logger.warning(f"[Guardrail:dev_agent] {message}")
                raise ValueError(f"Guardrail blocked code output — {message}")


class LoggingCallbackHandler(BaseCallbackHandler):
    """
    Logs every LLM call: agent name, prompt length, response length, latency.
    Always active — lightweight observability even without LangSmith.
    """

    def __init__(self, agent_name: str = "unknown"):
        super().__init__()
        self.agent_name = agent_name
        self._start_time: float = 0.0

    def on_llm_start(self, serialized: dict, prompts: list[str], **kwargs: Any) -> None:
        import time
        self._start_time = time.time()
        total_chars = sum(len(p) for p in prompts)
        logger.info(f"[{self.agent_name}] LLM call started — prompt {total_chars} chars")

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        import time
        elapsed = time.time() - self._start_time
        total_chars = sum(
            len(gen.text) if hasattr(gen, "text") else 0
            for gens in response.generations
            for gen in gens
        )
        logger.info(f"[{self.agent_name}] LLM call complete — {total_chars} chars in {elapsed:.2f}s")

    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        logger.error(f"[{self.agent_name}] LLM call failed — {error}")


def get_callbacks(agent_name: str, enable_code_guardrails: bool = False) -> list:
    """Return the callback stack for a given agent."""
    handlers: list = [LoggingCallbackHandler(agent_name=agent_name)]
    if enable_code_guardrails:
        handlers.append(CodeGuardrailHandler(agent_name=agent_name))
    return handlers
