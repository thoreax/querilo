from qa_engine.core.document_factory import ESDocumentFactory
from qa_engine.core.models import TextEntry
import pytest
import time

es_client_params = {
    "hosts": "http://localhost:9200",
    "timeout": 30,
}

index_name = "test_index_doc_entries"
embedding_size = 128
doc_id = "test_doc_id"


@pytest.fixture()
def es_doc_factory():
    factory = ESDocumentFactory(es_client_params, index_name)
    factory.clear()
    time.sleep(1)
    return factory


@pytest.fixture()
def loaded_doc_factory(es_doc_factory):
    # generate random embedding entries
    text_entries = []
    for i in range(10):
        text_entries.append(
            TextEntry(f"preloaded-text-entry-{i}", f"Preloaded text sample {i}", {}))

    es_doc_factory.store(doc_id, text_entries, refresh=True)
    return es_doc_factory


def test_create_index_if_not_exists(es_doc_factory):
    es_doc_factory.es_client.indices.delete(index=index_name)
    es_doc_factory = ESDocumentFactory(es_client_params, index_name)
    assert es_doc_factory.es_client.indices.exists(index=index_name)


def test_store(es_doc_factory):
    # generate random embedding entries
    text_entries = []
    for i in range(10):
        text_entries.append(TextEntry(str(i), f"My text entry {i}", {}))
    # Store them
    es_doc_factory.store(doc_id, text_entries, refresh=True)
    assert es_doc_factory.es_client.count(index=index_name)["count"] == 10


def test_retrieve(loaded_doc_factory):
    # create two vectors with cosine similarity 1
    text_entries = [
        TextEntry("a", "I am first", {}),
        TextEntry("b", "I am second", {}),
    ]
    loaded_doc_factory.store(doc_id, text_entries, refresh=True)
    retrieved_text_entries = loaded_doc_factory.retrieve(doc_id, ["a", "b"])

    assert len(retrieved_text_entries) == 2
    assert retrieved_text_entries[0].id == "a"
    assert retrieved_text_entries[1].id == "b"


def test_meta_retrieval(es_doc_factory):
    # generated some random text entries
    text_entries = [
        TextEntry("a", "I am first", {"a": 1}),
        TextEntry("b", "I am second", {"b": 2}),
    ]
    es_doc_factory.store(doc_id, text_entries, refresh=True)
    retrieved_text_entries = es_doc_factory.retrieve(doc_id, metadata={"a": 1})

    assert len(retrieved_text_entries) == 1
    assert retrieved_text_entries[0].id == "a"
    assert retrieved_text_entries[0].metadata == {"a": 1}


if __name__ == "__main__":
    pytest.main(["-v", "tests/es_factory.py"])
