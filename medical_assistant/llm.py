"""Factories for the watsonx.ai language model and embedding model.

Kept separate from the agents so tests can pass in fake models and so the
connection details are defined in exactly one place.
"""

from __future__ import annotations

from langchain_ibm import WatsonxEmbeddings, WatsonxLLM
from ibm_watsonx_ai.metanames import EmbedTextParamsMetaNames, GenTextParamsMetaNames

from medical_assistant.config import WATSONX, WatsonxSettings


def create_llm(settings: WatsonxSettings = WATSONX) -> WatsonxLLM:
    """Create the generation model (Mistral Large on watsonx.ai)."""
    settings.validate()
    params = {
        GenTextParamsMetaNames.MAX_NEW_TOKENS: settings.max_new_tokens,
        GenTextParamsMetaNames.TEMPERATURE: settings.temperature,
        GenTextParamsMetaNames.TOP_P: settings.top_p,
        GenTextParamsMetaNames.REPETITION_PENALTY: settings.repetition_penalty,
    }
    return WatsonxLLM(
        model_id=settings.llm_model_id,
        url=settings.url,
        apikey=settings.api_key,
        project_id=settings.project_id,
        params=params,
    )


def create_embeddings(settings: WatsonxSettings = WATSONX) -> WatsonxEmbeddings:
    """Create the embedding model used to vectorise PDF chunks and questions."""
    settings.validate()
    params = {
        EmbedTextParamsMetaNames.TRUNCATE_INPUT_TOKENS: settings.embedding_truncate_tokens,
        EmbedTextParamsMetaNames.RETURN_OPTIONS: {"input_text": True},
    }
    return WatsonxEmbeddings(
        model_id=settings.embedding_model_id,
        url=settings.url,
        apikey=settings.api_key,
        project_id=settings.project_id,
        params=params,
    )
