from core.embedding_factory import ESEmbeddingFactory
from core.models import EmbeddingEntry
import pytest
import time

es_client_params = {
    "hosts": "http://localhost:9200",
    "timeout": 30,
}

index_name = "test_index_es_embedding_factory"
embedding_size = 128
doc_id = "test_doc_id"


@pytest.fixture()
def es_embedding_factory():
    es_embedding_factory = ESEmbeddingFactory(es_client_params, index_name, embedding_size)
    es_embedding_factory.clear()
    time.sleep(1)
    return es_embedding_factory


@pytest.fixture()
def loaded_es_embedding_factory(es_embedding_factory):
    # generate random embedding entries
    embedding_entries = []
    for i in range(10):
        embedding_entries.append(
            EmbeddingEntry("preloaded-" + str(i), [i + -10.0 for _ in range(embedding_size)], {}))
    # Store them
    es_embedding_factory.store(doc_id, embedding_entries, refresh=True)
    return es_embedding_factory


def test_create_index_if_not_exists(es_embedding_factory):
    es_embedding_factory.es_client.indices.delete(index=index_name)
    es_embedding_factory = ESEmbeddingFactory(es_client_params, index_name, embedding_size)
    assert es_embedding_factory.es_client.indices.exists(index=index_name)


def test_store(es_embedding_factory):
    # generate random embedding entries
    embedding_entries = []
    for i in range(10):
        embedding_entries.append(EmbeddingEntry(str(i), [i for _ in range(embedding_size)], {}))
    # Store them
    es_embedding_factory.store(doc_id, embedding_entries, refresh=True)
    assert es_embedding_factory.es_client.count(index=index_name)["count"] == 10


def test_retrieve(loaded_es_embedding_factory):
    # create two vectors with cosine similarity 1
    embedding_entries = [
        EmbeddingEntry("a", [1.0 for _ in range(embedding_size)], {}),
        EmbeddingEntry("b", [1.0 for _ in range(embedding_size)], {}),
    ]
    loaded_es_embedding_factory.store(doc_id, embedding_entries, refresh=True)
    retrieved_embedding_entries = loaded_es_embedding_factory.retrieve(doc_id, [1.0 for _ in range(
        embedding_size)])

    assert loaded_es_embedding_factory.es_client.count(index=index_name)["count"] == 10 + 2
    assert retrieved_embedding_entries[0].id == "a"
    assert retrieved_embedding_entries[1].id == "b"
    assert retrieved_embedding_entries[0].embedding == [1.0 for _ in range(embedding_size)]
    assert retrieved_embedding_entries[1].embedding == [1.0 for _ in range(embedding_size)]
    assert retrieved_embedding_entries[0].metadata == {}
    assert retrieved_embedding_entries[1].metadata == {}


def test_meta_retrieval(es_embedding_factory):
    # generate random embedding entries
    embedding_entries = []
    for i in range(10):
        embedding_entries.append(
            EmbeddingEntry(str(i), [i + 1 for _ in range(embedding_size)], {"key": "value"}))
    # Store them
    es_embedding_factory.store(doc_id, embedding_entries, refresh=True)
    retrieved_embedding_entries = es_embedding_factory.retrieve(doc_id, [1.0 for _ in
                                                                         range(embedding_size)])
    assert retrieved_embedding_entries[0].metadata == {"key": "value"}


if __name__ == "__main__":
    pytest.main(["-v", "tests/es_factory.py"])
