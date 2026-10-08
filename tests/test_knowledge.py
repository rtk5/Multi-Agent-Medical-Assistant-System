from langchain_core.documents import Document

from medical_assistant.config import CHUNKING, PDF_CONFIGS, TEXTBOOKS_DIR, default_pdf_configs
from medical_assistant.domains import MedicalDomain
from medical_assistant.knowledge import build_demo_documents, load_pdfs, split_into_chunks
from medical_assistant.prompts import INPUT_VARIABLES, build_prompt


def test_every_specialty_has_demo_documents():
    for domain in (MedicalDomain.DIABETES, MedicalDomain.CANCER,
                   MedicalDomain.MENTAL_HEALTH, MedicalDomain.CARDIAC):
        docs = build_demo_documents(domain)
        assert len(docs) == 3
        assert all(doc.metadata["domain"] == domain.value for doc in docs)
        assert all(doc.page_content and not doc.page_content.startswith(" ") for doc in docs)


def test_general_domain_has_no_demo_documents():
    assert build_demo_documents(MedicalDomain.GENERAL) == []


def test_missing_pdfs_are_skipped_not_raised(tmp_path):
    missing = str(tmp_path / "does_not_exist.pdf")
    result = load_pdfs([missing], MedicalDomain.DIABETES)
    assert result.pages == []
    assert result.files_loaded == 0
    assert result.files_skipped == [missing]


def test_split_into_chunks_respects_size_and_overlap():
    text = ("Insulin lowers blood glucose by promoting uptake into muscle and fat. " * 60).strip()
    chunks = split_into_chunks([Document(page_content=text, metadata={"domain": "diabetes"})])
    assert len(chunks) > 1
    assert all(len(c.page_content) <= CHUNKING.chunk_size for c in chunks)
    assert all(c.metadata == {"domain": "diabetes"} for c in chunks)


def test_prompt_templates_expose_the_chain_variables():
    for domain in (MedicalDomain.DIABETES, MedicalDomain.CANCER,
                   MedicalDomain.MENTAL_HEALTH, MedicalDomain.CARDIAC):
        prompt = build_prompt(domain)
        assert sorted(prompt.input_variables) == sorted(INPUT_VARIABLES)


def test_pdf_configs_point_to_existing_textbooks():
    # Guards against config drift: every configured textbook should exist in textbooks/.
    for domain, names in PDF_CONFIGS.items():
        for name in names:
            assert (TEXTBOOKS_DIR / name).exists(), f"{domain.value}: missing {name}"
    resolved = default_pdf_configs()
    assert set(resolved) == set(PDF_CONFIGS)
