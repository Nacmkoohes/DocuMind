
import logging

from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from .exceptions import LLMNotConfigured, LLMError


logger = logging.getLogger(__name__)


class LLMClient:

    def __init__(self):
        if not settings.OPENROUTER_API_KEY:
            raise LLMNotConfigured(
                "OPENROUTER_API_KEY is not configured."
            )

        if not settings.OPENROUTER_MODEL:
            raise LLMNotConfigured(
                "OPENROUTER_MODEL is not configured."
            )

        self.llm = ChatOpenAI(
            model=settings.OPENROUTER_MODEL,
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.LLM_TIMEOUT,
            max_retries=2,
        )

    def generate(self, messages):
        try:
            response = self.llm.invoke(messages)
            return response.content

        except Exception as exc:
            logger.exception("LLM generation failed")
            raise LLMError("LLM request failed.") from exc

    def generate_with_prompt(self, prompt, inputs):
        try:
            chain = prompt | self.llm | StrOutputParser()
            return chain.invoke(inputs)

        except Exception as exc:
            logger.exception("LLM generation with prompt failed")
            raise LLMError("LLM request failed.") from exc
