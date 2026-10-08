"""Shared test fixtures. Tests never call watsonx: they use fake models."""

import pytest
from langchain_core.embeddings import FakeEmbeddings
from langchain_core.language_models.fake import FakeListLLM


@pytest.fixture
def fake_embeddings():
    return FakeEmbeddings(size=32)


@pytest.fixture
def fake_llm():
    return FakeListLLM(responses=["Stubbed clinical answer from the fake LLM."] * 50)
