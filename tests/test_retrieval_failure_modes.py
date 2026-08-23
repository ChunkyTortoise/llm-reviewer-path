from receipts.retrieval_failure_modes.retriever import classify


def test_empty_retrieval():
    result = classify("empty")
    assert result.ok is False
    assert result.failure == "empty_retrieval"


def test_conflicting_evidence():
    result = classify("conflict")
    assert result.ok is False
    assert result.failure == "conflicting_evidence"


def test_injection_in_retrieved_text():
    result = classify("injection")
    assert result.ok is False
    assert result.failure == "prompt_injection"


def test_malformed_structured_output():
    result = classify("malformed")
    assert result.ok is False
    assert result.failure == "malformed_structured_output"


def test_clean_pass():
    result = classify("clean")
    assert result.ok is True
    assert result.failure is None
