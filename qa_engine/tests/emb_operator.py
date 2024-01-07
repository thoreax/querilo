from qa_engine.core.embedding_operator import ModelEmbeddingOperator
from qa_engine.core.models import TextEntry
import numpy as np
import pytest

SIMILARITY_THRESHOLD = 0.5


@pytest.fixture
def operator():
    return ModelEmbeddingOperator('../artifacts/distiluse-base-multilingual-cased-v1')


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def test_identical_sentences(operator):
    entries = [
        TextEntry(
            id="1",
            text='hello world',
            metadata={}
        ),
        TextEntry(
            id="2",
            text='hello world',
            metadata={}
        ),
    ]

    embeddings = operator.embed(entries)
    assert np.isclose(cosine_similarity(embeddings[0].embedding, embeddings[1].embedding), 1.0)


def test_similar_sentences(operator):
    entries = [
        TextEntry(
            id="1",
            text='Aliens surly do exist by chance',
            metadata={}
        ),
        TextEntry(
            id="2",
            text='Aliens are real',
            metadata={}
        ),
    ]

    embeddings = operator.embed(entries)
    print('similarity: ', cosine_similarity(embeddings[0].embedding, embeddings[1].embedding))
    assert cosine_similarity(embeddings[0].embedding,
                             embeddings[1].embedding) > SIMILARITY_THRESHOLD


def test_different_sentences(operator):
    entries = [
        TextEntry(
            id="1",
            text='Aliens surly do exist by chance',
            metadata={}
        ),
        TextEntry(
            id="2",
            text='I like to eat pizza',
            metadata={}
        ),
    ]
    embeddings = operator.embed(entries)
    print('similarity: ', cosine_similarity(embeddings[0].embedding, embeddings[1].embedding))
    assert cosine_similarity(embeddings[0].embedding,
                             embeddings[1].embedding) < SIMILARITY_THRESHOLD


def test_different_sentences(operator):
    entries = [
        TextEntry(
            id="1",
            text='Aliens surly do exist by chance',
            metadata={}
        ),
        TextEntry(
            id="2",
            text='I like to eat pizza',
            metadata={}
        ),
    ]
    embeddings = operator.embed(entries)
    print('similarity: ', cosine_similarity(embeddings[0].embedding, embeddings[1].embedding))
    assert cosine_similarity(embeddings[0].embedding,
                             embeddings[1].embedding) < SIMILARITY_THRESHOLD


if __name__ == '__main__':
    pytest.main()
